# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

import re

wordpattern = re.compile(r'\S+')
statetobatterypower = {'charging': False, 'fully-charged': False, 'discharging': True}

def batterypower():
    try:
        from lagoon import upower
    except ImportError:
        return # Run all tests.
    def states():
        for line in upower.__show_info('/org/freedesktop/UPower/devices/battery_C173').splitlines():
            words = wordpattern.findall(line)
            if 2 == len(words) and 'state:' == words[0]:
                yield words[1]
    states = list(states())
    if states:
        state, = states
        return statetobatterypower[state]
