#!/usr/bin/env python3
"""本地网页：别人打开就能问，仍走同一套有出处才回答。"""

from __future__ import annotations

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from ask import answer

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>内部文档问答</title>
<style>
body { font-family: sans-serif; max-width: 42rem; margin: 2rem auto; padding: 0 1rem; }
textarea { width: 100%; min-height: 4rem; }
pre { white-space: pre-wrap; background: #f4f4f4; padding: 1rem; }
</style>
</head>
<body>
<h1>内部文档问答</h1>
<p>只根据内部制度原文回答；找不到就拒绝。不用登录。</p>
<form method="post" action="/">
<textarea name="question" placeholder="例如：一线城市住宿上限是多少">{question}</textarea>
<p><button type="submit">提问</button></p>
</form>
<pre>{result}</pre>
</body>
</html>
"""


def handle_ask(question: str) -> str:
    q = question.strip()
    if not q:
        return "请输入问题。"
    return answer(q)


def render(question: str = "", result: str = "") -> bytes:
    html = PAGE.replace("{question}", escape(question)).replace("{result}", escape(result))
    return html.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._send(render())

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        question = parse_qs(raw).get("question", [""])[0]
        self._send(render(question, handle_ask(question)))

    def _send(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="内部文档问答（本地网页）")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"打开 http://127.0.0.1:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
