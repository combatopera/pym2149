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

def V(script, step = 0, continuous = False):
    from .parse import concat, StepScript, VParse
    return concat(lambda *args: StepScript(*args, step), VParse(float, step, continuous), script, {})

def D(script):
    from .parse import concat, StepScript, VParse, vector
    step = 0
    return concat(lambda *args: StepScript(*args, step), VParse(vector, step, False), script, {})

def E(cls, script, **kwargs):
    from .parse import concat, Script, EParse, NoteWrapper
    namespace = object()
    kwargs = {(namespace, name): value for name, value in kwargs.items()}
    return concat(Script, EParse(NoteWrapper(cls), namespace), script, kwargs)

unit = E(lambda: None, '1')
naturalminor = V('0 2 3 5 7 8 10', step = 12, continuous = True)
harmonicminor = V('0 2 3 5 7 8 11', step = 12, continuous = True)
major = V('0 2 4 5 7 9 11', step = 12, continuous = True)
octatonic = V('0 1 3 4 6 7 9 10', step = 12, continuous = True)
