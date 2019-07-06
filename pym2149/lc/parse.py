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

from .lc import Operators, Sections, FlatSection, BiasSection, Section, Concat, EventSection, Repeat, Mul
from diapyr.util import innerclass
import re, numpy as np, inspect, itertools

class Script(Operators):

    mulcls = Repeat

    def __init__(self, sections, kwargs):
        self.len = max(itertools.chain([sections.len], (s.len for s in kwargs.values())))
        self.sections = sections
        self.kwargs = kwargs

    def getitem(self, frame, shift):
        return self.sections.forframe(frame - shift, shift)

class StepScript(Script):

    mulcls = Mul

    def __init__(self, sections, kwargs, step):
        super().__init__(sections, kwargs)
        self.step = step

    def getitem(self, frame, shift):
        return Value(super().getitem(frame, shift) + (frame - shift) // self.sections.len * self.step)

class Value(float):

    def pick(self, sequence):
        return sequence[round(self)]

class BadWordException(Exception): pass

class Parse:

    def __call__(self, script, successor):
        session = self.Session()
        session.sections = Sections()
        for word in re.findall(r'[^\s|]+', script):
            session.parseword(word)
        session.wrap(successor)
        return session.sections

class VParse(Parse):

    pattern = re.compile('(?:([0-9.]+)x)?(-?[0-9.]+)?(#+|b+)?([+]+|-+)?(?:(/{1,2})([0-9.]+))?')

    def __init__(self, type, step, continuous):
        self.type = type
        self.step = step
        self.continuous = continuous

    @innerclass
    class Session:

        def parseword(self, word):
            m = self.pattern.fullmatch(word)
            if m is None:
                raise BadWordException(word)
            times = m.group(1)
            width = 1 if times is None else float(times)
            initial = m.group(2)
            initial = self.type() if initial is None else self.type(initial)
            acc = m.group(3)
            if acc is not None:
                initial[2] += (1 if '#' in acc else -1) * len(acc)
            octave = m.group(4)
            if octave is not None:
                initial[0] += (1 if '+' in octave else -1) * len(octave)
            bias = m.group(5)
            if bias is not None:
                bias = len(bias) - 1
            slash = m.group(6)
            slide = (width if self.continuous else 0) if slash is None else float(slash)
            if not self.sections.empty():
                self._wrap(initial)
            hold = width - slide
            if hold > 0:
                self.sections.add(hold, FlatSection(initial))
            if slide:
                self.sections.add(slide, (BiasSection if bias else Section)(initial))

        def wrap(self, successor):
            if successor is None:
                _, firstsection = self.sections.at(0)
                self._wrap(firstsection.initial + self.step)
            else:
                self._wrap(successor[0]) # TODO: Unit-test what effect step would have.

        def _wrap(self, value):
            lastframe, lastsection = self.sections.at(-1)
            lastsection.wrap((value - lastsection.initial) / (self.sections.len - lastframe))

def vector(d = None):
    return np.array([0, 0 if d is None else float(d) - 1, 0])

def concat(scriptcls, parser, script, kwargs):
    scripts = []
    successor = None
    for segment in reversed(script.split(',')):
        successor = scriptcls(parser(segment, successor), kwargs)
        scripts.insert(0, successor)
    return scripts[0] if 1 == len(scripts) else Concat(*scripts)

class EParse(Parse):

    pattern = re.compile('(?:([0-9]+)x)?(-?[0-9.]+)?(?:/([0-9.]+))?')

    def __init__(self, note, namespace):
        self.note = note
        self.namespace = namespace

    @innerclass
    class Session:

        def parseword(self, word):
            m = self.pattern.fullmatch(word)
            if m is None:
                raise BadWordException(word)
            times = m.group(1)
            count = 1 if times is None else int(times)
            if count < 1:
                raise BadWordException(word)
            width = m.group(2)
            width = 1 if width is None else float(width)
            slash = m.group(3)
            offwidth = 0 if slash is None else float(slash)
            onwidth = max(0, width - offwidth)
            for _ in range(count):
                if onwidth:
                    self.sections.add(onwidth, EventSection(self.sections.len, None, self.note, self.namespace))
                if offwidth:
                    self.sections.add(offwidth, EventSection(self.sections.len, onwidth, self.note, self.namespace))

        def wrap(self, successor):
            pass

class NoteWrapper:

    def __init__(self, cls, init):
        def params(name):
            try:
                unbound = getattr(cls, name)
            except AttributeError:
                return
            return list(itertools.islice(inspect.signature(unbound).parameters.keys(), 1, None))
        self.onparams = params('on')
        self.offparams = params('off')
        self.cls = cls
        self.init = init

    def new(self):
        return self.cls(*self.init)
