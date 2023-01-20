import logging
import os
from logging import handlers
from sys import stdout




class Logging():
    def logmsg():
        myuid = os.getuid()
        if myuid != 0:
            print("Please re-run this utility with sudo. Current uid: {}".format(str(myuid)))
            exit(1)
        logfile = '/var/log/mnode-support-util.log'
        formatter = logging.Formatter('%(asctime)s [%(filename)s: %(lineno)d] [%(process)d] [%(levelname)s]: %(message)s','%m:%d:%Y %H:%M:%S')
        logging.getLogger().handlers.clear()
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        rotate_handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=5000000, backupCount=2, encoding=None, delay=0)
        rotate_handler.setFormatter(formatter)
        logger.addHandler(console)
        logger.addHandler(rotate_handler)
        return logger