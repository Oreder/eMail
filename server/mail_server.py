import os 
import socket
import signal
import psutil
import multiprocessing
import logging
import select
from time import sleep
from server_config import SERVER_PORT, READ_TIMEOUT, LOG_FILES_DIR, PROCESSES_CNT, BYTES_TRANSFER_PER_TIME
from client_collection import ClientsCollection
from client import Client
from client_socket import ClientSocket
from state import *
from common.custom_logger_proc import QueueProcessLogger
from common.logger_threads import CustomLogHandler

class MailServer(object):
    def __init__(self, host='localhost', port=SERVER_PORT, nprocs=PROCESSES_CNT, logdir='logs'):
        self.host = host
        self.port = port
        self.clients = ClientsCollection()
        self.processes_cnt = nprocs
        self.processes = []
        self.logdir = logdir
        self.logger = QueueProcessLogger(filename=f"{logdir}/log.log")
        # logger = logging.getLogger()
        # logger.addHandler(CustomLogHandler(f"{logdir}/log.log"))
        # logger.setLevel(logging.DEBUG)
        # self.logger = logger

    def __enter__(self):
        self.socket_init()
        return self

    def socket_init(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(READ_TIMEOUT)
        server_address = (self.host, self.port)
        self.sock.bind(server_address)
        self.sock.listen(0)
        self.logger.log(level=logging.DEBUG, msg=f"Server socket initiated on port: {self.port}")

    def serve(self, blocking=True):
        '''
        :param blocking: processes finish when main process will be finished (exit context manager)
        so we should do nothing with blocking=True or other actions in main thread
        :return: None
        '''
        for i in range(self.processes_cnt):
            p = WorkingProcess(self)
            # p.daemon = True             # Setting daemon does not work with processes
            p.name = f"Working process {i}"
            self.processes.append(p)

            # Setup signal handler
            signal.signal(signal.SIGTERM, p.terminate)

            # Run our process
            p.start()

        self.logger.log(level=logging.DEBUG, msg=f"Started {self.processes_cnt} processes")
        
        while blocking:
            try:
                sleep(10)
            except KeyboardInterrupt as e:
                self.__exit__(type(e), e, e.__traceback__)
        
    def handle_client_read(self, cl:Client):
        '''
        check possible states and call handler for matching state
        '''
        try:
            line = cl.socket.readbytes()
        except socket.timeout:
            self.logger.log(level=logging.WARNING, msg=f"Timeout on client read")
            self.sock.close()

        current_state = cl.machine.state

        if current_state == HELO_STATE:
            cmd = line[:4].lower()
            if (cmd == "helo") or (cmd == "ehlo"):
                domain  = line[4:].strip() or "unknown"
                cl.mail.helo_command = cmd
                cl.mail.domain = domain
                cl.machine.HELO(cl.socket, cl.socket.address, domain)
        
        elif current_state == MAIL_FROM_STATE:
            if line[:10].lower() == "mail from:":
                mail_from_ = re.search(RE_EMAIL_ADDRESS, line[10:])
                if mail_from_ is not None:
                    cl.mail.from_ = mail_from_.group(0)
                    cl.machine.MAIL_FROM(cl.socket, cl.mail.from_)
        
        elif current_state == RCPT_TO_STATE:
            if line[:8].lower() == "rcpt to:":
                mail_to = re.search(RE_EMAIL_ADDRESS, line[8:])
                if mail_to is not None:
                    cl.mail.to.append(mail_to.group(0))
                    cl.machine.RCPT_TO(cl.socket, cl.mail.to)
        
        elif current_state == DATA_STATE:
            if cl.data_start_already_matched:
                if len(line) < BYTES_TRANSFER_PER_TIME:
                    DATA_end_matched = re.search(DATA_end_pattern, line)
                    if DATA_end_matched:
                        data = DATA_end_matched.group(1)
                        if data:
                            cl.mail.body += data
                        cl.machine.DATA_end(cl.socket)      # ending
                        cl.mail.to_file()
                        cl.data_start_already_matched = False
                        
                else:  
                    cl.mail.body += line                # processing
                    cl.machine.DATA_additional(cl.socket)
            else:
                # check exist other recepients firstly
                if line[:8].lower() == "rcpt to:":
                    mail_to = re.search(RE_EMAIL_ADDRESS, line[8:])
                    if mail_to is not None:
                        cl.mail.to.append(mail_to.group(0))
                        cl.machine.ANOTHER_RECEPIENT(cl.socket, mail_to)
                
                # data start secondly
                elif line[:4].lower() == "data":
                    data = line[4:]
                    if data:
                        cl.mail.body += data
                    cl.machine.DATA_start(cl.socket)    # starting
                    cl.data_start_already_matched = True
                else:
                    # self.logger.log(level=logging.DEBUG, msg=f"500 [Reader] Command not found at state {current_state}")
                    pass

        # Transitions possible from any states
        if line[:4].lower() == "rset":
            cl.machine.RSET(cl.socket)
        
        if line[:4].lower() == "quit":
            cl.machine.QUIT(cl.socket)


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
        else:
            # self.logger.log(level=logging.DEBUG, msg=f"500 [Writer] Command not found at state {current_state}")
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        for p in self.processes:
            p.join()
        print("Terminate all ..")
        self.sock.close()
        psutil.Process(os.getpid()).kill()


class WorkingProcess(multiprocessing.Process):
    def __init__(self, serv:MailServer, *args, **kwargs):
        super(WorkingProcess, self).__init__(*args, **kwargs)
        self.active = True
        self.server = serv
        self.gsock = None
        self.timeouts = 10.0

    def killAll(self, pid):
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()

    def terminate(self, signal, frame) -> None:
        if self.gsock is not None:
            self.gsock.send(b"Request server to terminate..")       # b - Keyword!
            self.gsock.close()   

            print(f"Stop process by signal {signal}")
            self.killAll(pid=os.getpid())

    def run(self):
        try:
            while self.active:
                client_sockets = self.server.clients.sockets()
                readers, writers, errors = select.select([self.server.sock] + client_sockets, client_sockets, [], self.timeouts)        # timeout worked!
                for reader in readers:
                    if reader is self.server.sock:
                        connection, client_address = reader.accept()
                        client = Client(socket=ClientSocket(connection, client_address), logdir=self.server.logdir)
                        self.server.clients[connection] = client
                    else:
                        self.gsock = self.server.clients[reader].socket
                        self.server.handle_client_read(self.server.clients[reader])

                for writer in writers:
                    ret = self.server.handle_client_write(self.server.clients[writer])
                    if ret is True:
                        self.terminate(signal.SIGTERM, 0)
                    
        except (KeyboardInterrupt, ValueError, socket.timeout, OSError) as e:
            self.terminate(signal.SIGTERM, e)
            