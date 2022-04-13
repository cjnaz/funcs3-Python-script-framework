# funcs3 with gmailnudge and wanipcheck demo scripts

funcs gen3 is a collection of functions for building Python tools and scripts.  This code is supported only on Python 3.

A companion template script file is provided, along with template.cfg and template.service files.  I use these as the 
starter files for new tools.

` `
# gmailnudge demo code
This tool simply sends an email to a target address.  It demos the loadconfig, error logging, and email sending features in funcs3.

I run gmailnudge as a CRON job every 5 minutes to send an email to my domain's mail server.  I have GMail configured to fetch new
messages from my domain mail server so that I can get all of my email in one place, GMail.  The problem is that GMail checks the
remote mail server for new messages at a frequency based on how often there is new mail.  If you get a few messages a day then GMail
may not check for new messages but once an hour.  This is a serious problem if you are trying to reset a password on a web site and 
that site sends a reset message to your domain email account, but you can't get the message for a long time.  Within GMail I have a
filter rule set up to just delete new messages with a subject matching what is in `gmailnudge` in the config file.  

An exercise for the user:  Define a new `JunkSubject` var in the config file and change the snd_email call to use this new var.

` `
# wanipcheck demo code
(See [wanstatus](https://github.com/cjnaz/wanstatus) which includes monitoring internet access as well as WAN IP changes.)

This tool gets the WAN IP address and checks if it has changed.  If so, it sends email and text notification messages with the new 
WAN info.  NOTE that the minimum Python version is 3.7 due to use of 
subprocess.run with capture_output.

I use to not have a DDNS service for my domain, so if my home WAN address should change I would need to manually adjust my bookmarks for my web server. The wanipcheck script checks if the WAN IP address has changed, and if so sends the new info to both my 
email (using snd_email) and mobile text (using snd_notif). I run wanstatus as a CRON job hourly.

` `
# funcs3 Features

**_See the function documentation within the funcs3.py module for usage details._**

## Logging framework
Function & module var
- `setuplogging()` - Set up console or target file logging
- `logging` - Handle for logging calls in your code (i.e. `logging.info("Hello")`)

Python's logging framework is quite valuable for tracing more complicated scripts.  funcs3's `setuplogging` implementation is lean and functional.  It's 
especially valuable for scripts that will be run by CRON or as systemd services in order to provide debug info. Note that:
  - Logging goes to stderr.
  - If using loadconfig, then don't also call setuplogging.  loadconfig calls setuplogging.  See the logging notes in loadconfig, below.

## funcs3 minimum version check
Function & module var
- `funcs3_min_version_check()` - Compare min version required by the main script to the imported version of funcs3.
- `funcs3_version` - Content of the funcs3_version var 

Since the interfaces and features of func3 functions may change over time, 
`funcs3_min_version_check` allows for enforcing a minimum version rev level of the funcs3 
module from the calling script.  See example in wanipcheck.

## Configuration file and cfg dictionary
Functions & module vars
- `loadconfig()` - Read a configuration file into the cfg dictionary
- `getcfg()` - Retrieve a var from the cfg dictionary, with error check and default support
- `cfg{}` - Dictionary containing the config file keys
- `timevalue()` - Converts time value strings (i.e., 10s, 5m, 3h, 4d 5w) to seconds
- `retime()` - Converts a seconds value to an alternate time units

Config files make for easily customized and modified tools, rather than touching the code for such config edits.  The config file 
contents are read into the `cfg` dictionary.  The dictionary may be referenced directly as usual, such as `xx = cfg['EmailTo']`.  Alternately, use `getcfg` for accessing vars: `xx = getcfg('EmailTo')`.  `getcfg` provides error checking for 
if the var does not exist (maybe a typo?), and also supports a default mechanism.  On error, `getcfg` raises a `ConfigError` exception, which may be caught and handled in the main code.

The format of a config file is key/value pairs (with no section or default as in the Python configparser module).  Separating the key and value may be whitespace, `=` or `:`.See [testcfg.cfg](testcfg.cfg) for examples.



Notable loadconfig Features:

- **Native Ints, Bools, and Strings support** - Integer values in the config file are stored as integers in the cfg dictionary, True and False values (case insensitive) are stored as booleans, and 
all other entries are stored as strings.  This avoids having to clutter the script with explicit type casting.  If the config file has 
`xyz 5` then the script can be cleanly written as `if getcfg('xyz') > 3: ...`, or `print (cfg['xyz'] * 10)`. 
Similarly, `MyBool true` in the config file allows `if getcfg('MyBool'):` to be written.
- **Setup Logging** - The first call to loadconfig will set up a logging handler (calls funcs3.setuplogging, which calls basicConfig).  The `logging` handle is available for import by other modules (`from funcs3 import logging ...`).  By default, logging will go to the console at the WARNING/30 level and above.    
  - **Log level options** - Optional `LogLevel` in the config file will set the logging level after
  the config has been loaded.  If LogLevel is not specified in the config file, then 
  the logging level is set to the cfgloglevel passed to loadconfig (default 30:WARNING).
  The script code may also manually/explicitly set the logging level (after the initial loadconifig call, and config LogLevel not specified) and this value will be retained over later calls to loadconfig, thus allowing for a command line verbose switch feature.
  In any case, logging done within loadconfig is always done at the cfgloglevel.
  Logging module levels: 10(DEBUG), 20(INFO), 30(WARNING), 40(ERROR), 50(CRITICAL)
  - **Log file options** - The log file may be specified on the loadconfig call (cfglogfile), or may be
  specified via the `LogFile` param in the config file.  If cfglogfile is None (default) and no
  LogFile is specified in the loaded config file then logging will go to the console.  By default,
  specifying LogFile in the config file takes precedent over cfglogfile passed to loadconfig.
  Specifying `cfglogfile_wins=True` on the loadconfig call causes the specified cfglogfile to
  override any value specified in the loaded config file.  This may be useful for debug for directing log output to the console by overriding the config file LogFile value.
  Note that if LogFile is changed that logging will switch to the new file when the config file
  is reloaded.  Switching logging from a file back to the console is not supported.
  - **Logging format** - funcs3 has built-in format strings for console and file logging.  These defaults may be overridden by defining `CONSOLE_LOGGING_FORMAT` and/or `FILE_LOGGING_FORMAT` constants in the main script file.  See wanipcheck for an example.

- **Import nested config files** - loadconfig supports `Import` (keyword is case insensitive).  The listed file is imported as if the vars were in the main config file.  Nested imports are allowed.  A prime usage of `import` is to all placing email server credentials in your home directory with user-only readability.  
- **Config reload if changed** - loadconfig may be called periodically by the main script.  loadconfig detects
if the main/top-level config file modification time has changed and then reloads the file.  If `flush_on_reload=True` (default False) then the `cfg` dictionary is cleared/purged before reloading the config file.  If `force_flush_reload=True` (default False) then cfg is unconditionally cleared and the config file is reloaded.  loadconfig returns True if the config file was (re)loaded, so main code logic can run only when the config file was changed.  Reloading the config file when changed is especially useful for tools that run as services, such as [lanmonitor](https://github.com/cjnaz/lanmonitor).   This allows the main script to efficiently and dynamically track changes to the config file while the script is looping, such as for a service running forever in a loop.  See [lanmonitor](https://github.com/cjnaz/lanmonitor) for a working example.  Note that if using threading then a thread should be caused to pause while the config file is being reloaded with `flush_on_reload=True` or `force_flush_reload=True` since the params will disappear briefly.
- **timevalue and retime** - Time values in the form of "10s" (seconds) or "2.1h" (hours) may be reasonable as config file values.  `timevalue` is a class that accepts such time values and provides class vars for ease of use within your script.  `xx = timevalue("5m")` provides `xx.seconds` (float 300.0), `xx.original` ("5m" - the original string/int/float value passed), `xx.unit_str` ("mins"), and `xx.unit_char` ("m"). Supported resolutions are "s" (seconds), "m" (minutes), "h" (hours), "d" (days), and "w" (weeks), all case insensitive.
`retime` allows for converting (often for printing) a seconds-resolution time value to an alternate resolution.`retime` accepts an int or float seconds value and returns a float at the specified unit_char resolution.  For example, `print (retime(timevalue("3w").seconds, "d"))` prints "21.0".
- **ConfigError** - Critical errors within loadconfig and getcfg raise a `ConfigError`.  Such errors include loadconfig file access or parsing issues, and getcfg accesses to non-existing keys with no default.
- **Comparison to Python's configparser module** - configparser contains many customizable features.  Here are a few key comparisons:

  Feature | loadconfig | Python configparser
  ---|---|---
  Native types | Int, Bool (true/false case insensitive), String | String only, requires explicit type casting with getter functions
  Reload on config file change | built-in | requires coding
  Import sub-config files | Yes | No
  Section support | No | Yes
  Default support | No | Yes
  Fallback support | Yes (getcfg default) | Yes
  Whitespace in keywords | No | Yes
  Case sensitive keywords | Yes (always) | Default No, customizable
  Key/value delimiter | whitespace, ':', or '=' | ':' or '=', customizable
  Key only, no value | No | Yes
  Multi-line values | No | Yes
  Comment prefix | '#', fixed, thus can't be part of the value | '#' or ';', customizable
  Interpolation | No | Yes
  Mapping Protocol Access | No | Yes
  Save to file | No | Yes


## Email and text message sending
Functions
- `snd_notif()` - Tailored to sending text message notifications
- `snd_email()` - Sends an email

Features
- `snd_email` and `snd_notif` provide nice basic wrappers around Python's smtplib and use setup info from the config file.  The send-to target (config file `NotifList` default for snd_notif, or the function call `to=` parameter) is one or more email addresses (white space or comma separated).
Email 'to' address checking is very rudimentary - an email address must contain an `@` or a SndEmailError is raised.
- `snd_notif` is targeted to be used with mobile provider 
email-to-text-message bridge addresses, such as Verizon's xxxyyyzzzz@vzwpix.com.  [wanipcheck](wanipcheck) demonstrates sending a message
out when some circumstance comes up.  
Suggested application:  Write a script that checks status on critical processes on your server, and if anything
is wrong then send out a notification.  (Wait, rather than writing this, see [lanmonitor](https://github.com/cjnaz/lanmonitor).)
- `snd_email` supports sending a message built up by the script code as a python string, or by pointing to a text or html-formatted file.  
- The `EmailServer` and `EmailServerPort` settings in the config file support port 25 (plain text), port 465 (SSL), port 587 with plain text, and port 587 with TLS.
- `EmailUser` and `EmailPass` should be placed in a configuration file in your home directory, with access mode `600`, and `import`ed from your tool config file.
- On error, these functions raise an SndEmailError exception, which may be caught and handled in the main code.

## Lock file

Functions
- `requestlock()` - Set a file indicating to others that your tool is in-process
- `releaselock()` - Remove the lock file

Features
- For scripts that may take a long time to run and are run by CRON, the possibility exists that a job is still running when CRON wants to 
run it again, which may create a real mess.  The lock file mechanism is used in https://github.com/cjnaz/rclonesync-V2.  


## PROGDIR
Module var
- `PROGDIR` contains the absolute path to the main script directory.

PROGDIR is useful for building references to other files in the directory where the main script resides.  For example the default config file is at `os.path.join(PROGDIR, 'config.cfg'`).

` `
# Revision history
- V1.1 220412 - Added timevalue and retime
- V1.0 220131 - V1.0 baseline
- ...
- V0.1 180524 - New.  First github posting

