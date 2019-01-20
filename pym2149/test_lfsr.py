# Copyright 2014, 2018, 2019 Andrzej Cichocki

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
from .lfsr import Lfsr
from .ym2149 import ym2149nzdegrees

class TestLfsr(unittest.TestCase):

    def test_correctsequence(self):
        # Subsequence of the real LFSR from Hatari mailing list:
        expected = (0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0)
        # According to qnoispec, raw LFSR 1 maps to amp 0, so we flip our LFSR:
        expected = [1 - x for x in expected]
        actual = tuple(Lfsr(ym2149nzdegrees))
        self.assertTrue(''.join(map(str, expected)) in ''.join(map(str, actual)))
