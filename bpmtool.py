#!/usr/bin/env runpy

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
from pym2149.config import getconfigloader
from pym2149.boot import createdi

def main():
    config = getconfigloader().load()
    createdi(config)
    ups = config.updaterate
    lpb = config.linesperbeat
    for upl in xrange(1, 21):
        lpm = 60 * ups / upl
        bpm = lpm / lpb
        print "%2s" % upl, "%7.3f" % bpm

if '__main__' == __name__:
    main()
