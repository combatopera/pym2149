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
def pasteminbleps(unsigned int ampsize, np.ndarray[np.float32_t] out, np.ndarray[np.int32_t] naivex2outx, unsigned int outsize, np.ndarray[np.float32_t] demultiplexed, np.ndarray[np.int32_t] naivex2off, np.ndarray[np.float32_t] amp, unsigned int naivex, unsigned int naiverate, unsigned int outrate, unsigned int mixinsize):
  # TODO: This code needs tests.
  cdef unsigned int ampindex = 0
  cdef unsigned int out0 = naivex2outx[naivex]
  cdef float dclevel = 0
  cdef unsigned int dcindex = 0
  cdef unsigned int ampchunk
  cdef unsigned int limit
  cdef float a
  cdef unsigned int i
  cdef unsigned int dccount
  cdef unsigned int s
  while ampsize:
    ampchunk = min(ampsize, naiverate - naivex)
    limit = naivex + ampchunk
    while naivex < limit:
      a = amp[ampindex]
      if a:
        i = naivex2outx[naivex] - out0
        dccount = i + mixinsize - dcindex
        for _ in xrange(dccount):
            out[dcindex] += dclevel
            dcindex += 1
        s = naivex2off[naivex]
        for _ in xrange(mixinsize):
            out[i] += demultiplexed[s] * a
            # XXX: Do we really need 2 increments?
            i += 1
            s += 1
        dclevel += a
      ampindex += 1
      naivex += 1
    ampsize = ampsize - ampchunk
    naivex = 0
    out0 = out0 - outrate
  dccount = outsize - dcindex
  for _ in xrange(dccount):
      out[dcindex] += dclevel
      dcindex += 1
