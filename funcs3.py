#!/usr/bin/env python3
"""Funcs (gen 3)
A collection of support functions for simplifying writing tool scripts.

Functions:
    setuplogging             - Set up default logger (use if not using loadconfig)
    funcs3_min_version_check - Checker for funcs3 module min version
    loadconfig, getcfg       - Config file handlers
    requestlock, releaselock - Cross-tool/process safety handshake
    snd_notif, snd_email     - Send text message and email messages

    Import this module from the main script as follows:
        from funcs3 import *
      or import specific items:
        from funcs3 import PROGDIR, loadconfig, getcfg, cfg, setuplogging, logging, funcs3_min_version_check, funcs3_version, snd_notif, snd_email

Globals:
    cfg - Dictionary that contains the info read from the config file
    PROGDIR - A string var that contains the full path to the main
        program directory.  Useful for file IO when running the script
        from a different pwd, such as when running from cron.
"""

funcs3_version = "V1.0 220131"

#==========================================================
#
#  Chris Nelson, 2018-2020
#
# V1.0  220131  baseline
# V0.7a 210529  Bug in snd_email & snd_notif with log switch as logging at info level, changed to warning level.
# V0.7  210523  loadconfig flush_on_reload switch added.
# V0.6  210512  loadconfig returns True when cfg has been (re)loaded.  loadconfig supports import, flush and booleans.
#   ConfigError and SndEmailError exceptions now raised rather than terminating on critical error.
# V0.5  201203  Passing None to setuplogging logfile directs output to stdout.  Added funcs3_min_version_check().
# V0.4  201028  Reworked loadconfig & JAM with re to support ':' and '=' delimiters.
#   loadconfig may be re-called and will re-load if the config file mod time has changed.
#   Added '/' to progdir.  Requires Python3.
# V0.3  200426  Updated for Python 3. Python 2 unsupported.  Using tempfile module.
# V0.2  190319  Added email port selection and SSL/TLS support
# V0.1  180520  New
#
# Changes pending
#   
#==========================================================

import sys
import time
import os.path
import io
import smtplib
from email.mime.text import MIMEText
import logging
import tempfile
import re
import __main__

# Configs / Constants
# FILE_LOGGING_FORMAT    = '%(asctime)s/%(module)s/%(funcName)s/%(levelname)s:  %(message)s'    # Classic format
FILE_LOGGING_FORMAT    = '{asctime} {module:>10}.{funcName:20} {levelname:>8}:  {message}'
CONSOLE_LOGGING_FORMAT = '{funcName:>20} - {levelname:>8}:  {message}'
DEFAULT_LOGGING_LEVEL  = logging.WARNING

# Project globals
cfg = {}
PROGDIR = os.path.dirname(os.path.realpath(__main__.__file__)) + "/"

# Internal globals
_config_timestamp = 0
_current_loglevel = None
_current_logfile = None


#=====================================================================================
#=====================================================================================
#  Module exceptions
#=====================================================================================
#=====================================================================================
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ConfigError(Error):
    """Exceptions raised for config file function errors.
    Attributes:
        message -- error message including item in error
    Format:
        ConfigError:  <function> - <message>.
    """
    def __init__(self, message):
        self.message = message

class SndEmailError(Error):
    """Exceptions raised for snd_email and snd_notif errors.
    Attributes:
        message -- error message including item in error
    Format:
        SndEmailError:  <function> - <message>.
    """
    def __init__(self, message):
        self.message = message


#=====================================================================================
#=====================================================================================
#  Logging setup
#=====================================================================================
#=====================================================================================
def setuplogging (loglevel, logfile=None):
    """Set up logging.

    loglevel
        10(DEBUG), 20(INFO), 30(WARNING), 40(ERROR), 50(CRITICAL)
    logfile
        Default None logs to console.  Absolute path or relative path from the
        main program directory may be specified.
    
    Returns nothing
    """
    if logfile == None:
        logging.basicConfig(level=loglevel, format=CONSOLE_LOGGING_FORMAT, style='{')
    else:
        if os.path.isabs(logfile):
            logpath = logfile
        else:
            logpath = PROGDIR + logfile
        logging.basicConfig(level=loglevel, filename=logpath, format=FILE_LOGGING_FORMAT, style='{')


