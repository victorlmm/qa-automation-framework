"""Central configuration. Every value can be overridden with an environment variable."""
import os

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://automationexercise.com")
API_BASE_URL = os.getenv("API_BASE_URL", f"{BASE_URL}/api")
API_TIMEOUT_SECONDS = float(os.getenv("API_TIMEOUT_SECONDS", "15"))

# Third-party ad/consent hosts that make the demo site slow and flaky.
# Blocking them is a deliberate stability decision, documented in the README.
BLOCKED_HOSTS_PATTERN = (
    r"(googlesyndication|doubleclick|googleadservices|adservice\.google"
    r"|fundingchoicesmessages|googletagmanager|google-analytics)"
)
