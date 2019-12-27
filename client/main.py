import ssl
import socket
import smtplib
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
new_socket.sendall( fileLine.encode('ascii'))
print(new_socket.recv())
new_socket.sendall( ('AUTH PLAIN ' + base64.b64encode(bytes('\0letmetest548@yandex.ru\0goodday', 'utf-8')).decode('ascii')).encode('ascii'))#?
print(new_socket.recv())
fileLine = f.readline()
new_socket.sendall(('mail ' + fileLine).encode('ascii'))
print(new_socket.recv())
fileLine = f.readline()
new_socket.sendall(b'rcpt TO:<zombie9@mail.ru>\r\n')
print(new_socket.recv())
new_socket.sendall( b'data\r\n')
print(new_socket.recv())
#with open("/home/ultra/scw/smtp-course-work/maildir/1", mode='rb') as file: # b is important -> binary
 #   fileContent = file.read()rabbitmes@yandex.ru
new_socket.sendall(b'Completely drftgyhudrftyuvy y ygy text\r\n.\r\n')
print(new_socket.recv())
f.close()
new_socket.sendall(b'quit\r\n')
print(new_socket.recv())

#
# b'220 iva1-db9fc35c0844.qloud-c.yandex.net ESMTP (Want to use Yandex.Mail for your domain? Visit http://pdd.yandex.ru)\r\n'
# b'250-iva1-db9fc35c0844.qloud-c.yandex.net\r\n250-8BITMIME\r\n250-PIPELINING\r\n250-SIZE 42991616\r\n250-AUTH LOGIN PLAIN XOAUTH2\r\n250-DSN\r\n250 ENHANCEDSTATUSCODES\r\n'
# b'235 2.7.0 Authentication successful.\r\n'
# b'250 2.1.0 <MusicDevelop@yandex.ru> ok\r\n'
# b'250 2.1.5 <MusicDevelop@yandex.ru> recipient ok\r\n'
# b'354 Enter mail, end with "." on a line by itself\r\n'
# b'250 2.0.0 Ok: queued on iva1-db9fc35c0844.qloud-c.yandex.net as 1576799901-ptmcIpTstA-wLWGReg9\r\n'
#
# Process finished with exit code 0
