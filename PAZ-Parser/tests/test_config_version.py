"""`paz_config.json` versions: migration on load, the backup of a broken config, downgrades."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import api.bdo_config as bdo_config
import api.config_migrations as config_migrations
from api.bdo_config import BACKUP_NAME, load_config, save_config
from api.config_migrations import VERSION_KEY, current_version, migrate


@pytest.fixture
def config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "paz_config.json"
    monkeypatch.setattr(bdo_config, "config_file", lambda: path)
    return path


def _rename_dark(cfg: dict) -> dict:
    """1 -> 2: `dark` became `theme`."""
    cfg["theme"] = "dark" if cfg.pop("dark", False) else "light"
    return cfg


def _drop_zoom(cfg: dict) -> dict:
    """2 -> 3: `zoom` is gone."""
    cfg.pop("zoom", None)
    return cfg


@pytest.fixture
def two_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_migrations, "MIGRATIONS", (_rename_dark, _drop_zoom))


def _write(path: Path, cfg: object) -> None:
    path.write_text(json.dumps(cfg), encoding="utf-8")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_step_is_a_function() -> None:
    assert all(callable(step) for step in config_migrations.MIGRATIONS)
    assert current_version() == len(config_migrations.MIGRATIONS) + 1


def test_config_without_a_version_is_version_1(config_file: Path, two_steps: None) -> None:
    _write(config_file, {"dark": True, "zoom": 2, "last_folder": "C:/Paz"})

    assert load_config() == {"theme": "dark", "last_folder": "C:/Paz", VERSION_KEY: 3}


def test_each_step_runs_once_from_the_saved_version(config_file: Path, two_steps: None) -> None:
    _write(config_file, {VERSION_KEY: 2, "dark": True, "zoom": 2})

    # Only 2 -> 3 runs: `dark` was already handled by the 1 -> 2 step.
    assert load_config() == {VERSION_KEY: 3, "dark": True}


def test_migrated_config_is_saved(config_file: Path, two_steps: None) -> None:
    _write(config_file, {"dark": False})

    load_config()

    assert _read(config_file) == {"theme": "light", VERSION_KEY: 3}


def test_migrate_leaves_its_input_alone(two_steps: None) -> None:
    saved = {"dark": True, "zoom": 2}

    migrate(saved)

    assert saved == {"dark": True, "zoom": 2}


def test_save_writes_the_current_version(config_file: Path) -> None:
    save_config({"language": "de"})

    assert _read(config_file) == {VERSION_KEY: current_version(), "language": "de"}


@pytest.mark.parametrize(
    "content",
    ["{not json", "[1, 2]", json.dumps({VERSION_KEY: "2"}), json.dumps({VERSION_KEY: 0})],
    ids=["broken-json", "not-an-object", "version-text", "version-zero"],
)
def test_unreadable_config_is_backed_up(config_file: Path, content: str) -> None:
    config_file.write_text(content, encoding="utf-8")

    assert load_config() == {}
    assert not config_file.exists()
    assert (config_file.parent / BACKUP_NAME).read_text(encoding="utf-8") == content


def test_failed_step_backs_up_the_config(config_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(cfg: dict) -> dict:
        raise KeyError("theme")

    monkeypatch.setattr(config_migrations, "MIGRATIONS", (broken,))
    _write(config_file, {"dark": True})

    assert load_config() == {}
    assert _read(config_file.parent / BACKUP_NAME) == {"dark": True}


def test_save_after_backup_starts_a_new_config(config_file: Path) -> None:
    config_file.write_text("{not json", encoding="utf-8")

    save_config({"language": "fr"})

    assert _read(config_file) == {VERSION_KEY: current_version(), "language": "fr"}
    assert (config_file.parent / BACKUP_NAME).read_text(encoding="utf-8") == "{not json"


def test_newer_config_is_read_as_is_and_keeps_its_keys(config_file: Path) -> None:
    newer = {VERSION_KEY: current_version() + 5, "language": "en", "from_the_future": [1, 2]}
    _write(config_file, newer)

    assert load_config() == newer

    save_config({"language": "de"})

    assert _read(config_file) == {**newer, "language": "de"}
