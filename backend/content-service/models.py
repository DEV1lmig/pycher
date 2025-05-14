# Import models from shared location
from shared.models import Base, Course, Module, Lesson

# Re-export for backward compatibility
__all__ = ['Base', 'Course', 'Module', 'Lesson']
