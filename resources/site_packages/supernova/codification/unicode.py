from __future__ import absolute_import, division, unicode_literals
from kodi_six.utils import PY2


def to_unicode(text, encoding='utf-8', errors='strict'):
    if isinstance(text, bytes):
        return text.decode(encoding, errors)
    return text


def from_unicode(text, encoding='utf-8', errors='strict'):
    if PY2 and isinstance(text, unicode):
        return text.encode(encoding, errors)
    return text