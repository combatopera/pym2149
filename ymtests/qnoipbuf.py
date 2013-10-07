mixer.put(A_noise)
A_level.put(0x0f)
for _ in xrange(10):
  N_period.put(0x1f)
  sleep(25)
  N_period.put(0x01)
  sleep(25)
A_level.put(0x00)
