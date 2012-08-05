# This test only has many iface flags with common interfaces to try to get one
# with a real IP that we are allowed to bind to it


import subprocess

import sys

process = subprocess.Popen([sys.executable, 'repy.py', '--iface', 'eth0', '--iface', 'eth1', '--iface', 'en0', '--iface', 'en1', '--iface', 'xl0', '--iface', 'xl1', '--iface', '"Ethernet adapter Local Area Connection"', '--iface', '"Ethernet adapter Local Area Connection 2"', '--nootherips', 'restrictions.default', 'ip_multiple_iface_trybind.py'])
process.wait()
