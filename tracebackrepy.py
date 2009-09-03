""" 
Author: Justin Cappos

Start Date: September 17th, 2008

Description:
Module for printing clean tracebacks.   It takes the python traceback and 
makes the output look nicer so the programmer can tell what is happening...

"""


# we'll print our own exceptions
import traceback
# This needs hasattr.   I'll allow it...
traceback.hasattr = hasattr

# and don't want traceback to use linecache because linecache uses open
import fakelinecache
traceback.linecache = fakelinecache

# Need to be able to reference the last traceback...
import sys

userfilename = None

# Used to determine whether or not we use the service logger to log internal
# errors.  Defaults to false. -Brent
servicelog = False

# this is the directory where the node manager resides.   We will use this
# when deciding where to write our service log.
logdirectory = None


# We need the service logger to log internal errors -Brent
import servicelogger

# We need to be able to do a harshexit on internal errors
import harshexit

# I'd like to know if it's a "safety concern" so I can tell the user...
# I'll import the module so I can check the exceptions
import safe

# needed to get the PID
import os


# sets the user's file name.
# also sets whether or not the servicelogger is used. -Brent
def initialize(ufn, useservlog=False, logdir = '.'):
  global userfilename
  global servicelog
  global logdirectory
  userfilename = ufn
  servicelog = useservlog
  logdirectory = logdir


# Public: this prints the previous exception in a readable way...
def handle_exception():
  print >> sys.stderr, "Seattle Traceback (most recent call last):"

  # exc_info() gives the traceback (see the traceback module for info)
  exceptiontype, exceptionvalue, exceptiontraceback = sys.exc_info()

  for tracebackentry in traceback.extract_tb(exceptiontraceback):
    # the entry format is (filename, lineno, modulename, linedata)
    # linedata is always empty because we prevent the linecache from working
    # for safety reasons...
    #
    # The user code is read in and passed to the parser by us.   As a result, 
    # is seen by python as filename = '<string>'.   We only want to display
    # information about the user program, so we'll fix this up.
    if tracebackentry[0] == "<string>":
      if userfilename:
        # mimic python's output
        print >> sys.stderr, '  "'+userfilename+'", line '+str(tracebackentry[1])+", in "+str(tracebackentry[2])
      else:
        print >> sys.stderr, '  "'+tracebackentry[0]+'", line '+str(tracebackentry[1])+", in "+str(tracebackentry[2])


  # When I try to print an Exception object, I get:
  # "<type 'exceptions.Exception'>".   I'm going to look for this and produce
  # more sensible output if it happens.

  if exceptiontype == safe.CheckNodeException:
    print >> sys.stderr, "Unsafe call with line number / type:",str(exceptionvalue)

  elif exceptiontype == safe.CheckStrException:
    print >> sys.stderr, "Unsafe string on line number / string:",exceptionvalue

  elif exceptiontype == safe.RunBuiltinException:
    print >> sys.stderr, "Unsafe call:",exceptionvalue

  elif str(exceptiontype)[0] == '<':
    print >> sys.stderr, "Exception (with "+str(exceptiontype)[1:-1]+"):", exceptionvalue
  else:
    print >> sys.stderr, "Exception (with type "+str(exceptiontype)+"):", exceptionvalue




def handle_internalerror(error_string, exitcode):
  """
  <Author>
    Brent Couvrette
  <Purpose>
    When an internal error happens in repy it should be handled differently 
    than normal exceptions, because internal errors could possibly lead to
    security vulnerabilities if we aren't careful.  Therefore when an internal
    error occurs, we will not return control to the user's program.  Instead
    we will log the error to the service log if available, then terminate.
  <Arguments>
    error_string - The error string to be logged if logging is enabled.
    exitcode - The exit code to be used in the harshexit call.
  <Exceptions>
    None
  <Side Effects>
    The program will exit.
  <Return>
    Shouldn't return because harshexit will always be called.
  """

  try:
    print >> sys.stderr, "Internal Error"
    if not servicelog:
      # If the service log is disabled, lets just exit.
      harshexit.harshexit(exitcode)
    else:
      # Internal errors should not be given to the user's code to be caught,
      # so we print the exception to the service log and exit. -Brent
      exceptionstring = "[INTERNAL ERROR] " + error_string + '\n'
      for line in traceback.format_stack():
        exceptionstring = exceptionstring + line
  
      # This magic is determining what directory we are in, so that can be
      # used as an identifier in the log.  In a standard deployment this
      # should be of the form vXX where XX is the vessel number.  We don't
      # want any exceptions here preventing us from exitting, so we will
      # wrap this in a try-except block, and use a default value if we fail.
      try:
        identifier = os.path.basename(os.getcwd())
      except:
        # We use a blank except because if we don't, the user might be able to
        # handle the exception, which is unacceptable on internal errors.  Using
        # the current pid should avoid any attempts to write to the same file at
        # the same time.
        identifier = str(os.getpid())
      else:
        if identifier == '':
          # If the identifier is blank, use the PID.
          identifier = str(os.getpid())
    
      # Again we want to ensure that even if we fail to log, we still exit.
      try:
        servicelogger.multi_process_log(exceptionstring, identifier, logdirectory)
      except Exception, e:
        # if an exception occurs, log it (unfortunately, to the user's log)
        print 'Inner abort of servicelogger'
        print e,type(e)
        traceback.print_exc()
      finally:
        harshexit.harshexit(exitcode)

  except Exception, e:
    # if an exception occurs, log it (unfortunately, to the user's log)
    print 'Outer abort of servicelogger'
    print e,type(e)
    traceback.print_exc()
  finally:
    harshexit.harshexit(842)
