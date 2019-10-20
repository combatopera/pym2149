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

from .context import ContextImpl
import unittest

class TestContext(unittest.TestCase):

    tuning = None

    def setUp(self):
        self.c = ContextImpl(self)

    def test_globals(self):
        self.c._update('''g = 5
def bump():
    global g
    g += 1''')
        self.c._flip()
        self.assertEqual(5, self.c.g)
        self.c.bump()
        self.assertEqual(6, self.c.g)
        self.c._update('''foo = "bar"''')
        self.c._flip()
        self.assertEqual(6, self.c.g)
        self.c.bump()
        self.assertEqual(7, self.c.g)

    def test_flip(self):
        self.c._update('''speed = 100''')
        self.assertEqual(16, self.c.speed)
        self.c._flip()
        self.assertEqual(100, self.c.speed)
        self.c._update('''del speed''')
        self.assertEqual(100, self.c.speed)
        self.c._flip()
        with self.assertRaises(AttributeError) as cm:
            self.c.speed
        self.assertEqual(('speed',), cm.exception.args)

    def test_flip2(self):
        self.c._update('''x = object()
y = object()
z = object()
sections = [x, y]''')
        self.assertEqual((), self.c.sections)
        self.c._flip()
        s = self.c.sections
        self.assertEqual([self.c.x, self.c.y], s)
        self.c._update('''sections = [y, z]''')
        self.assertIs(s, self.c.sections)
        self.c._flip()
        self.assertEqual([self.c.y, self.c.z], self.c.sections)
