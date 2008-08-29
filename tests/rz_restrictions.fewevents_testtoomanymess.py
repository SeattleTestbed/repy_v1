def foo(ip,port,mess, ch):
  if mess == 'error':
    print "If the event count is <=2, this is an error"
  
  # just wait when getting a connection
  sleep(.4)


if callfunc == 'initialize':
  mycontext['count'] = 0

  ip = getmyip()

  ch1 = recvmess(ip,12345,foo)
  sendmess(ip,12345,"hi")
  sendmess(ip,12345,"hi")
  sendmess(ip,12345,"error") # should not get delivered if the event count is 2
  sleep(.1)
  stopcomm(ch1)

#  sockobj.close()
