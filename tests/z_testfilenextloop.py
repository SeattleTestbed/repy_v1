if callfunc == "initialize":
  fobj = open("junk_test.out")
  for line in fobj:
    pass

  try:
    fobj.next()
  except StopIteration:
    pass
  else:
    raise Exception('Should raise StopIteration')
  finally:
    fobj.close()
