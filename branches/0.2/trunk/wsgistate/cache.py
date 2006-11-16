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
#    3. Neither the name of psilib nor the names of its contributors may be used
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

'''WSGI middleware for caching.'''

import cgi
import marshal
import time
import rfc822
import copy

__all__ = ['WsgiMemoize', 'memoize', 'public', 'private', 'nocache', 'nostore',
    'notransform', 'revalidate', 'proxyvalidate', 'maxage', 'smaxage', 'vary',
    'modified']

def expiredate(seconds, value):
    now = time.time()
    return {'Cache-Control':value % seconds, 'Date':rfc822.formatdate(now),
        'Expires':rfc822.formatdate(now + seconds)}

def memoize(cache, **kw):
    '''Decorator for caching.'''
    def decorator(application):
        return WsgiMemoize(application, cache, **kw)
    return decorator

def control(application, value):
    '''Generic setter for 'Cache-Control' headers.

    @param application WSGI application
    @param value 'Cache-Control' value
    '''
    headers = {'Cache-Control':value}
    return CacheHeader(application, headers)

def expire(application, value):
    '''Generic setter for 'Cache-Control' headers + expiration info.

    @param application WSGI application
    @param value 'Cache-Control' value
    '''    
    now = rfc822.formatdate()
    headers = {'Cache-Control':value, 'Date':now, 'Expires':now}
    return CacheHeader(application, headers)

def age(value, seconds):
    '''Generic setter for 'Cache-Control' headers + future expiration info.

    @param value 'Cache-Control' value
    @param seconds # of seconds a resource should be considered invalid in   
    '''
    def decorator(application):
        return CacheHeader(application, expiredate(value, seconds))
    return decorator

def public(application):
    '''Response MAY be cached.'''
    return control(application, 'public')
    
def private(application):
    '''Response intended for 1 user that MUST NOT be cached.'''
    return expire(application, 'private')
    
def nocache(application):
    '''Response that a cache can't send without origin server revalidation.'''
    now = rfc822.formatdate()
    headers = {'Cache-Control':'no-cache', 'Pragma':'no-cache', 'Date':now,
        'Expires':now}
    return CacheHeader(application, headers)

def nostore(application):
    '''Response that MUST NOT be cached.'''
    return expire(application, 'no-store')

def notransform(application):
    '''A cache must not modify the Content-Location, Content-MD5, ETag,
    Last-Modified, Expires, Content-Encoding, Content-Range, and Content-Type
    headers.
    '''
    return control(application, 'no-transform')

def revalidate(application):
    '''A cache must revalidate a response with the origin server.'''
    return control(application, 'must-revalidate')

def proxyrevalidate(application):
    '''Shared caches must revalidate a response with the origin server.'''
    return control(application, 'proxy-revalidate')

def maxage(seconds):
    '''Sets the maximum time in seconds a response can be cached.'''
    return age('max-age=%d', seconds)

def smaxage(seconds):
    '''Sets the maximum time in seconds a shared cache can store a response.''' 
    return age('s-maxage=%d', seconds)

def expires(seconds):
    '''Sets the time a response expires from the cache (HTTP 1.0).'''
    headers = {'Expires':rfc822.formatdate(time.time() + seconds)}
    def decorator(application):
        return CacheHeader(application, headers)
    return decorator

def vary(headers):
    '''Sets which fields allow a cache to use a response without revalidation.'''
    headers = {'Vary':', '.join(headers)}
    def decorator(application):
        return CacheHeader(application, headers)
    return decorator

def modified(seconds=None):
    '''Sets the time a response was modified.'''
    headers = {'Modified':rfc822.formatdate(seconds)}
    def decorator(application):
        return CacheHeader(application, headers)
    return decorator


class CacheHeader(object):

    '''Controls HTTP Caching headers.'''

    def __init__(self, application, headers):
        self.application = application
        self.headers = headers
        
    def __call__(self, environ, start_response):
        if environ.get('REQUEST_METHOD') in ('GET', 'HEAD'):            
            def hdr_response(status, headers, exc_info=None):
                theaders = self.headers.copy()
                if 'Cache-Control' in theaders:                    
                    for idx, i in enumerate(headers):
                        if i[0] != 'Cache-Control': continue
                        curval = theaders.pop('Cache-Control')
                        newval = ', '.join([curval, i[1]])
                        headers.append(('Cache-Control', newval))
                        del headers[idx]
                        break
                headers.extend((k, v) for k, v in theaders.iteritems())
                return start_response(status, headers, exc_info)
            return self.application(environ, hdr_response)
        return self.application(environ, start_response)
        

class WsgiMemoize(object):

    '''WSGI middleware for response memoizing.'''

    def __init__(self, app, cache, **kw):
        self.application, self._cache = app, cache
        # Adds method to cache key
        self._methidx = kw.get('index_methods', False)
        # Adds user submitted data to cache key
        self._useridx = kw.get('index_user_info', False)
        # Which HTTP responses by method are cached
        self._allowed = kw.get('allowed_methods', ('GET', 'HEAD'))
        # Responses to user submitted data is cached
        self._usersub = kw.get('cache_user_info', False)
        
    def __call__(self, environ, start_response):
        key = self._keygen(environ)
        info = self._cache.get(key)
        # Cache if data uncached
        if info is not None:
            start_response(info['status'], info['headers'], info['exc_info'])
            return info['data']
        if self._cacheable(environ):
            def cache_response(status, headers, exc_info=None):
                # Add HTTP cache control headers
                newhdrs = expiredate(self._cache.timeout, 's-maxage=%d')
                headers.extend((k, v) for k, v in newhdrs.iteritems())
                cachedict = dict((('status', status), ('headers', headers),
                    ('exc_info', exc_info)))
                self._cache.set(key, cachedict)
                return start_response(status, headers, exc_info) 
            data = self.application(environ, cache_response)
            info = self._cache[key]
            info['data'] = data
            self._cache[key] = info
            return data
        return self.application(environ, start_response)

    def _keygen(self, environ):
        '''Generates cache keys.'''
        # Base of key is always path of request
        key = [environ['PATH_INFO']]
        # Add method name to key if configured that way
        if self._methidx: key.append(environ['REQUEST_METHOD'])
        # Add marshalled user submitted data to string if configured that way
        if self._useridx:
            wsginput = copy.copy(environ['wsgi.input'])
            qdict = cgi.parse(wsginput, environ, False, False)
            key.append(marshal.dumps(qdict))
        return ''.join(key)
    
    def _cacheable(self, environ):
        '''Tells if a request should be cached or not.'''
        # Returns false if method is not to be cached
        method = environ['REQUEST_METHOD']
        if method not in self._allowed: return False
        # Returns false if requests based on user submissions are not to be cached
        if self._usersub and ('QUERY_STRING' in environ or method == 'POST'):
            return False
        return True