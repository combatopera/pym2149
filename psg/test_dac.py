#!/usr/bin/env python

import unittest
from dac import *
from buf import *

class Ramps:

  def __call__(self, buf):
    for i in xrange(buf.framecount()):
      buf[i] = i

def expect(*values):
  return [v * 2 * Dac.halfpoweramp for v in values]

class TestDac(unittest.TestCase):

  def test_works(self):
    v = MasterBuf(4)
    v.fill(3, 4, 0)
    d = Dac(Ramps(), self, 15, 13, 1)
    self.value = 15
    d(v.ensureandcrop(3))
    self.assertEqual(expect(0, 1, 2, 0), list(v))
    self.value = 13
    d(v.ensureandcrop(3))
    self.assertEqual(expect(0, .5, 1, 0), list(v))
    d = Dac(Ramps(), self, 31, 27, 1)
    self.value = 31
    d(v.ensureandcrop(3))
    self.assertEqual(expect(0, 1, 2, 0), list(v))
    self.value = 23
    d(v.ensureandcrop(3))
    self.assertEqual(expect(0, .25, .5, 0), list(v))

if __name__ == '__main__':
  unittest.main()
