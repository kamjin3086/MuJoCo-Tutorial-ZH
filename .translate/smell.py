"""Machine pass over the Chinese translation sources: flag translation smells.

Reports, per file and cell:
  被-passive / 进行 / 让我们 (translation-ese)
  duplicated term annotations  中文（term） appearing more than once
  half-width punctuation glued to Chinese text
  missing space between Chinese and Latin/inline-code
Read-only: it never edits anything.
"""
from __future__ import annotations

import re
from pathlib import Path

ZH_DIR = Path(__file__).resolve().parent / "zh_src"

CJK = r"[㐀-䶿一-鿿]"
ANNOT = re.compile(r"[一-鿿]+（([A-Za-z][A-Za-z \-/]*)）")
HAWIDTH = re.compile(rf"({CJK})[,.;:!?]|\s[,.;:!?]")
GAP = re.compile(rf"({CJK})([A-Za-z`0-9])|([A-Za-z`0-9])({CJK})")
SMELLS = {
    "被字句": re.compile(r"被[一-鿿]{1,6}(?:掉|出来|完成|计算|设置|处理)?"),
    "进行": re.compile(r"进行"),
    "让我们": re.compile(r"让我们"),
    "通过…来": re.compile(r"通过.{2,20}来"),
    "被动态-得": re.compile(r"得到(?:了)?(?:计算|应用|设置|使用)"),
}


def cells(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    out: list[tuple[int, str]] = []
    current: int | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = re.fullmatch(r"###CELL (\d+)", line.strip())
        if m:
            if current is not None:
                out.append((current, "\n".join(buf).strip("\n")))
            current, buf = int(m.group(1)), []
        elif current is not None:
            buf.append(line)
    if current is not None:
        out.append((current, "\n".join(buf).strip("\n")))
    return out


def strip_code(md: str) -> str:
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    md = re.sub(r"`[^`\n]*`", " ", md)
    md = re.sub(r"\$\$.*?\$\$", " ", md, flags=re.S)
    md = re.sub(r"\]\([^)]*\)", " ", md)
    return md


def main() -> int:
    total = 0
    for path in sorted(ZH_DIR.glob("*.txt")):
        found: list[str] = []
        annotations: dict[str, int] = {}
        for idx, src in cells(path):
            prose = strip_code(src)
            for name, rx in SMELLS.items():
                for m in rx.finditer(prose):
                    line = prose[max(0, m.start() - 25): m.end() + 20].replace("\n", " ")
                    found.append(f"  cell {idx:>2}  [{name}] …{line}…")
            for m in GAP.finditer(prose):
                line = prose[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")
                found.append(f"  cell {idx:>2}  [中英文粘连] …{line}…")
            for m in HAWIDTH.finditer(prose):
                line = prose[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")
                found.append(f"  cell {idx:>2}  [半角标点] …{line}…")
            for m in ANNOT.finditer(prose):
                annotations[m.group(1).strip()] = annotations.get(m.group(1).strip(), 0) + 1
        dup = [f"  重复注释：{term} ×{n}" for term, n in annotations.items() if n > 1]
        if found or dup:
            print(f"{path.name}: {len(found) + len(dup)} 处")
            for line in found + dup:
                print(line)
            total += len(found) + len(dup)
    print(f"--- 共 {total} 处待人工确认")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
