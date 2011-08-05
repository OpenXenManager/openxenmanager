#!/usr/bin/env python
"""
put.py - Python HTTP PUT Client
Copyright 2006, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

Basic API usage, once with optional auth: 

import put
put.putname('test.txt', 'http://example.org/test')

f = open('test.txt', 'rb')
put.putfile(f, 'http://example.org/test')
f.close()

bytes = open('test.txt', 'rb').read()
auth = {'username': 'myuser', 'password': 'mypass'}
put.put(bytes, 'http://example.org/test', **auth)
"""

import sys, httplib, urlparse
from optparse import OptionParser

# True by default when running as a script
# Otherwise, we turn the noise off...
verbose = False

def barf(msg): 
   print >> sys.stderr, "Error! %s" % msg
   sys.exit(1)

if sys.version_info < (2, 4): 
   barf("Requires Python 2.4+")

def parseuri(uri): 
   """Parse URI, return (host, port, path) tuple.

   >>> parseuri('http://example.org/testing?somequery#frag')
   ('example.org', 80, '/testing?somequery')
   >>> parseuri('http://example.net:8080/test.html')
   ('example.net', 8080, '/test.html')
   """

   scheme, netplace, path, query, fragid = urlparse.urlsplit(uri)

   if ':' in netplace: 
      host, port = netplace.split(':', 2)
      port = int(port)
   else: host, port = netplace, 80

   if query: path += '?' + query

   return host, port, path

def putfile(f, uri, username=None, password=None): 
   """HTTP PUT the file f to uri, with optional auth data."""
   host, port, path = parseuri(uri)

   redirect = set([301, 302, 307])
   authenticate = set([401])
   okay = set([200, 201, 204])

   authorized = False
   authorization = None
   tries = 0

   while True: 
      # Attempt to HTTP PUT the data
      h = httplib.HTTPConnection(host, port)

      h.putrequest('PUT', path)

      h.putheader('User-Agent', 'put.py/1.0')
      h.putheader('Connection', 'keep-alive')
      h.putheader('Transfer-Encoding', 'chunked')
      h.putheader('Expect', '100-continue')
      h.putheader('Accept', '*/*')
      if authorization: 
         h.putheader('Authorization', authorization)
      h.endheaders()

      # Chunked transfer encoding
      # Cf. 'All HTTP/1.1 applications MUST be able to receive and 
      # decode the "chunked" transfer-coding'
      # - http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html
      while True: 
         bytes = f.read(1024)
         if not bytes: break
         length = len(bytes)
         #h.send('%X\r\n' % length)
         h.send(bytes)
      #h.send('0\r\n\r\n')

      resp = h.getresponse()
      status = resp.status # an int

      # Got a response, now decide how to act upon it
      if status in redirect: 
         location = resp.getheader('Location')
         uri = urlparse.urljoin(uri, location)
         host, port, path = parseuri(uri)

         # We may have to authenticate again
         if authorization: 
            authorization = None

      elif status in authenticate: 
         # If we've done this already, break
         if authorization: 
            # barf("Going around in authentication circles")
            barf("Authentication failed")

         if not (username and password): 
            barf("Need a username and password to authenticate with")

         # Get the scheme: Basic or Digest?
         wwwauth = resp.msg['www-authenticate'] # We may need this again
         wauth = wwwauth.lstrip(' \t') # Hence use wauth not wwwauth here
         wauth = wwwauth.replace('\t', ' ')
         i = wauth.index(' ')
         scheme = wauth[:i].lower()

         if scheme in set(['basic', 'digest']): 
            if verbose: 
               msg = "Performing %s Authentication..." % scheme.capitalize()
               print >> sys.stderr, msg
         else: barf("Unknown authentication scheme: %s" % scheme)

         if scheme == 'basic': 
            import base64
            userpass = username + ':' + password
            userpass = base64.encodestring(userpass).strip()
            authorized, authorization = True, 'Basic ' + userpass

         elif scheme == 'digest': 
            if verbose: 
               msg = "uses fragile, undocumented features in urllib2"
               print >> sys.stderr, "Warning! Digest Auth %s" % msg

            import urllib2 # See warning above

            passwd = type('Password', (object,), {
               'find_user_password': lambda self, *args: (username, password), 
               'add_password': lambda self, *args: None
            })()

            req = type('Request', (object,), { 
               'get_full_url': lambda self: uri, 
               'has_data': lambda self: None, 
               'get_method': lambda self: 'PUT', 
               'get_selector': lambda self: path
            })()

            # Cf. urllib2.AbstractDigestAuthHandler.retry_http_digest_auth
            auth = urllib2.AbstractDigestAuthHandler(passwd)
            token, challenge = wwwauth.split(' ', 1)
            chal = urllib2.parse_keqv_list(urllib2.parse_http_list(challenge))
            userpass = auth.get_authorization(req, chal)
            authorized, authorization = True, 'Digest ' + userpass

      elif status in okay: 
         if (username and password) and (not authorized): 
            msg = "Warning! The supplied username and password went unused"
            print >> sys.stderr, msg

         if verbose: 
            resultLine = "Success! Resource %s"
            statuses = {200: 'modified', 201: 'created', 204: 'modified'}
            print resultLine % statuses[status]

            statusLine = "Response-Status: %s %s"
            print statusLine % (status, resp.reason)

            body = resp.read(58)
            body = body.rstrip('\r\n')
            body = body.encode('string_escape')

            if len(body) >= 58: 
               body = body[:57] + '[...]'

            bodyLine = 'Response-Body: "%s"'
            print bodyLine % body
         break

      # @@ raise PutError, do the catching in main?
      else: barf('Got "%s %s"' % (status, resp.reason))

      tries += 1
      if tries >= 50: 
         barf("Too many redirects")

   return status, resp

def putname(fn, uri, username=None, password=None): 
   """HTTP PUT the file with filename fn to uri, with optional auth data."""
   auth = {'username': username, 'password': password}

   if fn != '-': 
      f = open(fn, 'rb')
      status, resp = putfile(f, uri, **auth)
      f.close()
   else: status, resp = putfile(sys.stdin, uri, **auth)

   return status, resp

def put(s, uri, username=None, password=None): 
   """HTTP PUT the string s to uri, with optional auth data."""
   try: from cStringIO import StringIO
   except ImportError: 
      from StringIO import StringIO

   f = StringIO(s)
   f.seek(0)
   status, resp = putfile(f, uri, username=username, password=password)
   f.close()

   return status, conn

def main(argv=None): 
   usage = ('%prog [options] filename uri\n' + 
            'The filename may be - for stdin\n' + 
            'Use command line password at your own risk!')

   parser = OptionParser(usage=usage)
   parser.add_option('-u', '--username', help='HTTP Auth username')
   parser.add_option('-p', '--password', help='HTTP Auth password')
   parser.add_option('-q', '--quiet', action='store_true', help="shhh!")
   options, args = parser.parse_args(argv)

   if len(args) != 2: 
      parser.error("Requires two arguments, filename and uri")

   fn, uri = args
   if not uri.startswith('http:'): 
      parser.error("The uri argument must start with 'http:'")

   if ((options.username and not options.password) or 
       (options.password and not options.username)): 
      parser.error("Must have both username and password or neither")

   global verbose
   verbose = (not options.quiet)

   auth = {'username': options.username, 'password': options.password}
   putname(fn, uri, **auth)

if __name__ == '__main__': 
   main()
