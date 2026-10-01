"""Filename-extension validation for the security scanning pipeline.

An allowed extension is only a preliminary signal.  A successful check here
does not establish the file's type; later scanner layers must still inspect its
MIME type, signature, and structure.
"""

from collections.abc import Iterable
from pathlib import PurePath

DEFAULT_SUPPORTED_EXTENSIONS = frozenset({".jpeg", ".jpg", ".png", ".txt", ".zip"})


class UnsupportedExtensionError(ValueError):
    """Raised when a filename does not end in a configured extension."""

    reason = "UNSUPPORTED_EXTENSION"
    layer = "EXTENSION"

    def __init__(self, filename: str, extension: str) -> None:
        self.filename = filename
        self.extension = extension
        display_extension = extension or "<none>"
        super().__init__(f"Unsupported file extension: {display_extension}")


class ExtensionChecker:
    """Check a filename's final suffix against an explicit allowlist."""

    def __init__(
        self,
        supported_extensions: Iterable[str] = DEFAULT_SUPPORTED_EXTENSIONS,
    ) -> None:
        self.supported_extensions = _normalize_allowlist(supported_extensions)

    def is_supported(self, filename: str) -> bool:
        """Return whether ``filename`` has an allowed final extension."""
        return self.extension_for(filename) in self.supported_extensions

    def validate(self, filename: str) -> str:
        """Return the normalized extension or raise a permanent rejection."""
        extension = self.extension_for(filename)
        if extension not in self.supported_extensions:
            raise UnsupportedExtensionError(filename, extension)
        return extension

    @staticmethod
    def extension_for(filename: str) -> str:
        """Extract a case-insensitive final extension from a filename."""
        return PurePath(filename.strip()).suffix.casefold()


def _normalize_allowlist(extensions: Iterable[str]) -> frozenset[str]:
    """Normalize and validate extension-checker configuration."""
    normalized = frozenset(extension.strip().casefold() for extension in extensions)
    if not normalized:
        raise ValueError("At least one supported extension must be configured")
    if any(
        not extension.startswith(".") or extension == "." or "/" in extension or "\\" in extension
        for extension in normalized
    ):
        raise ValueError("Supported extensions must be dot-prefixed filename suffixes")
    return normalized
