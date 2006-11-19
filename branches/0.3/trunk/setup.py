# Copyright (c) 2006 L. C. Rees.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1.  Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2.  Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# 3.  Neither the name of the Portable Site Information Project nor the names
# of its contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

'''setup - setuptools based setup for wsgistate.'''

import ez_setup
ez_setup.use_setuptools()

try:
    from setuptools import setup
except:
    from distutils.core import setup

setup(name='wsgistate',
      version='0.3.1',
      description='''WSGI session and caching middleware.''',
      long_description='''Session (flup-compatible), caching, memoizing, and HTTP cache control
middleware for WSGI. Supports memory, filesystem, database, and memcached based backends.

Simple memoization example:

from wsgistate.memory import MemoryCache
from wsgistate.cache import memoize

cache = MemoryCache()

@memoize(cache)
def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ['Hello World!']

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    http = make_server('', 8080, app)
    http.serve_forever()

Simple session example:

from wsgistate.memory import MemoryCache
from wsgistate.session import session, SessionCache

cache = MemoryCache()

@session(SessionCache(cache))
def app(environ, start_response):
    session = environ['com.saddi.service.session'].session
    count = session.get('count', 0) + 1
    session['count'] = count
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ['You have been here %d times!\n' % count]

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    http = make_server('', 8080, app)
    http.serve_forever()''',
      author='L. C. Rees',
      author_email='lcrees@gmail.com',
      license='BSD',
      packages = ['wsgistate'],
      test_suite='wsgistate.tests',
      zip_safe = True,
      keywords='WSGI session caching persistence memoizing HTTP Web',
      classifiers=['Development Status :: 3 - Alpha',
                    'Environment :: Web Environment',
                    'License :: OSI Approved :: BSD License',
                    'Natural Language :: English',
                    'Operating System :: OS Independent',
                    'Programming Language :: Python',
                    'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware'],
      install_requires = ['SQLAlchemy'],)