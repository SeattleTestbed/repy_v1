writedata = ['foo\n','bar\n','baz\n']

fo = file("junk_test.out",'w')
fo.writelines(writedata)
fo.close()

fo = file("junk_test.out",'r')
data = fo.readlines()
fo.close()

print writedata==data

fo = file("junk_test.out",'w')
fo.writelines(writedata)
fo.close()

fo = file("junk_test.out",'r')
data = fo.read()
fo.close()

print data

class myclass(object):
  pass

moredata1 = ("fee", "phi", "pho", "fum")

def myiter(self):
  return getattr(moredata1, "__iter__")()

setattr(myclass, "__iter__", myiter)

moredata2 = myclass()

fo = file("junk_test.out",'w')
fo.writelines(moredata1)
fo.close()

fo = file("junk_test.out",'r')
data = fo.read()
fo.close()

print data

fo = file("junk_test.out",'w')
fo.writelines(moredata2)
fo.close()

fo = file("junk_test.out",'r')
data = fo.read()
fo.close()

print data
