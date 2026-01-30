import ast
from textwrap import dedent

import pytest

import flake8_qgis.flake8_qgis as flake8_qgis_module
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


def test_QGS107():
    ret = _results("dialog.exec_()")
    assert ret == {"1:0 QGS107 Use 'exec' instead of 'exec_'"}
    ret = _results("def exec_(): pass")
    assert ret == {"1:0 QGS107 Use 'exec' instead of 'exec_'"}


def test_QGS108_and_QGS109():
    ret = _results('output = "TEMPORARY_OUTPUT"')
    assert ret == {
        "1:9 QGS108 Replace 'TEMPORARY_OUTPUT' with QgsProcessing.TEMPORARY_OUTPUT"
    }

    ret = _results(
        dedent(
            """
        processing.run("foo", "bar", "TEMPORARY_OUTPUT", is_child_algorithm=True)
        """
        )
    )

    assert ret == {
        "2:29 QGS108 Replace 'TEMPORARY_OUTPUT' with QgsProcessing.TEMPORARY_OUTPUT"
    }

    ret = _results('output = "TEMPORARY_OUTPT"')
    assert ret == {
        "1:9 QGS109 Replace 'TEMPORARY_OUTPT' with QgsProcessing.TEMPORARY_OUTPUT"
    }

    ret = _results('output = "TEMPORARY_OUTPUTS"')
    assert ret == {
        "1:9 QGS109 Replace 'TEMPORARY_OUTPUTS' with QgsProcessing.TEMPORARY_OUTPUT"
    }

    ret = _results('output = "something else"')
    assert ret == set()


def test_QGS110():
    ret = _results("processing.run('native:buffer', {}, is_child_algorithm=True)")
    assert ret == set()

    ret = _results("processing.run('native:buffer', {})")
    assert ret == {
        "1:0 QGS110 Use is_child_algorithm=True when running other algorithms in the "
        "plugin"
    }

    ret = _results("processing.run('native:buffer', {}, is_child_algorithm=False)")
    assert ret == {
        "1:0 QGS110 Use is_child_algorithm=True when running other algorithms in the "
        "plugin"
    }


@pytest.mark.parametrize(
    ("method_name", "imports", "expected_method"),
    [
        (
            "addMapLayer",
            "from qgis.core import QgsProject",
            "QgsProject.addMapLayer()",
        ),
        (
            "saveWithDetails",
            "from qgis.core import QgsAttributeForm",
            "QgsAttributeForm.saveWithDetails()",
        ),
    ],
)
def test_QGS201_ignored_return(method_name, imports, expected_method):
    assert method_name in flake8_qgis_module.RETURN_VALUES_TO_CHECK
    ret = _results(
        dedent(
            f"""
            {imports}

            project.instance().{method_name}('foo')
            """
        )
    )
    assert ret == {
        "4:0 QGS201 Check the success flag and possibly error message from return "
        f"value of {expected_method}."
    }


def test_QGS201_return_not_ignored():
    assert "addMapLayer" in flake8_qgis_module.RETURN_VALUES_TO_CHECK
    ret = _results(
        dedent(
            """
            from qgis.core import QgsProject

            layer = project.instance().addMapLayer('foo')
            """
        )
    )
    assert ret == set()


@pytest.mark.parametrize(
    ("method_name", "expected_method"),
    [
        (
            "prepare",
            "some of (QgsAbstractPropertyCollection.prepare(), "
            "QgsDiagramLayerSettings.prepare(), QgsProperty.prepare())",
        ),
        ("calculate", "QgsAggregateCalculator.calculate()"),
        (
            "addMapLayer",
            "some of (QgsMapLayerStore.addMapLayer(), QgsProject.addMapLayer())",
        ),
    ],
)
def test_QGS202_ignored_return(method_name, expected_method):
    assert method_name in flake8_qgis_module.RETURN_VALUES_TO_CHECK
    ret = _results(f"project.{method_name}(layer)")
    assert ret == {
        "1:0 QGS202 Check the success flag and possibly error message from return "
        f"value of the method if it is {expected_method}. Otherwise "
        "ignore this error."
    }


def test_QGS202_used_as_condition():
    method_name = "read"
    assert method_name in flake8_qgis_module.RETURN_VALUES_TO_CHECK
    ret = _results(
        f"""
if project.{method_name}("foo"):
    pass
        """
    )
    assert ret == set()


def test_QGS401():
    ret = _results("qApp.processEvents()")
    assert ret == {
        "1:0 QGS401 Use 'QApplication.instance()' or 'QgsApplication.instance()' "
        "instead of 'qApp'"
    }


