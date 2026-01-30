from pathlib import Path

from scripts.generate_qgis_return_methods import (
    parse_qgis_sip_methods,
    write_return_methods_json,
)


def test_parse_qgis_sip_methods(tmp_path: Path) -> None:
    root = tmp_path / "qgis"
    root.mkdir()
    sip = root / "core.sip"
    sip.write_text(
        """
class Foo
{
  public:
    bool writeToFile( const QString &path, QString *errorMessage /Out/ = 0 );
%Docstring
Writes the data to ``path``, returns ``True`` on success.
%End

    bool saveWithDetails( QString *error /Out/ = 0 );
%Docstring
:return: - ``True`` if save was successful
         - error: a message describing the failure
%End

    bool transform();
%Docstring
:return: - returns true if no errors
%End

    bool run();
%Docstring
:return: - returns true if no errors but name is too common
%End

    int resultCount() const;
%Docstring
:return: result count
%End

    int resultCode() const;
%Docstring
:return: confirmResult
%End

    int nope() const;
%Docstring
No return keywords here.
%End

    int falseSuccess() const;
%Docstring
:return: False which returns with success
No return keywords here.
%End
};
""",
        encoding="utf-8",
    )

    data = parse_qgis_sip_methods(root)
    assert data["methods_to_check"] == [
        "Foo.resultCode",
        "Foo.saveWithDetails",
        "Foo.transform",
        "Foo.writeToFile",
    ]


def test_write_return_methods_json(tmp_path: Path) -> None:
    output = tmp_path / "return_methods.json"
    data = {
        "methods_to_check": ["a"],
    }

    write_return_methods_json(data, output)
    assert output.exists()
    assert output.read_text(encoding="utf-8").endswith("\n")
