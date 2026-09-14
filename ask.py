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


def retrieve(query: str, chunks: list[Chunk], k: int = 1, sem_min: float | None = None) -> list[tuple[float, Chunk]]:
    ranked = sorted(((score(query, c), c) for c in chunks), key=lambda x: x[0], reverse=True)
    hits = [(s, c) for s, c in ranked[:k] if s >= 0.3]
    if hits:
        return hits
    # 词对不上时比意思近不近。向量当场算，不是向量库。
    model = _embedding_model()
    qv = next(model.embed([query]))
    cvs = list(model.embed([f"{c.heading}\n{c.text}" for c in chunks]))
    sem = sorted(((_cosine(qv, cv), c) for cv, c in zip(cvs, chunks)), key=lambda x: x[0], reverse=True)
    floor = SEM_THRESHOLD if sem_min is None else sem_min
    return [(s, c) for s, c in sem[:k] if s >= floor]


def question_parts(query: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"[，,；;]", query) if p.strip()]
    return parts or [query]


def _chunk_tokens(chunk: Chunk) -> set[str]:
    return set(tokens(chunk.heading + " " + chunk.text))


def leftover_tokens(query: str, hits: list[Chunk]) -> set[str]:
    left = set(tokens(query))
    for chunk in hits:
        left -= _chunk_tokens(chunk)
    return left


def follow_up(query: str, chunks: list[Chunk], already: list[Chunk]) -> list[tuple[float, Chunk]]:
    """已有原文没盖住的词，再查一次；盖不住的近邻段落丢掉。"""
    leftover = leftover_tokens(query, already)
    if not leftover:
        return []
    used = {(c.path, c.heading) for c in already}
    rest = [c for c in chunks if (c.path, c.heading) not in used]
    extra: list[tuple[float, Chunk]] = []
    for s, c in retrieve(query, rest, sem_min=0.52):
        if leftover & _chunk_tokens(c):
            extra.append((s, c))
    return extra


def collect_hits(query: str, chunks: list[Chunk]) -> list[tuple[float, Chunk]]:
    """问了几件事就查几次；同一段不重复贴。一段不够则按缺的词再查。"""
    seen: set[tuple[str, str]] = set()
    out: list[tuple[float, Chunk]] = []

    def add(hits: list[tuple[float, Chunk]]) -> None:
        for s, c in hits:
            key = (c.path, c.heading)
            if key in seen:
                continue
            seen.add(key)
            out.append((s, c))

    for part in question_parts(query):
        first = retrieve(part, chunks)
        add(first)
        add(follow_up(part, chunks, [c for _, c in first]))
    return out


def _best_units(query: str, chunk: Chunk, units: list[str]) -> list[str]:
    if len(units) <= 1:
        return units
    scored = [(score(query, Chunk(chunk.path, chunk.heading, unit)), unit) for unit in units]
    best = max(item[0] for item in scored)
    if best <= 0:
        return units
    kept = [unit for s, unit in scored if s >= best - 1e-12]
    order = {unit: i for i, unit in enumerate(units)}
    kept.sort(key=lambda unit: order[unit])
    return kept


def _sentences(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"(?<=[。；;])", text) if part.strip()]
    return parts or [text]


def excerpt(query: str, chunk: Chunk) -> str:
    """一张卡里只留最像问句的那一行、那一句，邻居条款丢掉。"""
    rows = [ln.strip() for ln in chunk.text.splitlines() if ln.strip()]
    kept_lines = _best_units(query, chunk, rows)
    trimmed: list[str] = []
    for line in kept_lines:
        sents = _best_units(query, chunk, _sentences(line))
        trimmed.append("".join(sents))
    return "\n".join(trimmed) if trimmed else chunk.text


def asks_for_number(query: str) -> bool:
    return any(word in query for word in ("多少", "几天", "几日", "几晚"))


def query_price(query: str) -> int | None:
    nums = re.findall(r"\d+", query)
    if len(nums) != 1:
        return None
    return int(nums[0])


