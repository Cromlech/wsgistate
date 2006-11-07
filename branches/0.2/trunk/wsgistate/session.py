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

<<<<<<< .mine
__all__ = ['SessionCache', 'SessionManager', 'CookieSession', 'URLSession', 'session',
    'urlsession']
=======
__all__ = ['SessionCache', 'Session', 'session', 'urlsession']
>>>>>>> .r10

def _shutdown(ref):
    cache = ref()
    if cache is not None: cache.shutdown()
    
def session(cache, **kw):
    '''Decorator for sessions.'''
    def decorator(application):
        return CookieSession(application, cache, **kw)
    return decorator

def urlsession(cache, **kw):
    '''Decorator for URL encoded sessions.'''
    def decorator(application):
        return URLSession(application, cache, **kw)
    return decorator


class SessionCache(object):
    
    '''Base class for session cache. You first acquire a session by
    calling create() or checkout(). After using the session, you must call
    checkin(). You must not keep references to sessions outside of a check
    in/check out block. Always obtain a fresh reference.
    '''
    # Would be nice if len(idchars) were some power of 2.
    idchars = '-_'.join([string.digits, string.ascii_letters])
    length = 64

    def __init__(self, cache, **kw):
        self.lock = threading.Condition()
        self.checkedout, self._closed, self.cache = dict(), False, cache
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
        self.lock.acquire()
        try:
<<<<<<< .mine
            sid, sess = self.newid(), dict()
            self.cache.set(sid, sess)            
            self.checkedout[sid] = sess
            return sid, sess
=======
            sid, session = self.newid(), dict()
            self.cache.set(sid, session)            
            self.checkedout[sid] = session
            return sid, session
>>>>>>> .r10
        finally:
            self.lock.release()

    def checkout(self, sid):
        '''Checks out a session for use. Returns the session if it exists,
        otherwise returns None. If this call succeeds, the session
        will be touch()'ed and locked from use by other processes.
        Therefore, it should eventually be released by a call to
        checkin().

        @param sid Session id        
        '''
        self.lock.acquire()
        try:
            # If we know it's already checked out, block.
<<<<<<< .mine
            while sid in self.checkedout: self.lock.wait()
            sess = self.cache.get(sid)
            if sess is not None:
=======
            while sid in self.checkedout: self.lock.wait()
            session = self.cache.get(sid)
            if session is not None:
>>>>>>> .r10
                # Randomize session id if set and remove old session id
                if self._random:
                    self.cache.delete(sid)
                    sid = self.newid()
                # Put in checkout
<<<<<<< .mine
                self.checkedout[sid] = sess
                return sid, sess
            return None, None
=======
                self.checkedout[sid] = session
                return sid, session
            return None, None
>>>>>>> .r10
        finally:
            self.lock.release()

    def checkin(self, sid, sess):
        '''Returns the session for use by other threads/processes.

        @param sid Session id
        @param session Session dictionary
        '''
        self.lock.acquire()
        try:
<<<<<<< .mine
            del self.checkedout[sid]
            self.cache.set(sid, sess)
            self.lock.notify()
=======
            del self.checkedout[sid]
            self.cache.set(sid, session)
            self.lock.notify()
>>>>>>> .r10
        finally:            
            self.lock.release()

    def shutdown(self):
        '''Clean up outstanding sessions.'''
        self.lock.acquire()
        try:
            if not self._closed:
<<<<<<< .mine
                # Save or delete any sessions that are still out there.
                for sid, sess in self.checkedout.iteritems():
                    self.cache.set(sid, sess)
                self.cache._cull()
                self.checkedout.clear()
=======
                # Save or delete any sessions that are still out there.
                for sid, session in self.checkedout.iteritems():
                    self.cache.set(sid, session)
                self.cache._cull()
                self.checkedout.clear()
>>>>>>> .r10
                self._closed = True
        finally:
            self.lock.release()

    # Utilities

    def newid(self):
        'Returns session key that is not being used.'
        sid = None
        for num in xrange(10000):
            sid = sha.new(str(random.randint(0, sys.maxint - 1)) +
                str(random.randint(0, sys.maxint - 1)) + self._secret).hexdigest()
            if sid not in self.cache: break
        return sid
            

class SessionManager(object):

    '''Session Manager.'''  

<<<<<<< .mine
=======
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

>>>>>>> .r10
    def __init__(self, cache, environ, **kw):
<<<<<<< .mine
        self._cache = cache
        self._fieldname = kw.get('fieldname', '_SID_')
        self._path = kw.get('path', '/')
        self.session = self._sid = self._csid = None
        self.expired = self.current = self._new = self.inurl = False
        self._get(environ)
=======
        self.cache = cache
        self.cname = kw.get('cookiename', '_SID_')
        self.fieldname = kw.get('fieldname', '_SID_')
        self.path = kw.get('path', '/')
        self.session = self.sid = self.csid = None
        self.newsession = self.expired = self.current = self.inurl = False
        self.get(environ)
>>>>>>> .r10

    @property
    def new(self):
