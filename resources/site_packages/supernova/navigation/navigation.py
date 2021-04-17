import socket
import sys
import time

from resources.site_packages.supernova.addon import ADDON, ADDON_ID
from resources.site_packages.supernova.codification.unicode import to_unicode
from resources.site_packages.supernova.config import SUPERNOVA_HOST

from kodi_six import xbmc, xbmcplugin, xbmcgui
from kodi_six.utils import py2_decode

import six
from six.moves import urllib_request
from six.moves import urllib_response
from six.moves import urllib_parse
from six.moves import urllib_error

from resources.site_packages.supernova.logger import log
from resources.site_packages.supernova.navigation.exceptions.PlayerException import PlayerException
from resources.site_packages.supernova.navigation.exceptions.RedirectException import RedirectException
from resources.site_packages.supernova.osarchitecture import PLATFORM
from resources.site_packages.supernova.util import notify, get_localized_string, get_localized_label

try:
    import simplejson as json
except ImportError:
    import json

HANDLE = int(sys.argv[1])


class closing(object):
    def __init__(self, thing):
        self.thing = thing

    def __enter__(self):
        return self.thing

    def __exit__(self, *exc_info):
        self.thing.close()


class InfoLabels(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        return dict.get(self, key.lower(), "")

    def __setitem__(self, key, val):
        dict.__setitem__(self, key.lower(), val)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v


def execute(url_suffix="", retry=0):
    buffer_timeout = get_buffer_timeout()
    preload_timeout = get_preload_timeout()

    socket.setdefaulttimeout(buffer_timeout)
    opener = urllib_request.build_opener(no_redirect_handler())
    opener.addheaders = [('User-Agent', ADDON_ID)]
    urllib_request.install_opener(opener)

    pause_current_playing_file_avoiding_doubling_request()

    url = sys.argv[0].replace("plugin://%s" % ADDON_ID, SUPERNOVA_HOST + url_suffix) + sys.argv[2]
    query_add = ""

    if len(sys.argv) > 3:
        query_add = sys.argv[3].replace(":", "=")

    if query_add and "resume=" not in url:
        query_add = query_add.replace("resume=", "doresume=")
        if "?" in url:
            url += "&" + query_add
        else:
            url += "?" + query_add

    log("Requesting %s from %s" % (url, repr(sys.argv)))

    try:
        data = _json(url)
    except PlayerException as e:
        redirect_url = e.__str__()
        log.debug("Launching player with %s" % (redirect_url))
        xbmcplugin.endOfDirectory(HANDLE, succeeded=True)
        xbmc.sleep(500)
        xbmc.executeJSONRPC(
            '{"jsonrpc":"2.0","method":"Player.Open","params":{"item":{"file":"%s"}},"id":"1"}' % (redirect_url))
        return
    except RedirectException as e:
        redirect_url = e.__str__()
        log.debug("Redirecting Kodi with %s" % (redirect_url))
        xbmcplugin.endOfDirectory(HANDLE, succeeded=True)
        xbmc.sleep(500)
        if "keyboard=1" in sys.argv[0]:
            xbmc.executebuiltin('Container.Update(%s,replace)' % (redirect_url))
        else:
            xbmc.executebuiltin('Container.Update(%s)' % (redirect_url))
        return
    except urllib_error.URLError as e:
        # We can retry the request if connection is refused.
        # For example when plugin has not yet started but is requested by someone.
        if retry <= 2:
            time.sleep(preload_timeout)
            return execute(retry=retry + 1)

        if isinstance(e.reason, IOError) or isinstance(e.reason, OSError) or 'Connection refused' in e.reason:
            notify(get_localized_string(30116), time=7000)
        else:
            import traceback
            map(log.error, traceback.format_exc().split("\n"))
            notify(e.reason, time=7000)
        return
    except Exception as e:
        import traceback
        log.debug(traceback.print_exc())
        map(log.error, traceback.format_exc().split("\n"))
        try:
            msg = six.ensure_text(e.__str__(), errors='ignore')
        except:
            try:
                msg = six.ensure_binary(e.__str__(), errors='ignore')
            except:
                msg = repr(e)
        notify(get_localized_label(msg), time=7000)
        return


def pause_current_playing_file_avoiding_doubling_request():
    try:
        if xbmc.Player().isPlaying() and ADDON_ID in xbmc.Player().getPlayingFile():
            xbmc.Player().pause()
    except:
        pass


def get_preload_timeout():
    try:
        preload_timeout = int(ADDON.getSetting("preload_timeout"))
        if preload_timeout < 1:
            preload_timeout = 1
    except:
        preload_timeout = 1
    return preload_timeout


def get_buffer_timeout():
    try:
        buffer_timeout = int(ADDON.getSetting("buffer_timeout"))
        if buffer_timeout < 60:
            buffer_timeout = 60
    except:
        buffer_timeout = 60
    buffer_timeout = buffer_timeout * 2
    return buffer_timeout


class no_redirect_handler(urllib_request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib_response.addinfourl(fp, headers, headers["Location"])
        try:
            infourl.status = code
        except AttributeError:
            pass
        infourl.code = code
        log.log("Redirecting with code %d to: %s", code, headers["Location"])
        return infourl

    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302


def _json(url):
    with closing(urllib_request.urlopen(url)) as response:
        if response.code == 300:
            raise PlayerException(response.info().getheader('Location'))
        elif response.code == 301:
            raise RedirectException(response.info().getheader('Location'))
        elif 302 <= response.code <= 307:
            pause_current_playing_file_avoiding_doubling_request()

            _infoLabels = InfoLabels(getInfoLabels())
            if 'mediatype' not in _infoLabels or not _infoLabels['mediatype']:
                _infoLabels['mediatype'] = 'episode'
                _infoLabels['dbtype'] = 'episode'

            if PLATFORM['kodi'] >= 19:
                item = xbmcgui.ListItem(
                    path=response.geturl(),
                    label=_infoLabels["label"],
                    label2=_infoLabels["label2"]
                )
            else:
                item = xbmcgui.ListItem(
                    path=response.geturl(),
                    label=_infoLabels["label"],
                    label2=_infoLabels["label2"],
                    thumbnailImage=_infoLabels["thumbnail"]
                )

            item.setArt({
                "thumb": _infoLabels["artthumb"],
                "poster": _infoLabels["artposter"],
                "tvshowposter": _infoLabels["arttvshowposter"],
                "banner": _infoLabels["artbanner"],
                "fanart": _infoLabels["artfanart"],
                "clearart": _infoLabels["artclearart"],
                "clearlogo": _infoLabels["artclearlogo"],
                "landscape": _infoLabels["artlandscape"],
                "icon": _infoLabels["articon"]
            })

            if 'castmembers' in _infoLabels:
                if PLATFORM['kodi'] >= 17:
                    item.setCast(_infoLabels['castmembers'])
                del _infoLabels['castmembers']

            _infoLabels = normalize_labels(_infoLabels)

            item.setInfo(type='Video', infoLabels=_infoLabels)
            xbmcplugin.setResolvedUrl(HANDLE, True, item)
            return

        payload = to_unicode(response.read())

        try:
            if payload:
                return json.loads(payload)
        except:
            raise Exception(payload)


def getInfoLabels():
    id_list = [int(s) for s in sys.argv[0].split("/") if s.isdigit()]
    tmdb_id = id_list[0] if id_list else None

    if not tmdb_id:
        request_url = sys.argv[0] + sys.argv[2]
        parsed_url = urllib_parse.urlparse(request_url)
        query = urllib_parse.parse_qs(parsed_url.query)
        query['index'] = query['index'][0] if 'index' in query else ''
        log.debug("Parsed URL: %s, Query: %s", repr(parsed_url), repr(query))
        if 'tmdb' in query and 'type' in query and query['type'][0] == 'search':
            tmdb_id = query['tmdb'][0]
            url = "%s/search/infolabels/%s?index=%s" % (SUPERNOVA_HOST, tmdb_id, query['index'])
        elif '/search' in parsed_url and 'tmdb' in query:
            tmdb_id = query['tmdb'][0]
            url = "%s/search/infolabels/%s?index=%s" % (SUPERNOVA_HOST, tmdb_id, query['index'])
        elif '/search' in parsed_url and 'q' in query:
            tmdb_id = py2_decode(query['q'][0])
            url = "%s/search/infolabels/%s?index=%s" % (SUPERNOVA_HOST, tmdb_id, query['index'])
        elif 'tmdb' in query and 'type' in query and query['type'][0] == 'movie':
            tmdb_id = query['tmdb'][0]
            url = "%s/movie/%s/infolabels" % (SUPERNOVA_HOST, tmdb_id)
        elif 'show' in query:
            tmdb_id = query['show'][0]
            if 'season' in query and 'episode' in query:
                url = "%s/show/%s/season/%s/episode/%s/infolabels" % (
                SUPERNOVA_HOST, tmdb_id, query['season'][0], query['episode'][0])
            else:
                url = "%s/show/%s/infolabels" % (SUPERNOVA_HOST, tmdb_id)
        else:
            url = "%s/infolabels" % (SUPERNOVA_HOST)
    elif 'movie' in sys.argv[0]:
        url = "%s/movie/%s/infolabels" % (SUPERNOVA_HOST, tmdb_id)
    elif ('episode' in sys.argv[0] or 'show' in sys.argv[0]) and len(id_list) > 2:
        url = "%s/show/%s/season/%s/episode/%s/infolabels" % (SUPERNOVA_HOST, tmdb_id, id_list[1], id_list[2])
    elif 'show' in sys.argv[0] and len(id_list) == 2:
        url = "%s/show/%s/season/%s/episode/%s/infolabels" % (SUPERNOVA_HOST, tmdb_id, id_list[1], 1)
    else:
        url = "%s/infolabels" % (SUPERNOVA_HOST)

    log.debug("Resolving TMDB item by calling %s for %s" % (url, repr(sys.argv)))

    try:
        with closing(urllib_request.urlopen(url)) as response:
            resolved = json.loads(to_unicode(response.read()), parse_int=str)
            if not resolved:
                return {}

            if 'info' in resolved and resolved['info']:
                resolved.update(resolved['info'])

            if 'art' in resolved and resolved['art']:
                resolved['artbanner'] = ''
                for k, v in resolved['art'].items():
                    resolved['art' + k] = v

            if 'info' in resolved:
                del resolved['info']
            if 'art' in resolved:
                del resolved['art']
            if 'stream_info' in resolved:
                del resolved['stream_info']

            if 'DBTYPE' not in resolved:
                resolved['DBTYPE'] = 'video'
            if 'mediatype' not in resolved or resolved['mediatype'] == '':
                resolved['mediatype'] = resolved['DBTYPE']

            return resolved
    except:
        log.debug("Could not resolve TMDB item: %s" % tmdb_id)
        return {}


def normalize_labels(labels):
    if PLATFORM['kodi'] <= 16:
        for i, item in enumerate(labels):
            if type(labels[item]) is tuple or type(labels[item]) is list:
                delist_label(labels, item)

    elif PLATFORM['kodi'] == 17:
        delist_label(labels, 'genre')
        delist_label(labels, 'country')
        delist_label(labels, 'director')
        delist_label(labels, 'studio')
        delist_label(labels, 'writer')
        delist_label(labels, 'tag')
        delist_label(labels, 'showlink')
        delist_label(labels, 'credits')

    return labels


def delist_label(labels, key):
    if key in labels:
        labels[key] = ', '.join(labels[key])
