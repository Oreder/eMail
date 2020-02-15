import os
import re
import uuid
from dataclasses import dataclass
from server_config import DEFAULT_USER_DIR, SERVER_DOMAIN, DEFAULT_SUPR_DIR, MAX_RECIPIENTS

@dataclass
class Mail():
    to:list
    body:str = ''
    from_:str = ''
    domain:str = ''
    helo_command:str = ''
    file_path: str = ''

    @property
    def mail(self):
        mail  = f"{self.helo_command.upper()}: {self.domain}\r\n"
        mail += f"FROM: {self.from_}\r\n"
        
        self.to = list(set(self.to))
        mail += f"TO: {self.to[0]}\r\n"
        if len(self.to) > 1:
            mail += f"CC: {'; '.join(self.to[1:])}\r\n"
        
        mail += self.body
        return mail

    def to_file(self, file_path=None):
        if file_path is None:
            self.file_path = f'{uuid.uuid4()}=@'
            file_path = self.file_path

        targets = self.to
        
        # Check max recipients
        if len(targets) > MAX_RECIPIENTS:
            return (452, 'Too many emails sent or too many recipients')
        else:
            # Select the first one, which is non-local to save to maildir
            nonLocalFound = False
            for target in targets:
                tmp = target.lower().split('@')
                user, domain = tmp[0], tmp[1]

                # TODO: new, cur, tmp
                directory = DEFAULT_USER_DIR
                if domain == SERVER_DOMAIN:
                    directory = DEFAULT_SUPR_DIR + user + '/maildir/'
                    
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    with open(directory + file_path, 'w') as fs:
                        fs.write(self.mail)
                else:
                    if not nonLocalFound:
                        with open(directory + file_path, 'w') as fs:
                            fs.write(self.mail)
                        nonLocalFound = True
            return (250, 'Requested mail action okay completed')

    @classmethod
    def from_file(cls, filepath):
        # for client part
        pass
