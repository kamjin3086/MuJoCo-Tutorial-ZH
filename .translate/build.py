"""Build Chinese copies of the tutorial notebooks.

Markdown cells are replaced by the translations in `.translate/zh_src/<name>.txt`;
code cells are copied byte-for-byte from the original notebook. Nothing is executed.

Usage (run from the repo root):

    .venv\\Scripts\\python.exe .translate\\build.py dump    # extract markdown -> .translate/en/<name>.txt
    .venv\\Scripts\\python.exe .translate\\build.py build    # splice   -> tutorial\\zh\\<name>.ipynb
    .venv\\Scripts\\python.exe .translate\\build.py check    # verify the built notebooks

Translation file format (UTF-8), one block per markdown cell:

    ###CELL 0
    translated markdown for cell 0 ...

    ###CELL 3
    translated markdown for cell 3 ...

Every markdown cell index of the notebook must appear exactly once. Blank lines at
the block edges are trimmed; everything else is used verbatim.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "tutorial"
OUT_DIR = SRC_DIR / "zh"
EN_DIR = Path(__file__).resolve().parent / "en"
ZH_DIR = Path(__file__).resolve().parent / "zh_src"
MARKER = re.compile(r"^###CELL (\d+)$")


def notebooks() -> list[Path]:
    return sorted(p for p in SRC_DIR.glob("*.ipynb"))


def markdown_indices(nb) -> list[int]:
    return [i for i, c in enumerate(nb.cells) if c.cell_type == "markdown"]


def parse_translation(path: Path) -> dict[int, str]:
    """Parse a translation file into {cell_index: text}."""
    blocks: dict[int, str] = {}
    current: int | None = None
    buf: list[str] = []

    def flush() -> None:
        if current is not None:
            if current in blocks:
                raise ValueError(f"{path.name}: duplicate ###CELL {current}")
            blocks[current] = "\n".join(buf).strip("\n")

    for line in path.read_text(encoding="utf-8").splitlines():
        m = MARKER.match(line.strip())
        if m:
            flush()
            current = int(m.group(1))
            buf = []
        elif current is not None:
            buf.append(line)
    flush()
    return blocks


def dump() -> None:
    EN_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for path in notebooks():
        nb = nbformat.read(str(path), as_version=4)
        out: list[str] = []
        for i in markdown_indices(nb):
            out.append(f"###CELL {i}")
            out.append(nb.cells[i].source.strip("\n"))
            out.append("")
        total += len(out)
        (EN_DIR / path.name).with_suffix(".txt").write_text("\n".join(out), encoding="utf-8")
    print(f"dumped markdown from {len(notebooks())} notebooks")


def build() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    for path in notebooks():
        zh_file = ZH_DIR / (path.stem + ".txt")
        if not zh_file.exists():
            print(f"  SKIP {path.name}: no {zh_file.relative_to(ROOT)}")
            continue
        nb = nbformat.read(str(path), as_version=4)
        wanted = markdown_indices(nb)
        translations = parse_translation(zh_file)

        missing = [i for i in wanted if i not in translations]
        extra = [i for i in translations if i not in wanted]
        if missing or extra:
            failures.append(f"{path.name}: missing cells {missing}, unexpected cells {extra}")
            continue

        for i in wanted:
            text = translations[i]
            if not text.strip():
                failures.append(f"{path.name}: cell {i} translated to empty text")
                continue
            nb.cells[i].source = text.splitlines(keepends=True)

        for cell in nb.cells:
            if cell.cell_type == "code":
                cell.outputs = []
                cell.execution_count = None

        nb.metadata.setdefault("original_notebook", f"../../{SRC_DIR.name}/{path.name}")
        nbformat.validator.normalize(nb)  # older notebooks ship without cell ids
        dst = OUT_DIR / path.name
        nbformat.write(nb, str(dst))
        print(f"  OK  {path.name} -> tutorial/zh/{path.name}")
    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  " + f)
        return 1
    return 0


def cjk_count(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def fenced_blocks(md: str) -> list[str]:
    return re.findall(r"```.*?```", md, re.S)


def link_targets(md: str) -> list[str]:
    return re.findall(r"\]\(([^)\s]+)", md)


def headings(md: str) -> list[str]:
    return [ln for ln in md.splitlines() if ln.startswith("#")]


def table_rows(md: str) -> list[str]:
    return [ln for ln in md.splitlines() if ln.lstrip().startswith("|")]


FENCE = re.compile(r"```.*?```", re.S)
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+\$", re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK_TARGET = re.compile(r"\]\([^)]*\)")
HTML_TAG = re.compile(r"<[^>]+>")


def prose_only(md: str) -> str:
    """Strip the parts of a markdown cell that legitimately stay in English."""
    text = FENCE.sub(" ", md)
    text = MATH.sub(" ", text)
    text = INLINE_CODE.sub(" ", text)
    text = LINK_TARGET.sub(" ", text)
    text = HTML_TAG.sub(" ", text)
    return text


def check() -> int:
    problems: list[str] = []
    built = list(OUT_DIR.glob("*.ipynb"))
    if not built:
        print("nothing built yet")
        return 1
    for zh_path in sorted(built):
        src_path = SRC_DIR / zh_path.name
        if not src_path.exists():
            problems.append(f"{zh_path.name}: no matching source notebook")
            continue
        src = nbformat.read(str(src_path), as_version=4)
        zh = nbformat.read(str(zh_path), as_version=4)
        nbformat.validate(zh)
        if len(src.cells) != len(zh.cells):
            problems.append(f"{zh_path.name}: cell count {len(zh.cells)} != source {len(src.cells)}")
            continue
        for i, (a, b) in enumerate(zip(src.cells, zh.cells)):
            if a.cell_type != b.cell_type:
                problems.append(f"{zh_path.name}: cell {i} type changed")
            elif a.cell_type == "code":
                if a.source != b.source:
                    problems.append(f"{zh_path.name}: cell {i} CODE DIFFERS from source")
            else:
                if fenced_blocks(a.source) != fenced_blocks(b.source):
                    problems.append(f"{zh_path.name}: cell {i} fenced code blocks differ from source")
                if link_targets(a.source) != link_targets(b.source):
                    problems.append(f"{zh_path.name}: cell {i} link targets differ from source")
                if len(headings(a.source)) != len(headings(b.source)):
                    problems.append(
                        f"{zh_path.name}: cell {i} has {len(headings(b.source))} headings, source has {len(headings(a.source))}"
                    )
                if len(table_rows(a.source)) != len(table_rows(b.source)):
                    problems.append(
                        f"{zh_path.name}: cell {i} has {len(table_rows(b.source))} table rows, source has {len(table_rows(a.source))}"
                    )
                stripped = prose_only(b.source)
                cjk = cjk_count(stripped)
                words = re.findall(r"[A-Za-z][A-Za-z'\-]*", stripped)
                # longest run of consecutive ASCII words (a translated line leaves at
                # most a lone term or a dotted domain behind)
                longest = max(
                    (len(re.findall(r"[A-Za-z][A-Za-z'\-]*", m.group(0))) for m in
                     re.finditer(r"[A-Za-z][A-Za-z'\-]*(?:\s+[A-Za-z][A-Za-z'\-]*)*", stripped)),
                    default=0,
                )
                if cjk == 0 and words:
                    problems.append(f"{zh_path.name}: cell {i} has no Chinese at all")
                elif longest >= 5:
                    problems.append(
                        f"{zh_path.name}: cell {i} looks untranslated (longest English run = {longest} words)"
                    )
        print(f"  checked {zh_path.name}: {len(zh.cells)} cells, code identical")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  " + p)
        return 1
    print("all checks passed")
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    return {"dump": lambda: 0 if dump() is None else 0, "build": build, "check": check}[mode]()


if __name__ == "__main__":
    raise SystemExit(main())
