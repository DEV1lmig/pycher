# Import models from shared location
import os
from sqlalchemy import create_engine
from shared.models import Base, User, Progress

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)

# Re-export for backward compatibility
__all__ = ['Base', 'User', 'Progress']
