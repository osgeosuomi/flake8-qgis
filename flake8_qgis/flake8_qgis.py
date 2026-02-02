import ast
import importlib.metadata as importlib_metadata
import json
import re
from _ast import FunctionDef, Import
from ast import Call
from collections import defaultdict
from collections.abc import Callable, Generator
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
)

if TYPE_CHECKING:
    FlakeError = tuple[int, int, str]

"""
Rule descriptions
===================
"""
FROM_IMPORT_USE_INSTEAD_OF = (
    "{code} Use 'from {correct_module} import {members}' "
    "instead of 'from {module} import {members}'"
)
IMPORT_USE_INSTEAD_OF = "{code} Use 'import {correct}' instead of 'import {incorrect}'"
QGS105 = (
    "QGS105 Do not pass iface (QgisInterface) as an argument, "
    "instead import it: 'from qgis.utils import iface'"
)
QGS106 = "QGS106 Use 'from osgeo import {members}' instead of 'import {members}'"
QGS107 = "QGS107 Use 'exec' instead of 'exec_'"
QGS108 = "QGS108 Replace 'TEMPORARY_OUTPUT' with QgsProcessing.TEMPORARY_OUTPUT"
QGS109 = "QGS109 Replace '{old}' with QgsProcessing.TEMPORARY_OUTPUT"
QGS110 = (
    "QGS110 Use is_child_algorithm=True when running other algorithms in the plugin"
)

# Return value rules
QGS201 = (
    "QGS201 Check the success flag and possibly "
    "error message from return value of {method}."
)
QGS202 = (
    "QGS202 Check the success flag and possibly error message from "
    "return value of the method if it is {method}. Otherwise ignore this error."
)


# QGIS>=4 rules,
# greatly inspired by https://github.com/qgis/QGIS/blob/master/scripts/pyqt5_to_pyqt6/pyqt5_to_pyqt6.py
# licensed under GNU General Public License v2.0
QGS401 = (
    "QGS401 Use 'QApplication.instance()' or 'QgsApplication.instance()'"
    " instead of 'qApp'"
)
QGS402 = (
    "QGS402 Use 'QMetaType.{new}' or 'QMetaType.Type.{new}'"
    " instead of 'QVariant.{old}'. "
    "WARNING: after this, the plugin may not be compatible with QGIS 3."
)
QGS403 = "QGS403 Enum has been changed in Qt6. Use '{new}' instead of '{old}'."
QGS404 = (
    "QGS404 QFontMetrics.width() has been removed in Qt6. "
    "Use QFontMetrics.horizontalAdvance() or "
    "QFontMetrics.boundingRect().width() instead."
)
QGS405 = "QGS405 activated[str] has been removed in Qt6, use textActivated instead"
QGS406 = "QGS406 QRegExp is removed in Qt6, use QRegularExpression instead"
QGS407 = (
    "QGS407 QDesktopWidget is removed in Qt6. "
    "Replace with alternative approach instead."
)
QGS408 = (
    "QGS408 support for compiled resources is removed in Qt6. "
    "Directly load icon resources. by file path and load UI fields using "
    "uic.loadUiType by file path instead."
)
QGS409 = (
    "QGS409 fragile call to addAction. Use my_action = QAction(...), "
    "obj.addAction(my_action) instead."
)
QGS410 = (
    "QGS410 Invalid conversion of QVariant({attr}) to NULL. "
    "Use from qgis.core import NULL instead."
)
QGS411 = (
    "QGS411 QDateTime(yyyy, mm, dd, hh, MM, ss, ms, ts) doesn't work "
    "anymore in Qt6, port to more reliable QDateTime(QDate, QTime, ts) form."
)
QGS412 = (
    "QGS412 QDateTime(QDate(...)) doesn't work anymore in Qt6, "
    "port to more reliable QDatetime(QDate, QTime(0,0,0)) form."
)

# Other constants

CLASS_FACTORY = "classFactory"

QGIS_INTERFACE = "QgisInterface"
TEMPORARY_OUTPUT = "TEMPORARY_OUTPUT"

