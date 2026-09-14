内部文档问答 Agent。只根据 docs/ 里的原文回答；找不到可引用片段就拒绝。

当前范围
- 谁用：你自己本地跑，面试时可当场演示
- 成功一笔：问「能不能」时先判断不能直接做，并把工单、报备等条件说出来，再挂出处；制度外拒绝
- 这次不做：登录、向量库（持久化索引）、Agent 框架、多用户、接真实网盘

怎么跑（需要 .venv，第一次会下载中文向量模型）

uv venv --python 3.12 .venv
uv pip install -r requirements.txt
.venv/bin/python ask.py "外包开 VPN 能下生产库吗"
.venv/bin/python ask.py "一线城市住宿上限是多少"
.venv/bin/python ask.py "今年公司股价是多少"
.venv/bin/python -m unittest -v test_ask.py

用 Pi 接着改这一份仓库，不要另起一个玩具。
