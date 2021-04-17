from resources.site_packages.supernova.addon import ADDON, ADDON_NAME, ADDON_ICON
from kodi_six import xbmcgui
from kodi_six.utils import py2_encode

from resources.site_packages.supernova.logger import log

from resources.site_packages.supernova.codification.unicode import to_unicode


def notify(message, header=ADDON_NAME, time=5000, image=ADDON_ICON):
    sound = ADDON.getSetting('do_not_disturb') == 'false'
    dialog = xbmcgui.Dialog()
    return dialog.notification(to_unicode(header), to_unicode(message), to_unicode(image), time, sound)


def get_localized_string(stringId):
    try:
        return py2_encode(ADDON.get_localized_string(stringId), 'utf-8', 'ignore')
    except:
        return stringId


def get_localized_label(label):
    try:
        if "LOCALIZE" not in label:
            return py2_encode(label)
        if ";;" not in label and label.endswith(']'):
            return py2_encode(get_localized_string(int(label[9:-1])))
        else:
            parts = label.split(";;")
            translation = get_localized_string(int(parts[0][9:14]))
            for i, part in enumerate(parts[1:]):
                if part[0:8] == "LOCALIZE":
                    parts[i + 1] = get_localized_string(int(part[9:14]))
                else:
                    parts[i + 1] = py2_encode(parts[i + 1])

            return py2_encode(translation % tuple(parts[1:]), 'utf-8', 'ignore')
    except Exception as e:
        log.error("Cannot decode the label: %s, Error: %s" % (label, e))
        return label
