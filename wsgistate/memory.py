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

'''Thread-safe in-memory cache backend.'''

import copy
try:
    import threading
except ImportError:
    import dummy_threading as threading

from wsgistate import synchronized
from wsgistate.simple import SimpleCache
from wsgistate.cache import WsgiMemoize
from wsgistate.session import CookieSession, URLSession, SessionCache

__all__ = ['MemoryCache', 'memoize', 'session', 'urlsession']


def memorymemo_deploy(global_conf, **kw):
    '''Paste Deploy loader for caching.'''
    def decorator(application):
        _memory_memo_cache = MemoryCache(kw.get('cache'), **kw)
        return WsgiMemoize(application, _memory_memo_cache, **kw)
    return decorator


def memorysess_deploy(global_conf, **kw):
    '''Paste Deploy loader for sessions.'''
    def decorator(application):
        _memory_base_cache = MemoryCache(kw.get('cache'), **kw)
        _memory_session_cache = SessionCache(_memory_base_cache, **kw)
        return CookieSession(application, _memory_session_cache, **kw)
    return decorator


def memoryurlsess_deploy(global_conf, **kw):
    '''Paste Deploy loader for URL encoded sessions.

    @param initstr Database initialization string
    '''
    def decorator(application):
        _memory_ubase_cache = MemoryCache(kw.get('cache'), **kw)
        _memory_url_cache = SessionCache(_memory_ubase_cache, **kw)
        return URLSession(application, _memory_url_cache, **kw)
    return decorator


def memoize(**kw):
    '''Decorator for caching.'''
    def decorator(application):
        _mem_memo_cache = MemoryCache(**kw)
        return WsgiMemoize(application, _mem_memo_cache, **kw)
    return decorator


def session(**kw):
    '''Decorator for sessions.'''
    def decorator(application):
        _mem_base_cache = MemoryCache(**kw)
        _mem_session_cache = SessionCache(_mem_base_cache, **kw)
        return CookieSession(application, _mem_session_cache, **kw)
    return decorator


def urlsession(**kw):
    '''Decorator for URL encoded sessions.'''
    def decorator(application):
        _mem_ubase_cache = MemoryCache(**kw)
        _mem_url_cache = SessionCache(_mem_ubase_cache, **kw)
        return URLSession(application, _mem_url_cache, **kw)
    return decorator


class MemoryCache(SimpleCache):

    '''Thread-safe in-memory cache backend.'''

    def __init__(self, *a, **kw):
        super(MemoryCache, self).__init__(*a, **kw)
        self._lock = threading.Condition()

    @synchronized
    def get(self, key, default=None):
        '''Fetch a given key from the cache. If the key does not exist, return
        default, which itself defaults to None.

        @param key Keyword of item in cache.
        @param default Default value (default: None)
        '''
        return copy.deepcopy(super(MemoryCache, self).get(key))

    @synchronized
    def set(self, key, value):
        '''Set a value in the cache.

        @param key Keyword of item in cache.
        @param value Value to be inserted in cache.
        '''
        super(MemoryCache, self).set(key, value)

    @synchronized
    def delete(self, key):
        '''Delete a key from the cache, failing silently.

        @param key Keyword of item in cache.
        '''
        super(MemoryCache, self).delete(key)
