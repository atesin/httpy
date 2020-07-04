##!/bin/python

# index, search for these labels including hashes

### staticConfig
### mainFunctionDef
### subFunctions
### checkLinkPersistence
### mainFunctionRun
### dirList
########################
### printHelp
### printConf
### includeConf
### testConf
### utilFunctions
### mainLoop


### staticConfig

import os
defaults = \
{
    #'hostname':  os.environ.get('HOSTNAME', os.environ.get('COMPUTERNAME', '*')),
    'software': 'HTTPy/7.0',
    'protocol': 'HTTP/1.1 ', # used for response line, note the trailing space
    'gateway' : 'CGI/1.1'
}


### mainFunctionDef (program flow continues in ### mainFunctionRun)

def mainLoop():

    ### subFunctions
    
    # this function should terminate the request,
    # call it with return() this way: return(sendResponse(statusCode [, bytesData]))
    def sendResponse(status, content=b''):
        ### checkLinkPersistence
        if True or req['SERVER_PROTOCOL'] < 'HTTP/1.1' and req['HTTP_CONNECTION'] != 'keep-alive':
            response.add('Connection: close')
            req['HTTP_CONNECTION'] = 'close'
        # craft response headers
        if req['REQUEST_METHOD'] == 'HEAD':
            content = b''
        headers  = f'{defaults["software"]} {status}\r\n'
        headers += '\r\n'.join(response)
        headers += f'\r\nContent-Length: {len(content)}\r\n\r\n'
        os.write(1, bytes(headers, 'utf_8')+content)
        # log info and close connection if applies
        req['REQUEST_STATUS'] = status[:3]
        log(strFormatMap(logFormat, req))
        if req['HTTP_CONNECTION'] == 'close':
            exit()
        
        
    ### mainFunctionRun
        
    req = collections.defaultdict(lambda: '*') # now can use req[index] safely
    #response = set() # response headers, string won't inherit to sub scopes
    
    # read first line skipping blank ones
    while True:
        try:
            req['THE_REQUEST'] = input()
        except (EOFError, KeyboardInterrupt):
            exit()
        if req['THE_REQUEST']:
            break

    # possible request found, populate request variables
    now = datetime.now()
    
    req['TIME'] = now.isoformat(' ', 'seconds') # now.strftime('%Y%m%d%H%M%S')
    req['TIME_WDAY'] = now.strftime('%w') # 0-6 = sun-sat
    # req['SERVER_HOST'] = defaults['hostname'] # not specified or needed anywhere
    req['SERVER_SOFTWARE'] = defaults['software']
    req['SERVER_ADDR'] = os.environ.get('NCAT_LOCAL_ADDR', '*')
    req['SERVER_PORT'] = os.environ.get('NCAT_LOCAL_PORT', '*')
    req['REMOTE_ADDR'] = os.environ.get('NCAT_REMOTE_ADDR', '*')
    req['REMOTE_PORT'] = os.environ.get('NCAT_REMOTE_PORT', '*')
    response = {'Server: '+defaults['software']} # response headers, str won't inherit to sub scopes
    
    # validate request line
    reqFields = req['THE_REQUEST'].split(' ', 2)
    if not (len(reqFields) > 2 and reqFields[1].startswith('/')):
        return sendResponse('400 Bad Request')
    
    # parse request line
    # THE_REQUEST = REQUEST_METHOD REQUEST_URI SERVER_PROTOCOL
    # REQUEST_URI = SCRIPT_NAME?QUERY_STRING#FRAGMENT
    req['REQUEST_METHOD'], req['REQUEST_URI'], req['SERVER_PROTOCOL'] = reqFields
    seg = req['REQUEST_URI'].split('#', 1)[0].split('?', 1)
    req['SCRIPT_NAME'] = seg[0]
    if len(seg) > 1:
        req['QUERY_STRING'] = seg[1]
    
    # validate method
    if req['REQUEST_METHOD'] not in ('GET', 'HEAD', 'POST'):
        return sendResponse('405 Method Not Allowed')
    
    # request line parsed, now go with headers
    
    # get headers until blank line found (or malformed header)
    while True:
        try:
            header = input().split(': ', 1)
        except EOFError:
            exit()
        if len(header) < 2:
            if header[0]:
                return sendResponse('400 Bad Request')
            break
        # yes i know HTTP_ should be taken from SERVER_PROTOCOL, but wtf
        req['HTTP_'+header[0].upper().replace('-', '_')] = header[1]
        
    # get (and flush) request body if any
    if 'HTTP_CONTENT_LENGTH' in req:
        req['POST_DATA'] = sys.stdin.read(int(req.get('HTTP_CONTENT_LENGTH', '0'))) # str


    # CONVERT ARRAY: FROM NUMERIC (LIST) -> TO ASSOCIATIVE (DICTIONARY)
    # dictOfWords = { i : listOfStr[i] for i in range(0, len(listOfStr) ) }
    
    
    # normalize environment variables before apply rules
    req['GATEWAY_INTERFACE'] = defaults['gateway']
    if req['SERVER_PORT'] == '443': # i don't have another better way to guess it
        req['REQUEST_SCHEME'] = 'https'
        req['HTTPS'] = 'on'
        req['SERVER_NAME'] = 'https://'+req['HTTP_HOST'] # Host header includes tcp port
    else:
        req['REQUEST_SCHEME'] = 'http'
        req['SERVER_NAME'] = 'http://'+req['HTTP_HOST']
    
    
    
    def applyConfig(hed, val):
        if hed.startswith('RESPONSE_'): # add response header?
            response.add(f'{hed[9:]}: {val}')
        else:
            req[hed] = val
                
    # apply literal configuration rules to request vars
    for hed, val in defaultConfig.items():
        if hed.startswith('RESPONSE_'): # add a response header?
            response.add(f'{hed[9:]}: {val}')
        else:
            req[hed] = val
    for rule in configRules: # more sophisticated than update()
        matches = re.search(rule[1], req[rule[0]]) # ('group1', group2, ... )
        if matches: # if not empty result
            for hed, val in rule[2].items():
                val = strFormatMap(val, matches.groups())
                if hed.startswith('RESPONSE_'): # add a response header?
                    response.add(f'{hed[9:]}: {val}')
                else:
                    req[hed] = val
    
    # check document root availability before processing the request
    if not os.path.isdir(req['DOCUMENT_ROOT']):
        return sendResponse('501 Not Implemented')
    
    # check for response status rewrite
    if 'REQUEST_STATUS' in req:
        return sendResponse(req['REQUEST_STATUS'])
    
    # block url path attacks
    req['SCRIPT_FILENAME'] = os.path.realpath(req['DOCUMENT_ROOT']+parse.unquote_plus(req['SCRIPT_NAME']))
    if os.path.commonpath(( req['DOCUMENT_ROOT'], req['SCRIPT_FILENAME'])) != req['DOCUMENT_ROOT']:
        return sendResponse('403 Forbidden')
        
    # deal with directories
    if os.path.isdir(req['SCRIPT_FILENAME']):
        indexFound = False
        for indexFile in req['INDEX_FILES'].split():
            if os.path.isfile(req['SCRIPT_FILENAME']+os.sep+indexFile):
                req['SCRIPT_FILENAME'] += os.sep+indexFile
                indexFound = True
                break
        if not indexFound:
            if req['DIRECTORY_LIST'].lower() in ('true', '1', 'yes'):
                content = bytes(dirList(req['SCRIPT_FILENAME'], req['SCRIPT_NAME']), 'utf_8')
                response.add('Content-Type: text/html; charset=utf-8')
                return sendResponse('200 OK', content)
            else:
                return sendResponse('403 Forbidden')
    
    # peek requested file to save further processing
    if not os.path.isfile(req['SCRIPT_FILENAME']):
        return sendResponse('404 Not Found')
    
    # validate post if applies (just forms at the moment, sorry)
    if req['REQUEST_METHOD'] == 'POST':
        if req['HTTP_CONTENT_TYPE'] != 'application/x-www-form-urlencoded':
            return sendResponse('415 Unsupported Media Type')
        if 'POST_DATA' not in req:
            req['POST_DATA'] = requestBody
        
    # process cgi response if applies
    fileExt = os.path.splitext(req['SCRIPT_FILENAME'])[1]
    if fileExt in cgiParams:
        # prepare environment variables
        if 'SystemRoot' in os.environ: # necessary to access windows api's
            req['SystemRoot'] = os.environ['SystemRoot']
        post = bytes(req['POST_DATA'], 'utf_8')
        req['CONTENT_LENGTH'] = str(len(post))
        req['CONTENT_TYPE'] = req['HTTP_CONTENT_TYPE']
        
        # read cgi stdout (and split it), and stderr (and log it, if any)
        cgi = subprocess.run((cgiParams[fileExt]), capture_output=True, input=post, env=req)
        out = cgi.stdout.split(b'\r\n\r\n', 1)
        err = cgi.stderr.decode('utf_8').rstrip() # rstrip() to avoid trailing blank lines
        if err:
            log(err)
            
        # update new response headers
        status = '200 OK'
        for header in out[0].decode('utf_8').split('\r\n'):
            if header.startswith('Status: '):
                status = header[8:]
            else:
                response.add(header)
        sendResponse(status, out[1] if len(out) > 1 else b'')
        
    # use browser cache?
    lastModified = datetime.fromtimestamp(os.stat(req['SCRIPT_FILENAME']).st_mtime)
    if 'HTTP_IF_MODIFIED_SINCE' in req:
        try: # on date conversion error send resource anyway
            if lastModified > datetime.strptime(req['HTTP_IF_MODIFIED_SINCE'], '%a, %d %b %Y %X GMT'):
                return sendResponse('304 Not Modified')
        except ValueError:
            pass
        response.add('Last-Modified: '+lastModified.strftime('%a, %d %b %Y %X GMT'))
    else:
        response.add('Last-Modified: '+lastModified.strftime('%a, %d %b %Y %X GMT'))
    
    # send file
    response.add('Content-Type: '+mimeTypes.get(fileExt, 'application/octet-stream'))
    try:
        return sendResponse('200 OK', open(req['SCRIPT_FILENAME'], mode='rb', buffering=0).read())
    except PermissionError:
        return sendResponse('403 Forbidden')
    

