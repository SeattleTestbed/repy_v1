"""
   Author: Justin Cappos

   Start Date: 1 July 2008

   Description:

   This module handles pausing the program if there is a resource violation.
   This module is likely to be fiddly and the cause of most of the portability
   issues...
"""

# for sleep
import time

# needed for cpu, disk, and memory handling
import nonportable

# needed for locking
import threading


# resources that drain / replenish over time
renewable_resources = ['cpu', 'filewrite', 'fileread', 'netsend', 'netrecv',
	'loopsend', 'looprecv', 'lograte', 'random']

# resources where the quantity of use may vary by use 
quantity_resources = [ "cpu", "memory", "diskused", "filewrite", "fileread", 
	'loopsend', 'looprecv', "netsend", "netrecv", "lograte", 'random']

# resources where the number of items is the quantity (events because each
# event is "equal", insockets because a listening socket is a listening socket)
fungible_item_resources = ['events', 'filesopened', 'insockets', 'outsockets']

# resources where there is no quantity.   There is only one messport 12345 and
# a vessel either has it or the vessel doesn't.   The resource messport 12345
# isn't fungible because it's not equal to having port 54321.   A vessel may
# have more than one of the resulting individual resources and so are
# stored in a list.
individual_item_resources = [ 'messport', 'connport' ]

# include resources that are fungible vs those that are individual...
item_resources = fungible_item_resources + individual_item_resources


# this is used by restrictions.py to set up our tables
known_resources = quantity_resources + item_resources 


must_assign_resources = [ "cpu", "memory", "diskused" ]

# the restrictions on how resources should be used.   This is filled in for
# me by the restrictions module
# keys are the all_resources, a value is a float with meaning to me...
resource_restriction_table = {}


# the current quantity of a resource that is used.   This should be updated
# by calling update_resource_consumption_table() before being used.
resource_consumption_table = {}


# Locks for resource_consumption_table
# I only need to lock the renewable resources because the other resources use
# sets (which handle locking internally)
renewable_resource_lock_table = {}
for init_resource in renewable_resources:
  renewable_resource_lock_table[init_resource] = threading.Lock()




# set up renewable resources to start now...
renewable_resource_update_time = {}
for init_resource in renewable_resources:
  renewable_resource_update_time[init_resource] = time.time()



# set up individual_item_resources to be in the restriction_table (as a set)
for init_resource in individual_item_resources:
  resource_restriction_table[init_resource] = set()


# updates the values in the consumption table (taking the current time into 
# account)
def update_resource_consumption_table(resource):

  thetime = time.time()

  # I'm going to reduce all renewable resources by the appropriate amount given
  # the amount of elapsed time.

  elapsedtime = thetime - renewable_resource_update_time[resource]

  renewable_resource_update_time[resource] = thetime

  if elapsedtime < 0:
    # a negative number (likely a NTP reset).   Let's just ignore it.
    return

  # remove the charge
  reduction = elapsedtime * resource_restriction_table[resource]
    
  if reduction > resource_consumption_table[resource]:

    # not much use to remove
    resource_consumption_table[resource] = 0.0
  else:

    # subtract some for elapsed time...
    resource_consumption_table[resource] = resource_consumption_table[resource] - reduction



# want to wait until a resource can be used again...
def sleep_until_resource_drains(resource):

  # It'll never drain!
  if resource_restriction_table[resource] == 0:
    raise Exception, "Resource '"+resource+"' limit set to 0, won't drain!"
    

  # We may need to go through this multiple times because other threads may
  # also block and consume resources.
  while resource_consumption_table[resource] > resource_restriction_table[resource]:

    # until we're expected to be under quota
    sleeptime = (resource_consumption_table[resource] - resource_restriction_table[resource]) / resource_restriction_table[resource]

    time.sleep(sleeptime)

    update_resource_consumption_table(resource)







############################ Externally called ########################



def start_resource_nanny():
  # init the resource_consumption_table
  for resource in quantity_resources:
    resource_consumption_table[resource] = 0.0

  for resource in item_resources:
    # double check there is no overlap...
    if resource in quantity_resources:
      raise Exception, "Resource cannot be both quantity and item based!"

    resource_consumption_table[resource] = set()


  nonportable.monitor_cpu_disk_and_mem(resource_restriction_table['cpu'], resource_restriction_table['diskused'], resource_restriction_table['memory'])




# let the nanny know that the process is consuming some resource
# can also be called with quantity '0' for a renewable resource so that the
# nanny will wait until there is some free "capacity"
def tattle_quantity(resource, quantity):

  # I assume that the quantity will never be negative
  if quantity < 0:
    raise Exception, "Internal Error: resource '"+resource+"' has a negative quantity "+str(quantity)+"!"
    
  # get the lock for this resource
  renewable_resource_lock_table[resource].acquire()
  
  # release the lock afterwards no matter what
  try: 
    # update the resource counters based upon the current time.
    update_resource_consumption_table(resource)

    # It's renewable, so I can wait for it to clear
    if resource not in renewable_resources:
      # Should never have a quantity tattle for a non-renewable resource
      raise Exception, "Internal Error: resource '"+resource+"' is not renewable!"
  

    resource_consumption_table[resource] = resource_consumption_table[resource] + quantity
    # I'll block if I'm over...
    sleep_until_resource_drains(resource)
  
  finally:
    # release the lock for this resource
    renewable_resource_lock_table[resource].release()
    




# let the nanny know that the process is consuming some resource
# can also be called with quantity '0' for a renewable resource so that the
# nanny will wait until there is some free "capacity"
def tattle_add_item(resource, item):
  if item != None:
    resource_consumption_table[resource].add(item)

  if len(resource_consumption_table[resource]) > resource_restriction_table[resource]:
    # it's clobberin time!
    raise Exception, "Resource '"+resource+"' limit exceeded!!"



def tattle_remove_item(resource, item):
  try:
    resource_consumption_table[resource].remove(item)
  except KeyError:
    pass



# used for individual_item_resources
def tattle_check(resource, item):
  if item not in resource_restriction_table[resource]:
    raise Exception, "Resource '"+resource+" "+str(item)+"' not allowed!!!"

  resource_consumption_table[resource].add(item)

