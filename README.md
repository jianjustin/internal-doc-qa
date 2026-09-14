内部文档问答 Agent。只根据 docs/ 里的原文回答；找不到可引用片段就拒绝。

当前范围
- 谁用：本机打开网页即可问，面试时可当场演示
- 成功一笔：有本地网页；问句走同一套引擎，有出处才答，没有的拒绝
- 这次不做：登录、向量库（持久化索引）、Agent 框架、多用户、接真实网盘

怎么跑（需要 .venv，第一次会下载中文向量模型）

uv venv --python 3.12 .venv
uv pip install -r requirements.txt
.venv/bin/python serve.py
然后打开 http://127.0.0.1:8000

命令行仍可用：

.venv/bin/python ask.py "一线城市住宿上限是多少"
.venv/bin/python -m unittest -v test_ask.py

用 Pi 接着改这一份仓库，不要另起一个玩具。
