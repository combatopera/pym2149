mixer.put() # All off.
A_level.put(0x00)
B_level.put(0x00)
C_level.put(0x00)
setprev(0x0d)
A_level.anim(1, 0x0f)
setprev(0x0d)
A_level.anim(1, 0x0d) # Observe last same as prev.
