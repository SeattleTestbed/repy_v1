
#pragma repy restrictions.fastestnetsendfullcpu

myip = getmyip()

mycontext['maxlag'] = 0

def sendforever(sockobj):
  while True:
    # send a message that is around 100 bytes
    sockobj.send("%9f "%getruntime() + " "*90)

def handleconnection(ip, port, connobj, ch, mainch):
  while True:
    sendtime = float(connobj.recv(100).strip().split()[0])
    lag = getruntime() - sendtime

    if mycontext['maxlag'] < lag:
      mycontext['maxlag'] = lag

  


def check_and_exit():
  if mycontext['maxlag'] > 2:
    print "TCP packets lag too long in the buffer: ", mycontext['maxlag']

  if mycontext['maxlag'] == 0:
    print "TCP packets were not received or had 0 lag"

  exitall()
  

if callfunc == 'initialize':
  waitforconn(myip, <connport>, handleconnection)
  clientsockobj = openconn(myip, <connport>, )
  settimer(10.0, check_and_exit, ())
  sendforever(clientsockobj)

