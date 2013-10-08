mixer.put() # All off.
for a in xrange(0x10):
  A_level.put(a)
  for b in xrange(0x10):
    B_level.put(b)
    for c in xrange(0x10):
      C_level.put(c)
      sleep(2)