<<<<<<< .mine
        '''Returns True if a session needs to be added to a cookie or URL query.
        The cookie is added if the session was just created or the session id
        is randomized.
=======
        '''Returns True if the session cookie should be added to the header.
        The cookie is added if the session was just created or the session id
        is randomized.
>>>>>>> .r10
        '''
<<<<<<< .mine
        return self._new or self._csid != self._sid
=======
        return self.newsession or self.csid != self.sid
>>>>>>> .r10

    def fromcookie(self, environ):
        '''Attempt to load the associated session using the identifier from
        the cookie.
        '''
        cookie = SimpleCookie(environ.get('HTTP_COOKIE'))
<<<<<<< .mine
        morsel = cookie.get(self._fieldname, None)
=======
        morsel = cookie.get(self.cname, None)
>>>>>>> .r10
        if morsel is not None:
<<<<<<< .mine
            self._sid, self.session = self._cache.checkout(morsel.value)            
            self._csid = morsel.value
=======
            self.sid, self.session = self.cache.checkout(morsel.value)
            self.csid = morsel.value
>>>>>>> .r10

    def fromquery(self, environ):
        '''Attempt to load the associated session using the identifier from
        the query string.
        '''
<<<<<<< .mine
        qdict = dict(cgi.parse_qsl(environ.get('QUERY_STRING', '')))
        value = qdict.get(self._fieldname)
        if value is not None:
            self._sid, self.session = self._cache.checkout(value)
            self._csid, self.inurl = value, True
            print value, self.session
=======
        for name, value in cgi.parse_qsl(environ.get('QUERY_STRING', '')):
            if name == self.fieldname:
                self.sid, self.session = self.cache.checkout(value)
                self.csid, self.inurl = value, True
                break
>>>>>>> .r10
        
    def get(self, environ):
        '''Attempt to associate with an existing Session.'''
        # Try cookie first.
        self.fromcookie(environ)
        # Next, try query string.
        if self.session is None: self.fromquery(environ)
        if self.session is None:
<<<<<<< .mine
            self._sid, self.session = self._cache.create()
            self._new = True
=======
            self.sid, self.session = self.cache.create()
            self.newsession = True
>>>>>>> .r10
    
    def close(self):
        '''Checks session back into session cache.'''
        # Check the session back in and get rid of our reference.
        self.cache.checkin(self.sid, self.session)
        self.session = None
        print 'close'
   
    def setcookie(self, headers):
        '''Sets a cookie header if needed.''' 
<<<<<<< .mine
        cookie, name = SimpleCookie(), self._fieldname
        cookie[name], cookie[name]['path'] = self._sid, self._path
        headers.append(('Set-Cookie', cookie[name].OutputString()))
=======
        cookie, name = SimpleCookie(), self.cname
        cookie[name], cookie[name]['path'] = self.sid, self.path
        headers.append(('Set-Cookie', cookie[name].OutputString()))
>>>>>>> .r10

    def seturl(self, environ):
        '''Encodes session ID in URL, if necessary.'''
        # Get path
        url = [''.join([
            quote(environ.get('SCRIPT_NAME', '')),
            quote(environ.get('PATH_INFO', ''))])]
        # Get query
        qs = environ.get('QUERY_STRING')
        if qs is not None: url.append('?' + qs)
        u = list(urlparse.urlsplit(''.join(url)))
        q = '%s=%s' % (self.fieldname, self.sid)
        # Encode session in query string
        if u[3]:
            u[3] = q + '&' + u[3]
        else:
            u[3] = q
        return urlparse.urlunsplit(u)


class _Session(object):

    '''WSGI middleware that adds a session service.'''

    def __init__(self, application, cache, **kw):
        self.application, self.cache, self.kw = application, cache, kw
        # environ key
        self.key = kw.get('key', 'com.saddi.service.session')

    def __call__(self, environ, start_response):
        # New session manager instance each time
        sess = SessionManager(self.cache, environ, **self.kw)
        environ[self.key] = sess
        try:
            # Return intial response if new or session id is random
            if sess.new: return self._initial(environ, start_response)                
            return self.application(environ, start_response)
<<<<<<< .mine
        # Always close session
        finally:            
            sess.close()
            
=======
        finally:            
            service.close()
>>>>>>> .r10

class CookieSession(_Session):            

    '''WSGI middleware that adds a session service in a cookie.'''

<<<<<<< .mine
    def _initial(self, environ, start_response):
        '''Initial response to a cookie session.'''
        def session_response(status, headers, exc_info=None):
            environ[self.key].setcookie(headers)
            return start_response(status, headers, exc_info)
        return self.application(environ, session_response)


class URLSession(_Session):
=======
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
>>>>>>> .r10
    
    '''WSGI middleware that adds a session service in a URL query string.'''

    def _initial(self, environ, start_response):
        '''Initial response to a query encoded session.'''
        url = environ[self.key].seturl(environ)
        # Redirect to URL with session in query component
        start_response('302 Found', [('location', url)])
        return ['You are being redirected to %s' % url]