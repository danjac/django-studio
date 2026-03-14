#!/usr/bin/env bash

set -euo pipefail

exec python ./manage.py "$@"
