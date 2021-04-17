from kodi_six import xbmcaddon

ONLY_CLIENT = False
JSONRPC_EXT_PORT = 65221
SUPERNOVA_HOST = "http://127.0.0.1:65220"

def init():
    global SUPERNOVA_HOST
    global JSONRPC_EXT_PORT
    global ONLY_CLIENT

    ADDON = xbmcaddon.Addon("plugin.video.elementum")

    try:
        SUPERNOVA_HOST = "http://" + ADDON.getSetting("remote_host") + ":" + ADDON.getSetting("remote_port")
        JSONRPC_EXT_PORT = int(ADDON.getSetting("local_port"))
        ONLY_CLIENT = ADDON.getSetting("local_only_client") == u"true"
    except:
        pass


init()
