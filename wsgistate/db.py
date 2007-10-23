# Copyright (c) 2005, the Lawrence Journal-World
# Copyright (c) 2006 L. C. Rees
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of Django nor the names of its contributors may be used
#       to endorse or promote products derived from this software without
#       specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''Database cache backend.'''

import time
from random import choice
from datetime import datetime

from sqlalchemy import (
        Table, Column, String, Binary, DateTime,
        Integer, PickleType, bindparam, select, update,
        delete, insert,
    )
try:
    from sqlalchemy import BoundMetaData
except ImportError:
    from sqlalchemy import MetaData as BoundMetaData

from wsgistate import BaseCache
from wsgistate.cache import WsgiMemoize
from wsgistate.session import CookieSession, URLSession, SessionCache

__all__ = ['DbCache', 'memoize', 'session', 'urlsession']

def dbmemo_deploy(global_conf, **kw):
    '''Paste Deploy loader for caching.'''
    def decorator(application):
        _db_memo_cache = DbCache(kw.get('cache'), **kw)
        return WsgiMemoize(application, _db_memo_cache, **kw)
    return decorator

def dbsession_deploy(global_conf, **kw):
    '''Paste Deploy loader for sessions.'''
    def decorator(application):
        _db_base_cache = DbCache(kw.get('cache'), **kw)
        _db_session_cache = SessionCache(_db_base_cache, **kw)
        return CookieSession(application, _db_session_cache, **kw)
    return decorator

def dburlsess_deploy(global_conf, **kw):
    '''Paste Deploy loader for URL encoded sessions.

    @param initstr Database initialization string
    '''
    def decorator(application):
        _db_ubase_cache = DbCache(kw.get('cache'), **kw)
        _db_url_cache = SessionCache(_db_ubase_cache, **kw)
        return URLSession(application, _db_url_cache, **kw)
    return decorator

def memoize(initstr, **kw):
    '''Decorator for caching.

    @param initstr Database initialization string
    '''
    def decorator(application):
        _db_memo_cache = DbCache(initstr, **kw)
        return WsgiMemoize(application, _db_memo_cache, **kw)
    return decorator

def session(initstr, **kw):
    '''Decorator for sessions.

    @param initstr Database initialization string
    '''
    def decorator(application):
        _db_base_cache = DbCache(initstr, **kw)
        _db_session_cache = SessionCache(_db_base_cache, **kw)
        return CookieSession(application, _db_session_cache, **kw)
    return decorator

def urlsession(initstr, **kw):
    '''Decorator for URL encoded sessions.

    @param initstr Database initialization string
    '''
    def decorator(application):
        _db_ubase_cache = DbCache(initstr, **kw)
        _db_url_cache = SessionCache(_db_ubase_cache, **kw)
        return URLSession(application, _db_url_cache, **kw)
    return decorator


class DbCache(BaseCache):

    '''Database cache backend.'''

    def __init__(self, *a, **kw):
        super(DbCache, self).__init__(self, *a, **kw)
        # Get table name
        tablename = kw.get('tablename', 'cache')
        # Bind metadata
        self._metadata = BoundMetaData(a[0])
        # Make cache
        self._cache = Table(
            tablename, self._metadata,
            Column(
                'id', Integer, primary_key=True, nullable=False, unique=True
            ),
            Column('key', String(60), nullable=False),
            Column('value', PickleType, nullable=False),
            Column('expires', DateTime, nullable=False)
        )
        # Create cache if it does not exist
        if not self._cache.exists(): self._cache.create()
        # Maximum number of entries to cull per call if cache is full
        self._maxcull = kw.get('maxcull', 10)
        max_entries = kw.get('max_entries', 300)
        try:
            self._max_entries = int(max_entries)
        except (ValueError, TypeError):
            self._max_entries = 300

    def __len__(self):
        return self._cache.count().execute().fetchone()[0]

    def get(self, key, default=None):
        '''Fetch a given key from the cache.  If the key does not exist, return
        default, which itself defaults to None.

        @param key Keyword of item in cache.
        @param default Default value (default: None)
        '''
        row = select(
            [self._cache.c.value, self._cache.c.expires],
            self._cache.c.key==key
        ).execute().fetchone()
        if row is None:
            return default
        if row.expires < datetime.now().replace(microsecond=0):
            self.delete(key)
            return default
        return row.value

    def set(self, key, value):
        '''Set a value in the cache.

        @param key Keyword of item in cache.
        @param value Value to be inserted in cache.
        '''
        if len(self) > self._max_entries: self._cull()
        timeout, cache = self.timeout, self._cache
        # Get expiration time
        expires = datetime.fromtimestamp(
            time.time() + timeout
        ).replace(microsecond=0)
        #try:
        # Update database if key already present
        if key in self:
            update(
                cache,
                cache.c.key==key,
                dict(value=value, expires=expires),
            ).execute()
        # Insert new key if key not present
        else:
            insert(cache, dict(key=key, value=value, expires=expires)).execute()
        # To be threadsafe, updates/inserts are allowed to fail silently
        #except: pass

    def delete(self, k):
        '''Delete a key from the cache, failing silently.

        @param key Keyword of item in cache.
        '''
        delete(self._cache, self._cache.c.key==k).execute()

    def _cull(self):
        '''Remove items in cache to make more room.'''
        cache, maxcull = self._cache, self._maxcull
        # Remove items that have timed out
        now = datetime.now().replace(microsecond=0)
        delete(cache, cache.c.expires < now).execute()
        # Remove any items over the maximum allowed number in the cache
        if len(self) >= self._max_entries:
            # Upper limit for key query
            ul = maxcull * 2
            # Get list of keys
            keys = [
                i[0] for i in select(
                    [cache.c.key], limit=ul
                ).execute().fetchall()
            ]
            # Get some keys at random
            delkeys = list(choice(keys) for i in xrange(maxcull))
            # Delete keys
            fkeys = tuple({'key':k} for k in delkeys)
            delete(cache, cache.c.key.in_(bindparam('key'))).execute(*fkeys)