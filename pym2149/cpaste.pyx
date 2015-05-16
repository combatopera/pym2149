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

cimport numpy as np
import cython

@cython.boundscheck(False)
def pasteminbleps(unsigned int ampsize, np.ndarray[np.float32_t] out, np.ndarray[np.int32_t] naivex2outx, unsigned int outsize, np.ndarray[np.float32_t] demultiplexed, np.ndarray[np.int32_t] naivex2off, np.ndarray[np.float32_t] amp, unsigned int naivex, unsigned int naiverate, unsigned int outrate):
  # TODO: This code needs tests.
  cdef unsigned int mixinsize = gmixinsize
  cdef np.float32_t* outp = &out[0]
  cdef np.float32_t* demultiplexedp = &demultiplexed[0]
  cdef np.float32_t* ampp = &amp[0]
  cdef np.int32_t* naivex2outxp = &naivex2outx[0]
  cdef np.int32_t* naivex2offp = &naivex2off[0]
  cdef unsigned int out0 = naivex2outxp[naivex]
  cdef np.float32_t dclevel = 0
  cdef unsigned int dcindex = 0
  cdef unsigned int ampchunk
  cdef np.float32_t a
  cdef unsigned int i
  cdef unsigned int dccount
  cdef np.float32_t* mixinp
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
          for UNROLL in xrange(gmixinsize):
            outp[0] += mixinp[0] * a + dclevel
            outp += 1
            mixinp += 1
        else: # The mixin starts before the pending DC adjustment.
          dccount = i + mixinsize - dcindex
          for UNROLL in xrange(dccount):
            outp[0] += dclevel
            outp += 1
          outp -= mixinsize
          for UNROLL in xrange(gmixinsize):
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
