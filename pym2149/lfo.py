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

class LFO(list):

  def __init__(self, initial):
    self.append(initial)

  def lin(self, n, target):
    source = self[-1]
    for i in xrange(1, n + 1):
      self.append(int(round(source + (target - source) * i / n)))
    return self

  def jump(self, target):
    self[-1] = target
    return self

  def hold(self, n):
    return self.lin(n, self[-1])

  def tri(self, n, target, waves):
    source = self[-1]
    for _ in xrange(waves):
      self.lin(n, target)
      self.lin(n * 2, source * 2 - target)
      self.lin(n, source)
    return self

  def __call__(self, frame):
    return self[min(frame, len(self) - 1)]
