"""1.11.1020's site bump (b9bfb63b) left /download/ saying "Current version: v1.11.1019." and CI failed; 96a727ba4 fixed the
page by hand. The bump now moves that line: its shapes, applied to the live download page, leave no old-version mention.
Both tests fail on the bump script before this change."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("bump_site_version", ROOT / "scripts" / "bump_site_version.py")
bump = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bump)


def test_the_download_page_is_one_of_the_bumped_files():
    assert bump.FILES.get("download/index.html") == 0


def test_the_shapes_move_every_version_mention_on_the_download_page():
    page = (ROOT / "download" / "index.html").read_text(encoding="utf-8")
    old = bump.current_version()
    assert old and f"Current version: v{old}." in page
    for a, b in bump.shapes(old, "9.9.9").items():
        page = page.replace(a, b)
    assert bump._pointer_count(page, old) == 0
    assert "Current version: v9.9.9." in page
