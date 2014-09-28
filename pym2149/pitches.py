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

from buf import singleton
from pitch import Pitch

@singleton
class __all__(list):

  def __init__(self):
    for octave in xrange(10):
      for letter, offset in zip('CDEFGAB', [0, 2, 4, 5, 7, 9, 11]):
        name = "%s%s" % (letter, octave)
        globals()[name] = Pitch((1 + octave) * 12 + offset)
        self.append(name)
