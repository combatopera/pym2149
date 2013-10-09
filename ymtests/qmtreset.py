A_fine.put(0x00)
A_rough.put(0x07)
A_level.put(0x0f)
for i in xrange(10):
  mixer.put()
  sleep(2 + i)
  mixer.put(A_tone)
  sleep(2 + i)
A_level.put(0x00)
