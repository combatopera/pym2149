#!/usr/bin/env python

import unittest, numpy as np
from minblep import MinBleps
from buf import MasterBuf

class TestMinBleps(unittest.TestCase):

  def test_minphasereconstruction(self):
    minbleps = MinBleps(500)
    absdft = np.abs(np.fft.fft(minbleps.bli))
    absdft2 = np.abs(np.fft.fft(minbleps.minbli))
    self.assertTrue(np.allclose(absdft, absdft2))

  def getmixins(self, scale):
    ctrlrate, outrate = 12, 1
    self.assertEqual(12, MinBleps.idealscale(ctrlrate, outrate))
    minbleps = MinBleps(scale)
    masterbuf = MasterBuf(np.float32)
    mixins = []
    for x in xrange(ctrlrate * 2):
      outi, buf, _ = minbleps.getmixin(x, ctrlrate, outrate, 1, masterbuf)
      mixins.append((outi, np.copy(buf.buf)))
    return mixins

  def test_sharing(self):
    mixins = self.getmixins(4) # A third of the ideal.
    for x in xrange(0, 2):
      self.assertEqual(0, mixins[x][0])
      self.assertTrue((mixins[0][1] == mixins[x][1]).all())
    for x in xrange(2, 5):
      self.assertEqual(1, mixins[x][0])
      self.assertTrue((mixins[3][1] == mixins[x][1]).all())
    for x in xrange(5, 8):
      self.assertEqual(1, mixins[x][0])
      self.assertTrue((mixins[6][1] == mixins[x][1]).all())
    for x in xrange(8, 11):
      self.assertEqual(1, mixins[x][0])
      self.assertTrue((mixins[9][1] == mixins[x][1]).all())
    for x in xrange(11, 14):
      self.assertEqual(1, mixins[x][0])
      self.assertTrue((mixins[0][1] == mixins[x][1]).all())
    for x in xrange(14, 17):
      self.assertEqual(2, mixins[x][0])
      self.assertTrue((mixins[3][1] == mixins[x][1]).all())
    for x in xrange(17, 20):
      self.assertEqual(2, mixins[x][0])
      self.assertTrue((mixins[6][1] == mixins[x][1]).all())
    for x in xrange(20, 23):
      self.assertEqual(2, mixins[x][0])
      self.assertTrue((mixins[9][1] == mixins[x][1]).all())
    for x in xrange(23, 24):
      self.assertEqual(2, mixins[x][0])
      self.assertTrue((mixins[0][1] == mixins[x][1]).all())

  def test_sharing2(self):
    mixins = self.getmixins(3) # A quarter of the ideal.
    for x in xrange(0, 2):
      self.assertEqual(0, mixins[x][0])
      self.assertTrue((mixins[0][1] == mixins[x][1]).all())
    for x in xrange(2, 6):
      self.assertEqual(1, mixins[x][0])
      self.assertTrue((mixins[4][1] == mixins[x][1]).all())
    for x in xrange(6, 10):
      self.assertEqual(1, mixins[x][0])
      self.assertTrue((mixins[8][1] == mixins[x][1]).all())
    for x in xrange(10, 14):
      self.assertEqual(1, mixins[x][0])
      self.assertTrue((mixins[0][1] == mixins[x][1]).all())
    for x in xrange(14, 18):
      self.assertEqual(2, mixins[x][0])
      self.assertTrue((mixins[4][1] == mixins[x][1]).all())
    for x in xrange(18, 22):
      self.assertEqual(2, mixins[x][0])
      self.assertTrue((mixins[8][1] == mixins[x][1]).all())
    for x in xrange(22, 24):
      self.assertEqual(2, mixins[x][0])
      self.assertTrue((mixins[0][1] == mixins[x][1]).all())

if __name__ == '__main__':
  unittest.main()
