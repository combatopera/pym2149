# Copyright 2014, 2018 Andrzej Cichocki

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

import re

# Does not support quoted whitespace, but we're only interested in numbers:
pattern = re.compile(r'^([^\s]+)?\s+([^\s]+)?\s+([^\s]+)?')

def readbytecode(f, label):
  while True:
    line = f.readline()
    if not line:
      raise Exception("Label not found: %s" % label)
    groups = pattern.search(line).groups()
    if label == groups[0]: # XXX: Support terminating colon?
      break
  bytecode = []
  while True:
    if groups[1] is not None:
      if 'dc.b' != groups[1].lower():
        raise Exception("Unsupported directive: %s" % groups[1])
      for s in groups[2].split(','):
        if s[0] == '%':
          n = int(s[1:], 2)
        elif s[0] == '$':
          n = int(s[1:], 16)
        # XXX: Octal?
        else:
          n = int(s)
        bytecode.append(n)
      # TODO: Support termination not just at end of line.
      if len(bytecode) >= 2 and not bytecode[-1]:
        ctrl = bytecode[-2]
        if ctrl >= 0x82 and ctrl <= 0xff:
          break
    line = f.readline()
    if not line:
      raise Exception("Unterminated bytecode: %s" % bytecode)
    groups = pattern.search(line).groups()
  return bytecode
