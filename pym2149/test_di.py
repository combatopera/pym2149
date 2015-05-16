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
        class N(int): pass
        class P(int): pass
        @types(int, this = I)
        def factory(n):
            return N(n) if n < 0 else P(n)
        self.assertEqual((di.addfactory,), di.add(factory))
        di.add(5)
        i = di(I) # No spin as DI thinks factory is I only.
        self.assertIs(P, i.__class__)
        self.assertEqual(5, i)

    def test_optional(self):
        class A:
            @types()
            def __init__(self): pass
        class B:
            @types()
            def __init__(self): pass
        class Opt:
            @types(A, B)
            def __init__(self, a, b = 123):
                self.a = a
                self.b = b
        di = DI()
        di.add(A)
        di.add(Opt)
        opt = di(Opt)
        self.assertIs(A, opt.a.__class__)
        self.assertEqual(123, opt.b)
        di.add(B)
        self.assertEqual(123, di(Opt).b) # It's cached.
        di = DI()
        di.add(A)
        di.add(B)
        di.add(Opt)
        opt = di(Opt)
        self.assertIs(A, opt.a.__class__)
        self.assertIs(B, opt.b.__class__)

    class Eventful:

        @types(list)
        def __init__(self, events): self.events = events

    class OK(Eventful):

        def start(self): self.events.append(self.__class__.__name__ + '.start')

        def stop(self): self.events.append(self.__class__.__name__ + '.stop')

    def test_lifecycle(self):
        class A(self.OK): pass
        class B(self.OK): pass
        events = []
        di = DI()
        di.add(events)
        di.add(A)
        di.start()
        self.assertEqual(['A.start'], events)
        di.add(B)
        di.start() # Should only start new stuff.
        self.assertEqual(['A.start', 'B.start'], events)
        di.start() # Nothing more to be done.
        self.assertEqual(['A.start', 'B.start'], events)
        di.stop()
        self.assertEqual(['A.start', 'B.start', 'B.stop', 'A.stop'], events)
        di.stop() # Should be idempotent.
        self.assertEqual(['A.start', 'B.start', 'B.stop', 'A.stop'], events)

    def test_startdoesnotinstantiatenonstartables(self):
        class KaboomException: pass
        class Kaboom:
            @types()
            def __init__(self): raise KaboomException
            def stop(self): pass # Not significant.
        di = DI()
        di.add(Kaboom)
        di.start() # Should do nothing.
        try:
            di(Kaboom)
            self.fail('Expected a KaboomException.')
        except KaboomException:
            pass # Expected.

    class BadStart(Eventful):

        class BadStartException: pass

        def start(self): raise self.BadStartException

    def test_unrollduetobadstart(self):
        class A(self.OK): pass
        class B(self.OK): pass
        class C(self.OK): pass
        events = []
        di = DI()
        di.add(events)
        di.add(A)
        di.start()
        self.assertEqual(['A.start'], events)
        di.add(B)
        di.add(C)
        di.add(self.BadStart)
        try:
            di.start()
            self.fail('Expected a BadStartException.')
        except self.BadStart.BadStartException:
            pass # Expected.
        self.assertEqual(['A.start', 'B.start', 'C.start', 'C.stop', 'B.stop'], events)
        di.stop()
        self.assertEqual(['A.start', 'B.start', 'C.start', 'C.stop', 'B.stop', 'A.stop'], events)

    class BadStop(OK):

        class BadStopException: pass

        def stop(self): raise self.BadStopException

    def test_stoperrorislogged(self):
        events = []
        di = DI()
        def error(msg, *args, **kwargs):
            self.assertEqual({'exc_info': True}, kwargs)
            self.assertEqual("Failed to stop an instance of %s:", msg)
            arg, = args
            events.append(arg)
        di.error = error
        di.add(events)
        di.add(self.OK)
        di.add(self.BadStop)
        di.start()
        self.assertEqual(['OK.start', 'BadStop.start'], events)
        di.stop()
        self.assertEqual(['OK.start', 'BadStop.start', "%s.%s" % (self.BadStop.__module__, self.BadStop.__name__), 'OK.stop'], events)

if '__main__' == __name__:
    unittest.main()
