# This test only has the
# --iface lo flag, and we want to be sure getmyip returns an IP that is loopback
# and that we are allowed to bind to it

import subprocess
import sys

process = subprocess.Popen([sys.executable, 'repy.py', '--iface', 'lo', 'restrictions.default', 'ip_nopreferred_noallowed_checkgetmyip.py'])
process.wait()