MINIMUM_REQUIRED_MODULES = 2
QDATETIME_ARG_COUNT = 8
ADD_ACTION_ARG_COUNT = 4

QMETATYPE_MAPPING = {
    "Invalid": "UnknownType",
    "BitArray": "QBitArray",
    "Bitmap": "QBitmap",
    "Brush": "QBrush",
    "ByteArray": "QByteArray",
    "Char": "QChar",
    "Color": "QColor",
    "Cursor": "QCursor",
    "Date": "QDate",
    "DateTime": "QDateTime",
    "EasingCurve": "QEasingCurve",
    "Uuid": "QUuid",
    "ModelIndex": "QModelIndex",
    "PersistentModelIndex": "QPersistentModelIndex",
    "Font": "QFont",
    "Hash": "QVariantHash",
    "Icon": "QIcon",
    "Image": "QImage",
    "KeySequence": "QKeySequence",
    "Line": "QLine",
    "LineF": "QLineF",
    "List": "QVariantList",
    "Locale": "QLocale",
    "Map": "QVariantMap",
    "Transform": "QTransform",
    "Matrix4x4": "QMatrix4x4",
    "Palette": "QPalette",
    "Pen": "QPen",
    "Pixmap": "QPixmap",
    "Point": "QPoint",
    "PointF": "QPointF",
    "Polygon": "QPolygon",
    "PolygonF": "QPolygonF",
    "Quaternion": "QQuaternion",
    "Rect": "QRect",
    "RectF": "QRectF",
    "RegularExpression": "QRegularExpression",
    "Region": "QRegion",
    "Size": "QSize",
    "SizeF": "QSizeF",
    "SizePolicy": "QSizePolicy",
    "String": "QString",
    "StringList": "QStringList",
    "TextFormat": "QTextFormat",
    "TextLength": "QTextLength",
    "Time": "QTime",
    "Url": "QUrl",
    "Vector2D": "QVector2D",
    "Vector3D": "QVector3D",
    "Vector4D": "QVector4D",
    "UserType": "User",
}

DEPRECATED_RENAMED_ENUMS = {
    ("Qt", "MidButton"): ("MouseButton", "MiddleButton"),
    ("Qt", "TextColorRole"): ("ItemDataRole", "ForegroundRole"),
    ("Qt", "BackgroundColorRole"): ("ItemDataRole", "BackgroundRole"),
    ("QPainter", "HighQualityAntialiasing"): ("RenderHint", "Antialiasing"),
}

QGIS_RETURN_METHODS_PATH = Path(__file__).with_name("qgis_return_methods.json")


def _load_return_methods() -> dict[str, set[str]]:
    try:
        raw = QGIS_RETURN_METHODS_PATH.read_text(encoding="utf-8")
    except OSError:
        return {}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    class_methods = data.get("methods_to_check", [])
    classes_by_methods: dict[str, set[str]] = defaultdict(set[str])

    for method in class_methods:
        parts = method.split(".")
        if len(parts) == 2:  # noqa: PLR2004
            classes_by_methods[parts[1]].add(parts[0])
        else:
            # Adds just the key
            classes_by_methods[method]

    return classes_by_methods


RETURN_VALUES_TO_CHECK = _load_return_methods()


def _test_qgis_module(module: str | None) -> str | None:
    if module is None:
        return None

    modules = module.split(".")
    if len(modules) < MINIMUM_REQUIRED_MODULES:
        return None

    if (
        modules[0] in ("qgs", "qgis")
        and modules[1].startswith("_")
        and modules[1] != "_3d"
    ):
        modules[1] = modules[1][1:]
        return ".".join(modules)

    return None


def _test_pyqt_module(module: str | None) -> str | None:
    if module is None:
        return None

    modules = module.split(".")
    if re.match(r"^PyQt[456]$", modules[0]):
        modules[0] = "qgis.PyQt"
        return ".".join(modules)

    return None


