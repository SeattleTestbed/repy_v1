def foo(ip,port,mess, ch):
  raise Exception, "Should not get here"

def noop(ip,port,mess, ch):
  stopcomm(ch)

if callfunc == 'initialize':
  ip = getmyip()
  recvmess(ip,12345,foo)
  recvmess(ip,12345,noop)   # should replace foo
  sleep(.1)
  sendmess(ip,12345,'hi')
