# This test only has the
# --ip 256.256.256.256 flag, and we want to be sure getmyip doesn't returns this IP
# we should get the loopback IP

import subprocess

process = subprocess.Popen(['python', 'repy.py', '--ip', '256.256.256.256', 'restrictions.default', 'ip_junkip_checkgetmyip.py'])
process.wait()