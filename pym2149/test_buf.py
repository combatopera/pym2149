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

  def test_loop(self):
    b = Buf(np.zeros(20))
    r = np.arange(5)
    b.putring(3, 2, r, 1, 8, 2)
    self.assertEqual([0, 0, 0, 1, 0, 2, 0, 3, 0, 4, 0, 2, 0, 3, 0, 4, 0, 2, 0, 0], list(b.buf))
    b.putring(4, 2, r, 1, 8, 2)
    self.assertEqual([0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 2, 2, 3, 3, 4, 4, 2, 2, 0], list(b.buf))

  def test_putringops(self):
    r = np.empty(5)
    self.assertEqual(0, Buf.putringops(r, None, 0))
    self.assertEqual(1, Buf.putringops(r, 0, 1))
    self.assertEqual(1, Buf.putringops(r, 4, 1))
    self.assertEqual(1, Buf.putringops(r, 0, 5))
    self.assertEqual(2, Buf.putringops(r, 0, 6))
    self.assertEqual(2, Buf.putringops(r, 1, 5))
    self.assertEqual(2, Buf.putringops(r, 0, 10))
    self.assertEqual(2, Buf.putringops(r, 0, 9, 1))
    self.assertEqual(3, Buf.putringops(r, 0, 10, 1))
    self.assertEqual(3, Buf.putringops(r, 3, 8, 2))
    self.assertEqual(4, Buf.putringops(r, 3, 9, 2))

if __name__ == '__main__':
  unittest.main()
