#!/bin/bash
set -euo pipefail
exec gunicorn --config gunicorn.conf.py config.asgi:application