def _test_module_at_import_from(
    error_code: str,
    node: ast.ImportFrom,
    tester: Callable[[str | None], str | None],
) -> list["FlakeError"]:
    fixed_module_name = tester(node.module)
    if fixed_module_name:
        message = FROM_IMPORT_USE_INSTEAD_OF.format(
            code=error_code,
            correct_module=fixed_module_name,
            module=node.module,
            members=", ".join([alias.name for alias in node.names]),
        )

        return [(node.lineno, node.col_offset, message)]

    return []


def _test_module_at_import(
    error_code: str, node: ast.Import, tester: Callable[[str | None], str | None]
) -> list["FlakeError"]:
    errors: list[FlakeError] = []
    for alias in node.names:
        fixed_module_name = tester(alias.name)
        if fixed_module_name:
            message = IMPORT_USE_INSTEAD_OF.format(
                code=error_code, correct=fixed_module_name, incorrect=alias.name
            )
            errors.append((node.lineno, node.col_offset, message))

    return errors


def _get_qgs105(node: ast.FunctionDef) -> list["FlakeError"]:
    errors: list[FlakeError] = []
    if node.name == CLASS_FACTORY:
        return errors
    for arg in node.args.args:
        if (
            arg.arg == "iface"
            or (hasattr(arg, "type_comment") and arg.type_comment == QGIS_INTERFACE)
            or (
                arg.annotation
                and hasattr(arg.annotation, "id")
                and arg.annotation.id == QGIS_INTERFACE
            )
        ):
            errors.append((node.lineno, node.col_offset, QGS105))
    return errors


def _get_qgs106(node: ast.Import) -> list["FlakeError"]:
    errors: list[FlakeError] = []
    for alias in node.names:
        if alias.name in ("gdal", "ogr"):
            errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    QGS106.format(members=alias.name),
                )
            )
    return errors


def _get_qgs406_import_from(node: ast.ImportFrom) -> list["FlakeError"]:
    errors: list[FlakeError] = []
    for name in node.names:
        if name.name == "QRegExp":
            errors.append((node.lineno, node.col_offset, QGS406))
    return errors


def _get_qgs408_import_from(node: ast.ImportFrom) -> list["FlakeError"]:
    if node.module == "resources_rc":
        return [(node.lineno, node.col_offset, QGS408)]
    return []


def _get_qgs406_import(node: ast.Import) -> list["FlakeError"]:
    errors: list[FlakeError] = []
    for alias in node.names:
        if alias.name == "QRegExp":
            errors.append((node.lineno, node.col_offset, QGS406))
    return errors


def _get_qgs408_import(node: ast.Import) -> list["FlakeError"]:
    errors: list[FlakeError] = []
    for alias in node.names:
        if alias.name == "resources_rc":
            errors.append((node.lineno, node.col_offset, QGS408))
    return errors


def _get_qgs107(node: ast.FunctionDef) -> list["FlakeError"]:
    if node.name == "exec_":
        return [(node.lineno, node.col_offset, QGS107)]
    return []


def _get_qgs107_attribute(node: ast.Attribute) -> list["FlakeError"]:
    if node.attr == "exec_":
        return [(node.lineno, node.col_offset, QGS107)]
    return []


def _get_qgs110(node: Call) -> list["FlakeError"]:
    assert isinstance(node.func, ast.Attribute)
    if not (
        isinstance(node.func.value, ast.Name)
        and node.func.value.id == "processing"
        and node.func.attr == "run"
    ):
        return []

    is_child_keyword = None
    for keyword in node.keywords:
        if keyword.arg == "is_child_algorithm":
            is_child_keyword = keyword
            break

    if is_child_keyword is None or (
        isinstance(is_child_keyword.value, ast.Constant)
        and is_child_keyword.value.value is False
    ):
        return [(node.lineno, node.col_offset, QGS110)]

    return []


