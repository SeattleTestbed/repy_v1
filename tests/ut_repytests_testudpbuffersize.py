
#pragma repy restrictions.fasternetsendfullcpu

myip = getmyip()

mycontext['maxlag'] = 0
maxloglock = getlock()
mycontext['packetcount'] = 0

def sendforever():
  while True:
    # send a message that is around 100 bytes
    sendmess(myip, <messport>, str(getruntime())+" "+"X"*92)

def getmessages(ip, port, message, ch):
  sendtime = float(message.split()[0])
  lag = getruntime() - sendtime

  maxloglock.acquire()

  if mycontext['maxlag'] < lag:
    mycontext['maxlag'] = lag

  mycontext['packetcount'] = mycontext['packetcount'] + 1
  maxloglock.release()
  


def check_and_exit():
  if mycontext['maxlag'] > 2:
    print "UDP packets lag too long in the buffer: ", mycontext['maxlag']

  if mycontext['maxlag'] == 0:
    print "UDP packets were not received or had 0 lag"

  if mycontext['packetcount'] < 500:
    print "There weren't many packets sent",mycontext['packetcount']

  exitall()
  

if callfunc == 'initialize':
  recvmess(myip, <messport>, getmessages)
  settimer(10.0, check_and_exit, ())
  sendforever()

