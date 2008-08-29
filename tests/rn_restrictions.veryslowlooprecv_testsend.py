def foo(ip,port,mess, ch):
  print ip,port,mess,ch
  stopcomm(ch)
  sleep(.5)
  exitall()

if callfunc == 'initialize':
  recvmess('127.0.0.1',12345,foo)
  sleep(.1)
  sendmess('127.0.0.1',12345,'hi')
  sendmess('127.0.0.1',12345,'Hello, this is too long of a message to be received in such a short time')
  print "hi"
