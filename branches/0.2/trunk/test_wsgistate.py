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

import wsgistate
import unittest
import StringIO
import copy

class TestWsgiForm(unittest.TestCase):
    
    '''Test cases for wsgistate.'''
        
    test_env = {
        'CONTENT_LENGTH': '118',
        'wsgi.multiprocess': 0,
        'wsgi.version': (1, 0),
        'CONTENT_TYPE': 'application/x-www-form-urlencoded',
        'SERVER_NAME': '127.0.0.1',
        'wsgi.run_once': 0,
        'wsgi.errors': StringIO.StringIO(),
        'wsgi.multithread': 0,
        'SCRIPT_NAME': '',
        'wsgi.url_scheme': 'http',
        'wsgi.input': StringIO.StringIO(
'num=12121&str1=test&name=%3Ctag+id%3D%22Test%22%3EThis+is+a+%27test%27+%26+another.%3C%2Ftag%3E&state=NV&Submit=Submit'
            ), 
        'REQUEST_METHOD': 'POST',
        'HTTP_HOST': '127.0.0.1',
        'PATH_INFO': '/',
        'SERVER_PORT': '80',
        'SERVER_PROTOCOL': 'HTTP/1.0'}       

    def dummy_app(self, environ, func):
        return environ

    def dummy_sr(self):
        pass