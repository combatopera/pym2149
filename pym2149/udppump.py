#!/usr/bin/env python

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

import socket, sys, struct, os, threading, time, subprocess

host = '127.0.0.1'
bufsize = 1024 # XXX: Big enough?

def main():
    port1, port2, ctrl = sys.argv[1:]
    port1 = int(port1)
    port2 = int(port2)
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def pollshutdown():
        while os.path.exists(ctrl):
            time.sleep(.5)
        subprocess.check_call(['kill', str(os.getpid())])
    threading.Thread(target = pollshutdown).start()
    os.utime(ctrl, (0, 0))
    while True:
        msg = sock1.recvfrom(bufsize)[0]
        port, = struct.unpack('!H', msg[22:24])
        if port == port1:
            sock2.sendto(msg[28:], (host, port2))

if '__main__' == __name__:
    main()
