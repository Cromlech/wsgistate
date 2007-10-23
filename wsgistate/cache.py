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

import time
import rfc822
from StringIO import StringIO

__all__ = ['WsgiMemoize', 'CacheHeader', 'memoize', 'public', 'private',
    'nocache', 'nostore', 'notransform', 'revalidate', 'proxyrevalidate',
    'maxage', 'smaxage', 'vary', 'modified']

def memoize(cache, **kw):
    '''Decorator for caching.'''
    def decorator(application):
        return WsgiMemoize(application, cache, **kw)
    return decorator

def getinput(environ):
    '''Non-destructively retrieves wsgi.input value.'''
    wsginput = environ['wsgi.input']
    # Non-destructively fetch string value of wsgi.input
    if hasattr(wsginput, 'getvalue'):
        qs = wsginput.getvalue()
    # Otherwise, read and reconstruct wsgi.input
    else:
        # Never read more than content length
        clength = int(environ['CONTENT_LENGTH'])
        qs = wsginput.read(clength)
        environ['wsgi.input'] = StringIO(qs)
    return qs

def expiredate(seconds, value):
    '''Expire date headers for cache control.

    @param seconds Seconds
    @param value Value for Cache-Control header
    '''
    now = time.time()
    return {'Cache-Control':value % seconds, 'Date':rfc822.formatdate(now),
        'Expires':rfc822.formatdate(now + seconds)}

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

def age(value, second):
    '''Generic setter for 'Cache-Control' headers + future expiration info.

    @param value 'Cache-Control' value
    @param seconds # of seconds a resource should be considered invalid in
    '''
    def decorator(application):
        return CacheHeader(application, expiredate(second, value))
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

    '''Controls HTTP Cache Control headers.'''

    def __init__(self, application, headers):
        self.application = application
        self.headers = headers

    def __call__(self, environ, start_response):
        # Restrict cache control to GET and HEAD per HTTP 1.1 RFC
        if environ.get('REQUEST_METHOD') in ('GET', 'HEAD'):
            # Co-routine to add cache control headers
            def hdr_response(status, headers, exc_info=None):
                theaders = self.headers.copy()
                # Aggregate all 'Cache-Control' directives
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
        self._methkey = kw.get('key_methods', False)
        # Adds user submitted data to cache key
        self._userkey = kw.get('key_user_info', False)
        # Which HTTP responses by method are cached
        self._allowed = kw.get('allowed_methods', set(['GET', 'HEAD']))

    def __call__(self, environ, start_response):
        # Verify requested response is cacheable
        if environ['REQUEST_METHOD'] not in self._allowed:
            return self.application(environ, start_response)
        # Generate cache key
        key = self._keygen(environ)
        # Query cache for key prescence
        info = self._cache.get(key)
        # Return cached data
        if info is not None:
            start_response(info['status'], info['headers'], info['exc_info'])
            return info['data']
        # Cache start_response info
        def cache_response(status, headers, exc_info=None):
            # Add HTTP cache control headers
            newhdrs = expiredate(self._cache.timeout, 's-maxage=%d')
            headers.extend((k, v) for k, v in newhdrs.iteritems())
            cachedict = {'status':status, 'headers':headers, 'exc_info':exc_info}
            self._cache.set(key, cachedict)
            return start_response(status, headers, exc_info)
        # Wrap data in list to trigger iterator (Roberto De Alemeida)
        data = list(self.application(environ, cache_response))
        # Fetch cached dictionary
        info = self._cache.get(key)
        # Store in dictionary
        info['data'] = data
        # Store in cache
        self._cache.set(key, info)
        # Return data as response to intial request
        return data

    def _keygen(self, environ):
        '''Generates cache keys.'''
        # Base of key is always path of request
        key = [environ['PATH_INFO']]
        # Add method name to key if configured that way
        if self._methkey: key.append(environ['REQUEST_METHOD'])
        # Add user submitted data to string if configured that way
        if self._userkey:
            qs = environ.get('QUERY_STRING', '')
            if qs != '':
                key.append(qs)
            else:
                win = getinput(environ)
                if win != '': key.append(win)
        return ''.join(key)
