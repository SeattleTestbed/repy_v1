if callfunc == "initialize":
  def foo():
    a = openconn("google.com", 80)

  def bar():
    b = openconn("yahoo.com", 80)

  foo()
  bar()
  foo()
  bar()
  foo()
  bar()
