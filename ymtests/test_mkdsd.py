#!/usr/bin/env python

import unittest
from mkdsd import Data

class TestReg(unittest.TestCase):

  def test_anim(self):
    d = Data()
    r = d.reg()
    d.setprev(0)
    self.assertEqual(0, d.totalticks)
    r.anim(2, 5)
    # We did a whole cycle to decide it never stops:
    self.assertEqual(128, d.totalticks)

if __name__ == '__main__':
  unittest.main()
