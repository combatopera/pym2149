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

import os, re

pattern = re.compile(r'^(\s*)for\s+UNROLL\s+in\s+xrange\s*\(\s*([^\s]+)\s*\)\s*:\s*$')
indentregex = re.compile(r'^\s*')
maxchunk = 0x80

def unroll(frompath, topath, **kwargs):
    f = open(os.path.join(os.path.dirname(__file__), frompath))
    try:
        g = open(os.path.join(os.path.dirname(__file__), topath), 'w')
        try:
            unrollimpl(f, g, kwargs)
            g.flush()
        finally:
            g.close()
    finally:
        f.close()

def unrollimpl(f, g, options):
    for name, value in options.iteritems():
        print >> g, "%s = %r" % (name, value)
    buffer = []
    while True:
        line = buffer.pop(0) if buffer else f.readline()
        if not line:
            break
        m = pattern.search(line)
        if m is None:
            g.write(line)
            continue
        outerindent = m.group(1)
        variable = m.group(2)
        line = f.readline()
        m = indentregex.search(line)
        innerindent = m.group()
        body = []
        while line.startswith(innerindent):
            body.append(line)
            line = f.readline()
        buffer.append(line)
        if variable in options:
            for _ in xrange(options[variable]):
                for line in body:
                    g.write(outerindent + line[len(innerindent):])
        else:
            mask = 0x01
            while mask < maxchunk:
                print >> g, "%sif %s & 0x%x:" % (outerindent, variable, mask)
                for _ in xrange(mask):
                    for line in body:
                        g.write(line)
                mask <<= 1
            print >> g, "%swhile %s >= 0x%x:" % (outerindent, variable, maxchunk)
            for _ in xrange(maxchunk):
                for line in body:
                    g.write(line)
            print >> g, "%s%s -= 0x%x" % (innerindent, variable, maxchunk)