def _get_qgs201_and_qgs202(
    node: ast.Call, imported_names: set[str]
) -> list["FlakeError"]:
    assert isinstance(node.func, ast.Attribute)
    method_name = node.func.attr
    if (
        method_name
        and method_name in RETURN_VALUES_TO_CHECK
        and (_call_is_ignored(node) and not _call_used_as_condition(node))
    ):
        has_uppercase_characters = any(c.isupper() for c in method_name)

        # Now it is important to check whether method is really part of PyQgs API or
        # if it just has a same name
        if class_names := RETURN_VALUES_TO_CHECK[method_name]:
            # For class methods, use QGS201 only if the class is imported.
            suitable_class_names = class_names & imported_names

            if not suitable_class_names and not has_uppercase_characters:
                return []

            if len(suitable_class_names) > 1:
                method = "some of (" + ", ".join(
                    f"{class_name}.{method_name}()"
                    for class_name in sorted(suitable_class_names)
                )
                method += ")"
                rule = QGS201
            elif len(suitable_class_names) == 1:
                method = f"{next(iter(suitable_class_names))}.{method_name}()"
                rule = QGS201
            elif len(class_names) > 1:
                method = "some of (" + ", ".join(
                    f"{class_name}.{method_name}()"
                    for class_name in sorted(class_names)
                )
                method += ")"
                rule = QGS202
            else:
                method = f"{next(iter(class_names))}.{method_name}()"
                rule = QGS202
        else:
            if not has_uppercase_characters:
                return []

            rule = QGS202
            method = method_name

        return [(node.lineno, node.col_offset, rule.format(method=method))]
    return []


def _get_qgs401(node: ast.Name) -> list["FlakeError"]:
    if node.id == "qApp":
        return [(node.lineno, node.col_offset, QGS401)]
    return []


def _get_qgs406(node: ast.Name) -> list["FlakeError"]:
    if node.id == "QRegExp":
        return [(node.lineno, node.col_offset, QGS406)]
    return []


def _get_qgs402(
    node: ast.Attribute, existing_errors: list["FlakeError"]
) -> list["FlakeError"]:
    if not (isinstance(node.value, ast.Name) and node.value.id == "QVariant"):
        return []

    # If there is a NULL warning, let's not add another one here.
    for error in existing_errors:
        if "QGS4" in error[2] and "NULL" in error[2]:
            return []

    old_attr = node.attr
    if (
        old_attr == "Type"
        and hasattr(node, "parent")
        and isinstance(node.parent, ast.Attribute)
    ):
        old_attr = f"Type.{node.parent.attr}"
        new_attr = QMETATYPE_MAPPING.get(node.parent.attr, node.parent.attr)
    else:
        new_attr = QMETATYPE_MAPPING.get(old_attr, old_attr)
    return [
        (
            node.lineno,
            node.col_offset,
            QGS402.format(new=new_attr, old=old_attr),
        )
    ]


def _get_qgs403(node: ast.Attribute) -> list["FlakeError"]:
    if (
        isinstance(node.value, ast.Name)
        and (
            node.value.id,
            node.attr,
        )
        in DEPRECATED_RENAMED_ENUMS
    ):
        new = ".".join(
            [node.value.id, *DEPRECATED_RENAMED_ENUMS[(node.value.id, node.attr)]]
        )
        old = ".".join([node.value.id, node.attr])
        return [(node.lineno, node.col_offset, QGS403.format(new=new, old=old))]

    if (
        isinstance(node.value, ast.Name)
        and hasattr(node, "parent")
        and isinstance(node.parent, ast.Attribute)
        and (node.value.id, node.parent.attr) in DEPRECATED_RENAMED_ENUMS
    ):
        new = ".".join(
            [
                node.value.id,
                *DEPRECATED_RENAMED_ENUMS[(node.value.id, node.parent.attr)],
            ]
        )
        old = ".".join([node.value.id, node.attr, node.parent.attr])
        return [(node.lineno, node.col_offset, QGS403.format(new=new, old=old))]

    return []


def _get_qgs404(node: ast.Attribute) -> list["FlakeError"]:
    if node.attr != "width":
        return []

    # Check for QFontMetrics.width()
    # It can be a call QFontMetrics(font).width() or a name font_metrics.width()
    # The original code used object_types to track font metrics objects
    # Here we just check for 'width' attribute as a heuristic, or if it's called
    # on QFontMetrics
    if (
        isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id in ("QFontMetrics", "QFontMetricsF")
    ):
        return [(node.lineno, node.col_offset, QGS404)]

    if isinstance(node.value, ast.Name) and "metrics" in node.value.id.lower():
        # Heuristic for variables named like *_metrics
        return [(node.lineno, node.col_offset, QGS404)]

    return []


