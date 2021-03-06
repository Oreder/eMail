import socket
import logging
from state import *
from common.custom_logger_proc import QueueProcessLogger
from transitions import Machine
from transitions.extensions import GraphMachine as gMachine

class SMTP_FSM(object):
    def __init__(self, name, logdir):
        self.name = name
        self.logger = QueueProcessLogger(filename=f'{logdir}/fsm.log')
        self.machine = self.init_machine()

        self.init_transition('HELO'           , HELO_STATE     , HELO_WRITE_STATE     )
        self.init_transition('MAIL_FROM'      , MAIL_FROM_STATE, MAIL_FROM_WRITE_STATE)
        self.init_transition('RCPT_TO'        , RCPT_TO_STATE  , RCPT_TO_WRITE_STATE  )
        self.init_transition('DATA_start'     , DATA_STATE     , DATA_WRITE_STATE     )
        self.init_transition('DATA_additional', DATA_STATE     , DATA_STATE           )
        self.init_transition('DATA_end'       , DATA_STATE     , DATA_END_WRITE_STATE )
        self.init_transition('QUIT'           , '*'     , QUIT_WRITE_STATE     )

        self.init_transition('GREETING_write' , GREETING_WRITE_STATE , HELO_STATE     )
        self.init_transition('HELO_write'     , HELO_WRITE_STATE     , MAIL_FROM_STATE)
        self.init_transition('MAIL_FROM_write', MAIL_FROM_WRITE_STATE, RCPT_TO_STATE  )
        self.init_transition('RCPT_TO_write'  , RCPT_TO_WRITE_STATE  , DATA_STATE     )
        self.init_transition('ANOTHER_RECEPIENT', DATA_STATE  , RCPT_TO_WRITE_STATE)
        self.init_transition('DATA_start_write',DATA_WRITE_STATE     , DATA_STATE     )
        self.init_transition('DATA_end_write' , DATA_END_WRITE_STATE , QUIT_STATE     )
        self.init_transition('QUIT_write'     , QUIT_WRITE_STATE     , FINISH_STATE   )

        self.init_transition('RSET'      , source='*', destination=HELO_WRITE_STATE)
        self.init_transition('RSET_write', source='*', destination=HELO_STATE      )

    def init_machine(self):
        return gMachine(
            model=self,
            states=states,
            initial=GREETING_WRITE_STATE
        )

    def init_transition(self, trigger, source, destination):
        self.machine.add_transition(
            before=trigger + '_handler',
            trigger=trigger,
            source=source,
            dest=destination
        )

    def GREETING_handler(self, socket):
        self.logger.log(level=logging.DEBUG, msg="220 SMTP GREETING OK")

    def GREETING_write_handler(self, socket:socket.socket):
        socket.send("220 SMTP GREETING OK\n".encode())

    def HELO_handler(self, socket, address, domain):
        self.logger.log(level=logging.DEBUG, msg="domain: {} connected".format(domain))

    def HELO_write_handler(self, socket:socket.socket, address, domain):
        socket.send("250 {} OK \n".format(domain).encode())

    def MAIL_FROM_handler(self, socket, address):
        self.logger.log(level=logging.DEBUG, msg=f"From: {address}")

    def MAIL_FROM_write_handler(self, socket:socket.socket, address):
        socket.send("250 Checking header OK\n".encode())

    def RCPT_TO_handler(self, socket, address):
        self.logger.log(level=logging.DEBUG, msg=f"To: {address}")

    def ANOTHER_RECEPIENT_handler(self, socket, address):
        self.logger.log(level=logging.DEBUG, msg=f"CC: {address}")
        
    def RCPT_TO_write_handler(self, socket:socket.socket, address):
        socket.send("250 Accept writing OK\n".encode())

    def DATA_start_handler(self, socket):
        self.logger.log(level=logging.DEBUG, msg="Accept sending OK")
    
    def DATA_start_write_handler(self, socket:socket.socket):
        socket.send("354 Sending process starts\n".encode())

    def DATA_additional_handler(self, socket):
        self.logger.log(level=logging.DEBUG, msg="Additional data")

    def DATA_end_handler(self, socket):
        self.logger.log(level=logging.DEBUG, msg="Sending process ends")
    
    def DATA_end_write_handler(self, socket:socket.socket, filename):
        socket.send(f"250 Sending attachment(s) {filename}\n".encode())

    def QUIT_handler(self, socket:socket.socket):
        self.logger.log(level=logging.DEBUG, msg="Disconnect..\n")

    def QUIT_write_handler(self, socket:socket.socket):
        socket.send("221 QUIT OK\n".encode())

    def RSET_handler(self, socket):
        self.logger.log(level=logging.DEBUG, msg=f"Reseting connection..\n")

    def RSET_write_handler(self, socket:socket.socket):
        socket.send(f"250 Accept writing OK\n".encode())