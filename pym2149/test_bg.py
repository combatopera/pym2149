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

from .bg import SimpleBackground
import unittest, time, threading

class TestSleeper(unittest.TestCase):

    def setUp(self):
        self.s = SimpleBackground.Sleeper()

    def _assertnotinterrupted(self):
        start = time.time()
        self.s.sleep(.1)
        self.assertAlmostEqual(.1, time.time() - start, delta = .01)

    def test_notinterrupted(self):
        self._assertnotinterrupted()

    def test_interruptbefore(self):
        self.s.interrupt()
        start = time.time()
        self.s.sleep(1)
        self.assertAlmostEqual(0, time.time() - start, delta = .01)
        self._assertnotinterrupted()

    def test_interruptduring(self):
        def firesoon():
            time.sleep(.1)
            self.s.interrupt()
        t = threading.Thread(target = firesoon)
        t.start()
        start = time.time()
        self.s.sleep(1)
        self.assertAlmostEqual(.1, time.time() - start, delta = .01)
        t.join()
        self._assertnotinterrupted()
