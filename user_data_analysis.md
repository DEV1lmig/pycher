# User Data Structure Analysis

## Current User Data Structure

Based on the analysis of `seed_users.json`, each user follows this structure:

```json
{
  "user_info": {
    "id": number,
    "username": string,
    "email": string,
    "password": string,
    "first_name": string,
    "last_name": string
  },
  "enrollments": [
    {
      "user_id": number,
      "course_id": number,
      "is_completed": boolean,
      "progress_percentage": float,
      "is_active": boolean,
      "exam_unlocked": boolean
    }
  ],
  "module_progress": [
    {
      "user_id": number,
      "module_id": number,
      "is_completed": boolean,
      "is_unlocked": boolean
    }
  ],
  "lesson_progress": [
    {
      "user_id": number,
      "lesson_id": number,
      "is_completed": boolean
    }
  ],
  "exercise_submissions": [
    {
      "user_id": number,
      "exercise_id": number,
      "lesson_id": number,
      "is_correct": boolean,
      "code_submitted": string,
      "attempt_number": number
    }
  ]
}
```

## Course Structure Mapping

### Course 1: Python Básico
- **Modules**: 1, 2, 3 (plus module 4 for exam)
- **Lessons**: 1-11
- **Regular Exercises**: 1-11 (one per lesson)
- **Exam Exercises**: 12-16 (5 different exams)

**Module-Lesson Mapping:**
- Module 1: Lessons 1-3 (Exercises 1-3)
- Module 2: Lessons 4-7 (Exercises 4-7)
- Module 3: Lessons 8-11 (Exercises 8-11)

### Course 2: Python Intermedio
- **Modules**: 5, 6, 7 (plus module 8 for exam)
- **Lessons**: 12-23
- **Regular Exercises**: 17-28 (one per lesson)
- **Exam Exercises**: 29-33 (5 different exams)

**Module-Lesson Mapping:**
- Module 5: Lessons 12-14 (Exercises 17-19)
- Module 6: Lessons 15-17 (Exercises 20-22)
- Module 7: Lessons 18-23 (Exercises 23-28)

### Course 3: Python Avanzado
- **Modules**: 9, 10, 11 (plus module 12 for exam)
- **Lessons**: 24-31
- **Regular Exercises**: 34-43 (one per lesson)
- **Exam Exercises**: 44-48 (5 different exams)

**Module-Lesson Mapping:**
- Module 9: Lessons 24-26 (Exercises 34-36)
- Module 10: Lessons 27-29 (Exercises 37-39)
- Module 11: Lessons 30-31 (Exercises 40-43)

## Exercise ID Patterns

### Regular Exercises (Lesson-based)
- Course 1: Exercise IDs 1-11 (Lessons 1-11)
- Course 2: Exercise IDs 17-28 (Lessons 12-23)
- Course 3: Exercise IDs 34-43 (Lessons 24-31)

### Exam Exercises (Course-based)
- Course 1 Exams: Exercise IDs 12-16 (5 different exams)
- Course 2 Exams: Exercise IDs 29-33 (5 different exams)
- Course 3 Exams: Exercise IDs 44-48 (5 different exams)

## Current User Patterns

### User 101 (Beginner)
- Course 1, 25% progress
- Module 1 completed, Module 2 unlocked, Module 3 locked
- Lessons 1-3 completed
- Exercises 1-3 completed
- Exam not unlocked

### User 102 (Intermediate)
- Course 1, 50% progress
- Modules 1-2 completed, Module 3 unlocked
- Lessons 1-7 completed
- Exercises 1-7 completed
- Exam not unlocked

### User 103 (Advanced)
- Course 1, 90% progress
- All modules (1-3) completed
- All lessons (1-11) completed
- All exercises (1-11) completed
- Exam unlocked but no exam submissions

### User 104 (Pro)
- Multiple courses enrolled
- Course 1: 100% complete with exam submission (exercise 12)
- Course 2: 100% complete
- Course 3: 95% complete with exam unlocked
- All lessons and exercises completed for enrolled courses

## Key Patterns Identified

### Progress Calculation
- Progress percentage appears to be based on lesson completion
- ~92% progress when all lessons completed but exam not taken
- 100% when exam is also completed

### Module Unlocking Pattern
- Modules unlock sequentially
- All modules must be completed for exam to unlock
- `is_unlocked: true` and `is_completed: true` for completed modules

### Exercise Submission Pattern
- Each exercise has realistic Python code
- All submissions marked as `is_correct: true`
- `attempt_number: 1` for all current submissions
- Exercise submissions include both `exercise_id` and `lesson_id`

### Exam Unlocking Pattern
- `exam_unlocked: true` when all course lessons completed
- No exam submissions initially for exam-ready users
- Exam exercises don't have `lesson_id` (they're course-level)

## Required Data for New Users

### Course 1 Exam Ready Users (IDs 105-109)
- **Enrollments**: Course 1, ~92% progress, exam_unlocked: true
- **Module Progress**: Modules 1, 2, 3 all completed and unlocked
- **Lesson Progress**: Lessons 1-11 all completed
- **Exercise Submissions**: Exercises 1-11 with realistic code

### Course 2 Exam Ready Users (IDs 110-114)
- **Enrollments**: Course 2, ~92% progress, exam_unlocked: true
- **Module Progress**: Modules 5, 6, 7 all completed and unlocked
- **Lesson Progress**: Lessons 12-23 all completed
- **Exercise Submissions**: Exercises 17-28 with realistic code

### Course 3 Exam Ready Users (IDs 115-119)
- **Enrollments**: Course 3, ~92% progress, exam_unlocked: true
- **Module Progress**: Modules 9, 10, 11 all completed and unlocked
- **Lesson Progress**: Lessons 24-31 all completed
- **Exercise Submissions**: Exercises 34-43 with realistic code

## Naming Convention for New Users
- **Username**: `exam_ready_course{X}_user{Y}` where X=course_id, Y=user_number
- **Email**: `exam_ready_course{X}_user{Y}@pycher.com`
- **First Name**: `ExamReady{X}`
- **Last Name**: `User{Y}`
- **Password**: `password123` (consistent with existing users)