# Copyright (c) 2006-2007 L. C. Rees.  All rights reserved.
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

try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='wsgistate',
    version='0.4.3',
    description='''WSGI session and caching middleware.''',
    long_description='''Session (flup-compatible), caching, memoizing,
and HTTP cache control middleware for WSGI. Supports memory, filesystem,
database, and memcached based backends.

# Simple memoization example:

from wsgistate.memory import memoize

@memoize()
def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ['Hello World!']

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    http = make_server('', 8080, app)
    http.serve_forever()

# Simple session example:

from wsgistate.memory import session

@session()
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
    url='http://pypi.python.org/pypi/wsgistate/',
    license='BSD',
    packages=['wsgistate', 'wsgistate.tests'],
    test_suite='wsgistate.tests',
    zip_safe=False,
    keywords='WSGI session caching persistence memoizing HTTP Web',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
    ],
    install_requires=['SQLAlchemy>0.3', 'python-memcached>=1.50'],
    entry_points='''
    [paste.filter_factory]
    file_memo=wsgistate.file:filememo_deploy
    firebird_memo=wsgistate.db:dbmemo_deploy
    memcache_memo=wsgistate.memcached:mcmemo_deploy
    memory_memo=wsgistate.memory:memorymemo_deploy
    mssql_memo=wsgistate.db:dbmemo_deploy
    mysql_memo=wsgistate.db:dbmemo_deploy
    oracle_memo=wsgistate.db:dbmemo_deploy
    postgres_memo=wsgistate.db:dbmemo_deploy
    simple_memo=wsgistate.simple:simplememo_deploy
    sqlite_memo=wsgistate.db:dbmemo_deploy
    file_session=wsgistate.file:filesess_deploy
    firebird_session=wsgistate.db:dbsess_deploy
    memcache_session=wsgistate.memcached:mcsess_deploy
    memory_session=wsgistate.memory:memorysess_deploy
    mssql_session=wsgistate.db:dbsess_deploy
    mysql_session=wsgistate.db:dbsess_deploy
    oracle_session=wsgistate.db:dbsess_deploy
    postgres_session=wsgistate.db:dbsess_deploy
    simple_session=wsgistate.simple:simplesess_deploy
    sqlite_session=wsgistate.db:dbsess_deploy
    file_urlsess=wsgistate.file:fileurlsess_deploy
    firebird_urlsess=wsgistate.db:dburlsess_deploy
    memcache_urlsess=wsgistate.memcached:mcurlsess_deploy
    memory_urlsess=wsgistate.memory:memoryurlsess_deploy
    mssql_urlsess=wsgistate.db:dburlsess_deploy
    mysql_urlsess=wsgistate.db:dburlsess_deploy
    oracle_urlsess=wsgistate.db:dburlsess_deploy
    postgres_urlsess=wsgistate.db:dburlsess_deploy
    simple_urlsess=wsgistate.simple:simpleurlsess_deploy
    sqlite_urlsess=wsgistate.db:dburlsess_deploy
    '''
)
