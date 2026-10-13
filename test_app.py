#!/usr/bin/env python3
"""Run the Docker smoke test from the host."""

import subprocess
import sys

raise SystemExit(subprocess.call([
    'docker', 'compose', 'run', '--rm', '--no-deps',
    'ocr-app', 'python', 'tests/smoke_test.py',
]))
