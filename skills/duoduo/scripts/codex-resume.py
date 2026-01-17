#!/usr/bin/env python3
"""
codex-resume.py <pr_number>
恢复 Codex session
"""
import sys
import os
import subprocess

PR_NUMBER = sys.argv[1]
S = os.path.dirname(os.path.abspath(__file__))

subprocess.run([sys.executable, f"{S}/session-resume.py", "codex", PR_NUMBER])
