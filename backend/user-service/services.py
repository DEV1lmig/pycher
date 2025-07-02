from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func as sql_func
from sqlalchemy.exc import IntegrityError
import os
import httpx
import logging
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


# Ensure EXECUTION_SERVICE_URL is defined, e.g.:
# EXECUTION_SERVICE_URL = os.getenv("EXECUTION_SERVICE_URL", "http://execution-service:8001")
# For local dev without docker-compose for services:
EXECUTION_SERVICE_URL = os.getenv("EXECUTION_SERVICE_URL", "http://execution-service:8001") # Or your configured URL


# --- Helper functions for cascading completion ---

def _check_and_update_lesson_completion(db: Session, user_id: int, lesson_id: int):
    """
    Checks if all exercises in a lesson are completed by a user. If so, marks the
    lesson as complete and triggers module/course progress updates.
    This is the single source of truth for lesson completion.
    """
    db.flush()
    logger.debug(f"User ID {user_id}, Lesson ID {lesson_id}: Starting _check_and_update_lesson_completion.")
    lesson = db.query(Lesson).options(selectinload(Lesson.module)).filter(Lesson.id == lesson_id).first()
    if not lesson or not lesson.module:
        logger.error(f"Lesson {lesson_id} or its module not found. Cannot update progress.")
        return

    # Ensure a progress record for the lesson exists. It should have been created by start_lesson.
    lesson_progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == lesson_id
    ).first()
    if not lesson_progress:
        logger.error(f"CRITICAL: No UserLessonProgress found for User {user_id}, Lesson {lesson_id}. Cannot mark as complete.")
        return

    # If already complete, do nothing further.
    if lesson_progress.is_completed:
        logger.info(f"User ID {user_id}, Lesson ID {lesson_id}: Lesson already marked as complete.")
        return

    exercise_ids_in_lesson = [e.id for e in db.query(Exercise.id).filter(Exercise.lesson_id == lesson_id).all()]

    all_exercises_correct = True
    if exercise_ids_in_lesson:
        correctly_submitted_count = db.query(UserExerciseSubmission.exercise_id).filter(
            UserExerciseSubmission.user_id == user_id,
            UserExerciseSubmission.exercise_id.in_(exercise_ids_in_lesson),
            UserExerciseSubmission.is_correct == True
        ).distinct().count()
        all_exercises_correct = (correctly_submitted_count == len(exercise_ids_in_lesson))

    # A lesson is complete if it has no exercises OR if all its exercises are correct.
    if all_exercises_correct:
        lesson_progress.is_completed = True
        lesson_progress.completed_at = dt.utcnow()
        db.add(lesson_progress)
        logger.info(f"User ID {user_id}, Lesson ID {lesson_id}: Conditions met. Marking lesson as completed.")

        # --- FIX: The update chain is now linear and correct. ---
        # A lesson completion ONLY triggers a module check. The module check will handle the rest.
        _check_and_update_module_completion(db, user_id, lesson.module_id)
        # REMOVED: recalculate_and_update_course_progress(db, user_id, lesson.module.course_id)
    else:
        logger.info(f"User ID {user_id}, Lesson ID {lesson_id}: Not all exercises are complete. Lesson completion status unchanged.")


def _check_and_update_module_completion(db: Session, user_id: int, module_id: int):
    logger.debug(f"Checking module completion for User ID: {user_id}, Module ID: {module_id}")

    # Flush to see the result of the lesson completion that triggered this call.
    db.flush()

    module = db.query(Module).options(selectinload(Module.course)).filter(Module.id == module_id).first()
    if not module or not module.course:
        logger.warning(f"Module or course not found for module_id={module_id}")
        return

    # --- START: FIX - Define missing variables ---
    course_id = module.course.id

    module_progress = db.query(UserModuleProgress).filter(
        UserModuleProgress.user_id == user_id,
        UserModuleProgress.module_id == module_id
    ).first()

    if not module_progress:
        logger.error(f"CRITICAL: No UserModuleProgress found for User {user_id}, Module {module_id}.")
        return
    # --- END: FIX ---

    lesson_ids_query = db.query(Lesson.id).filter(Lesson.module_id == module_id)
    total_lessons_in_module = lesson_ids_query.count()

    if total_lessons_in_module == 0:
        logger.info(f"Module ID {module_id} has no lessons. Considering it complete.")
        all_completed = True
    else:
        # FIX SAWarning: Pass the query object directly to .in_()
        completed_lessons_count = db.query(UserLessonProgress.id).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id.in_(lesson_ids_query),
            UserLessonProgress.is_completed == True
        ).count()
        all_completed = (completed_lessons_count == total_lessons_in_module)

    logger.debug(f"User ID {user_id}, Module ID {module_id}: Lessons completed: {completed_lessons_count}/{total_lessons_in_module}. All completed: {all_completed}")

    if all_completed and not module_progress.is_completed:
        # --- START: FIX - Mark the module as complete ---
        module_progress.is_completed = True
        module_progress.completed_at = dt.utcnow()
        db.add(module_progress)
        logger.info(f"User {user_id} has completed all lessons for Module {module_id}. Marking module as complete.")

        # Now that this module is complete, check if the entire course is complete
        _check_and_update_course_completion(db, user_id, course_id)
        # --- END: FIX ---
    else:
        # If not all lessons are complete, just recalculate the overall course percentage
        recalculate_and_update_course_progress(db, user_id, course_id)


