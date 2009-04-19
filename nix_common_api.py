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


def getAvailableInterfaces():
  """
  <Purpose>
    Returns a list of available network interfaces.
  
  <Returns>
    An array of string interfaces
  """
  # Common headers
  # This list contains common header elements so that they can be stripped
  headers = ["Name", "Kernel", "Iface"]
  
  # Netstat will return all interfaces, but also has some duplication
  # Sed will filter the output to only return the interface names
  # Uniq, is somewhat obvious, it will only return the unique interfaces to remove duplicates
  cmd = "netstat -i | sed -e 's/^\\([a-zA-Z0-9]\\{1,\\}\\)\\([ ^I]*\\)\\(.*\\)$/\\1/' | uniq"

  # Launch up a shell, get the feed back
  process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, close_fds=True)

  # Get the output
  output = process.stdout.readlines()
  
  # Close the pipe
  process.stdout.close()
  
  # Create an array for the interfaces
  interfaces = []
  
  for line in output:
    # Strip the newline
    line = line.strip("\n")
    # Check if this is a header
    if line in headers:
      continue
    interfaces.append(line)
  
  # Done, return the interfaces
  return interfaces


def getInterfaceIPAddresses(interfaceName):
  """
  <Purpose>
    Returns the IP address associated with the interface.
  
  <Arguments>
    interfaceName: The string name of the interface, e.g. eth0
  
  <Returns>
    A list of IP addresses associated with the interface.
  """
  # We use ifconfig with the interface name, redirect errors to null so as not to mess us up
  cmd = "/sbin/ifconfig "+interfaceName.strip()+" 2>/dev/null "
  cmd += "| grep inet " # Simple grep to reduce to lines that include inet
  # This complicated sed expression extracts the first IP address on the line, and ignores everything else
  cmd += "| sed -n -e 's|\\([a-zA-Z ^I]*[a-zA-Z][ ^I:]\\)\\([0-9]\\{1,3\\}[\\.][0-9]\\{1,3\\}[\\.][0-9]\\{1,3\}[\\.][0-9]\\{1,3\\}\\)\\{1,\\}.*|\\2|p'"

  # Launch up a shell, get the feed back
  process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, close_fds=True)

  # Get the output
  output = process.stdout.readlines()
  
  # Close the pipe
  process.stdout.close()
  
  # Create an array for the ip's
  ipaddrs = []
  
  for line in output:
     # Strip the newline and any spacing
     line = line.strip("\n\t ")
     ipaddrs.append(line)

  # Done, return the interfaces
  return ipaddrs

