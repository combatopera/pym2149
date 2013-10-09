N_period.put(0x1f)
for i in xrange(10):
  mixer.put()
  A_level.put(0x0d)
  sleep(2 + i)
  A_level.put(0x0f)
  mixer.put(A_noise)
  sleep(2 + i)
A_level.put(0x00)
