"""Tests for environment configuration."""

import pytest
from pydantic import ValidationError

from worker.config.settings import Settings


def test_settings_have_secure_processing_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in (
        "MAX_FILE_SIZE",
        "MAX_ARCHIVE_EXTRACTED_SIZE",
        "MAX_ARCHIVE_FILES",
        "MAX_ARCHIVE_NESTING_DEPTH",
        "QUARANTINE_PREFIX",
        "TRUSTED_PREFIX",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings(_env_file=None)

    assert settings.max_file_size == 50 * 1024 * 1024
    assert settings.max_archive_extracted_size == 200 * 1024 * 1024
    assert settings.max_archive_files == 1_000
    assert settings.max_archive_nesting_depth == 3
    assert settings.quarantine_prefix == "quarantine/"
    assert settings.trusted_prefix == "trusted/"


def test_settings_reject_invalid_port() -> None:
    with pytest.raises(ValidationError):
        Settings(port=0, _env_file=None)
