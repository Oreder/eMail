# eMail
Environment requirements:
+ OS: Ubuntu 18.04 x64
+ Python: 3.7.5
+ Evolution ([install](https://rc.partners.org/kb/article/2702) | [eMail setup](https://askubuntu.com/questions/51467/how-do-i-setup-an-email-account-in-evolution))
+ Visual Studio [Code](https://code.visualstudio.com/docs/setup/linux) | [PyCharm](https://itsfoss.com/install-pycharm-ubuntu/) Community Edition for debugging

### How to run
```sh
    python3 main.py
```

## Maildir guide
Currently, maildir is a directory that stores email messages as files. Maildir works with Courier, a mail server that provides folders and quotas for the email accounts on your hosting account.

The folders inside the mail directory are subdirectories such as *.Drafts*, *.Trash* and *.Sent*. Each of these folders contain three additional subdirectories called *tmp*, *new* and *cur*.

+ **tmp** - This subdirectory stores email messages that are in the process of being delivered. It may also store other kinds of temporary files.
+ **new** - This subdirectory stores messages that have been delivered but have not yet been seen by any mail application, such as webmail or Outlook.
+ **cur** - This subdirectory stores messages that have already been viewed by mail applications, like webmail or Outlook.

## About [Content-Transfer-Encoding](https://github.com/VitalyVen/smtp-course-work/issues/6)
CODE TRANSFER NOTE: The quoted-printable and base64 converters are designed so that the data after its use is easily interconvertible. The only nuance that arises in such a relay is a sign of the end of the line. When converting from quoted-printable to base64, the newline should be replaced with the CRLF sequence. Accordingly, and vice versa, but ONLY when converting text data.

## Tests 
```sh
    export PYTHONPATH=`pwd`
    cd server && pytest-3
```

# References
1. J. Klensin, Network Working Group (October 2008) ([DRAFT STANDARD](https://tools.ietf.org/html/rfc5321))
2. SMTP protocol [Explained](https://www.afternerd.com/blog/smtp/) (How Email works?)
3. About powerful [select](https://pymotw.com/2/select/)
4. [Interface to pselect and sigprocmask system calls](https://cysignals.readthedocs.io/en/latest/pselect.html)

## TODOs
+ Multiple recipients (100%)
+ Graceful shutdown (!)
+ Big mails (90%)
+ Tests (100%)
+ Fast sending and receiving mails (0%) 

## Notices
1. Our server is not using like fork() works. Here, each running process uses your own select. Therefore, in order to terminate a single job by connection, we have to close all sockets in each process. It is the main idea of graceful shutdown. 
2. Other solution of problem getting out of select is destroying all processes by a powerful library **psutil**. Getting a parent process and then all we need is destroying its child processes.
3. Solution of graceful shutdown (get out of select/poll by sigint):
    - First step: create one socket (as checker), this socket is allways added into select
    - Second step: Check if this socket is preparing to read?
    - Third step: If it does not prepare, that means we need to close owner process, and write to sigint worker remaining datas.
    - Remember: otherwise, we can use pipe instead of a socket.
4. Last TODO causes mostly by using regular expressions!