#!/usr/bin/env python
"""Stimulate GMail to pull mail from the remote email host more often.
Typically run every 5 minutes by a cron job:
 */5  *  *  *  *  cd /<path to script dir>/ && ./gmailnudge.py >> log.txt 2>&1
Set up a filter in GMail to delete these messages.
"""
__version__ = "v0.2 200426"

#==========================================================
#
#  Chris Nelson, January 2018-2020
#
# 190319 v0.2  Added NudgeText config param
# 180521 v0.1  New
#
# Changes pending
#   
#==========================================================

import sys
sys.path.append('../funcs3')    # Useful if funcs3 is placed elsewhere
from funcs3 import *

setuplogging()

def main():
    loadconfig(cfgfile = 'gmailnudge.cfg')

    # Set up GMail rule to delete messages with subject = the NudgeText in config file.
    snd_email (subj=getcfg('NudgeText'), body="Don't care", to='EmailTo')

    logging.info ('Nudge message sent')


if __name__ == '__main__': main()
