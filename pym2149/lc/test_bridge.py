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

from .bridge import LiveCodingBridge
from ..context import Sections
import unittest

class TestAdjustFrameIndex(unittest.TestCase):

    class Pattern:

        def __init__(self, len):
            self.len = len

    ignoreloop = None
    section = None
    chipchannels = None
    speed = 10
    A = Pattern(10),
    B = Pattern(11),
    C = Pattern(12),

    def setUp(self):
        self.b = LiveCodingBridge(self, self, self, self)

    def adjust(self, *args):
        return self.b.adjustframeindex(self.oldsections, *args)

    @property
    def _sections(self):
        return Sections(self.speed, self.sections)

    def test_shift(self):
        self.oldsections = self.A, self.C
        self.sections = self.A, self.B, self.C
        self.assertEqual(100+110+60, self.adjust(100+60))
        self.assertEqual(100+110+120+100+110+60, self.adjust(100+120+100+60))
        self.oldsections = self.B, self.C
        self.sections = self.A, self.B, self.C
        self.assertEqual(100+55, self.adjust(55))
        self.assertEqual(100+110+60, self.adjust(110+60))
        self.assertEqual(100+110+120+100+55, self.adjust(110+120+55))
        self.assertEqual(100+110+120+100+110+60, self.adjust(110+120+110+60))
        self.oldsections = self.A, self.B, self.C
        self.sections = self.B, self.C
        self.assertEqual(55, self.adjust(100+55))
        self.assertEqual(110+60, self.adjust(100+110+60))
        self.assertEqual(110+120+55, self.adjust(100+110+120+100+55))
        self.assertEqual(110+120+110+60, self.adjust(100+110+120+100+110+60))
        self.oldsections = self.A, self.B, self.C
        self.sections = self.A, self.C
        self.assertEqual(100+60, self.adjust(100+110+60))
        self.assertEqual(100+120+100+60, self.adjust(100+110+120+100+110+60))

    def test_swap(self):
        self.oldsections = self.A, self.B, self.C
        self.sections = self.A, self.C, self.B
        self.assertEqual(50, self.adjust(50))
        self.assertEqual(100+120+55, self.adjust(100+55))
        self.assertEqual(100+60, self.adjust(100+110+60))

    def test_insertearlier(self):
        self.oldsections = self.A, self.B, self.C
        self.sections = self.C, self.A, self.B, self.C
        self.assertEqual(120+50, self.adjust(50))
        self.assertEqual(120+100+55, self.adjust(100+55))
        self.assertEqual(120+100+110+60, self.adjust(100+110+60))

    def test_delete(self):
        self.oldsections = self.A, self.B, self.C
        self.sections = self.A, self.C
        self.assertEqual(50, self.adjust(50))
        self.assertEqual(100, self.adjust(100+55))
        self.assertEqual(100+60, self.adjust(100+110+60))
        self.oldsections = self.A, self.B, self.C
        self.sections = self.C,
        self.assertEqual(0, self.adjust(50))
        self.assertEqual(0, self.adjust(100+55))
        self.assertEqual(60, self.adjust(100+110+60))
