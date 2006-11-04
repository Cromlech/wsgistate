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
    '''Decorator for simple cache.'''
    def decorator(application):
        return WsgiCache(application, cache, **kw)
    return decorator

def control(application, value):
    headers = [('Cache-Control', value)]
    return CacheHeader(application, headers)

def expire(application, value):
    now = rfc822.formatdate()
    headers = [('Cache-Control', value), ('Date', now), ('Expires', now)]
    return CacheHeader(application, headers)

def age(value, seconds):
    now = time.time()
    headers = [('Cache-Control', value % seconds), ('Date', rfc822.formatdate(now)),
        ('Expires', rfc822.formatdate(now + seconds))]
    def decorator(application):
        return CacheHeader(application, headers)
    return decorator

def public(application):
    return control(application, 'public')
    
def private(application):
    return expire(application, 'private')
    
def nocache(application):
    now = rfc822.formatdate()
    headers = [('Cache-Control', 'no-cache'), ('Pragma', 'no-cache'),
        ('Date', now), ('Expires', now)]
    return CacheHeader(application, headers)

def nostore(application):
    return expire(application, 'no-store')

def notransform(application):
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

    '''WSGI middleware for caching.'''  

    def __init__(self, app, cache, **kw):
        '''Init method.'''
        super(WsgiCache, self).__init__()
        self.application, self._cache = app, cache
        # Adds method to cache key
        self._methidx = kw.get('index_methods', False)
        # Adds user submitted data (GET, POST) to cache key
        self._useridx = kw.get('index_user_info', False)
        # Which HTTP responses by method are cached
        self._allowed = kw.get('allowed_methods', set(['GET', 'HEAD']))
        # Responses to user submitted data (GET, POST) is cached
        self._usersub = kw.get('cache_user_info', False)
        
    def __call__(self, environ, start_response):
        '''Caches responses to HTTP requests.'''
        key = self._keygen(environ)
        cached = self._cache.get(key)      
        # Cache if data not cached
        try:
            data = cached['data']
            start_response(cached['status'], cached['headers'], cached['exc_info'])
        except TypeError:
            if self._cacheable(environ):                
                sr = _CacheResponse(start_response, key, self._cache)
                data = self.application(environ, sr.cache_start_response)
                self._cache[key]['data'] = data
            else:
                data = self.application(environ, start_response)                
        return data

    def _keygen(self, environ):
        '''Generates cache keys.'''
        # Base of key is alwasy path of request
        key = environ['PATH_INFO']
        # Add method name to key if configured that way
        if self._methidx: key = ''.join([key, environ['REQUEST_METHOD']])
        # Add marshalled user submitted data to string if configured that way
        if self._useridx:
            qdict = cgi.parse(environ['wsgi.input'], environ, False, False)
            key = ''.join([key, marshal.dumps(qdict)])
        return key
    
    def _cacheable(self, environ):
        '''Tells if a request should be cached or not.'''
        # Returns false if method is not to be cached
        if environ['REQUEST_METHOD'] not in self._allowed: return False
        # Returns false if requests based on user submissions are not to be cached
        if self._usersub:
            if 'QUERY_STRING' in environ: return False
            if environ['REQUEST_METHOD'] == 'POST': return False
        return True


class _CacheResponse(object):

    def __init__(self, start_response, key, cache):
        self._start_response = start_response
        self._cache, self._key = cache, key

    def cache_start_response(self, status, headers, exc_info=None):
        cachedict = dict((('status', status), ('headers', headers), ('exc_info', exc_info)))
        self._cache.set(self._key, cachedict)
        return self._start_response(status, headers, exc_info)