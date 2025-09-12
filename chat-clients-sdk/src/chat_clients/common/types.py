from enum import Enum

class UserChatClientType(Enum):
    """Supported User Chat Client Type
    """
    WEB = "WEB"
    SLACK = "SLACK"
    TEAMS = "TEAMS"
    # TELEGRAM = "TELEGRAM"
    # more can be added later

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """
        Class method to check if value is a valid type
        """
        return value in [e.value for e in UserChatClientType]

class ConnectionType(Enum):
    """Amazon Connect Participant create connection API enumerations
    """
    WEBSOCKET = "WEBSOCKET"
    CONNECTION_CREDENTIALS = "CONNECTION_CREDENTIALS"

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """
        Class method to check if value is a valid type
        """
        return value in [e.value for e in UserChatClientType]
