def foo(ip,port,mess, ch):
  print ip,port,mess,ch
  print
  stopcomm(ch)

if callfunc == 'initialize':
  recvmess('127.0.0.1',12345,foo)
  sleep(.1)
  sendmess('127.0.0.1',12345,'Hello, this is too long for such a short time')
  sleep(.5)
  exitall()