def _check_and_update_course_completion(db: Session, user_id: int, course_id: int):
    """
    Checks if all modules in a course are completed. If so, unlocks the final exam.
    This function is triggered after a module is completed.
    """
    logger.debug(f"User ID {user_id}, Course ID {course_id}: Starting _check_and_update_course_completion.")

    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id,
        UserCourseEnrollment.is_active == True
    ).first()

    if not enrollment:
        logger.warning(f"User {user_id} has no active enrollment for Course {course_id}. Cannot check course completion.")
        return

    if enrollment.exam_unlocked:
        logger.info(f"User {user_id}, Course {course_id}: Exam already unlocked. Recalculating progress.")
        recalculate_and_update_course_progress(db, user_id, course_id)
        return

    module_ids_in_course_query = db.query(Module.id).filter(Module.course_id == course_id)
    total_modules_in_course = module_ids_in_course_query.count()

    if total_modules_in_course > 0:
        completed_modules_count = db.query(UserModuleProgress.id).filter(
            UserModuleProgress.user_id == user_id,
            UserModuleProgress.module_id.in_(module_ids_in_course_query),
            UserModuleProgress.is_completed == True
        ).count()
        all_modules_completed = (completed_modules_count >= total_modules_in_course)
    else:
        all_modules_completed = True # A course with no modules is considered "ready for exam".

    logger.debug(f"User ID {user_id}, Course ID {course_id}: Modules completed: {completed_modules_count}/{total_modules_in_course}. All completed: {all_modules_completed}")

    if all_modules_completed and not enrollment.exam_unlocked:
        enrollment.exam_unlocked = True
        db.add(enrollment)
        logger.info(f"User {user_id} has completed all modules for Course {course_id}. Exam is now unlocked. Staged for commit.")

    recalculate_and_update_course_progress(db, user_id, course_id)


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

    should_increment_count = False
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
            should_increment_count = True # Mark for incrementing on reactivation
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
        should_increment_count = True # Mark for incrementing on new enrollment
        logger.info(f"Created new enrollment for User ID {user_id} in Course ID {course_id}.")

    # Update students_count on the course if the enrollment was new or reactivated
    course_model = None
    if should_increment_count:
        course_model = db.query(Course).filter(Course.id == course_id).first()
        if course_model:
            course_model.students_count = (course_model.students_count or 0) + 1
            db.add(course_model)
            logger.info(f"Incremented student count for Course ID {course_id}. New count: {course_model.students_count}")

    try:
        db.commit()
        db.refresh(enrollment)
        if should_increment_count and course_model:
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

    # --- MODULE PROGRESS CHECK ---
    module_progress = db.query(UserModuleProgress).filter(
        UserModuleProgress.user_id == user_id,
        UserModuleProgress.module_id == lesson_model_instance.module_id
    ).first()

    if not module_progress:
        logger.error(f"CRITICAL: No UserModuleProgress found for User ID {user_id}, Module ID {lesson_model_instance.module_id} when starting Lesson ID {lesson_id}. This should be created on enrollment.")
        raise HTTPException(status_code=500, detail="Module progress record not found. Please try re-enrolling in the course.")

    if not module_progress.is_unlocked and not module_progress.is_completed:
        logger.warning(f"User ID {user_id} attempted to start a lesson in a locked module (Module ID: {lesson_model_instance.module_id}).")
        raise HTTPException(status_code=403, detail="Module is locked. Complete the previous module to unlock.")


    # --- LESSON PROGRESS HANDLING (ATOMIC GET-OR-CREATE) ---
    # --- FIX: This logic is now robust against race conditions due to the DB constraint ---
    progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == lesson_id
    ).first()

    if not progress:
        try:
            progress = UserLessonProgress(user_id=user_id, lesson_id=lesson_id, started_at=dt.utcnow())
            db.add(progress)
            # We flush here to ensure the record exists before we continue.
            # The commit will happen at the end of the function.
            db.flush()
            logger.info(f"Created new UserLessonProgress for User {user_id}, Lesson {lesson_id}.")
        except IntegrityError:
            # This block handles the race condition. If another request created the record
            # between our .first() check and our .flush(), the DB will raise an IntegrityError.
            # We rollback the failed insert and fetch the record that now exists.
            db.rollback()
            logger.warning(f"Race condition handled: UserLessonProgress for U:{user_id} L:{lesson_id} was created by another request. Fetching existing record.")
            progress = db.query(UserLessonProgress).filter(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.lesson_id == lesson_id
            ).first()
            if not progress:
                # This should be virtually impossible to hit but is good practice.
                logger.error(f"CRITICAL FAILURE: Could not create or find UserLessonProgress for U:{user_id} L:{lesson_id} after IntegrityError.")
                raise HTTPException(status_code=500, detail="Could not initialize lesson progress.")
        except Exception as e:
            db.rollback()
            logger.error(f"An unexpected error occurred while creating UserLessonProgress for U:{user_id} L:{lesson_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Could not initialize lesson progress due to a server error.")


    # --- Proceed with other updates now that we have a 'progress' record ---
    progress.lesson = lesson_model_instance # Ensure relationship is loaded for the response

    # Mark module as started if it's the first time a lesson in it is started
    if module_progress.started_at is None:
        module_progress.started_at = dt.utcnow()
        db.add(module_progress)

    # Update last accessed timestamps
    enrollment.last_accessed = dt.utcnow()
    enrollment.last_accessed_module_id = lesson_model_instance.module_id
    enrollment.last_accessed_lesson_id = lesson_id
    module_progress.last_accessed_lesson_id = lesson_id
    db.add(enrollment)
    db.add(module_progress)

    # --- FIX: Recalculate progress BEFORE committing ---
    # This ensures that any subsequent logic has the most up-to-date percentage.
    recalculate_and_update_course_progress(db, user_id, enrollment.course_id)

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

