mixer.put(A_tone, A_noise)
A_level.put(0x10) # Variable level.
A_fine.put(0x1f)
A_rough.put(0x00)
N_period.put(0x1f)
E_shape.put(0x0a) # Triangle.
E_fine.put(0x77)
E_rough.put(0xff)
sleep(500)
A_level.put(0x00)