def test_QGS402():
    ret = _results("QVariant.Type.UInt")
    assert ret == {
        "1:0 QGS402 Use 'QMetaType.UInt' or 'QMetaType.Type.UInt' instead of "
        "'QVariant.Type.UInt'. WARNING: after this, the plugin may not be compatible "
        "with QGIS 3."
    }

    ret = _results("QVariant.Int")
    assert ret == {
        "1:0 QGS402 Use 'QMetaType.Int' or 'QMetaType.Type.Int' instead of "
        "'QVariant.Int'. WARNING: after this, the plugin may not be compatible with "
        "QGIS 3."
    }

    ret = _results("QVariant.Invalid")
    assert ret == {
        "1:0 QGS402 Use 'QMetaType.UnknownType' or 'QMetaType.Type.UnknownType' "
        "instead of 'QVariant.Invalid'. WARNING: after this, the plugin may not be "
        "compatible with QGIS 3."
    }


def test_QGS403():
    ret = _results("value = QPainter.HighQualityAntialiasing")
    assert ret == {
        "1:8 QGS403 Enum has been changed in Qt6. Use "
        "'QPainter.RenderHint.Antialiasing' instead of "
        "'QPainter.HighQualityAntialiasing'."
    }

    ret = _results("role = Qt.MouseButton.MidButton")
    assert ret == {
        "1:7 QGS403 Enum has been changed in Qt6. Use 'Qt.MouseButton.MiddleButton' "
        "instead of 'Qt.MouseButton.MidButton'."
    }


def test_QGS404():
    expected_error = {
        "1:0 QGS404 QFontMetrics.width() has been removed in Qt6. "
        "Use QFontMetrics.horizontalAdvance() or "
        "QFontMetrics.boundingRect().width() instead."
    }

    ret = _results("QFontMetrics.width()")
    assert ret == expected_error

    ret = _results("font_metrics.width()")
    assert ret == expected_error

    assert _results("self.width()") == set()


def test_QGS405():
    ret = _results("combo_box.activated[str].connect(foo)")
    assert ret == {
        "1:0 QGS405 activated[str] has been removed in Qt6, use textActivated instead"
    }


def test_QGS406():
    ret = _results("from qgis.PyQt.QtCore import QRegExp")
    assert ret == {
        "1:0 QGS406 QRegExp is removed in Qt6, use QRegularExpression instead"
    }
    ret = _results("import QRegExp")
    assert ret == {
        "1:0 QGS406 QRegExp is removed in Qt6, use QRegularExpression instead"
    }
    ret = _results("re = QRegExp('foo')")
    assert ret == {
        "1:5 QGS406 QRegExp is removed in Qt6, use QRegularExpression instead"
    }


def test_QGS407():
    ret = _results("QApplication.desktop()")
    assert ret == {
        "1:0 QGS407 QDesktopWidget is removed in Qt6. Replace with alternative "
        "approach instead."
    }


def test_QGS408():
    ret = _results("import resources_rc")
    assert ret == {
        "1:0 QGS408 support for compiled resources is removed in Qt6. Directly load "
        "icon resources. by file path and load UI fields using uic.loadUiType by file "
        "path instead."
    }

    ret = _results("from resources_rc import item")
    assert ret == {
        "1:0 QGS408 support for compiled resources is removed in Qt6. Directly load "
        "icon resources. by file path and load UI fields using uic.loadUiType by file "
        "path instead."
    }


def test_QGS409():
    ret = _results("menu.addAction(foo, bar, baz)")
    assert ret == set()

    ret = _results("menu.addAction(foo, bar, baz, qux)")
    assert ret == {
        "1:0 QGS409 fragile call to addAction. Use my_action = QAction(...), "
        "obj.addAction(my_action) instead."
    }


def test_QGS410():
    ret = _results("val = QVariant()")
    assert ret == {
        "1:6 QGS410 Invalid conversion of QVariant() to NULL. Use from qgis.core "
        "import NULL instead."
    }

    ret = _results("val = QVariant(QVariant.Int)")
    assert ret == {
        "1:6 QGS410 Invalid conversion of QVariant(QVariant) to NULL. Use from "
        "qgis.core import NULL instead."
    }


def test_QGS411():
    ret = _results("val = QDateTime(0,0,0,0,0,0,0,0)")
    assert ret == {
        "1:6 QGS411 QDateTime(yyyy, mm, dd, hh, MM, ss, ms, ts) doesn't work anymore "
        "in Qt6, port to more reliable QDateTime(QDate, QTime, ts) form."
    }


def test_QGS412():
    ret = _results("val = QDateTime(QDate(2023, 1, 1))")
    assert ret == {
        "1:6 QGS412 QDateTime(QDate(...)) doesn't work anymore in Qt6, "
        "port to more reliable QDatetime(QDate, QTime(0,0,0)) form."
    }
