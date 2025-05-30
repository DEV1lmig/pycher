from sqlalchemy.orm import Session, joinedload, selectinload # Ensure selectinload is imported
from sqlalchemy import func
from fastapi import HTTPException, status
from utils import get_password_hash, verify_password
from datetime import datetime as dt # Alias to avoid conflict if 'datetime' is used elsewhere
from typing import Optional, List, Dict, Any, Union, Tuple, Callable # Add all types you use

# Assuming your User model is in shared.models.user
# If it's local to user-service, adjust the import path for User
from models import User
from models import (
    Course, Module, Lesson, Exercise,
    UserCourseEnrollment, UserModuleProgress, UserLessonProgress, UserExerciseSubmission,
    CourseExam, UserExamAttempt
)
# Change this from a relative import to an absolute import
from schemas import (
    UserProgressReportDataSchema, ReportCourseProgressSchema, ReportModuleProgressSchema,
    ReportLessonProgressSchema, ReportExerciseProgressSchema, ReportExamAttemptSchema,
    UserCreate, LessonProgressDetailResponse, ExerciseProgressInfo
)
# Import logger if you use it, e.g., from logging import getLogger; logger = getLogger(__name__)
import logging
logger = logging.getLogger(__name__)

import httpx
import json # Add this import

EXECUTION_SERVICE_URL = "http://execution-service:8001" # Assuming Docker service name, adjust if needed
# For local development without Docker Compose for services:
# EXECUTION_SERVICE_URL = "http://localhost:8001"


# --- Helper functions for cascading completion ---

def _check_and_update_lesson_completion(db: Session, user_id: int, lesson_id: int):
    logger.debug(f"Checking lesson completion for User ID: {user_id}, Lesson ID: {lesson_id}")
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        logger.warning(f"_check_and_update_lesson_completion: Lesson ID {lesson_id} not found.")
        return

    # Get all exercises for this lesson
    lesson_exercises = db.query(Exercise.id).filter(Exercise.lesson_id == lesson_id).all()
    exercise_ids_in_lesson = [e.id for e in lesson_exercises]

    if not exercise_ids_in_lesson:
        logger.info(f"Lesson ID {lesson_id} has no exercises. Considering it complete for User ID {user_id} if progress record exists.")
        # If a lesson has no exercises, it's considered complete once started.
        # Ensure UserLessonProgress exists and mark it complete.
        lesson_progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id
        ).first()
        if lesson_progress and not lesson_progress.is_completed:
            lesson_progress.is_completed = True
            lesson_progress.completed_at = dt.utcnow()
            db.add(lesson_progress)
            # db.commit() will be handled by the calling function (e.g., complete_exercise)
            logger.info(f"Marked Lesson ID {lesson_id} (no exercises) as complete for User ID {user_id}.")
            _check_and_update_module_completion(db, user_id, lesson.module_id)
        return

    # Check if all exercises in the lesson have a correct submission by the user
    all_exercises_correctly_submitted = True
    for exercise_id in exercise_ids_in_lesson:
        correct_submission = db.query(UserExerciseSubmission).filter(
            UserExerciseSubmission.user_id == user_id,
            UserExerciseSubmission.exercise_id == exercise_id,
            UserExerciseSubmission.is_correct == True
        ).first()
        if not correct_submission:
            all_exercises_correctly_submitted = False
            break

    if all_exercises_correctly_submitted:
        lesson_progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id
        ).first()
        if lesson_progress and not lesson_progress.is_completed:
            lesson_progress.is_completed = True
            lesson_progress.completed_at = dt.utcnow()
            db.add(lesson_progress)
            logger.info(f"All exercises in Lesson ID {lesson_id} completed. Marked lesson as complete for User ID {user_id}.")
            _check_and_update_module_completion(db, user_id, lesson.module_id)
        elif not lesson_progress:
            logger.warning(f"Lesson ID {lesson_id} marked as complete by exercises, but no UserLessonProgress record found for User ID {user_id}. Creating one.")
            # This case should ideally be handled by `start_lesson` creating the record.
            new_lesson_progress = UserLessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                is_completed=True,
                started_at=dt.utcnow(), # Or fetch from first exercise submission time
                completed_at=dt.utcnow()
            )
            db.add(new_lesson_progress)
            _check_and_update_module_completion(db, user_id, lesson.module_id)


