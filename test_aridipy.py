#!/usr/bin/env python

# Copyright 2014 Andrzej Cichocki

# This file is part of aridipy.
#
# aridipy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# aridipy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with aridipy.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from aridipy import Expressions, View, Fork

class TestFork(unittest.TestCase):

    def test_inheritedexpressionusescorrectcontext(self):
        expressions = Expressions()
        lines = ['woo = config.yay\n', '']
        readline = lambda: lines.pop(0)
        expressions.loadfile('whatever', readline)
        view = View(expressions)
        fork = Fork(view)
        view.yay = 'viewyay'
        self.assertEqual('viewyay', fork.woo)
        fork.yay = 'forkyay'
        self.assertEqual('forkyay', fork.woo)

if '__main__' == __name__:
    unittest.main()
