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

import os
import string
import time
import weakref
import atexit
import cgi
import urlparse
import sha
import random
import sys
from Cookie import SimpleCookie
from urllib import quote
try:
    import threading
except ImportError:
    import dummy_threading as threading

__all__ = ['SessionService', 'SessionCache', 'Session', 'session', 'urlsession']    

def _shutdown(ref):
    cache = ref()
    if cache is not None: cache.shutdown()
    
def session(cache, **kw):
    '''Decorator for sessions.'''
    def decorator(application):
        return Session(application, cache, **kw)
    return decorator

def urlsession(cache, **kw):
    '''Decorator for URL encoded sessions.'''
    def decorator(application):
        return URLSession(application, cache, **kw)
    return decorator


class SessionCache(object):
    
    '''Base class for session stores. You first acquire a session by
    calling create() or checkout(). After using the session, you must call
    checkin(). You must not keep references to sessions outside of a check
    in/check out block. Always obtain a fresh reference.
    '''
    # Would be nice if len(idchars) were some power of 2.
    idchars = '-_'.join([string.digits, string.ascii_letters])  
    length = 64

    def __init__(self, cache, **kw):
        self._lock = threading.Condition()
        self._checkedout, self._closed, self._cache = dict(), False, cache
        # Sets if session id is random on every access or not
        self._random = kw.get('random', False)
        self._secret = ''.join(self.idchars[ord(c) % len(self.idchars)]
            for c in os.urandom(self.length))
        # Ensure shutdown is called.
        atexit.register(_shutdown, weakref.ref(self))

    def __del__(self):
        self.shutdown()

    # Public interface.

    def create(self):
        '''Create a new session with a unique identifier.
        
        The newly-created session should eventually be released by
        a call to checkin().            
        '''
        assert not self._closed
        self._lock.acquire()
        try:
            sid, sess = self.newid(), dict()
            self._cache.set(sid, sess)
            assert sid not in self._checkedout            
            self._checkedout[sid] = sess
            return sid, sess
        finally:
            self._lock.release()

    def checkout(self, sid):
        '''Checks out a session for use. Returns the session if it exists,
        otherwise returns None. If this call succeeds, the session
        will be touch()'ed and locked from use by other processes.
        Therefore, it should eventually be released by a call to
        checkin().

        @param sid Session id        
        '''
        assert not self._closed
        self._lock.acquire()
        try:
            # If we know it's already checked out, block.
            while sid in self._checkedout: self._lock.wait()
            sess = self._cache.get(sid)
            if sess is not None:
                assert sid not in self._checkedout
                # Randomize session id if set and remove old session id
                if self._random:
                    self._cache.delete(sid)
                    sid = self.newid()
                # Put in checkout
                self._checkedout[sid] = sess
                return sid, sess
            else:
                return None, None
        finally:
            self._lock.release()

    def checkin(self, sid, session):
        '''Returns the session for use by other threads/processes.

        @param sid Session id
        @param session Session dictionary
        '''
        assert not self._closed
        if session is None: return
        self._lock.acquire()
        try:
            assert sid in self._checkedout
            del self._checkedout[sid]
            self._cache.set(sid, session)
            self._lock.notify()
        finally:            
            self._lock.release()

    def shutdown(self):
        '''Clean up outstanding sessions.'''
        self._lock.acquire()
        try:
            if not self._closed:
                # Save or delete any sessions that are still out there.                
                for sid, sess in self._checkedout.iteritems():
                    self._cache.set(sid, session)
                self._cache._cull()
                self._checkedout.clear()
                self._closed = True
        finally:
            self._lock.release()

    # Utilities

    def newid(self):
        'Returns session key that is not being used.'
        sid = None
        for num in xrange(10000):
            sid = sha.new(str(random.randint(0, sys.maxint - 1)) +
                str(random.randint(0, sys.maxint - 1)) + self._secret).hexdigest()
            if sid not in self._cache: break
        return sid
            

