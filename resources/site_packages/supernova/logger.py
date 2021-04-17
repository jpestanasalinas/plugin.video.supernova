import xbmc
from resources.site_packages.supernova import settings


def log(message):
    if __is_log_enabled():
        xbmc.log("SUPERNOVA: " + message)


def __is_log_enabled():
    return settings.get_setting("debug")
