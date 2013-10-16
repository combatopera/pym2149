#!/usr/bin/env python

import unittest, numpy as np
from buf import Buf

class TestBuf(unittest.TestCase):

  def test_putring(self):
    b = Buf(np.zeros(20))
    r = np.arange(5)
    b.putring(3, 2, r, 4, 8)
    self.assertEqual([0, 0, 0, 4, 0, 0, 0, 1, 0, 2, 0, 3, 0, 4, 0, 0, 0, 1, 0, 0], list(b.buf))
    b.putring(4, 2, r, 4, 8)
    self.assertEqual([0, 0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 0, 1, 1, 0], list(b.buf))

if __name__ == '__main__':
  unittest.main()