class SessionService(object):

    '''WSGI extension API passed to applications as
    environ['com.saddi.service.session'].

    Public API: (assume service = environ['com.saddi.service.session'])
      service.session - Returns the Session associated with the client.
      service.current - True if the client is currently associated with
        a Session.
      service.new - True if the Session was created in this
        transaction.
      service.expired - True if the client is associated with a
        non-existent Session.
      service.inurl - True if the Session ID should be encoded in
        the URL. (read/write)
      service.seturl(url) - Returns url encoded with Session ID (if
        necessary).
    '''  

    def __init__(self, cache, environ, **kw):
        self.cache = cache
        self.cname = kw.get('cookiename', '_SID_')
        self.fieldname = kw.get('fieldname', '_SID_')
        self.path = kw.get('path', '/')
        self.session = self.sid = self.csid = None
        self.newsession = self.expired = self.current = self.inurl = False
        self.get(environ)

    @property
    def new(self):
        '''Returns True if the session cookie should be added to the header.
        The cookie is added if the session was just created or the session id
        is randomized.
        '''
        return self.newsession or self.csid != self.sid

    def fromcookie(self, environ):
        '''Attempt to load the associated session using the identifier from
        the cookie.
        '''
        cookie = SimpleCookie(environ.get('HTTP_COOKIE'))
        morsel = cookie.get(self.cname, None)
        if morsel is not None:
            self.sid, self.session = self.cache.checkout(morsel.value)
            self.csid = morsel.value

    def fromquery(self, environ):
        '''Attempt to load the associated session using the identifier from
        the query string.
        '''
        for name, value in cgi.parse_qsl(environ.get('QUERY_STRING', '')):
            if name == self.fieldname:
                self.sid, self.session = self.cache.checkout(value)
                self.csid, self.inurl = value, True
                break
        
    def get(self, environ):
        '''Attempt to associate with an existing Session.'''
        # Try cookie first.
        self.fromcookie(environ)
        # Next, try query string.
        if self.session is None: self.fromquery(environ)
        if self.session is None:
            self.sid, self.session = self.cache.create()
            self.newsession = True
    
    def close(self):
        '''Checks session back into session cache.'''
        # Check the session back in and get rid of our reference.
        self.cache.checkin(self.sid, self.session)
        self.session = None
   
    def setcookie(self, headers):
        '''Sets a cookie header if needed.''' 
        cookie, name = SimpleCookie(), self.cname
        cookie[name], cookie[name]['path'] = self.sid, self.path
        headers.append(('Set-Cookie', cookie[name].OutputString()))

    def seturl(self, environ):
        '''Encodes session ID in URL, if necessary.'''
        url = [''.join([
            quote(environ.get('SCRIPT_NAME', '')),
            quote(environ.get('PATH_INFO', ''))])]
        if environ.get('QUERY_STRING'):
            url.append('?' + environ['QUERY_STRING'])
        url.append('?' + environ['QUERY_STRING'])
        u = list(urlparse.urlsplit(''.join(url)))
        q = '%s=%s' % (self.fieldname, self.sid)
        if u[3]:
            u[3] = q + '&' + u[3]
        else:
            u[3] = q
        return urlparse.urlunsplit(u)


class Session(object):

    '''WSGI middleware that adds a session service. A SessionService instance
    is passed to the application in environ['com.saddi.service.session'].
    References to this instance should not be saved. (A new instance is
    instantiated with every call to the application.)
    '''

    def __init__(self, application, cache, **kw):
        self.application, self.cache, self.kw = application, cache, kw
        self.key = kw.get('key', 'com.saddi.service.session')

    def __call__(self, environ, start_response):
        service = SessionService(self.cache, environ, **self.kw)
        environ[self.key] = service
        try:
            if service.new:
                def session_response(status, headers, exc_info=None):
                    service.setcookie(headers)
                    return start_response(status, headers, exc_info)
                return self.application(environ, session_response)
            return self.application(environ, start_response)
        finally:            
            service.close()


class URLSession(Session):

    def __call__(self, environ, start_response):
        service = SessionService(self.cache, environ, **self.kw)
        environ[self.key] = service
        try:
            if service.new:
                url = service.seturl(environ)
                start_response('302 Found', [('location', url)])
                return ['You are being redirected to %s' % url]
            return self.application(environ, start_response)
        finally:            
            service.close()
    
        