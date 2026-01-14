import ast

from flake8_qgis import Plugin

"""Tests for `flake8_qgis` package."""


def _results(s: str) -> set[str]:
    tree = ast.parse(s)
    plugin = Plugin(tree)
    return {f"{line}:{col} {msg}" for line, col, msg, _ in plugin.run()}


def test_trivial_case():
    assert _results("") == set()


def test_plugin_version():
    assert isinstance(Plugin.version, str)
    assert "." in Plugin.version


def test_plugin_name():
    assert isinstance(Plugin.name, str)


def test_QGS101_pass():
    ret = _results("from qgs.core import QgsMapLayer, QgsVectorLayer")
    assert ret == set()


def test_QGS101_pass_with_3d_exception():
    ret = _results("from qgis._3d import *")
    assert ret == set()


def test_QGS102_pass_with_3d_exception():
    ret = _results("import qgis._3d")
    assert ret == set()


def test_QGS101():
    ret = _results("from qgs._core import QgsMapLayer, QgsVectorLayer")
    ret = ret.union(_results("from qgis._core import QgsApplication"))
    assert ret == {
        "1:0 QGS101 Use 'from qgis.core import QgsApplication' instead of 'from "
        "qgis._core import QgsApplication'",
        "1:0 QGS101 Use 'from qgs.core import QgsMapLayer, QgsVectorLayer' instead of "
        "'from qgs._core import QgsMapLayer, QgsVectorLayer'",
    }


def test_QGS102_pass():
    ret = _results("import qgs.core.QgsVectorLayer as QgsVectorLayer")
    assert ret == set()


def test_QGS102():
    ret = _results("import qgs._core.QgsVectorLayer as QgsVectorLayer")
    assert ret == {
        "1:0 QGS102 Use 'import qgs.core.QgsVectorLayer' instead of 'import "
        "qgs._core.QgsVectorLayer'"
    }


def test_QGS103_pass():
    ret = _results("from qgis.PyQt.QtCore import pyqtSignal")
    ret = ret.union(_results("from qgis.PyQt.QtWidgets import QCheckBox"))
    assert ret == set()


def test_QGS103():
    ret = _results("from PyQt5.QtCore import pyqtSignal")
    ret = ret.union(_results("from PyQt6.QtWidgets import QCheckBox"))
    assert ret == {
        "1:0 QGS103 Use 'from qgis.PyQt.QtWidgets import QCheckBox' instead of 'from "
        "PyQt6.QtWidgets import QCheckBox'",
        "1:0 QGS103 Use 'from qgis.PyQt.QtCore import pyqtSignal' instead of 'from "
        "PyQt5.QtCore import pyqtSignal'",
    }


def test_QGS104_pass():
    ret = _results("import qgis.PyQt.QtCore.pyqtSignal as pyqtSignal")
    assert ret == set()


def test_QGS104():
    ret = _results("import PyQt5.QtCore.pyqtSignal as pyqtSignal")
    assert ret == {
        "1:0 QGS104 Use 'import qgis.PyQt.QtCore.pyqtSignal' instead of 'import "
        "PyQt5.QtCore.pyqtSignal'"
    }


def test_QGS105_pass():
    ret = _results(
        """
def classFactory(iface):
    pass
        """
    )
    assert ret == set()


def test_QGS105():
    ret = _results(
        """
def some_function(somearg, iface):
    pass
        """
    )
    assert ret == {
        "2:0 QGS105 Do not pass iface (QgisInterface) as an argument, instead import "
        "it: 'from qgis.utils import iface'"
    }


def test_QGS105_typed():
    ret = _results(
        """
def some_function(somearg, interface: QgisInterface):
    pass
        """
    )
    assert ret == {
        "2:0 QGS105 Do not pass iface (QgisInterface) as an argument, instead import "
        "it: 'from qgis.utils import iface'"
    }


def test_QGS105_method():
    ret = _results(
        """
class SomeClass:
    def some_method(self, somearg, iface):
        pass
        """
    )
    assert ret == {
        "3:4 QGS105 Do not pass iface (QgisInterface) as an argument, instead import "
        "it: 'from qgis.utils import iface'"
    }


def test_QGS105_static_method():
    ret = _results(
        """
class SomeClass:
    @staticmethod
    def some_method(somearg, iface):
        pass
        """
    )
    assert len(ret) == 1
    assert next(iter(ret)).endswith(
        "QGS105 Do not pass iface (QgisInterface) as an argument, instead import "
        "it: 'from qgis.utils import iface'"
    )


def test_QGS106_pass():
    ret = _results("from osgeo import gdal")
    ret = ret.union(_results("from osgeo import ogr"))
    assert ret == set()


def test_QGS106():
    ret = _results("import gdal")
    ret = ret.union(_results("import ogr"))
    assert ret == {
        "1:0 QGS106 Use 'from osgeo import gdal' instead of 'import gdal'",
        "1:0 QGS106 Use 'from osgeo import ogr' instead of 'import ogr'",
    }
