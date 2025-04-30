#!/bin/sh
alembic upgrade head
if [ $? -ne 0 ]; then
    echo "Migration failed"
    exit 1
fi
echo "Migration completed successfully"
# Run the application
exec "$@"
