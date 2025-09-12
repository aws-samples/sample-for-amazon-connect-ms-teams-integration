"""time_helper.py - Helper class that contains commonly used date timestamp methods"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from chat_clients.common.logging_helper import get_logger

# Configure logger
logger = get_logger(f"{__name__}")

# Check if "TZ" environment variable is set
# if it is set, test whether it is a supported by ZoneInfo
# - if invalid, then fall back to default timezone.
# current_timezone defaults to US/Eastern.
DEFAULT_TIME_ZONE: str = "US/Eastern"
current_timezone = DEFAULT_TIME_ZONE
if os.environ.get("TZ", None):
    current_timezone = os.environ.get("TZ", DEFAULT_TIME_ZONE)
    try:
        ZoneInfo(current_timezone)
    except: # NOSONAR - disable SonarLint false-positive rule
        logger.warning("Timezone %s is not supported.  Falling back to default timezone %s", current_timezone, DEFAULT_TIME_ZONE)
        current_timezone = DEFAULT_TIME_ZONE


def get_iso_timestamp(dts: datetime = None) -> str:
    """Get current date and timestamp in ISO 8601 format with local timezone"""

    # get current datetime in UTC
    dt = datetime.now(tz=ZoneInfo(current_timezone))

    # override dt with dts if present
    if dts:
        dt = dts

    # Get current iso 8601 format datetime string including the default timezone
    iso_timestamp = dt.isoformat()

    return iso_timestamp

def get_current_local_time() -> datetime:
    """
    Get current local time

    Returns:
        datetime: Current time zone aware date-timestamp
    """
    try:
        current_ts_with_tz = datetime.now(tz=ZoneInfo(current_timezone))
    except: # NOSONAR - disable SonarLint false-positive rule
        logger.warning("Timezone %s is not supported.  Falling back to default timezone %s", current_timezone, DEFAULT_TIME_ZONE)
        current_ts_with_tz = datetime.now(tz=ZoneInfo(DEFAULT_TIME_ZONE))

    return current_ts_with_tz
