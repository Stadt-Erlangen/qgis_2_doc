# coding=utf-8
"""DockWidget test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'gis@stadt.erlangen.de'
__date__ = '2020-07-29'
__copyright__ = 'Copyright 2020, eGov/GIS'

import unittest

from PyQt5.QtGui import QDockWidget

from qgis_2_doc_dockwidget import Qgis2DocDockWidget

from utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class Qgis2DocDockWidgetTest(unittest.TestCase):
    """Test dockwidget works."""

    def setUp(self):
        """Runs before each test."""
        self.dockwidget = Qgis2DocDockWidget(None)

    def tearDown(self):
        """Runs after each test."""
        self.dockwidget = None

    def test_dockwidget_ok(self):
        """Test we can click OK."""
        pass

if __name__ == "__main__":
    suite = unittest.makeSuite(Qgis2DocDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

