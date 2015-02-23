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

import unittest
from lazyconf import Loader, View

class Fork:

    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, name):
        return getattr(self.parent, name)

class TestView(unittest.TestCase):

    def test_inheritedexpressionusescorrectcontext(self):
        loader = Loader()
        lines = ['woo = config.yay\n', '']
        readline = lambda: lines.pop(0)
        loader.loadfile(None, readline)
        view = View(loader)
        fork = Fork(view)
        view.yay = 'viewyay'
        self.assertEqual('viewyay', fork.woo)
        fork.yay = 'forkyay'
        self.assertEqual('forkyay', fork.woo)

if __name__ == '__main__':
    unittest.main()
