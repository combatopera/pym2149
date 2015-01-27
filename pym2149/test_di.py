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
        self.assertEqual([], di.all(str))
        self.assertEqual([], di.all(unicode))
        self.assertEqual([], di.all(basestring))
        self.assertEqual([], di.all(list))
        self.assertEqual((di.addinstance,), di.add('hmm'))
        self.assertEqual(['hmm'], di.all(str))
        self.assertEqual([], di.all(unicode))
        self.assertEqual(['hmm'], di.all(basestring))
        self.assertEqual([], di.all(list))
        self.assertEqual((di.addinstance,), di.add(u'hmmm'))
        self.assertEqual(['hmm'], di.all(str))
        self.assertEqual(['hmmm'], di.all(unicode))
        self.assertEqual(['hmm', 'hmmm'], di.all(basestring))
        self.assertEqual([], di.all(list))

    def test_simpleinjection(self):
        di = DI()
        class Hmm:
            @types(str)
            def __init__(self, dep):
                self.dep = dep
        self.assertEqual((di.addclass,), di.add(Hmm))
        self.assertEqual((di.addinstance,), di.add('hmm'))
        hmm = di(Hmm)
        self.assertEqual('hmm', hmm.dep)
        self.assertIs(hmm, di(Hmm))

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
        hmm = di(Hmm)
        self.assertEqual('implval', hmm.val)

    def test_factory(self):
        di = DI()
        class I: pass
        class N(int, I): pass
        class P(int, I): pass
        @types(int, this = I)
        def factory(n):
            return N(n) if n < 0 else P(n)
        self.assertEqual((di.addfactory,), di.add(factory))
        di.add(5)
        i = di(I) # No spin as DI thinks factory is I only.
        self.assertIs(P, i.__class__)
        self.assertEqual(5, i)

if __name__ == '__main__':
    unittest.main()
