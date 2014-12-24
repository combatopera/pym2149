#!/usr/bin/env python

# Copyright 2014 Andrzej Cichocki

# This file is part of pym2149.
#
# pym2149 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pym2149 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pym2149.  If not, see <http://www.gnu.org/licenses/>.

import unittest, numpy as np
from minblep import MinBleps
from nod import BufNode
from collections import namedtuple

class TestMinBleps(unittest.TestCase):

  def test_minphasereconstruction(self):
    minbleps = MinBleps(500, 1, 500)
    absdft = np.abs(np.fft.fft(minbleps.bli))
    absdft2 = np.abs(np.fft.fft(minbleps.minbli))
    self.assertTrue(np.allclose(absdft, absdft2))

  def test_types(self):
    minbleps = MinBleps(500, 1, 500)
    self.assertEqual(BufNode.floatdtype, minbleps.minblep.dtype)

  def test_xform(self):
    ctrlrate, outrate, scale = 10, 6, 5
    minbleps = MinBleps(ctrlrate, outrate, scale)
    mixins = []
    MixinInfo = namedtuple('MixinInfo', 'outi shape data')
    for x in xrange(ctrlrate * 2):
      outi = minbleps.naivex2outx[x % ctrlrate]
      shape = minbleps.naivex2shape[x % ctrlrate]
      data = minbleps.minblep[shape::scale]
      mixins.append(MixinInfo(outi, shape, data))
    self.assertEqual([0, 0, 1, 1, 2, 3, 3, 4, 4, 5] * 2, [m.outi for m in mixins])
    self.assertEqual([4, 1, 3, 0, 2] * 4, [m.shape for m in mixins])

  def test_counts(self):
    mb = MinBleps(10, 6, 5)
    self.assertEqual([0, 0, 1, 1, 2, 3, 3, 4, 4, 5], [mb.getoutcount(0, n) for n in xrange(10)])
    self.assertEqual([0, 1, 1, 2, 3, 3, 4, 4, 5, 6], [mb.getoutcount(1, n) for n in xrange(10)])
    self.assertEqual([0, 0, 1, 2, 2, 3, 3, 4, 5, 5], [mb.getoutcount(2, n) for n in xrange(10)])
    self.assertEqual([0, 1, 2, 2, 3, 3, 4, 5, 5, 6], [mb.getoutcount(3, n) for n in xrange(10)])
    self.assertEqual([0, 1, 1, 2, 2, 3, 4, 4, 5, 5], [mb.getoutcount(4, n) for n in xrange(10)])
    self.assertEqual([0, 0, 1, 1, 2, 3, 3, 4, 4, 5], [mb.getoutcount(5, n) for n in xrange(10)])
    self.assertEqual([0, 1, 1, 2, 3, 3, 4, 4, 5, 6], [mb.getoutcount(6, n) for n in xrange(10)])
    self.assertEqual([0, 0, 1, 2, 2, 3, 3, 4, 5, 5], [mb.getoutcount(7, n) for n in xrange(10)])
    self.assertEqual([0, 1, 2, 2, 3, 3, 4, 5, 5, 6], [mb.getoutcount(8, n) for n in xrange(10)])
    self.assertEqual([0, 1, 1, 2, 2, 3, 4, 4, 5, 5], [mb.getoutcount(9, n) for n in xrange(10)])
    self.assertEqual([0, 2, 4, 5, 7, 9, 10, 12, 14, 15], [mb.getminnaiven(0, n) for n in xrange(10)])
    self.assertEqual([-1, 1, 3, 4, 6, 8, 9, 11, 13, 14], [mb.getminnaiven(1, n) for n in xrange(10)])
    self.assertEqual([0, 2, 3, 5, 7, 8, 10, 12, 13, 15], [mb.getminnaiven(2, n) for n in xrange(10)])
    self.assertEqual([-1, 1, 2, 4, 6, 7, 9, 11, 12, 14], [mb.getminnaiven(3, n) for n in xrange(10)])
    self.assertEqual([0, 1, 3, 5, 6, 8, 10, 11, 13, 15], [mb.getminnaiven(4, n) for n in xrange(10)])
    self.assertEqual([0, 2, 4, 5, 7, 9, 10, 12, 14, 15], [mb.getminnaiven(5, n) for n in xrange(10)])
    self.assertEqual([-1, 1, 3, 4, 6, 8, 9, 11, 13, 14], [mb.getminnaiven(6, n) for n in xrange(10)])
    self.assertEqual([0, 2, 3, 5, 7, 8, 10, 12, 13, 15], [mb.getminnaiven(7, n) for n in xrange(10)])
    self.assertEqual([-1, 1, 2, 4, 6, 7, 9, 11, 12, 14], [mb.getminnaiven(8, n) for n in xrange(10)])
    self.assertEqual([0, 1, 3, 5, 6, 8, 10, 11, 13, 15], [mb.getminnaiven(9, n) for n in xrange(10)])

if __name__ == '__main__':
  unittest.main()
