import re

HELO_STATE              = 'helo'        # 'ehlo'
HELO_WRITE_STATE        = 'helo_write'

GREETING_STATE          = 'greeting'
GREETING_WRITE_STATE    = 'greeting_write'

MAIL_FROM_STATE         = 'mail_from'
MAIL_FROM_WRITE_STATE   = 'mail_from_write'

RCPT_TO_STATE           = 'rcpt_to'
RCPT_TO_WRITE_STATE     = 'rcpt_to_write'

DATA_STATE              = 'data'            # For reading start date message and all next, except last
                                            # Note we should't reply to on all additional data messages
DATA_WRITE_STATE        = 'data_write'
DATA_END_WRITE_STATE    = 'data_end_write'

QUIT_STATE              = 'quit'
QUIT_WRITE_STATE        = 'quit_write'
FINISH_STATE            = 'finish'

RE_CRLF                 = r"\r(\n)?"
RE_EMAIL_ADDRESS        = r'[\w\.-]+@[\w\.-]+'
DATA_end_pattern        = re.compile(f"([\s\S]*)\.{RE_CRLF}", re.IGNORECASE)

states = [
    GREETING_WRITE_STATE,

    HELO_STATE,
    HELO_WRITE_STATE,

    MAIL_FROM_STATE,
    MAIL_FROM_WRITE_STATE,

    RCPT_TO_STATE,
    RCPT_TO_WRITE_STATE,

    DATA_STATE,
    DATA_WRITE_STATE,
    DATA_END_WRITE_STATE,

    QUIT_STATE,
    QUIT_WRITE_STATE,
    FINISH_STATE
]