#=====================================================================================
#=====================================================================================
#  funcs3 minimum version check
#=====================================================================================
#=====================================================================================
def funcs3_min_version_check(min_version):
    """Compare current funcs3 module version against passed in minimum expected version.

    min_version
        Int or float
    
    Return True if current version >= passed-in min version, else False
    """
    current_version = float(funcs3_version[1:4])
    if current_version >= min_version:
        return True
    else:
        return False


#=====================================================================================
#=====================================================================================
#  Config file functions loadconfig, getcfg
#=====================================================================================
#=====================================================================================
cfgline = re.compile(r"([^\s=:]+)[\s=:]+(.+)")

def loadconfig(cfgfile      = 'config.cfg',
        cfgloglevel         = DEFAULT_LOGGING_LEVEL,
        cfglogfile          = None,
        cfglogfile_wins     = False,
        flush_on_reload     = False,
        force_flush_reload  = False,
        isimport            = False):
    """Read config file into dictionary cfg, and set up logging.  See README.md loadconfig documentation for important usage details.

    cfgfile
        Default is 'config.cfg' in the program directory.  Absolute path or relative path from
        the main program directory may be specified.
    cfgloglevel
        Sets logging level during config file loading. Default is 30(WARNING).
    cfglogfile
        Log file to open - optional
    cfglogfile_wins
        cfglogfile overrides any LogFile specified in the config file
    flush_on_reload
        If the config file will be reloaded (due to being changed) then clean out cfg first
    force_flush_reload
        Forces cfg to be cleaned out and the config file to be reloaded
    isimport
        Internally set True when handling imports.  Not used by top-level scripts.

    Returns True if cfg has been (re)loaded, and False if not reloaded, so that the
    caller can do processing only if the cfg is freshly loaded.

    A ConfigError is raised if there are file access or parsing issues.
    """
    global _config_timestamp
    global cfg
    global _current_loglevel
    global _current_logfile
    
    # Initial logging will go to the console if no cfglogfile is specified on the initial loadconfig call.
    if _current_loglevel is None:
        setuplogging(cfgloglevel, logfile=cfglogfile)
        _current_loglevel = cfgloglevel
        _current_logfile  = cfglogfile

    if force_flush_reload:
        logging.getLogger().setLevel(cfgloglevel)           # logging within loadconfig is always done at cfgloglevel
        _current_loglevel = cfgloglevel
        logging.debug("cfg dictionary flushed and forced reloaded (force_flush_reload)")
        cfg.clear()
        _config_timestamp = 0

    if os.path.isabs(cfgfile):
        config = cfgfile
    else:
        config = PROGDIR + cfgfile

    if not os.path.exists(config):
        _msg = f"Config file <{config}> not found."
        raise ConfigError (_msg)

    try:
        if not isimport:        # Top level config file
            current_timestamp = os.path.getmtime(cfgfile)
            if _config_timestamp == current_timestamp:
                return False

            # Initial load call, or config file has changed.  Do (re)load.
            _config_timestamp = current_timestamp
            logging.getLogger().setLevel(cfgloglevel)   # Set logging level for remainder of loadconfig call
            _current_loglevel = cfgloglevel

            if flush_on_reload:
                cfg.clear()
                logging.debug (f"cfg dictionary flushed and reloaded due to changed config file (flush_on_reload)")

        logging.info (f"Loading {config}")
        with io.open(config, encoding='utf8') as ifile:
            for line in ifile:
                if line.strip().lower().startswith("import"):           # Is an import line
                    line = line.split("#", maxsplit=1)[0].strip()
                    target = os.path.expanduser(line.split()[1])
                    if os.path.exists(target):
                        loadconfig(target, cfgloglevel, isimport=True)
                    else:
                        _msg = f"Could not find and import <{target}>"
                        raise ConfigError (_msg)
                else:                                                   # Is a param/key line
                    _line = line.split("#", maxsplit=1)[0].strip()
                    if len(_line) > 0:
                        out = cfgline.match(_line)
                        if out:
                            key = out.group(1)
                            rol = out.group(2)  # rest of line
                            isint = False
                            try:
                                cfg[key] = int(rol)         # add int to dict
                                isint = True
                            except:
                                pass
                            if not isint:
                                if rol.lower() == "true":   # add bool to dict
                                    cfg[key] = True
                                elif rol.lower() == "false":
                                    cfg[key] = False
                                else:
                                    cfg[key] = rol          # add string to dict
                            logging.debug (f"Loaded {key} = <{cfg[key]}>  ({type(cfg[key])})")
                        else: logging.warning (f"loadconfig:  Error on line <{line}>.  Line skipped.")


    except Exception as e:
        _msg = f"Failed while attempting to open/read config file <{config}>.\n  {e}"
        raise ConfigError (_msg) from None

    # Operations only for finishing a top-level call
    if not isimport:
        if getcfg("DontEmail", False):
            logging.info ('DontEmail is set - Emails and Notifications will NOT be sent')
        elif getcfg("DontNotif", False):
            logging.info ('DontNotif is set - Notifications will NOT be sent')

        if not cfglogfile_wins:
            config_logfile  = getcfg("LogFile", None)
            logger = logging.getLogger()
            if config_logfile != _current_logfile:
                if config_logfile is None:
                    logging.error("Changing the LogFile from a real file to None is not supported.  Aborting.")
                    sys.exit()
                logger.handlers.clear()                             # remove the current stream/file handler
                handler = logging.FileHandler(config_logfile, "a")
                handler.setFormatter(logging.Formatter(fmt=FILE_LOGGING_FORMAT, style='{'))
                logger.addHandler(handler)
                _current_logfile = config_logfile
                logging.info (f"Logging file  changed to <{config_logfile}>")   # Logged based on cfgloglevel

        config_loglevel = getcfg("LogLevel", None)
        if config_loglevel is not None:
            if config_loglevel != _current_loglevel:
                logging.info (f"Logging level changed to <{config_loglevel}> from config file")
                logging.getLogger().setLevel(config_loglevel)       # Restore loglevel from that set by cfgloglevel
                _current_loglevel = config_loglevel

    return True


