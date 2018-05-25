#!/usr/bin/env python
"""Script Funcs v3
A random collection of support funcs for simplifying writing basic tool scripts.

Functions:
    setuplogging - Set up default logger 
    loadconfig, JAM, getcfg - Config file handlers
    requestlock, releaselock - Cross tool/process safety handshake
    snd_notif, snd_email - Send text message and email messages

    Import this module from the main script as follows:
        from funcs3 import *

Globals:
    cfg - Dictionary that contains the info read from the config file
    progdir - A string var that contains the full path to the main
        program directory.  Useful for file IO when running the script
        from a different pwd, such as when running from cron.
"""

# Revision history:
#    180524  New


import time
import os.path
import smtplib
from email.mime.text import MIMEText
import logging
import __main__


### Project globals
cfg = {}
progdir = os.path.dirname(os.path.realpath(__main__.__file__))


def setuplogging (logfile= 'log.txt'):
    """Set up logging.

    Param:
    logfile -- 
        The default log file is <main file path>/log.txt.
        Absolute or relative path (from the main program directory) may
        be specified.
    """

    if os.path.isabs(logfile):  logpath = logfile
    else:                       logpath = progdir + '/' + logfile

    logging.basicConfig(filename=logpath,
        format='%(asctime)s/%(module)s/%(funcName)s/%(levelname)s:  %(message)s')


def loadconfig(cfgfile= 'config.cfg', cfgloglevel= 30):
    """Read config file into dictionary cfg.

    Params:
    cfgfile     -- Default is 'config.cfg' in the program directory
        Absolute or relative path (from the main program directory) may
        be specified.
    cfgloglevel -- sets logging level during config file loading.
        Default is 30:WARNING.

    Notes:
    Logging module levels: 10:DEBUG, 20:INFO, 30:WARNING, 40:ERROR, 50:CRITICAL
    Optional LoggingLevel in the config file will set the logging level after
    the config has been loaded.  The default logging level is 30:WARNING.
    """

    logging.getLogger().setLevel(cfgloglevel)

    if os.path.isabs(cfgfile):  config = cfgfile
    else:                       config = progdir + '/' + cfgfile

    if not os.path.exists(config):
        logging.error("loadConfg:  Config file <{}> does not exist.  Aborting.".format(config))
        exit()
    
    logging.info ('Loading {}'.format(config))
    with open(config) as ifile:
        for line in ifile:
            line = line[0:line.find('#')].lstrip().rstrip() # throw away comment and any leading & trailing whitespace
            if len(line) > 0:
                xx = line.strip().split(None, 1)        # parse to 2-element list
                if len(xx) == 2:
                    try:
                        cfg[xx[0]] = int(xx[1])         # append int to dict
                    except:
                        cfg[xx[0]] = xx[1]              # append string to dict
                    logging.debug ("Loaded {} = {}".format(xx[0], xx[1]))
                else: logging.warning ("loadConfig error on line {}.  Line skipped.".format(xx))

    if 'LoggingLevel' in cfg:                           # LoggingLevel from config file sets the following log level
        ll = cfg['LoggingLevel']
        logging.info ('Logging level set to <{}>'.format(ll))
        logging.getLogger().setLevel(ll)
    else:  logging.getLogger().setLevel(30)             # INFO level is default


