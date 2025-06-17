from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
import os
from fastapi import HTTPException, status
# Assuming utils.py is in the same directory as services.py
from utils import get_password_hash, verify_password, generate_input_from_constraints
from datetime import datetime as dt
from typing import Optional, List, Dict, Any # Ensure all necessary types are imported

from models import User, UserCourseEnrollment, UserModuleProgress, UserLessonProgress, UserExerciseSubmission, CourseExam, UserExamAttempt, Course, Module, Lesson, Exercise, ExamQuestion # Ensure Module is imported
from schemas import ( # Adjusted if your schemas are structured differently
    UserProgressReportDataSchema, ReportCourseProgressSchema, ReportModuleProgressSchema,
    ReportLessonProgressSchema, ReportExerciseProgressSchema, ReportExamAttemptSchema,
    UserCreate, LessonProgressDetailResponse, ExerciseProgressInfo, UserModuleProgressResponse, UserCourseProgressResponse
)
import logging # Ensure logging is imported
logger = logging.getLogger(__name__) # Ensure logger is initialized

import httpx
import json # If you need to dump json for feedback, otherwise not strictly needed here

# Ensure EXECUTION_SERVICE_URL is defined, e.g.:
# EXECUTION_SERVICE_URL = os.getenv("EXECUTION_SERVICE_URL", "http://execution-service:8001")
# For local dev without docker-compose for services:
EXECUTION_SERVICE_URL = os.getenv("EXECUTION_SERVICE_URL", "http://execution-service:8001") # Or your configured URL


# --- Helper functions for cascading completion ---

def _check_and_update_lesson_completion(db: Session, user_id: int, lesson_id: int):
    logger.debug(f"User ID {user_id}, Lesson ID {lesson_id}: Starting _check_and_update_lesson_completion.")
    lesson = db.query(Lesson).options(selectinload(Lesson.module)).filter(Lesson.id == lesson_id).first() # Eager load module
    if not lesson:
        logger.warning(f"User ID {user_id}: _check_and_update_lesson_completion: Lesson ID {lesson_id} not found.")
        return

    if not lesson.module: # Check if module is loaded
        logger.error(f"Lesson ID {lesson_id} does not have an associated module. Cannot update module/course progress.")
        return # Or handle appropriately

    lesson_exercises = db.query(Exercise.id).filter(Exercise.lesson_id == lesson_id).all()
    exercise_ids_in_lesson = [e.id for e in lesson_exercises]
    logger.debug(f"User ID {user_id}, Lesson ID {lesson_id}: Found {len(exercise_ids_in_lesson)} exercises: {exercise_ids_in_lesson}")

    if not exercise_ids_in_lesson:
        logger.info(f"User ID {user_id}, Lesson ID {lesson_id}: Lesson has no exercises. Considering it complete if progress record exists.")
        lesson_progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id
        ).first()
        if lesson_progress and not lesson_progress.is_completed:
            lesson_progress.is_completed = True
            lesson_progress.completed_at = dt.utcnow()
            db.add(lesson_progress)
            logger.info(f"User ID {user_id}, Lesson ID {lesson_id}: SETTING UserLessonProgress (no exercises) .is_completed to True. Staged for commit.")
            _check_and_update_module_completion(db, user_id, lesson.module_id)
            recalculate_and_update_course_progress(db, user_id, lesson.module.course_id)
        return

    all_exercises_correctly_submitted = True
    for exercise_id_in_loop in exercise_ids_in_lesson:
        logger.debug(f"User ID {user_id}, Lesson ID {lesson_id}: Checking Exercise ID {exercise_id_in_loop} for correct submission.")
        correct_submission = db.query(UserExerciseSubmission).filter(
            UserExerciseSubmission.user_id == user_id,
            UserExerciseSubmission.exercise_id == exercise_id_in_loop,
            UserExerciseSubmission.is_correct == True
        ).first()

        if not correct_submission:
            all_exercises_correctly_submitted = False
            logger.warning(f"User ID {user_id}, Lesson ID {lesson_id}: Exercise ID {exercise_id_in_loop} NOT found as correctly submitted. Lesson will not be marked complete based on this check.")
            break
        else:
            logger.debug(f"User ID {user_id}, Lesson ID {lesson_id}: Exercise ID {exercise_id_in_loop} IS correctly submitted.")

    logger.debug(f"User ID {user_id}, Lesson ID {lesson_id}: Final check for all_exercises_correctly_submitted: {all_exercises_correctly_submitted}")

    if all_exercises_correctly_submitted:
        lesson_progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id
        ).order_by(UserLessonProgress.id.desc()).first()

        if lesson_progress and not lesson_progress.is_completed:
            lesson_progress.is_completed = True
            lesson_progress.completed_at = dt.utcnow()
            db.add(lesson_progress)
            logger.info(f"User ID {user_id}, Lesson ID {lesson_id}: SETTING UserLessonProgress.is_completed to True. Staged for commit.")
        elif not lesson_progress:
            logger.warning(f"Lesson ID {lesson_id} marked as complete by exercises, but no UserLessonProgress record found for User ID {user_id}. Creating one.")
            new_lesson_progress = UserLessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                is_completed=True,
                started_at=dt.utcnow(),
                completed_at=dt.utcnow()
            )
            db.add(new_lesson_progress)
            logger.info(f"User ID {user_id}, Lesson ID {lesson_id}: CREATING UserLessonProgress as completed. Staged for commit.")

        _check_and_update_module_completion(db, user_id, lesson.module_id)
        recalculate_and_update_course_progress(db, user_id, lesson.module.course_id)
    else:
        logger.info(f"User ID {user_id}, Lesson ID {lesson_id}: Not all exercises correctly submitted. UserLessonProgress will not be marked as complete by this path.")


