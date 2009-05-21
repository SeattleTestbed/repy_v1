

# Function with variable arguments
def func1(*args):
  # Recognize the current clientnum
  mycontext[mycontext["clientnum"]] = True

# Function with exactly 5 args
def func2(ip,port,sock,ch1,ch2):
  mycontext[mycontext["clientnum"]] = True

# Check the same functions, from inside an object
class Thing():
  def func3(self,*args):
    mycontext[mycontext["clientnum"]] = True

  def func4(self,ip,port,sock,ch1,ch2):
    mycontext[mycontext["clientnum"]] = True

def timeout():
  print "Timed out!"
  print "mycontext:",mycontext
  exitall()

if callfunc == "initialize":
  ip = getmyip()
  port = <connport>

  # Setup the waitforconn
  waith = waitforconn(ip,port,func1)

  # Setup mycontext
  mycontext["clientnum"] = 1
  
  # Set our timeout timer
  timeh = settimer(40,timeout,())

  # Try connecting 
  sock1 = openconn(ip,port)
  sleep(3)
  sock1.close()

  # Switch the callback function
  mycontext["clientnum"] += 1
  waith = waitforconn(ip,port,func2)
  sock2 = openconn(ip,port)
  sleep(3)
  sock2.close()

  # Get a "Thing" object
  th = Thing()
  mycontext["clientnum"] += 1
  waith = waitforconn(ip,port,th.func3)
  sock3 =openconn(ip,port)
  sleep(3)
  sock3.close()

  mycontext["clientnum"] += 1
  waith = waitforconn(ip,port,th.func4)
  sock4 = openconn(ip,port)
  sleep(3)
  sock4.close()

  # Cancel the timer, cleanup and exit
  canceltimer(timeh)
  stopcomm(waith)

  if not (mycontext[1] and mycontext[2] and mycontext[3] and mycontext[4]):
    print "Not all connections worked!",mycontext

  exitall()



  

