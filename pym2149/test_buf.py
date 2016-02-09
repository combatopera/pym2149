#!/usr/bin/env pyven

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

import unittest, numpy as np
from pyrbo import T, U, Z, NoSuchPlaceholderException, AlreadyBoundException
from buf import Buf

class TestBuf(unittest.TestCase):

    def test_works(self):
        t = np.uint16
        u = np.int32
        tbuf = Buf[T, t]
        ubuf = Buf[U, u]
        names = ['Buf', 'Buf_uint16_?', 'Buf_?_int32', 'Buf_uint16_int32', 'Buf_uint16_int32']
        for bufcls in Buf, tbuf, ubuf, tbuf[U, u], ubuf[T, t]:
            self.assertEqual(names.pop(0), bufcls.__name__)
            v = np.zeros(10, dtype = t)
            buf = bufcls(v)
            buf.fillpart(4, 6, 5)
            self.assertEqual([0, 0, 0, 0, 5, 5, 0, 0, 0, 0], list(v))
            buf.fill_i1(6)
            self.assertEqual([6] * 10, list(v))
        try:
            Buf[Z, None]
            self.fail('Expected no such placeholder.')
        except NoSuchPlaceholderException, e:
            self.assertEqual((Z,), e.args)
        try:
            tbuf[T, TestBuf]
            self.fail('Expected already bound.')
        except AlreadyBoundException, e:
            self.assertEqual((T, t, TestBuf), e.args)

if '__main__' == __name__:
    unittest.main()