def _check_and_update_module_completion(db: Session, user_id: int, module_id: int):
    logger.debug(f"Checking module completion for User ID: {user_id}, Module ID: {module_id}")
    module = db.query(Module).options(selectinload(Module.course)).filter(Module.id == module_id).first() # Eager load course
    if not module:
        logger.warning(f"_check_and_update_module_completion: Module ID {module_id} not found.")
        return

    if not module.course: # Check if course is loaded
        logger.error(f"Module ID {module_id} does not have an associated course. Cannot update course progress.")
        return

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
            logger.info(f"User ID {user_id}, Module ID {module_id}: SETTING UserModuleProgress (no lessons) .is_completed to True. Staged for commit.")
            _check_and_update_course_completion(db, user_id, module.course_id)
            recalculate_and_update_course_progress(db, user_id, module.course_id)
        return

    all_lessons_completed = True
    for lesson_id_in_loop in lesson_ids_in_module: # Renamed to avoid conflict
        lesson_progress_record = db.query(UserLessonProgress).filter( # Renamed to avoid conflict
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id_in_loop,
            UserLessonProgress.is_completed == True
        ).first()
        if not lesson_progress_record:
            all_lessons_completed = False
            logger.debug(f"User ID {user_id}, Module ID {module_id}: Lesson ID {lesson_id_in_loop} NOT completed. Module not yet complete.")
            break

    if all_lessons_completed:
        module_progress = db.query(UserModuleProgress).filter(
            UserModuleProgress.user_id == user_id,
            UserModuleProgress.module_id == module_id
        ).first()

        if not module_progress:
            logger.info(f"No UserModuleProgress for Module ID {module_id}, User ID {user_id}. Creating one as completed.")
            module_progress = UserModuleProgress(user_id=user_id, module_id=module_id, started_at=dt.utcnow(), is_completed=True, completed_at=dt.utcnow())
            db.add(module_progress)
            logger.info(f"User ID {user_id}, Module ID {module_id}: CREATING UserModuleProgress as completed. Staged for commit.")


        elif not module_progress.is_completed: # Check if it exists but is not completed
            module_progress.is_completed = True
            module_progress.completed_at = dt.utcnow()
            db.add(module_progress)
            logger.info(f"User ID {user_id}, Module ID {module_id}: SETTING UserModuleProgress.is_completed to True. Staged for commit.")

        _check_and_update_course_completion(db, user_id, module.course_id)
        recalculate_and_update_course_progress(db, user_id, module.course_id)
    else:
        logger.info(f"User ID {user_id}, Module ID {module_id}: Not all lessons completed. UserModuleProgress will not be marked as complete.")


