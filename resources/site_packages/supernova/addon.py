# -*- coding: utf-8 -*-
import os
import sys

from kodi_six import xbmcaddon

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_ICON = ADDON.getAddonInfo("icon")

try:
    ADDON_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__).decode(sys.getfilesystemencoding(), 'ignore')),
                                              "../..", "..", ".."))
except:
    ADDON_PATH = ADDON.getAddonInfo("path")
