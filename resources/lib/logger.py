import xbmc
from resources.lib import settings


def debug(message):
    if __is_log_enabled():
        xbmc.log("SUPERNOVA: " + message)


def __is_log_enabled():
    return settings.get_setting("debug")
