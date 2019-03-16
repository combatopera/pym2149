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

from .dosound import issleepcommand
import re, itertools

# Does not support quoted whitespace, but we're only interested in numbers:
pattern = re.compile(r'^(\S+)?(?:\s+(\S+)(?:\s+(\S+))?)?')

class SourceException(Exception): pass

class Label:

    def __init__(self, bytecode, index):
        self.bytecode = bytecode
        self.index = index

    def __iter__(self):
        return itertools.islice(self.bytecode, self.index, None)

def lines(f):
    return (pattern.search(line).groups() for line in f)

def readlabeltobytecode(f):
    labels = {}
    bytecode = []
    for label, directive, argstext in lines(f):
        if label is not None:
            labels[label] = Label(bytecode, len(bytecode)) # Last one wins.
        if directive is not None:
            process(bytecode, directive, argstext, True)
    return labels

def readbytecode(f, findlabel):
    bytecode = None
    for label, directive, argstext in lines(f):
        if bytecode is None and findlabel == label: # XXX: Support terminating colon?
            bytecode = [] # And fall through to next clause if there is a directive.
        if bytecode is not None and directive is not None:
            process(bytecode, directive, argstext)
            # TODO LATER: Support termination not just at end of line.
            if len(bytecode) >= 2 and not bytecode[-1] and issleepcommand(bytecode[-2]):
                break
    if bytecode is None:
        raise SourceException("Label not found: %s" % findlabel)
    return bytecode

def process(bytecode, directive, argstext, startedeven = False):
    key = directive.lower()
    if startedeven and 'even' == key:
        if len(bytecode) & 1:
            bytecode.append(0) # May be used as value by accident.
    elif 'dc.w' == key:
        bytecode.extend([None, None]) # Unknown endianness.
    elif 'dc.b' == key:
        bytecode.extend(map(number, argstext.split(',')))
    else:
        raise SourceException("Unsupported directive: %s" % directive)

def number(s):
    if s[0] == '%':
        return int(s[1:], 2)
    elif s[0] == '$':
        return int(s[1:], 16)
    else:
        return int(s) # XXX: Could it be octal?
