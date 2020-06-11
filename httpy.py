# !/bin/python
# ncat -lk 80 -c httpy.py

### index (search for these labels):
### printConf
### printHelp
### loadConf
### testConf
### mainFunction
### subFunctions
### functionRun
### mainLoop

# configure connection close in line ### forceClose

# debug
import sys
def log(msg):
    print(msg, file=sys.stderr)


### printConf
    
if len(sys.argv) > 1 and sys.argv[1] == '-p':
    print("""\
# httpy basic configuration


# log format, see available variables at bottom

logFormat = '{_time} {_clientAddr} - {_reqLine} - {Host} {_statusCode}'


# media types according filename extensions for 'Content-Type' header
# defaults to 'application/octet-stream' for unknown files

mimeTypes = \\
{
    '.html': 'text/html; charset=utf-8',
    '.css' : 'text/css; charset=utf-8',
    '.txt' : 'text/plain; charset=utf-8',
    '.js'  : 'application/javascript; charset=utf-8',
    '.jpg' : 'image/jpeg',
    '.png' : 'image/png',
    '.gif' : 'image/gif',
    '.ico' : 'image/vnd.microsoft.icon'
}


'''
request configuration rules

configRules = [rule, rule, ... ]
rule        = ['variable', 'pattern', {config, config, ... }]
config      = 'variable':'value'

rule explanation:
1- if this variable/header name...
2- matches its value against this pattern (regex)...
3- then set back these other configuration variables/headers

can capture groups in pattern to use it in values with {}, some examples:
- virtual host: ['Host', '^(www\.)?blog\.mysite$', {'_docRoot': '/www/blog'}]
- url rewrite : ['_path', '/year/(201[0-9])$', {'_query': 'year={0}'}]
- redirection : ['_query', '(^|&)clip=235($|&)', {
                                     '_statusCode': '302',
                                     '_statusMsg' : 'Moved Temporarily',
                                     'Location'   : 'http://vimeo/upload-235'}]
more posibilities: caching, custom error pages, geoblocking, scheduling, etc.
'''

configRules = \\
[
    ['', '', {'_docRoot': 'C:\\\\www', '_indexFiles': 'index.html'}]
]


'''
request variables (along with request headers)

in order of appearance inside code, all values are strings
when they are unavailable yet then defaults to '_'

_time      : request time, iso format (YYYY-MM-DD HH:MM:SS)
_dayWeek   : day of the week positional number: 0-6 (sunday - saturday)
_clientAddr: remote IP address, as reported by ncat if available
_listenAddr: local IP address, as reported by ncat if available
_listenPort: local TCP port, as reported by ncat if available
_reqLine   : whole request line, e.g 'GET /logo.jpg HTTP/1.1'
_statusCode: resulting status code of current request ('200', '404', etc.)
_statusMsg : current status message, like 'OK' or 'Not Found'
_method    : request method, currently just 'GET' and 'HEAD' supported
_proto     : request protocol, like 'HTTP/1.0' or 'HTTP/1.1'
_path      : requested resource path, excluding query string
_query     : anything in the url after the question sign
_cacheDate : If-Modified-Since request header timedate, iso format
_fileDate  : real file modification timedate iso format
_indexFiles: search these files automatically in directories (space delim list)
_dirList   : whether to list files inside directories not (True or False)
'''\
""")
    exit()


### printHelp
    
if len(sys.argv) < 3 or ( sys.argv[1] != '-c' and sys.argv[1] != '-t' ):
    print('''\
httpy v4: Console based HTTP server for python 3
https://github.com/atesin/httpy
Requires Ncat also (https://nmap.org)
Common usage:

ncat -lk 80 -c "httpy.py -c <file>" : Run with specified configuration file
httpy.py -t <file>                  : Test and print parsed configuration file
httpy.py -p                         : Print a basic configuration file

httpy just take HTTP requests from standard input and writes the response to
standard output, so it requires ncat as external program to function online,
logs (access, error, etc.) goes to stderr

httpy is licensed under WTFPL, i wrote it just to learn python in a fun way
so it may contain errors, so you are the solely responsible for running it
and its consequences\
''')
    exit()


### loadConf

# 'include' configuration file
try:
    includeFile = open(sys.argv[2], mode='r')
    exec(includeFile.read())
    includeFile.close()
    type(logFormat)
    type(mimeTypes)
    type(configRules)
except FileNotFoundError:
    log('Configuration file not found')
    exit()
except PermissionError:
    log("I don't have permission to read the file")
    exit()
except SyntaxError as err:
    log('Configuration syntax error found on line '+str(err.lineno))
    log(err.text+' '*(err.offset-1)+'^ here')
    exit()