def policy_caps(chunks: list[Chunk]) -> list[tuple[str, int]]:
    caps: list[tuple[str, int]] = []
    for chunk in chunks:
        for ln in chunk.text.splitlines():
            found = re.search(r"上限\s*(\d+)", ln)
            if not found:
                continue
            if "一线" in ln or "北上广深" in ln:
                caps.append(("一线", int(found.group(1))))
            elif "其他" in ln:
                caps.append(("其他", int(found.group(1))))
    return caps


def overage_line(query: str, hit_chunks: list[Chunk]) -> str | None:
    """问句里有房价、制度里有上限时，按超标自付来算；没说城市就两条都算。"""
    if "超标" not in query and "掏" not in query:
        return None
    price = query_price(query)
    if price is None:
        return None
    caps = policy_caps(hit_chunks)
    if not caps:
        return None
    if any(word in query for word in ("一线", "北上广深", "上海", "北京", "广州", "深圳", "魔都")):
        caps = [item for item in caps if item[0] == "一线"] or caps
    elif "其他" in query:
        caps = [item for item in caps if item[0] == "其他"] or caps
    parts: list[str] = []
    for label, cap in caps:
        pay = price - cap
        if pay <= 0:
            parts.append(f"{label}城市上限 {cap} 元，{price} 未超标，自己掏 0 元。")
        else:
            parts.append(f"{label}城市上限 {cap} 元，超标 {pay} 元，自己掏 {pay} 元。")
    if len(caps) > 1:
        parts.append("请说明城市后可以只留一条。")
    return "".join(parts) if len(parts) == 1 else " ".join(parts)


def spoken_line(query: str, excerpts: list[str]) -> str | None:
    """问数字而原文没有数字时，明说没写，不编造。"""
    blob = "\n".join(excerpts)
    if asks_for_number(query) and not re.search(r"\d", blob):
        return "制度没写具体金额或天数。"
    return None


def asks_permission(query: str) -> bool:
    return any(word in query for word in ("能不能", "能否", "可以吗", "能下", "能开", "能直接"))


def permission_verdict(query: str, excerpts: list[str]) -> str | None:
    """问能不能时，原文有禁止或须，就判断不能直接做，并把条件说出来。"""
    if not asks_permission(query):
        return None
    blob = "\n".join(excerpts)
    detail = spoken_from_excerpts(excerpts)
    if "禁止" in blob:
        return f"不能直接做。{detail}" if detail else "不能直接做。原文如下。"
    if "须" in blob or "必须" in blob:
        return f"不能直接做，须满足：{detail}" if detail else "不能直接做，须满足原文条件。"
    return None


def spoken_from_excerpts(excerpts: list[str]) -> str:
    """原文已有答案时，先说一句去掉条目符号的人话，再挂出处。"""
    bits: list[str] = []
    for piece in excerpts:
        text = piece.lstrip("- ").strip()
        text = re.sub(r"（[^）]*）", "", text)
        text = text.replace("：", "")
        text = re.sub(r"\s+", "", text)
        if text:
            bits.append(text)
    return " ".join(bits)


def answer(query: str, docs_dir: Path = DOCS_DIR) -> str:
    if not docs_dir.is_dir():
        return "拒绝：找不到文档目录。"
    chunks = load_chunks(docs_dir)
    hits = collect_hits(query, chunks)
    if not hits:
        return "拒绝：现有制度里没有找到可引用的原文，不能回答。"
    hit_chunks = [chunk for _, chunk in hits]
    excerpts = [excerpt(query, chunk) for chunk in hit_chunks]
    lines = ["根据内部制度："]
    overage = overage_line(query, hit_chunks)
    missing_number = None if overage else spoken_line(query, excerpts)
    verdict = None if (overage or missing_number) else permission_verdict(query, excerpts)
    spoken = overage or missing_number or verdict or spoken_from_excerpts(excerpts)
    if spoken:
        lines.append(spoken)
    for chunk, piece in zip(hit_chunks, excerpts):
        lines.append(f"- 出处：{chunk.path} / {chunk.heading}")
        lines.append(f"  原文：{piece}")
    if overage:
        lines.append("数字由问句中的房价与制度上限计算；未说明城市时两条都列出。")
    elif verdict:
        lines.append("判断来自原文中的禁止或须，不是另行规定。")
    else:
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
