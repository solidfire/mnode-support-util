import logging
import os
from logging import handlers
from sys import stdout
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
#============================================================
# Setup logging to file and console
# DEBUG = /var/log/mnode-support-util.log
# INFO = console and /var/log/mnode-support-util.log
#============================================================

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

class MLog():
    def log_failed_return(status, text):
        logmsg = Logging.logmsg()
        logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(status))
        logmsg.debug("FAILED RETURN: {}: {}".format(status, text))

    def log_exception(exception):
        logmsg = Logging.logmsg()
        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
        logmsg.debug(exception)