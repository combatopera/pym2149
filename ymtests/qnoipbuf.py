mixer.put(A_noise)
A_level.put(0x0f)
for i in xrange(20):
  N_period.put(0x1f)
  sleep(2 + i)
  N_period.put(0x01)
  sleep(2 + i)
A_level.put(0x00)
