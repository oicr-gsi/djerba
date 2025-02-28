#! /usr/bin/env python3

from djerba.plugins.plugin_tester import PluginTester
from djerba.plugins.tar.status.plugin import main as status_plugin

class TestTarSNVIndelPlugin(PluginTester):


    def test_status(self):
        pass

if __name__ == '__main__':
    unittest.main()