def _check_and_update_module_completion(db: Session, user_id: int, module_id: int):
    logger.debug(f"Checking module completion for User ID: {user_id}, Module ID: {module_id}")
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        logger.warning(f"_check_and_update_module_completion: Module ID {module_id} not found.")
        return

    # Get all lessons for this module
    module_lessons = db.query(Lesson.id).filter(Lesson.module_id == module_id).all()
    lesson_ids_in_module = [l.id for l in module_lessons]

    if not lesson_ids_in_module:
        logger.info(f"Module ID {module_id} has no lessons. Considering it complete for User ID {user_id} if progress record exists.")
        module_progress = db.query(UserModuleProgress).filter(
            UserModuleProgress.user_id == user_id,
            UserModuleProgress.module_id == module_id
        ).first()
        if module_progress and not module_progress.is_completed:
            module_progress.is_completed = True
            module_progress.completed_at = dt.utcnow()
            db.add(module_progress)
            logger.info(f"Marked Module ID {module_id} (no lessons) as complete for User ID {user_id}.")
            _check_and_update_course_completion(db, user_id, module.course_id)
        return

    all_lessons_completed = True
    for lesson_id in lesson_ids_in_module:
        lesson_progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id,
            UserLessonProgress.is_completed == True
        ).first()
        if not lesson_progress:
            all_lessons_completed = False
            break

    if all_lessons_completed:
        module_progress = db.query(UserModuleProgress).filter(
            UserModuleProgress.user_id == user_id,
            UserModuleProgress.module_id == module_id
        ).first()

        if not module_progress: # Create if doesn't exist (e.g. if module started implicitly)
            logger.info(f"No UserModuleProgress for Module ID {module_id}, User ID {user_id}. Creating one as completed.")
            module_progress = UserModuleProgress(user_id=user_id, module_id=module_id, started_at=dt.utcnow()) # Or derive started_at
            db.add(module_progress)

        if not module_progress.is_completed:
            module_progress.is_completed = True
            module_progress.completed_at = dt.utcnow()
            db.add(module_progress) # Add again if it was fetched and modified
            logger.info(f"All lessons in Module ID {module_id} completed. Marked module as complete for User ID {user_id}.")
            _check_and_update_course_completion(db, user_id, module.course_id)


def _check_and_update_course_completion(db: Session, user_id: int, course_id: int):
    logger.debug(f"Checking course completion for User ID: {user_id}, Course ID: {course_id}")
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        logger.warning(f"_check_and_update_course_completion: Course ID {course_id} not found.")
        return

    # Get all modules for this course
    course_modules = db.query(Module.id).filter(Module.course_id == course_id).all()
    module_ids_in_course = [m.id for m in course_modules]

    if not module_ids_in_course:
        logger.info(f"Course ID {course_id} has no modules. Considering it complete for User ID {user_id} if enrollment exists.")
        enrollment = db.query(UserCourseEnrollment).filter(
            UserCourseEnrollment.user_id == user_id,
            UserCourseEnrollment.course_id == course_id,
            UserCourseEnrollment.is_active_enrollment == True
        ).first()
        if enrollment and not enrollment.is_completed:
            enrollment.is_completed = True
            enrollment.progress_percentage = 100.0
            db.add(enrollment)
            logger.info(f"Marked Course ID {course_id} (no modules) as complete for User ID {user_id}.")
        return

    all_modules_completed = True
    for module_id in module_ids_in_course:
        module_progress = db.query(UserModuleProgress).filter(
            UserModuleProgress.user_id == user_id,
            UserModuleProgress.module_id == module_id,
            UserModuleProgress.is_completed == True
        ).first()
        if not module_progress:
            all_modules_completed = False
            break

    if all_modules_completed:
        enrollment = db.query(UserCourseEnrollment).filter(
            UserCourseEnrollment.user_id == user_id,
            UserCourseEnrollment.course_id == course_id,
            UserCourseEnrollment.is_active_enrollment == True
        ).first()
        if enrollment and not enrollment.is_completed:
            enrollment.is_completed = True
            enrollment.progress_percentage = 100.0 # Mark as 100%
            db.add(enrollment)
            logger.info(f"All modules in Course ID {course_id} completed. Marked course as complete for User ID {user_id}.")

# --- Existing Service Functions (Modified or to be reviewed) ---

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    """Create a new user in the database"""
    try:
        hashed_password = get_password_hash(user.password)

        db_user = User(
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            hashed_password=hashed_password,
            is_active=True
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear usuario"
        )

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# --- Progress Tracking Service Functions ---

