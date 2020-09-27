# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

from .buf import BufType
from .const import i4, i8, u1, u4, u8
from .nod import BufNode
from .shapes import Shape, signaldtype, toneshape
from pyrbo import LOCAL, turbo
import itertools, numpy as np

oscnodepyrbotype = dict(
    blockbuf = dict(buf = [signaldtype]),
    block = dict(framecount = u4),
    index = i4,
    shape = Shape.pyrbotype,
)

class ShapeOsc(BufNode):

    progressdtype = u4

    def __init__(self, scale, periodreg):
        super().__init__(BufType.signal)
        self.stepsize = 0 # XXX: Move to reset?
        self.scale = scale
        self.periodreg = periodreg

    def reset(self, shape):
        self.index = -1
        self.progress = np.iinfo(self.progressdtype).max
        self.shape = shape

    def callimpl(self):
        self.index, self.progress, self.stepsize = self.shapeimpl()

    @turbo(
        self = dict(
            oscnodepyrbotype,
            progress = progressdtype,
            stepsize = u4,
            scale = u4,
            periodreg = dict(value = u4),
            eager = u1,
        ),
        i = u4,
        j = u4,
        n = u4,
        val = signaldtype,
    )
    def shapeimpl(self):
        self_blockbuf_buf = self_block_framecount = self_index = self_progress = self_scale = self_periodreg_value = self_shape_buf = self_shape_size = self_shape_introlen = self_eager = LOCAL
        if self_eager:
            self_stepsize = self_periodreg_value * self_scale
        i = 0
        if self_progress < self_stepsize:
            val = self_shape_buf[self_index]
            j = min(self_stepsize - self_progress, self_block_framecount)
            while i < j:
                self_blockbuf_buf[i] = val
                i += 1
        if i == self_block_framecount:
            self_progress += self_block_framecount
        else:
            if not self_eager:
                self_stepsize = self_periodreg_value * self_scale
            n = (self_block_framecount - i) // self_stepsize
            while n:
                self_index += 1
                if self_index == self_shape_size:
                    self_index = self_shape_introlen
                val = self_shape_buf[self_index]
                j = i + self_stepsize
                while i < j:
                    self_blockbuf_buf[i] = val
                    i += 1
                n -= 1
            if i == self_block_framecount:
                self_progress = self_stepsize
            else:
                self_index += 1
                if self_index == self_shape_size:
                    self_index = self_shape_introlen
                val = self_shape_buf[self_index]
                self_progress = self_block_framecount - i
                while i < self_block_framecount:
                    self_blockbuf_buf[i] = val
                    i += 1
        return self_index, self_progress, self_stepsize

class IncompatibleShapeException(Exception): pass

class RToneOsc(BufNode):

    def __init__(self, mfpclock, chipimplclock, timer):
        super().__init__(BufType.signal)
        self.effectversion = None
        self.mfpclock = mfpclock
        self.chipimplclock = chipimplclock
        self.timer = timer

    def reset(self, shape):
        self.index = -1
        self.maincounter = 0
        self.precounterxmfp = None
        self.shape = shape

    def callimpl(self):
        if self.effectversion != self.timer.effect.version:
            self.reset(self.timer.effect.value.getshape())
            self.effectversion = self.timer.effect.version
        else:
            shape = self.timer.effect.value.getshape()
            if shape.size != self.shape.size or shape.introlen != self.shape.introlen:
                raise IncompatibleShapeException
            self.shape = shape
        prescalerornone = self.timer.prescalerornone.value
        if prescalerornone is None:
            self.blockbuf.fill_same(self.shape.buf[self.index])
            self.precounterxmfp = None
        else:
            if self.precounterxmfp is None:
                self.precounterxmfp = prescalerornone * self.chipimplclock
            self.index, self.maincounter, self.precounterxmfp = self.rtoneimpl(prescalerornone, self.timer.effectivedata.value)

    @turbo(
        self = dict(
            oscnodepyrbotype,
            mfpclock = i8, # Signed so j doesn't blow up.
            chipimplclock = u8,
            maincounter = i4,
            precounterxmfp = u4,
        ),
        prescaler = u4,
        etdr = u4,
        chunksizexmfp = u8,
        stepsizexmfp = u8,
        nextstepxmfp = i8,
        i = u4,
        j = u4,
        val = signaldtype,
    )
    def rtoneimpl(self, prescaler, etdr):
        self_blockbuf_buf = self_block_framecount = self_mfpclock = self_chipimplclock = self_index = self_maincounter = self_precounterxmfp = self_shape_buf = self_shape_size = self_shape_introlen = LOCAL
        chunksizexmfp = self_chipimplclock * prescaler
        stepsizexmfp = chunksizexmfp * etdr
        nextstepxmfp = chunksizexmfp * self_maincounter + self_precounterxmfp - chunksizexmfp
        i = 0
        while True:
            j = min((nextstepxmfp + self_mfpclock - 1) // self_mfpclock, self_block_framecount)
            val = self_shape_buf[self_index]
            while i < j:
                self_blockbuf_buf[i] = val
                i += 1
            if j == self_block_framecount:
                break
            nextstepxmfp += stepsizexmfp
            self_index += 1
            if self_index == self_shape_size:
                self_index = self_shape_introlen
        nextstepxmfp -= self_mfpclock * self_block_framecount
        self_maincounter = 1
        while nextstepxmfp < 0:
            nextstepxmfp += chunksizexmfp
            self_maincounter -= 1
        self_maincounter += nextstepxmfp // chunksizexmfp
        return self_index, self_maincounter, nextstepxmfp % chunksizexmfp

class ToneOsc(ShapeOsc):

    eager = True

    def __init__(self, scale, periodreg):
        scaleofstep = scale * 2 // 2 # Normally half of 16.
        super().__init__(scaleofstep, periodreg)
        self.reset(toneshape)

class NoiseOsc(ShapeOsc):

    eager = False

    def __init__(self, scale, periodreg, shape):
        scaleofstep = scale * 2 # This results in authentic spectrum, see qnoispec.
        super().__init__(scaleofstep, periodreg)
        self.reset(shape)

class EnvOsc(ShapeOsc):

    eager = True
    steps = 32
    shapes = {
        0x0c: Shape(range(steps)),
        0x08: Shape(range(steps - 1, -1, -1)),
        0x0e: Shape(itertools.chain(range(steps), range(steps - 1, -1, -1))),
        0x0a: Shape(itertools.chain(range(steps - 1, -1, -1), range(steps))),
        0x0f: Shape(itertools.chain(range(steps), steps * [0]), steps),
        0x0d: Shape(itertools.chain(range(steps), steps * [steps - 1]), steps),
        0x0b: Shape(itertools.chain(range(steps - 1, -1, -1), steps * [steps - 1]), steps),
        0x09: Shape(itertools.chain(range(steps - 1, -1, -1), steps * [0]), steps),
    }
    for s in range(0x08):
        shapes[s] = shapes[0x0f if s & 0x04 else 0x09]
    del s

    def __init__(self, scale, periodreg, shapereg):
        scaleofstep = scale * 32 // self.steps
        super().__init__(scaleofstep, periodreg)
        self.shapeversion = None
        self.shapereg = shapereg

    def callimpl(self):
        if self.shapeversion != self.shapereg.version:
            self.reset(self.shapes[self.shapereg.value])
            self.shapeversion = self.shapereg.version
        super().callimpl()
