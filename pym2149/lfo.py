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

from __future__ import division

class AbstractLFO:

  def loop(self, n):
    return Loop(self, n)

  def round(self):
    return Round(self)

  def render(self, n = None):
    if n is None:
      n = len(self)
    return [self(i) for i in xrange(n)]

class Loop(AbstractLFO):

  def __init__(self, lfo, n):
    self.loop = len(lfo) - n
    self.lfo = lfo

  def __call__(self, frame):
    n = len(self.lfo)
    if frame >= n:
      frame = self.loop + ((frame - self.loop) % (n - self.loop))
    return self.lfo(frame)

class Round(AbstractLFO):

  def __init__(self, lfo):
    self.lfo = lfo

  def __call__(self, frame):
    return int(round(self.lfo(frame)))

  def __len__(self):
    return len(self.lfo)

class LFO(list, AbstractLFO):

  def __init__(self, initial):
    list.__init__(self, [initial])

  def lin(self, n, target):
    source = self[-1]
    for i in xrange(1, n + 1):
      self.append(source + (target - source) * i / n)
    return self

  def jump(self, target):
    self[-1] = target
    return self

  def hold(self, n):
    return self.lin(n, self[-1])

  def tri(self, m, target, n):
    unit = m * 4
    if 0 != n % unit:
      raise Exception("Expected a multiple of %s but got: %s" % (unit, n))
    source = self[-1]
    for _ in xrange(n // unit):
      self.lin(m, target)
      self.lin(m * 2, source * 2 - target)
      self.lin(m, source)
    return self

  def __call__(self, frame):
    return self[min(frame, len(self) - 1)]
