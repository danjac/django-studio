#!/usr/bin/env bash
# Set up a local development environment: .env, git repository, Python
# dependencies, pre-commit hooks and Playwright browsers.
set -euo pipefail

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
fi

if [ ! -d .git ]; then
    git init
    echo "Initialized git repository"
fi

just pyinstall
just precommitinstall
just playwright-install
