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
import md5
import random
import sys
from Cookie import SimpleCookie
try:
    import threading
except ImportError:
    import dummy_threading as threading

__all__ = ['SessionService', 'SessionCache', 'Session', 'session']    

def _shutdown(ref):
    cache = ref()
    if cache is not None: cache.shutdown()
    
def session(cache, **kw):
    '''Decorator for sessions.'''
    def decorator(application):
        return Session(self, application, cache, **kw)
    return decorator


class SessionCache(object):
    
    '''Abstract base class for session stores. You first acquire a session by
    calling create() or checkout(). After using the session,
    you must call checkin(). You must not keep references to sessions
    outside of a check in/check out block. Always obtain a fresh reference.

    After timeout minutes of inactivity, sessions are deleted.
    '''
    
    # Would be nice if len(idchars) were some power of 2.
    idchars = '-_'.join([string.digits, string.ascii_letters])  
    length = 32

    def __init__(self, cache, **kw):
        super(SessionCache, self).__init__()
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
        "Returns session key that isn't being used."
        sid = None
        for num in xrange(10000):
            sid = md5.new(str(random.randint(0, sys.maxint - 1)) +
                str(random.randint(0, sys.maxint - 1)) + self._secret).hexdigest()
            if sid not in self._cache: break
        return sid
            

# SessionMiddleware stuff.

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

    _expiredid = 'expired session'

    def __init__(self, cache, environ, **kw):
        self._cache = cache
        self._cookiename = kw.get('cookiename', '_SID_')
        self._fieldname = kw.get('fieldname', '_SID_')
        self._path = kw.get('path', '/')
        self._session, self._sid, self._csid = None, None, None
        self._newsession, self._expired, self.inurl = False, False, False
        if __debug__: self._closed = False
        self.get(environ)

    def _fromcookie(self, environ):
        '''Attempt to load the associated session using the identifier from
        the cookie.
        '''
        cookie = SimpleCookie(environ.get('HTTP_COOKIE'))
        morsel = cookie.get(self._cookiename, None)
        if morsel is not None:
            self._sid, self._session = self._cache.checkout(morsel.value)
            self._expired, self._csid = self._session is None, morsel.value

    def _fromquery(self, environ):
        '''
        Attempt to load the associated session using the identifier from
        the query string.
        '''
        qs = cgi.parse_qsl(environ.get('QUERY_STRING', ''))
        for name, value in qs:
            if name == self._fieldname:
                self._sid, self._session = self._cache.checkout(value)
                self._expired, self._csid = self._session is None, value
                self.inurl = True
                break
        
    def get(self, environ):
        '''Attempt to associate with an existing Session.'''
        # Try cookie first.
        self._fromcookie(environ)
        # Next, try query string.
        if self._session is None: self._fromquery(environ)

    def _addcookie(self):
        '''Returns True if the session cookie should be added to the header
        (if not encoding the session ID in the URL). The cookie is added if
        one of these three conditions are true: a) the session was just
        created, b) the session is no longer valid, or c) the client is
        associated with a non-existent session.
        '''
        return self._newsession or \
               (self._session is not None) or \
               (self._session is None and self._expired)
        
    def setcookie(self, headers):
        '''Adds Set-Cookie header if needed.'''
        if not self.inurl:           
            expire = False
            # Reassign cookie if session id is randomized
            if self._csid != self._sid or self._addcookie():                
                if self._sid is None: sid, expire = self._expiredid, True
                cookie, name = SimpleCookie(), self._cookiename
                cookie[name], cookie[name]['path'] = self._sid, self._path
                if expire:
                    # Expire cookie
                    cookie[name]['expires'] = -365*24*60*60
                    cookie[name]['max-age'] = 0
                headers.append(('Set-Cookie', cookie[name].OutputString()))
    
    def close(self):
        '''Checks session back into session cache.'''
        if self._session is None: return
        # Check the session back in and get rid of our reference.
        sid = self._cache.checkin(self._sid, self._session)
        self._session = None
        if __debug__: self._closed = True

    # Public API

    @property
    def session(self):
        '''Returns the Session object associated with this client.'''
        assert not self._closed
        if self._session is None:
            self._sid, self._session = self._cache.create()
            self._newsession = True
        assert self._session is not None
        return self._session

    @property
    def current(self):
        '''True if a Session currently exists for this client'''
        assert not self._closed
        return self._session is not None

    @property
    def new(self):
        '''True if the Session was created in this transaction.'''
        assert not self._closed
        return self._newsession

    @property    
    def expired(self):
        '''True if the client was associated with a non-existent Session'''
        assert not self._closed
        return self._expired

    # Utilities

    def seturl(self, url):
        '''Encodes session ID in URL, if necessary.'''
        assert not self._closed
        if not self.inurl or self._session is None: return url
        u = list(urlparse.urlsplit(url))
        q = '%s=%s' % (self._fieldname, self.close())
        if u[3]:
            u[3] = q + '&' + u[3]
        else:
            u[3] = q
        return urlparse.urlunsplit(u)


class Session(object):

    '''WSGI middleware that adds a session service. A SessionService instance
    is passed to the application in environ['com.saddi.service.session'].
    A references to this instance should not be saved. (A new instance is
    instantiated with every call to the application.)
    '''

    def __init__(self, application, cache, **kw):
        self._application, self._cache = application, cache 
        self._sessionkey = kw.get('sessionkey', 'com.saddi.service.session')
        self._kw = kw

    def __call__(self, environ, start_response):
        service = SessionService(self._cache, environ, **self._kw)
        environ[self._sessionkey] = service
        def my_start_response(status, headers, exc_info=None):
            service.setcookie(headers)
            service.close()
            return start_response(status, headers, exc_info)
        try:
            return self._application(environ, my_start_response)
        except:
            # If anything goes wrong, ensure the session is checked back in.
            service.close()