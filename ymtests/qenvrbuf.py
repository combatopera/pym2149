mixer.put() # All off.
A_level.put(0x10) # Variable level.
E_fine.put(0x77)
E_rough.put(0x0e)
for i in xrange(10):
  E_shape.put(0x0a) # Triangle.
  sleep(2 + i)
A_level.put(0x00)
