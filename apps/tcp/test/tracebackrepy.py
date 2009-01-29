""" 
Author: Justin Cappos

Start Date: September 17th, 2008

Description:
Module for printing clean tracebacks.   It takes the python traceback and 
makes the output look nicer so the programmer can tell what is happening...

"""


# we'll print our own exceptions
import traceback
# and don't want traceback to use linecache because linecache uses open
import fakelinecache
traceback.linecache = fakelinecache

# Need to be able to reference the last traceback...
import sys

userfilename = None


# I'd like to know if it's a "safety concern" so I can tell the user...
# I'll import the module so I can check the exceptions
import safe


# sets the user's file name
def initialize(ufn):
  global userfilename
  userfilename = ufn

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



