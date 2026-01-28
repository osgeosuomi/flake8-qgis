# Unreleased

## New Features

* [#22](https://github.com/osgeosuomi/flake8-qgis/issues/22) Add QGIS 4 compatibility rules

## Maintenance tasks

* Update development environment and reformat codebase
* Update maintainer information
* Drop support for Python 3.9

# Version 1.1.0 (19-05-2025)

## New Features

* [#11](https://github.com/osgeosuomi/flake8-qgis/pull/11) Allow _3d import exception for QGS101 and QGS102

## Fixes

* Fix typo in QGS105 message

## Maintenance tasks

* [#14](https://github.com/osgeosuomi/flake8-qgis/pull/14) Update README with rule details
* [#16](https://github.com/osgeosuomi/flake8-qgis/pull/16) Mention _3d exception in README
* [#17](https://github.com/osgeosuomi/flake8-qgis/pull/17) Add test for QGS102 _3d exception
* [#10](https://github.com/osgeosuomi/flake8-qgis/pull/10) Clean code by separating error checks
* [#7](https://github.com/osgeosuomi/flake8-qgis/pull/7) Update pre-commit and dependencies
* [#18](https://github.com/osgeosuomi/flake8-qgis/pull/18) Upgrade workflows and dependencies

# Version 0.1.4 (10-08-2021)

## New Features

* Warn about importing gdal directly

# Version 0.1.3 (28-06-2021)

## New Features

* Allow iface to be passed to classFactory

## Fixes

* Include "qgis" module in QGS101 and QGS102 checks

## Maintenance tasks

* Fix README typos

# Version 0.1.2 (24-06-2021)

## Fixes

* Improve QGS103 warning message

## Maintenance tasks

* Add PyPI badge
* Fix CI badge typo

# Version 0.1.1 (24-06-2021)

## Maintenance tasks

* Release 0.1.1

# Version 0.1.0 (24-06-2021)

## New Features

* Add QGS101, QGS103, QGS104, and QGS105 checks with tests

## Maintenance tasks

* [#1](https://github.com/osgeosuomi/flake8-qgis/pull/1) Add CI and issue templates
* Improve README and add LICENSE
* Bootstrap project templates
