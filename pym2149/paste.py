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

import numpy as np
from pyrbo import turbo, X

mixinsize = None

@turbo(ampsize = np.uint32, outp = [np.float32], naivex2outxp = [np.int32], outsize = np.uint32, demultiplexedp = [np.float32], naivex2offp = [np.int32], ampp = [np.float32], naivex = np.uint32, naiverate = np.uint32, outrate = np.uint32, out0 = np.uint32, dclevel = np.float32, dcindex = np.uint32, ampchunk = np.uint32, a = np.float32, i = np.uint32, dccount = np.uint32, mixinp = [np.float32], mixinsize = X)
def pasteminbleps(ampsize, outp, naivex2outxp, outsize, demultiplexedp, naivex2offp, ampp, naivex, naiverate, outrate):
  # TODO: This code needs tests.
  out0 = naivex2outxp[naivex]
  dclevel = 0
  dcindex = 0
  while ampsize:
    ampchunk = min(ampsize, naiverate - naivex)
    for naivex in xrange(naivex, naivex + ampchunk):
      a = ampp[0]
      ampp += 1
      if a:
        i = naivex2outxp[naivex] - out0
        mixinp = demultiplexedp + naivex2offp[naivex]
        if dcindex <= i: # We can DC-adjust while pasting this mixin.
          dccount = i - dcindex
          for UNROLL in xrange(dccount):
            outp[0] += dclevel
            outp += 1
          for UNROLL in xrange(mixinsize):
            outp[0] += mixinp[0] * a + dclevel
            outp += 1
            mixinp += 1
        else: # The mixin starts before the pending DC adjustment.
          dccount = i + mixinsize - dcindex
          for UNROLL in xrange(dccount):
            outp[0] += dclevel
            outp += 1
          outp -= mixinsize
          for UNROLL in xrange(mixinsize):
            outp[0] += mixinp[0] * a
            outp += 1
            mixinp += 1
        dcindex = i + mixinsize
        dclevel += a
    ampsize -= ampchunk
    naivex = 0
    out0 -= outrate
  dccount = outsize - dcindex
  for UNROLL in xrange(dccount):
    outp[0] += dclevel
    outp += 1