def enroll_user_in_course(db: Session, user_id: int, course_id: int):
    """
    Enroll a user in a course. If an inactive enrollment exists, reactivate it.
    Otherwise, create a new enrollment.
    """
    # Check for any existing enrollment (active or inactive)
    existing_enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()

    if existing_enrollment:
        if existing_enrollment.is_active_enrollment:
            logger.warning(f"Enrollment attempt failed: User ID {user_id} already actively enrolled in Course ID {course_id}.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already actively enrolled in this course")
        else:
            # Reactivate the existing inactive enrollment
            logger.info(f"Reactivating existing inactive enrollment for User ID {user_id} in Course ID {course_id}.")
            existing_enrollment.is_active_enrollment = True
            existing_enrollment.enrollment_date = func.now() # Update enrollment date to now
            existing_enrollment.is_completed = False
            existing_enrollment.progress_percentage = 0.0
            existing_enrollment.last_accessed = None
            existing_enrollment.last_accessed_module_id = None
            existing_enrollment.last_accessed_lesson_id = None
            # Consider if UserModuleProgress, UserLessonProgress etc. for this user/course should be reset here.
            # For now, we are not touching them, assuming progress starts fresh.
            # If they should be cleared, add that logic here.
            # Also, ensure UserModuleProgress and UserLessonProgress are created if needed for the first module/lesson
            # For simplicity, we assume starting a module/lesson will create these.
            db.add(existing_enrollment)
            enrollment_to_return = existing_enrollment
    else:
        # Create a new enrollment
        logger.info(f"Creating new enrollment for User ID {user_id} in Course ID {course_id}.")
        new_enrollment = UserCourseEnrollment(
            user_id=user_id,
            course_id=course_id,
            is_active_enrollment=True # Default is True, but explicit for clarity
        )
        db.add(new_enrollment)
        enrollment_to_return = new_enrollment

    try:
        db.commit()
        db.refresh(enrollment_to_return)
        # Potentially check if the first module/lesson should be auto-started or progress records created
        logger.info(f"Enrollment successful for User ID {user_id} in Course ID {course_id}. Enrollment ID: {enrollment_to_return.id}")
        return enrollment_to_return
    except Exception as e:
        db.rollback()
        logger.error(f"Error during enrollment/reactivation for User ID {user_id}, Course ID {course_id}: {e}", exc_info=True)
        # More specific error message might be useful depending on the context
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not process enrollment.")

def start_lesson(db: Session, user_id: int, lesson_id: int):
    # Fetch the lesson and ensure its module is available for module_id
    lesson_model_instance = db.query(Lesson).options(
        selectinload(Lesson.module) # Ensures lesson.module is loaded for lesson.module_id
    ).filter(Lesson.id == lesson_id).first()

    if not lesson_model_instance:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if not lesson_model_instance.module: # Check if module relationship is loaded
        # This should not happen if selectinload worked, but good for robustness
        raise HTTPException(status_code=500, detail="Lesson module data not found.")

    # Ensure user is enrolled in the course
    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == lesson_model_instance.module.course_id, # Access course_id via module
        UserCourseEnrollment.is_active_enrollment == True
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="User not enrolled in this course or enrollment inactive.")

    # Create or update lesson progress
    # Eager load the 'lesson' relationship when fetching UserLessonProgress
    progress = db.query(UserLessonProgress).options(
        joinedload(UserLessonProgress.lesson).selectinload(Lesson.module) # Eager load lesson and its module
    ).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == lesson_id
    ).first()

    if not progress:
        progress = UserLessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            started_at=dt.utcnow(),
            is_completed=False # Explicitly set to false on start
        )
        # Explicitly associate the fetched lesson_model_instance with the new progress object.
        # This makes `progress.lesson` available immediately for the @property.
        progress.lesson = lesson_model_instance
        db.add(progress)
        logger.info(f"Created UserLessonProgress for User ID {user_id}, Lesson ID {lesson_id}")

    # Also ensure UserModuleProgress exists for the parent module
    module_progress = db.query(UserModuleProgress).filter(
        UserModuleProgress.user_id == user_id,
        UserModuleProgress.module_id == lesson_model_instance.module_id # Use module_id from fetched lesson
    ).first()
    if not module_progress:
        module_progress = UserModuleProgress(
            user_id=user_id,
            module_id = lesson_model_instance.module_id, # Use module_id from fetched lesson
            started_at=dt.utcnow(),
            is_completed=False
        )
        db.add(module_progress)
        logger.info(f"Created UserModuleProgress for User ID {user_id}, Module ID {lesson_model_instance.module_id} (triggered by starting lesson {lesson_id}).")


    # Update last accessed timestamps
    enrollment.last_accessed = dt.utcnow()
    enrollment.last_accessed_module_id = lesson_model_instance.module_id # Use module_id from fetched lesson
    enrollment.last_accessed_lesson_id = lesson_id
    if module_progress:
        module_progress.last_accessed_lesson_id = lesson_id
    db.add(enrollment)
    if module_progress: db.add(module_progress)


    try:
        db.commit()
        db.refresh(progress) # Refresh to get ID and ensure relationships are synced if needed
        # The 'lesson' attribute on 'progress' should now be correctly populated,
        # allowing the @property 'module_id' to work.
        if module_progress: db.refresh(module_progress)
        db.refresh(enrollment)
    except Exception as e:
        db.rollback()
        logger.error(f"Error in start_lesson for User ID {user_id}, Lesson ID {lesson_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not start lesson.")

    return progress # 'progress' instance will be serialized by Pydantic

