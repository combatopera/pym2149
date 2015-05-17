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

from nod import BufNode
from buf import DiffRing

loopsize = 1024

tonediffs = DiffRing((1 - (i & 1) for i in xrange(loopsize)), 0, BufNode.bindiffdtype)

# FIXME: Implement this properly.
sinusdiffs = DiffRing([13, 14, 15, 14, 13, 11, 0, 11] * (loopsize // 8), 0, BufNode.zto127diffdtype)
