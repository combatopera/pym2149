from util import blocks

def dosound(bytecode, chip, clock, stream):
  def g():
    for b in bytecode:
      yield b & 0xff # It's supposed to be bytecode.
  g = g()
  bi = blocks(clock, 50) # Authentic period.
  while True:
    ctrl = g.next()
    if ctrl <= 0xF:
      chip.R[ctrl].value = g.next()
    elif 0x80 == ctrl:
      softreg = g.next()
    elif 0x81 == ctrl:
      targetreg = chip.R[g.next()]
      adjust = g.next()
      if adjust >= 0x80:
        adjust -= 0x100 # Convert back to signed.
      last = g.next()
      while True:
        # TODO LATER: What happens if we reach/skip zero?
        softreg += adjust # Yes, this is done up-front.
        targetreg.value = softreg
        stream(bi.next()) # One frame with that value.
        # That's right, if we skip past it we loop forever:
        if last == softreg:
          break
    elif ctrl >= 0x82:
      ticks = g.next()
      if not ticks:
        break
      ticks += 1 # Apparently!
      for i in xrange(ticks):
        stream(bi.next())
    else:
      raise Exception(ctrl)
