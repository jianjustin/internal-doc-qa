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

# 问法换成制度里的用词，才能撞上原文。只归一这一墙上会失败的说法。
CANON = {
    "酒店": "住宿",
    "宾馆": "住宿",
    "旅馆": "住宿",
    "上海": "一线城市",
    "北京": "一线城市",
    "广州": "一线城市",
    "深圳": "一线城市",
    "北上广深": "一线城市",
    "最多": "上限",
    "限额": "上限",
    "封顶": "上限",
    "一晚": "晚",
    "每晚": "晚",
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


def canonicalize(text: str) -> str:
    out = text
    for src in sorted(CANON, key=len, reverse=True):
        out = out.replace(src, CANON[src])
    return out


def tokens(text: str) -> list[str]:
    parts = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", canonicalize(text).lower())
    out: list[str] = []
    for part in parts:
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) >= 2:
            out.extend(part[i : i + 2] for i in range(len(part) - 1))
        elif part not in STOPWORDS:
            out.append(part)
    return out


def score(query: str, chunk: Chunk) -> float:
    q = set(tokens(query))
    if not q:
        return 0.0
    blob = set(tokens(chunk.heading + " " + chunk.text))
    if not blob:
        return 0.0
    return len(q & blob) / len(q)


_EMBED_MODEL = None
SEM_THRESHOLD = 0.55


def _embedding_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        from fastembed import TextEmbedding

        _EMBED_MODEL = TextEmbedding(model_name="BAAI/bge-small-zh-v1.5")
    return _EMBED_MODEL


def _cosine(a, b) -> float:
    dot = float(sum(x * y for x, y in zip(a, b)))
    na = float(sum(x * x for x in a) ** 0.5)
    nb = float(sum(y * y for y in b) ** 0.5)
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def retrieve(query: str, chunks: list[Chunk], k: int = 1) -> list[tuple[float, Chunk]]:
    ranked = sorted(((score(query, c), c) for c in chunks), key=lambda x: x[0], reverse=True)
    hits = [(s, c) for s, c in ranked[:k] if s >= 0.3]
    if hits:
        return hits
    # 词对不上时比意思近不近。向量当场算，不是向量库。
    model = _embedding_model()
    qv = next(model.embed([query]))
    cvs = list(model.embed([f"{c.heading}\n{c.text}" for c in chunks]))
    sem = sorted(((_cosine(qv, cv), c) for cv, c in zip(cvs, chunks)), key=lambda x: x[0], reverse=True)
    return [(s, c) for s, c in sem[:k] if s >= SEM_THRESHOLD]


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
