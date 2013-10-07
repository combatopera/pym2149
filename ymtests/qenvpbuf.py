mixer.put() # All off.
A_level.put(0x10) # Variable level.
E_shape.put(0x0a) # Triangle.
E_fine.put(0x77) # Non-zero.
for _ in xrange(10):
  E_rough.put(0xff)
  sleep(25)
  E_rough.put(0x00)
  sleep(25)
A_level.put(0x00)
