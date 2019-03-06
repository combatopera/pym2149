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
import threading, logging, time

log = logging.getLogger(__name__)

class Task:

    def __init__(self, when, task):
        self.when = when
        self.task = task

class Delay(SimpleBackground):

    @types()
    def __init__(self):
        pass

    def start(self):
        self.sleeper = self.Sleeper()
        self.tasks = set()
        self.taskslock = threading.RLock()
        super().start(self._bg, self.sleeper)

    def __call__(self, delay, task):
        with self.taskslock:
            self.tasks.add(Task(time.time() + delay, task))
        self.sleeper.interrupt()

    def _bg(self, sleeper):
        while not self.quit:
            now = time.time()
            with self.taskslock:
                tasks = {task for task in self.tasks if task.when <= now}
            for task in tasks:
                try:
                    task.task()
                except Exception:
                    log.exception('Task failed:')
            with self.taskslock:
                self.tasks -= tasks
                sleeptime = min(task.when for task in self.tasks) - time.time() if self.tasks else None
            sleeper.sleep(sleeptime)
        with self.taskslock:
            log.debug("Tasks denied: %s", len(self.tasks))
