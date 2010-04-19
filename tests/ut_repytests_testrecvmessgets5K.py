#pragma repy

def recvfunc(ip,port,mesg,ch):
  if mesg == mycontext['testmessage']:
    # success!
    exitall()

  print 'Unexpected message with lens',len(mesg), len(mycontext['testmessage'])

def timeout():
  print "Timed out!"
  exitall()

if callfunc == "initialize":
  ip = getmyip()
  port = <messport>

  # Setup the recvmess
  waith = recvmess(ip,port,recvfunc)

  # Set our timeout timer
  timeh = settimer(40,timeout,())

  mycontext['testmessage'] = 'a'*4096 + 'b'*1024

  # Try connecting 
  sendmess(ip,port,mycontext['testmessage'])
  

