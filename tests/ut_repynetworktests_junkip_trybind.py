# This test only has the
# --ip 256.256.256.256 flag, and we want try to bind to something random "128.0.1.5"  to be sure waitforconn and recvmess fail


import subprocess
import sys

process = subprocess.Popen([sys.executable, 'repy.py', '--ip', '256.256.256.256', 'restrictions.default', 'ip_junkip_trybind.py'])
process.wait()
