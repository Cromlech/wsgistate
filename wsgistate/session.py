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
import urllib
import sha
import random
import sys
from Cookie import SimpleCookie
from urllib import quote
try:
    import threading
except ImportError:
    import dummy_threading as threading

from wsgistate import synchronized

__all__ = ['SessionCache', 'SessionManager', 'CookieSession', 'URLSession',
     'session', 'urlsession']

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
        self._lock = threading.Condition()
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

    @synchronized
    def create(self):
        '''Create a new session with a unique identifier.

        The newly-created session should eventually be released by
        a call to checkin().
        '''
        sid, sess = self.newid(), dict()
        self.cache.set(sid, sess)
        self.checkedout[sid] = sess
        return sid, sess

    @synchronized
    def checkout(self, sid):
        '''Checks out a session for use. Returns the session if it exists,
        otherwise returns None. If this call succeeds, the session
        will be touch()'ed and locked from use by other processes.
        Therefore, it should eventually be released by a call to
        checkin().

        @param sid Session id
        '''
        # If we know it's already checked out, block.
        while sid in self.checkedout: self._lock.wait()
        sess = self.cache.get(sid)
        if sess is not None:
            # Randomize session id if set and remove old session id
            if self._random:
                self.cache.delete(sid)
                sid = self.newid()
            # Put in checkout
            self.checkedout[sid] = sess
            return sid, sess
        return None, None

    @synchronized
    def checkin(self, sid, sess):
        '''Returns the session for use by other threads/processes.

        @param sid Session id
        @param session Session dictionary
        '''
        del self.checkedout[sid]
        self.cache.set(sid, sess)
        self._lock.notify()

    @synchronized
    def shutdown(self):
        '''Clean up outstanding sessions.'''
        if not self._closed:
            # Save or delete any sessions that are still out there.
            for sid, sess in self.checkedout.iteritems():
                self.cache.set(sid, sess)
            self.checkedout.clear()
            self.cache._cull()
            self._closed = True

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

    def __init__(self, cache, environ, **kw):
        self._cache = cache
        self._fieldname = kw.get('fieldname', '_SID_')
        self._path = kw.get('path', '/')
        self.session = self._sid = self._csid = None
        self.expired = self.current = self.new = self.inurl = False
        self._get(environ)

    def _fromcookie(self, environ):
        '''Attempt to load the associated session using the identifier from
        the cookie.
        '''
        cookie = SimpleCookie(environ.get('HTTP_COOKIE'))
        morsel = cookie.get(self._fieldname, None)
        if morsel is not None:
            self._sid, self.session = self._cache.checkout(morsel.value)
            self._csid = morsel.value
            if self._csid != self._sid: self.new = True

    def _fromquery(self, environ):
        '''Attempt to load the associated session using the identifier from
        the query string.
        '''
        self._qdict = dict(cgi.parse_qsl(environ.get('QUERY_STRING', '')))
        value = self._qdict.get(self._fieldname)
        if value is not None:
            self._sid, self.session = self._cache.checkout(value)
            if self._sid is not None:
                self._csid, self.inurl = value, True
                if self._csid != self._sid: self.current = self.new = True

    def _get(self, environ):
        '''Attempt to associate with an existing Session.'''
        # Try cookie first.
        self._fromcookie(environ)
        # Next, try query string.
        if self.session is None: self._fromquery(environ)
        if self.session is None:
            self._sid, self.session = self._cache.create()
            self.new = True

    def close(self):
        '''Checks session back into session cache.'''
        # Check the session back in and get rid of our reference.
        self._cache.checkin(self._sid, self.session)
        self.session = None

    def setcookie(self, headers):
        '''Sets a cookie header if needed.'''
        cookie, name = SimpleCookie(), self._fieldname
        cookie[name], cookie[name]['path'] = self._sid, self._path
        headers.append(('Set-Cookie', cookie[name].OutputString()))

    def seturl(self, environ):
        '''Encodes session ID in URL, if necessary.'''
        path = ''.join([quote(environ.get('SCRIPT_NAME', '')),
            quote(environ.get('PATH_INFO', ''))])
        # Get query
        if self._qdict:
            self._qdict[self._fieldname] = self._sid
        else:
            self._qdict = {self._fieldname:self._sid}
        return '?'.join([path, urllib.urlencode(self._qdict)])

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
        # Always close session
        finally:
            sess.close()


class CookieSession(_Session):

    '''WSGI middleware that adds a session service in a cookie.'''

    def _initial(self, environ, start_response):
        '''Initial response to a cookie session.'''
        def session_response(status, headers, exc_info=None):
            environ[self.key].setcookie(headers)
            return start_response(status, headers, exc_info)
        return self.application(environ, session_response)


class URLSession(_Session):

    '''WSGI middleware that adds a session service in a URL query string.'''

    def _initial(self, environ, start_response):
        '''Initial response to a query encoded session.'''
        url = environ[self.key].seturl(environ)
        # Redirect to URL with session in query component
        start_response('302 Found', [('location', url)])
        return ['The browser is being redirected to %s' % url]