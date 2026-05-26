from prefect_grace.platform.scope_guard import (
    has_overlap,
    is_path_allowed,
    is_path_frozen,
    normalize_path,
    should_block_diff,
)


def test_normalize_path() -> None:
    assert normalize_path("/opt/astro-project/backend/app.py") == "backend/app.py"
    assert normalize_path("opt/astro-project/backend/app.py") == "backend/app.py"
    assert normalize_path("./backend/app.py") == "backend/app.py"
    assert normalize_path("backend\\app.py") == "backend/app.py"


def test_is_path_allowed() -> None:
    allowed = [
        "prefect_grace/project.yaml",
        "prefect_grace/policies/*.yaml",
        "prefect_grace/platform/**",
    ]

    assert is_path_allowed("prefect_grace/project.yaml", allowed)
    assert is_path_allowed("prefect_grace/policies/verification.yaml", allowed)
    assert is_path_allowed("prefect_grace/platform/scope_guard.py", allowed)
    assert is_path_allowed("prefect_grace/platform/nested/dir/file.py", allowed)

    assert not is_path_allowed("prefect_grace/project.yaml.bak", allowed)
    assert not is_path_allowed("prefect_grace/project.yaml/nested", allowed)
    assert not is_path_allowed("prefect_grace/cli.py", allowed)
    assert not is_path_allowed("backend/main.py", allowed)


def test_is_path_frozen() -> None:
    frozen = [
        "backend/**",
        "frontend/**",
    ]

    assert is_path_frozen("backend/main.py", frozen)
    assert is_path_frozen("frontend/package.json", frozen)
    assert not is_path_frozen("prefect_grace/project.yaml", frozen)


def test_has_overlap() -> None:
    # Overlapping allowed write scopes
    assert has_overlap(["prefect_grace/platform/**"], ["prefect_grace/platform/scope_guard.py"])
    assert has_overlap(["backend/**"], ["backend/sub/folder/**"])
    assert not has_overlap(["backend/**"], ["frontend/**"])


def test_should_block_diff() -> None:
    allowed = ["prefect_grace/project.yaml", "prefect_grace/platform/**"]
    frozen = ["prefect_grace/platform/frozen/**"]

    # Allowed & not frozen
    assert not should_block_diff(
        ["prefect_grace/project.yaml", "prefect_grace/platform/scope_guard.py"],
        allowed,
        frozen,
    )

    # Not allowed
    assert should_block_diff(
        ["prefect_grace/project.yaml", "prefect_grace/cli.py"], allowed, frozen
    )

    # Frozen
    assert should_block_diff(
        ["prefect_grace/platform/frozen/config.py"], allowed, frozen
    )
