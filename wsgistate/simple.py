# Copyright (c) 2005 Allan Saddi <allan@saddi.com>
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

'''Single-process in-memory cache backend.'''

import time
import random
from wsgistate import BaseCache
from wsgistate.cache import WsgiMemoize
from wsgistate.session import CookieSession, URLSession, SessionCache

__all__ = ['SimpleCache', 'memoize', 'session', 'urlsession']


def simplememo_deploy(global_conf, **kw):
    '''Paste Deploy loader for caching.'''
    def decorator(application):
        _simple_memo_cache = SimpleCache(kw.get('cache'), **kw)
        return WsgiMemoize(application, _simple_memo_cache, **kw)
    return decorator


def simplesess_deploy(global_conf, **kw):
    '''Paste Deploy loader for sessions.'''
    def decorator(application):
        _simple_base_cache = SimpleCache(kw.get('cache'), **kw)
        _simple_session_cache = SessionCache(_simple_base_cache, **kw)
        return CookieSession(application, _simple_session_cache, **kw)
    return decorator


def simpleurlsess_deploy(global_conf, **kw):
    '''Paste Deploy loader for URL encoded sessions.

    @param initstr Database initialization string
    '''
    def decorator(application):
        _simple_ubase_cache = SimpleCache(kw.get('cache'), **kw)
        _simple_url_cache = SessionCache(_simple_ubase_cache, **kw)
        return URLSession(application, _simple_url_cache, **kw)
    return decorator


def memoize(**kw):
    '''Decorator for caching.'''
    def decorator(application):
        _simple_memo_cache = SimpleCache(**kw)
        return WsgiMemoize(application, _simple_memo_cache, **kw)
    return decorator


def session(**kw):
    '''Decorator for sessions.'''
    def decorator(application):
        _simple_base_cache = SimpleCache(**kw)
        _simple_session_cache = SessionCache(_simple_base_cache, **kw)
        return CookieSession(application, _simple_session_cache, **kw)
    return decorator


def urlsession(**kw):
    '''Decorator for URL encoded sessions.'''
    def decorator(application):
        _simple_ubase_cache = SimpleCache(**kw)
        _simple_url_cache = SessionCache(_simple_ubase_cache, **kw)
        return URLSession(application, _simple_url_cache, **kw)
    return decorator


class SimpleCache(BaseCache):

    '''Single-process in-memory cache backend.'''

    def __init__(self, *a, **kw):
        super(SimpleCache, self).__init__(*a, **kw)
        # Get random seed
        random.seed()
        self._cache = dict()
        # Set max entries
        max_entries = kw.get('max_entries', 300)
        try:
            self._max_entries = int(max_entries)
        except (ValueError, TypeError):
            self._max_entries = 300
        # Set maximum number of items to cull if over max
        self._maxcull = kw.get('maxcull', 10)

    def get(self, key, default=None):
        '''Fetch a given key from the cache.  If the key does not exist, return
        default, which itself defaults to None.

        @param key Keyword of item in cache.
        @param default Default value (default: None)
        '''
        values = self._cache.get(key)
        if values is None:
            return default
        # Delete if item timed out and return default.
        if values[0] < time.time():
            self.delete(key)
            return default
        return values[1]

    def set(self, key, value):
        '''Set a value in the cache.

        @param key Keyword of item in cache.
        @param value Value to be inserted in cache.
        '''
        # Cull timed out values if over max # of entries
        if len(self._cache) >= self._max_entries:
            self._cull()

        # Set value and timeout in cache
        self._cache[key] = (time.time() + self.timeout, value)

    def delete(self, key):
        '''Delete a key from the cache, failing silently.

        @param key Keyword of item in cache.
        '''
        try:
            del self._cache[key]
        except KeyError:
            pass

    def keys(self):
        '''Returns a list of keys in the cache.'''
        return self._cache.keys()

    def _cull(self):
        '''Remove items in cache to make room.'''
        num, maxcull = 0, self._maxcull
        # Cull number of items allowed (set by self._maxcull)
        for key in self.keys():
            # Remove only maximum # of items allowed by maxcull
            if num <= maxcull:
                # Remove items if expired
                if self.get(key) is None:
                    num += 1
            else:
                break
        # Remove any additional items up to max # of items allowed by maxcull
        while len(self.keys()) >= self._max_entries and num <= maxcull:
            # Cull remainder of allowed quota at random
            self.delete(random.choice(self.keys()))
            num += 1