def getcfg(param, default="__nodefault__"):
    """Get a param from the cfg dictionary.

    Returns the value of param from the cfg dictionary.  Equivalent to just referencing cfg[]
    but with handling if the item does not exist.
    
    param
        String name of param/key to be fetched from cfg
    default
        if provided, is returned if the param doesn't exist in cfg

    Raises ConfigError if param does not exist in cfg and no default provided.
    """
    
    try:
        return cfg[param]
    except:
        if default != "__nodefault__":
            return default
    _msg = f"getcfg - Config parameter <{param}> not in cfg and no default."
    raise ConfigError (_msg)


#=====================================================================================
#=====================================================================================
#  Lock file management functions
#=====================================================================================
#=====================================================================================

LOCKFILE_DEFAULT = "funcs3_LOCK"
LOCK_TIMEOUT     = 5                # seconds

def requestlock(caller, lockfile=LOCKFILE_DEFAULT, timeout=LOCK_TIMEOUT):
    """Lock file request.

    caller
        Info written to the lock file and displayed in any error messages
    lockfile
        Lock file name.  Various lock files may be used simultaneously
    timeout
        Default 5s

    Returns
        0:  Lock request successful
       -1:  Lock request failed.  Warning level log messages are generated.
    """
    lock_file = os.path.join(tempfile.gettempdir(), lockfile)

    xx = time.time() + timeout
    while True:
        if not os.path.exists(lock_file):
            try:
                with io.open(lock_file, 'w', encoding='utf8') as ofile:
                    ofile.write(f"Locked by <{caller}> at {time.asctime(time.localtime())}.")
                    logging.debug (f"LOCKed by <{caller}> at {time.asctime(time.localtime())}.")
                return 0
            except Exception as e:
                logging.warning(f"Unable to create lock file <{lock_file}>\n  {e}")
                return -1
        else:
            if time.time() > xx:
                break
        time.sleep(0.1)

    try:
        with io.open(lock_file, encoding='utf8') as ifile:
            lockedBy = ifile.read()
        logging.warning (f"Timed out waiting for lock file <{lock_file}> to be cleared.  {lockedBy}")
    except Exception as e:
        logging.warning (f"Timed out and unable to read existing lock file <{lock_file}>\n  {e}.")
    return -1


def releaselock(lockfile=LOCKFILE_DEFAULT):
    """Lock file release.

    Any code can release a lock, even if that code didn't request the lock.
    Generally, only the requester should issue the releaselock.

    lockfile
        Lock file to remove/release

    Returns
        0:  Lock release successful (lock file deleted)
       -1:  Lock release failed.  Warning level log messages are generated.
    """
    lock_file = os.path.join(tempfile.gettempdir(), lockfile)
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except Exception as e:
            logging.warning (f"Unable to remove lock file <{lock_file}>\n  {e}.")
            return -1
        logging.debug(f"Lock file removed: <{lock_file}>")
        return 0
    else:
        logging.warning(f"Attempted to remove lock file <{lock_file}> but the file does not exist.")
        return -1