def JAM():
    """Jam new values into cfg from the file 'JAM' in the program directory,
    if exists.  This allows for changing config values on a running program.
    Use getcfg or direct references to cfg[] for each access, rather than
    getting a local value, else newly jammed values wont be used.
    After the new values are loaded the JAM file is renamed to JAMed.
    The logging level may be changed by setting/changing LoggingLevel.
    """
    
    if os.path.exists(progdir + '/JAM'):
        with open(progdir + '/JAM') as ifile:
            for line in ifile:
                line = line[0:line.find('#')].lstrip().rstrip() # throw away comment and any leading & trailing whitespace
                if len(line) > 0:
                    xx = line.strip().split(None, 1)    # parse to 2-element list
                    if len(xx) == 2:
                        try:
                            cfg[xx[0]] = int(xx[1])     # append int to dict
                        except:
                            cfg[xx[0]] = xx[1]          # append string to dict
                        logging.warning ("JAMed {} = {}".format(xx[0], xx[1]))
                    else: logging.warning ("JAM error on line {}.  Line skipped.".format(xx))
        if os.path.exists(progdir + '/JAMed'): os.remove(progdir + '/JAMed')
        os.rename (progdir + '/JAM', progdir + '/JAMed')

    if 'LoggingLevel' in cfg:                           # LoggingLevel from config file sets the following log level
        ll = cfg['LoggingLevel']
        logging.info ('Logging level set to <{}>'.format(ll))
        logging.getLogger().setLevel(ll)
    else:  logging.getLogger().setLevel(30)             # INFO level is default


def getcfg(param, default=None):
    """Get a param from the cfg dictionary.
    Equivalent to just referencing cfg[], but with handling if the item does
    not exist.
    
    Params:
    param   -- string name of item to be fetched from cfg
    default -- if provided, is returned if the param doesn't exist in cfg.

    Error and abort if param does not exist in cfg and no default provided.
    """
    
    try:
        return cfg[param]
    except:
        if default != None:  return default
        logging.error ("Config error:  <{}> missing or invalid value.  Aborting.".format(param))
        exit()


def requestlock(caller):
    """Lock file request.
    The lock file is /tmp/LOCK.

    Param:
    caller -- Info written to the lock file and displayed in any error messages.  

    Note that on Windows /tmp is expected on the same drive as the progdir,
    which may not be C:
    """
    if not os.path.exists("/tmp"):      
        logging.error ("requestlock:  /tmp directory does not exist.  Create it manually(?).  Aborting.")
        exit()
        
    for xx in range(5):
        if os.path.exists("/tmp/LOCK"):
            with open("/tmp/LOCK") as ifile:
                lockedBy = ifile.read()
                logging.warning ("{}.  Waiting a sec.".format(lockedBy))
            time.sleep (1)
        else:  
            with open("/tmp/LOCK", 'w') as ofile:
                ofile.write("Locked by {} at {}".format(caller, time.asctime(time.localtime())))
                logging.debug ("LOCKed by {} at {}.".format(caller, time.asctime(time.localtime())))
            return 0
    logging.warning ("Timed out waiting for LOCK file to be cleared.  {}".format(lockedBy))
    return -1
        

def releaselock(caller):
    """Lock file release.
    Any code can release a lock, even if that code didn't request the lock.
    Only the requester should issue the releaselock.

    Param:
    caller -- Used only for logging info.
    """
    if os.path.exists("/tmp/LOCK"):
        with open("/tmp/LOCK") as ifile:
            lockedBy = ifile.read()
            logging.debug ("Caller {} removed lock file requested by {}.".format(caller, lockedBy))
        os.remove("/tmp/LOCK")
        return 0
    else:
        logging.warning ("<{}> attempted to remove /tmp/LOCK but the file does not exist.".format(caller))
        return -1
        

def snd_notif(subj='Notification message', msg=''):
    """Send a text message using the cfg NotifList from the config file.

    Params:
    subj -- Subject text string
    msg  -- Message text string

    cfg NotifList is required in the config file.
    cfg DontNotif is optional, and if == True no text message is sent.
    Useful for debug.
    """

    xx = 0
    if getcfg('DontNotif', default='False') == 'True':
        logging.warning ("sndNotif:  DontNotif==True - Message NOT sent <{}> <{}>".format(subj, msg))
    else:
        xx = snd_email (subj=subj, body=msg, to='NotifList')
        logging.warning ("Notification message sent <{}> <{}>".format(subj, msg))
    return xx


