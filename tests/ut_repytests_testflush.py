import subprocess
import time

processOne = subprocess.Popen(['python', 'repy.py', '--simple', 'restrictions.default', 's_testflush.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(stdoutFirst, stderrFirst) = processOne.communicate()
processOne.wait()
processTwo = subprocess.Popen(['python', 's_testflush.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(stdoutSecond, stderrSecond) = processTwo.communicate()
processTwo.wait()

if stderrFirst != stderrSecond or stdoutFirst != stdoutSecond:
  raise Exception