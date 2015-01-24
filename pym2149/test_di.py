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
from di import DI, types

class TestDI(unittest.TestCase):

    def test_instances(self):
        di = DI()
        self.assertEqual([], di.getorcreate(str))
        self.assertEqual([], di.getorcreate(unicode))
        self.assertEqual([], di.getorcreate(basestring))
        self.assertEqual([], di.getorcreate(list))
        di.addinstance('hmm')
        self.assertEqual(['hmm'], di.getorcreate(str))
        self.assertEqual([], di.getorcreate(unicode))
        self.assertEqual(['hmm'], di.getorcreate(basestring))
        self.assertEqual([], di.getorcreate(list))
        di.addinstance(u'hmmm')
        self.assertEqual(['hmm'], di.getorcreate(str))
        self.assertEqual(['hmmm'], di.getorcreate(unicode))
        self.assertEqual(['hmm', 'hmmm'], di.getorcreate(basestring))
        self.assertEqual([], di.getorcreate(list))

    def test_simpleinjection(self):
        di = DI()
        class Hmm:
            @types(str)
            def __init__(self, dep):
                self.dep = dep
        di.addclass(Hmm)
        di.addinstance('hmm')
        hmm, = di.getorcreate(Hmm)
        self.assertEqual('hmm', hmm.dep)
        self.assertEqual([hmm], di.getorcreate(Hmm)) # Should be same object.

if __name__ == '__main__':
    unittest.main()
