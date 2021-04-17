import xbmcaddon
import xbmcgui
from resources.lib import logger

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo("name")

line1 = "Hola mundo"

logger.debug("HOLA MUNDO")
xbmcgui.Dialog().ok(__addonname__, line1)