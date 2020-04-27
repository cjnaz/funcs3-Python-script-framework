#!/usr/bin/env python
"""Check WAN IP address and if it has changed then send me an email
Intended to be run every hour by a cron job:
  01  *  *  *  *  cd /<path to script>/wanipcheck && ./wanipcheck.py >> log.txt 2>&1
"""

__version__ = "v0.3 200426"

#==========================================================
#
#  Chris Nelson, January 2018-2020
#
# 200426 v0.3  Changed to curl, updated funcs3 module.
# 190319 v0.2  Genericized EmailTo, fixed Python 3x compatibility.
# 180521 v0.1  New
#
# Changes pending
#   
#==========================================================


import subprocess
import sys                      # Useful if funcs3 is placed elsewhere
sys.path.append('../funcs3')
from funcs3 import *

setuplogging()

def main():
    loadconfig(cfgfile = 'WANIPCheck.cfg')

    try:
        WANip = subprocess.run(["curl", 'https://ipapi.co/ip/'], capture_output=True, text=True).stdout # .split("\n")
    except Exception as e:
        logging.error ("Getting the WAN IP failed: <{}>".format(e))
        sys.exit (1)

    WANfile = progdir + '/' + getcfg('WanIpFile')

    if not os.path.exists(WANfile):
        with open(WANfile, 'w') as ofile:
            ofile.write (WANip)
            logging.warning ("Created {} with IP address {}".format(WANfile, WANip))
        sys.exit ()

    with open(WANfile) as ifile:
        SavedWANip = ifile.readline()

    if WANip != SavedWANip:
        message = "Prior WAN IP: <{}>. Current WAN IP: <{}>".format (SavedWANip, WANip)
        subject = "NOTICE:  HOME WAN IP CHANGED"
        snd_notif (subj=subject, msg=message, log=True)     # ERROR CHECK THESE
        snd_email (subj=subject, body=message, to='EmailTo')

        with open(WANfile, 'w') as ofile:
            ofile.write (WANip)
    else: logging.info ("No change")


if __name__ == '__main__': main()
