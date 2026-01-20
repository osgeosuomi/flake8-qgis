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

Please check the Examples section below for good and bad usage examples for each rule.

While it's important to adhere to these rules, there might be good reasons to ignore some of them. You can do so by using the standard Flake8 configuration. For example, in the `setup.cfg` file:
```python
[flake8]
ignore = QGS101, QGS102
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