#=====================================================================================
#=====================================================================================
#  Notification and email functions
#=====================================================================================
#=====================================================================================

def snd_notif(subj='Notification message', msg='', log=False):
    """Send a text message using the cfg NotifList.

    subj
        Subject text string
    msg
        Message text string
    log
        If True, elevates log level from DEBUG to WARNING to force logging

    cfg NotifList is required in the config file
    cfg DontNotif and DontEmail are optional, and if == True no text message is sent. Useful for debug.

    Raises SndEmailError on call errors and sendmail errors
    """

    if getcfg('DontNotif', default=False)  or  getcfg('DontEmail', default=False):
        if log:
            logging.warning (f"Notification NOT sent <{subj}> <{msg}>")
        else:
            logging.debug (f"Notification NOT sent <{subj}> <{msg}>")
        return

    snd_email (subj=subj, body=msg, to='NotifList')
    if log:
        logging.warning (f"Notification sent <{subj}> <{msg}>")
    else:
        logging.debug (f"Notification sent <{subj}> <{msg}>")


def snd_email(subj='', body='', filename='', to='', log=False):
    """Send an email message using email account info from the config file.

    Either body or filename must be passed.  body takes precedence over filename.

    subj
        Email subject text
    body
        A string message to be sent
    filename
        A string full path to the file to be sent.  Default path is the PROGDIR.
        Absolute and relative paths from PROGDIR accepted.
    to
        To whom to send the message.  To may be a single email address (contains an '@') or
        it is assumed to be a cfg keyword with a whitespace-separated-list of email addresses.
    log
        If True, elevates log level from DEBUG to WARNING to force logging of the email subj

    cfg EmailFrom, EmailServer, and EmailServerPort are required in the config file.
        EmailServerPort must be one of the following:
            P25:  SMTP to port 25 without any encryption
            P465: SMTP_SSL to port 465
            P587: SMTP to port 587 without any encryption
            P587TLS:  SMTP to port 587 and with TLS encryption
    cfg EmailUser and EmailPass are optional in the config file.
        Needed if the server requires credentials.  Recommend that these params be in a secure file in 
        one's home dir and import the file via the config file.
    cfg DontEmail is optional, and if == True no email is sent.
        Also blocks snd_notifs.  Useful for debug.
    cfg EmailVerbose = True enables the emailer debug level.
    """

    if getcfg('DontEmail', default=False):
        if log:
            logging.warning (f"Email NOT sent <{subj}>")
        else:
            logging.debug (f"Email NOT sent <{subj}>")
        return

    if not (body == ''):
        m = body
    elif os.path.exists(filename):
        fp = io.open(filename, encoding='utf8')
        m = fp.read()
        fp.close()
    else:
        _msg = f"snd_email - No <body> and can't find file <{filename}>."
        raise SndEmailError (_msg)

    m += f"\n(sent {time.asctime(time.localtime())})"

    if '@' in to:
          To = to.split()           # To must be a list
    else: To = getcfg(to).split()
    if not (len(To) > 0):
        _msg = f"snd_email - 'to' list is invalid: <{to}>."
        raise SndEmailError (_msg)

    try:
        msg = MIMEText(m)
        msg['Subject'] = subj
        msg['From'] = getcfg('EmailFrom')
        msg['To'] = ", ".join(To)

        server = getcfg('EmailServer')
        port = getcfg('EmailServerPort')
        if port == "P25":
            s = smtplib.SMTP(server, 25)
        elif port == "P465":
            s = smtplib.SMTP_SSL(server, 465)
        elif port == "P587":
            s = smtplib.SMTP(server, 587)
        elif port == "P587TLS":
            s = smtplib.SMTP(server, 587)
            s.starttls()
        else:
            raise ConfigError (f"Config EmailServerPort <{port}> is invalid")

        if 'EmailUser' in cfg:
            s.login (getcfg('EmailUser'), getcfg('EmailPass'))
        if getcfg("EmailVerbose", default=False): # == True:
            s.set_debuglevel(1)
        s.sendmail(getcfg('EmailFrom'), To, msg.as_string())
        s.quit()

        if log:
            logging.warning (f"Email sent <{subj}>")
        else:
            logging.debug (f"Email sent <{subj}>")
    except Exception as e:
        _msg = f"snd_email:  Send failed for <{subj}>:\n  <{e}>"
        raise SndEmailError (_msg)


