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

import bisect, numpy as np

class BaseSection:

    def __init__(self, initial):
        self.initial = initial

class FlatSection(BaseSection):

    def getvalue(self, frame, xadjust):
        return self.initial

    def unbiased(self, frame):
        return self.getvalue(frame, 0)

    def wrap(self, perframe):
        pass

class Section(BaseSection):

    def getvalue(self, frame, xadjust):
        return self.initial + frame * self.perframe

    def unbiased(self, frame):
        return self.getvalue(frame, 0)

    def wrap(self, perframe):
        self.perframe = perframe

class BiasSection(BaseSection):

    def getvalue(self, frame, xadjust):
        return self.initial + frame * self.perframe + self.bias

    def unbiased(self, frame):
        return self.initial + frame * self.perframe

    def wrap(self, perframe):
        self.bias = float(np.sign(perframe)) / -2
        self.perframe = perframe

class Sections:

    def __init__(self):
        self.frames = [] # First is always 0, but it's convenient.
        self.sections = []
        self.len = 0

    def add(self, width, section):
        self.frames.append(self.len)
        self.sections.append(section)
        self.len += width # TODO LATER: Error accumulation.

    def init(self, sections, initials):
        self.frames = sections.frames.copy()
        self.sections = [type(s)(i) for s, i in zip(sections.sections, initials)]
        self.len = sections.len
        n = len(self.sections)
        for i in range(n):
            s = self.sections[i]
            if i + 1 < n:
                t = self.sections[i + 1]
                tframes = self.frames[i + 1]
            else:
                t = self.sections[0]
                tframes = self.len
            s.perframe = (t.initial - s.initial) / (tframes - self.frames[i])

    def empty(self):
        return not self.frames

    def at(self, index):
        return self.frames[index], self.sections[index]

    def forframe(self, absframe, xadjust):
        relframe = absframe % self.len
        sectionframe, section = self.at(bisect.bisect(self.frames, relframe) - 1)
        return section.getvalue(relframe - sectionframe, absframe - relframe + xadjust)

class Operators:

    def __getitem__(self, frame):
        return Slice(self, frame) if isinstance(frame, slice) else self.getitem(frame, 0)

    def __add__(self, that):
        return Sum(self, that)

    def __sub__(self, that):
        return Diff(self, that)

    def __mul__(self, that):
        return self.mulcls(self, that)

    def __and__(self, that):
        return Merge(self, that)

    def __or__(self, that):
        return Then(self, that, self, that)

    def __lshift__(self, frames):
        return self >> -frames

    def __rshift__(self, frames):
        return RShift(self, frames)

    def of(self, beat):
        return Of(self, beat)

    def inversions(self):
        degreetoindex = {}
        degrees = []
        refs = []
        for s in self.sections.sections:
            degree = tuple(s.initial[1:])
            if degree in degreetoindex:
                index = degreetoindex[degree]
            else:
                degreetoindex[degree] = index = len(degrees)
                degrees.append(np.array((0,) + degree))
            refs.append((index, s.initial[0]))
        invs = []
        for _ in range(len(degrees)):
            sections = Sections()
            sections.init(self.sections, (degrees[index] + np.array([octave, 0, 0]) for index, octave in refs))
            invs.append(type(self)(sections, self.kwargs))
            degrees.append(degrees.pop(0) + np.array([1, 0, 0]))
        return invs

    def apply(self, speed, frame, chip, context):
        self.of(speed)[frame](frame, speed, chip, self.kwargs, context)

class EventSection:

    def __init__(self, relframe, onframes, note, namespace):
        self.relframe = relframe
        self.onframes = onframes
        self.note = note
        self.namespace = namespace

    def getvalue(self, frame, xadjust):
        return Event(xadjust + self.relframe, self.onframes, self.note, self.namespace)

class Event:

    def __init__(self, absframe, onframes, note, namespace):
        self.absframe = absframe
        self.onframes = onframes
        self.note = note
        self.namespace = namespace

    def __call__(self, frame, speed, chipproxy, kwargs, context):
        note = self.note.new() # XXX: Allow a note to maintain state?
        def noteargs(params, shift, **extras):
            for name in params:
                if name in extras:
                    yield name, extras[name]
                elif 'frame' == name:
                    yield name, frame - self.absframe * speed + shift
                else:
                    key = self.namespace, name
                    if key in kwargs:
                        yield name, (kwargs[key] >> -self.absframe).of(speed) >> shift
        if self.onframes is None:
            if self.note.onparams is not None:
                note.on(**dict(noteargs(self.note.onparams, 0, context = context, chip = chipproxy)))
        else:
            if self.note.offparams is not None:
                onframes = self.onframes * speed
                note.off(**dict(noteargs(self.note.offparams, onframes, context = context, chip = chipproxy, onframes = onframes)))

