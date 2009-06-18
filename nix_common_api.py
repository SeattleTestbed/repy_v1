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
  cmdstr = 'netstat -an |grep -e "'+localip+'[:\.]'+str(localport)+'[ \\t]*'+remoteip+'[:\.]'+str(remoteport)+'[ \\t]"|grep -i tcp'
  
  # Launch up a shell, get the feed back
  process_obj = subprocess.Popen(cmdstr, stdout=subprocess.PIPE, shell=True, close_fds=True)
  
  # Get the output
  entries = process_obj.stdout.readlines()
  
  # Close the pipe
  process_obj.stdout.close()
 
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
  
  # Construct the command
  cmdstr = 'netstat -an |grep -e "'+ip+'[:\.]'+str(port)+'[ \\t]" |' # Basic netstat with preliminary grep
  for term in grep_terms:   # Add additional grep's
    cmdstr +=  'grep -i '+term+' |'
  # Count up the lines.   
  # JAC: To fix the wc error messages mentioned in #402, we need to discard
  # stderr.   I don't think we can do anything smarter because our process may
  # have died at that point.
  cmdstr += "wc -l 2> /dev/null"  
       


  # Launch up a shell, get the feed back
  process_obj = subprocess.Popen(cmdstr, stdout=subprocess.PIPE, shell=True, close_fds=True)
  
  # Get the output
  number_of_sockets = process_obj.stdout.read()
  
  # Close the pipe
  process_obj.stdout.close()
  
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
  
  # Netstat will return all interfaces, but also has some duplication
  # Sed will filter the output to only return the interface names
  # Uniq, is somewhat obvious, it will only return the unique interfaces to remove duplicates
  cmdstring = "netstat -i | sed -e 's/^\\([a-zA-Z0-9]\\{1,\\}\\)\\([ ^I]*\\)\\(.*\\)$/\\1/' | uniq"

  # Launch up a shell, get the feed back
  process_obj = subprocess.Popen(cmdstring, stdout=subprocess.PIPE, shell=True, close_fds=True)

  # Get the output
  output_array = process_obj.stdout.readlines()
  
  # Close the pipe
  process_obj.stdout.close()
  
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
  # We use ifconfig with the interface name, redirect errors to null so as not to mess us up
  cmdstring = "/sbin/ifconfig "+interfaceName.strip()+" 2>/dev/null "
  cmdstring += "| grep inet " # Simple grep to reduce to lines that include inet
  # This complicated sed expression extracts the first IP address on the line, and ignores everything else
  cmdstring += "| sed -n -e 's|\\([a-zA-Z ^I]*[a-zA-Z][ ^I:]\\)\\([0-9]\\{1,3\\}[\\.][0-9]\\{1,3\\}[\\.][0-9]\\{1,3\}[\\.][0-9]\\{1,3\\}\\)\\{1,\\}.*|\\2|p'"

  # Launch up a shell, get the feed back
  process_obj = subprocess.Popen(cmdstring, stdout=subprocess.PIPE, shell=True, close_fds=True)

  # Get the output
  output_array = process_obj.stdout.readlines()
  
  # Close the pipe
  process_obj.stdout.close()
  
  # Create an array for the ip's
  ipaddressList = []
  
  for line in output_array:
     # Strip the newline and any spacing
     line = line.strip("\n\t ")
     ipaddressList.append(line)

  # Done, return the interfaces
  return ipaddressList

