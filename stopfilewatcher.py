"""
   Author: Justin Cappos

   Start Date: 7 July 2008

   Description:
  
   Checks for the existance of a file and exits if it exists...
   An attempt is made to parse the file for a string of the format
   "EINT;MESG" where EINT is a string representation of an integer that is
   passed to nonportable.harshexit and MESG is a string to be printed prior
   to exiting. On any error, no message is printed and repy is exited with code 44 "Stopped"
"""

import threading

import time    # for sleep

import os      # for path.exists

import nonportable     # for harshexit


#frequency to check
frequency = 0.5

# This is so that we can open the stopfiel
myopen = open

def init(stopfn):
  if os.path.exists(stopfn):
    raise Exception, "Stop file: '"+stopfn+"' exists!"

  tobj = threading.Timer(frequency,checkfunction,[stopfn])

  # start the timer
  tobj.start()
  

def checkfunction(stopfn):
  # run forever
  while True:
    if os.path.exists(stopfn):
      try:
        # Get a file object for the file
        fileobject = myopen(stopfn)

        # Read in the contents, close the object
        contents = fileobject.read()
        fileobject.close()
          
        # Check the length, if there is nothing then just close as stopped
        if len(contents) > 0:
          # Split, at most we have 2 parts, the exit code and message
          (exitcode, mesg) = contents.split(";",1)
          exitcode = int(exitcode)
          
          # Check if exitcode is 56, which stands for ThreadErr is specified
          # ThreadErr cannot be specified externally, since it has side-affects
          # such as changing global thread restrictions
          if exitcode == 56:
            raise Exception, "ThreadErr exit code specified. Exit code not allowed."
          
          # Print the message, then call harshexit with the exitcode
          if mesg != "": 
            print mesg
          nonportable.harshexit(exitcode)
          
        else:
          raise Exception, "Stopfile has no content."
          
      except:
        # On any issue, just do stopped
        nonportable.harshexit(44)
      
    time.sleep(frequency)
