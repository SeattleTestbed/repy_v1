"""
   Author: Justin Cappos

   Start Date: 7 July 2008

   Description:
  
   Checks for the existance of a file and exits if it exists...
"""

import threading

import time    # for sleep

import os      # for path.exists

import nonportable     # for harshexit


#frequency to check
frequency = 1.0


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
#      print "Stop file: '"+stopfn+"' exists!"
      nonportable.harshexit(44)
    time.sleep(frequency)
