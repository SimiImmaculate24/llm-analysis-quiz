# app/config.py
import os

SECRET = os.getenv("QUIZ_SECRET", "Immaculate")  # matches user-provided secret
ALLOWED_EMAIL = os.getenv("QUIZ_EMAIL", "24ds2000040@ds.study.iitm.ac.in")
TIMEOUT_SECONDS = int(os.getenv("QUIZ_TIMEOUT", "170"))  # < 3 minutes (180s)
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "1") == "1"