def complete_exercise(db: Session, user_id: int, exercise_id: int, submitted_code: str):
    exercise = db.query(Exercise).options(
        selectinload(Exercise.lesson)
    ).filter(Exercise.id == exercise_id).first()

    if not exercise:
        logger.warning(f"complete_exercise: Exercise ID {exercise_id} not found for User ID {user_id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    if not exercise.lesson_id:
        logger.error(f"complete_exercise: Exercise ID {exercise_id} is not associated with a lesson.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Exercise misconfiguration: not linked to a lesson.")

    lesson_progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == exercise.lesson_id
    ).first()
    if not lesson_progress:
        logger.info(f"No UserLessonProgress for User ID {user_id}, Lesson ID {exercise.lesson_id}. Starting lesson implicitly.")
        # Assuming start_lesson handles its own commit or is part of the transaction
        start_lesson(db, user_id, exercise.lesson_id)
        # It's good practice to re-fetch or ensure the lesson_progress object is available if needed immediately
        lesson_progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == exercise.lesson_id
        ).first()
        if not lesson_progress: # If still not found after starting, something is wrong
             logger.error(f"Failed to create or find UserLessonProgress for User ID {user_id}, Lesson ID {exercise.lesson_id} after implicit start.")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initialize lesson progress.")


    all_tests_passed = True
    execution_summary_output = [] # To store output/error from each test case
    overall_execution_error = ""
    total_execution_time_ms = 0

    try:
        test_cases_list = json.loads(exercise.test_cases) if exercise.test_cases else [{"input": None, "output": ""}] # Default if no test_cases
        if not isinstance(test_cases_list, list): # Basic validation
            logger.error(f"Exercise ID {exercise.id} has malformed test_cases (not a list). Treating as no test cases.")
            test_cases_list = [{"input": None, "output": ""}] # Fallback

    except json.JSONDecodeError:
        logger.error(f"Failed to parse test_cases for Exercise ID {exercise.id}. Raw: {exercise.test_cases}")
        overall_execution_error = "Error: Invalid test case configuration for the exercise."
        all_tests_passed = False
        test_cases_list = [] # Prevent further processing

    if not test_cases_list and not overall_execution_error: # If test_cases was empty string or "[]"
        logger.info(f"Exercise ID {exercise.id} has no defined test cases. Marking as correct if code executes without error.")
        # In this scenario, we might just run the code once without specific input/output checks
        # Or, define a policy (e.g., must have at least one test case to be auto-gradable)
        # For now, let's run it once.
        test_cases_list = [{"input": None, "output": None}] # Special case: run once, no specific output check unless error

    for i, test_case in enumerate(test_cases_list):
        if not all_tests_passed and overall_execution_error: # Stop if initial parsing failed
            break

        test_input = test_case.get("input")
        expected_test_output = test_case.get("output") # Can be None if we only check for errors

        actual_test_output_str_raw = "" # Store raw output before stripping
        execution_test_error_str = ""
        test_execution_time_ms = 0

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{EXECUTION_SERVICE_URL}/execute",
                    json={"code": submitted_code, "input_data": test_input, "timeout": 5},
                    timeout=10.0
                )
                response.raise_for_status()
                exec_result = response.json()

                actual_test_output_str_raw = exec_result.get("output", "") # Get raw output
                actual_test_output_str = actual_test_output_str_raw.strip() # Stripped version for comparison
                execution_test_error_str = exec_result.get("error", "").strip()
                test_execution_time_ms = int(exec_result.get("execution_time", 0) * 1000)
                total_execution_time_ms += test_execution_time_ms

                # DETAILED LOGGING FOR COMPARISON
                logger.debug(f"--- Test Case {i+1} (EID: {exercise_id}, UID: {user_id}) ---")
                logger.debug(f"Input to script: {repr(test_input)}")
                logger.debug(f"Expected Output (raw from JSON): {repr(expected_test_output)}")
                logger.debug(f"Actual Output (raw from execution): {repr(actual_test_output_str_raw)}")

                expected_output_for_comparison = expected_test_output.strip() if expected_test_output is not None else None

                logger.debug(f"Expected Output (stripped for comparison): {repr(expected_output_for_comparison)}")
                logger.debug(f"Actual Output (stripped for comparison): {repr(actual_test_output_str)}")
                # END DETAILED LOGGING

                if execution_test_error_str:
                    all_tests_passed = False
                    execution_summary_output.append(f"Test Case {i+1} (Input: {test_input}):\nError:\n{execution_test_error_str}")
                    logger.info(f"Test Case {i+1} for EID {exercise_id}, UID {user_id} errored: {execution_test_error_str}")
                    break # Stop on first error
                elif expected_test_output is not None and actual_test_output_str != expected_output_for_comparison:
                    all_tests_passed = False
                    execution_summary_output.append(f"Test Case {i+1} (Input: {test_input}):\nExpected:\n{expected_output_for_comparison}\nGot:\n{actual_test_output_str}")
                    logger.info(f"Test Case {i+1} for EID {exercise_id}, UID {user_id} failed. Expected: {repr(expected_output_for_comparison)}, Got: {repr(actual_test_output_str)}")
                    break # Stop on first failed test
                elif expected_test_output is None and not execution_test_error_str: # Case where no specific output, just no error
                    execution_summary_output.append(f"Test Case {i+1} (Input: {test_input}): Passed (no specific output expected, no error).")
                    logger.info(f"Test Case {i+1} for EID {exercise_id}, UID {user_id} passed (no specific output, no error).")
                else: # Passed
                    execution_summary_output.append(f"Test Case {i+1} (Input: {test_input}): Passed")
                    logger.info(f"Test Case {i+1} for EID {exercise_id}, UID {user_id} passed. Expected: {repr(expected_output_for_comparison)}, Got: {repr(actual_test_output_str)}")

        except httpx.RequestError as e:
            logger.error(f"HTTP request to execution service failed for EID {exercise_id}, UID {user_id}, Test Case {i+1}: {e}")
            overall_execution_error = f"Error connecting to execution service: {str(e)}"
            all_tests_passed = False
            break
        except httpx.HTTPStatusError as e:
            logger.error(f"Execution service returned error for EID {exercise_id}, UID {user_id}, Test Case {i+1}: {e.response.status_code} - {e.response.text}")
            try:
                error_detail = e.response.json().get("detail", e.response.text)
            except ValueError:
                error_detail = e.response.text
            overall_execution_error = f"Execution service error: {error_detail}"
            all_tests_passed = False
            break
        except Exception as e:
            logger.error(f"Error processing execution for EID {exercise_id}, UID {user_id}, Test Case {i+1}: {e}", exc_info=True)
            overall_execution_error = f"Error processing execution result: {str(e)}"
            all_tests_passed = False
            break

    is_correct_submission = all_tests_passed and not overall_execution_error

    previous_attempts_count = db.query(UserExerciseSubmission).filter(
        UserExerciseSubmission.user_id == user_id,
        UserExerciseSubmission.exercise_id == exercise_id
    ).count()
    current_attempt_number = previous_attempts_count + 1

    final_output_to_store = overall_execution_error if overall_execution_error else "\n---\n".join(execution_summary_output)

    submission = UserExerciseSubmission(
        user_id=user_id,
        exercise_id=exercise_id,
        lesson_id=exercise.lesson_id,
        submitted_code=submitted_code,
        is_correct=is_correct_submission,
        output=final_output_to_store[:2000], # Truncate if too long for DB
        score=100 if is_correct_submission else 0,
        execution_time_ms=total_execution_time_ms,
        attempt_number=current_attempt_number,
        submitted_at=dt.utcnow()
    )
    db.add(submission)

    try:
        db.commit()
        db.refresh(submission)
        logger.info(f"Exercise ID {exercise_id} submitted by User ID {user_id}, Attempt: {current_attempt_number}. Overall Correct: {is_correct_submission}.")

        if is_correct_submission:
            _check_and_update_lesson_completion(db, user_id, exercise.lesson_id)
            db.commit() # Commit changes from lesson completion check

    except Exception as e:
        db.rollback()
        logger.error(f"Error in complete_exercise DB operations for User ID {user_id}, Exercise ID {exercise_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not record exercise completion properly.")

    return submission