def _get_qgs405(node: ast.Subscript) -> list["FlakeError"]:
    if not (isinstance(node.value, ast.Attribute) and node.value.attr == "activated"):
        return []

    # activated[str]
    if isinstance(node.slice, ast.Name) and node.slice.id == "str":
        return [(node.lineno, node.col_offset, QGS405)]
    if isinstance(node.slice, ast.Constant) and node.slice.value == "str":
        # For python 3.9+ where ast.Index is deprecated
        # and slice is just a Constant
        return [(node.lineno, node.col_offset, QGS405)]
    return []


def _get_qgs404_call_attribute(node: Call) -> list["FlakeError"]:
    assert isinstance(node.func, ast.Attribute)
    if (
        node.func.attr == "width"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr.lower() in ("fontmetrics", "qfontmetrics")
    ):
        # obj.fontMetrics().width()
        return [(node.lineno, node.col_offset, QGS404)]
    return []


def _get_qgs407(node: Call) -> list["FlakeError"]:
    assert isinstance(node.func, ast.Attribute)
    if node.func.attr == "desktop":
        return [(node.lineno, node.col_offset, QGS407)]
    return []


def _get_qgs409(node: Call) -> list["FlakeError"]:
    assert isinstance(node.func, ast.Attribute)
    if node.func.attr == "addAction" and len(node.args) >= ADD_ACTION_ARG_COUNT:
        return [(node.lineno, node.col_offset, QGS409)]
    return []


def _get_qgs410(node: Call) -> list["FlakeError"]:
    assert isinstance(node.func, ast.Name)
    if node.func.id != "QVariant":
        return []

    if not node.args:
        return [(node.lineno, node.col_offset, QGS410.format(attr=""))]

    if (
        len(node.args) == 1
        and isinstance(node.args[0], ast.Attribute)
        and isinstance(node.args[0].value, ast.Name)
        and node.args[0].value.id == "QVariant"
    ):
        return [
            (
                node.lineno,
                node.col_offset,
                QGS410.format(attr=node.args[0].value.id),
            )
        ]

    return []


def _get_qgs411(node: Call) -> list["FlakeError"]:
    assert isinstance(node.func, ast.Name)
    if node.func.id == "QDateTime" and len(node.args) == QDATETIME_ARG_COUNT:
        # QDateTime(yyyy, mm, dd, hh, MM, ss, ms, ts)
        return [(node.lineno, node.col_offset, QGS411)]
    return []


def _get_qgs412(node: Call) -> list["FlakeError"]:
    assert isinstance(node.func, ast.Name)
    if node.func.id == "QDateTime" and (
        len(node.args) == 1
        and isinstance(node.args[0], ast.Call)
        and hasattr(node.args[0].func, "id")
        and node.args[0].func.id == "QDate"
    ):
        # QDateTime(QDate(...))
        return [(node.lineno, node.col_offset, QGS412)]
    return []


def _get_qgs108_and_qgs109(node: ast.Constant) -> list["FlakeError"]:
    if isinstance(node.value, str):
        if node.value == TEMPORARY_OUTPUT:
            return [(node.lineno, node.col_offset, QGS108)]

        if (
            node.value.startswith("TEMP")
            and "_" in node.value
            and _is_within_one_edit(node.value, TEMPORARY_OUTPUT)
        ):
            return [(node.lineno, node.col_offset, QGS109.format(old=node.value))]
    return []


def _remove_qgs402_qmetatype_errors(errors: list["FlakeError"]) -> None:
    for error in errors[:]:
        if "QGS4" in error[2] and "'QMetaType." in error[2]:
            errors.remove(error)


