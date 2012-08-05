# This test only has the
# --ip 127.0.0.1 flag, and we want to be sure getmyip returns 127.0.0.1,
# and that we are allowed to bind to it

import subprocess
import sys

process = subprocess.Popen([sys.executable, 'repy.py', '--ip', '127.0.0.1', 'restrictions.default', 'ip_onlyloopback_checkgetmyip.py'])
process.wait()
