#!/usr/bin/env python3
"""内部文档问答：只根据 docs/ 原文回答，找不到就拒绝。"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent / "docs"
STOPWORDS = {
    "的",
    "了",
    "是",
    "在",
    "和",
    "与",
    "或",
    "及",
    "等",
    "吗",
    "呢",
    "啊",
    "请",
    "问",
    "一下",
    "多少",
    "什么",
    "怎么",
    "如何",
    "能否",
    "可以",
    "需要",
}


@dataclass(frozen=True)
class Chunk:
    path: str
    heading: str
    text: str


def load_chunks(docs_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.glob("*.md")):
        heading = path.stem
        buf: list[str] = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("#"):
                if buf:
                    chunks.append(Chunk(path.name, heading, "\n".join(buf).strip()))
                    buf = []
                heading = line.lstrip("#").strip() or path.stem
                continue
            if not line:
                if buf:
                    chunks.append(Chunk(path.name, heading, "\n".join(buf).strip()))
                    buf = []
                continue
            buf.append(line)
        if buf:
            chunks.append(Chunk(path.name, heading, "\n".join(buf).strip()))
    return [c for c in chunks if c.text]


def tokens(text: str) -> list[str]:
    parts = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text.lower())
    out: list[str] = []
    for part in parts:
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) >= 2:
            out.extend(part[i : i + 2] for i in range(len(part) - 1))
        elif part not in STOPWORDS:
            out.append(part)
    return out


def score(query: str, chunk: Chunk) -> float:
    q = tokens(query)
    if not q:
        return 0.0
    blob = tokens(chunk.heading + " " + chunk.text)
    if not blob:
        return 0.0
    hits = sum(blob.count(t) for t in q)
    return hits / len(q)


def retrieve(query: str, chunks: list[Chunk], k: int = 3) -> list[tuple[float, Chunk]]:
    ranked = sorted(((score(query, c), c) for c in chunks), key=lambda x: x[0], reverse=True)
    return [(s, c) for s, c in ranked[:k] if s >= 0.6]


def answer(query: str, docs_dir: Path = DOCS_DIR) -> str:
    if not docs_dir.is_dir():
        return "拒绝：找不到文档目录。"
    chunks = load_chunks(docs_dir)
    hits = retrieve(query, chunks)
    if not hits:
        return "拒绝：现有制度里没有找到可引用的原文，不能回答。"
    lines = ["根据内部制度："]
    for s, chunk in hits:
        lines.append(f"- 出处：{chunk.path} / {chunk.heading}")
        lines.append(f"  原文：{chunk.text}")
    lines.append("以上内容均来自检索到的原文，没有额外推断。")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="内部文档问答（找不到原文就拒绝）")
    parser.add_argument("question", nargs="+", help="要问的问题")
    parser.add_argument("--docs", type=Path, default=DOCS_DIR)
    args = parser.parse_args(argv)
    print(answer(" ".join(args.question), args.docs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
