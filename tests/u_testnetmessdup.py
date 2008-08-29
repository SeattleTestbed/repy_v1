def foo(ip,port,mess, ch):
  stopcomm(ch)

if callfunc == 'initialize':
  ip = getmyip()
  recvmess(ip,12345,foo)
  # should raise an exception here on Mac, but not on Linux...
  recvmess(ip,12345,foo)
  sleep(.1)
  sendmess(ip,12345,'hi')
  sleep(.1)
  sendmess(ip,12345,'hi')
