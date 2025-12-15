from pathlib import Path

from swifttools.swift_too.version import version_tuple

XRTMODES = {
    0: "Auto",
    1: "Null",
    2: "ShortIM",
    3: "LongIM",
    4: "PUPD",
    5: "LRPD",
    6: "WT",
    7: "PC",
    8: "Raw",
    9: "Bias",
    150: "PC_150",
    200: "PC_200",
    255: "Manual",
    None: "Unset",
}
MODESXRT = {
    "Auto": 0,
    "Null": 1,
    "ShortIM": 2,
    "LongIM": 3,
    "PUPD": 4,
    "LRPD": 5,
    "WT": 6,
    "PC": 7,
    "Raw": 8,
    "Bias": 9,
    "PC_150": 150,
    "PC_200": 200,
    "Manual": 255,
}

# Define the API version
API_VERSION = f"{version_tuple[0]}.{version_tuple[1]}"

# Submission URL
API_URL = f"https://www.swift.psu.edu/api/v{API_VERSION}"
API_URL = f"http://localhost:8000/api/v{API_VERSION}"  # For local testing

# HTTP Status codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_SERVER_ERROR = 500

# Magic strings
STATUS_PENDING = "Pending"
SESSION_COOKIE_NAME = "session"

# Create and optionally load cookies
COOKIE_JAR_PATH = Path.home() / ".cache/swift_too" / "cookies.txt"
