#!/bin/sh

set -ex

cockroach sql -e 'DROP DATABASE IF EXISTS ketchup'
cockroach sql -e 'CREATE DATABASE ketchup'
cockroach sql -e 'GRANT ALL ON DATABASE ketchup TO example'

python -c 'import app; app.db.create_all()'
