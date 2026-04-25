import sys
import os

# Hostinger requires this bridge file to map Phusion Passenger into your local venv directory
# Note: You may need to change 'python' to the exact path in Hostinger if running into issues,
# but Phusion usually detects the global Python automatically if WSGI is set.
sys.path.append(os.getcwd())

from app import app as application
