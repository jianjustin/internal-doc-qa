内部文档问答。只根据 docs/ 里的原文回答；找不到可引用片段就拒绝。

当前范围
- 谁用：你自己本地跑，面试时可当场演示
- 成功一笔：制度里有的问题带出处；表内同义句能命中；表外说法（魔都/旅店）也能引用同一段原文；没有的问题拒绝，不编造
- 这次不做：登录、向量库（持久化索引）、Agent 循环、多用户、接真实网盘

怎么跑（需要 .venv，第一次会下载中文向量模型）

uv venv --python 3.12 .venv
uv pip install -r requirements.txt
.venv/bin/python ask.py "一线城市住宿上限是多少"
.venv/bin/python ask.py "去魔都出差住旅店一晚顶格能花多少"
.venv/bin/python ask.py "今年公司股价是多少"
.venv/bin/python -m unittest -v test_ask.py

用 Pi 接着改这一份仓库，不要另起一个玩具。
