#!/usr/bin/env python

import sys, operator

class Reg:

  def __init__(self, data, index, xform):
    self.data = data
    self.index = index
    self.xform = xform

  def put(self, *value):
    self.data.bytecode.extend([self.index, self.xform(*value)])

  def anim(self, preadjust, last):
    self.data.bytecode.extend([0x81, self.index, preadjust & 0xff, last])
    # If prev equals last we do a full cycle rather than nothing, see dosound0:
    value = self.data.prev
    while True:
      value = (value + preadjust) & 0xff
      self.data.totalticks += 1
      if value == last or value == self.data.prev:
        break

class Data:

  def __init__(self):
    self.index = 0
    self.totalticks = 0
    self.bytecode = []

  def reg(self, xform = lambda x: x):
    r = Reg(self, self.index, xform)
    self.index += 1
    return r

  def setprev(self, prev):
    self.bytecode.extend([0x80, prev])
    self.prev = prev

  def sleep(self, ticks):
    if ticks < 2:
      raise Exception(ticks)
    while ticks:
      part = min(256, ticks)
      self.bytecode.extend([0x82, part - 1])
      self.totalticks += part
      ticks -= part

  def save(self, f):
    w = lambda v: f.write(''.join(chr(x) for x in v))
    w([self.totalticks >> 8, self.totalticks & 0xff])
    w(self.bytecode)
    w([0x82, 0])

def main():
  for inpath in sys.argv[1:]:
    outpath = inpath[:inpath.rindex('.')] + '.dsd'
    print >> sys.stderr, outpath
    data = Data()
    A_fine, A_rough, B_fine, B_rough, C_fine, C_rough, N_period = (data.reg() for _ in xrange(7))
    mixer, setprev, sleep = data.reg(lambda *v: 0x3f & ~reduce(operator.or_, v, 0)), data.setprev, data.sleep
    A_level, B_level, C_level, E_fine, E_rough, E_shape = (data.reg() for _ in xrange(6))
    A_tone, B_tone, C_tone, A_noise, B_noise, C_noise = (0x01 << i for i in xrange(6))
    execfile(inpath, locals())
    f = open(outpath, 'wb')
    try:
      data.save(f)
      f.flush()
    finally:
      f.close()

if '__main__' == __name__:
  main()
