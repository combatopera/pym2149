#!/usr/bin/env python

import sys, operator

class Reg:

  def __init__(self, bytecode, index, xform):
    self.bytecode = bytecode
    self.index = index
    self.xform = xform

  def put(self, value):
    self.bytecode.extend([self.index, self.xform(value)])

class Data:

  def __init__(self):
    self.index = 0
    self.totalticks = 0
    self.bytecode = []

  def reg(self, xform = lambda x: x):
    r = Reg(self.bytecode, self.index, xform)
    self.index += 1
    return r

  def sleep(self, ticks):
    if ticks < 2:
      raise Exception(ticks)
    self.bytecode.extend([0x82, ticks - 1])
    self.totalticks += ticks

  def save(self, f):
    w = lambda v: f.write(''.join(chr(x) for x in v))
    w([self.totalticks >> 8, self.totalticks & 0xff])
    w(self.bytecode)
    w([0x82, 0])

def main():
  inpath, outpath = sys.argv[1:]
  data = Data()
  A_fine, A_rough, B_fine, B_rough, C_fine, C_rough, N_period = (data.reg() for _ in xrange(7))
  mixer = data.reg(lambda *v: 0x3f & ~reduce(operator.or_, v))
  A_level, B_level, C_level, E_fine, E_rough, E_shape = (data.reg() for _ in xrange(6))
  A_tone, B_tone, C_tone, A_noise, B_noise, C_noise = (0x01 << i for i in xrange(6))
  sleep = data.sleep
  execfile(inpath)
  f = open(outpath, 'wb')
  try:
    data.save(f)
    f.flush()
  finally:
    f.close()

if '__main__' == __name__:
  main()
