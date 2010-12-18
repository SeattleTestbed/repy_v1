#pragma out
#pragma repy


# we will ensure we can get random numbers quickly if there are no restrictions

def foo():
  if mycontext['winner'] == None:
    mycontext['winner'] = 'timer'
  

if callfunc == 'initialize':

  # let's do this 3 times because sometimes on XP there is a race / timer
  # scheduling issue that makes a pass fail. (See #963)
  for attempt in range(3):

    # delay between attempts
    sleep(1)

    # reset / set a global to indicate which thread wins
    mycontext['winner'] = None

    settimer(.5, foo, ())
  
    # generate lots of numbers.   With rate limiting, the timer should fire 
    # first...   Without rate limiting, the main thread should win.
    for num in range(50):
      randomfloat()
      # If I don't sleep here, then the other thread isn't likely to be 
      # scheduled
      sleep(.00001)
  
    if mycontext['winner'] == None:
      # this means the main thread won
      print "This should be reached when there aren't time restrictions"

    # wait for the timer to fire
    while mycontext['winner'] == None:
      sleep(.2)



