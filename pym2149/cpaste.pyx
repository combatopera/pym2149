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
  cdef np.float32_t [::1] outv = out
  cdef np.float32_t [::1] demultiplexedv = demultiplexed
  cdef np.float32_t [::1] ampv = amp
  cdef np.int32_t [::1] naivex2outxv = naivex2outx
  cdef np.int32_t [::1] naivex2offv = naivex2off
  cdef np.float32_t* outp = &outv[0]
  cdef np.float32_t* demultiplexedp = &demultiplexedv[0]
  cdef np.float32_t* ampp = &ampv[0]
  cdef np.int32_t* naivex2outxp = &naivex2outxv[0]
  cdef np.int32_t* naivex2offp = &naivex2offv[0]
  cdef unsigned int ampindex = 0
  cdef unsigned int out0 = naivex2outxp[naivex]
  cdef np.float32_t dclevel = 0
  cdef unsigned int dcindex = 0
  cdef unsigned int ampchunk
  cdef unsigned int limit
  cdef np.float32_t a
  cdef unsigned int i
  cdef unsigned int dccount
  cdef unsigned int s
  while ampsize:
    ampchunk = min(ampsize, naiverate - naivex)
    limit = naivex + ampchunk
    while naivex < limit:
      a = ampp[ampindex]
      if a:
        i = naivex2outxp[naivex] - out0
        dccount = i + mixinsize - dcindex
        for UNROLL in xrange(dccount):
            outp[dcindex] += dclevel
            dcindex += 1
        s = naivex2offp[naivex]
        for UNROLL in xrange(gmixinsize):
            outp[i] += demultiplexedp[s] * a
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
  for UNROLL in xrange(dccount):
      outp[dcindex] += dclevel
      dcindex += 1