def _is_within_one_edit(actual: str, expected: str) -> bool:
    if actual == expected:
        return True

    len_actual = len(actual)
    len_expected = len(expected)
    if abs(len_actual - len_expected) > 1:
        return False

    if len_actual == len_expected:
        mismatches = sum(1 for a, b in zip(actual, expected, strict=True) if a != b)
        return mismatches <= 1

    if len_actual < len_expected:
        actual, expected = expected, actual
        len_actual, len_expected = len_expected, len_actual

    idx_actual = 0
    idx_expected = 0
    found_diff = False
    while idx_actual < len_actual and idx_expected < len_expected:
        if actual[idx_actual] == expected[idx_expected]:
            idx_actual += 1
            idx_expected += 1
            continue
        if found_diff:
            return False
        found_diff = True
        idx_actual += 1

    return True


def _call_is_ignored(node: ast.Call) -> bool:
    return isinstance(getattr(node, "parent", None), ast.Expr)


def _call_used_as_condition(node: ast.Call) -> bool:
    current: ast.AST = node
    parent = getattr(node, "parent", None)
    while parent is not None:
        if isinstance(parent, (ast.Subscript, ast.Attribute)):
            return False
        if isinstance(
            parent,
            (ast.UnaryOp, ast.BoolOp, ast.Compare, ast.BinOp, ast.NamedExpr),
        ):
            current = parent
            parent = getattr(current, "parent", None)
            continue
        if (
            isinstance(parent, (ast.If, ast.While, ast.Assert))
            and parent.test is current
        ):
            return True
        break
    return False


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[FlakeError] = []
        self.imported_names: set[str] = set()

    def previsit_imports(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        self.imported_names.add(alias.name)
                self._visit_import_from(node)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "." not in alias.name:
                        self.imported_names.add(alias.name)
                self._visit_import(node)

    def _visit_import_from(self, node: ast.ImportFrom) -> None:
        self.errors += _test_module_at_import_from("QGS101", node, _test_qgis_module)
        self.errors += _test_module_at_import_from("QGS103", node, _test_pyqt_module)
        self.errors += _get_qgs406_import_from(node)
        self.errors += _get_qgs408_import_from(node)

    def _visit_import(self, node: Import) -> None:
        self.errors += _test_module_at_import("QGS102", node, _test_qgis_module)
        self.errors += _test_module_at_import("QGS104", node, _test_pyqt_module)
        self.errors += _get_qgs106(node)
        self.errors += _get_qgs406_import(node)
        self.errors += _get_qgs408_import(node)

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        self.errors += _get_qgs105(node)
        self.errors += _get_qgs107(node)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        self.errors += _get_qgs401(node)
        self.errors += _get_qgs406(node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.errors += _get_qgs107_attribute(node)
        self.errors += _get_qgs402(node, self.errors)
        self.errors += _get_qgs403(node)
        self.errors += _get_qgs404(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute):
            self.errors += _get_qgs404_call_attribute(node)
            self.errors += _get_qgs407(node)
            self.errors += _get_qgs409(node)
            self.errors += _get_qgs110(node)
            self.errors += _get_qgs201_and_qgs202(node, self.imported_names)
        elif isinstance(node.func, ast.Name):
            qgs410_errors = _get_qgs410(node)
            if qgs410_errors:
                self.errors += qgs410_errors
                # There might be QMetaType error as well, let's remove it.
                _remove_qgs402_qmetatype_errors(self.errors)

            self.errors += _get_qgs411(node)
            self.errors += _get_qgs412(node)

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.errors += _get_qgs405(node)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        self.errors += _get_qgs108_and_qgs109(node)
        self.generic_visit(node)


class Plugin:
    name = __name__
    version = importlib_metadata.version("flake8_qgis")

    def __init__(self, tree: ast.AST) -> None:
        self._tree = tree

    def run(self) -> Generator[tuple[int, int, str, type[Any]], None, None]:
        visitor = Visitor()

        # Pre-collect imported names to be sure those are already collected
        # when needed
        visitor.previsit_imports(self._tree)

        # Add parent
        for node in ast.walk(self._tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node  # type: ignore[attr-defined]
        visitor.visit(self._tree)

        for line, col, msg in visitor.errors:
            yield line, col, msg, type(self)
