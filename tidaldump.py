#!/usr/bin/env python

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

import subprocess, re
from pym2149 import osctrl

command = ['sudo', 'tcpdump', '-Xl', '-i', 'lo', 'udp', 'dst', 'port', '57120']
lenpattern = re.compile(' length ([0-9]+)')
header = 28
linesize = 16
bytepattern = re.compile('[0-9a-f]{2}')
statusprefix = '/status\0'.encode('ascii')
bundleprefix = '#bundle\0'.encode('ascii')

def main():
    p = subprocess.Popen(command, stdout = subprocess.PIPE)
    readline = lambda: p.stdout.readline().decode()
    while True:
        line = readline()
        m = lenpattern.search(line)
        if m is None:
            continue
        n = int(m.group(1))
        total = header + n
        v = bytearray()
        for _ in range((total + linesize - 1) // linesize):
            line = readline()[10:49]
            v.extend(int(x, 16) for x in bytepattern.findall(line))
        del v[:header]
        print osctrl.parse(v)

if '__main__' == __name__:
    main()
