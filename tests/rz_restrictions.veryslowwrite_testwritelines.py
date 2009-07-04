# getattr/setattr can be used to circumvent nannying restrictions on
# disk write rates and probably other things. They are very dangerous to
# keep around, I think.

class one_time_use_sequence(object):
  # This class behaves like a normal iterable object the first time
  # __iter__ is called; after that, it pretends to be an empty array.

  # This works because in emulated_file.writelines() we first call
  # python's writelines() directly, which iterates over the object,
  # then we iterate over it again ourselves and sum the lengths of each
  # string as our total. Because we can pretend to be empty the second
  # iteration, nanny doesn't notice we actually wrote some data.

  def __init__(self, data):
    self.data = data
    self.used = False

def foo(self):
  if self.used:
    return getattr([], '__iter__')()

  self.used = True
  return getattr(self.data, '__iter__')()

setattr(one_time_use_sequence, "__iter__", foo)

if callfunc == 'initialize':
  longstr = "some really really long amount of data"

  my_single_use_sequence = \
      one_time_use_sequence([longstr])

  fh = open("junk_test.out", "wb")
  start_time = getruntime()
  fh.writelines(my_single_use_sequence)
  end_time = getruntime()
  fh.close()

  if end_time - start_time < 1:
    print "This shouldn't happen. (file.writelines isn't nannying correctly.)"
