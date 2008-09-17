""" 
Author: Justin Cappos

Start Date: June 26th, 2008

Description:
Restricted execution environment for python.   Should stop someone from doing
"bad things" (which is also defined to include many useful things).
This module allows the user to define code that gets called either on the 
reciept of a packet, when a timer fires, on startup, and on shutdown.
The restricted code can only do a few "external" things like send data 
packets and store data to disk.   The CPU, memory, disk usage, and network
bandwidth are all limited.

Usage:  ./repy.py restrictionsfile.txt program_to_run.py

"""


import safe
import sys
import emulfile
import emultimer
import emulcomm
import emulmisc
import restrictions
import time
import threading
import logging

import stopfilewatcher

import nonportable

import statusstorage

## we'll use tracebackrepy to print our exceptions
import tracebackrepy

# Allow the user to do try, except, finally, etc.
safe._NODE_CLASS_OK.append("TryExcept")
safe._NODE_CLASS_OK.append("TryFinally")
safe._NODE_CLASS_OK.append("Raise")
safe._NODE_CLASS_OK.append("ExcepthandlerType")
safe._NODE_CLASS_OK.append("Invert")
# needed for traceback
# NOTE: still needed for tracebackrepy
safe._BUILTIN_OK.append("isinstance")
safe._BUILTIN_OK.append("BaseException")
safe._BUILTIN_OK.append("WindowsError")
safe._BUILTIN_OK.append("type")
safe._BUILTIN_OK.append("issubclass")
# needed for socket ops and other things...   These should be safe, right?
safe._BUILTIN_OK.append("getattr")
safe._BUILTIN_OK.append("hasattr")
safe._BUILTIN_OK.append("setattr")
# needed to allow primitive marshalling to be built
safe._BUILTIN_OK.append("ord")
safe._BUILTIN_OK.append("chr")
# __repr__ should be harmless, but do we really want to add it?
safe._STR_OK.append("__repr__")
# allow __ in strings.   I'm 99% sure this is okay (do I want to risk it?)
safe._NODE_ATTR_OK.append('value')





# This is the user's program after parsing
usercode = None
usercontext = {
	'mycontext':{}, 		# set up a place for them to store state
	'open':emulfile.emulated_open,	# emulated open function
	'file':emulfile.emulated_file,	# emulated file object
	'listdir':emulfile.listdir,	# List the files in the expts dir
	'removefile':emulfile.removefile,# remove a file in the expts dir
	'getmyip':emulcomm.getmyip, # provides an external IP
	'gethostbyname_ex':emulcomm.gethostbyname_ex, # same as socket method
	'recvmess':emulcomm.recvmess,	# message receive (UDP)
	'sendmess':emulcomm.sendmess, 	# message sending (UDP)
	'openconn':emulcomm.openconn,	# reliable comm channel (TCP)
	'waitforconn':emulcomm.waitforconn,# reliable comm listen (TCP)
	'stopcomm':emulcomm.stopcomm,	# stop receiving (TDP/UDP)
	'settimer':emultimer.settimer, 	# sets a timer
	'canceltimer':emultimer.canceltimer, # stops a timer if it hasn't fired
	'sleep':emultimer.sleep, 	# blocks the thread for some time
	'randomfloat':emulmisc.randomfloat,	# same as random.random()
	'getruntime':emulmisc.getruntime, # amount of time the program has run
	'getlock':emulmisc.getlock, 	# acquire a lock object
	'exitall':emulmisc.exitall	# Stops executing the sandboxed program
}



def main(restrictionsfn, program, args,stopfile=None):
  global usercontext
  global usercode
  global simpleexec

  # start the nanny up and read the restrictions files.  
  restrictions.init_restrictions(restrictionsfn)

  # check for a stop file (I need to do this after forking in 
  # init_restrictions)
  if stopfile:
    stopfilewatcher.init(stopfile)


  if logfile:
    # time to set up the circular logger
    loggerfo = logging.circular_logger(logfile)
    # and redirect err and out there...
    sys.stdout = loggerfo
    sys.stderr = loggerfo
  else:
    # let's make it so that the output (via print) is always flushed
    sys.stdout = logging.flush_logger(sys.stdout)


  usercode = file(program).read()

  # If the program doesn't have any special handling, just exec and exit
  if simpleexec:
    safe.safe_exec(usercode,usercontext)
    sys.exit(0)


  # I'll use this to detect when the program is idle so I know when to quit...
  idlethreadcount =  threading.activeCount()

  # call the initialize function
  usercontext['callfunc'] = 'initialize'
  usercontext['callargs'] = args[:]
  try:
    safe.safe_exec(usercode,usercontext)
  except SystemExit:
    raise
  except:
    # I think it makes sense to exit if their code throws an exception...
    tracebackrepy.handle_exception()
    nonportable.harshexit(6)

  # I've changed to the threading library, so this should increase if there are
  # pending events
  while threading.activeCount() > idlethreadcount:
    # do accounting here?
    time.sleep(1)

  # call the user program to notify them that we are exiting...
  usercontext['callfunc'] = 'exit'
  usercontext['callargs'] = (None,)
  try:
    safe.safe_exec(usercode,usercontext)
  except SystemExit:
    raise
  except:
    # I think it makes sense to exit if their code throws an exception...
    tracebackrepy.handle_exception()
    nonportable.harshexit(7)

  # normal exit...
  nonportable.harshexit(0)


if __name__ == '__main__':
  global simpleexec
  global logfile

  # Set up the simple variable if needed
  args = sys.argv[1:]
  simpleexec = False
  if sys.argv[1] == '--simple':
    simpleexec = True
    args = sys.argv[2:]

  if args[0] == '--logfile':
    # set up the circular log buffer...
    logfile = args[1]
    args = args[2:]

  else:
    # use standard streams (stdout / stderr
    logfile = None
    

    
  stopfile = None
  if args[0] == '--stop':
    # Watch for the creation of this file and abort when it happens...
    stopfile = args[1]
    args = args[2:]


  statusfile = None
  if args[0] == '--status':
    # Write status information into this file...
    statusfile = args[1]
    args = args[2:]

  statusstorage.init(statusfile)
  statusstorage.write_status("Started")


  restrictionsfn = args[0]
  progname = args[1]
  progargs = args[2:]

  tracebackrepy.initialize(progname)

  try:
    main(restrictionsfn, progname,progargs,stopfile)
  except SystemExit:
    nonportable.harshexit(4)
  except:
    tracebackrepy.handle_exception()
    nonportable.harshexit(3)