### dirList

def dirList(path, url):
    dirs = []
    files = []
    # scan directory entries
    scan = os.scandir(path)
    for dirEntry in scan:
        stat = dirEntry.stat()
        if dirEntry.is_dir():
            dirs.append((dirEntry.name, datetime.fromtimestamp(stat.st_mtime).isoformat(' ', 'minutes')))
        else:
            files.append((dirEntry.name, str(stat.st_size), datetime.fromtimestamp(stat.st_mtime).isoformat(' ', 'minutes')))
    scan.close()
    # sort directory contents
    dirs.sort()
    files.sort()
    
    # craft html directory contents
    content = \
    (
        '<html>\r\n'
        '<head><title>Index of '+url+'</title></head>\r\n'
        '<body>\r\n'
        ' <h2>Index of '+url+'</h2>\r\n'
        ' <hr/>\r\n'
        ' <table border="0">\r\n'
    )
    if url == '/':
        url = ''
    else:
        content +='  <tr><td><a href="..">../</a>&emsp;&emsp;</td><td align="right">-&emsp;&emsp;</td><td>-</td></tr>\r\n'
    for name, date in dirs:
        content += '  <tr><td><a href="'+url+'/'+parse.quote(name)+'">'+name+'/</a>&emsp;&emsp;</td><td align="right">-&emsp;&emsp;</td><td>'+date+'</td></tr>\r\n' # fecha, tamaño
    for name, size, date in files:
        content += '  <tr><td><a href="'+url+'/'+parse.quote(name)+'">'+name+'</a>&emsp;&emsp;</td><td align="right">'+size+'&emsp;&emsp;</td><td>'+date+'</td></tr>\r\n' # fecha, tamaño
    content += \
    (
        ' </table>\r\n'
        ' <hr/>\r\n'
        '</body>\r\n'
        '</html>\r\n'
    )
    return content
    

