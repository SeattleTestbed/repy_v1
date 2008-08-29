def foo(ip,port,mess, ch):
  stopcomm(ch)
  exitall()

if callfunc == 'initialize':
  ip = getmyip()
  recvmess(ip,12345,foo)
  sleep(.1)
  sendmess(ip,12345,'hi')
  sendmess(ip,12345,'Hello, this is too long of a message to be received in such a short time')
  print "hi"