def _check_and_update_course_completion(db: Session, user_id: int, course_id: int):
    logger.debug(f"Checking course completion for User ID: {user_id}, Course ID: {course_id}")
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        logger.warning(f"_check_and_update_course_completion: Course ID {course_id} not found.")
        return

    # Get all modules for this course
    course_modules = db.query(Module.id).filter(Module.course_id == course_id).all()
    module_ids_in_course = [m.id for m in course_modules]

    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id,
        UserCourseEnrollment.is_active_enrollment == True
    ).first()

    if not enrollment:
        logger.warning(f"User ID {user_id}, Course ID {course_id}: No active enrollment found in _check_and_update_course_completion.")
        return

    if not module_ids_in_course:
        logger.info(f"Course ID {course_id} has no modules. Considering it complete for User ID {user_id}.")
        if not enrollment.is_completed:
            enrollment.is_completed = True
            enrollment.progress_percentage = 100.0
            enrollment.exam_unlocked = True # ADDED: Unlock exam if course has no modules but is completed
            db.add(enrollment)
            logger.info(f"Marked Course ID {course_id} (no modules) as complete and exam unlocked for User ID {user_id}.")
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
            logger.debug(f"User ID {user_id}, Course ID {course_id}: Module ID {module_id} not completed. Course not yet complete.")
            break

    logger.debug(f"User ID {user_id}, Course ID {course_id}: All modules completed status: {all_modules_completed}")

    if all_modules_completed:
        if not enrollment.is_completed: # Only update if not already marked as completed
            enrollment.is_completed = True
            enrollment.progress_percentage = 100.0 # Mark as 100%
            enrollment.exam_unlocked = True # ADDED: Unlock exam when all modules are completed
            db.add(enrollment)
            logger.info(f"All modules in Course ID {course_id} completed. Marked course as complete and exam unlocked for User ID {user_id}.")
        # If already completed, exam_unlocked should have been set previously, but we can ensure it here too.
        elif not enrollment.exam_unlocked: # If course is completed but exam somehow not unlocked
            enrollment.exam_unlocked = True
            db.add(enrollment)
            logger.info(f"Course ID {course_id} was already complete. Ensured exam is unlocked for User ID {user_id}.")
    # No db.commit() here, it should be handled by the calling function (e.g., complete_exercise or complete_module)


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
    Also, create UserModuleProgress entries for all modules in the course,
    unlocking the first module.
    """
    # Check for any existing enrollment (active or inactive)
    existing_enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()

    enrollment_is_new = False
    if existing_enrollment:
        if not existing_enrollment.is_active_enrollment:
            existing_enrollment.is_active_enrollment = True
            existing_enrollment.enrollment_date = dt.utcnow() # Reset enrollment date on re-activation
            existing_enrollment.last_accessed = dt.utcnow()
            # Reset progress fields if re-enrolling after unenrolling
            existing_enrollment.is_completed = False
            existing_enrollment.progress_percentage = 0.0
            existing_enrollment.total_time_spent_minutes = 0
            existing_enrollment.last_accessed_module_id = None
            existing_enrollment.last_accessed_lesson_id = None
            db.add(existing_enrollment)
            logger.info(f"Reactivated enrollment for User ID {user_id} in Course ID {course_id}.")
        else:
            logger.info(f"User ID {user_id} is already actively enrolled in Course ID {course_id}.")
        enrollment = existing_enrollment
    else:
        enrollment = UserCourseEnrollment(
            user_id=user_id,
            course_id=course_id,
            enrollment_date=dt.utcnow(),
            last_accessed=dt.utcnow(),
            is_active_enrollment=True
        )
        db.add(enrollment)
        enrollment_is_new = True
        logger.info(f"Created new enrollment for User ID {user_id} in Course ID {course_id}.")

    # Update students_count on the course if it's a new, active enrollment
    # This part might be better handled by an event or a separate admin function
    # to avoid direct modification of Course model from user-service if Course is primarily content-service's domain.
    # For now, assuming direct update is acceptable or Course model is accessible here.
    if enrollment_is_new: # Only increment if it's a truly new enrollment being activated
        course_model = db.query(Course).filter(Course.id == course_id).first()
        if course_model:
            course_model.students_count = (course_model.students_count or 0) + 1
            db.add(course_model)

    try:
        db.commit()
        db.refresh(enrollment)
        if enrollment_is_new and course_model:
            db.refresh(course_model)
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing enrollment for User ID {user_id}, Course ID {course_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not process enrollment.")

    # --- Create UserModuleProgress entries for all modules in the course ---
    course_modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order_index.asc()).all()

    if not course_modules:
        logger.warning(f"Course ID {course_id} has no modules. No UserModuleProgress entries created for User ID {user_id}.")
    else:
        for index, module_item in enumerate(course_modules):
            user_module_progress = db.query(UserModuleProgress).filter(
                UserModuleProgress.user_id == user_id,
                UserModuleProgress.module_id == module_item.id
            ).first()

            is_first_module = (index == 0)

            if not user_module_progress:
                user_module_progress = UserModuleProgress(
                    user_id=user_id,
                    module_id=module_item.id,
                    is_completed=False,
                    started_at=None, # Not started yet
                    is_unlocked=is_first_module # Unlock only the first module
                )
                db.add(user_module_progress)
                logger.info(f"Created UserModuleProgress for User ID {user_id}, Module ID {module_item.id}. Unlocked: {is_first_module}")
            else:
                # If progress exists (e.g., re-enrollment), ensure unlock status is correct
                # This logic assumes re-enrollment should reset unlock status based on order.
                # If a module was previously completed, its `is_unlocked` might already be true
                # and `is_completed` true. We only force `is_unlocked` based on its position.
                # A more nuanced approach might be needed if completed modules should remain unlocked
                # even if they are not the first, upon re-enrollment.
                # For now, we'll set it based on being the first module.
                if user_module_progress.is_unlocked != is_first_module:
                    # Only update if it's different, and typically only if it's not completed.
                    # If it's completed, it should naturally be considered unlocked.
                    # This simple logic might need refinement based on exact re-enrollment UX.
                    # A safe bet is to ensure the first module is always unlocked on active enrollment.
                    if is_first_module:
                         user_module_progress.is_unlocked = True
                         logger.info(f"Ensured UserModuleProgress for User ID {user_id}, Module ID {module_item.id} is Unlocked (first module).")
                    # For other modules, if they were somehow marked unlocked but shouldn't be (and aren't completed),
                    # this logic doesn't explicitly re-lock them unless `is_first_module` is false and it was true.
                    # The `complete_module` function should handle unlocking subsequent modules.
                    # The main goal here is to ensure the *first* module is unlocked.
                    # Subsequent modules are unlocked by completing the previous one.
                    elif not user_module_progress.is_completed: # Only re-lock if not completed
                        user_module_progress.is_unlocked = False # Ensure non-first modules start locked unless completed
                        logger.info(f"Ensured UserModuleProgress for User ID {user_id}, Module ID {module_item.id} is Locked (not first, not completed).")


                db.add(user_module_progress)

        try:
            db.commit()
            # Refresh relevant objects if needed, e.g., for returning in response
            # For now, the main enrollment object is already refreshed.
        except Exception as e:
            db.rollback()
            logger.error(f"Error committing UserModuleProgress entries for User ID {user_id}, Course ID {course_id}: {e}", exc_info=True)
            # Don't necessarily fail the whole enrollment if this part fails,
            # but log it as a critical issue. Or decide if this should also raise an HTTPException.


    # The response model is UserCourseProgressResponse, which might expect module progress.
    # For now, returning the basic enrollment. If the response model needs more,
    # this function would need to gather that data.
    # Let's assume UserCourseProgressResponse can be built from the enrollment object.
    # We need to construct the response according to UserCourseProgressResponse schema

    # Simplified response for now, assuming UserCourseProgressResponse can be built from this.
    # You might need to query and build a more complex object if the schema demands it.
    return UserCourseProgressResponse(
        id=enrollment.id,
        user_id=enrollment.user_id,
        course_id=enrollment.course_id,
        is_started=(enrollment.last_accessed is not None), # Basic assumption
        is_completed=enrollment.is_completed,
        started_at=enrollment.enrollment_date, # Or a more specific started_at if tracked
        completed_at=None, # This would be set when course is completed
        current_module_id=enrollment.last_accessed_module_id,
        progress_percentage=enrollment.progress_percentage,
        total_time_spent_minutes=enrollment.total_time_spent_minutes,
        modules_progress=[] # Populate this if your schema requires it and you fetch it here
    )

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

def complete_exercise(db: Session, user_id: int, exercise_id: int, code_submitted: str, input_data: Optional[str] = None):
    """
    Handles the submission of an exercise by a user.
    Validates the code using either a 'submission_test_strategy' (generated inputs)
    or falls back to the 'input_data' provided from the user's interactive test run.
    """
    logger.info(f"Attempting to complete exercise ID {exercise_id} for user ID {user_id}.")
    exercise = db.query(Exercise).options(
        selectinload(Exercise.lesson)
    ).filter(Exercise.id == exercise_id).first()

    if not exercise:
        logger.warning(f"complete_exercise: Exercise ID {exercise_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    # --- NEW: Detect if this is a course exam exercise ---
    is_exam_exercise = (
        exercise.course_id is not None and
        exercise.module_id is None and
        exercise.lesson_id is None
    )

    if is_exam_exercise:
        logger.info(f"User {user_id} is submitting a course exam exercise (ID {exercise_id}) for course {exercise.course_id}.")
        # Evaluate the code as usual (reuse your validation logic)
        # For simplicity, let's assume you have a function that returns pass/fail and output
        validation_result = run_exam_code_validation(code_submitted, exercise, input_data)
        passed = validation_result["passed"]
        output = validation_result["output"]
        error_message = validation_result.get("error", "")

        # Create a UserExamAttempt record
        exam_attempt = UserExamAttempt(
            user_id=user_id,
            exam_id=exercise.course_id,  # Or link to a CourseExam if you have one
            started_at=dt.utcnow(),
            completed_at=dt.utcnow(),
            passed=passed,
            answers=None  # Or store code/output if desired
        )
        db.add(exam_attempt)
        db.commit()
        db.refresh(exam_attempt)

        # If passed, unlock the next course (implement this logic as needed)
        if passed:
            unlock_next_course_for_user(db, user_id, exercise.course_id)

        return {
            "exam_attempt_id": exam_attempt.id,
            "passed": passed,
            "output": output,
            "error": error_message,
            "message": "Examen enviado y registrado correctamente." if passed else "Examen enviado, pero no aprobado."
        }

    # --- existing code for regular exercises ---
    lesson_progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == exercise.lesson_id
    ).first()
    if not lesson_progress:
        logger.info(f"No UserLessonProgress for User ID {user_id}, Lesson ID {exercise.lesson_id}. Starting lesson implicitly.")
        # Calling start_lesson also handles module progress and enrollment checks/updates
        start_lesson(db, user_id, exercise.lesson_id) # This function should handle db.commit internally or stage changes
        lesson_progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == exercise.lesson_id
        ).first()
        if not lesson_progress: # Should not happen if start_lesson is robust
            logger.error(f"Failed to create/find UserLessonProgress for User ID {user_id}, Lesson ID {exercise.lesson_id} after implicit start.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initialize lesson progress.")

    logger.info(f"User ID {user_id}, EID {exercise_id}: Starting complete_exercise. Input data provided: {'Yes' if input_data else 'No'}") # ADDED: Log input_data presence

    validation_rules = exercise.validation_rules if isinstance(exercise.validation_rules, dict) else {}
    if not validation_rules and isinstance(exercise.validation_rules, str): # Handle if it's a JSON string
        try:
            validation_rules = json.loads(exercise.validation_rules)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse validation_rules JSON string for Exercise ID {exercise.id}. Raw: {exercise.validation_rules}")
            validation_rules = {}


    all_system_tests_passed = True # Overall result of the submission
    final_submission_message = ""  # User-facing message for the submission result
    representative_output_for_db = "" # E.g., output of the first test run
    # Store detailed results from each test run (generated or single)
    # This could be stored as a JSON string in the DB if the field supports it.
    detailed_results_log: List[Dict[str, Any]] = []

    submission_strategy = validation_rules.get("submission_test_strategy")

    if submission_strategy and submission_strategy.get("type") == "generated_inputs":
        logger.info(f"EID {exercise_id}, UID {user_id}: Using 'generated_inputs' strategy for submission.")
        count = submission_strategy.get("count", 1)
        constraints = submission_strategy.get("input_constraints", {})

        for i in range(count):
            generated_input_value = generate_input_from_constraints(constraints)
            test_description = f"Generated Test {i+1}/{count} (Input: '{generated_input_value}')"
            logger.debug(f"  Running {test_description} for EID {exercise_id}")

            execution_payload = {
                "exercise_id": exercise_id,
                "code": code_submitted,
                "input_data": generated_input_value
            }
            current_test_passed = False
            current_test_output = ""
            current_test_error = ""

            try:
                response = httpx.post(f"{EXECUTION_SERVICE_URL}/execute", json=execution_payload, timeout=15.0)
                response.raise_for_status()
                exec_result = response.json()
                current_test_passed = exec_result.get("passed", False)
                current_test_output = exec_result.get("output", "")
                current_test_error = exec_result.get("error", "")
                if i == 0: representative_output_for_db = current_test_output

            except httpx.RequestError as e:
                current_test_error = f"Error connecting to execution service: {e}"
                logger.error(f"{test_description} - {current_test_error}")
            except httpx.HTTPStatusError as e:
                current_test_error = f"Execution service error: {e.response.status_code}"
                try: current_test_error += f" - {e.response.json().get('error', 'Unknown execution error')}"
                except: pass # Keep it simple if parsing error response fails
                logger.error(f"{test_description} - {current_test_error}")
            except Exception as e:
                current_test_error = f"Unexpected error during execution: {e}"
                logger.error(f"{test_description} - {current_test_error}", exc_info=True)

            detailed_results_log.append({
                "description": test_description,
                "input": generated_input_value,
                "passed": current_test_passed,
                "output": current_test_output,
                "error": current_test_error
            })

            if not current_test_passed:
                all_system_tests_passed = False
                final_submission_message = f"Failed on {test_description}. Details: {current_test_error or 'Output did not match.'}"
                logger.warning(f"EID {exercise_id}, UID {user_id}: Submission failed on {test_description}.")
                break # Stop on first failure for generated tests

        if all_system_tests_passed:
             final_submission_message = f"All {count} generated input tests passed."

    else: # Fallback: No 'generated_inputs' strategy. Use input_data from the user's interactive run.
        test_description = f"Test with user-provided input: '{input_data}'"
        logger.info(f"EID {exercise_id}, UID {user_id}: No 'generated_inputs' strategy. {test_description}")

        if validation_rules.get("requires_input_function") and input_data is None:
            logger.warning(f"EID {exercise_id}, UID {user_id}: Exercise requires input, but no input_data from UI and no generation strategy. This may lead to failure if validator expects input.")
            # The execution-service will handle None input as per its logic (e.g., empty string for stdin)

        execution_payload = {
            "exercise_id": exercise_id,
            "code": code_submitted,
            "input_data": input_data # This is from the textarea
        }
        current_test_passed = False
        current_test_output = ""
        current_test_error = ""

        try:
            response = httpx.post(f"{EXECUTION_SERVICE_URL}/execute", json=execution_payload, timeout=15.0)
            response.raise_for_status()
            exec_result = response.json()
            current_test_passed = exec_result.get("passed", False)
            current_test_output = exec_result.get("output", "")
            current_test_error = exec_result.get("error", "")
            representative_output_for_db = current_test_output

        except httpx.RequestError as e:
            current_test_error = f"Error connecting to execution service: {e}"
            logger.error(f"{test_description} - {current_test_error}")
        except httpx.HTTPStatusError as e:
            current_test_error = f"Execution service error: {e.response.status_code}"
            try: current_test_error += f" - {e.response.json().get('error', 'Unknown execution error')}"
            except: pass
            logger.error(f"{test_description} - {current_test_error}")
        except Exception as e:
            current_test_error = f"Unexpected error during execution: {e}"
            logger.error(f"{test_description} - {current_test_error}", exc_info=True)

        all_system_tests_passed = current_test_passed

    # --- Common post-submission actions ---

    # Update UserExerciseSubmission record
    submission_record = db.query(UserExerciseSubmission).filter(
        UserExerciseSubmission.user_id == user_id,
        UserExerciseSubmission.exercise_id == exercise_id
    ).first()

    if not submission_record:
    # Create a new submission record
        submission_record = UserExerciseSubmission(
            user_id=user_id,
            exercise_id=exercise_id,
            lesson_id=exercise.lesson_id,
            code_submitted=code_submitted,
            is_correct=all_system_tests_passed,
            output=representative_output_for_db,
            error_message=current_test_error if not all_system_tests_passed else None,
            feedback=None,
            attempt_number=1,  # <-- Always set to 1 on creation
            submitted_at=dt.utcnow(),
            passed=all_system_tests_passed,
            # ...
        )
        db.add(submission_record)
    else:
        # Update with the latest results
        submission_record.is_correct = all_system_tests_passed
        submission_record.output = representative_output_for_db
        submission_record.error_message = current_test_error if not all_system_tests_passed else None
        submission_record.code_submitted = code_submitted
        submission_record.submitted_at = dt.utcnow()
        # --- FIX: handle None case ---
        if submission_record.attempt_number is None:
            submission_record.attempt_number = 2
        else:
            submission_record.attempt_number += 1

    # Commit changes to UserExerciseSubmission
    try:
        db.commit()
        db.refresh(submission_record)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating submission record for User ID {user_id}, Exercise ID {exercise_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update submission record.")

    # --- NEW: If this is an exam exercise and passed, mark the exam module as completed ---
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if exercise and exercise.validation_type == "exam" and submission_record.is_correct:
        # Find the exam module for this course
        exam_module = db.query(Module).filter(
            Module.course_id == exercise.course_id,
            Module.is_exam == True
        ).first()
        if exam_module:
            # Mark UserModuleProgress as completed for the exam module
            ump = db.query(UserModuleProgress).filter(
                UserModuleProgress.user_id == user_id,
                UserModuleProgress.module_id == exam_module.id
            ).first()
            if not ump:
                ump = UserModuleProgress(
                    user_id=user_id,
                    module_id=exam_module.id,
                    started_at=dt.utcnow(),
                    is_completed=True,
                    completed_at=dt.utcnow()
                )
                db.add(ump)
            elif not ump.is_completed:
                ump.is_completed = True
                ump.completed_at = dt.utcnow()
                db.add(ump)
            db.commit()
            _check_and_update_course_completion(db, user_id, exercise.course_id) # Ensure course completion is checked
            logger.info(f"User {user_id} completed exam module {exam_module.id} for course {exercise.course_id}.")

    _check_and_update_lesson_completion(db, user_id, exercise.lesson_id)
    _check_and_update_module_completion(db, user_id, exercise.lesson.module_id) # Ensure module completion is checked
    db.commit()
    logger.info(f"User ID {user_id}, Exercise ID {exercise_id}: Submission processed. Passed: {all_system_tests_passed}.")
    lesson = db.query(Lesson).filter(Lesson.id == exercise.lesson_id).first()
    if lesson:
        # Get all lessons in the module, ordered
        lessons_in_module = db.query(Lesson).filter(Lesson.module_id == lesson.module_id).order_by(Lesson.order_index).all()
        if lessons_in_module:
            last_lesson = lessons_in_module[-1]
            if lesson.id == last_lesson.id:
                # Get all exercises in the last lesson, ordered
                exercises_in_lesson = db.query(Exercise).filter(Exercise.lesson_id == last_lesson.id).order_by(Exercise.order_index).all()
                if exercises_in_lesson:
                    last_exercise = exercises_in_lesson[-1]
                    if exercise.id == last_exercise.id and all_system_tests_passed:
                        # Only now check and update module completion
                        _check_and_update_module_completion(db, user_id, lesson.module_id)
                        db.commit()
    return submission_record

def get_batch_module_progress_details(db: Session, user_id: int, module_ids: list[int]) -> dict:
    """
    Returns a dictionary mapping module_id to the full progress object for the given user.
    """
    progress_records = db.query(UserModuleProgress).filter(
        UserModuleProgress.user_id == user_id,
        UserModuleProgress.module_id.in_(module_ids)
    ).all()
    progress_map = {}
    for mid in module_ids:
        record = next((r for r in progress_records if r.module_id == mid), None)
        if record:
            # Calculate progress percentage based on completed lessons
            total_lessons = db.query(func.count(Lesson.id)).filter(Lesson.module_id == mid).scalar() or 0
            completed_lessons = 0
            if total_lessons > 0:
                completed_lessons = db.query(func.count(UserLessonProgress.id)).filter(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.lesson.has(Lesson.module_id == mid),
                    UserLessonProgress.is_completed == True
                ).scalar() or 0
            progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0.0

            progress_map[mid] = {
                "id": record.id,
                "user_id": record.user_id,
                "module_id": record.module_id,
                "is_started": record.started_at is not None,
                "is_completed": record.is_completed,
                "started_at": record.started_at,
                "completed_at": record.completed_at,
                "current_lesson_id": record.last_accessed_lesson_id,
                "progress_percentage": progress_percentage,
                "is_unlocked": record.is_unlocked,
                "lessons_progress": [],
                "course_id": getattr(record.module, "course_id", None) if hasattr(record, "module") and record.module else None,
            }
        else:
            # Default progress object if not started
            module_info = db.query(Module.course_id).filter(Module.id == mid).first()
            course_id_for_default = module_info.course_id if module_info else None
            progress_map[mid] = {
                "id": -1,
                "user_id": user_id,
                "module_id": mid,
                "is_started": False,
                "is_completed": False,
                "started_at": None,
                "completed_at": None,
                "current_lesson_id": None,
                "progress_percentage": 0.0,
                "is_unlocked": False,
                "lessons_progress": [],
                "course_id": course_id_for_default,
            }
    return progress_map

def get_batch_lesson_progress_details(db: Session, user_id: int, lesson_ids: list[int]) -> dict:
    """
    Returns a dictionary mapping lesson_id to completion status (True/False) for the given user.
    """
    progress_records = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id.in_(lesson_ids)
    ).all()
    progress_map = {lid: False for lid in lesson_ids}
    for record in progress_records:
        progress_map[record.lesson_id] = bool(record.is_completed)
    return progress_map

def update_last_accessed(db: Session, user_id: int, course_id: int, module_id: int = None, lesson_id: int = None):
    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    enrollment.last_accessed = dt.utcnow()
    if module_id:
        enrollment.last_accessed_module_id = module_id
    if lesson_id:
        enrollment.last_accessed_lesson_id = lesson_id
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment

def start_module(db: Session, user_id: int, module_id: int):
    module_progress = db.query(UserModuleProgress).filter(
        UserModuleProgress.user_id == user_id,
        UserModuleProgress.module_id == module_id
    ).first()

    if not module_progress:
        # This case should ideally be handled by enroll_user_in_course creating all entries.
        # If it's missing, it implies an issue or the module isn't part of the user's current enrollment scope.
        # However, to be robust, we can create it here, but it should be marked as locked unless it's the first.
        # For simplicity, we'll assume `enroll_user_in_course` has done its job.
        # If not, we might need to check if it's the first module of the course to unlock it.
        logger.warning(f"UserModuleProgress not found for User ID {user_id}, Module ID {module_id} in start_module. This should have been created on enrollment.")
        # To prevent error, let's create a basic one, assuming it should be locked by default if created ad-hoc.
        # A better approach is to ensure enroll_user_in_course is robust.
        module_info = db.query(Module.course_id, Module.order_index).filter(Module.id == module_id).first()
        if not module_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found.")

        is_first_module_of_course = (module_info.order_index == 1) # Simplified check

        module_progress = UserModuleProgress(
            user_id=user_id,
            module_id=module_id,
            started_at=dt.utcnow(),
            is_completed=False,
            is_unlocked=is_first_module_of_course # Unlock if it's the first, otherwise default to locked
        )
        db.add(module_progress)
        # Ensure the user is enrolled in the course this module belongs to
        enrollment = db.query(UserCourseEnrollment).filter(
            UserCourseEnrollment.user_id == user_id,
            UserCourseEnrollment.course_id == module_info.course_id,
            UserCourseEnrollment.is_active_enrollment == True
        ).first()
        if not enrollment:
            # This is a more critical issue - trying to start a module for a course not enrolled in.
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not enrolled in the course for this module.")

    elif not module_progress.is_unlocked and not module_progress.is_completed:
        # If the module progress exists but is explicitly locked (and not completed)
        logger.warning(f"User ID {user_id} attempting to start locked Module ID {module_id}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Módulo bloqueado. Completa el módulo anterior primero.")

    if module_progress.started_at is None: # Only set started_at if it's the first time
        module_progress.started_at = dt.utcnow()
        db.add(module_progress)

    # Update last accessed on course enrollment
    module_db_instance = db.query(Module).filter(Module.id == module_id).first()
    if module_db_instance:
        enrollment = db.query(UserCourseEnrollment).filter(
            UserCourseEnrollment.user_id == user_id,
            UserCourseEnrollment.course_id == module_db_instance.course_id,
            UserCourseEnrollment.is_active_enrollment == True
        ).first()
        if enrollment:
            enrollment.last_accessed = dt.utcnow()
            enrollment.last_accessed_module_id = module_id
            # last_accessed_lesson_id will be updated when a lesson is started
            db.add(enrollment)
        else:
            logger.error(f"No active enrollment found for User ID {user_id} in Course ID {module_db_instance.course_id} when starting Module ID {module_id}.")


    try:
        db.commit()
        db.refresh(module_progress)
        if enrollment:
            db.refresh(enrollment)
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing start_module for User ID {user_id}, Module ID {module_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not start module.")

    # Construct response based on UserModuleProgressResponse schema
    # This requires fetching course_id and calculating progress_percentage
    course_id_for_response = module_db_instance.course_id if module_db_instance else None

    total_lessons_in_module = db.query(func.count(Lesson.id)).filter(Lesson.module_id == module_id).scalar() or 0
    completed_lessons_count = 0
    if total_lessons_in_module > 0:
        completed_lessons_count = db.query(func.count(UserLessonProgress.id)).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson.has(Lesson.module_id == module_id), # Ensure lesson belongs to this module
            UserLessonProgress.is_completed == True
        ).scalar() or 0

    progress_percentage_val = (completed_lessons_count / total_lessons_in_module * 100) if total_lessons_in_module > 0 else 0

    return UserModuleProgressResponse(
        id=module_progress.id,
        user_id=module_progress.user_id,
        module_id=module_progress.module_id,
        course_id=course_id_for_response,
        is_started=module_progress.started_at is not None,
        is_completed=module_progress.is_completed,
        is_unlocked=module_progress.is_unlocked, # Reflect the current unlock status
        started_at=module_progress.started_at,
        completed_at=module_progress.completed_at,
        current_lesson_id=module_progress.last_accessed_lesson_id,
        progress_percentage=progress_percentage_val,
        lessons_progress=[] # Populate if needed
    )

def complete_module(db: Session, user_id: int, module_id: int):
    module_progress = db.query(UserModuleProgress).filter(
        UserModuleProgress.user_id == user_id,
        UserModuleProgress.module_id == module_id
    ).first()
    if not module_progress:
        raise HTTPException(status_code=404, detail="Module progress not found")
    if not module_progress.is_completed:
        module_progress.is_completed = True
        module_progress.completed_at = dt.utcnow()
        db.add(module_progress)
        db.commit()
        db.refresh(module_progress)

        # Unlock the next module for this user
        current_module = db.query(Module).filter(Module.id == module_id).first()
        if current_module:
            next_module = db.query(Module).filter(
                Module.course_id == current_module.course_id,
                Module.order_index > current_module.order_index
            ).order_by(Module.order_index.asc()).first()
            if next_module:
                next_progress = db.query(UserModuleProgress).filter(
                    UserModuleProgress.user_id == user_id,
                    UserModuleProgress.module_id == next_module.id
                ).first()
                if not next_progress:
                    next_progress = UserModuleProgress(
                        user_id=user_id,
                        module_id=next_module.id,
                        started_at=None,
                        is_completed=False,
                        is_unlocked=True  # <-- Unlock here
                    )
                    db.add(next_progress)
                    db.commit()
    return module_progress

def get_user_module_progress(db: Session, user_id: int, module_id: int) -> Optional[UserModuleProgressResponse]:
    db.expire_all()

    module_progress = db.query(UserModuleProgress).filter(
        UserModuleProgress.user_id == user_id,
        UserModuleProgress.module_id == module_id
    ).first()

    if not module_progress:
        total_lessons_in_module = db.query(func.count(Lesson.id)).filter(Lesson.module_id == module_id).scalar() or 0
        return UserModuleProgressResponse(
            id=-1, # Or some indicator it's a default
            user_id=user_id,
            module_id=module_id,
            is_completed=False,
            started_at=None,
            completed_at=None,
            last_accessed_lesson_id=None,
            progress_percentage=0.0,
            # You might need course_id and lessons_progress if your schema demands it for default
            course_id=db.query(Module.course_id).filter(Module.id == module_id).scalar(), # Fetch course_id
            lessons_progress=[] # Default empty
        )
    db.refresh(module_progress)  # Ensure Module is refreshed to get latest data

    # Calculate progress percentage
    total_lessons_in_module = db.query(func.count(Lesson.id)).filter(Lesson.module_id == module_id).scalar() or 0

    completed_lessons_count = 0
    if total_lessons_in_module > 0:
        completed_lessons_count = db.query(func.count(UserLessonProgress.id)).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id.in_(
                db.query(Lesson.id).filter(Lesson.module_id == module_id)
            ),
            UserLessonProgress.is_completed == True
        ).scalar() or 0

    progress_percentage = (completed_lessons_count / total_lessons_in_module * 100) if total_lessons_in_module > 0 else 0

    # Fetch course_id for the response schema
    module_info = db.query(Module.course_id).filter(Module.id == module_id).first()
    course_id_for_response = module_info.course_id if module_info else None

    # Potentially fetch detailed lesson progress if UserModuleProgressResponse needs it
    # For now, focusing on the module's overall percentage
    detailed_lessons_progress = [] # Populate if your schema needs it

    return UserModuleProgressResponse(
        id=module_progress.id,
        user_id=module_progress.user_id,
        module_id=module_progress.module_id,
        course_id=course_id_for_response, # Add course_id
        is_started=module_progress.started_at is not None, # Add is_started
        is_completed=module_progress.is_completed,
        is_unlocked=True, # This might need more complex logic if modules can be locked
        started_at=module_progress.started_at,
        completed_at=module_progress.completed_at,
        current_lesson_id=module_progress.last_accessed_lesson_id, # map to current_lesson_id
        progress_percentage=progress_percentage,
        lessons_progress=detailed_lessons_progress # Add lessons_progress
    )

def complete_lesson(db: Session, user_id: int, lesson_id: int):
    lesson_progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == lesson_id
    ).first()
    if not lesson_progress:
        lesson_progress = UserLessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            started_at=dt.utcnow(),
            is_completed=True,
            completed_at=dt.utcnow()
        )
        db.add(lesson_progress)
    else:
        if not lesson_progress.is_completed:
            lesson_progress.is_completed = True
            lesson_progress.completed_at = dt.utcnow()
            db.add(lesson_progress)
    db.commit()
    db.refresh(lesson_progress)
    return lesson_progress

def get_course_exam(db: Session, course_id: int):
    return db.query(CourseExam).filter(CourseExam.course_id == course_id).first()

def start_exam_attempt(db: Session, user_id: int, exam_id: int):
    attempt = UserExamAttempt(
        user_id=user_id,
        exam_id=exam_id,
        started_at=dt.utcnow(),
        is_completed=False
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt

def submit_exam_attempt(db: Session, user_id: int, attempt_id: int, answers: dict):
    attempt = db.query(UserExamAttempt).filter(
        UserExamAttempt.id == attempt_id,
        UserExamAttempt.user_id == user_id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Exam attempt not found")
    if attempt.is_completed:
        raise HTTPException(status_code=400, detail="Attempt already submitted")
    attempt.answers = answers
    attempt.completed_at = dt.utcnow()
    attempt.is_completed = True
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt

def get_user_exam_attempts(db: Session, user_id: int, exam_id: int):
    return db.query(UserExamAttempt).filter(
        UserExamAttempt.user_id == user_id,
        UserExamAttempt.exam_id == exam_id
    ).all()

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
    """Get detailed progress summary for a course, including exam status."""
    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()

    if not enrollment:
        # This will be handled by the frontend if useCourseAccess returns null/undefined
        # For direct API calls, a 404 might be appropriate if the endpoint expects it.
        # For now, let's assume the calling context handles a missing enrollment.
        # If called by an endpoint that should 404, raise HTTPException here.
        # raise HTTPException(status_code=404, detail="User not enrolled in this course")
        # Returning None or an empty dict might be better if the frontend expects to check for it.
        # For consistency with UserEnrollmentWithProgressResponse, let's prepare for a potential 404 if no enrollment.
        # However, the frontend's useCourseAccess().getCourseProgress() likely handles null.
        # The original code raised HTTPException, so we'll keep that behavior if no enrollment.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not enrolled in this course")


    total_lessons = db.query(Lesson).join(Module).filter(Module.course_id == course_id).count()
    completed_lessons_count = db.query(UserLessonProgress).join(Lesson).join(Module).filter(
        Module.course_id == course_id,
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.is_completed == True
    ).count()

    # --- Progress Percentage Calculation with Exam ---
    # Define how much lessons and exam contribute.
    # For example, lessons up to 90%, exam the final 10%.
    LESSONS_MAX_CONTRIBUTION = 90.0
    EXAM_CONTRIBUTION = 10.0

    current_lesson_progress_pct = 0.0
    if total_lessons > 0:
        current_lesson_progress_pct = (completed_lessons_count / total_lessons) * LESSONS_MAX_CONTRIBUTION

    # If all lessons are completed (based on enrollment.is_completed flag, which means all modules are done)
    # ensure lesson progress contribution is at its max.
    if enrollment.is_completed:
        current_lesson_progress_pct = LESSONS_MAX_CONTRIBUTION

    final_progress_percentage = current_lesson_progress_pct
    exam_passed_for_progress = False

    # Check for exam and its completion status
    exam_exercise_for_course = db.query(Exercise).filter(
        Exercise.course_id == course_id,
        Exercise.validation_type == "exam"
    ).first()

    if exam_exercise_for_course:
        exam_submission = db.query(UserExerciseSubmission).filter(
            UserExerciseSubmission.user_id == user_id,
            UserExerciseSubmission.exercise_id == exam_exercise_for_course.id,
            UserExerciseSubmission.is_correct == True # Assuming is_correct means passed
        ).first()
        if exam_submission:
            exam_passed_for_progress = True
            # Add exam contribution only if all lessons are also considered complete
            if enrollment.is_completed:
                final_progress_percentage += EXAM_CONTRIBUTION

    # Cap progress at 100%
    final_progress_percentage = min(round(final_progress_percentage, 2), 100.0)

    # Determine true course completion (all lessons/modules AND exam if it exists)
    is_truly_course_completed = enrollment.is_completed and (not exam_exercise_for_course or exam_passed_for_progress)

    return {
        "course_id": course_id,
        "user_id": user_id,
        "completed_lessons": completed_lessons_count,
        "total_lessons": total_lessons,
        # "completed_exercises": completed_exercises, # You can re-add if needed
        # "total_exercises": total_exercises,       # You can re-add if needed
        "progress_percentage": final_progress_percentage,
        "is_course_completed": is_truly_course_completed, # This now reflects overall completion including exam
        "exam_unlocked": enrollment.exam_unlocked, # CRITICAL: Pass the flag from the enrollment record
        "exam_passed": exam_passed_for_progress, # Useful for UI to know if exam itself was passed
        "last_accessed": enrollment.last_accessed,
        "last_accessed_module_id": enrollment.last_accessed_module_id,
        "last_accessed_lesson_id": enrollment.last_accessed_lesson_id,
        # Ensure all fields expected by UserEnrollmentWithProgressResponse are here if this dict
        # is directly used to create an instance of it.
        "id": enrollment.id, # from UserCourseEnrollment
        "enrollment_date": enrollment.enrollment_date, # from UserCourseEnrollment
        "total_time_spent_minutes": enrollment.total_time_spent_minutes # from UserCourseEnrollment
    }

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
    return

def get_user_lesson_progress_detail(db: Session, user_id: int, lesson_id: int) -> Optional[LessonProgressDetailResponse]:
    lesson_progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == lesson_id
    ).first()

    if not lesson_progress:
        logger.info(f"No UserLessonProgress found for User ID {user_id}, Lesson ID {lesson_id}. Lesson not started by user.")
        return LessonProgressDetailResponse(
            lesson_id=lesson_id,  # Always use the path param, which is an int
            is_completed=False,
            started_at=None,
            completed_at=None,
            exercises_progress=[]
        )
    # ... rest of your logic ...

    # Fetch exercises for the lesson
    lesson_exercises = db.query(Exercise).filter(Exercise.lesson_id == lesson_id).order_by(Exercise.order_index).all()

    exercises_progress_info_list: List[ExerciseProgressInfo] = []
    for exercise_entity in lesson_exercises:
        # Get the latest submission for this exercise by the user
        latest_submission = db.query(UserExerciseSubmission).filter(
            UserExerciseSubmission.user_id == user_id,
            UserExerciseSubmission.exercise_id == exercise_entity.id
        ).order_by(UserExerciseSubmission.submitted_at.desc()).first()

        exercises_progress_info_list.append(
            ExerciseProgressInfo(
                exercise_id=exercise_entity.id,
                title=exercise_entity.title, # Assuming ExerciseProgressInfo has a title field
                is_correct=latest_submission.is_correct if latest_submission else None,
                attempts=int(latest_submission.attempt_number) if (latest_submission and latest_submission.attempt_number is not None) else 0,
                last_submitted_at=latest_submission.submitted_at if latest_submission else None
                # Add other fields to ExerciseProgressInfo as needed and populate them here
            )
        )

    logger.info(f"get_user_lesson_progress_detail for User ID {user_id}, Lesson ID {lesson_id} - DB value for lesson_progress.is_completed: {lesson_progress.is_completed}")
    return LessonProgressDetailResponse(
        lesson_id=lesson_progress.lesson_id,
        is_completed=lesson_progress.is_completed,
        started_at=lesson_progress.started_at,
        completed_at=lesson_progress.completed_at,
        exercises_progress=exercises_progress_info_list # Pass the populated list
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
def change_user_username(db: Session, user: User, new_username: str):
    # Check if username is already taken
    existing = db.query(User).filter(User.username == new_username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Nombre de usuario ya registrado")
    user.username = new_username
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"detail": "Nombre de usuario actualizado correctamente"}

def change_user_password(db: Session, user: User, current_password: str, new_password: str):
    from utils import verify_password, get_password_hash
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
    if verify_password(new_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="La nueva contraseña no puede ser igual a la anterior")
    user.hashed_password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"detail": "Contraseña actualizada correctamente"}
def create_user_exam_attempt(db, user_id, exam_id, answers):
    exam = db.query(CourseExam).filter_by(id=exam_id).first()
    if not exam:
        raise Exception("Exam not found")
    questions = db.query(ExamQuestion).filter_by(exam_id=exam_id).order_by(ExamQuestion.order_index).all()
    correct = 0
    for q in questions:
        if str(answers.get(str(q.id))) == str(q.correct_answer.get("value")):
            correct += 1
    percent = (correct / len(questions)) * 100 if questions else 0
    passed = percent >= exam.pass_threshold_percentage
    attempt = UserExamAttempt(
        user_id=user_id,
        exam_id=exam_id,
        answers=answers,
        passed=passed
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt

def can_unlock_next_course(db, user_id, current_course_id):
    # 1. Check if current course is completed
    enrollment = db.query(UserCourseEnrollment).filter_by(
        user_id=user_id,
        course_id=current_course_id,
        is_completed=True
    ).first()
    if not enrollment:
        return False

    # 2. Find the next course (by id or order)
    next_course = db.query(Course).filter(Course.id > current_course_id).order_by(Course.id.asc()).first()
    if not next_course:
        return False

    already_enrolled = db.query(UserCourseEnrollment).filter_by(
        user_id=user_id,
        course_id=next_course.id
    ).first()
    return not already_enrolled

def recalculate_and_update_course_progress(db: Session, user_id: int, course_id: int):
    """
    Recalculates the course progress percentage and updates the UserCourseEnrollment record.
    """
    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id,
        UserCourseEnrollment.is_active_enrollment == True
    ).first()
    if not enrollment:
        logger.warning(f"User ID {user_id}, Course ID {course_id}: No active enrollment found in recalculate_and_update_course_progress.")
        return

    total_lessons = db.query(Lesson).join(Module).filter(Module.course_id == course_id).count()
    completed_lessons_count = db.query(UserLessonProgress).join(Lesson).join(Module).filter(
        Module.course_id == course_id,
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.is_completed == True
    ).count()

    LESSONS_MAX_CONTRIBUTION = 90.0
    EXAM_CONTRIBUTION = 10.0

    current_lesson_progress_pct = 0.0
    if total_lessons > 0:
        current_lesson_progress_pct = (completed_lessons_count / total_lessons) * LESSONS_MAX_CONTRIBUTION

    if enrollment.is_completed: # If the course is already marked fully complete (e.g. all modules done)
        current_lesson_progress_pct = LESSONS_MAX_CONTRIBUTION

    final_progress_percentage = current_lesson_progress_pct

    exam_exercise_for_course = db.query(Exercise).filter(
        Exercise.course_id == course_id,
        Exercise.validation_type == "exam"
    ).first()

    if exam_exercise_for_course:
        exam_submission = db.query(UserExerciseSubmission).filter(
            UserExerciseSubmission.user_id == user_id,
            UserExerciseSubmission.exercise_id == exam_exercise_for_course.id,
            UserExerciseSubmission.is_correct == True
        ).first()
        # Only add exam contribution if the course's modules are completed (enrollment.is_completed) AND exam is passed
        if exam_submission and enrollment.is_completed:
            final_progress_percentage += EXAM_CONTRIBUTION

    final_progress_percentage = min(round(final_progress_percentage, 2), 100.0)

    if enrollment.progress_percentage != final_progress_percentage:
        enrollment.progress_percentage = final_progress_percentage
        db.add(enrollment)
        logger.info(f"User ID {user_id}, Course ID {course_id}: Staged UserCourseEnrollment.progress_percentage to {final_progress_percentage}.")

def run_exam_code_validation(code_submitted, exercise, input_data=None, timeout=10):
    """
    Calls the execution-service to validate exam code.
    Returns a dict: {"passed": bool, "output": str, "error": str}
    """
    payload = {
        "exercise_id": exercise.id,
        "code": code_submitted,
        "input_data": input_data,
        "timeout": timeout
    }
    try:
        url = f"{EXECUTION_SERVICE_URL}/api/v1/execute"
        response = httpx.post(url, json=payload, timeout=timeout + 2)
        response.raise_for_status()
        data = response.json()
        return {
            "passed": data.get("passed", False),
            "output": data.get("actual_output", ""),
            "error": data.get("message", "") if not data.get("passed", False) else ""
        }
    except httpx.HTTPError as e:
        return {
            "passed": False,
            "output": "",
            "error": f"Error al validar el examen: {str(e)}"
        }
def unlock_next_course_for_user(db, user_id, current_course_id):
    # Find the next course (by ID or order)
    next_course = db.query(Course).filter(Course.id > current_course_id).order_by(Course.id.asc()).first()
    if next_course:
        # Enroll the user or mark as unlocked
        enroll_user_in_course(db, user_id, next_course.id)
        logger.info(f"User {user_id} unlocked next course {next_course.id}.")
