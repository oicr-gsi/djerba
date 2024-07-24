#! /usr/bin/env python3

import os
import sys
import unittest
from test_mini import TestScript

class TestBuild(TestScript):
    
    def setUp(self):
        super().setUp()
        self.set_executable(MINI_DJERBA_BUILD)

if __name__ == '__main__':

    if len(sys.argv)==2:
        MINI_DJERBA_BUILD = sys.argv[1]
        if not os.path.isfile(MINI_DJERBA_BUILD) and os.access(MINI_DJERBA_BUILD, os.X_OK):
            print("mini-djerba build is not an executable file", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: test_build.py PATH_TO_MINI_DJERBA_BUILD", file=sys.stderr)
        sys.exit(1)
    unittest.main(argv=[sys.argv[0]], verbosity=2)
