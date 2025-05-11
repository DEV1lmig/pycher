#!/bin/sh
alembic revision --autogenerate -m "init"
alembic upgrade head
python seed_db.py
if [ $? -ne 0 ]; then
    echo "Migration failed"
    exit 1
fi
echo "Migration completed successfully"
# Run the application
exec "$@"
