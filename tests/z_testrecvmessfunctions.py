

# Function with variable arguments
def func1(*args):
  # Recognize the current clientnum
  mycontext[mycontext["clientnum"]] = True

# Function with exactly 4 args
def func2(ip,port,mesg,ch):
  mycontext[mycontext["clientnum"]] = True

# Check the same functions, from inside an object
class Thing():
  def func3(self,*args):
    mycontext[mycontext["clientnum"]] = True

  def func4(self,ip,port,mesg,ch):
    mycontext[mycontext["clientnum"]] = True

def timeout():
  print "Timed out!"
  print "mycontext:",mycontext
  exitall()

if callfunc == "initialize":
  ip = getmyip()
  port = <messport>

  # Setup the waitforconn
  waith = recvmess(ip,port,func1)

  # Setup mycontext
  mycontext["clientnum"] = 1
  
  # Set our timeout timer
  timeh = settimer(40,timeout,())

  # Try connecting 
  sendmess(ip,port,"ping")
  sleep(3)

  # Switch the callback function
  mycontext["clientnum"] += 1
  waith = recvmess(ip,port,func2)
  sendmess(ip,port,"ping")
  sleep(3)

  # Get a "Thing" object
  th = Thing()
  mycontext["clientnum"] += 1
  waith = recvmess(ip,port,th.func3)
  sendmess(ip,port,"ping")
  sleep(3)

  mycontext["clientnum"] += 1
  waith = recvmess(ip,port,th.func4)
  sendmess(ip,port,"ping")
  sleep(3)

  # Cancel the timer, cleanup and exit
  canceltimer(timeh)
  stopcomm(waith)

  if not (mycontext[1] and mycontext[2] and mycontext[3] and mycontext[4]):
    print "Not all connections worked!",mycontext

  exitall()



  

