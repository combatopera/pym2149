mixer.put() # All off.
A_level.put(0x10) # Variable level.
E_shape.put(0x0a) # Triangle.
E_fine.put(0x00)
for i in xrange(20):
  E_rough.put(0x05)
  sleep(2 + i)
  E_rough.put(0x02)
  sleep(2 + i)
A_level.put(0x00)
