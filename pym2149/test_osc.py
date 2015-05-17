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
from osc import ToneOsc, NoiseDiffs, NoiseOsc, EnvOsc, RationalDiff, RToneOsc
from mfp import mfpclock
from nod import Block, BufNode
from reg import VersionReg
from buf import DiffRing, RingCursor, Buf
from lfsr import Lfsr
from ym2149 import ym2149nzdegrees
from shapes import tonediffs, loopsize
from dac import pwmeffect

def Reg(value):
    r = VersionReg()
    r.value = value
    return r

class Timer:

    def __init__(self, xform, that):
        self.xform = xform
        self.that = that
        self.effect = Reg(pwmeffect)

    def isrunning(self): return True

    def getstepsize(self):
        return self.xform(self.that.value)

class TestToneOsc(unittest.TestCase):

    performancelimit = .05

    @staticmethod
    def createosc(scale, periodreg):
        return ToneOsc(scale, periodreg)

    def test_works(self):
        o = self.createosc(8, Reg(3))
        v = o.call(Block(96)).tolist()
        self.assertEqual([1] * 24, v[:24])
        self.assertEqual([0] * 24, v[24:48])
        self.assertEqual([1] * 24, v[48:72])
        self.assertEqual([0] * 24, v[72:])
        v = o.call(Block(48)).tolist()
        self.assertEqual([1] * 24, v[:24])
        self.assertEqual([0] * 24, v[24:])

    def test_resume(self):
        o = self.createosc(8, Reg(3))
        v = o.call(Block(25)).tolist()
        self.assertEqual([1] * 24, v[:24])
        self.assertEqual([0], v[24:])
        v = o.call(Block(24)).tolist()
        self.assertEqual([0] * 23, v[:23])
        self.assertEqual([1], v[23:])

    def test_carry(self):
        r = Reg(0x01)
        size = 3 * 8 + 1
        ref = self.createosc(8, r).call(Block(size)).tolist()
        for n in xrange(size + 1):
            o = self.createosc(8, r)
            v1 = o.call(Block(n)).tolist()
            v2 = o.call(Block(size - n)).tolist()
            self.assertEqual(ref, v1 + v2)

    def test_endexistingstepatendofblock(self):
        r = Reg(0x01)
        o = self.createosc(8, r)
        self.assertEqual([1] * 4, o.call(Block(4)).tolist())
        self.assertEqual([1] * 4, o.call(Block(4)).tolist())
        self.assertEqual([0] * 4, o.call(Block(4)).tolist())

    def test_increaseperiodonboundary(self):
        r = Reg(0x01)
        o = self.createosc(8, r)
        self.assertEqual([1] * 8 + [0] * 8, o.call(Block(16)).tolist())
        r.value = 0x02
        self.assertEqual([1] * 16 + [0] * 15, o.call(Block(31)).tolist())
        r.value = 0x03
        self.assertEqual([0] * 9 + [1] * 24 + [0], o.call(Block(34)).tolist())

    def test_decreaseperiodonboundary(self):
        r = Reg(0x03)
        o = self.createosc(8, r)
        self.assertEqual([1] * 24 + [0] * 24, o.call(Block(48)).tolist())
        r.value = 0x02
        self.assertEqual([1] * 16 + [0] * 16 + [1] * 6, o.call(Block(38)).tolist())
        r.value = 0x01
        self.assertEqual([1] * 2 + [0] * 8 + [1] * 8 + [0], o.call(Block(19)).tolist())

    def test_smallerblocksthanperiod(self):
        r = Reg(0x05)
        o = self.createosc(1, r)
        self.assertEqual([1,1,1,1], o.call(Block(4)).tolist())
        self.assertEqual([1,0,0,0], o.call(Block(4)).tolist())
        self.assertEqual([0,0,1], o.call(Block(3)).tolist())
        self.assertEqual([1,1,1,1], o.call(Block(4)).tolist())
        self.assertEqual([0,0,0,0,0], o.call(Block(5)).tolist())
        self.assertEqual([1], o.call(Block(1)).tolist())

    def test_performance(self):
        blockrate = 50
        blocksize = 2000000 // blockrate
        for p in 0x001, 0xfff:
            r = Reg(p)
            o = self.createosc(8, r)
            start = time.time()
            for _ in xrange(blockrate):
                o.call(Block(blocksize))
            cmptime(self, time.time() - start, self.performancelimit)

def cmptime(self, taken, strictlimit):
    expression = "%.3f < %s" % (taken, strictlimit)
    sys.stderr.write("%s ... " % expression)
    self.assertTrue(eval(expression))

