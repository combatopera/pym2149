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

from . import V
from .lc import Event
import unittest

class TestEvent(unittest.TestCase):

    def test_offkwarg(self):
        namespace = object()
        calls = []
        class MyNote:
            def on(self, frame, hmm):
                calls.append(['on', frame, hmm[0], hmm[frame]])
            def off(self, frame, onframes, hmm):
                calls.append(['off', frame, hmm[0], hmm[frame], onframes])
        self.cls = MyNote
        self.onparams = ['frame', 'hmm']
        self.offparams = ['frame', 'onframes', 'hmm']
        e = Event(35, None, self, namespace)
        f = Event(40, 5, self, namespace)
        speed = 10
        kwargs = {(namespace, 'hmm'): V('20/80 100')}
        e(350, speed, self, [], kwargs, self)
        e(360, speed, self, [], kwargs, self)
        e(390, speed, self, [], kwargs, self)
        f(400, speed, self, [], kwargs, self)
        f(410, speed, self, [], kwargs, self)
        self.assertEqual([
            ['on', 0, 55, 55],
            ['on', 10, 55, 56],
            ['on', 40, 55, 59],
            ['off', 50, 55, 60, 50],
            ['off', 60, 55, 61, 50],
        ], calls)
