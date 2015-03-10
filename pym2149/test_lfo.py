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
from lfo import Env

class TestEnv(unittest.TestCase):

  def test_works(self):
    self.assertEqual([5], Env(5))
    self.assertEqual([8], Env(5).jump(8))
    self.assertEqual([5, 8], Env(5).lin(1, 8))
    self.assertEqual([5, 6, 7, 8], Env(5).lin(3, 8))
    self.assertEqual([5, 7, 8], Env(5).lin(2, 8))
    self.assertEqual([5, 6, 7, 7, 8], Env(5).lin(4, 8))
    # Negative values:
    self.assertEqual([-5, -8], Env(-5).lin(1, -8))
    self.assertEqual([-5, -6, -7, -8], Env(-5).lin(3, -8))
    self.assertEqual([-5, -7, -8], Env(-5).lin(2, -8))
    self.assertEqual([-5, -6, -7, -7, -8], Env(-5).lin(4, -8))
    # Holds:
    self.assertEqual([5, 5, 5, 5, 6, 7, 8], Env(5).hold(3).lin(3, 8))
    self.assertEqual([5, 5, 5, 8], Env(5).hold(3).jump(8))
    # Triangular:
    self.assertEqual([5, 6, 7, 6, 5, 4, 3, 4, 5], Env(5).tri(2, 7, 1))

if __name__ == '__main__':
  unittest.main()