class TestRToneOsc(TestToneOsc): # FIXME: MFP timers do not behave like YM2149 tones.

    performancelimit = .1

    @staticmethod
    def createosc(scale, periodreg):
        clock = 200
        xform = lambda period: scale * period * mfpclock // clock
        return RToneOsc(clock, Timer(xform, periodreg))

def diffblock(d, n):
    v = Buf(np.empty(n, dtype = int))
    d.call(Block(n))(v)
    return v.tolist()

class TestRationalDiff(unittest.TestCase):

    class Timer:

        def __init__(self, running, value):
            self.running = running
            self.value = value

        def isrunning(self): return self.running

        def getstepsize(self):
            return self.value

    def test_works(self):
        p = self.Timer(True, 81920)
        d = RationalDiff(RationalDiff.bindiffdtype, 100, p).reset(tonediffs)
        expected = [1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0] * 4
        for _ in xrange(13):
            self.assertEqual(expected, diffblock(d, 80))
        actual = []
        expected = [1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0] * 5
        def block(n):
            actual.extend(diffblock(d, n))
        for _ in xrange(33):
            block(3)
        block(1)
        self.assertEqual(expected, actual)

    def test_notrunning(self):
        p = self.Timer(False, None)
        d = RationalDiff(RationalDiff.bindiffdtype, 1000, p).reset(tonediffs)
        for _ in xrange(50):
            self.assertEqual([1] * 100, diffblock(d, 100))
        self.assertEqual(5000*mfpclock, d.progress)
        p.running = True
        p.value = 24576
        self.assertEqual([0] * 10 + [1] * 10 + [0] * 5, diffblock(d, 25))
        self.assertEqual(5*mfpclock, d.progress)
        p.running = False
        p.value = None
        self.assertEqual([0] * 25, diffblock(d, 25))
        self.assertEqual(30*mfpclock, d.progress)

class TestNoiseOsc(unittest.TestCase):

    noisediffs = NoiseDiffs(ym2149nzdegrees)

    def test_works(self):
        n = 100
        o = NoiseOsc(8, Reg(3), self.noisediffs)
        u = Lfsr(ym2149nzdegrees)
        for _ in xrange(2):
            v = o.call(Block(48 * n)).tolist()
            for i in xrange(n):
                self.assertEqual([u()] * 48, v[i * 48:(i + 1) * 48])

    def test_carry(self):
        r = Reg(0x01)
        size = 17 * 16 + 1
        ref = NoiseOsc(8, r, self.noisediffs).call(Block(size)).tolist()
        for n in xrange(size + 1):
            o = NoiseOsc(8, r, self.noisediffs)
            v1 = o.call(Block(n)).tolist()
            v2 = o.call(Block(size - n)).tolist()
            self.assertEqual(ref, v1 + v2)

    def test_increaseperiodonboundary(self):
        r = Reg(0x01)
        o = NoiseOsc(4, r, self.noisediffs)
        o.diff.ringcursor = RingCursor(DiffRing([1, 0], 0, BufNode.bindiffdtype))
        self.assertEqual([1] * 8 + [0] * 8, o.call(Block(16)).tolist())
        r.value = 0x02
        self.assertEqual([1] * 16 + [0] * 15, o.call(Block(31)).tolist())
        r.value = 0x03
        self.assertEqual([0] + [1] * 24 + [0], o.call(Block(26)).tolist())

    def test_decreaseperiodonboundary(self):
        r = Reg(0x03)
        o = NoiseOsc(4, r, self.noisediffs)
        o.diff.ringcursor = RingCursor(DiffRing([1, 0], 0, BufNode.bindiffdtype))
        self.assertEqual([1] * 24 + [0] * 24, o.call(Block(48)).tolist())
        r.value = 0x02
        self.assertEqual([1] * 16 + [0] * 16 + [1] * 6, o.call(Block(38)).tolist())
        r.value = 0x01
        self.assertEqual([1] * 10 + [0] * 8 + [1] * 8 + [0], o.call(Block(27)).tolist())

    def test_performance(self):
        blockrate = 50
        blocksize = 2000000 // blockrate
        for p in 0x01, 0x1f:
            r = Reg(p)
            o = NoiseOsc(8, r, self.noisediffs)
            start = time.time()
            for _ in xrange(blockrate):
                o.call(Block(blocksize))
            cmptime(self, time.time() - start, .05)

