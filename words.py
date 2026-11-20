"""The word list: what is saved on the phone, and how it gets there.

One module owns the file's shape, the PC's address, the cache check, the
download and the offline fallback. The screens ask for categories; they never
see JSON, and never have to know which of those steps happened.
"""

import json
import pathlib

import httpx

from game import Category

HERE = pathlib.Path(__file__).parent
SAVED = HERE / "local_words.json"  # the copy the phone keeps
ADDRESS = HERE / "pc_address.txt"  # last PC address the user typed


def use_storage(directory):
    """Keep the two files in a writable folder.

    On desktop that is already HERE, next to this file. In the APK the app is
    packed into a read-only archive, so app.py passes Flet's data directory
    before the first load. Both files are made only of what the phone received,
    so a fresh install starting empty is correct.
    """
    global SAVED, ADDRESS
    SAVED = pathlib.Path(directory) / "local_words.json"
    ADDRESS = pathlib.Path(directory) / "pc_address.txt"


def _saved():
    """The saved document exactly as it is on disk, or None."""
    try:
        return json.loads(SAVED.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _categories(document):
    """The document's categories, as the game's Category objects."""
    return [Category(cat["name"], cat["words"]) for cat in document["categories"]]


def load():
    """The saved categories. Empty when there are none, or the file is broken.

    A broken file counts as an empty one on purpose: the home screen then
    offers a sync, which overwrites it. The alternative is a crash on a screen
    whose refresh button has not been drawn yet.
    """
    document = _saved()
    if not document:
        return []
    try:
        return _categories(document)
    except (KeyError, TypeError):
        return []


def saved_address():
    """The PC address last used, or "" when there is none."""
    try:
        return ADDRESS.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _base(typed):
    """The typed address as a URL. http:// is added only when it is missing."""
    typed = typed.strip().rstrip("/")
    if typed.startswith(("http://", "https://")):
        return typed
    return "http://" + typed


def _write(document):
    """Write the document so an interrupted sync cannot leave half a file."""
    temp = SAVED.with_suffix(".tmp")
    temp.write_text(
        json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temp.replace(SAVED)


def _write_address(base):
    ADDRESS.write_text(base, encoding="utf-8")


def sync(typed):
    """Bring the newest word list from the PC.

    Returns (categories, message, ok). When the PC cannot be reached the saved
    categories come back with ok False, so the game stays playable.
    """
    # One empty-address message for every screen that can ask for a sync.
    if not typed.strip():
        return load(), "أدخل عنوان الحاسب من الإعدادات", False

    base = _base(typed)
    try:
        remote = httpx.get(f"{base}/version", timeout=5).json()["version"]
    except Exception:
        return load(), "تعذر الاتصال بالحاسب", False

    saved = _saved()
    if saved and saved.get("version") == remote:
        _write_address(base)
        return load(), f"الكلمات محدثة (نسخة {remote})", True

    # The download and the parse share one try: a half-good answer from the
    # PC is a failure, not a half-updated list.
    try:
        document = httpx.get(f"{base}/data", timeout=10).json()
        categories = _categories(document)
    except Exception:
        return load(), "تعذر الاتصال بالحاسب", False

    _write(document)
    _write_address(base)
    return categories, f"تم تنزيل نسخة {remote}", True
