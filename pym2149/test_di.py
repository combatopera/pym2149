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
        self.assertEqual([], di(str))
        self.assertEqual([], di(unicode))
        self.assertEqual([], di(basestring))
        self.assertEqual([], di(list))
        self.assertEqual((di.addinstance,), di.add('hmm'))
        self.assertEqual(['hmm'], di(str))
        self.assertEqual([], di(unicode))
        self.assertEqual(['hmm'], di(basestring))
        self.assertEqual([], di(list))
        self.assertEqual((di.addinstance,), di.add(u'hmmm'))
        self.assertEqual(['hmm'], di(str))
        self.assertEqual(['hmmm'], di(unicode))
        self.assertEqual(['hmm', 'hmmm'], di(basestring))
        self.assertEqual([], di(list))

    def test_simpleinjection(self):
        di = DI()
        class Hmm:
            @types(str)
            def __init__(self, dep):
                self.dep = dep
        self.assertEqual((di.addclass,), di.add(Hmm))
        self.assertEqual((di.addinstance,), di.add('hmm'))
        hmm, = di(Hmm)
        self.assertEqual('hmm', hmm.dep)
        self.assertEqual([hmm], di(Hmm)) # Should be same object.

    def test_metaclass(self):
        di = DI()
        class HasVal(type): pass
        class Impl:
            __metaclass__ = HasVal
            val = 'implval'
        class Hmm:
            @types(HasVal)
            def __init__(self, hasval):
                self.val = hasval.val
        self.assertEqual((di.addclass, di.addinstance), di.add(Impl))
        self.assertEqual((di.addclass,), di.add(Hmm))
        hmm, = di(Hmm)
        self.assertEqual('implval', hmm.val)

if __name__ == '__main__':
    unittest.main()
