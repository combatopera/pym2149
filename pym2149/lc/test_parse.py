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

from .parse import VParse, EParse, BadWordException
import unittest

class TestVParse(unittest.TestCase):

    @staticmethod
    def _perframes(sections):
        return [getattr(s, 'perframe', None) for s in sections.sections]

    def test_works(self):
        sections = VParse(float, 0, False)('1/1 2/1 .5/1', None)
        self.assertEqual([0, 1, 2], sections.frames)
        self.assertEqual(3, sections.len)
        self.assertEqual([1, 2, .5], [s.initial for s in sections.sections])
        self.assertEqual([1, -1.5, .5], self._perframes(sections))

    def test_widths(self):
        sections = VParse(float, 0, False)('1x/1 2x1/1 .5x2/.5', None) # Default value is 0.
        self.assertEqual([0, 1, 2, 3], sections.frames)
        self.assertEqual(3.5, sections.len)
        self.assertEqual([0, 1, 1, 2], [s.initial for s in sections.sections])
        self.assertEqual([1, None, 1, -4], self._perframes(sections))

    def test_slides(self):
        sections = VParse(float, 0, False)('5/.5 4/1 3/2 2/1', None) # Width of first word still implicitly 1.
        self.assertEqual([0, .5, 1, 2, 4], sections.frames)
        self.assertEqual(5, sections.len)
        self.assertEqual([5, 5, 4, 3, 2], [s.initial for s in sections.sections])
        self.assertEqual([None, -2, -1, -.5, 3], self._perframes(sections))

    def test_x(self):
        with self.assertRaises(BadWordException) as cm:
            VParse(float, 0, False)('x', None)
        self.assertEqual(('x',), cm.exception.args)

    def test_slash(self):
        with self.assertRaises(BadWordException) as cm:
            VParse(float, 0, False)('/', None)
        self.assertEqual(('/',), cm.exception.args)

    def test_combo(self):
        sections = VParse(float, 0, False)('3x4/5 0/1', None) # Total width is biggest explicit number.
        self.assertEqual([0, 5], sections.frames)
        self.assertEqual(6, sections.len)
        self.assertEqual([4, 0], [s.initial for s in sections.sections])
        self.assertEqual([-.8, 4], self._perframes(sections))

    def test_halfnotes(self):
        sections = VParse(float, 0, False)('2.5x4/1 0/1', None) # Implicit slide is still 1.
        self.assertEqual([0, 1.5, 2.5], sections.frames)
        self.assertEqual(3.5, sections.len)
        self.assertEqual([4, 4, 0], [s.initial for s in sections.sections])
        self.assertEqual([None, -4, 4], self._perframes(sections))

class TestEParse(unittest.TestCase):

    def test_works(self):
        sections = EParse(None, None)('1 2 .5', None)
        self.assertEqual([0, 1, 3], sections.frames)
        self.assertEqual(3.5, sections.len)
        self.assertEqual([0, 1, 3], [s.relframe for s in sections.sections])
        self.assertEqual([None, None, None], [s.onframes for s in sections.sections])

    def test_repeats(self):
        sections = EParse(None, None)('1x 2x3 3x2', None) # Default width is 1.
        self.assertEqual([0, 1, 4, 7, 9, 11], sections.frames)
        self.assertEqual(13, sections.len)
        self.assertEqual([0, 1, 4, 7, 9, 11], [s.relframe for s in sections.sections])
        self.assertEqual([None] * 6, [s.onframes for s in sections.sections])

    def test_badrepeat(self):
        with self.assertRaises(BadWordException) as cm:
            EParse(None, None)('.5x1', None)
        self.assertEqual(('.5x1',), cm.exception.args)
        with self.assertRaises(BadWordException) as cm:
            EParse(None, None)('-1x1', None)
        self.assertEqual(('-1x1',), cm.exception.args)
        with self.assertRaises(BadWordException) as cm:
            EParse(None, None)('3 0x1 2', None)
        self.assertEqual(('0x1',), cm.exception.args)

    def test_noteoff(self):
        # In '/.5' default width is 1, in '.5/1' width is biggest explicit number:
        sections = EParse(None, None)('/2 /.5 3/2 .5/1', None)
        self.assertEqual([0, 2, 2.5, 3, 4, 6], sections.frames)
        self.assertEqual(7, sections.len)
        self.assertEqual([0, 2, 2.5, 3, 4, 6], [s.relframe for s in sections.sections])
        self.assertEqual([0, None, .5, None, 1, 0], [s.onframes for s in sections.sections])
