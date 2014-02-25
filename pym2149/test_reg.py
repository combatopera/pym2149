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
from reg import Reg, DerivedReg

class TestReg(unittest.TestCase):

  def test_works(self):
    r = Reg(None)
    self.assertEqual(1, r.version)
    self.assertEqual(None, r.value)
    r.value = 'hello'
    self.assertEqual(2, r.version)
    self.assertEqual('hello', r.value)
    r.value = 'hello'
    self.assertEqual(3, r.version)
    self.assertEqual('hello', r.value)
    r.value = 100
    self.assertEqual(100, r.value)
    self.assertEqual(4, r.version)

class TestDerivedReg(unittest.TestCase):

  def test_works(self):
    r1 = Reg(2)
    r2 = Reg(3)
    rd = DerivedReg(lambda x, y: x + y, r1, r2)
    self.assertEqual(5, rd.value)
    self.assertEqual((1, 1, 0), rd.version)
    r1.value = 5
    self.assertEqual(8, rd.value)
    self.assertEqual((2, 1, 0), rd.version)
    r2.value = 7
    # It should also work if we try the version first:
    self.assertEqual((2, 2, 0), rd.version)
    self.assertEqual(12, rd.value)
    rd.value = 100
    self.assertEqual(100, rd.value)
    self.assertEqual((2, 2, 1), rd.version)
    rd.value = 101
    self.assertEqual(101, rd.value)
    self.assertEqual((2, 2, 2), rd.version)
    r2.value = 11
    self.assertEqual(16, rd.value)
    self.assertEqual((2, 3, 2), rd.version)

  def test_bypassfirst(self):
    r1 = Reg(2)
    r2 = Reg(3)
    rd = DerivedReg(lambda x, y: x + y, r1, r2)
    rd.value = 100
    self.assertEqual(100, rd.value)
    self.assertEqual((1, 1, 1), rd.version)

if __name__ == '__main__':
  unittest.main()
