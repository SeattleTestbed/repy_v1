# send a probe message to each neighbor
def probe_neighbors(port):

  for neighborip in mycontext["neighborlist"]:
    mycontext['sendtime'][neighborip] = getruntime()
    sendmess(neighborip, port, 'ping',getmyip(),port)

    sendmess(neighborip, port,'share'+encode_row(getmyip(), mycontext["neighborlist"], mycontext['latency'].copy()))
  # Call me again in 10 seconds
  settimer(10,probe_neighbors,(port,))
  


# Handle an incoming message
def got_message(srcip,srcport,mess,ch):
  if mess == 'ping':
    sendmess(srcip,srcport,'pong')
  elif mess == 'pong':
    # elapsed time is now - time when I sent the ping
    mycontext['latency'][srcip] = getruntime() - mycontext['sendtime'][srcip]

  elif mess.startswith('share'):
    mycontext['row'][srcip] = mess[len('share'):]



def encode_row(rowip, neighborlist, latencylist):

  retstring = "<tr><td>"+rowip+"</td>"
  for neighborip in neighborlist:
    if neighborip in latencylist:
      retstring = retstring + "<td>"+str(latencylist[neighborip])+"</td>"
    else:
      retstring = retstring + "<td>Unknown</td>"

  retstring = retstring + "</tr>"
  return retstring


# Displays a web page with the latency information
def show_status(srcip,srcport,connobj, ch, mainch): 

  # I'm going to write a HTML header first...
  connobj.send("<html><head><title>Latency Information</title></head><body><h1>Latency information from "+getmyip()+' </h1><table border="1">')

  connobj.send("<tr><td></td><td>"+ "</td><td>".join(mycontext['neighborlist'])+"</td></tr>")

  # copy to prevent a race
#  connobj.send(encode_row(getmyip(), mycontext['neighborlist'], mycontext['latency'].copy()))

  for nodeip in mycontext['neighborlist']:
    if nodeip in mycontext['row']:
      connobj.send(mycontext['row'][nodeip])
    else:
      connobj.send('<tr><td>'+nodeip+'</td><td>No Data Reported</td></tr>')

  # now the footer...
  connobj.send("</table></html>")

  # and we're done, so let's close this connection...
  connobj.close()



if callfunc == 'initialize':

  # this holds the response information (i.e. when nodes responded)
  mycontext['latency'] = {}

  # this remembers when we sent a probe
  mycontext['sendtime'] = {}

  # this remembers row data from the other nodes
  mycontext['row'] = {}
  
  # get the nodes to probe
  mycontext['neighborlist'] = []
  for line in file("neighboriplist.txt"):
    mycontext['neighborlist'].append(line.strip())

  ip = getmyip() 
  pingport = int(callargs[0])

  # call gotmessage whenever receiving a message
  recvmess(ip,pingport,got_message)  

  probe_neighbors(pingport)

  # we want to register a function to show a status webpage
  pageport = int(callargs[1])
  waitforconn(ip,pageport,show_status)  

