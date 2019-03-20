#!/usr/bin/env python
"""Check WAN IP address and if it has changed then send me an email
Intended to be run every hour by a cron job:
  01  *  *  *  *  cd /<path to script>/wanipcheck && ./wanipcheck.py >> log.txt 2>&1
"""

# Revision history
# 190319  Genericized EmailTo, fixed Python 3x compatibility.
# 180521  New

import requests
import sys                      # Useful if funcs3 is placed elsewhere
sys.path.append('../funcs3')
from funcs3 import *

setuplogging()

def main():
    loadconfig(cfgfile = 'WANIPCheck.cfg')

    try:
        WANip = requests.get('https://ipapi.co/ip/').text
    except Exception as e:
        logging.error ("Getting the WAN IP failed: <{}>".format(e))
        exit ()

    WANfile = progdir + '/' + getcfg('WanIpFile')

    if not os.path.exists(WANfile):
        with open(WANfile, 'w') as ofile:
            ofile.write (WANip)
            logging.warning ("Created {} with IP address {}".format(WANfile, WANip))
        exit ()

    with open(WANfile) as ifile:
        SavedWANip = ifile.readline()

    if WANip != SavedWANip:
        message = "Prior WAN IP: <{}>. Current WAN IP: <{}>".format (SavedWANip, WANip)
        subject = "NOTICE:  HOME WAN IP CHANGED"
        snd_notif (subj=subject, msg=message)     # ERROR CHECK THESE
        snd_email (subj=subject, body=message, to='EmailTo')

        with open(WANfile, 'w') as ofile:
            ofile.write (WANip)
    else: logging.info ("No change")


if __name__ == '__main__': main()