def get_last_accessed_progress(db: Session, user_id: int):
    """Get user's last accessed course, module, and lesson"""
    last_enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.is_completed == False
    ).order_by(UserCourseEnrollment.last_accessed.desc()).first()

    if not last_enrollment:
        return None

    return {
        "course_id": last_enrollment.course_id,
        "module_id": last_enrollment.last_accessed_module_id,
        "lesson_id": last_enrollment.last_accessed_lesson_id
    }

def get_course_progress_summary(db: Session, user_id: int, course_id: int):
    """Get detailed progress summary for a course"""
    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()

    if not enrollment:
        raise HTTPException(status_code=404, detail="User not enrolled in this course")

    # Get total lessons and completed lessons
    total_lessons = db.query(Lesson).join(Module).filter(Module.course_id == course_id).count()
    completed_lessons = db.query(UserLessonProgress).join(Lesson).join(Module).filter(
        Module.course_id == course_id,
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.is_completed == True
    ).count()

    # Get total exercises and completed exercises
    total_exercises = db.query(Exercise).join(Lesson).join(Module).filter(Module.course_id == course_id).count()
    completed_exercises = db.query(UserExerciseSubmission).join(Exercise).join(Lesson).join(Module).filter(
        Module.course_id == course_id,
        UserExerciseSubmission.user_id == user_id,
        UserExerciseSubmission.is_correct == True
    ).count()

    progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

    return {
        "course_id": course_id,
        "user_id": user_id,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "completed_exercises": completed_exercises,
        "total_exercises": total_exercises,
        "progress_percentage": progress_percentage,
        "is_course_completed": enrollment.is_completed,
        "last_accessed": enrollment.last_accessed,
        "last_accessed_module_id": enrollment.last_accessed_module_id,
        "last_accessed_lesson_id": enrollment.last_accessed_lesson_id
    }

