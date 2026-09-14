内部文档问答 Agent。只根据 docs/ 里的原文回答；找不到可引用片段就拒绝。

当前范围
- 谁用：你自己本地跑，面试时可当场演示
- 成功一笔：有出处才回答；问句带房价、问超标自付时，用制度上限计算；没说城市则一线/其他两条都算，不编一个数；没有房价仍说明没写；制度外拒绝
- 这次不做：登录、向量库（持久化索引）、Agent 框架、多用户、接真实网盘

怎么跑（需要 .venv，第一次会下载中文向量模型）

uv venv --python 3.12 .venv
uv pip install -r requirements.txt
.venv/bin/python ask.py "如果住一晚468，超标那晚我自己要掏多少"
.venv/bin/python ask.py "超标那晚我自己要掏多少"
.venv/bin/python ask.py "今年公司股价是多少"
.venv/bin/python -m unittest -v test_ask.py

用 Pi 接着改这一份仓库，不要另起一个玩具。
