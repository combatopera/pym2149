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

from .bg import SimpleBackground
from diapyr import types
from collections import namedtuple
import threading, logging, time, bisect

log = logging.getLogger(__name__)

class Task(namedtuple('BaseTask', 'when task')):

    def __call__(self):
        try:
            self.task()
        except Exception:
            log.exception('Task failed:')

class Delay(SimpleBackground):

    @types()
    def __init__(self):
        pass

    def start(self):
        self.sleeper = self.Sleeper()
        self.tasks = []
        self.taskslock = threading.RLock()
        super().start(self._bg, self.sleeper)

    def __call__(self, delay, task):
        with self.taskslock:
            t = Task(time.time() + delay, task)
            self.tasks.insert(bisect.bisect(self.tasks, t), t)
        self.sleeper.interrupt()

    def _bg(self, sleeper):
        while not self.quit:
            with self.taskslock:
                i = bisect.bisect(self.tasks, (time.time(), None))
                tasks = self.tasks[:i]
                del self.tasks[:i]
            for task in tasks:
                task()
            with self.taskslock:
                sleeptime = self.tasks[0].when - time.time() if self.tasks else None
            sleeper.sleep(sleeptime)
        with self.taskslock:
            log.debug("Tasks denied: %s", len(self.tasks))
