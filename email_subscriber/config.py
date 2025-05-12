import re
import pathlib
ROOT_PATH = pathlib.Path(__file__).parent.resolve()

DB_DIR = (ROOT_PATH.parent / "database").resolve()
DB_URL = f"sqlite:///{str(DB_DIR)}/subscribers.sqlite3"

SMTP_SERVER = "smtp.qq.com"
SMTP_PASSWORD = "yekvywjfbxqfcjae"
MY_EMAIL = "3681495832@qq.com"

SUBSCRIBER_MASK = r".*@stumail\.sztu\.edu\.cn"

# test_email = "202300204004@stumail.sztu.edu.cn"

# print(bool(re.compile(SUBSCRIBER_MASK).match(test_email)))