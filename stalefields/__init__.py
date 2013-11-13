# -*- coding: utf-8 -*-
"""
A model mixin to keep track of changed fields in a model.
"""
__version_info__ = {
    'major': 0,
    'minor': 8,
    'micro': 5,
    'releaselevel': 'final',
    'serial': 1
}


def get_version(short=False):
    assert __version_info__['releaselevel'] in ('alpha', 'beta', 'final')
    vers = ["%(major)i.%(minor)i" % __version_info__, ]
    if __version_info__['micro']:
        vers.append(".%(micro)i" % __version_info__)
    if __version_info__['releaselevel'] != 'final' and not short:
        vers.append('%s%i' % (
            __version_info__['releaselevel'][0], __version_info__['serial']))
    return ''.join(vers)

__version__ = get_version()

from django.core.exceptions import ImproperlyConfigured

try:
    from stalefields import StaleFieldsMixin
except (ImportError, ImproperlyConfigured), e:
    pass
