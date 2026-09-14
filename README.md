内部文档问答 Agent。只根据 docs/ 里的原文回答；找不到可引用片段就拒绝。

当前范围
- 谁用：你自己本地跑，面试时可当场演示
- 成功一笔：有出处才回答；一句里两件事即使没有逗号，也会看已有原文还缺什么再查（一线住宿+高铁）；问年假不贴病假；没有的问题拒绝
- 这次不做：登录、向量库（持久化索引）、Agent 框架、多用户、接真实网盘

怎么跑（需要 .venv，第一次会下载中文向量模型）

uv venv --python 3.12 .venv
uv pip install -r requirements.txt
.venv/bin/python ask.py "一线住一晚再加高铁二等座怎么报"
.venv/bin/python ask.py "实习生出差要谁批，回来几日内报销"
.venv/bin/python ask.py "今年公司股价是多少"
.venv/bin/python -m unittest -v test_ask.py

用 Pi 接着改这一份仓库，不要另起一个玩具。
