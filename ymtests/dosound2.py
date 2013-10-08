mixer.put() # All off.
A_level.put(0x00)
B_level.put(0x00)
C_level.put(0x00)
setprev(0xff)
A_level.anim(1, 0x0d)
setprev(0xfe)
A_level.anim(2, 0x0d)
