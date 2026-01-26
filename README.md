# flake8-qgis
[![PyPI version](https://badge.fury.io/py/flake8-qgis.svg)](https://badge.fury.io/py/flake8-qgis)
[![Downloads](https://img.shields.io/pypi/dm/flake8-qgis.svg)](https://pypistats.org/packages/flake8-qgis)
![CI](https://github.com/osgeosuomi/flake8-qgis/workflows/CI/badge.svg)
[![Code on Github](https://img.shields.io/badge/Code-GitHub-brightgreen)](https://github.com/osgeosuomi/flake8-qgis)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)


A [flake8](https://flake8.pycqa.org/en/latest/index.html) plugin for QGIS3 python plugins written in Python.


Made with Cookiecutter template [cookiecutter-flake8-plugin](https://github.com/MartinThoma/cookiecutter-flake8-plugin).
Inspired by [flake8-simplify](https://github.com/MartinThoma/flake8-simplify).

## Installation

Install with `pip`:

```bash
pip install flake8-qgis
```

## Usage

Just call `flake8 .` in your package or `flake your.py`.


## Rules
Rule | Description
--- | ---
[QGS101](#QGS101) | Avoid using from-imports from qgis protected members
[QGS102](#QGS102) | Avoid using imports from qgis protected members
[QGS103](#QGS103) | Avoid using from-imports from PyQt directly
[QGS104](#QGS104) | Avoid using imports from PyQt directly
[QGS105](#QGS105) | Avoid passing QgisInterface as an argument
[QGS106](#QGS106) | Avoid importing gdal directly, import it from osgeo package
[QGS107](#QGS107) | Use 'exec' instead of 'exec_'
[QGS401](#QGS401) | Use 'QApplication.instance()' instead of 'qApp'
[QGS402](#QGS402) | Use 'QMetaType.Type.X' instead of 'QVariant.X'
[QGS403](#QGS403) | Used enum has been removed in Qt6
[QGS404](#QGS404) | QFontMetrics.width() has been removed in Qt6
[QGS405](#QGS405) | QComboBox activated\[str] has been removed in Qt6
[QGS406](#QGS406) | QRegExp has been removed in Qt6, use QRegularExpression instead
[QGS407](#QGS407) | QDesktopWidget has been removed in Qt6
[QGS408](#QGS408) | Support for compiled resources has been removed in PyQt6
[QGS409](#QGS409) | Fragile call to addAction
[QGS410](#QGS410) | Use NULL instead of QVariant()
[QGS411](#QGS411) | QDateTime(yyyy, mm, dd, hh, MM, ss, ms, ts) doesn't work anymore in Qt6
[QGS412](#QGS412) | QDateTime(QDate(...)) doesn't work anymore in Qt6

Please check the Examples section below for good and bad usage examples for each rule.

While it's important to adhere to these rules, there might be good reasons to ignore some of them. You can do so by using the standard Flake8 configuration. For example, in the `setup.cfg` file:
```python
[flake8]
ignore = QGS101, QGS102
```
If you only want to support QGIS 3, you can put:

```python
[tool.flake8]
# Select QGIS3 compatible rules
select = ["QGS1"]
```

### QGS101

Avoid using from-imports from qgis protected members

An exception is made for importing `qgis._3d` (since flake-qgis 1.1.0). The underscore in the package name is used to prevent the name from starting with a number, ensuring it is a valid package name.

#### Why is this bad?
Protected members are potentially unstable across software versions. Future changes in protected members might cause problems.

#### Example
```python
# Bad
from qgis._core import QgsMapLayer, QgsVectorLayer
from qgis._core import QgsApplication

# Good
from qgis.core import QgsMapLayer, QgsVectorLayer
from qgis.core import QgsApplication
```

### QGS102

Avoid using imports from qgis protected members

An exception is made for importing `qgis._3d` (since flake-qgis 1.1.0). The underscore in the package name is used to prevent the name from starting with a number, ensuring it is a valid package name.

#### Why is this bad?
Protected members are potentially unstable across software versions. Future changes in protected members might cause problems.

#### Example

```python
# Bad
import qgis._core.QgsVectorLayer as QgsVectorLayer

# Good
import qgis.core.QgsVectorLayer as QgsVectorLayer
```

### QGS103

Avoid using from-imports from PyQt directly

#### Why is this bad?
Importing directly from PyQt might create conflict with QGIS bundled PyQt version

#### Example

```python
# Bad
from PyQt5.QtCore import pyqtSignal

# Good
from qgis.PyQt.QtCore import pyqtSignal
```

### QGS104

Avoid using imports from PyQt directly

#### Why is this bad?
Importing directly from PyQt might create conflict with QGIS bundled PyQt version

#### Example

```python
# Bad
import PyQt5.QtCore.pyqtSignal as pyqtSignal

# Good
import qgis.PyQt.QtCore.pyqtSignal as pyqtSignal
```

### QGS105

Avoid passing QgisInterface as an argument

#### Why is this bad?
It is much easier to import QgisInterface, and it's easier to [mock](https://github.com/osgeosuomi/pytest-qgis#hooks) it as well when writing tests. This approach is not however documented properly, so the API might change at some point to exclude this.

This rule can be excluded safely since this is only a matter of preference. Passing iface as an argument is the documented way of getting QgisInterface in plugins. However, it requires writing more code.

#### Example

```python
# Bad: iface passed as argument
def some_function(somearg, iface):
    # do something with iface


# Good: iface imported
from qgis.utils import iface

def some_function(somearg):
    # do something with iface
```

```python
# in classFactory the passing is OK, since QGIS injects it
def classFactory(iface):
    # preferably do not pass the iface to plugin
```

### QGS106
Avoid importing gdal directly, import it from osgeo package

#### Why is this bad?
Importing directly from gdal might create conflict with different gdal versions

#### Example

```python
# Bad
import gdal
import ogr

# Good
from osgeo import gdal
```


### QGS107
Use 'exec' instead of 'exec_'

#### Why is this bad?
exec_ was introduced in PyQt to avoid conflict with Python 2.7 exec keyword.
Keyword exec was removed in Python 3.0 and exec_ was removed in later PyQt versions.

#### Example

```python
# Bad
window.exec_()

# Good
window.exec()
```

## QGIS 4 compatibility rules


### QGS401
Use 'QApplication.instance()' instead of 'qApp'

#### Why is this bad?
qApp has been removed from Qt6 api.

#### Example

```python
# Bad
qgis.PyQt.QtWidgets import qApp

qApp.processEvents()

# Good
qgis.PyQt.QtWidgets import QApplication

QApplication.instance().processEvents()
```

### QGS402
Use 'QMetaType.Type.X' instead of 'QVariant.X'. Rule also suggests renaming if neccessary.

> [!CAUTION]
> After fixing these warnings, the plugin may not be compatible
> with QGIS 3 versions so feel free to ignore this rule and come up with another solution
> it if you want to support both.

#### Why is this bad?
QVariant.Type has been removed from Qt6 api.

#### Example

```python
# Bad
QVariant.Int
QVariant.String

# Good
QMetaType.Int
QMetaType.QString
```

### QGS403
Use 'X' enum instead of removed 'Y'.

#### Why is this bad?
Lot of enums have been refactored in Qt6 api.

#### Example

```python
# Bad
Qt.MidButton

# Good
Qt.MouseButton.MiddleButton
```

### QGS404
QFontMetrics.width() has been removed in Qt6.
Use QFontMetrics.horizontalAdvance() or QFontMetrics.boundingRect().width() instead.

#### Why is this bad?

QFontMetrics.width was removed from Qt6 api.

#### Example

```python
# Bad
QFontMetrics.width()

# Good
QFontMetrics.horizontalAdvance()
```

### QGS405
QComboBox.activated\[str] has been removed in Qt6. Use QComboBox.textActivated instead.

#### Why is this bad?
Qt6 api removed QComboBox.activated str overload. Only int overload remains.

#### Example

```python
# Bad
combo_box.activated[str].connect(signal)

# Good
combo_box.textActivated.connect(signal)
```

### QGS406
QRegExp has been removed in Qt6, use QRegularExpression instead.

#### Why is this bad?
QRegExp has been removed from Qt6 api.

#### Example

```python
# Bad
from qgis.PyQt.QtCore import QRegExp

re = QRegExp('foo')

# Good
from qgis.PyQt.QtCore import QRegularExpression

re = QRegularExpression('foo')
```

### QGS407
QDesktopWidget has been removed in Qt6. Replace with some alternative approach instead.

#### Why is this bad?
QDesktopWidget has been removed from Qt6 api.

### QGS408
Support for compiled resources has been removed in PyQt6.
Directly load icon resources by file path and load UI fields using uic.loadUiType by file path instead.

> [!TIP]
> You can also use [qgis_plugin_tools.resources.load_ui_from_file](https://github.com/osgeosuomi/qgis_plugin_tools/blob/main/tools/resources.py#L349C5-L349C22).

#### Why is this bad?
Support for compiled resources has been removed from PyQt6 api.

#### Example

```python
# Bad
from resources_rc import dialog

# Good
from pathlib import Path
from qgis.PyQt import uic

dialog, _ = uic.loadUiType(Path("ui_file.ui"))
```

### QGS409
Many addAction calls have been removed in Qt6. Use my_action = QAction(...), obj.addAction(my_action) instead.

#### Why is this bad?
Many addAction calls with multiple args have been removed from Qt6 api.

#### Example

```python
# Bad
menu.addAction(foo, bar, baz, qux)

# Good
action = QAction(foo, bar, baz, qux)
menu.addAction(action)
```

### QGS410
Use NULL instead of QVariant()

#### Why is this bad?
PyQgs NULL has to be used explicitly.

#### Example

```python
# Bad
null_value = QVariant()
null_value = QVariant(QVariant.Null)

# Good
from qgis.core import NULL

null_value = NULL
```

### QGS411
QDateTime(yyyy, mm, dd, hh, MM, ss, ms, ts) doesn't work anymore in Qt6, port to more reliable QDateTime(QDate, QTime, ts) form.

#### Why is this bad?
QDateTime api has changed in Qt6.

#### Example

```python
# Bad
dt = QDateTime(2026, 1, 26, 0, 0, 0, 0, 0)

# Good
dt = QDateTime(QDate(2026, 1, 26), QTime(0, 0, 0, 0), 0)
```

### QGS412
QGS412 QDateTime(QDate(...)) doesn't work anymore in Qt6, port to more reliable QDatetime(QDate, QTime(0,0,0)) form.

#### Why is this bad?
QDateTime api has changed in Qt6.

#### Example

```python
# Bad
dt = QDateTime(QDate(2026, 1, 26))

# Good
dt = QDateTime(QDate(2026, 1, 26), QTime(0, 0, 0, 0))
```


## Development

This project uses [uv](https://docs.astral.sh/uv/getting-started/installation/)
to manage python packages. Make sure to have it installed first.

Install development dependencies
```
# Activate the virtual environment
$ source .venv/bin/activate
$ uv sync
# Install pre-commit hooks
$ pre-commit install
```

### Updating dependencies

`uv lock --upgrade`

## Contributing

Contributions are very welcome.
