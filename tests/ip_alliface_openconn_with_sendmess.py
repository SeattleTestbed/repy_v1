# This test only has the
# --iface any flag, and we want to be sure getmyip returns an IP that is not loopback
# and that we are allowed to bind to it
# We then attempt to use openconn and sendmess with no localip specified to make sure
# auto resolve works

def noop(ip,port,mess,ch):
  sleep(30)
  
def noop1(ip,port,mess,ch, ch1):
  sleep(30)

if callfunc == 'initialize':
  ip = getmyip()
  if ip == "127.0.0.1":
    print "Got unexpected IP:"+ip+" Expected real IP address!"
  
  handle = recvmess(ip,12345,noop)
  sendmess(ip,12345,"Hi There!")
  sleep(2)
  stopcomm(handle)
  
  handle = waitforconn(ip,12345,noop1)
  socket = openconn(ip, 12345)
  sleep(2)
  socket.close()
  
  exitall()
