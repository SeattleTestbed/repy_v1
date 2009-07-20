if callfunc == "initialize":
  fobj = open("junk_test.out", 'w')
  try:
    fobj.writelines(5)
  except TypeError:
    pass
  else:
    print "This shouldn't happen!"
  finally:
    fobj.close()
