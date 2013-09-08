#!/usr/bin/env python

import unittest, os, subprocess

class TestAll(unittest.TestCase):

  def test_all(self):
    codes = []
    d, thisname = os.path.split(__file__)
    for name in os.listdir(d):
      if thisname != name and name.startswith('test_') and name.endswith('.py'):
        codes.append(subprocess.call([os.path.join(d, name)]))
    self.assertTrue(not codes or set([0]) == set(codes))

if __name__ == '__main__':
  unittest.main()
