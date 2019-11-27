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

cdef extern from "resid/siddefs.h":

    ctypedef unsigned reg8
    ctypedef int cycle_count

cdef extern from "resid/sid.h":

    cdef cppclass SID:
        SID()
        int clock(cycle_count& delta_t, short* buf, int n)
        void write(reg8 offset, reg8 value)

cdef class NativeSID:

    cdef SID sid

    def write(self, offset, value):
        self.sid.write(offset, value)
