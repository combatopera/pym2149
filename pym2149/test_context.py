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

    def test_globals(self):
        c = ContextImpl(self)
        c._update('''g = 5
def bump():
    global g
    g += 1
''', True)
        self.assertEqual(5, c.g)
        c.bump()
        self.assertEqual(6, c.g)
        c._update('''foo = 'bar'
''', True)
        self.assertEqual(6, c.g)
        c.bump()
        self.assertEqual(7, c.g)
