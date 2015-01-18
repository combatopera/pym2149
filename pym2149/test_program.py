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

import unittest
from program import FX

class TestFX(unittest.TestCase):

  def test_setbend(self):
    class Config:
      finepitchbendisrate = True
      pitchbendpersemitone = 1 # Don't care.
    fx = FX(Config())
    for coarse in xrange(0x80):
      for fine in xrange(0x80):
        fx.setbend(((coarse << 7) | fine) - 0x2000)
        self.assertEqual((coarse << 7) - 0x2000, fx.bend)
        self.assertEqual(fine - 0x40, fx.bendrate)

if __name__ == '__main__':
  unittest.main()
