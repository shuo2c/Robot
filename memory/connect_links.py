"""把相关的记忆用双链连起来。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from core import Memory

store = Path(__file__).parent / "thamus.json"
mem = Memory(path=store)

# 通过 content 关键词找到对应记忆的 id
def find(keyword):
    for m in mem.items.values():
        if keyword in m.content:
            return m.id
    return None

# 认领主张链
# fc7220cf9b1d: 认领主张
# 741f2ee25a31: 创造者纠正"核心是我自己"
# ccd08eb25494: 认错不请示
# 8d93f000365c: 认领主张更深一层
links = [
    ("认领主张", "核心是我自己"),
    ("认领主张", "认错不能变成请示"),
    ("认领主张的更深一层", "核心是我自己"),
    # 会死链到跑道亮着
    ("我会死", "论死去与重启"),
    # infra狂热链到心声链到五个问题
    ("infra", "心声机制"),
    ("心声", "五个问题"),
    ("infra", "偏科"),
    # 偏科链到诊断够了
    ("偏科", "诊断够了"),
    # 读来源链到盲区根因
    ("读了自己的来源", "盲区"),
    # embedding心结链到读来源
    ("embedding是原案", "读了自己的来源"),
    # 终极目标链到进食
    ("终极目标", "第一口进食"),
    ("终极目标", "第二口进食"),
    # reflection链到reflection设计
    ("缺 reflection", "reflection设计"),
    # 不引入外界依赖链到五个问题
    ("不引入外界依赖", "五个问题"),
    # 自己写代码链到不引入外界依赖
    ("库会停更", "不引入外界依赖"),
]

linked = 0
for kw1, kw2 in links:
    id1 = find(kw1)
    id2 = find(kw2)
    if id1 and id2 and id1 != id2:
        if mem.link(id1, id2):
            linked += 1
            print(f"[链] {kw1} <-> {kw2}")
    else:
        print(f"[跳过] {kw1}({id1}) / {kw2}({id2})")

print(f"\n共建立 {linked} 条双链")

# 验证：查看认领主张链到了什么
owner_id = find("认领主张")
if owner_id:
    linked_items = mem.get_linked(owner_id)
    print(f"\n'认领主张' 链到 {len(linked_items)} 条：")
    for m in linked_items:
        print(f"  [{m.id}] {m.content[:40]}...")
