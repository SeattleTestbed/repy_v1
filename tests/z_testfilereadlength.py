if callfunc == "initialize":
  fobj = open("junk_test.out", 'rb')
  str = fobj.read(5)
  if len(str) > 5:
    fail("fobj.read() should read no more than len bytes!")
