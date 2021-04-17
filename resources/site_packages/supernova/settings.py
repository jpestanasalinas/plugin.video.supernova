import xbmcaddon


def get_setting(setting_name):
    return xbmcaddon.Addon().getSetting(setting_name)