except NameError:
    log('Some of the configuration variables are missing')
    exit()
    

### testConf

if sys.argv[1] == '-t':
    print('# parsed httpy configuration')
    print('logFormat =', repr(logFormat))
    print('mimeTypes =', mimeTypes)
    print('configRules =', configRules)
    print('# configuration OK')
    exit()


### mainFunction (program flow continues in ### mainRun)
    
if sys.version_info < (3, 0):
    log('Warning: running with python < v3 could lead unexpected results')

from datetime import datetime
import os
import re
import collections
from urllib import parse

def mainLoop():

    ### subFunctions
    
    # this function should terminate the request,
    # call it with return() this way: return(printLog(statusCode))
    def printLog():
        if sys.version_info < (3, 2):
            log(logFormat.format(**req))
        else:
            log(logFormat.format_map(req))
        if req['Connection'] == 'close':
            exit()

    def sendHeaders():
        ### forceClose
        if req['Connection'] != 'keep-alive' and req['_proto'] == 'HTTP/1.0\r\n':
            response.add('Connection: close')
            req['Connection'] = 'close'
        sendString(
            'HTTP/1.1 '+str(req['_statusCode'])+' '+req['_statusMsg']+'\r\n'+
            'Server: python/3\r\n'+
            '\r\n'.join(response)+
            '\r\n\r\n'
        )
        
    
    def dirList(dirPath):
        if req['_method'] != 'HEAD':
            # scan directory contents
            dirs = []
            files = []
            dir = os.scandir(dirPath)
            for dirEntry in dir:
                stat = dirEntry.stat()
                if dirEntry.is_dir():
                    dirs.append((dirEntry.name, datetime.fromtimestamp(stat.st_mtime).isoformat(' ', 'minutes')))
                else:
                    files.append((dirEntry.name, str(stat.st_size), datetime.fromtimestamp(stat.st_mtime).isoformat(' ', 'minutes')))
            dir.close()
            dirs.sort()
            files.sort()
            
            # craft html directory contents
            filesList = (
                '<html>\r\n'
                '<head><title>Index of '+req['_path']+'</title></head>\r\n'
                '<body>\r\n'
                ' <h2>Index of '+req['_path']+'</h2>\r\n'
                ' <hr/>\r\n'
                ' <table border="0">\r\n'
            )
            
            if dirPath != req['_docRoot']:
                filesList +='  <tr><td><a href="..">../</a>&emsp;&emsp;</td><td align="right">-&emsp;&emsp;</td><td>-</td></tr>\r\n'
            for name, date in dirs:
                filesList += '  <tr><td><a href="'+req['_path']+'/'+name+'">'+name+'/</a>&emsp;&emsp;</td><td align="right">-&emsp;&emsp;</td><td>'+date+'</td></tr>\r\n' # fecha, tamaño
            for name, size, date in files:
                filesList += '  <tr><td><a href="'+req['_path']+'/'+name+'">'+name+'</a>&emsp;&emsp;</td><td align="right">'+size+'&emsp;&emsp;</td><td>'+date+'</td></tr>\r\n' # fecha, tamaño
                
            filesList += (
                ' </table>\r\n'
                ' <hr/>\r\n'
                '</body>\r\n'
                '</html>\r\n'
            )
            response.add('Content-Length: '+str(len(filesList)))
            response.add('Content-Type: text/html; charset=utf-8')
    
        req['_statusCode'], req['_statusMsg'] = '200', 'OK'
        sendHeaders()
        if req['_method'] != 'HEAD':
            sendString(filesList)
        printLog()


    # these functions are because python can't redirect binary files to stdout
    
    def sendString(msg):
        sendBytes(bytes(msg, encoding='utf_8'))

    def sendFile(path):
        sendBytes(open(path, mode='rb', buffering=0).read())

    def sendBytes(data):
        os.write(1, data)
        
        
    ### functionRun
    
    # iniciar la linea del registro de logs
    # despues se vera si se pasan estas variables a las variables de la request (dicionario req{})
    now = datetime.now()
    response = set() # response headers, string won't inherit to sub scopes
    
    def defaultValue():
        return '_'
    req = collections.defaultdict(defaultValue) # now can use req[index] safely
    
    req[''] = '_'
    req['_time'] = now.isoformat(' ', 'seconds')
    req['_dayWeek'] = now.strftime('%w')
    req['_clientAddr'] = os.environ.get('NCAT_REMOTE_ADDR', '_')
    req['_listenAddr'] = os.environ.get('NCAT_LOCAL_ADDR', '_')
    req['_listenPort'] = os.environ.get('NCAT_LOCAL_PORT', '_')
    
    
    # read blank lines until request line found
    while True:
        try:
            req['_reqLine'] = input()
        except EOFError:
            exit()
        if req['_reqLine']:
            break


    # validate request line
    reqFields = req['_reqLine'].split(' ', 2)
    if not (len(reqFields) > 2 and reqFields[1].startswith('/')):
        req['_statusCode'], req['_statusMsg'] = '400', 'Bad Request'
        sendHeaders()
        return(printLog())
    
    
    # parse request line
    req['_method'], req['_path'], req['_proto'] = reqFields
    try:
        req['_path'], req['_query'] = req['_path'].split('?', 1)
    except ValueError:
        req['_query'] = ''
    
    # validate method
    if req['_method'] not in ('GET', 'HEAD'):
        req['_statusCode'], req['_statusMsg'] = '405', 'Method Not Allowed'
        sendHeaders()
        return(printLog())
    
    # get headers until blank line found (or malformed header)
    while True:
        try:
            header = input().split(': ', 1)
        except EOFError:
            exit()
        if len(header) < 2:
            if header[0]:
                req['_statusCode'], req['_statusMsg'] = '400', 'Bad Request'
                sendHeaders()
                return(printLog())
            break
        req[header[0]] = header[1]
        
    # apply configuration rules
    for rule in configRules:
        matches = re.search(rule[1], req[rule[0]]) # ('group1', group2, ... )
        if matches: # not empty result
            #req.update(rule[2])
            for hed, val in rule[2].items():
                req[hed] = val.format_map(matches)
            
            
    # send custom status code before check for document root
    if '_statusCode' in req:
        sendHeaders()
        return(printLog())
    if not os.path.isdir(req['_docRoot']):
        req['_statusCode'], req['_statusMsg'] = '501', 'Not Implemented'
        sendHeaders()
        return(printLog())

    # block url path attacks
    filePath = parse.unquote_plus(req['_path'])
    filePath = os.path.realpath(req['_docRoot']+filePath)
    if os.path.commonpath([filePath, req['_docRoot']]) != req['_docRoot']:
        req['_statusCode'], req['_statusMsg'] = '403', 'Forbidden'
        sendHeaders()
        return(printLog())

    # tratar con directorios
    if os.path.isdir(filePath):
        indexFound = False
        for indexFile in req['_indexFiles'].split():
            if os.path.isfile(filePath+'/'+indexFile):
                filePath += '/'+indexFile
                indexFound = True
                break
        if not indexFound:
            if req['_dirList'].lower() in ('true', '1'):
                return(dirList(filePath))
            else:
                req['_statusCode'], req['_statusMsg'] = '403', 'Forbidden'
                sendHeaders()
                return(printLog())
            
    # retrieve file size if exists
    try:
        response.add('Content-Length: '+str(os.stat(filePath).st_size))
    except FileNotFoundError:
        req['_statusCode'], req['_statusMsg'] = '404', 'Not Found'
        sendHeaders()
        return(printLog())


    # get modified date to handle browser cache
    fileDate = datetime.fromtimestamp(os.stat(filePath).st_mtime)
    if 'If-Modified-Since' in req:
        try:
            cacheDate = datetime.strptime(req['If-Modified-Since'], '%a, %d %b %Y %X GMT')
            req['_cacheDate'] = cacheDate.isoformat(' ', 'seconds')
            if fileDate > cacheDate:
                req['_statusCode'], req['_statusMsg'] = '304', 'Not-Modified'
                sendHeaders()
                return(printLog())
        except ValueError:
            pass
        response.add('Last-Modified: '+fileDate.strftime('%a, %d %b %Y %X GMT'))
    else:
        response.add('Last-Modified: '+fileDate.strftime('%a, %d %b %Y %X GMT'))
    req['_fileDate'] = cacheDate.isoformat(' ', 'seconds')
        
    
    '''
    # get http post data
    if req['_method'] == 'POST':
        while True:
            try:
                req['_postData'] = input()
            except EOFError:
                exit()
            if req['_postData']
                break
    '''
    
    
    # todo bien, enviar archivo
    req['_statusCode'], req['_statusMsg'] = '200', 'OK'
    response.add('Content-Type: '+mimeTypes.get(os.path.splitext(filePath)[1], 'application/octet-stream'))
    sendHeaders()
    sendFile(filePath)
    return(printLog())


### mainLoop

# was done this way because 'keep-alive'
# the program stops and exits when tries to read data and there's no more (EOF)
while True:
    mainLoop()