def snd_email(subj='', body='', filename='', to=''):
    """Send an email message using email account info from the config file.
    Either body or fileName must be passed.  body takes precedence over fileName.

    Params:
    body     -- is a string message to be sent.
    filename -- is a string full path to the file to be sent.
        Default path is the program directory.
        Absolute and relative paths accepted
    to       -- to whom to send the message
        to may be a single email address (contains an '@') string 
        or it is assumed to be a cfg keyword with list of eamil addresses

    cfg EmailFrom and EmailServer are required in the config file
    cfg EmailUser and EmailPass are optional in the config file.
        Needed if the server requires crudentials.
    cfg DontEmail is optional, and if == True no email is sent.
        Also blocks sndNotifs.  Useful for debug.

    NOTE:  Likely not correctly implemented for SSL mail sending.
    """

    if getcfg('DontEmail', default='False') == 'True':
        logging.warning ("snd_email:  DontEmail==True - <{}> message NOT emailed.".format(subj))
        return

    if not (body == ''):
        m = body
    elif os.path.exists(filename):
        fp = open(filename, 'rb')
        m = fp.read()
        fp.close()
    else: logging.error ("snd_email:  No <body> and can't find file <{}>.".format(filename)); exit()

    m += '\n(sent {})'.format(time.asctime(time.localtime()))

    if '@' in to:
          To = to.split()           # To must be a list
    else: To = getcfg(to).split()
    if not (len(To) > 0):
        logging.error ("snd_email:  <to> list is invalid: <{}>.".format(to)); exit()
    try:
        msg = MIMEText(m)
        msg['Subject'] = subj
        msg['From'] = getcfg('EmailFrom')
        msg['To'] = ", ".join(To)

        s = smtplib.SMTP(getcfg('EmailServer'))

        if 'EmailUser' in cfg:
            s.login (getcfg('EmailUser'), getcfg('EmailPass'))
        # s.set_debuglevel(1)
        s.sendmail(getcfg('EmailFrom'), To, msg.as_string())
        s.quit()

        logging.debug ("Sent message <{}>".format(subj))
    except Exception, e:
        logging.warning ("snd_email:  Send failed for <{}>: <{}>".format(subj, e))
        return -1
    return 0


if __name__ == '__main__':

    setuplogging(logfile= 'testlogfile.txt')
    loadconfig (cfgfile='testcfg.cfg', cfgloglevel=10)

    # Tests for loadConfig, getcfg
##    for key in cfg:
##        print "{:>15} = {}".format(key, cfg[key])
##
##    print "Testing getcfg - Not in cfg with default: <{}>".format(getcfg('NotInCfg', '--default--'))
##    print "Testing getcfg - Not in cfg with no default... will cause an exit()"
##    getcfg('NotInCfg-NoDef')


    # Tests for JAM
##    with open("JAM", 'w') as ofile:
##        ofile.write("JammedInt 1234\n")
##        ofile.write("JammedStr This is a text string # with a comment on the end\n")
##        ofile.write("LoggingLevel 10\n")
##    JAM()
##    print "JammedInt = <{}>, {}".format(getcfg('JammedInt'), type(getcfg('JammedInt')))
##    print "JammedStr = <{}>, {}".format(getcfg('JammedStr'), type(getcfg('JammedStr')))


    # Tests for sndNotif and snd_email
##    cfg['DontEmail'] = 'True'
##    cfg['DontNotif'] = 'True'
##    snd_email (subj="Test email with body", body="To be, or not to be...", to="xyz@gmail.com")
##    snd_email (subj="Test email with filename", filename="testfile.txt", to="EmailTo")
##    snd_notif (subj="This is a test subject", msg='This is the message body')


    # Tests for lock files
##    stat = requestlock ("try1")
##    print "got back from requestLock.  stat = {}".format(stat)
##    stat = requestlock ("try2")
##    print "got back from 2nd requestLock.  stat = {}".format(stat)
##    stat = releaselock ("try1")
##    print "got back from releaseLock.  stat = {}".format(stat)
##    stat = releaselock ("try2")
##    print "got back from 2nd releaseLock.  stat = {}".format(stat)

    