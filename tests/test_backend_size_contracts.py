from __future__ import annotations

from pathlib import Path

from scripts import check_size_limits


def write_lines(path: Path, line_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join("x = 1" for _ in range(line_count)) + "\n", encoding="utf-8")


def test_strict_checker_fails_on_oversized_backend_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    oversized_file = tmp_path / "backend" / "app" / "oversized.py"
    write_lines(oversized_file, 1001)

    exit_code = check_size_limits.main(["--root", "backend/app", "--strict"])

    assert exit_code == 1


def test_checker_excludes_cache_venv_generated_and_migration_artifacts(tmp_path: Path) -> None:
    excluded_files = [
        tmp_path / "backend" / "app" / "__pycache__" / "cached.py",
        tmp_path / "backend" / "app" / "generated" / "schema.py",
        tmp_path / "backend" / "app" / "migrations" / "0001_snapshot.py",
        tmp_path / "backend" / "app" / "service_pb2.py",
        tmp_path / "venv" / "lib" / "third_party.py",
    ]
    included_file = tmp_path / "backend" / "app" / "included.py"
    for path in excluded_files:
        write_lines(path, 1001)
    write_lines(included_file, 10)

    scanned_files = list(check_size_limits.iter_python_files(tmp_path))

    assert scanned_files == [included_file]


def test_checker_reports_ast_span_and_exact_token_count(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    source_file = tmp_path / "backend" / "app" / "large_function.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text(
        "def large_function():\n"
        "    total = 0\n"
        + "\n".join(f"    total += {index}" for index in range(20))
        + "\n    return total\n",
        encoding="utf-8",
    )

    exit_code = check_size_limits.main(
        ["--root", "backend/app", "--strict", "--max-function-tokens", "10"]
    )
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "function large_function spans" in output
    assert "AST lines" in output
    assert "tokens (limit: 10)" in output


def test_allow_known_oversized_suppresses_blocking_exit(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    oversized_file = tmp_path / "backend" / "app" / "main.py"
    write_lines(oversized_file, 1001)

    exit_code = check_size_limits.main(
        [
            "--root",
            "backend/app",
            "--strict",
            "--allow-known-oversized",
            "backend/app/main.py",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "ALLOWED [file-lines]" in output
    assert "0 blocking violation(s), 1 allowed known oversized finding(s)" in output