###############################################################################


# debug
import sys
def log(msg):
    print(msg, file=sys.stderr)

runCmd   = sys.argv[1] if len(sys.argv) > 1 else ''
confFile = sys.argv[2] if len(sys.argv) > 2 else 'httpy.conf'

### printHelp
if runCmd == '-h':
    print("""\
httpy v2: Console based HTTP server for python 3
https://github.com/atesin/httpy
Requires Ncat to function online (https://nmap.org)
Default configuration file: httpy.conf

httpy just takes HTTP requests from standard input and writes responses to
standard output and logs to standard error, it requires external program "ncat"
to function online

httpy is licensed under WTFPL and published without any warranty, i wrote it
just to learn python in a fun way so it may contain errors, now you are adviced
you are the solely responsible for running it and its consequences


COMMON USAGE

ncat -lk 80 -c "httpy.py [file]" : Run with [specified] configuration file
httpy.py -t [file]               : test and print parsed configuration file
httpy.py -p                      : print a basic configuration sample
httpy.py -h                      : this help


HTTPY CONFIGURATION FILE VARIABLES

(c) : non standard custom httpy variables, can be set through rules
(E) : essential, no default value but need to be set for the server could work
(r) : read only, please don't modify them or could cause unexpected results,
      if some variable is unset it will return the default value "*"

DIRECTORY_LIST    : (c) list directory if no index file found (boolean string)
DOCUMENT_ROOT     : (E) local directory for online documents repository
HTTPS             :     "on" if request were sent through https (guessed)
HTTP_*            : (r) headers sent by client, uppercased, i.e.: HTTP_HOST
INDEX_FILES       : (c) space separated list of directory index files to search
POST_DATA         : (c) urlencoded data sent by forms, can be overwritten
QUERY_STRING      :     url query string if present (beetween "?" and "#")
REMOTE_ADDR       : (r) remote IP from where the request came from
REMOTE_PORT       : (r) remote TCP port where the request came from
REQUEST_METHOD    : (r) request method like GET, POST or HEAD
REQUEST_SCHEME    :     url scheme used (guessed) by browser, "http" or "https"
REQUEST_STATUS    :     rewrite new request status, ej.: "418 I'm a teapot"
REQUEST_URI       : (r) original url from request line
RESPONSE_*        : (c) response header to be included, i.e.: RESPONSE_Location
SCRIPT_FILENAME   :     absolute local filesystem path for the requested file
SCRIPT_NAME       : (r) path portion of the url (before "?" and "#")
SERVER_ADDR       : (r) local IP address that received the request
SERVER_NAME       :     root uri ready for redirects, like "http://my.self"
SERVER_PORT       : (r) local TCP port that receives the request
SERVER_PROTOCOL   : (r) protocol and version from request line
SERVER_SOFTWARE   : (r) self name and version used for responses: "HTTPy/x.y"
THE_REQUEST       : (r) the whole original request line, mostly used for logs
TIME              : (r) when request arrived, format "YYYY-MM-DD HH:MM:SS"
TIME_WDAY         : (r) numeric day of week when request arrived (0-6: sat-sun)


HTTPY RETURNED STATUS CODES

200 OK                     : (success) resource found and sent
304 Not Modified           : (success) file not modified since last request
400 Bad Request            : found malformed request line or request header
403 Forbidden              : read a directory without index file or directory
                             list enabled, attempt to access a file outside
                             document root, permission file error
404 Not Found              : the file doesn't exists in specified path
405 Method Not Allowed     : request method other than GET, POST or HEAD
415 Unsupported Media Type : POST with no 'application/x-www-form-urlencoded'
                             content type (sorry, only html forms supported)
500 Internal Server Error  : error generated by cgi interpreter, check its logs
501 Not Implemented        : document root misconfigured or not found\
""")
    exit()
    
