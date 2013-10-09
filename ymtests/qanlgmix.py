mixer.put() # All off.
def reset():
  for l in A_level, B_level, C_level:
    l.put(0x0d) # Half amplitude.
reset()
sleep(50) # Allow it to settle at DC 0.
for a in xrange(0x10):
  for b in xrange(0x10):
    for c in xrange(0x10):
      A_level.put(a)
      B_level.put(b)
      C_level.put(c)
      sleep(2)
      reset()
      sleep(2)
