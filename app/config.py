# app/config.py
import os

SECRET = os.getenv("QUIZ_SECRET", "Immaculate")
ALLOWED_EMAIL = os.getenv("QUIZ_EMAIL", "24ds2000040@ds.study.iitm.ac.in")
TIMEOUT_SECONDS = int(os.getenv("QUIZ_TIMEOUT", "170"))

# Default to headless unless otherwise set
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "1") == "1"
