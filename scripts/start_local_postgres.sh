#!/bin/sh
set -eu

PGROOT=/code/tmp/postgres
PGDATA="$PGROOT/data"
PGLOG="$PGROOT/postgres.log"
PGSOCK="$PGROOT/socket"
PGPORT="${PGPORT:-55432}"
PGBIN=/usr/lib/postgresql/15/bin

mkdir -p "$PGROOT"
mkdir -p "$PGSOCK"

if [ ! -d "$PGDATA" ]; then
  "$PGBIN/initdb" -D "$PGDATA" -A trust -U agent >/dev/null
fi

"$PGBIN/pg_ctl" -D "$PGDATA" -l "$PGLOG" -o "-F -k $PGSOCK -p $PGPORT" start >/dev/null

createdb -h 127.0.0.1 -p "$PGPORT" -U agent course_pipeline 2>/dev/null || true
echo "postgres started on 127.0.0.1:$PGPORT"
