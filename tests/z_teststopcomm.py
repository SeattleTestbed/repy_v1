def foo(ip,port,mess, ch):
  print ip,port,mess,ch

if callfunc == 'initialize':
  ch = recvmess('',12345,foo)
  sleep(.1)
  stopcomm(ch)