if __name__ == '__main__':

    loadconfig (cfgfile='testcfg.cfg', cfgloglevel=10)

    # # ===== Tests for funcs3_min_version_check =====
    # if not funcs3_min_version_check(2):
    #     print(f"ERROR:  funcs3 module must be at least version 2.0.  Found <{funcs3_version}>.")
    # if funcs3_min_version_check(1): #0.7):
    #     print(f"funcs3_min_version_check passes.  Found <{funcs3_version}>.")


    # # ===== Tests for loadconfig, getcfg =====
    # # Test config loading exceptions
    # try:
    #     loadconfig("nosuchfile.txt", cfgloglevel=getcfg("CfgLogLevel", 30))
    # except ConfigError as e:
    #     logging.error (f"In main...  {e}")
    # loadconfig("nosuchfile.txt")      # This one exercises untrapped error caught by Python

    # # Test config reload - Edit CfgLogLevel, LogLevel, LogFile, and testvar in testcfg.cfg
    # print (f"Initial logging level: {logging.getLogger().level}")
    # while True:
    #     reloaded = loadconfig (cfgfile='testcfg.cfg', cfgloglevel=getcfg("CfgLogLevel", 30), flush_on_reload=True) #, cfglogfile="junk9.txt")#, cfgloglevel=10)
    #     if reloaded:
    #         print ("\nConfig file reloaded")
    #         print (f"Logging level: {logging.getLogger().level}")
    #         logging.debug   ("Debug   level message")
    #         logging.info    ("Info    level message")
    #         logging.warning ("Warning level message")
    #         print ("testvar", getcfg("testvar", None), type(getcfg("testvar", None)))
    #     time.sleep(.5)

    # # Tests for getcfg with/without defaults
    # print (f"Testing getcfg - Not in cfg with default: <{getcfg('NotInCfg', 'My Default Value')}>")
    # try:
    #     getcfg('NotInCfg-NoDef')
    # except ConfigError as e:
    #     print (e)
    # getcfg('NotInCfg-NoDef')          # This one exercises untrapped error caught by Python

    # # Test flush_on_reload, force_flush
    # from pathlib import Path
    # cfg["dummy"] = True
    # print (f"var dummy in cfg: {getcfg('dummy', False)}")                       # The first True
    # loadconfig(cfgfile='testcfg.cfg', flush_on_reload=True, cfgloglevel=10)
    # print (f"var dummy in cfg: {getcfg('dummy', False)}")                       # True because not reloaded
    # Path('testcfg.cfg').touch()
    # # Alternately enable each of these calls
    # loadconfig(cfgfile='testcfg.cfg', cfgloglevel=10)                           # dummy still exists (not flushed)
    # # loadconfig(cfgfile='testcfg.cfg', flush_on_reload=True, cfgloglevel=10)     # dummy flushed on reload
    # # loadconfig(cfgfile='testcfg.cfg', force_flush_reload=True, cfgloglevel=10)  # dummy force flushed
    # print (f"var dummy in cfg: {getcfg('dummy', False)}")


    # # ===== Tests for snd_notif and snd_email =====
    # # Set debug or warning LogLevel
    # # cfg['DontEmail'] = True     # Comment these in/out
    # # cfg['DontNotif'] = True
    # snd_email (subj="Test email with body", body="To be, or not to be...", to="EmailTo")
    # snd_email (subj="Test email with body", body="To be, or not to be...", to="xyz@gmail.com")
    # try:            # No such file.  Exception raised.
    #     snd_email (subj="Test email with filename JAMed", filename="JAMed", to="EmailTo")
    # except SndEmailError as e:
    #     print (f"snd_email failed:  {e}")
    # try:            # File should (normally) exist
    #     snd_email (subj="Test email with filename LICENSE.txt", filename="LICENSE.txt", to="EmailTo", log=True)
    # except SndEmailError as e:
    #     print (f"snd_email failed:  {e}")
    # snd_notif (subj="This is a test subject", msg='This is the message body')
    # snd_notif (subj="This is another test subject", msg='This is another message body', log=True)


    # # ===== Tests for lock files =====
    # stat = requestlock ("try1")
    # print (f"got back from 1st requestLock.  stat = {stat}")
    # stat = requestlock ("try2")
    # print (f"got back from 2nd requestLock.  stat = {stat}")
    # stat = releaselock ()
    # print (f"got back from 1st releaseLock.  stat = {stat}")
    # stat = releaselock ()
    # print (f"got back from 2nd releaseLock.  stat = {stat}")