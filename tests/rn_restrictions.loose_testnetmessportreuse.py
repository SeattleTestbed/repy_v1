def foo(ip,port,mess, ch):
  print ip,port,mess,ch
  stopcomm(ch)

def noop(a,b,c,d):
  pass

if callfunc == 'initialize':
  ip = getmyip()
  noopch = recvmess(ip,12345,noop)
  recvmess(ip,12346,foo)
  sleep(.1)
  sendmess(ip,12346,'hi',ip,12345)
  stopcomm(noopch)
