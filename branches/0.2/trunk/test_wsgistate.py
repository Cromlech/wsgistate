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

'''Unit tests for wsgistate.'''

import unittest
import StringIO
import copy
import os
import time
from wsgistate import *
import urlparse


class TestWsgiState(unittest.TestCase):
    
    '''Test cases for wsgistate.'''
        
    def dummy_sr(self, status, headers, exc_info=None):
        return headers

    def dummy_sr2(self, status, headers, exc_info=None):
        return headers    

    def my_app(self, environ, start_response):
        session = environ['com.saddi.service.session'].session
        count = session.get('count', 0) + 1
        session['count'] = count
        environ['count'] = count
        headers = start_response('200 OK', [])
        if headers: environ['cookie'] = headers[0][1]
        return environ

    def my_app2(self, environ, start_response):
        session = environ['com.saddi.service.session'].session
        count = session.get('count', 0) + 1
        session['count'] = count
        environ['count'] = count
        headers = start_response('200 OK', [])
        return environ    

    def test_sc_set_getitem(self):
        '''Tests __setitem__ and __setitem__ on SimpleCache.'''
        cache = simple.SimpleCache()
        cache['test'] = 'test'
        self.assertEqual(cache['test'], 'test')

    def test_sc_set_get(self):
        '''Tests set and get on SimpleCache.'''
        cache = simple.SimpleCache()
        cache.set('test', 'test')
        self.assertEqual(cache.get('test'), 'test')

    def test_sc_delitem(self):
        '''Tests __delitem__ on SimpleCache.'''
        cache = simple.SimpleCache()
        cache['test'] = 'test'
        del cache['test']
        self.assertEqual(cache.get('test'), None)

    def test_sc_set_get(self):
        '''Tests delete on SimpleCache.'''
        cache = simple.SimpleCache()
        cache.set('test', 'test')
        cache.delete('test')
        self.assertEqual(cache.get('test'), None)

    def test_set_getmany(self):
        '''Tests delete on SimpleCache.'''
        cache = simple.SimpleCache()
        cache.set('test', 'test')
        cache.set('test2', 'test2')
        self.assertEqual(sorted(cache.get_many(('test', 'test2')).values()), ['test', 'test2'])

    def test_sc_in_true(self):
        '''Tests in (true) on SimpleCache.'''
        cache = simple.SimpleCache()
        cache.set('test', 'test')
        self.assertEqual('test' in cache, True)

    def test_sc_in_false(self):
        '''Tests in (false) on SimpleCache.'''
        cache = simple.SimpleCache()
        cache.set('test2', 'test')
        self.assertEqual('test' in cache, False)

    def test_sc_timeout(self):
        '''Tests timeout in SimpleCache.'''
        cache = simple.SimpleCache(timeout=1)
        cache.set('test', 'test')
        time.sleep(1)
        self.assertEqual(cache.get('test'), None)        

    def test_mc_set_getitem(self):
        '''Tests __setitem__ and __setitem__ on MemoryCache.'''
        cache = memory.MemoryCache()
        cache['test'] = 'test'
        self.assertEqual(cache['test'], 'test')

    def test_mc_set_get(self):
        '''Tests set and get on MemoryCache.'''
        cache = memory.MemoryCache()
        cache.set('test', 'test')
        self.assertEqual(cache.get('test'), 'test')

    def test_mc_delitem(self):
        '''Tests __delitem__ on MemoryCache.'''
        cache = memory.MemoryCache()
        cache['test'] = 'test'
        del cache['test']
        self.assertEqual(cache.get('test'), None)

    def test_mc_set_get(self):
        '''Tests delete on MemoryCache.'''
        cache = memory.MemoryCache()
        cache.set('test', 'test')
        cache.delete('test')
        self.assertEqual(cache.get('test'), None)

    def test_mc_set_getmany(self):
        '''Tests delete on MemoryCache.'''
        cache = memory.MemoryCache()
        cache.set('test', 'test')
        cache.set('test2', 'test2')
        self.assertEqual(sorted(cache.get_many(('test', 'test2')).values()), ['test', 'test2'])

    def test_mc_in_true(self):
        '''Tests in (true) on MemoryCache.'''
        cache = memory.MemoryCache()
        cache.set('test', 'test')
        self.assertEqual('test' in cache, True)

    def test_mc_in_false(self):
        '''Tests in (false) on MemoryCache.'''
        cache = memory.MemoryCache()
        cache.set('test2', 'test')
        self.assertEqual('test' in cache, False)

    def test_mc_timeout(self):
        '''Tests timeout in MemoryCache.'''
        cache = memory.MemoryCache(timeout=1)
        cache.set('test', 'test')
        time.sleep(1)
        self.assertEqual(cache.get('test'), None)           

    def test_fc_set_getitem(self):
        '''Tests __setitem__ and __setitem__ on FileCache.'''
        cache = file.FileCache(os.curdir)
        cache['test'] = 'test'
        self.assertEqual(cache['test'], 'test')

    def test_fc_set_get(self):
        '''Tests set and get on FileCache.'''
        cache = file.FileCache(os.curdir)
        cache.set('test', 'test')
        self.assertEqual(cache.get('test'), 'test')

    def test_fc_delitem(self):
        '''Tests __delitem__ on FileCache.'''
        cache = file.FileCache(os.curdir)
        cache['test'] = 'test'
        del cache['test']
        self.assertEqual(cache.get('test'), None)

    def test_fc_set_get(self):
        '''Tests delete on FileCache.'''
        cache = file.FileCache(os.curdir)
        cache.set('test', 'test')
        cache.delete('test')
        self.assertEqual(cache.get('test'), None)

    def test_fc_set_getmany(self):
        '''Tests delete on FileCache.'''
        cache = file.FileCache(os.curdir)
        cache.set('test', 'test')
        cache.set('test2', 'test2')
        self.assertEqual(sorted(cache.get_many(('test', 'test2')).values()), ['test', 'test2'])

    def test_fc_in_true(self):
        '''Tests in (true) on FileCache.'''
        cache = file.FileCache(os.curdir)
        cache.set('test', 'test')
        self.assertEqual('test' in cache, True)

    def test_fc_in_false(self):
        '''Tests in (false) on FileCache.'''
        cache = file.FileCache(os.curdir)
        cache.set('test2', 'test')
        self.assertEqual('test' in cache, False)

    def test_fc_timeout(self):
        '''Tests timeout in FileCache.'''
        cache = file.FileCache(os.curdir, timeout=1)
        cache.set('test', 'test')
        time.sleep(1)
        self.assertEqual(cache.get('test'), None)           
    
    def test_db_set_getitem(self):
        '''Tests __setitem__ and __setitem__ on DbCache.'''
        cache = db.DbCache('sqlite:///:memory:')
        cache['test'] = 'test'
        self.assertEqual(cache['test'], 'test')

    def test_db_set_get(self):
        '''Tests set and get on DbCache.'''
        cache = db.DbCache('sqlite:///:memory:')
        cache.set('test', 'test')
        self.assertEqual(cache.get('test'), 'test')

    def test_db_delitem(self):
        '''Tests __delitem__ on DbCache.'''
        cache = db.DbCache('sqlite:///:memory:')
        cache['test'] = 'test'
        del cache['test']
        self.assertEqual(cache.get('test'), None)

    def test_db_set_get(self):
        '''Tests delete on DbCache.'''
        cache = db.DbCache('sqlite:///:memory:')
        cache.set('test', 'test')
        cache.delete('test')
        self.assertEqual(cache.get('test'), None)

    def test_db_set_getmany(self):
        '''Tests delete on DbCache.'''
        cache = db.DbCache('sqlite:///:memory:')
        cache.set('test', 'test')
        cache.set('test2', 'test2')
        self.assertEqual(sorted(cache.get_many(('test', 'test2')).values()), ['test', 'test2'])

    def test_db_in_true(self):
        '''Tests in (true) on DbCache.'''
        cache = db.DbCache('sqlite:///:memory:')
        cache.set('test', 'test')
        self.assertEqual('test' in cache, True)

    def test_db_in_false(self):
        '''Tests in (false) on DbCache.'''
        cache = db.DbCache('sqlite:///:memory:')
        cache.set('test2', 'test')
        self.assertEqual('test' in cache, False)

    def test_db_timeout(self):
        '''Tests timeout in DbCache.'''
        cache = db.DbCache('sqlite:///:memory:', timeout=1)
        cache.set('test', 'test')
        time.sleep(2)
        self.assertEqual(cache.get('test'), None)         

    def test_mcd_set_getitem(self):
        '''Tests __setitem__ and __setitem__ on MemCache.'''
        cache = memcached.MemCached('localhost')
        cache['test'] = 'test'
        self.assertEqual(cache['test'], 'test')

    def test_mcd_set_get(self):
        '''Tests set and get on MemCache.'''
        cache = memcached.MemCached('localhost')
        cache.set('test', 'test')
        self.assertEqual(cache.get('test'), 'test')

    def test_mcd_delitem(self):
        '''Tests __delitem__ on MemCache.'''
        cache = memcached.MemCached('localhost')
        cache['test'] = 'test'
        del cache['test']
        self.assertEqual(cache.get('test'), None)

    def test_mcd_set_get(self):
        '''Tests delete on MemCache.'''
        cache = memcached.MemCached('localhost')
        cache.set('test', 'test')
        cache.delete('test')
        self.assertEqual(cache.get('test'), None)

    def test_mcd_set_getmany(self):
        '''Tests delete on MemCache.'''
        cache = memcached.MemCached('localhost')
        cache.set('test', 'test')
        cache.set('test2', 'test2')
        self.assertEqual(sorted(cache.get_many(('test', 'test2')).values()), ['test', 'test2'])

    def test_mcd_in_true(self):
        '''Tests in (true) on MemCache.'''
        cache = memcached.MemCached('localhost')
        cache.set('test', 'test')
        self.assertEqual('test' in cache, True)

    def test_mcd_in_false(self):
        '''Tests in (false) on MemCache.'''
        cache = memcached.MemCached('localhost')
        cache.set('test2', 'test')
        self.assertEqual('test' in cache, False)

    def test_mcb_timeout(self):
        '''Tests timeout in DbCache.'''
        cache = memcached.MemCached('localhost', timeout=1)
        cache.set('test', 'test')
        time.sleep(1)
        self.assertEqual(cache.get('test'), None)          

    def test_cookiesession_sc(self):
        '''Tests session cookies with SimpleCache.'''
        testc = simple.SimpleCache()
        cache = session.SessionCache(testc)
        csession = session.CookieSession(self.my_app, cache)
        cookie = csession({}, self.dummy_sr)['cookie']
        csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        self.assertEqual(result['count'], 4)

    def test_cookiesession_mc(self):
        '''Tests session cookies with MemoryCache.'''
        testc = memory.MemoryCache()
        cache = session.SessionCache(testc)
        csession = session.CookieSession(self.my_app, cache)
        cookie = csession({}, self.dummy_sr)['cookie']
        csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        self.assertEqual(result['count'], 4)
        
    def test_cookiesession_fc(self):
        '''Tests session cookies with FileCache.'''
        testc = file.FileCache('.')
        cache = session.SessionCache(testc)
        csession = session.CookieSession(self.my_app, cache)
        cookie = csession({}, self.dummy_sr)['cookie']
        csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        self.assertEqual(result['count'], 4)

    def test_cookiesession_dc(self):
        '''Tests session cookies with DbCache.'''
        testc = db.DbCache('sqlite:///:memory:')
        cache = session.SessionCache(testc)
        csession = session.CookieSession(self.my_app, cache)
        cookie = csession({}, self.dummy_sr)['cookie']
        csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        self.assertEqual(result['count'], 4)

    def test_cookiesession_mdc(self):
        '''Tests session cookies with MemCached.'''
        testc = memcached.MemCached('localhost')
        cache = session.SessionCache(testc)
        csession = session.CookieSession(self.my_app, cache)
        cookie = csession({}, self.dummy_sr)['cookie']
        csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':cookie}, self.dummy_sr)
        self.assertEqual(result['count'], 4)

    def test_random_cookiesession_sc(self):
        '''Tests random session cookies with SimpleCache.'''
        testc = simple.SimpleCache()
        cache = session.SessionCache(testc, random=True)
        csession = session.CookieSession(self.my_app, cache)
        result = csession({}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        self.assertEqual(result['count'], 4)

    def test_random_cookiesession_mc(self):
        '''Tests random session cookies with MemoryCache.'''
        testc = memory.MemoryCache()
        cache = session.SessionCache(testc, random=True)
        csession = session.CookieSession(self.my_app, cache)
        result = csession({}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        self.assertEqual(result['count'], 4)
        
    def test_random_cookiesession_fc(self):
        '''Tests random session cookies with FileCache.'''
        testc = file.FileCache('.')
        cache = session.SessionCache(testc, random=True)
        csession = session.CookieSession(self.my_app, cache)
        result = csession({}, self.dummy_sr)
        cookie = result['cookie']
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        self.assertEqual(result['count'], 4)

    def test_random_cookiesession_dc(self):
        '''Tests random session cookies with DbCache.'''
        testc = db.DbCache('sqlite:///:memory:')
        cache = session.SessionCache(testc, random=True)
        csession = session.CookieSession(self.my_app, cache)
        result = csession({}, self.dummy_sr)
        cookie = result['cookie']
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        self.assertEqual(result['count'], 4)

    def test_random_cookiesession_mdc(self):
        '''Tests random session cookies with MemCached.'''
        testc = memcached.MemCached('localhost')
        cache = session.SessionCache(testc, random=True)
        csession = session.CookieSession(self.my_app, cache)
        result = csession({}, self.dummy_sr)
        cookie = result['cookie']
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        result = csession({'HTTP_COOKIE':result['cookie']}, self.dummy_sr)
        self.assertEqual(result['count'], 4)

    def test_urlsession_sc(self):
        '''Tests URL encoded sessions with SimpleCache.'''
        testc = simple.SimpleCache()
        cache = session.SessionCache(testc)
        csession = session.URLSession(self.my_app2, cache)
        url = csession({}, self.dummy_sr2)[0].split()[-1]
        query = urlparse.urlsplit(url)[3]
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        result = csession({'QUERY_STRING':query}, self.dummy_sr2)
        self.assertEqual(result['count'], 4)

    def test_urlsession_mc(self):
        '''Tests URL encoded sessions with MemoryCache.'''
        testc = memory.MemoryCache()
        cache = session.SessionCache(testc)
        csession = session.URLSession(self.my_app2, cache)
        url = csession({}, self.dummy_sr2)[0].split()[-1]
        query = urlparse.urlsplit(url)[3]
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        result = csession({'QUERY_STRING':query}, self.dummy_sr2)
        self.assertEqual(result['count'], 4)
        
    def test_urlsession_fc(self):
        '''Tests URL encoded sessions with FileCache.'''
        testc = file.FileCache('.')
        cache = session.SessionCache(testc)
        csession = session.URLSession(self.my_app2, cache)
        url = csession({}, self.dummy_sr2)[0].split()[-1]
        query = urlparse.urlsplit(url)[3]
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        result = csession({'QUERY_STRING':query}, self.dummy_sr2)
        self.assertEqual(result['count'], 4)

    def test_urlsession_dc(self):
        '''Tests URL encoded sessions with DbCache.'''
        testc = db.DbCache('sqlite:///:memory:')
        cache = session.SessionCache(testc)
        csession = session.URLSession(self.my_app2, cache)
        url = csession({}, self.dummy_sr2)[0].split()[-1]
        query = urlparse.urlsplit(url)[3]
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        result = csession({'QUERY_STRING':query}, self.dummy_sr2)
        self.assertEqual(result['count'], 4)

    def test_urlsession_mdc(self):
        '''Tests URL encoded sessions with MemCached.'''
        testc = memcached.MemCached('localhost')
        cache = session.SessionCache(testc)
        csession = session.URLSession(self.my_app2, cache)
        url = csession({}, self.dummy_sr2)[0].split()[-1]
        query = urlparse.urlsplit(url)[3]
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        csession({'QUERY_STRING':query}, self.dummy_sr2)
        result = csession({'QUERY_STRING':query}, self.dummy_sr2)
        self.assertEqual(result['count'], 4)
        

if __name__ == '__main__': unittest.main()        