class TestEnvOsc(unittest.TestCase):

    def test_diffs(self):
        v = EnvOsc.diffs0c
        self.assertEqual(1 + loopsize, v.buf.shape[0])
        self.assertEqual(1, v.loopstart)
        self.assertEqual(range(32) + range(32), list(np.cumsum(v.buf[:64])))
        v = EnvOsc.diffs08
        self.assertEqual(loopsize, v.buf.shape[0])
        self.assertEqual(0, v.loopstart)
        self.assertEqual(range(31, -1, -1) + range(31, -1, -1), list(np.cumsum(v.buf[:64])))
        v = EnvOsc.diffs0e
        self.assertEqual(loopsize, v.buf.shape[0])
        self.assertEqual(0, v.loopstart)
        self.assertEqual(range(32) + range(31, -1, -1) + range(32), list(np.cumsum(v.buf[:96])))
        v = EnvOsc.diffs0a
        self.assertEqual(1 + loopsize, v.buf.shape[0])
        self.assertEqual(1, v.loopstart)
        self.assertEqual(range(31, -1, -1) + range(32) + range(31, -1, -1), list(np.cumsum(v.buf[:96])))
        v = EnvOsc.diffs0f
        self.assertEqual(33 + loopsize, v.buf.shape[0])
        self.assertEqual(33, v.loopstart)
        self.assertEqual(range(32) + [0] * 32, list(np.cumsum(v.buf[:64])))
        v = EnvOsc.diffs0d
        self.assertEqual(32 + loopsize, v.buf.shape[0])
        self.assertEqual(32, v.loopstart)
        self.assertEqual(range(32) + [31] * 32, list(np.cumsum(v.buf[:64])))
        v = EnvOsc.diffs0b
        self.assertEqual(33 + loopsize, v.buf.shape[0])
        self.assertEqual(33, v.loopstart)
        self.assertEqual(range(31, -1, -1) + [31] * 32, list(np.cumsum(v.buf[:64])))
        v = EnvOsc.diffs09
        self.assertEqual(32 + loopsize, v.buf.shape[0])
        self.assertEqual(32, v.loopstart)
        self.assertEqual(range(31, -1, -1) + [0] * 32, list(np.cumsum(v.buf[:64])))

    def test_reset(self):
        shapereg = Reg(0x0c)
        periodreg = Reg(0x0001)
        o = EnvOsc(8, periodreg, shapereg)
        self.assertEqual(range(32) + range(16), o.call(Block(48 * 8)).tolist()[::8])
        self.assertEqual(range(16, 32) + range(16), o.call(Block(32 * 8)).tolist()[::8])
        shapereg.value = 0x0c
        self.assertEqual(range(32) + range(16), o.call(Block(48 * 8)).tolist()[::8])

    def test_08(self):
        shapereg = Reg(0x08)
        periodreg = Reg(3)
        o = EnvOsc(8, periodreg, shapereg)
        for _ in xrange(2):
            v = o.call(Block(8 * 3 * 32)).tolist()
            for i in xrange(32):
                self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])

    def test_09(self):
        for shape in xrange(0x04):
            o = EnvOsc(8, Reg(3), Reg(shape))
            v = o.call(Block(8 * 3 * 32)).tolist()
            for i in xrange(32):
                self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])
            self.assertEqual([0] * (8 * 3 * 34), o.call(Block(8 * 3 * 34)).tolist())

    def test_09loop(self):
        o = EnvOsc(1, Reg(1), Reg(0x09))
        self.assertEqual(range(31, -1, -1), o.call(Block(32)).tolist())
        m = loopsize - 10
        self.assertEqual([0] * m, o.call(Block(m)).tolist())
        self.assertEqual([0] * 20, o.call(Block(20)).tolist())

    def test_0a(self):
        shapereg = Reg(0x0a)
        periodreg = Reg(3)
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
        shapereg = Reg(0x0c)
        periodreg = Reg(3)
        o = EnvOsc(8, periodreg, shapereg)
        for _ in xrange(2):
            v = o.call(Block(8 * 3 * 32)).tolist()
            for i in xrange(32):
                self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])

    def test_0e(self):
        shapereg = Reg(0x0e)
        periodreg = Reg(3)
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
            o = EnvOsc(8, Reg(3), Reg(shape))
            v = o.call(Block(8 * 3 * 32)).tolist()
            for i in xrange(32):
                self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])
            self.assertEqual([0] * (8 * 3 * 34), o.call(Block(8 * 3 * 34)).tolist())

if '__main__' == __name__:
    unittest.main()
