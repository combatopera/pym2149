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

import logging, numba as nb

log = logging.getLogger(__name__)

def pasteminbleps(ampsize, out, naivex2outx, outsize, demultiplexed, naivex2off, amp, naivex, naiverate, outrate):
  pasteminblepsimpl(ampsize, out, naivex2outx, outsize, demultiplexed, naivex2off, amp, naivex, naiverate, outrate)

log.debug('Compiling output stage.')

@nb.jit(nb.void(nb.i4, nb.f4[:], nb.i4[:], nb.i4, nb.f4[:], nb.i4[:], nb.f4[:], nb.i4, nb.i4, nb.i4), nopython = True)
def pasteminblepsimpl(ampsize, out, naivex2outx, outsize, demultiplexed, naivex2off, amp, naivex, naiverate, outrate):
  # TODO: This code needs tests.
  # Naming constants makes inspect_types easier to read:
  zero = 0
  one = 1
  ampindex = zero
  out0 = naivex2outx[naivex]
  dclevel = nb.f4(0)
  dcindex = zero
  while ampsize:
    ampchunk = min(ampsize, naiverate - naivex)
    limit = naivex + ampchunk
    while naivex < limit:
      a = amp[ampindex]
      if a != zero:
        i = naivex2outx[naivex] - out0
        j = i + mixinsize
        dccount = j - dcindex
        for UNROLL in xrange(dccount):
            out[dcindex] += dclevel
            dcindex += one
        s = naivex2off[naivex]
        for UNROLL in xrange(mixinsize):
            out[i] += demultiplexed[s] * a
            # XXX: Do we really need 2 increments?
            i += one
            s += one
        dclevel += a
      ampindex += one
      naivex += one
    ampsize = ampsize - ampchunk
    naivex = zero
    out0 = out0 - outrate
  dccount = outsize - dcindex
  for UNROLL in xrange(dccount):
      out[dcindex] += dclevel
      dcindex += one

log.debug('Done compiling.')
