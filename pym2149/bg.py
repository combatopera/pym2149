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

import threading, logging, tempfile, shutil, os, time

log = logging.getLogger(__name__)

class Background:

    def __init__(self, config):
        if config.profile:
            if config.trace:
                raise Exception
            _, self.profilesort, self.profilepath = config.profile
            self.bg = self.profile
        elif config.trace:
            self.bg = self.trace
        else:
            self.bg = self.__call__

    def profile(self, *args, **kwargs):
        profilepath = self.profilepath + time.strftime('.%Y-%m-%dT%H-%M-%S')
        tmpdir = tempfile.mkdtemp()
        try:
            binpath = os.path.join(tmpdir, 'stats')
            import cProfile
            cProfile.runctx('self.__call__(*args, **kwargs)', globals(), locals(), binpath)
            import pstats
            f = open(profilepath, 'w')
            try:
                stats = pstats.Stats(binpath, stream = f)
                stats.sort_stats(self.profilesort)
                stats.print_stats()
                f.flush()
            finally:
                f.close()
        finally:
            shutil.rmtree(tmpdir)

    def trace(self, *args, **kwargs):
        from trace import Trace
        t = Trace()
        t.runctx('self.__call__(*args, **kwargs)', globals(), locals())
        t.results().write_results()

    def start(self):
        self.quit = False
        self.thread = threading.Thread(target = self.bg)
        self.thread.start()

    def stop(self):
        self.quit = True
        self.thread.join()
