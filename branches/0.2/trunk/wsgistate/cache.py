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

__all__ = ['WsgiCache', 'cache']

def cache(cache, **kw):
    '''Decorator for caching.'''
    def decorator(application):
        return WsgiCache(application, cache, **kw)
    return decorator

def expiredate(value, seconds):
    now = time.time()
    return [('Cache-Control', value % seconds),
        ('Date', rfc822.formatdate(now)),
        ('Expires', rfc822.formatdate(now + seconds))]

def control(application, value):
    '''Generic setter for 'Cache-Control' headers.

    @param application WSGI application
    @param value 'Cache-Control' value
    '''
    headers = [('Cache-Control', value)]
    return CacheHeader(application, headers)

def expire(application, value):
    '''Generic setter for 'Cache-Control' headers + expiration info.

    @param application WSGI application
    @param value 'Cache-Control' value
    '''    
    now = rfc822.formatdate()
    headers = [('Cache-Control', value), ('Date', now), ('Expires', now)]
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
    '''Sets caching to 'public'.'''
    return control(application, 'public')
    
def private(application):
    '''Sets caching to 'private'.'''
    return expire(application, 'private')
    
def nocache(application):
    '''Sets caching to 'no-cache'.'''
    now = rfc822.formatdate()
    headers = [('Cache-Control', 'no-cache'), ('Pragma', 'no-cache'),
        ('Date', now), ('Expires', now)]
    return CacheHeader(application, headers)

def nostore(application):
    '''Turns off caching.'''
    return expire(application, 'no-store')

def notransform(application):
    ''''''
    return control(application, 'no-transform')

def mustrevalidate(application):
    return control(application, 'must-revalidate')

def proxyrevalidate(application):
    return control(application, 'proxy-revalidate')

def maxage(seconds):
    return age('max-age=%d', seconds)

def smaxage(seconds):
    return age('s-maxage=%d', seconds)

def expires(seconds):
    headers = [('Expires', rfc822.formatdate(time.time() + seconds))]
    return CacheHeader(application, headers)

def vary(headers):
    headers = [('Vary', ', '.join(headers))]
    def decorator(application):
        return CacheHeader(application, headers)
    return decorator

def modified(time=None):
    headers = [('Modified', rfc822.formatdate(time))]
    return CacheHeader(application, headers)


class CacheHeader(object):

    '''Controls HTTP Caching headers.'''

    def __init__(self, application, headers):
        self.application = application
        self.headers = headers
        
    def __call__(self, environ, start_response):
        if environ.get('REQUEST_METHOD').upper() in ('GET', 'HEAD'):
            def hdr_response(status, headers, exc_info=None):
                headers.extend(self.headers)
                return start_response(status, headers, exc_info)
            return self.application(environ, hdr_response)
        return self.application(environ, start_response)
        

class WsgiCache(object):

    '''WSGI middleware for response caching.'''  

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
        if cached is not None:
            start_response(info['status'], info['headers'], info['exc_info'])
            return info['data']
        if self._cacheable(environ):
            def cache_response(self, status, headers, exc_info=None):
                expirehdrs = expiredate(self._cache.timeout, 's-maxage=%d')
                headers.extend(expirehdrs)
                cachedict = dict((('status', status), ('headers', headers),
                    ('exc_info', exc_info)))
                self._cache.set(key, cachedict)
                return start_response(status, headers, exc_info) 
            data = self.application(environ, cache_response)
            self._cache[key]['data'] = data
            return data
        return self.application(environ, start_response)

    def _keygen(self, environ):
        '''Generates cache keys.'''
        # Base of key is always path of request
        key = environ['PATH_INFO']
        # Add method name to key if configured that way
        if self._methidx: key += environ['REQUEST_METHOD']
        # Add marshalled user submitted data to string if configured that way
        if self._useridx:
            qdict = cgi.parse(environ['wsgi.input'], environ, False, False)
            key += marshal.dumps(qdict)
        return key
    
    def _cacheable(self, environ):
        '''Tells if a request should be cached or not.'''
        # Returns false if method is not to be cached
        if environ['REQUEST_METHOD'] not in self._allowed: return False
        # Returns false if requests based on user submissions are not to be cached
        if self._usersub:
            if 'QUERY_STRING' in environ or environ['REQUEST_METHOD'] == 'POST':
                return False
        return True