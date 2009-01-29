""" 
<Author>
  Justin Cappos
  Ivan Beschastnikh (12/24/08) -- added usage

<Start Date>
  June 26th, 2008

<Description>
  Restricted execution environment for python.  Should stop someone
  from doing "bad things" (which is also defined to include many
  useful things).  This module allows the user to define code that
  gets called either on the reciept of a packet, when a timer fires,
  on startup, and on shutdown.  The restricted code can only do a few
  "external" things like send data packets and store data to disk.
  The CPU, memory, disk usage, and network bandwidth are all limited.

<Usage>
  Usage: repy.py [options] restrictionsfile.txt program_to_run.py [program args]

  Where [options] are some combination of the following:

  --simple               : Simple execution mode -- execute and exit
  --logfile filename.txt : Set up a circular log buffer and output to logfilename.txt
  --stop filename        : Repy will watch for the creation of this file and abort when it happens
  --status filename.txt  : Write status information into this file
  --cwd dir              : Set Current working directory
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

import repy_constants   

import os

## we'll use tracebackrepy to print our exceptions
import tracebackrepy

# This block allows or denies different actions in the safe module.   I'm 
# doing this here rather than the natural place in the safe module because
# I want to keep that module unmodified to make upgrading easier.

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

# These are the functions and variables in the user's name space (along with 
# the builtins allowed by the safe module).   
usercontext = {
    'mycontext':{},                     # set up a place for them to store state
    'open':emulfile.emulated_open,      # emulated open function
    'file':emulfile.emulated_file,      # emulated file object
    'listdir':emulfile.listdir,         # List the files in the expts dir
    'removefile':emulfile.removefile,   # remove a file in the expts dir
    'getmyip':emulcomm.getmyip,         # provides an external IP
    'gethostbyname_ex':emulcomm.gethostbyname_ex, # same as socket method
    'recvmess':emulcomm.recvmess,       # message receive (UDP)
    'sendmess':emulcomm.sendmess,       # message sending (UDP)
    'openconn':emulcomm.openconn,       # reliable comm channel (TCP)
    'waitforconn':emulcomm.waitforconn, # reliable comm listen (TCP)
    'stopcomm':emulcomm.stopcomm,       # stop receiving (TDP/UDP)
    'settimer':emultimer.settimer,      # sets a timer
    'canceltimer':emultimer.canceltimer,# stops a timer if it hasn't fired
    'sleep':emultimer.sleep,            # blocks the thread for some time
    'randomfloat':emulmisc.randomfloat, # same as random.random()
    'getruntime':emulmisc.getruntime,   # amount of time the program has run
    'getlock':emulmisc.getlock,         # acquire a lock object
    'exitall':emulmisc.exitall          # Stops executing the sandboxed program
}


# There is a "simple execution" mode where there is a single entry into the
# code.   This is used only for testing python vs repy in the unit tests
# The simpleexec variable indicates whether or not simple execution mode should
# be used...
#simpleexec = None


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


  # grab the user code from the file
  usercode = file(program).read()

  # In order to work well with files that may contain a mix of \r\n and \n
  # characters (see ticket #32), I'm going to replace all \r\n with \n
  usercode = usercode.replace('\r\n','\n')

  # If we are in "simple execution" mode, execute and exit
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


  # Once there are no more pending events for the user thread, we give them
  # an "exit" event.   This allows them to clean up, etc. if needed.

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


def usage(str_err=""):
  # Ivan 12/24/2008
  """
   <Purpose>
      Prints repy.py usage and possibly an error supplied argument
   <Arguments>
      str_err (string):
        Options error to print to stdout
   <Exceptions>
      None
   <Side Effects>
      Modifies stdout
   <Returns>
      None
  """
  print
  if str_err:
    print "Error:", str_err
  print """
Usage: repy.py [options] restrictionsfile.txt program_to_run.py [program args]

Where [options] are some combination of the following:

--simple               : Simple execution mode -- execute and exit
--ip IP                : IP address that repy should use (default: allow any)
--logfile filename.txt : Set up a circular log buffer and output to logfilename.txt
--stop filename        : Repy will watch for the creation of this file and abort when it happens
--status filename.txt  : Write status information into this file
--cwd dir              : Set Current working directory
"""
  return


if __name__ == '__main__':
  global simpleexec
  global logfile

  # Set up the simple variable if needed
  args = sys.argv[1:]
  simpleexec = False


  if len(args) < 2:
    usage("Must supply a restrictions file and a program file to execute")
    sys.exit(1)
  
  try:
    if sys.argv[1] == '--simple':
      simpleexec = True
      args = sys.argv[2:]

    if args[0] == '--ip':
      # Allow the program to use only this IP
      emulcomm.specificIP = args[1]
      args = args[2:]

    if args[0] == '--logfile':
      # set up the circular log buffer...
      logfile = args[1]
      args = args[2:]

    else:
      # use standard streams (stdout / stderr)
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
      
    # Armon: Set Current Working Directory
    if args[0] == '--cwd':
      # Move
      os.chdir(args[1])
      args = args[2:]
    
    # Update repy current directory
    repy_constants.REPY_CURRENT_DIR = os.path.abspath(os.getcwd())

  except IndexError:
    usage("Option usage error")
    sys.exit(1)

  if len(args) < 2:
    usage("Must supply a restrictions file and a program file to execute")
    sys.exit(1)

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
