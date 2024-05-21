#!/bin/sh

if [ "$POSTGRES_DB" = "fastapi_db" ]
then
    echo "Waiting for fastapi_db..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "fastapi_db started"
fi

alembic upgrade heads

exec "$@"