def finalize_course_completion(db: Session, user_id: int, course_id: int):
    """
    Marks the user's enrollment in a course as completed.
    This effectively "unlocks" the next course for viewing and enrollment.
    NOTE: This function does NOT commit the transaction.
    """
    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()

    if enrollment and not enrollment.is_completed:
        enrollment.is_completed = True
        enrollment.progress_percentage = 100.0
        db.add(enrollment)
        logger.info(f"User {user_id} has completed Course {course_id}. Staged for commit.")
    elif not enrollment:
        logger.warning(f"Could not finalize course completion: No enrollment found for User {user_id} in Course {course_id}.")


def _check_and_unlock_next_course(db: Session, user_id: int, completed_course_id: int):
    """
    Finalizes the completion of a course after all conditions (modules, exam) are met.
    Marking the course as 'is_completed = True' effectively unlocks the next course
    for the frontend's access control logic.
    """
    logger.info(f"User {user_id}, Course {completed_course_id}: Finalizing course completion and checking for next course unlock.")

    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == completed_course_id,
        UserCourseEnrollment.is_active_enrollment == True
    ).first()

    if not enrollment:
        logger.warning(f"User {user_id}, Course {completed_course_id}: Cannot finalize completion, no active enrollment found.")
        return

    # Condition 1: All modules must be complete.
    # The exam_unlocked flag is a good proxy for this, as it's set by _check_and_update_course_completion.
    if not enrollment.exam_unlocked:
        logger.warning(f"User {user_id}, Course {completed_course_id}: Cannot finalize, not all modules are complete (exam not unlocked).")
        return

    # Condition 2: The course's exam (if it exists) must be passed.
    exam_exercise = db.query(Exercise).filter(
        Exercise.course_id == completed_course_id,
        Exercise.validation_type == "exam"
    ).first()

    if exam_exercise:
        exam_submission = db.query(UserExerciseSubmission).filter(
            UserExerciseSubmission.user_id == user_id,
            UserExerciseSubmission.exercise_id == exam_exercise.id,
            UserExerciseSubmission.is_correct == True
        ).first()
        if not exam_submission:
            logger.warning(f"User {user_id}, Course {completed_course_id}: Cannot finalize, exam exercise {exam_exercise.id} has not been passed.")
            return

    # All conditions met. Finalize the course completion.
    if not enrollment.is_completed:
        enrollment.is_completed = True
        enrollment.progress_percentage = 100.0 # Ensure percentage is maxed out
        enrollment.completed_at = dt.utcnow()
        db.add(enrollment)
        logger.info(f"SUCCESS: User {user_id} has officially completed Course {completed_course_id}. Next course is now accessible.")
    else:
        logger.info(f"User {user_id}, Course {completed_course_id}: Course was already marked as complete.")


