# funcs3 with gmailnudge and wanipcheck demo stripts

funcs3 is a collection of functions for building basic Python tools and scripts.  This code was developed using Python 2.7, and tested/debugged for Python 3.

Tools using the loadconfig function will need to have a config file defined.  Three config files are included in this repo, 
but they must be adjusted by the user for valid email credentials and email addresses.


## gmailnudge
This tool simply sends an email to a target address.  It demos the loadconfig, error logging, and email sending features in funcs3.

I run gmailnudge as a CRON job every 5 minutes to send an email to my domain mail server.  I have GMail configured to fetch new
messages from my domain mail server so that I can get all of my email in one place, GMail.  The problem is that GMail checks the
remote mail server for new messages at a frequency based on how often there is new mail.  If you get a few messages a day then GMail
may not check for new messages but once an hour.  This is a serious problem if you are trying to reset a password on a web site and 
that site sends a reset message to your domain email account, but you cant get the message for a long time.  Within GMail I have a
filter rule set up to just delete new messages with a subject matching what is in gmailnudge.  

An exercise for the user:  Define a new `JunkSubject` var in the config file and change the snd_email call to use this new var.


## wanipcheck
This tool gets the WAN IP address and checks if it has changed.  If so, it send email and text notification messages with the new 
WAN info.

I have remote access tools set up on my mobile, but I'm not using a DDNS service, so if my home WAN address should change then my
remote access tools break.  The wanipcheck script checks if the WAN IP address has changed, and if so sends the new info to both my 
email (using snd_email) and mobile text (using snd_notif). I run this as a CRON job hourly.


## funcs3 major features

See the documentation within the funcs3.py module for usage details.

### Logging framework
Python's logging framework is quite valuable for tracing more complicated scripts.  funcs3's implementation is lean and functional.  It's 
especially valuable for scripts that will be run by CRON in order to provide debug info.


### Configuration file
Config files make for easily customized and modified tools, rather than touching the code for such config edits.  The config file 
contents are read into the `cfg` dictionary.  The dictionary may be referenced directly as usual, such as `xx = cfg['EmailTo']`.  Alternately, use
`getcfg` for accessing vars, at least the first time, such as `xx = getcfg('EmailTo')`.  `getcfg` provides error checking (with an ERROR log message) 
if the var does not exist (maybe a typo?), and also supports a default mechanism.  Note that `getcfg` exits (if no
default is specified) after the logged error message, rather than throwing an exception.  This would be a worthy enhancement for more complex scripts
usage, but I wanted to keep the main scripts clean and lean.

One nice thing about the config file reader is that integer values in the config file are stored as integers in the cfg dictionary, and 
all other entries are stored as strings.  This avoids having to clutter the scrpt with explicit type casting.  If the config file has 
`xyz 5` then the script can be cleanly written as `if getcfg('xyz') > 3: ...`, or `print cfg['xyz'] * 10`.  

The `JAM` function allows for changing values within the cfg dictionary on-the-fly while the script is running.  JAM is useful for 
tools/scripts that do not terminate, yet you want ot make some adjustments, such as changing the logging level.  In order for new values to be 
jammed and used within the script, `JAM()` must be called periodically, and accesses to the vars need to reference the dictionary rather
than assigning the dictionary value to a local variable and then only using the local variable.

### Email and text message sending
`snd_email` and `snd_notif` provide nice basic wrappers around Python's smtplib and use setup info from the config file.  The send-to targets can be multiple
email addresses by listing more than one with white space separation in the config file.  

`snd_notif` is expected to be used with mobile provider 
email-to-text-message bridge addresses, such as Verizon's xxxyyyzzzz@vzwpix.com.  wanipcheck is a good example of simply sending a message
out when some circumstance comes up.  
Suggested application:  Write a script that checks status on critical processes on your server, and if anything
is wrong then send out a notification.

`snd_email` supports sending a message built up by the script code as a python string, or by pointing to a file.  

The `EmailServer` and `EmailServerPort` settings in the config file support port 25 (plain text), port 465 (SSL), port 587 with plain text, and port 587 with TLS.

### Lock file
For scripts that may take a long time to run and are run by CRON, the possibility exists that a job is still running when CRON wants to 
run it again, which may create a real mess.  The lock file mechanism is used in https://github.com/cjnaz/RCloneSync.  


## Revision history

- 190319  Added email TLS support.  
- 180524  New.  First github posting

