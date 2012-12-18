import sys
import subprocess

# Test without execinfo.  We should only have the program's output.
proc = subprocess.Popen([sys.executable, 'repy.py', 'restrictions.test', 'print_helloworld.repy'], stdout = subprocess.PIPE, stderr = subprocess.PIPE, stdin = subprocess.PIPE)
stdout, stderr = proc.communicate()

# Windows prints out \r\n instead of \n
stdout = stdout.replace('\r\n', '\n')

expected_out = \
'''hello world
'''

if stdout != expected_out:
  print "Unexpected output:"
  print stdout

if stderr:
  print "Unexpected error output:"
  print stderr


# Test with execinfo.  We should see the execinfo string first, then the
# program's output.
proc = subprocess.Popen([sys.executable, 'repy.py', '--execinfo', 'restrictions.test', 'print_helloworld.repy'], stdout = subprocess.PIPE, stderr = subprocess.PIPE, stdin = subprocess.PIPE)
stdout, stderr = proc.communicate()

# Windows prints out \r\n instead of \n
stdout = stdout.replace('\r\n', '\n')

expected_out = \
'''========================================
Running program: print_helloworld.repy
Arguments: []
========================================
hello world
'''

if stdout != expected_out:
  print "Unexpected output:"
  print stdout

if stderr:
  print "Unexpected error output:"
  print stderr
