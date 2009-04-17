"""

Author: Armon Dadgar
Start Date: April 16th, 2009
Description:
  Houses code which is common between the Linux, Darwin, and FreeBSD API's to avoid redundancy.

"""

import subprocess

def existsListeningNetworkSocket(ip, port, tcp):
  """
  <Purpose>
    Determines if there exists a network socket with the specified ip and port which is the LISTEN state.
  
  <Arguments>
    ip: The IP address of the listening socket
    port: The port of the listening socket
    tcp: Is the socket of TCP type, else UDP
    
  <Returns>
    True or False.
  """
  # This only works if both are not of the None type
  if not (ip and port):
    return False
  
  # Escape the characters, so that they aren't treated as special regex
  ip = ip.replace(".","\.")
  ip = ip.replace("*",".*")
  
  # UDP connections are stateless, so for TCP check for the LISTEN state
  # and for UDP, just check that there exists a UDP port
  if tcp:
    grep = ["tcp", "LISTEN"]
  else:
    grep = ["udp"]
  
  # Construct the command
  cmd = 'netstat -an |grep -e "'+ip+'[:\.]'+str(port)+'[ \\t]" |' # Basic netstat with preliminary grep
  for term in grep:   # Add additional grep's
    cmd +=  'grep -i '+term+' |'
  cmd += "wc -l"  # Count up the lines

  # Launch up a shell, get the feed back
  process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, close_fds=True)
  
  # Get the output
  num = process.stdout.read()
  
  # Close the pipe
  process.stdout.close()
  
  # Convert to an integer
  num = int(num)
  
  return (num > 0)

