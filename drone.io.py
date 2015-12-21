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

import os, sys, subprocess, itertools

condaversion = '3.16.0'

def main():
    conf = {}
    execfile('project.info', conf)
    projectdir = os.getcwd()
    os.chdir(os.path.dirname(projectdir))
    for project in itertools.chain(['runpy'], conf['projects']):
        subprocess.check_call(['hg', 'clone', "https://bitbucket.org/combatopera/%s" % project])
    os.environ['PATH'] = "%s%s%s" % (os.path.join(os.getcwd(), 'runpy'), os.pathsep, os.environ['PATH'])
    subprocess.check_call(['wget', '--no-verbose', "http://repo.continuum.io/miniconda/Miniconda-%s-Linux-x86_64.sh" % condaversion])
    installcommand = ['bash', "Miniconda-%s-Linux-x86_64.sh" % condaversion]
    p = subprocess.Popen(installcommand, stdin = subprocess.PIPE)
    p.communicate(input = '\nyes\nminiconda\nno\n')
    if p.wait():
        raise subprocess.CalledProcessError(p.returncode, installcommand)
    subprocess.check_call([os.path.join('miniconda', 'bin', 'conda'), 'install', '-q', 'pyflakes', 'nose'] + ['numpy', 'cython', 'mock'])
    os.environ['MINICONDA_HOME'] = os.path.join(os.getcwd(), 'miniconda')
    os.chdir(projectdir)
    sys.exit(subprocess.call(['tests']))

if '__main__' == __name__:
    main()
