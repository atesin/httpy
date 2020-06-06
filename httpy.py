# !/bin/python
# ncat -lk 80 -c httpy.py


'''
pendiente
- procesar las cabeceras de entrada, actualmente se guardan todas en un diccionario
- directory listing
- urldecode
- mas mime types
- multipart uploads
- cookies
- not modified responses
- cgi
'''


# configuracion
docRoot = 'C:\\PROGRAMS\\www'
indexFile = 'index.html'
dirList = False # no soportado por ahora
mimes = {
    '.html': 'text/html',
    '.css' : 'text/css',
    '.txt' : 'text/plain',
    '.js'  : 'application/javascript',
    '.jpg' : 'image/jpeg',
    '.png' : 'image/png',
    '.gif' : 'image/gif',
    '.ico' : 'image/vnd.microsoft.icon'}



import datetime
import os
import sys


# definicion de funciones, el programa continua en la linea -=-=-=-


def main():

    # sub funciones primero, esta funcion continua en la linea _._._._._
    
    # debug
    def d(*m):
        print(m, file=sys.stderr)

    def printLog(statusCode):
        print(logLine, statusCode, '-', reqLine, file=sys.stderr)
        exit()

    # .-.-.-.-. estas funciones son porque python no soprta imprimir archivos binarios a stdout
    
    def sendHeaders(status):
        sendString('HTTP/1.1 '+status+'\r\n')
        sendString('Server: Python/3\r\n')
        for header in headers:
            sendString(header+'\r\n')
        sendString('\r\n')

    def sendString(str):
        sendBytes(bytes(str, encoding='utf-8'))

    def sendFile(path):
        sendBytes(open(path, mode='rb', buffering=0).read())

    def sendBytes(data):
        os.write(1, data)
        
    # .-.-.-.-. hasta aqui

    # _._._._._ aqui continua la funcion principal

    # iniciar la linea del registro de logs, el tiempo es solo para los logs
    # despues se vera si se pasan estas variables a las variables de la request (dicionario req{})
    logLine = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S ')+os.environ['NCAT_REMOTE_ADDR']

    # leer linea de request: \n\n\n... METHOD /url PROTO/VER
    while True:
        try:
            reqLine = input()
        except EOFError:
            exit()
        if reqLine:
            break

    # parsear linea de request
    # despues se vera si se pasan estas variables al dicionario req{}
    # TODO: urldecode para la url
    reqElm = reqLine.split(' ', 2)
    if not (len(reqElm) > 2 and reqElm[1].startswith('/')):
        sendHeaders('400 Bad Request')
        printLog(400)
    
    # leer headers hasta una linea en blanco
    req = {}
    while True:
        try:
            header = input().split(': ', 1)
        except EOFError:
            exit()
        if len(header) < 2:
            if header[0]:
                sendHeaders('400 Bad Request')
                printLog(400)
            break
        req[header[0]] = header[1]
    
    # TODO: mas metodos, solo GET por ahora
    if reqElm[0] != 'GET':
        sendHeaders('405 Method Not Allowed')
        printLog(405)


    # validar url solicitada antes de acceder al filesystem
    # TODO: ver que pasa con los asteriscos
    # TODO: implementar urldecode
    path = os.path.realpath(docRoot+reqElm[1])
    if os.path.commonpath([path, docRoot]) != docRoot:
        sendHeaders('403 Forbidden')
        printLog(403)


    # tratar con directorios
    if reqElm[1].endswith('/'):
        if not os.path.isfile(path+'/'+indexFile):
            if not dirList or True: # TODO: 'or True' es para overridear dirList
                sendHeaders('403 Forbidden')
                printLog(403)
            # TODO: agregar el dir listing aqui
        path += '/'+indexFile

    # validar tipo soportado
    # TODO: no soporta mime multipart para descargar archivos todavia
    headers = set()
    try:
        headers.add('Content-Type: '+mimes[os.path.splitext(path)[1]])
    except KeyError:
        sendHeaders('415 Unsupported Media Type')
        printLog(415)


    # consultar archivo solicitado
    if not os.path.isfile(path):
        sendHeaders('404 Not Found')
        printLog(404)

    # todo bien, enviar archivo
    headers.add('Content-Length: '+str(os.stat(path).st_size))
    sendHeaders('200 OK')
    sendFile(path)
    printLog(200)

        
# -=-=-=- continua el programa


# se hizo asi para habilitar la persistencia despues
# el programa termina y sale cuando trata de leer datos y no hay mas (EOF)
# TODO: keep-alive (or not) support
while True:
    main()


