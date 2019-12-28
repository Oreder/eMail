import ssl
import socket
import os
import base64


context = ssl._create_stdlib_context()
new_socket = socket.create_connection(("smtp.yandex.ru", 465), 5,
                                     None)
new_socket =context.wrap_socket(new_socket,
                                      server_hostname="smtp.yandex.ru")
print( list( os.walk('./../maildir/') ) )
f = open('./../maildir/1', 'r')
fileLine = f.readline()
print(fileLine)
print(new_socket.recv())#220
new_socket.sendall( fileLine.encode('ascii'))
print(new_socket.recv())#250
print('AUTH LOGIN')
new_socket.send(('AUTH PLAIN ' + base64.b64encode(b"\0letmetest548@yandex.ru\0goodday").decode("ascii") + '\r\n').encode('ascii'))
print(new_socket.recv())
fileLine = f.readline()
new_socket.sendall(('mail ' + fileLine).encode('ascii'))#from
print(new_socket.recv())
fileLine = f.readline()
new_socket.sendall(('rcpt ' + fileLine).encode('ascii'))#to
print(new_socket.recv())
print('')
new_socket.sendall( b'data\r\n')
print(new_socket.recv())

md = ''
for line in f:
        md = md + line

new_socket.sendall(md.encode('ascii'))
print(new_socket.recv())
f.close()
new_socket.sendall(b'quit\r\n')
print(new_socket.recv())
print('\n')
