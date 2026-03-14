#!/usr/bin/env bash

set -euo pipefail

# Runs Django management commands to prepare the application for release:
# - checks the deployment settings
# - applies database migrations

MANAGE="python ./manage.py"

$MANAGE check --deploy --traceback
$MANAGE migrate --no-input --traceback
