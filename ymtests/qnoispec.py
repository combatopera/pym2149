mixer.put(A_noise)
for p in xrange(0x20):
  A_level.put(0x0f)
  N_period.put(p)
  sleep(48)
  A_level.put(0x00)
  sleep(2)
