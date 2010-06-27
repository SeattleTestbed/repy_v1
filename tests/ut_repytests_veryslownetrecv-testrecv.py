#pragma repy restrictions.veryslownetrecv

def foo(ip,port,sock, mainch, ch):
  data = sock.recv(1000)
  print ip,port,data
  stopcomm(ch)
  stopcomm(mainch)

if callfunc == 'initialize':
  ip = getmyip()
  waitforconn(ip,<connport>,foo)
  sleep(.1)
  csock = openconn(ip,<connport>)
  csock.send('Hello, this is too long for such a short time')
  sleep(.5)
  exitall()