def update_user(db: Session, user_id: int, user_update: dict):
    """Update user information"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update only provided fields
        for field, value in user_update.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)

        # updated_at will be automatically set by SQLAlchemy due to onupdate=func.now()
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )

def unenroll_user_from_course(db: Session, user_id: int, course_id: int):
    """
    Unenrolls a user from a course by marking their enrollment as inactive
    and resetting their progress for that course.
    """
    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()

    if not enrollment:
        logger.warning(f"Unenrollment attempt: User ID {user_id} not found for Course ID {course_id} (no existing enrollment).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found.")

    if not enrollment.is_active_enrollment:
        logger.info(f"User ID {user_id} is already unenrolled (inactive) from Course ID {course_id}.")
        # Optionally, still return 204 or a specific message
        # For consistency, we can just let it pass through to the commit and return 204
        # Or raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already unenrolled from this course.")
        # For now, let's treat it as a successful "unenroll" operation if already inactive.
        return # Or raise an error if preferred

    logger.info(f"Starting unenrollment (soft delete) for User ID: {user_id} from Course ID: {course_id}")

    try:
        enrollment.is_active_enrollment = False
        enrollment.is_completed = False # Reset completion status
        enrollment.progress_percentage = 0.0 # Reset progress
        enrollment.last_accessed = None # Reset last accessed time
        enrollment.last_accessed_module_id = None # Reset last accessed module
        enrollment.last_accessed_lesson_id = None # Reset last accessed lesson
        # total_time_spent_minutes could also be reset or left as is for historical data

        # Note: We are NO LONGER deleting UserModuleProgress, UserLessonProgress, etc.
        # Their existence is fine; they just won't be relevant if the enrollment is inactive.
        # If re-enrollment should clear them, that logic would go into the enroll function.

        db.add(enrollment) # Ensure changes are staged
        db.commit()
        logger.info(f"Successfully soft-unenrolled User ID: {user_id} from Course ID: {course_id}. Enrollment marked inactive.")

    except Exception as e:
        db.rollback()
        logger.error(
            f"Error during soft unenrollment for User ID: {user_id}, Course ID: {course_id}. Transaction rolled back. Error: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while trying to unenroll from the course. Please check server logs for details."
        )
    return # Success, FastAPI handles 204

def get_user_enrollments_with_progress(db: Session, user_id: int) -> list[UserCourseEnrollment]:
    """
    Retrieves all *active* course enrollments for a given user, including their progress
    and related course information.
    """
    enrollments = db.query(UserCourseEnrollment).options(
        selectinload(UserCourseEnrollment.course)  # Eagerly load the 'course' relationship
    ).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.is_active_enrollment == True # Filter for active enrollments
    ).all()
    logger.info(f"Fetched {len(enrollments)} active enrollments for User ID: {user_id}")
    return enrollments

def get_user_lesson_progress_detail(db: Session, user_id: int, lesson_id: int) -> Optional[LessonProgressDetailResponse]: # Or schemas.LessonProgressDetailResponse
    """
    Retrieves detailed progress for a specific lesson for a user,
    including the lesson's completion status and status of its exercises.
    """
    logger.debug(f"Fetching detailed lesson progress for User ID: {user_id}, Lesson ID: {lesson_id}")

    # Get the UserLessonProgress record
    lesson_progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == lesson_id
    ).first()

    if not lesson_progress:
        # If there's no progress record, it implies the lesson hasn't been started or accessed.
        # Depending on requirements, you could return None, raise 404, or return a default state.
        # For now, let's check if the lesson itself exists to provide a more specific response.
        lesson_exists = db.query(Lesson.id).filter(Lesson.id == lesson_id).first()
        if not lesson_exists:
            logger.warning(f"get_user_lesson_progress_detail: Lesson ID {lesson_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found.")
        logger.info(f"No UserLessonProgress found for User ID {user_id}, Lesson ID {lesson_id}. Lesson not started by user.")
        # Return a default "not started" state or None. For the frontend hook, returning a structure is better.
        return LessonProgressDetailResponse(
            lesson_id=lesson_id,
            is_completed=False,
            started_at=None,
            completed_at=None,
            exercises_progress=[] # No exercises attempted if lesson not started
        )

    # Get all exercises associated with this lesson
    exercises_in_lesson = db.query(Exercise.id, Exercise.title).filter(Exercise.lesson_id == lesson_id).order_by(Exercise.order_index).all()

    exercises_progress_info: list[ExerciseProgressInfo] = []
    for ex_id, ex_title in exercises_in_lesson:
        # Find the latest correct submission for this exercise by the user
        latest_correct_submission = db.query(UserExerciseSubmission).filter(
            UserExerciseSubmission.user_id == user_id,
            UserExerciseSubmission.exercise_id == ex_id,
            UserExerciseSubmission.is_correct == True
        ).order_by(UserExerciseSubmission.submitted_at.desc()).first()

        # If no correct submission, find the latest incorrect one to show it was attempted
        last_submission_id = None
        is_correct_for_exercise = False
        if latest_correct_submission:
            is_correct_for_exercise = True
            last_submission_id = latest_correct_submission.id
        else:
            latest_any_submission = db.query(UserExerciseSubmission.id).filter(
                UserExerciseSubmission.user_id == user_id,
                UserExerciseSubmission.exercise_id == ex_id
            ).order_by(UserExerciseSubmission.submitted_at.desc()).first()
            if latest_any_submission:
                last_submission_id = latest_any_submission.id

        exercises_progress_info.append(ExerciseProgressInfo(
            exercise_id=ex_id,
            # title=ex_title, # Optional: if you want to return title here too
            is_correct=is_correct_for_exercise,
            last_submission_id=last_submission_id
        ))

    return LessonProgressDetailResponse(
        lesson_id=lesson_progress.lesson_id,
        is_completed=lesson_progress.is_completed,
        started_at=lesson_progress.started_at,
        completed_at=lesson_progress.completed_at,
        exercises_progress=exercises_progress_info
    )

def get_user_progress_report_data(db: Session, user_id: int) -> UserProgressReportDataSchema:
    logger.info(f"Starting to fetch progress report data for user_id: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found for report generation: user_id {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    report_courses_data = []

    enrollments = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.is_active_enrollment == True
    ).options(
        selectinload(UserCourseEnrollment.course).selectinload(Course.modules).selectinload(Module.lessons).selectinload(Lesson.exercises),
        selectinload(UserCourseEnrollment.course).selectinload(Course.exams) # No need for .selectinload(CourseExam.exam_details)
    ).order_by(UserCourseEnrollment.enrollment_date.desc()).all()

    logger.debug(f"Found {len(enrollments)} active enrollments for user_id: {user_id}")

    for enrollment in enrollments:
        course_entity = enrollment.course
        if not course_entity:
            logger.warning(f"Enrollment ID {enrollment.id} for user {user_id} has no associated course. Skipping.")
            continue

        logger.debug(f"Processing course: {course_entity.title} (ID: {course_entity.id})")

        # --- Modules and Lessons Progress ---
        report_modules_data = []
        module_ids_in_course = [m.id for m in course_entity.modules]

        user_module_progress_map = {
            ump.module_id: ump for ump in db.query(UserModuleProgress).filter(
                UserModuleProgress.user_id == user_id,
                UserModuleProgress.module_id.in_(module_ids_in_course)
            ).all()
        }

        for module_entity in sorted(course_entity.modules, key=lambda m: m.order_index or 0):
            user_module_prog = user_module_progress_map.get(module_entity.id)
            report_lessons_data = []
            lesson_ids_in_module = [l.id for l in module_entity.lessons]

            user_lesson_progress_map = {
                ulp.lesson_id: ulp for ulp in db.query(UserLessonProgress).filter(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.lesson_id.in_(lesson_ids_in_module)
                ).all()
            }

            for lesson_entity in sorted(module_entity.lessons, key=lambda l: l.order_index or 0):
                user_lesson_prog = user_lesson_progress_map.get(lesson_entity.id)
                report_exercises_data = []
                exercise_ids_in_lesson = [e.id for e in lesson_entity.exercises]

                all_submissions_for_lesson = db.query(UserExerciseSubmission).filter(
                    UserExerciseSubmission.user_id == user_id,
                    UserExerciseSubmission.exercise_id.in_(exercise_ids_in_lesson)
                ).order_by(UserExerciseSubmission.exercise_id, UserExerciseSubmission.submitted_at.desc()).all()

                latest_submissions_map = {}
                for sub in all_submissions_for_lesson:
                    if sub.exercise_id not in latest_submissions_map:
                        latest_submissions_map[sub.exercise_id] = sub

                for exercise_entity in sorted(lesson_entity.exercises, key=lambda e: e.order_index or 0):
                    submission = latest_submissions_map.get(exercise_entity.id)
                    report_exercises_data.append(ReportExerciseProgressSchema(
                        title=exercise_entity.title,
                        is_correct=submission.is_correct if submission else None,
                        attempts=submission.attempts if submission else 0,
                        score=submission.score if submission else None,
                        submitted_at=submission.submitted_at if submission else None
                    ))

                report_lessons_data.append(ReportLessonProgressSchema(
                    title=lesson_entity.title,
                    is_completed=user_lesson_prog.is_completed if user_lesson_prog else False,
                    started_at=user_lesson_prog.started_at if user_lesson_prog else None,
                    completed_at=user_lesson_prog.completed_at if user_lesson_prog else None,
                    exercises=report_exercises_data
                ))

            report_modules_data.append(ReportModuleProgressSchema(
                title=module_entity.title,
                is_completed=user_module_prog.is_completed if user_module_prog else False,
                started_at=user_module_prog.started_at if user_module_prog else None,
                completed_at=user_module_prog.completed_at if user_module_prog else None,
                lessons=report_lessons_data
            ))


        # --- Exams Progress ---
        report_exams_data = []
        # course_exam_ids = [ce.id for ce in course_entity.exams] # These are CourseExam IDs
        # No, course_entity.exams already contains CourseExam objects due to eager loading

        # Fetch all attempts for CourseExams in this course by the user
        # We can iterate course_entity.exams directly if they are loaded.
        # Let's refine the attempt fetching to be more targeted if needed,
        # but for now, let's assume course_entity.exams are CourseExam objects.

        course_exam_ids_for_attempts = [ce.id for ce in course_entity.exams]
        all_exam_attempts = db.query(UserExamAttempt).filter(
            UserExamAttempt.user_id == user_id,
            UserExamAttempt.exam_id.in_(course_exam_ids_for_attempts) # UserExamAttempt.exam_id links to CourseExam.id
        ).order_by(UserExamAttempt.exam_id, UserExamAttempt.started_at.desc()).all()

        latest_exam_attempts_map = {}
        for attempt in all_exam_attempts:
            if attempt.exam_id not in latest_exam_attempts_map: # Keep only the latest
                latest_exam_attempts_map[attempt.exam_id] = attempt

        for course_exam_entity in sorted(course_entity.exams, key=lambda ce: ce.order_index or 0): # Use ce.order_index
            attempt = latest_exam_attempts_map.get(course_exam_entity.id)
            exam_title = course_exam_entity.title # Use ce.title

            report_exams_data.append(ReportExamAttemptSchema(
                title=exam_title,
                score=attempt.score if attempt else None,
                passed=attempt.passed if attempt else None,
                completed_at=attempt.completed_at if attempt else None
            ))

        report_courses_data.append(ReportCourseProgressSchema(
            title=course_entity.title,
            enrollment_date=enrollment.enrollment_date,
            is_completed=enrollment.is_completed,
            progress_percentage=enrollment.progress_percentage,
            modules=report_modules_data,
            exams=report_exams_data
        ))

    logger.info(f"Successfully aggregated report data for user_id: {user_id}")
    return UserProgressReportDataSchema(
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        report_generated_at=dt.utcnow(),
        courses=report_courses_data
    )
