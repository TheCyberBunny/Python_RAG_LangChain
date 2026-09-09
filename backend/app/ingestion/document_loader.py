"""
File-based Document loader.

Reads every file in a folder and turns the supported ones into
Document objects, replacing a hardcoded seed function as the source
of truth for the domain models.
"""

from datetime import date
from pathlib import Path  # the modern, object-oriented way to work with
                           # file paths - nicer than building path strings
                           # by hand with os.path.join

from app.core.exceptions import DocumentLoadError, UnsupportedFileTypeError
from app.models import Document, DocumentCategory

# A tuple of the frontmatter keys every document file must have.
# Referencing this constant in the check below (rather than repeating
# the five names inline) means adding a required field later is a
# one-line change.
REQUIRED_FIELDS = ("id", "title", "category", "owner_id", "last_reviewed_at")


def _parse_frontmatter(text: str, source: Path) -> tuple[dict[str, str], str]:
    """
    Split "key: value" header lines from the body, on the first line
    that's exactly "---". Returns (fields_dict, body_text).

    Leading underscore in the function name is Python's "internal use
    only" convention (no `private` keyword exists) - this helper isn't
    meant to be called from outside this module.
    """
    if "---" not in text:
        raise DocumentLoadError(f"{source.name}: missing '---' frontmatter separator")

    # str.partition splits on the FIRST occurrence and returns a
    # 3-tuple: (everything before, the separator itself, everything
    # after). The middle value is thrown away here with `_` - a
    # naming convention for "this value exists but I don't need it."
    header_block, _, body = text.partition("---")

    fields: dict[str, str] = {}
    for line in header_block.strip().splitlines():
        if ":" not in line:
            raise DocumentLoadError(f"{source.name}: malformed header line {line!r}")
        #the _ is a special variable name in Python that is used to indicate that the value is temporary or insignificant.
        # In this case, it is used to ignore the separator returned by the partition method(line 40).
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()

    # A list comprehension used to build a list of PROBLEMS rather than
    # results - still the same "keep what matches the condition" shape.
    missing = [field for field in REQUIRED_FIELDS if field not in fields]
    if missing:
        raise DocumentLoadError(f"{source.name}: missing required field(s) {missing}")

    return fields, body.strip()


def load_one_document(path: Path) -> Document:
    # Check the extension BEFORE reading the file - cheaper than
    # opening a file we already know we can't use.
    if path.suffix != ".md":
        raise UnsupportedFileTypeError(
            f"{path.name}: unsupported file type {path.suffix!r} (only .md is supported)"
        )

    text = path.read_text(encoding="utf-8")
    fields, body = _parse_frontmatter(text, path)

    # Each conversion below is wrapped in its own try/except so the
    # error message can say exactly WHICH field was bad, rather than a
    # generic "something in this file didn't parse."
    try:
        category = DocumentCategory(fields["category"])
    except ValueError as exc:
        # "raise ... from exc" chains the new exception to the original
        # one - the traceback shows both, instead of hiding the real
        # low-level cause. This is the Python equivalent of Java's
        # `throw new DocumentLoadError(...).initCause(originalException)`.
        raise DocumentLoadError(
            f"{path.name}: unknown category {fields['category']!r}"
        ) from exc

    try:
        last_reviewed_at = date.fromisoformat(fields["last_reviewed_at"])
    except ValueError as exc:
        raise DocumentLoadError(
            f"{path.name}: invalid last_reviewed_at date {fields['last_reviewed_at']!r}"
        ) from exc

    try:
        document_id = int(fields["id"])
        owner_id = int(fields["owner_id"])
    except ValueError as exc:
        raise DocumentLoadError(f"{path.name}: id and owner_id must be integers") from exc

    return Document(document_id, fields["title"], category, body, owner_id, last_reviewed_at)


def load_documents_from_folder(folder_path: str | Path) -> list[Document]:
    # Path(...) accepts either a string or an existing Path - this is
    # what lets callers pass a plain string like "docs" without caring
    # about the Path/str distinction themselves.
    folder = Path(folder_path)
    documents: list[Document] = []

    for path in sorted(folder.iterdir()):
        if path.is_dir():
            continue
        try:
            documents.append(load_one_document(path))
        except DocumentLoadError as exc:
            # This is the "instead of crashing" part of today's topic:
            # one bad file gets logged and skipped, and the loop moves
            # on to the next one, rather than an unhandled exception
            # killing the entire load for every other file too.
            print(f"  SKIPPED {path.name}: {exc}")

    return documents