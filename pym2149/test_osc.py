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

import unittest, time, sys, numpy as np
from osc import ToneOsc, NoiseOsc, EnvOsc, RationalDerivative, RToneOsc
from mfp import mfpclock
from nod import Block
from reg import Reg, VersionReg
from ring import DerivativeRing
from buf import Buf
from lfsr import Lfsr
from ym2149 import ym2149nzdegrees, YM2149
from shapes import toneshape
from dac import PWMEffect
from collections import namedtuple

class AbstractTestOsc:

    def test_performance(self):
        blockrate = 50
        blocksize = 2000000 // blockrate
        for p in self.performanceperiods:
            r = Reg(value = p)
            o = self.createosc(8, r)
            start = time.time()
            for _ in xrange(blockrate):
                o.call(Block(blocksize))
            self.cmptime(time.time() - start, self.performancelimit)

    def cmptime(self, taken, strictlimit):
        expression = "%.3f < %s" % (taken, strictlimit)
        sys.stderr.write("%s ... " % expression)
        self.assertTrue(eval(expression))

class TestToneOsc(AbstractTestOsc, unittest.TestCase):

    performanceperiods = 0x001, 0xfff
    performancelimit = .05

    @staticmethod
    def createosc(scale, periodreg):
        return ToneOsc(scale, periodreg)

    def test_works(self):
        o = self.createosc(8, Reg(value = 3))
        v = o.call(Block(96)).tolist()
        self.assertEqual([1] * 24, v[:24])
        self.assertEqual([0] * 24, v[24:48])
        self.assertEqual([1] * 24, v[48:72])
        self.assertEqual([0] * 24, v[72:])
        v = o.call(Block(48)).tolist()
        self.assertEqual([1] * 24, v[:24])
        self.assertEqual([0] * 24, v[24:])

    def test_resume(self):
        o = self.createosc(8, Reg(value = 3))
        v = o.call(Block(25)).tolist()
        self.assertEqual([1] * 24, v[:24])
        self.assertEqual([0], v[24:])
        v = o.call(Block(24)).tolist()
        self.assertEqual([0] * 23, v[:23])
        self.assertEqual([1], v[23:])

    def test_carry(self):
        r = Reg(value = 0x01)
        size = 3 * 8 + 1
        ref = self.createosc(8, r).call(Block(size)).tolist()
        for n in xrange(size + 1):
            o = self.createosc(8, r)
            v1 = o.call(Block(n)).tolist()
            v2 = o.call(Block(size - n)).tolist()
            self.assertEqual(ref, v1 + v2)

    def test_endexistingstepatendofblock(self):
        r = Reg(value = 0x01)
        o = self.createosc(8, r)
        self.assertEqual([1] * 4, o.call(Block(4)).tolist())
        self.assertEqual([1] * 4, o.call(Block(4)).tolist())
        self.assertEqual([0] * 4, o.call(Block(4)).tolist())

    def test_increaseperiodonboundary(self):
        r = Reg(value = 0x01)
        o = self.createosc(8, r)
        self.assertEqual([1] * 8 + [0] * 8, o.call(Block(16)).tolist())
        r.value = 0x02
        self.assertEqual([1] * 16 + [0] * 15, o.call(Block(31)).tolist())
        r.value = 0x03
        self.assertEqual([0] * 9 + [1] * 24 + [0], o.call(Block(34)).tolist())

    def test_decreaseperiodonboundary(self):
        r = Reg(value = 0x03)
        o = self.createosc(8, r)
        self.assertEqual([1] * 24 + [0] * 24, o.call(Block(48)).tolist())
        r.value = 0x02
        self.assertEqual([1] * 16 + [0] * 16 + [1] * 6, o.call(Block(38)).tolist())
        r.value = 0x01
        self.assertEqual([1] * 2 + [0] * 8 + [1] * 8 + [0], o.call(Block(19)).tolist())

    def test_smallerblocksthanperiod(self):
        r = Reg(value = 0x05)
        o = self.createosc(1, r)
        self.assertEqual([1,1,1,1], o.call(Block(4)).tolist())
        self.assertEqual([1,0,0,0], o.call(Block(4)).tolist())
        self.assertEqual([0,0,1], o.call(Block(3)).tolist())
        self.assertEqual([1,1,1,1], o.call(Block(4)).tolist())
        self.assertEqual([0,0,0,0,0], o.call(Block(5)).tolist())
        self.assertEqual([1], o.call(Block(1)).tolist())

