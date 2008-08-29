def foo(ip,port,mess, ch):
  print ip,port,mess,ch
  stopcomm(ch)

if callfunc == 'initialize':
  ip = getmyip()
  recvmess(ip,12345,foo)
  sleep(.1)
  sendmess(ip,12345,'hi')