class Overlay:

    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, *args):
        for e in self.e1, self.e2:
            e(*args)

class Binary(Operators):

    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

class Sum(Binary):

    kwargs = {} # XXX: Can this ever have kwargs? Or replace with bundle mechanism.

    @property
    def len(self):
        return max(self.p1.len, self.p2.len)

    def getitem(self, frame, shift):
        return self.p1.getitem(frame, shift) + self.p2.getitem(frame, shift)

class Diff(Binary):

    @property
    def len(self):
        return max(self.p1.len, self.p2.len)

    def getitem(self, frame, shift):
        return self.p1.getitem(frame, shift) - self.p2.getitem(frame, shift)

class Mul(Binary):

    @property
    def len(self):
        return max(self.p1.len, self.p2.len)

    def getitem(self, frame, shift):
        return self.p1.getitem(frame, shift) * self.p2.getitem(frame, shift)

class Merge(Binary):

    @property
    def mulcls(self):
        mulcls, = set(p.mulcls for p in [self.p1, self.p2])
        return mulcls

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.len = max(self.p1.len, self.p2.len)
        self.kwargs = {**self.p1.kwargs, **self.p2.kwargs}

    def getitem(self, frame, shift):
        x = self.p1.getitem(frame, shift)
        y = self.p2.getitem(frame, shift)
        return Overlay(x, y)

class RShift(Operators):

    @property
    def mulcls(self):
        return self.p.mulcls

    @property
    def kwargs(self):
        return self.p.kwargs

    @property
    def len(self):
        return self.p.len

    def __init__(self, p, frames):
        self.p = p
        self.frames = frames

    def getitem(self, frame, shift):
        return self.p.getitem(frame, self.frames + shift)

class Repeat(Operators):

    @property
    def mulcls(self):
        return self.p.mulcls

    @property
    def kwargs(self):
        return self.p.kwargs

    def __init__(self, p, times):
        self.len = p.len * times
        self.p = p
        self.times = times

    def getitem(self, frame, shift):
        return self.p.getitem(frame, shift)

class Of(Operators):

    kwargs = {} # TODO: Implement.

    @property
    def len(self):
        return self.p.len * self.beat

    @property
    def mulcls(self):
        return self.p.mulcls

    def __init__(self, p, beat):
        self.p = p
        self.beat = beat

    def getitem(self, frame, shift):
        return self.p.getitem(frame / self.beat, shift / self.beat)

class Concat(Binary):

    kwargs = {} # TODO LATER: Implement.

    @property
    def len(self):
        return self.p1.len + self.p2.len

    @property
    def mulcls(self):
        mulcls, = set(p.mulcls for p in [self.p1, self.p2])
        return mulcls

    def getitem(self, frame, shift):
        split = self.p1.sections.len
        if frame - shift < split:
            return self.p1.getitem(frame, shift)
        else:
            return self.p2.getitem(frame, shift + split)

class Then(Binary):

    @property
    def mulcls(self):
        mulcls, = set(p.mulcls for p in [self.p1, self.p2])
        return mulcls

    @property
    def len(self):
        return self.len1.len + self.len2.len

    def __init__(self, p1, p2, len1, len2):
        super().__init__(p1, p2)
        self.kwargs = {name: Then(
            p1.kwargs.get(name, p2.kwargs.get(name)),
            p2.kwargs.get(name, p1.kwargs.get(name)),
            len1,
            len2,
        ) for name in p1.kwargs.keys() | p2.kwargs.keys()}
        self.len1 = len1
        self.len2 = len2

    def getitem(self, frame, shift):
        split = self.len1.len
        total = split + self.len2.len
        loop = (frame - shift) // total
        if (frame - shift) % total < split:
            return self.p1.getitem(frame, shift + self.len2.len * loop)
        else:
            return self.p2.getitem(frame, shift + self.len1.len * (1 + loop))

class Slice(Operators):

    @property
    def mulcls(self):
        return self.p.mulcls

    def __init__(self, p, slice):
        def readslice(ref, adj):
            return ref if adj is None else (ref + adj if adj < 0 else adj)
        self.start = readslice(0, slice.start)
        self.stop = readslice(p.len, slice.stop)
        # TODO: Use step.
        self.len = self.stop - self.start
        self.kwargs = {name: Slice(v, slice) for name, v in p.kwargs.items()}
        self.p = p

    def getitem(self, frame, shift):
        loop = (frame - shift) // self.len
        return self.p.getitem(frame, shift - self.start - (self.p.len - self.len) * loop)