class TestRToneOsc(AbstractTestOsc, unittest.TestCase): # FIXME: MFP timers do not behave like YM2149 tones.

    performanceperiods = 0x001, 0xfff
    performancelimit = .1

    @staticmethod
    def createosc(scale, periodreg):
        clock = 200
        effect = VersionReg(value = PWMEffect(None))
        effectivedata = Reg().link(lambda p: scale*p*mfpclock//clock, periodreg)
        periodreg.value = periodreg.value # Init effectivedata.
        return RToneOsc(clock, namedtuple('Timer', 'effect prescalerornone effectivedata')(effect, Reg(value = 1), effectivedata))

    def test_works(self):
        o = self.createosc(8, Reg(value = 3))
        v = o.call(Block(96)).tolist()
        self.assertEqual([1] * 24, v[:24])
        self.assertEqual([0] * 24, v[24:48])
        self.assertEqual([1] * 24, v[48:72])
        self.assertEqual([0] * 24, v[72:])
        v = o.call(Block(48)).tolist()
        self.assertEqual([1] * 24, v[:24])
        self.assertEqual([0] * 24, v[24:])

    def test_resume(self):
        o = self.createosc(8, Reg(value = 3))
        v = o.call(Block(25)).tolist()
        self.assertEqual([1] * 24, v[:24])
        self.assertEqual([0], v[24:])
        v = o.call(Block(24)).tolist()
        self.assertEqual([0] * 23, v[:23])
        self.assertEqual([1], v[23:])

    def test_carry(self):
        r = Reg(value = 0x01)
        size = 3 * 8 + 1
        ref = self.createosc(8, r).call(Block(size)).tolist()
        for n in xrange(size + 1):
            o = self.createosc(8, r)
            v1 = o.call(Block(n)).tolist()
            v2 = o.call(Block(size - n)).tolist()
            self.assertEqual(ref, v1 + v2)

    def test_endexistingstepatendofblock(self):
        r = Reg(value = 0x01)
        o = self.createosc(8, r)
        self.assertEqual([1] * 4, o.call(Block(4)).tolist())
        self.assertEqual([1] * 4, o.call(Block(4)).tolist())
        self.assertEqual([0] * 4, o.call(Block(4)).tolist())

    def test_increaseperiodonboundary(self):
        r = Reg(value = 0x01)
        o = self.createosc(8, r)
        self.assertEqual([1] * 8 + [0] * 8, o.call(Block(16)).tolist())
        r.value = 0x02
        self.assertEqual([1] * 16 + [0] * 15, o.call(Block(31)).tolist())
        r.value = 0x03
        # Unlike tone, the existing countdown is not affected:
        self.assertEqual([0] + [1] * 24 + [0] * 24 + [1], o.call(Block(50)).tolist())

    def test_decreaseperiodonboundary(self):
        r = Reg(value = 0x03)
        o = self.createosc(8, r)
        self.assertEqual([1] * 24 + [0] * 24, o.call(Block(48)).tolist())
        r.value = 0x02
        self.assertEqual([1] * 16 + [0] * 16 + [1] * 6, o.call(Block(38)).tolist())
        r.value = 0x01
        # Unlike tone, the existing countdown is not affected:
        self.assertEqual([1] * 10 + [0] * 8 + [1] * 8 + [0], o.call(Block(27)).tolist())

    def test_smallerblocksthanperiod(self):
        r = Reg(value = 0x05)
        o = self.createosc(1, r)
        self.assertEqual([1,1,1,1], o.call(Block(4)).tolist())
        self.assertEqual([1,0,0,0], o.call(Block(4)).tolist())
        self.assertEqual([0,0,1], o.call(Block(3)).tolist())
        self.assertEqual([1,1,1,1], o.call(Block(4)).tolist())
        self.assertEqual([0,0,0,0,0], o.call(Block(5)).tolist())
        self.assertEqual([1], o.call(Block(1)).tolist())

    def test_writetdrwhilestopped(self):
        pass # TODO: Implement.

    def test_writetdrwhileenabled(self):
        pass # TODO: Implement.

    def test_stoptimer(self):
        effect = VersionReg(value = namedtuple('Effect', 'getshape')(lambda: toneshape))
        prescalerornone = Reg(value=3)
        effectivedata = Reg(value=5)
        chipimplclock = mfpclock*2 # Not dissimilar to the real thing.
        o = RToneOsc(chipimplclock, namedtuple('Timer', 'effect prescalerornone effectivedata')(effect, prescalerornone, effectivedata))
        self.assertEqual([1]*30 + [0]*11, o.call(Block(41)).tolist())
        self.assertEqual(4, o.derivative.maincounter)
        self.assertEqual(chipimplclock//2, o.derivative.prescalercount)
        self.assertEqual([0]*19 + [1]*30 + [0]*10, o.call(Block(59)).tolist())
        self.assertEqual(4, o.derivative.maincounter)
        self.assertEqual(chipimplclock, o.derivative.prescalercount)
        prescalerornone.value = None
        self.assertEqual([0]*100, o.call(Block(100)).tolist())
        self.assertEqual(4, o.derivative.maincounter)
        self.assertEqual(None, o.derivative.prescalercount)
        prescalerornone.value = 3
        self.assertEqual([0]*24 + [1]*30 + [0], o.call(Block(55)).tolist())
        self.assertEqual(5, o.derivative.maincounter)
        self.assertEqual(chipimplclock*5//2, o.derivative.prescalercount)
        # XXX: Finished?

class TestRationalDerivative(unittest.TestCase):

    @staticmethod
    def integrate(d, n):
        v = Buf(np.empty(n, dtype = int))
        d.call(Block(n))(v)
        return v.tolist()

    def test_works(self):
        effect = namedtuple('Effect', 'getshape')(lambda: toneshape)
        timer = namedtuple('Timer', 'effect prescalerornone effectivedata')(VersionReg(value = effect), Reg(value = 1), Reg(value = 81920))
        d = RationalDerivative(100, timer)
        expected = [1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0] * 4
        for _ in xrange(13):
            self.assertEqual(expected, self.integrate(d, 80))
        actual = []
        expected = [1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0] * 5
        def block(n):
            actual.extend(self.integrate(d, n))
        for _ in xrange(33):
            block(3)
        block(1)
        self.assertEqual(expected, actual)

    def test_notrunning(self):
        effect = namedtuple('Effect', 'getshape')(lambda: toneshape)
        timer = namedtuple('Timer', 'effect prescalerornone effectivedata')(VersionReg(value = effect), Reg(value = None), Reg(value = 1))
        d = RationalDerivative(1000, timer)
        for _ in xrange(50):
            self.assertEqual([0] * 100, self.integrate(d, 100)) # Expect no interrupts.
        self.assertEqual(None, d.prescalercount)
        self.assertEqual(0, d.maincounter)
        timer.prescalerornone.value = 24576
        # The maincounter was 0, so that's an interrupt in the void:
        self.assertEqual([1] * 10 + [0] * 10 + [1] * 5, self.integrate(d, 25))
        self.assertEqual(5*mfpclock, d.prescalercount)
        self.assertEqual(1, d.maincounter)
        timer.prescalerornone.value = None
        # No more interrupts, maincounter preserved:
        self.assertEqual([1] * 25, self.integrate(d, 25))
        self.assertEqual(None, d.prescalercount)
        self.assertEqual(1, d.maincounter)

class TestNoiseOsc(AbstractTestOsc, unittest.TestCase):

    performanceperiods = 0x01, 0x1f
    performancelimit = .05

    @staticmethod
    def createosc(scale, periodreg):
        return NoiseOsc(scale, periodreg, YM2149.noiseshape)

    def test_works(self):
        n = 100
        o = NoiseOsc(8, Reg(value = 3), YM2149.noiseshape)
        u = Lfsr(ym2149nzdegrees)
        for _ in xrange(2):
            v = o.call(Block(48 * n)).tolist()
            for i in xrange(n):
                self.assertEqual([u()] * 48, v[i * 48:(i + 1) * 48])

    def test_carry(self):
        r = Reg(value = 0x01)
        size = 17 * 16 + 1
        ref = NoiseOsc(8, r, YM2149.noiseshape).call(Block(size)).tolist()
        for n in xrange(size + 1):
            o = NoiseOsc(8, r, YM2149.noiseshape)
            v1 = o.call(Block(n)).tolist()
            v2 = o.call(Block(size - n)).tolist()
            self.assertEqual(ref, v1 + v2)

    def test_increaseperiodonboundary(self):
        r = Reg(value = 0x01)
        o = NoiseOsc(4, r, DerivativeRing([1, 0]))
        self.assertEqual([1] * 8 + [0] * 8, o.call(Block(16)).tolist())
        r.value = 0x02
        self.assertEqual([1] * 16 + [0] * 15, o.call(Block(31)).tolist())
        r.value = 0x03
        self.assertEqual([0] + [1] * 24 + [0], o.call(Block(26)).tolist())

    def test_decreaseperiodonboundary(self):
        r = Reg(value = 0x03)
        o = NoiseOsc(4, r, DerivativeRing([1, 0]))
        self.assertEqual([1] * 24 + [0] * 24, o.call(Block(48)).tolist())
        r.value = 0x02
        self.assertEqual([1] * 16 + [0] * 16 + [1] * 6, o.call(Block(38)).tolist())
        r.value = 0x01
        self.assertEqual([1] * 10 + [0] * 8 + [1] * 8 + [0], o.call(Block(27)).tolist())

class TestEnvOsc(unittest.TestCase):

    def test_shapes(self):
        r = EnvOsc.shapes[0x0c]
        self.assertEqual(1025, r.npbuf.shape[0])
        self.assertEqual(1, r.loopstart)
        self.assertEqual(range(32) + range(32), list(np.cumsum(r.npbuf[:64])))
        r = EnvOsc.shapes[0x08]
        self.assertEqual(1025, r.npbuf.shape[0])
        self.assertEqual(1, r.loopstart)
        self.assertEqual(range(31, -1, -1) + range(31, -1, -1), list(np.cumsum(r.npbuf[:64])))
        r = EnvOsc.shapes[0x0e]
        self.assertEqual(1025, r.npbuf.shape[0])
        self.assertEqual(1, r.loopstart)
        self.assertEqual(range(32) + range(31, -1, -1) + range(32), list(np.cumsum(r.npbuf[:96])))
        r = EnvOsc.shapes[0x0a]
        self.assertEqual(1025, r.npbuf.shape[0])
        self.assertEqual(1, r.loopstart)
        self.assertEqual(range(31, -1, -1) + range(32) + range(31, -1, -1), list(np.cumsum(r.npbuf[:96])))
        r = EnvOsc.shapes[0x0f]
        self.assertEqual(1033, r.npbuf.shape[0])
        self.assertEqual(33, r.loopstart)
        self.assertEqual(range(32) + [0] * 32, list(np.cumsum(r.npbuf[:64])))
        r = EnvOsc.shapes[0x0d]
        self.assertEqual(1033, r.npbuf.shape[0])
        self.assertEqual(33, r.loopstart)
        self.assertEqual(range(32) + [31] * 32, list(np.cumsum(r.npbuf[:64])))
        r = EnvOsc.shapes[0x0b]
        self.assertEqual(1033, r.npbuf.shape[0])
        self.assertEqual(33, r.loopstart)
        self.assertEqual(range(31, -1, -1) + [31] * 32, list(np.cumsum(r.npbuf[:64])))
        r = EnvOsc.shapes[0x09]
        self.assertEqual(1033, r.npbuf.shape[0])
        self.assertEqual(33, r.loopstart)
        self.assertEqual(range(31, -1, -1) + [0] * 32, list(np.cumsum(r.npbuf[:64])))

    def test_reset(self):
        shapereg = VersionReg(value = 0x0c)
        periodreg = Reg(value = 0x0001)
        o = EnvOsc(8, periodreg, shapereg)
        self.assertEqual(range(32) + range(16), o.call(Block(48 * 8)).tolist()[::8])
        self.assertEqual(range(16, 32) + range(16), o.call(Block(32 * 8)).tolist()[::8])
        shapereg.value = 0x0c
        self.assertEqual(range(32) + range(16), o.call(Block(48 * 8)).tolist()[::8])

    def test_08(self):
        shapereg = VersionReg(value = 0x08)
        periodreg = Reg(value = 3)
        o = EnvOsc(8, periodreg, shapereg)
        for _ in xrange(2):
            v = o.call(Block(8 * 3 * 32)).tolist()
            for i in xrange(32):
                self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])

    def test_09(self):
        for shape in xrange(0x04):
            o = EnvOsc(8, Reg(value = 3), VersionReg(value = shape))
            v = o.call(Block(8 * 3 * 32)).tolist()
            for i in xrange(32):
                self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])
            self.assertEqual([0] * (8 * 3 * 34), o.call(Block(8 * 3 * 34)).tolist())

    def test_09loop(self):
        o = EnvOsc(1, Reg(value = 1), VersionReg(value = 0x09))
        self.assertEqual(range(31, -1, -1), o.call(Block(32)).tolist())
        self.assertEqual(set([0]), set(o.call(Block(10000)).tolist()))

    def test_0a(self):
        shapereg = VersionReg(value = 0x0a)
        periodreg = Reg(value = 3)
        o = EnvOsc(8, periodreg, shapereg)
        v = o.call(Block(8 * 3 * 32)).tolist()
        for i in xrange(32):
            self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])
        v = o.call(Block(8 * 3 * 32)).tolist()
        for i in xrange(32):
            self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])
        v = o.call(Block(8 * 3 * 32)).tolist()
        for i in xrange(32):
            self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])

    def test_0c(self):
        shapereg = VersionReg(value = 0x0c)
        periodreg = Reg(value = 3)
        o = EnvOsc(8, periodreg, shapereg)
        for _ in xrange(2):
            v = o.call(Block(8 * 3 * 32)).tolist()
            for i in xrange(32):
                self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])

    def test_0e(self):
        shapereg = VersionReg(value = 0x0e)
        periodreg = Reg(value = 3)
        o = EnvOsc(8,periodreg, shapereg)
        v = o.call(Block(8 * 3 * 32)).tolist()
        for i in xrange(32):
            self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])
        v = o.call(Block(8 * 3 * 32)).tolist()
        for i in xrange(32):
            self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])
        v = o.call(Block(8 * 3 * 32)).tolist()
        for i in xrange(32):
            self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])

    def test_0f(self):
        for shape in xrange(0x04, 0x08):
            o = EnvOsc(8, Reg(value = 3), VersionReg(value = shape))
            v = o.call(Block(8 * 3 * 32)).tolist()
            for i in xrange(32):
                self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])
            self.assertEqual([0] * (8 * 3 * 34), o.call(Block(8 * 3 * 34)).tolist())

if '__main__' == __name__:
    unittest.main()
