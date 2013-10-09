A_fine.put(0x00)
rough1 = 0x06
rough2 = 0x08
A_rough.put(rough2)
mixer.put(A_tone)
for i in xrange(5):
  A_level.put(0x0f)
  sleep(2 + i)
  A_level.put(0x0d)
  sleep(2 + i)
for i in xrange(10):
  A_rough.put(rough1)
  A_level.put(0x0d)
  sleep(2 + i)
  A_rough.put(rough2)
  A_level.put(0x0f)
  sleep(2 + i)
A_level.put(0x00)
