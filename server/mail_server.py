import socket
import multiprocessing
import logging
import select
from server_config import SERVER_PORT, READ_TIMEOUT, LOG_FILES_DIR, PROCESSES_CNT
from client_collection import ClientsCollection
from client import Client
from client_socket import ClientSocket
from state import *
from common.custom_logger_proc import QueueProcessLogger
from common.logger_threads import CustomLogHandler
# import sys
import os 
from time import sleep
import signal

class MailServer(object):
    def __init__(self, host='localhost', port=SERVER_PORT, processes=PROCESSES_CNT, logdir='logs'):
        self.host = host
        self.port = port
        self.clients = ClientsCollection()
        self.processes_cnt = processes
        self.processes = []
        self.logdir = logdir
        
        self.logger = QueueProcessLogger(filename=f'{logdir}/log.log')
        # logger = logging.getLogger()
        # logger.addHandler(CustomLogHandler(f'{logdir}/log_t.log'))
        # logger.setLevel(logging.DEBUG)
        # self.logger = logger

    def __enter__(self):
        self.socket_init()
        # self.socket_graceful_shutdown()
        return self

    def socket_init(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(READ_TIMEOUT)
        server_address = (self.host, self.port)
        self.sock.bind(server_address)
        self.sock.listen(0)
        self.logger.log(level=logging.DEBUG, msg=f'Server socket initiated on port: {self.port}')

    def socket_graceful_shutdown(self):
        # server_address = (self.host, self.port)
        # self.gsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.gsock.connect(server_address)
        pass

    def serve(self, blocking=True):
        '''
        :param blocking: processes finish when main process will be finished (exit context manager)
        so we should do nothing with blocking=True or other actions in main thread
        :return: None
        '''
        for i in range(self.processes_cnt):
            p = WorkingProcess(self)
            # p.daemon = True #not work with processes, kill it join it in __exit__()
            self.processes.append(p)
            p.name = 'Working Process {}'.format(i)
            
            # Setup signal handler
            # signal.signal(signal.SIGINT, p.terminate)
            signal.signal(signal.SIGTERM, p.terminate)
            # signal.signal(signal.SIGKILL, p.terminate)
            p.start()

        self.logger.log(level=logging.DEBUG, msg=f'Started {self.processes_cnt} processes')
        #TODO not while True, make it wait signal, without do nothing, it utilize CPU on 100%

        while blocking:
            try:
                sleep(0.1)
            except KeyboardInterrupt as e:
                self.__exit__(type(e), e, e.__traceback__)
        
    def handle_client_read(self, cl:Client):
        '''
         check possible states from cl.machine.state
         match exact state with re patterns
         call handler for this state
        '''
        try:
            line = cl.socket.readbytes()
        except socket.timeout:
            self.logger.log(level=logging.WARNING, msg=f'Timeout on client read')
            self.sock.close()
            return False

        current_state = cl.machine.state

        if current_state == HELO_STATE:
            HELO_matched = re.search(HELO_pattern, line)
            if HELO_matched:
                command = HELO_matched.group(1)
                domain  = HELO_matched.group(2) or "unknown"
                cl.mail.helo_command = command
                cl.mail.domain = domain
                cl.machine.HELO(cl.socket, cl.socket.address, domain)
                # return True
        
        elif current_state == MAIL_FROM_STATE:
            MAIL_FROM_matched = re.search(MAIL_FROM_pattern, line)
            if MAIL_FROM_matched:
                cl.mail.from_ = MAIL_FROM_matched.group(1)
                cl.machine.MAIL_FROM(cl.socket, cl.mail.from_)
                # return True
        
        elif current_state == RCPT_TO_STATE:
            RCPT_TO_matched = re.search(RCPT_TO_pattern, line)
            if RCPT_TO_matched:
                mail_to = RCPT_TO_matched.group(1)
                cl.mail.to.append(mail_to)
                cl.machine.RCPT_TO(cl.socket, mail_to)
                # return True
        
        elif current_state == DATA_STATE:
            if cl.data_start_already_matched:
                DATA_end_matched = re.search(DATA_end_pattern, line)
                if DATA_end_matched:
                    data = DATA_end_matched.group(1)
                    if data:
                        cl.mail.body += data
                    cl.machine.DATA_end(cl.socket)      # ending
                    cl.mail.to_file()
                    cl.data_start_already_matched=False
                else:  
                    cl.mail.body += line                # processing
                    cl.machine.DATA_additional(cl.socket)
            else:
                # check exist other recepients firstly
                RCPT_TO_matched = re.search(RCPT_TO_pattern, line)
                if RCPT_TO_matched:
                    mail_to = RCPT_TO_matched.group(1)
                    cl.mail.to.append(mail_to)
                    cl.machine.ANOTHER_RECEPIENT(cl.socket, mail_to)
                    # return True
                
                # data start secondly
                DATA_start_matched = re.search(DATA_start_pattern, line)
                if DATA_start_matched:
                    data = DATA_start_matched.group(1)
                    if data:
                        cl.mail.body += data
                    cl.machine.DATA_start(cl.socket)    # starting
                    cl.data_start_already_matched = True
                else:
                    pass    #TODO: incorrect commands to message to client
            # return True
        
        QUIT_matched = re.search(QUIT_pattern, line)
        if QUIT_matched:
            cl.machine.QUIT(cl.socket)
            # cl.flag = True
            # return False
            return True

        # Transition possible from any states
        RSET_matched = re.search(RSET_pattern, line)
        if RSET_matched:
            cl.machine.RSET(cl.socket)
        else:
            pass
        # return True

        
        # cl.socket.send(f'500 Unrecognised command {line}\n'.encode())
        # print('500 Unrecognised command')

    def handle_client_write(self, cl:Client):
        current_state = cl.machine.state
        if current_state == GREETING_WRITE_STATE:
            cl.machine.GREETING_write(cl.socket)
        elif current_state == HELO_WRITE_STATE:
            cl.machine.HELO_write(cl.socket, cl.socket.address, cl.mail.domain)
        elif current_state == MAIL_FROM_WRITE_STATE:
            cl.machine.MAIL_FROM_write(cl.socket, cl.mail.from_)
        elif current_state == RCPT_TO_WRITE_STATE:
            cl.machine.RCPT_TO_write(cl.socket, cl.mail.to)
        elif current_state == DATA_WRITE_STATE:
            cl.machine.DATA_start_write(cl.socket)
        elif current_state == DATA_END_WRITE_STATE:
            cl.machine.DATA_end_write(cl.socket, cl.mail.file_path)
        elif current_state == QUIT_WRITE_STATE:
            cl.machine.QUIT_write(cl.socket)
            self.clients.pop(cl.socket.connection)
            return True
        # else:
        #     pass
        
        # return True 
            # print(current_state)
            # cl.socket.send(f'500 Unrecognised command TODO\n'.encode())
            # print('500 Unrecognised command')

    def __exit__(self, exc_type, exc_val, exc_tb):
        
        for p in self.processes:
            p.join()
        print("Terminate all ..")
        self.sock.close()
        # signal.siginterrupt(signal.SIGINT, True)
        psutil.Process(os.getpid()).kill()

        # for p in self.processes:          -- for process
        #     p.join(timeout=2)
        # self.logger.terminate()           -- for thread
        # self.logger.join(timeout=2)

# import asyncio
# import signal

import psutil

class WorkingProcess(multiprocessing.Process):
    def __init__(self, serv:MailServer, *args, **kwargs):
        super(WorkingProcess, self).__init__(*args, **kwargs)
        self.active = True
        self.server = serv
        # self.current_client = clientSocket
        self.gsock = None
        # connection, client_address = self.server.sock.accept()
        # self.client = Client(ClientSocket(connection, client_address))

        self.timeouts = 100.0

    def killAll(self, pid):
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        # parent.kill()

    def terminate(self, signal, frame) -> None:
        
        # if self.gsock is not None:
        #     self.gsock.send(b'Request server to terminate..')
        #     # self.gsock.close()
        # if signal == signal.SIGTERM:
        #     print(f"Stop process by signal {signal}")
        #     self.gsock.close()
        if self.gsock is not None:
            self.gsock.send(b'Request server to terminate..')
            self.gsock.close()   

            # if signal == signal.SIGTERM:
            print(f"Stop process by signal {signal}")
            self.killAll(pid=os.getpid())

        # self.active = False
        # getout of select from server

    def run(self):
        try:
            i = 0
            while self.active:  #for make terminate() work
                # print(f'Iteration {i}')
                i += 1

                client_sockets = self.server.clients.sockets()
                readers, writers, errors = select.select([self.server.sock] + client_sockets, client_sockets, [], 10.0)        # timeout worked!
                for reader in readers:
                    if reader is self.server.sock:
                        connection, client_address = reader.accept()
                        client = Client(socket=ClientSocket(connection, client_address), logdir=self.server.logdir)
                        self.server.clients[connection] = client

                        print("Server")
                        print(reader)
                    else:
                        print("Client")
                        self.gsock = self.server.clients[reader].socket
                        # self.active &= self.server.handle_client_read(self.server.clients[reader])
                        ret = self.server.handle_client_read(self.server.clients[reader])
                    
                        print(reader) 

                for writer in writers:
                    # self.active &= self.server.handle_client_write(self.server.clients[writer])
                    ret = self.server.handle_client_write(self.server.clients[writer])
                    if ret is True:
                        self.terminate(signal.SIGTERM, 0)
                    
        except (KeyboardInterrupt, ValueError, socket.timeout, OSError) as e:
            self.terminate(signal.SIGTERM, e)
            