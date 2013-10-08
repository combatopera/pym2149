mixer.put(A_tone)
A_level.put(0x0f)
A_fine.put(0x00)
for i in xrange(10):
  A_rough.put(0x0e)
  sleep(2 + i)
  A_rough.put(0x00) # Period now zero.
  sleep(2 + i)
A_level.put(0x00)
