include tcp.repy

MAX = 10
WINDOW = 2

def test_mod_range():    
  # usual
  assert mod_range(0, 5, MAX) == range(0, 5)

  # wrap around
  assert mod_range(5, 15, MAX) != range(5, 15) 
  assert mod_range(5, 15, MAX) == range(5, MAX) + range(0, 5)

  # should be none
  assert not mod_range(5, 3, MAX)

def test_mod_add():
  assert mod_add(1, 1, MAX) == 2
  assert mod_add(1, 11, MAX) == 2

def test_mod_sub():
  assert mod_sub(1, 1, MAX) == 0
  assert mod_sub(1, 11, MAX) == 0

def test_mod_gt():
  assert mod_gt(2, 1, MAX, WINDOW)
  assert not mod_gt(1, 2, MAX, WINDOW)
  assert not mod_gt(1, 1, MAX, WINDOW)
  assert mod_gt(11, 9, MAX, WINDOW)
  assert not mod_gt(12, 9, MAX, WINDOW)

def test_mod_lt():
  assert mod_lt(1, 2, MAX, WINDOW)
  assert not mod_lt(2, 1, MAX, WINDOW)
  assert not mod_lt(1, 1, MAX, WINDOW)
  assert mod_lt(9, 11, MAX, WINDOW)
  assert not mod_lt(9, 12, MAX, WINDOW)

if callfunc == 'initialize':
  test_mod_range()
  test_mod_add()
  test_mod_sub()
  test_mod_gt()
  test_mod_lt()
