import os
from pathlib import Path

API_BASE_URL = os.environ.get(
    "MY_DROPBOX_API",
    "https://bry9itqmyb.execute-api.ap-southeast-1.amazonaws.com/stage",
)
SESSION_FILE_PATH = Path("~/.mydropbox-session").expanduser().resolve()