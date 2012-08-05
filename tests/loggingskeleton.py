"""
<Program>
  Skeleton for the repy logging tests

<Author>
  Justin Cappos

<Edits>
  Stephen Sievers

<Purpose and Use>
  This module is meant for running the repy logging tests with utf.py
  This is a modified subset of the old run_tests.py testing framework
  which was used for the old logging tests. It has been adapted for
  usage with the new framework.

  Logging tests should import this module and use the test() method
"""

import os
import sys

# Used to spawn subprocesses for tests. Fails on
# WindowsCE so we use WindowsAPI instead
try:
  import subprocess
  mobileNoSubprocess = False
except ImportError:
  # Set flag to avoid using subprocess
  mobileNoSubprocess = True 

  # import windows API
  import windows_api as windowsAPI
  pass


# filename, restrictionsfile, arguments={}, script_args=''

def test(testname, restrictionsfile="restrictions.default"):
  endput = ''
  
  # remove any existing log
  try:
    os.remove("experiment.log.old")
    os.remove("experiment.log.new")
  except OSError:
    pass
    
  # run the experiment
  if not mobileNoSubprocess:
    process = subprocess.Popen([sys.executable, 'repy.py', restrictionsfile, testname, '--logfile', 'experiment.log', '--status', 'foo'], 
                                    stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    # (testout, testerr) = exec_repy_script(testname, restrictionfn, {'logfile':'experiment.log', 'status':'foo'})
  else:
    process = subprocess.Popen([sys.executable, 'repy.py', restrictionsfile, testname, '--status', 'foo'], 
                                    stderr=subprocess.PIPE, stdout=subprocess.PIPE)  
  
    # (testout, testerr) = exec_repy_script(testname, restrictionfn, {'status':'foo'})
  (testout, testerr) = process.communicate() 
    
  capture_test_result(testname, testout, testerr, ".repy")
  # first, check to make sure there was no output or error
  if mobileNoSubprocess or (testout == '' and testerr == ''):
    if not mobileNoSubprocess:
      try:
        myfo = file("experiment.log.old","r")
        logdata = myfo.read()
        myfo.close()
        if os.path.exists("experiment.log.new"):
          myfo = file("experiment.log.new","r")
          logdata = logdata + myfo.read()
          myfo.close()
         # use only the last 16KB
        logdata = logdata[-16*1024:]
      except:
        endput = endput+testname+"\nCan't read log!\n\n"
        return False
    else:
      logdata = testout
      
    if "Fail" in logdata:
      endput = endput+testname+"\nString 'Fail' in logdata\n\n"
      return False
      
    # Armon: Use this to test that logging from the external process is working   
    elif "kill" in logdata:
      return True
      
    elif "Success" not in logdata:
      endput = endput+testname+"\nString 'Success' or 'kill' not in logdata\n\n"
      return False 
    else:
      return True
  else:
    endput = endput+testname+"\nHad output or errput! out:"+testout+"err:"+ testerr+"\n\n"
    return False
    
# Captures the output of a test and puts it into the log file
def capture_test_result(testname, pyout, pyerr, additionalExt=""):
  global captureOutput
  global captureDir
  
  # Ignore if we're not capturing output
  if not captureOutput:
    return None
    
  current_dir = os.getcwd()
  
  # Change to directory and write file
  os.chdir(captureDir)
  fileh = file(testname + additionalExt + ".out", "w")
  fileh.write(pyout)
  fileh.close()
  
  fileh = file(testname + additionalExt + ".err", "w")
  fileh.write(pyerr)
  fileh.close()
  
  # Pop back to test directory
  os.chdir(current_dir)
  
# If boolean is true, then unit test output will be
# captured and stored
captureOutput = False
captureDir = None
if len(sys.argv) > 1 and sys.argv[1] == '-ce':
  captureOutput = True
  captureDir = sys.argv[2]
  sys.argv = sys.argv[2:]
  setup_test_capture()
