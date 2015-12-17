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

import subprocess, re, os, np

def iterlibraries():
    ldconfigpath = '/sbin/ldconfig'
    trylibs = 'jack', 'asound'
    if os.path.exists(ldconfigpath):
        installed = set(re.search(r'[^\s]+', line).group() for line in subprocess.check_output([ldconfigpath, '-p']).splitlines() if line.startswith('\t'))
        for name in trylibs:
            if "lib%s.so" % name in installed:
                yield name, {}

turboconf = {
    'include_dirs': np.get_include(),
    'libraries': list(iterlibraries()),
}
