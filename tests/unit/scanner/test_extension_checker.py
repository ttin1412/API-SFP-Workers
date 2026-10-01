"""Unit tests for the extension scanner layer."""

import pytest

from worker.scanner.extension_checker import ExtensionChecker, UnsupportedExtensionError


@pytest.mark.parametrize("filename", ["photo.jpeg", "photo.jpg", "image.png"])
def test_accepts_supported_image_extensions(filename: str) -> None:
    checker = ExtensionChecker()

    assert checker.is_supported(filename)
    assert checker.validate(filename) == f".{filename.rsplit('.', maxsplit=1)[1]}"


def test_extension_matching_is_case_insensitive() -> None:
    checker = ExtensionChecker()

    assert checker.validate("PHOTO.JPEG") == ".jpeg"


@pytest.mark.parametrize(
    ("filename", "extension"),
    [
        ("payload.exe", ".exe"),
        ("photo.jpeg.exe", ".exe"),
        ("README", ""),
        (".jpg", ""),
    ],
)
def test_rejects_unsupported_and_disguised_extensions(
    filename: str,
    extension: str,
) -> None:
    checker = ExtensionChecker()

    assert not checker.is_supported(filename)
    with pytest.raises(UnsupportedExtensionError) as error:
        checker.validate(filename)

    assert error.value.reason == "UNSUPPORTED_EXTENSION"
    assert error.value.layer == "EXTENSION"
    assert error.value.extension == extension


def test_uses_a_configurable_allowlist() -> None:
    checker = ExtensionChecker([".PDF", " .csv "])

    assert checker.is_supported("report.pdf")
    assert checker.is_supported("data.CSV")
    assert not checker.is_supported("photo.jpg")


@pytest.mark.parametrize("extensions", [[], ["jpg"], ["."], [".jp/g"]])
def test_rejects_invalid_allowlist_configuration(extensions: list[str]) -> None:
    with pytest.raises(ValueError):
        ExtensionChecker(extensions)
