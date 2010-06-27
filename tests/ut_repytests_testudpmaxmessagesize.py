
#pragma repy 

myip = getmyip()

def getmessages(ip, port, message, ch):
  # this should be the last message we get.
  if len(message) == 65507:
    exitall()


def error_and_exit():
  print 'Failed to receive maximum size UDP message (65507)'
  exitall()


if callfunc == 'initialize':

  recvmess(myip, <messport>, getmessages)

  for allowedmessagesize in [1, 100, 10000, 65000, 65506]:
    try:
      sendmess(myip, <messport>, "X"*allowedmessagesize)
    except Exception, e:
      print "Failed to send message of size:",allowedmessagesize,"due to error '",str(e),"'"

  
  for disallowedmessagesize in [70000, 65555, 65508]:
    try:
      sendmess(myip, <messport>, "X"*disallowedmessagesize)
    except Exception, e:
      # It would be great to only catch the appropriate exception here
      pass
    else:
      print "No exception when sending message of size:",disallowedmessagesize,"!!!"

  # this message should cause us to exit.   
  sendmess(myip, <messport>, "X"*65507)

  # ... if not, it's an error because the message likely wasn't received
  settimer(2.0, error_and_exit, ())