def complete_exercise(db: Session, user_id: int, exercise_id: int, code_submitted: str, input_data: Optional[str] = None):
    logger.info(f"Attempting to complete exercise ID {exercise_id} for user ID {user_id}.")

    # Eagerly load relationships that might be needed
    exercise = db.query(Exercise).options(
        selectinload(Exercise.lesson).selectinload(Lesson.module)
    ).filter(Exercise.id == exercise_id).first()

    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    # --- START: REFACTORED VALIDATION ---
    # Validate based on the type of exercise
    if exercise.validation_type == "exam":
        if not exercise.course_id:
            raise HTTPException(status_code=500, detail="Exam exercise is not properly linked to a course.")
    else: # Default case for regular lesson exercises
        if not exercise.lesson or not exercise.lesson.module:
            raise HTTPException(status_code=500, detail="Lesson exercise is not properly linked to a lesson and module.")

        # --- FIX: Ensure the lesson is marked as started before proceeding ---
        try:
            logger.info(f"Ensuring lesson {exercise.lesson_id} is started for user {user_id} before completing exercise.")
            start_lesson(db=db, user_id=user_id, lesson_id=exercise.lesson_id)
        except HTTPException as e:
            # If start_lesson fails (e.g., module locked), propagate the error
            logger.error(f"Failed to start lesson {exercise.lesson_id} during exercise completion for user {user_id}. Detail: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while trying to start lesson {exercise.lesson_id} for user {user_id}. Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Could not ensure lesson is started.")
    # --- END: REFACTORED VALIDATION ---

    # --- START: Call Execution Service ---
    logger.info(f"Calling execution service for exercise {exercise_id} for user {user_id}")
    payload = {
        "exercise_id": exercise.id,
        "code": code_submitted,
        "input_data": input_data,  # This will be None for submissions, which is correct
        "timeout": 10  # A reasonable default timeout
    }
    try:
        url = f"{EXECUTION_SERVICE_URL}/execute"
        # The execution service might take a moment, so a slightly longer timeout for the request itself is wise.
        with httpx.Client(timeout=12.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses

        result_data = response.json()
        all_system_tests_passed = result_data.get("passed", False)
        # Use 'output' from the response model which maps to 'actual_output'
        representative_output_for_db = result_data.get("output", "")
        # Use 'error' from the response model which maps to 'message'
        current_test_error = result_data.get("error", "") if not all_system_tests_passed else ""
        logger.info(f"Execution service response for EID {exercise_id}: Passed={all_system_tests_passed}")

    except httpx.HTTPStatusError as e:
        logger.error(f"Execution service returned an error status {e.response.status_code} for EID {exercise_id}. Response: {e.response.text}", exc_info=True)
        all_system_tests_passed = False
        representative_output_for_db = e.response.text
        current_test_error = f"Error de validación: El servicio de ejecución devolvió un error ({e.response.status_code})."
    except httpx.RequestError as e:
        logger.error(f"Could not connect to execution service at {EXECUTION_SERVICE_URL}. Error: {e}", exc_info=True)
        all_system_tests_passed = False
        representative_output_for_db = ""
        current_test_error = "Error de validación: No se pudo conectar con el servicio de ejecución. Por favor, inténtalo de nuevo más tarde."
    except Exception as e:
        logger.error(f"An unexpected error occurred during execution service call for EID {exercise_id}. Error: {e}", exc_info=True)
        all_system_tests_passed = False
        representative_output_for_db = ""
        current_test_error = "Error de validación: Ocurrió un error inesperado durante la validación del código."
    # --- END: Call Execution Service ---

    submission_record = db.query(UserExerciseSubmission).filter(
        UserExerciseSubmission.user_id == user_id,
        UserExerciseSubmission.exercise_id == exercise_id
    ).first()

    if not submission_record:
        # For lesson exercises, link the submission to the lesson for easier querying
        lesson_id_for_submission = exercise.lesson_id if exercise.validation_type != "exam" else None
        submission_record = UserExerciseSubmission(user_id=user_id, exercise_id=exercise_id, lesson_id=lesson_id_for_submission, attempt_number=1)
    else:
        submission_record.attempt_number = (submission_record.attempt_number or 0) + 1

    submission_record.code_submitted = code_submitted
    submission_record.is_correct = all_system_tests_passed
    submission_record.output = representative_output_for_db
    submission_record.error_message = current_test_error if not all_system_tests_passed else None
    submission_record.submitted_at = dt.utcnow()
    submission_record.passed = all_system_tests_passed

    db.add(submission_record)

    # Handle exam attempt state specifically
    if exercise.validation_type == "exam":
        active_attempt = db.query(UserExamAttempt).filter(
            UserExamAttempt.user_id == user_id,
            UserExamAttempt.exercise_id == exercise_id,
            UserExamAttempt.is_active == True
        ).first()

        if active_attempt:
            if not all_system_tests_passed:
                active_attempt.failure_count += 1
            else:
                active_attempt.passed = True
                active_attempt.is_active = False
                active_attempt.completed_at = dt.utcnow()
            db.add(active_attempt)

    # If the exercise is correct, trigger the correct cascade of progress updates.
    if all_system_tests_passed:
        # --- START: FIX for module exam completion ---
        # This logic now correctly handles all three types of exercises.

        # 1. Regular lesson exercise
        if exercise.lesson_id is not None:
            logger.info(f"Correct submission for lesson exercise {exercise.id}. Triggering lesson completion check for lesson {exercise.lesson_id}.")
            _check_and_update_lesson_completion(db, user_id, exercise.lesson_id)

        # 2. Module-level exam
        elif exercise.module_id is not None and exercise.lesson_id is None:
            logger.info(f"Correct submission for module exam {exercise.id}. Triggerging module completion check for module {exercise.module_id}.")
            _check_and_update_module_completion(db, user_id, exercise.module_id)

        # 3. Course-level (final) exam
        elif exercise.course_id is not None and exercise.module_id is None and exercise.lesson_id is None:
            logger.info(f"Correct submission for final course exam {exercise.id}. Finalizing course completion for course {exercise.course_id}.")
            _finalize_course_completion(db, user_id, exercise.course_id)
            # Note: The logic to unlock the *next* course can be added here if needed.

    db.commit()
    db.refresh(submission_record)

    return submission_record, result_data


def _finalize_course_completion(db: Session, user_id: int, course_id: int):
    """
    Marks a course as fully completed for a user.
    This is triggered after the user successfully passes the final exam.
    """
    logger.info(f"Finalizing course completion for User {user_id}, Course {course_id}.")

    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()

    if not enrollment:
        logger.error(f"CRITICAL: Could not find enrollment for User {user_id} in Course {course_id} to finalize completion.")
        return

    if not enrollment.is_completed:
        enrollment.is_completed = True
        enrollment.progress_percentage = 100.0
        enrollment.completed_at = dt.utcnow()
        db.add(enrollment)
        logger.info(f"Enrollment for User {user_id}, Course {course_id} marked as complete with 100% progress.")
    else:
        logger.warning(f"Attempted to finalize course {course_id} for user {user_id}, but it was already marked as complete.")


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
            total_lessons = db.query(sql_func.count(Lesson.id)).filter(Lesson.module_id == mid).scalar() or 0
            completed_lessons = 0
            if total_lessons > 0:
                completed_lessons = db.query(sql_func.count(UserLessonProgress.id)).filter(
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

    total_lessons_in_module = db.query(sql_func.count(Lesson.id)).filter(Lesson.module_id == module_id).scalar() or 0
    completed_lessons_count = 0
    if total_lessons_in_module > 0:
        completed_lessons_count = db.query(sql_func.count(UserLessonProgress.id)).filter(
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

# --- REMOVED FUNCTION ---
# The complete_module function has been removed. Module completion is now handled
# exclusively by the _check_and_update_module_completion helper function, which is
# triggered automatically when a lesson is completed. This ensures data integrity.

def get_user_module_progress(db: Session, user_id: int, module_id: int) -> Optional[UserModuleProgressResponse]:
    db.expire_all()

    module_progress = db.query(UserModuleProgress).filter(
        UserModuleProgress.user_id == user_id,
        UserModuleProgress.module_id == module_id
    ).first()

    if not module_progress:
        total_lessons_in_module = db.query(sql_func.count(Lesson.id)).filter(Lesson.module_id == module_id).scalar() or 0
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
    total_lessons_in_module = db.query(sql_func.count(Lesson.id)).filter(Lesson.module_id == module_id).scalar() or 0

    completed_lessons_count = 0
    if total_lessons_in_module > 0:
        completed_lessons_count = db.query(sql_func.count(UserLessonProgress.id)).filter(
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

# --- REMOVED FUNCTION ---
# The complete_lesson function has been removed to prevent inconsistent state.
# All lesson completions should now flow through the _check_and_update_lesson_completion helper.

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not enrolled in this course")

    total_lessons = db.query(Lesson).join(Module).filter(Module.course_id == course_id).count()
    completed_lessons_count = db.query(UserLessonProgress).join(Lesson).join(Module).filter(
        Module.course_id == course_id,
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.is_completed == True
    ).count()

    total_exercises = db.query(Exercise).join(Lesson).join(Module).filter(Module.course_id == course_id).count()
    completed_exercises = db.query(UserExerciseSubmission).join(Exercise).join(Lesson).join(Module).filter(
        Module.course_id == course_id,
        UserExerciseSubmission.user_id == user_id,
        UserExerciseSubmission.is_correct == True
    ).count()

    LESSONS_MAX_CONTRIBUTION = 90.0
    EXAM_CONTRIBUTION = 10.0

    current_lesson_progress_pct = 0.0
    if total_lessons > 0:
        current_lesson_progress_pct = (completed_lessons_count / total_lessons) * LESSONS_MAX_CONTRIBUTION

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
            UserExerciseSubmission.is_correct == True
        ).first()
        if exam_submission:
            exam_passed_for_progress = True
            if enrollment.is_completed:
                final_progress_percentage += EXAM_CONTRIBUTION

    # Cap progress at 100%
    final_progress_percentage = min(round(final_progress_percentage, 2), 100.0)

    # --- CRITICAL: Unambiguous course completion flag ---
    # True only if all modules are complete AND (if exam exists, it is passed)
    is_truly_course_completed = bool(enrollment.is_completed and (not exam_exercise_for_course or exam_passed_for_progress))

    return {
        "course_id": course_id,
        "user_id": user_id,
        "completed_lessons": completed_lessons_count,
        "total_lessons": total_lessons,
        "completed_exercises": completed_exercises,
        "total_exercises": total_exercises,
        "progress_percentage": final_progress_percentage,
        "is_course_completed": is_truly_course_completed,  # <-- Use this flag in the frontend!
        "exam_unlocked": enrollment.exam_unlocked,
        "exam_passed": exam_passed_for_progress,
        "last_accessed": enrollment.last_accessed,
        "last_accessed_module_id": enrollment.last_accessed_module_id,
        "last_accessed_lesson_id": enrollment.last_accessed_lesson_id,
        "id": enrollment.id,
        "enrollment_date": enrollment.enrollment_date,
        "total_time_spent_minutes": enrollment.total_time_spent_minutes
    }

def get_user_enrollments_with_progress(db: Session, user_id: int) -> list[UserCourseEnrollment]:
    """
    Retrieves all course enrollments for a given user (both active and inactive),
    including their progress and related course information.
    """
    enrollments = db.query(UserCourseEnrollment).options(
        selectinload(UserCourseEnrollment.course).selectinload(Course.modules).selectinload(Module.lessons).selectinload(Lesson.exercises),
        selectinload(UserCourseEnrollment.course).selectinload(Course.exams)
    ).filter(
        UserCourseEnrollment.user_id == user_id
    ).all()
    logger.info(f"Fetched {len(enrollments)} total enrollments for User ID: {user_id}")
    logger.info(f"Enrollments include active and inactive states. Active enrollments are those with is_active_enrollment=True. {enrollments}")
    return enrollments

def unenroll_user_from_course(db: Session, user_id: int, course_id: int):
    """
    Unenrolls a user from a course by marking their enrollment as inactive,
    resetting their progress, and decrementing the course's student count.
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
        return

    logger.info(f"Starting unenrollment (soft delete) for User ID: {user_id} from Course ID: {course_id}")

    try:
        # Mark enrollment as inactive and reset progress fields
        enrollment.is_active_enrollment = False
        enrollment.is_completed = False
        enrollment.progress_percentage = 0.0
        enrollment.last_accessed = None
        enrollment.last_accessed_module_id = None
        enrollment.last_accessed_lesson_id = None
        db.add(enrollment)

        # Decrement the student count on the corresponding course
        course_model = db.query(Course).filter(Course.id == course_id).first()
        if course_model:
            course_model.students_count = max(0, (course_model.students_count or 0) - 1)
            db.add(course_model)
            logger.info(f"Decremented student count for Course ID {course_id}. New count: {course_model.students_count}")

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
    logger.info(f"get_user_lesson_progress_detail: Called for User ID {user_id}, Lesson ID {lesson_id}")
    lesson_progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == lesson_id
    ).first()

    # --- START: ROBUST FIX for next_lesson_info logic with LOGGING ---
    current_lesson = db.query(Lesson).options(
        selectinload(Lesson.module)
    ).filter(Lesson.id == lesson_id).first()

    if not current_lesson:
        logger.error(f"get_user_lesson_progress_detail: Could not find Lesson with ID {lesson_id}.")
        raise HTTPException(status_code=404, detail="Lesson not found")

    logger.debug(f"Found current lesson: ID {current_lesson.id}, Module ID {current_lesson.module_id}, Order Index {current_lesson.order_index}")

    next_lesson_info = None

    # 1. Try to find the next lesson in the current module
    logger.debug(f"Step 1: Searching for next lesson in Module ID {current_lesson.module_id} with order_index > {current_lesson.order_index}")
    next_lesson_in_module = db.query(Lesson).filter(
        Lesson.module_id == current_lesson.module_id,
        Lesson.order_index > current_lesson.order_index
    ).order_by(Lesson.order_index.asc()).first()

    if next_lesson_in_module:
        logger.info(f"Found next lesson within the same module. Next Lesson ID: {next_lesson_in_module.id}")
        next_lesson_info = {"id": next_lesson_in_module.id, "title": next_lesson_in_module.title}
    else:
        logger.info(f"No subsequent lesson found in Module ID {current_lesson.module_id}. Proceeding to Step 2.")
        # 2. If no next lesson, find the first lesson of the next unlocked module
        logger.debug(f"Step 2: Searching for next module in Course ID {current_lesson.module.course_id} with order_index > {current_lesson.module.order_index}")
        next_module = db.query(Module).filter(
            Module.course_id == current_lesson.module.course_id,
            Module.order_index > current_lesson.module.order_index
        ).order_by(Module.order_index.asc()).first()

        if next_module:
            logger.info(f"Found next module: ID {next_module.id}, Title: '{next_module.title}'. Checking if unlocked for User ID {user_id}.")
            # Check if the user has access to this next module
            next_module_progress = db.query(UserModuleProgress).filter(
                UserModuleProgress.user_id == user_id,
                UserModuleProgress.module_id == next_module.id,
                UserModuleProgress.is_unlocked == True
            ).first()

            if next_module_progress:
                logger.info(f"Next module (ID: {next_module.id}) is unlocked. Searching for its first lesson.")
                first_lesson_in_next_module = db.query(Lesson).filter(
                    Lesson.module_id == next_module.id
                ).order_by(Lesson.order_index.asc()).first()

                if first_lesson_in_next_module:
                    logger.info(f"Found first lesson in next module. Next Lesson ID: {first_lesson_in_next_module.id}")
                    next_lesson_info = {"id": first_lesson_in_next_module.id, "title": first_lesson_in_next_module.title}
                else:
                    logger.warning(f"Next module (ID: {next_module.id}) is unlocked but contains no lessons.")
            else:
                logger.warning(f"Found next module (ID: {next_module.id}), but it is LOCKED for User ID {user_id}.")
        else:
            logger.info("No subsequent module found in the course. This is the last module.")
    # --- END: ROBUST FIX for next_lesson_info logic with LOGGING ---

    if not lesson_progress:
        logger.info(f"No UserLessonProgress found for User ID {user_id}, Lesson ID {lesson_id}. Lesson not started by user.")
        return LessonProgressDetailResponse(
            lesson_id=lesson_id,
            is_completed=False,
            started_at=None,
            completed_at=None,
            exercises_progress=[],
            next_lesson_info=next_lesson_info # Return next lesson even if current is not started
        )

    # Fetch exercises for the lesson
    lesson_exercises = db.query(Exercise).filter(Exercise.lesson_id == lesson_id).order_by(Exercise.order_index).all()

    exercises_progress_info_list: List[ExerciseProgressInfo] = []
    for exercise_entity in lesson_exercises:
        submission = db.query(UserExerciseSubmission).filter(
            UserExerciseSubmission.user_id == user_id,
            UserExerciseSubmission.exercise_id == exercise_entity.id
        ).order_by(UserExerciseSubmission.submitted_at.desc()).first()

        # --- START: FIX for ValidationError ---
        # The ExerciseProgressInfo schema requires a 'title' and has an 'attempts' field.
        # We need to provide them from the exercise and submission objects.
        exercises_progress_info_list.append(
            ExerciseProgressInfo(
                exercise_id=exercise_entity.id,
                title=exercise_entity.title,
                is_correct=submission.is_correct if submission else False,
                attempts=submission.attempt_number if submission else 0,
                last_submitted_at=submission.submitted_at if submission else None,
                passed=submission.passed if submission else None # <-- ADD THIS LINE
            )
        )
        # --- END: FIX for ValidationError ---

    logger.info(f"get_user_lesson_progress_detail for User ID {user_id}, Lesson ID {lesson_id} - DB value for lesson_progress.is_completed: {lesson_progress.is_completed}")
    return LessonProgressDetailResponse(
        lesson_id=lesson_progress.lesson_id,
        is_completed=lesson_progress.is_completed,
        started_at=lesson_progress.started_at,
        completed_at=lesson_progress.completed_at,
        exercises_progress=exercises_progress_info_list,
        next_lesson_info=next_lesson_info
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
    return UserProgressReportDataSchema(
        user_id=user_id,
        username=user.username,
        email=user.email,
        first_name=getattr(user, "first_name", None),
        last_name=getattr(user, "last_name", None),
        report_generated_at=dt.utcnow(),
        courses=report_courses_data
    )


def change_user_username(db: Session, user: User, new_username: str):
    """
    Changes a user's username after checking for conflicts.
    """
    if user.username == new_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nuevo nombre de usuario no puede ser igual al actual."
        )
    existing_user = db.query(User).filter(User.username == new_username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
                       detail="El nombre de usuario ya está en uso."
        )
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
        url = f"{EXECUTION_SERVICE_URL}/execute"
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



# Define a constant for the failure limit
EXAM_FAILURE_LIMIT = 5

def get_or_create_current_exam_exercise(db: Session, user_id: int, course_id: int):
    """
    Gets the user's active exam exercise for a course.
    If the active attempt has too many failures, or none exists, it assigns a new one.
    **Crucially, it first checks if the user has already passed an exam for this course.**
    """
    # --- START: FIX - Check if the exam is unlocked for the user ---
    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()

    if not enrollment or not enrollment.exam_unlocked:
        logger.warning(f"User {user_id} attempted to access exam for Course {course_id}, but it is not unlocked.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes completar todos los módulos del curso antes de acceder al examen."
        )
    # --- END: FIX ---

    # --- START: CORRECTED FIX - Check UserExamAttempt table for a passed attempt ---
    #  1. Check if the user has any passed attempt for this course.
    already_passed_attempt = db.query(UserExamAttempt).filter(
        UserExamAttempt.user_id == user_id,
        UserExamAttempt.course_id == course_id,
        UserExamAttempt.passed == True
    ).first()

    if already_passed_attempt:
        logger.warning(f"User {user_id} attempted to start a new exam for Course {course_id} but has already passed one (Attempt ID: {already_passed_attempt.id}).")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ya has aprobado el examen para este curso. No puedes comenzar uno nuevo."
        )
    # --- END: CORRECTED FIX ---

    # 2. Look for an existing active attempt for this course
    active_attempt = db.query(UserExamAttempt).filter(
        UserExamAttempt.user_id == user_id,
        UserExamAttempt.course_id == course_id,
        UserExamAttempt.is_active == True
    ).first()

    # 2. If an attempt exists and is within the failure limit, return its exercise
    if active_attempt and active_attempt.failure_count < EXAM_FAILURE_LIMIT:
        logger.info(f"Returning existing active exam (Exercise ID: {active_attempt.exercise_id}) for User {user_id}.")
        return db.query(Exercise).filter(Exercise.id == active_attempt.exercise_id).first()

    # 3. If attempt exists but has too many failures, deactivate it
    if active_attempt:
        logger.warning(f"Deactivating exam attempt {active_attempt.id} for User {user_id} due to reaching failure limit ({active_attempt.failure_count} failures).")
        active_attempt.is_active = False
        db.add(active_attempt)

    # 4. Fetch a new random exercise for the course
    logger.info(f"Fetching a new random exam for User {user_id}, Course {course_id}.")

    new_exam_exercise = db.query(Exercise).filter(
        Exercise.course_id == course_id,
        Exercise.module_id == None,
        Exercise.lesson_id == None,
        Exercise.validation_type == 'exam'
    ).order_by(sql_func.random()).first()

    if not new_exam_exercise:
        raise HTTPException(status_code=404, detail="No exam exercises found for this course.")

    # Find the corresponding CourseExam for this course.
    course_exam = db.query(CourseExam).filter(CourseExam.course_id == course_id).first()
    if not course_exam:
        raise HTTPException(status_code=500, detail="Exam configuration error: exercise found but no parent exam record.")

    # 5. Create a new UserExamAttempt record for the new exercise
    new_attempt = UserExamAttempt(
        user_id=user_id,
        course_id=course_id,
        exam_id=course_exam.id,
        exercise_id=new_exam_exercise.id,
        is_active=True,
        failure_count=0
    )
    db.add(new_attempt)
    db.commit() # Commit deactivation of old and creation of new
    db.refresh(new_attempt)
    logger.info(f"Created new exam attempt {new_attempt.id} (Exercise ID: {new_exam_exercise.id}) for User {user_id}.")

    return new_exam_exercise
