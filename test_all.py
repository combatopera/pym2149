#!/usr/bin/env python

import unittest, os, subprocess, sys, re

class TestAll(unittest.TestCase):

  def test_all(self):
    thispath = __file__
    top, thisname = os.path.split(thispath)
    flakesregex = []
    f = open(os.path.join(top, '.flakesignore'))
    try:
      for line in f:
        line, = line.splitlines()
        flakesregex.append(line)
    finally:
      f.close()
    flakesregex = re.compile('|'.join(flakesregex))
    def flakesaccept(path):
      return flakesregex.search(path[len(top) + len(os.sep):].replace(os.sep, '/')) is None
    paths = []
    for dirpath, dirnames, filenames in os.walk(top):
      paths.extend(sorted(os.path.join(dirpath, n) for n in filenames if n.endswith('.py')))
      dirnames.sort()
    subprocess.call(['pyflakes'] + [p for p in paths if flakesaccept(p)])
    codes = []
    for path in paths:
      name = os.path.basename(path)
      if thisname == name:
        pass
      elif name.startswith('test_'):
        print >> sys.stderr, path
        codes.append(subprocess.call(path))
      elif name.startswith('test'):
        print >> sys.stderr, path
        print >> sys.stderr, 'F'
        codes.append(1)
    print >> sys.stderr, thispath
    self.assertTrue(not codes or set([0]) == set(codes))

if __name__ == '__main__':
  unittest.main()
