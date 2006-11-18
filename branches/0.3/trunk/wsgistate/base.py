# Copyright (c) 2005, the Lawrence Journal-World
# Copyright (c) 2005 Allan Saddi <allan@saddi.com>
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

'''Base Cache class.'''

__all__ = ['BaseCache']


class BaseCache(object):

    '''Base Cache class.'''    
    
    def __init__(self, *a, **kw):
        super(BaseCache, self).__init__()
        timeout = kw.get('timeout', 300)
        try:
            timeout = int(timeout)
        except (ValueError, TypeError):
            timeout = 300
        self.timeout = timeout

    def __getitem__(self, key):
        '''Fetch a given key from the cache.'''
        return self.get(key)

    def __setitem__(self, key, value):
        '''Set a value in the cache. '''
        self.set(key, value)

    def __delitem__(self, key):
        '''Delete a key from the cache.'''
        self.delete(key) 

    def __contains__(self, key):
        '''Tell if a given key is in the cache.'''
        return self.get(key) is not None

    def get(self, key, default=None):
        '''Fetch a given key from the cache.  If the key does not exist, return
        default, which itself defaults to None.

        @param key Keyword of item in cache.
        @param default Default value (default: None)
        '''
        raise NotImplementedError()

    def set(self, key, value):
        '''Set a value in the cache. 

        @param key Keyword of item in cache.
        @param value Value to be inserted in cache.        
        '''
        raise NotImplementedError()

    def delete(self, key):
        '''Delete a key from the cache, failing silently.

        @param key Keyword of item in cache.
        '''
        raise NotImplementedError()

    def get_many(self, keys):
        '''Fetch a bunch of keys from the cache.  For certain backends
        (memcached, pgsql) this can be *much* faster when fetching multiple values.

        Returns a dict mapping each key in keys to its value.  If the given
        key is missing, it will be missing from the response dict.

        @param keys Keywords of items in cache.        
        '''
        d = dict()
        for k in keys:
            val = self.get(k)
            if val is not None: d[k] = val
        return d