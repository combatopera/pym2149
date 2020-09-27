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

from .dosound import issleepcommand
import itertools, re

class Line:

    # Does not support quoted whitespace, but we're only interested in numbers:
    pattern = re.compile(r'^(\S+)?(?:\s+(\S+)(?:\s+(\S+))?)?')

    def __init__(self, line):
        self.label, self.directive, self.argstext = self.pattern.search(line).groups()

class Label:

    def __init__(self, bytecode, index):
        self.bytecode = bytecode
        self.index = index

    def __iter__(self):
        return itertools.islice(self.bytecode, self.index, None)

def readlabeltobytecode(f):
    labels = {}
    bytecode = BytecodeBuilder(True)
    for line in map(Line, f):
        if line.label is not None:
            labels[line.label] = bytecode.startingnow() # Last one wins.
        if line.directive is not None:
            bytecode.process(line)
    return labels

class NoSuchLabelException(Exception): pass

def readbytecode(f, findlabel):
    bytecode = None
    for line in map(Line, f):
        if bytecode is None and findlabel == line.label: # XXX: Support terminating colon?
            bytecode = BytecodeBuilder(False) # And fall through to next clause if there is a directive.
        if bytecode is not None and line.directive is not None:
            bytecode.process(line)
            if bytecode.hasterminator():
                break
    if bytecode is None:
        raise NoSuchLabelException(findlabel)
    return bytecode.bytes

class UnsupportedDirectiveException(Exception): pass

class BytecodeBuilder:

    @staticmethod
    def number(s):
        if s[0] == '%':
            return int(s[1:], 2)
        elif s[0] == '$':
            return int(s[1:], 16)
        else:
            return int(s) # XXX: Could it be octal?

    def __init__(self, aligned):
        self.bytes = []
        self.aligned = aligned

    def startingnow(self):
        return Label(self.bytes, len(self.bytes))

    def process(self, line):
        key = line.directive.lower()
        if self.aligned and 'even' == key:
            if len(self.bytes) & 1:
                self.bytes.append(0) # May be used as value by accident.
        elif 'dc.w' == key:
            self.bytes.extend([None, None]) # Unknown endianness.
        elif 'dc.b' == key:
            self.bytes.extend(map(self.number, line.argstext.split(',')))
        else:
            raise UnsupportedDirectiveException(line.directive)

    def hasterminator(self):
        # TODO LATER: Support termination not just at end of line.
        return len(self.bytes) >= 2 and not self.bytes[-1] and issleepcommand(self.bytes[-2])
