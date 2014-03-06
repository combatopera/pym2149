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

from __future__ import division
import unittest
from util import Timer

class TestTimer(unittest.TestCase):

  def test_carry(self):
    clock = 2000000
    t = Timer(clock, None)
    def nextframecount(rate):
      blocks = list(t.blocks(rate))
      self.assertEqual(1, len(blocks))
      return blocks[0].framecount
    self.assertEqual(33333, nextframecount(60))
    self.assertEqual(20, t.carryticks)
    self.assertEqual(33334, nextframecount(60))
    self.assertEqual(-20, t.carryticks)
    self.assertEqual(33333, nextframecount(60))
    self.assertEqual(0, t.carryticks)
    self.assertEqual(clock * 10, nextframecount(.1))
    self.assertEqual(0, t.carryticks)

  def test_minblockrate(self):
    t = Timer(1000, 2)
    self.assertEqual([333], [b.framecount for b in t.blocks(3)])
    self.assertEqual(1, t.carryticks)
    self.assertEqual([334], [b.framecount for b in t.blocks(3)])
    self.assertEqual(-1, t.carryticks)
    self.assertEqual([333], [b.framecount for b in t.blocks(3)])
    self.assertEqual(0, t.carryticks)
    self.assertEqual([500], [b.framecount for b in t.blocks(2)])
    self.assertEqual(0, t.carryticks)
    self.assertEqual([500, 500], [b.framecount for b in t.blocks(1)])
    self.assertEqual(0, t.carryticks)
    # Don't bother returning a block of size zero:
    self.assertEqual([], [b.framecount for b in t.blocks(2001)])
    self.assertEqual(1000, t.carryticks)
    t.carryticks = 0

  def test_inexactminblockrate(self):
    t = Timer(1000, 3)
    # Every block satisfies the given condition:
    self.assertEqual([333, 333, 333, 1], [b.framecount for b in t.blocks(1)])
    self.assertEqual(0, t.carryticks)

  def test_fractionalrefreshrates(self):
    t = Timer(100, None)
    self.assertEqual([200], [b.framecount for b in t.blocks(.5)])
    self.assertEqual(0, t.carryticks)
    self.assertEqual([300], [b.framecount for b in t.blocks(1 / 3)])
    self.assertEqual(0, t.carryticks)
    self.assertEqual([67], [b.framecount for b in t.blocks(1.5)])
    self.assertEqual(-.5, t.carryticks)
    self.assertEqual([66], [b.framecount for b in t.blocks(1.5)])
    self.assertEqual(.5, t.carryticks)
    self.assertEqual([67], [b.framecount for b in t.blocks(1.5)])
    self.assertEqual(0, t.carryticks)

  def test_nonintegerclock(self):
    t = Timer(100.5, None)
    self.assertEqual([34], [b.framecount for b in t.blocks(3)])
    self.assertEqual(-1.5, t.carryticks)
    self.assertEqual([33], [b.framecount for b in t.blocks(3)])
    self.assertEqual(0, t.carryticks)
    self.assertEqual([34], [b.framecount for b in t.blocks(3)])
    self.assertEqual(-1.5, t.carryticks)
    t.carryticks = 0

if __name__ == '__main__':
  unittest.main()
