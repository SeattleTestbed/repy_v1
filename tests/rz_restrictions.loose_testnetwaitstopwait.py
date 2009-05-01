def new_client(remoteip, remoteport, socketlikeobj, commhandle, thisnatcon): 
  pass

# run the test!
if callfunc == "initialize":
 
  ip = '127.0.0.1' 

  handle = waitforconn(ip,12345,new_client) 
  # should work

  sock1 = openconn(ip,12345)
 
  stopcomm(handle) 

  sock1.close()

  # should fail
  try:
    sock2 = openconn(ip,12345)
  except Exception, e:
    #just do nothing
    pass
  else:
    print 'failed to get error opening sock2'
    sock2.close()

  handle = waitforconn(ip,12345,new_client)

  # should work
  sock3 = openconn(ip,12345)
  sock3.close()

  stopcomm(handle) 

  # should fail
  try:
    sock4 = openconn(ip,12345)
  except Exception, e:
    #just do nothing
    pass
  else:
    print 'failed to get error opening sock4'
    sock4.close()


  

