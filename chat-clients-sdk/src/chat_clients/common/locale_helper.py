"""locale.py - Module contains common routines related to locale"""

from logging import Logger
from chat_clients.common.logging_helper import get_logger

class Utils:
    """
    Class contains common routines related to AWS services locale. For example,
    both Amazon Kendra and Amazon Comprehend require a ISO 639-1 language code.
    """

    @staticmethod
    def get_service_locale(locale: str) -> str:
        """
        Get service specific language code (aka locale) based on caller provided locale.
        Caller provided locale is made up of ISO 639-1 language code and the ISO 3166-1
        region code, separated by an underscore

        Args:
            locale (str): caller provided locale

        Returns:
            str: service specific language code

        Raises:
            Exception: unsupported locale provided by caller

        Examples:
            >>> Utils.get_service_language_code('en_US')
            'en'
            >>> Utils.get_service_language_code('zh_HK')
            'zh'
            >>> Utils.get_service_language_code('fr_CA')
            'fr'
            >>> Utils.get_service_language_code('unsupported_locale')
            Exception: Unsupported locale: unsupported_locale
        """
        if locale == 'en_US':
            return 'en'
        elif (
            locale == 'zh_HK' or
            locale == 'zh_CN' or
            locale == 'zh_TW' or
            locale == 'zh_SG'):
            return 'zh'
        elif locale == 'fr_CA':
            return 'fr'

        raise Exception(f"Unsupported locale: {locale}")

class Locale:
    """
    Instantiate default locale if one is not provided. The default locale is
    "en_US"
    """
    # class constants
    DEFAULT_LOCALE: str = "en_US"

    # class variables
    locale: str = None
    service_locale: str = None

    logger: Logger = None

    def __init__(self, locale: str = None):
        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # set class variables
        self.locale = locale if locale else self.DEFAULT_LOCALE
        self.service_locale = Utils.get_service_locale(self.locale)

        self.logger.debug("Locale: %s, Service Locale: %s", self.locale, self.service_locale)

    def get_locale(self) -> str:
        """Get locale"""
        return self.locale

    def get_service_locale(self) -> str:
        """Get service locale"""
        return self.service_locale
