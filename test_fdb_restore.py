import io
import zipfile
from pathlib import Path

import pytest

import fdb_restore


# ── 5.1 find_backup_files ────────────────────────────────────────────────────

def test_find_backup_files_matches_pattern(tmp_path):
    (tmp_path / "TB_backup.fbk.zip").touch()
    (tmp_path / "TB_old.fbk.zip").touch()
    (tmp_path / "other.zip").touch()
    (tmp_path / "TB_backup.fbk").touch()
    result = fdb_restore.find_backup_files(tmp_path)
    assert [f.name for f in result] == ["TB_backup.fbk.zip", "TB_old.fbk.zip"]


def test_find_backup_files_empty(tmp_path):
    assert fdb_restore.find_backup_files(tmp_path) == []


# ── 5.2 select_backup_file ───────────────────────────────────────────────────

def test_select_backup_file_zero_exits():
    with pytest.raises(SystemExit):
        fdb_restore.select_backup_file([])


def test_select_backup_file_one_returns_directly(tmp_path, capsys):
    f = tmp_path / "TB_only.fbk.zip"
    f.touch()
    result = fdb_restore.select_backup_file([f])
    assert result == f
    assert "TB_only.fbk.zip" in capsys.readouterr().out


def test_select_backup_file_many_prompts(tmp_path, monkeypatch):
    files = [tmp_path / f"TB_{i}.fbk.zip" for i in range(3)]
    for f in files:
        f.touch()
    monkeypatch.setattr("builtins.input", lambda _: "2")
    result = fdb_restore.select_backup_file(files)
    assert result == files[1]


def test_select_backup_file_many_retries_on_bad_input(tmp_path, monkeypatch):
    files = [tmp_path / f"TB_{i}.fbk.zip" for i in range(2)]
    for f in files:
        f.touch()
    responses = iter(["x", "0", "3", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    result = fdb_restore.select_backup_file(files)
    assert result == files[0]


# ── 5.3 extract_fbk ──────────────────────────────────────────────────────────

def test_extract_fbk_returns_temp_file(tmp_path):
    zip_path = tmp_path / "TB_test.fbk.zip"
    dummy_content = b"dummy fbk content"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("TB6DATENBANK.fbk", dummy_content)

    fbk_path = fdb_restore.extract_fbk(zip_path)
    try:
        assert fbk_path.exists()
        assert fbk_path.suffix == ".fbk"
        assert fbk_path.read_bytes() == dummy_content
    finally:
        fbk_path.unlink(missing_ok=True)


def test_extract_fbk_no_fbk_inside_exits(tmp_path):
    zip_path = tmp_path / "TB_empty.fbk.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("README.txt", "no fbk here")
    with pytest.raises(SystemExit):
        fdb_restore.extract_fbk(zip_path)


# ── patch_fbk ────────────────────────────────────────────────────────────────

def test_patch_fbk_replaces_needle(tmp_path):
    NEEDLE = b"\x00\x00\x2b\x04\xff\xff\xff\xff"
    PATCH  = b"\x00\x00\x2b\x04\x00\x00\x00\x00"
    fbk = tmp_path / "test.fbk"
    fbk.write_bytes(b"header" + NEEDLE + b"middle" + NEEDLE + b"end")
    count = fdb_restore.patch_fbk(fbk)
    assert count == 2
    assert fbk.read_bytes() == b"header" + PATCH + b"middle" + PATCH + b"end"


def test_patch_fbk_no_match_leaves_file_unchanged(tmp_path):
    fbk = tmp_path / "test.fbk"
    original = b"no needle here"
    fbk.write_bytes(original)
    count = fdb_restore.patch_fbk(fbk)
    assert count == 0
    assert fbk.read_bytes() == original


# ── 5.4 resolve_password ─────────────────────────────────────────────────────

def test_resolve_password_isc(monkeypatch):
    monkeypatch.setenv("ISC_PASSWORD", "secret1")
    monkeypatch.delenv("ISQL_PASSWORD", raising=False)
    assert fdb_restore.resolve_password() == "secret1"


def test_resolve_password_isql_fallback(monkeypatch):
    monkeypatch.delenv("ISC_PASSWORD", raising=False)
    monkeypatch.setenv("ISQL_PASSWORD", "secret2")
    assert fdb_restore.resolve_password() == "secret2"


def test_resolve_password_prompts_when_absent(monkeypatch):
    monkeypatch.delenv("ISC_PASSWORD", raising=False)
    monkeypatch.delenv("ISQL_PASSWORD", raising=False)
    monkeypatch.setattr("getpass.getpass", lambda _: "typed_pw")
    assert fdb_restore.resolve_password() == "typed_pw"
