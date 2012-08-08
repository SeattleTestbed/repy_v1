import subprocess
import time
import sys
import utf

processOne = subprocess.Popen([sys.executable, 'repy.py', '--simple', 'restrictions.default', 's_testfileinit.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(rawstdoutFirst, stderrFirst) = processOne.communicate()
processOne.wait()
processTwo = subprocess.Popen([sys.executable, 's_testfileinit.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(rawstdoutSecond, stderrSecond) = processTwo.communicate()
processTwo.wait()

stdoutFirst = utf.strip_android_debug_messages(rawstdoutFirst)
stdoutSecond = utf.strip_android_debug_messages(rawstdoutSecond)

if stderrFirst != stderrSecond or stdoutFirst != stdoutSecond:
  raise Exception
