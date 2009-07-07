"""

Author: Armon Dadgar
Start Date: April 16th, 2009
Description:
  Houses code which is common between the Linux, Darwin, and FreeBSD API's to avoid redundancy.

"""

import subprocess

def exists_outgoing_network_socket(localip, localport, remoteip, remoteport):
  """
  <Purpose>
    Determines if there exists a network socket with the specified unique tuple.
    Assumes TCP.

  <Arguments>
    localip: The IP address of the local socket
    localport: The port of the local socket
    remoteip:  The IP of the remote host
    remoteport: The port of the remote host
    
  <Returns>
    A Tuple, indicating the existence and state of the socket. E.g. (Exists (True/False), State (String or None))

  """
  # This only works if all are not of the None type
  if not (localip and localport and remoteip and remoteport):
    return (False, None)
  
  # Escape the characters, so that they aren't treated as special regex
  localip = localip.replace(".","\.")
  localip = localip.replace("*",".*")
  remoteip = remoteip.replace(".","\.")
  remoteip = remoteip.replace("*",".*")  

  # Construct the command
  netstat_process = subprocess.Popen(["netstat", "-an"], stdout=subprocess.PIPE, close_fds=True)
  grep_process1 = subprocess.Popen(['grep', '-e', localip + '[:\.]' + str(localport) + '[ \\t]*' + remoteip + \
      '[:\.]' + str(remoteport) + '[ \\t]'], stdin=netstat_process.stdout, stdout=subprocess.PIPE, close_fds=True)
  grep_process2 = subprocess.Popen(['grep', '-i', 'tcp'], stdin=grep_process1.stdout, stdout=subprocess.PIPE, close_fds=True)
  
  # Launch up a shell, get the feed back
  
  # Get the output
  entries = grep_process2.stdout.readlines()
  
  # Close the pipe
  grep_process2.stdout.close()
 
  # Check if there is any entries
  if len(entries) > 0:
    line = entries[0]
    # Replace tabs with spaces, explode on spaces
    parts = line.replace("\t","").strip("\n").split()
    # Get the state
    socket_state = parts[-1]
      
    return (True, socket_state)

  else:
    return (False, None)




def exists_listening_network_socket(ip, port, tcp):
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
    grep_terms = ["tcp", "LISTEN"]
  else:
    grep_terms = ["udp"]
  
  # Launch up a shell, get the feedback
  netstat_process = subprocess.Popen(["netstat", "-an"], stdout=subprocess.PIPE, close_fds=True)
  grep_process1 = subprocess.Popen(["grep", "-e", ip+'[:\.]'+str(port)+'[ \\t]'], stdin=netstat_process.stdout, stdout=subprocess.PIPE, close_fds=True)
  prev_process = grep_process1
  for term in grep_terms:
    # Daisy-chain grep processes
    cur_process = subprocess.Popen(["grep", "-i", term], stdin=prev_process.stdout, stdout=subprocess.PIPE, close_fds=True)
    prev_process = cur_process

  wc_process = subprocess.Popen(["wc", "-l"], stdin=prev_process.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)

  # JAC: To fix the wc error messages mentioned in #402, we need to discard
  # stderr.   I don't think we can do anything smarter because our process may
  # have died at that point.
  wc_process.stderr.read()
  wc_process.stderr.close()
  
  # Get the output
  number_of_sockets = wc_process.stdout.read()
  
  # Close the pipe
  wc_process.stdout.close()
  
  # Convert to an integer
  number_of_sockets = int(number_of_sockets)
  
  return (number_of_sockets > 0)


def get_available_interfaces():
  """
  <Purpose>
    Returns a list of available network interfaces.
  
  <Returns>
    An array of string interfaces
  """
  # Common headers
  # This list contains common header elements so that they can be stripped
  common_headers_list = ["Name", "Kernel", "Iface"]
  
  # Netstat will return all interfaces, but also has some duplication.
  # Cut will get the first field from each line, which is the interface name.
  # Sort prepares the input for uniq, which only works on sorted lists.
  # Uniq, is somewhat obvious, it will only return the unique interfaces to remove duplicates.
  # Launch up a shell, get the feedback
  netstat_process = subprocess.Popen(["netstat", "-i"], stdout=subprocess.PIPE, close_fds=True)
  cut_process = subprocess.Popen(["cut", "-d ", "-f1"], stdin=netstat_process.stdout, stdout=subprocess.PIPE, close_fds=True)
  sort_process = subprocess.Popen(["sort"], stdin=cut_process.stdout, stdout=subprocess.PIPE, close_fds=True)
  uniq_process = subprocess.Popen(["uniq"], stdin=sort_process.stdout, stdout=subprocess.PIPE, close_fds=True)

  # Get the output
  output_array = uniq_process.stdout.readlines()
  
  # Close the pipe
  uniq_process.stdout.close()
  
  # Create an array for the interfaces
  interfaces_list = []
  
  for line in output_array:
    # Strip the newline
    line = line.strip("\n")
    # Check if this is a header
    if line in common_headers_list:
      continue
    interfaces_list.append(line)
  
  # Done, return the interfaces
  return interfaces_list


def get_interface_ip_addresses(interfaceName):
  """
  <Purpose>
    Returns the IP address associated with the interface.
  
  <Arguments>
    interfaceName: The string name of the interface, e.g. eth0
  
  <Returns>
    A list of IP addresses associated with the interface.
  """

  # Launch up a shell, get the feed back
  # We use ifconfig with the interface name.
  ifconfig_process = subprocess.Popen(["/sbin/ifconfig", interfaceName.strip()], stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
  # Simple grep to reduce to lines that include inet
  grep_process = subprocess.Popen(["grep", "inet"], stdin=ifconfig_process.stdout, stdout=subprocess.PIPE, close_fds=True)
  # This complicated sed expression extracts the first IPv4 address on the line, and ignores everything else
  sed_process = subprocess.Popen(["sed", "-n", "-e", "s|\\([a-zA-Z ^I]*[a-zA-Z][ ^I:]\\)\\([0-9]\\{1,3\\}[\\.][0-9]\\{1,3\\}[\\.][0-9]\\{1,3\}[\\.][0-9]\\{1,3\\}\\)\\{1,\\}.*|\\2|p"], \
      stdin=grep_process.stdout, stdout=subprocess.PIPE, close_fds=True)

  # Ignore stderr from ifconfig.
  ifconfig_process.stderr.read()
  ifconfig_process.stderr.close()

  # Get the output
  output_array = sed_process.stdout.readlines()
  
  # Close the pipe
  sed_process.stdout.close()
  
  # Create an array for the ip's
  ipaddressList = []
  
  for line in output_array:
     # Strip the newline and any spacing
     line = line.strip("\n\t ")
     ipaddressList.append(line)

  # Done, return the interfaces
  return ipaddressList
