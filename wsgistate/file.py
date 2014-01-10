# Copyright (c) 2005, the Lawrence Journal-World
# Copyright (c) 2006 L. C. Rees
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of Django nor the names of its contributors may
#    be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

'''File-based cache backend'''

try:
    import cPickle as pickle
except ImportError:
    import pickle

import os
import time
import urllib

from wsgistate.simple import SimpleCache
from wsgistate.cache import WsgiMemoize
from wsgistate.session import CookieSession, URLSession, SessionCache

__all__ = ['FileCache', 'memoize', 'session', 'urlsession']


def filememo_deploy(global_conf, **kw):
    '''Paste Deploy loader for caching.'''
    def decorator(application):
        _file_memo_cache = FileCache(kw.get('cache'), **kw)
        return WsgiMemoize(application, _file_memo_cache, **kw)
    return decorator


def filesess_deploy(global_conf, **kw):
    '''Paste Deploy loader for sessions.'''
    def decorator(application):
        _file_base_cache = FileCache(kw.get('cache'), **kw)
        _file_session_cache = SessionCache(_file_base_cache, **kw)
        return CookieSession(application, _file_session_cache, **kw)
    return decorator


def fileurlsess_deploy(global_conf, **kw):
    '''Paste Deploy loader for URL encoded sessions.

    @param initstr Database initialization string
    '''
    def decorator(application):
        _file_ubase_cache = FileCache(kw.get('cache'), **kw)
        _file_url_cache = SessionCache(_file_ubase_cache, **kw)
        return URLSession(application, _file_url_cache, **kw)
    return decorator


def memoize(path, **kw):
    '''Decorator for caching.

    @param path Filesystem path
    '''
    def decorator(application):
        _file_memo_cache = FileCache(path, **kw)
        return WsgiMemoize(application, _file_memo_cache, **kw)
    return decorator


def session(path, **kw):
    '''Decorator for sessions.

    @param path Filesystem path
    '''
    def decorator(application):
        _file_base_cache = FileCache(path, **kw)
        _file_session_cache = SessionCache(_file_base_cache, **kw)
        return CookieSession(application, _file_session_cache, **kw)
    return decorator


def urlsession(path, **kw):
    '''Decorator for URL encoded sessions.

    @param path Filesystem path
    '''
    def decorator(application):
        _file_ubase_cache = FileCache(path, **kw)
        _file_url_cache = SessionCache(_file_ubase_cache, **kw)
        return URLSession(application, _file_url_cache, **kw)
    return decorator


class FileCache(SimpleCache):

    '''File-based cache backend'''

    def __init__(self, *a, **kw):
        super(FileCache, self).__init__(*a, **kw)
        # Create directory
        try:
            self._dir = a[0]
        except IndexError:
            raise IOError('file.FileCache requires a valid directory path.')
        if not os.path.exists(self._dir):
                self._createdir()
        # Remove unneeded methods and attributes
        del self._cache

    def __contains__(self, key):
        '''Tell if a given key is in the cache.'''
        return os.path.exists(self._key_to_file(key))

    def get(self, key, default=None):
        '''Fetch a given key from the cache.  If the key does not exist, return
        default, which itself defaults to None.

        @param key Keyword of item in cache.
        @param default Default value (default: None)
        '''
        try:
            exp, value = pickle.load(open(self._key_to_file(key), 'rb'))
            # Remove item if time has expired.
            if exp < time.time():
                self.delete(key)
                return default
            return value
        except (IOError, OSError, EOFError, pickle.PickleError):
            pass
        return default

    def set(self, key, value):
        '''Set a value in the cache.

        @param key Keyword of item in cache.
        @param value Value to be inserted in cache.
        '''
        if len(self.keys()) > self._max_entries:
            self._cull()
        try:
            fname = self._key_to_file(key)
            pickle.dump((time.time() + self.timeout, value),
                        open(fname, 'wb'), 2)
        except (IOError, OSError):
            pass

    def delete(self, key):
        '''Delete a key from the cache, failing silently.

        @param key Keyword of item in cache.
        '''
        try:
            os.remove(self._key_to_file(key))
        except (IOError, OSError):
            pass

    def keys(self):
        '''Returns a list of keys in the cache.'''
        return os.listdir(self._dir)

    def _createdir(self):
        '''Creates the cache directory.'''
        try:
            os.makedirs(self._dir)
        except OSError:
            raise EnvironmentError(
                'Cache directory "%s" does not exist and ' +
                'could not be created' % self._dir)

    def _key_to_file(self, key):
        '''Gives the filesystem path for a key.'''
        return os.path.join(self._dir, urllib.quote_plus(key))