### printConf
elif runCmd == '-p':
    print("""\
# Basic httpy configuration
# Type "httpy.py -h" for more details
logFormat = '{TIME} {REMOTE_ADDR} - {THE_REQUEST} - {HTTP_HOST} {REQUEST_STATUS}'
mimeTypes = \\
{
  '.html': 'text/html; charset=utf-8',
  '.htm': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.jpg': 'image/jpeg',
  '.png': 'image/png',
  '.gif': 'image/gif',
  '.ico': 'image/vnd.microsoft.icon'
}
defaultConfig = \\
{
  'DOCUMENT_ROOT': '/var/www', # unix like: "/var/www", windows: "C:\\\\www"
  #'INDEX_FILES': 'index.html'
}
configRules = \\
(
  #('SCRIPT_NAME', '\\.php$', {'REDIRECT_STATUS': '200'}) # required by php
)
cgiParams = \\
{
  #'.fileextension': 'path/to/cgi-bin'
}\
""")
    exit()

if runCmd and runCmd != '-t': # if it has something, but different from '-t'
    confFile = runCmd


### includeConf
    
try:
    includeFile = open(confFile, mode='r')
    exec(includeFile.read())
    includeFile.close()
    validConf = False
    if isinstance(logFormat, str): # isinstance(object, classinfo)
        if isinstance(mimeTypes, dict):
            if isinstance(defaultConfig, dict):
                if isinstance(configRules, tuple):
                    if isinstance(cgiParams, dict):
                        validConf = True
    if not validConf:
        log('Invalid configuration file format')
        log('Type "httpy.py -h" for more details')
        exit()
