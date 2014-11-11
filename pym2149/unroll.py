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

import os

def unroll(frompath, topath, **kwargs):
    f = open(os.path.join(os.path.dirname(__file__), frompath))
    try:
        g = open(os.path.join(os.path.dirname(__file__), topath), 'w')
        try:
            for name, value in kwargs.iteritems():
                print >> g, "%s = %r" % (name, value)
            for line in f:
                if 'UNROLL' in line:
                    print line,
                g.write(line)
            g.flush()
        finally:
            g.close()
    finally:
        f.close()