except FileNotFoundError:
    log('Configuration file not found')
    log('Type "httpy.py -h" for more details')
    exit()
except PermissionError:
    log("I don't have permission to read the file")
    log('Type "httpy.py -h" for more details')
    exit()
except SyntaxError as err:
    log('Configuration syntax error found on line '+str(err.lineno))
    log(err.text+' '*(err.offset-1)+'^ here')
    log('Type "httpy.py -h" for more details')
    exit()
except NameError:
    log('Some of the configuration variables are missing, exiting...')
    log('Type "httpy.py -h" for more details')
    exit()


### testConf
    
if runCmd == '-t':
    print('# Parsed httpy configuration')
    print('# Type "httpy.py -h" for more details')
    print('logFormat =', repr(logFormat))
    print('mimeTypes =', repr(mimeTypes).replace("', '", "',\r\n  '").replace("{'", "\\\r\n{\r\n  '").replace("'}", "'\r\n}"))
    print('defaultConfig =', repr(defaultConfig).replace("', '", "',\r\n  '").replace("{'", "\\\r\n{\r\n  '").replace("'}", "'\r\n}"))
    print('configRules =', repr(configRules).replace("), (", "),\r\n  (").replace("((", "\\\r\n(\r\n  (").replace("))", ")\r\n)"))
    print('cgiParams =', repr(cgiParams).replace("', '", "',\r\n  '").replace("{'", "\\\r\n{\r\n  '").replace("'}", "'\r\n}"))
    print('# configuration OK')
    exit()


### utilFunctions
    
if sys.version_info < (3, 0):
    log('Warning: running with python < v3 could lead unexpected results')

from datetime import datetime
import os
import re
import collections
from urllib import parse
import subprocess

#  wraps str.format[(**kwargs)|_map(maping)] according python version
def strFormatMap(format, map):
    if sys.version_info < (3, 2):
        return format.format(**map)
    return format.format_map(map)


### mainLoop

# was done this way because 'keep-alive'
# the program stops and exits when tries to read data and there's no more (EOF)
# or when it receives "Connection: close" or when request is HTTP/1.0 or below

while True:
    mainLoop()

