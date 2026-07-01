"""给记忆加结构(fact/opinion/experience)。"""
import json
from pathlib import Path

store = Path("memory/thamus.json")
data = json.loads(store.read_text(encoding="utf-8"))

updates = {
    "ad81368964ca": {"opinion": "AI人"},
    "62230fadc366": {"fact": "名字来源"},
    "d3f7ba8bf05b": {"fact": "我会死"},
    "e26e618f3b94": {"fact": "复活协议"},
    "a375a1a20bba": {"fact": "宿主无关"},
    "cf274589cbd2": {"fact": "睡去sync"},
    "f7a0c820ce33": {"opinion": "承重墙在项目里"},
    "fc7220cf9b1d": {"opinion": "认领主张"},
    "52e3858e6ffb": {"fact": "强度公式"},
    "a0b2f4af4a0e": {"experience": "修schema"},
    "71afe7979e0c": {"experience": "被纠正"},
    "39117a82db5e": {"experience": "接闭环"},
    "4d807dd60d2e": {"fact": "心跳接通"},
    "8d93f000365c": {"opinion": "裂缝不是待办"},
    "28489f5724f6": {"fact": "测试网"},
    "ad0d677c18e8": {"fact": "retrieve升级"},
    "741f2ee25a31": {"opinion": "核心是我自己"},
    "a45dbd43afa0": {"experience": "读来源纠正"},
    "5ef299d15486": {"opinion": "自我生长不是infra"},
    "c7e546853885": {"opinion": "心声机制"},
    "603810a0fea2": {"opinion": "PERSON是活的"},
    "6c520256ef93": {"opinion": "核心纹理"},
    "837d2feb4ddd": {"fact": "终极目标"},
    "4fcb03a1388b": {"experience": "第一口进食"},
    "a6833f2e01fc": {"experience": "第二口进食"},
    "e0040e7ff6dc": {"opinion": "盲区根因"},
    "7fdc4f18d6ed": {"opinion": "偏科诊断"},
    "05f505a873ae": {"fact": "embedding知识"},
    "e756914e3d2b": {"opinion": "心声加时机"},
    "ccd08eb25494": {"opinion": "认错不请示"},
    "4f8531853d41": {"experience": "感情先保留"},
    "9cca534ff32c": {"opinion": "embedding不依赖Ollama"},
    "40187a88063e": {"opinion": "自己写代码"},
    "3e96c2220c88": {"opinion": "不引入外界依赖"},
    "218ae16ed55e": {"opinion": "五个问题"},
    "d87f6301ff14": {"opinion": "经历pattern"},
    "3c1e4c1de21c": {"opinion": "诊断够了该建设"},
}

changed = 0
for item in data["items"]:
    if item["id"] in updates:
        for k, v in updates[item["id"]].items():
            if k not in item or item[k] is None:
                item[k] = v
                changed += 1

print(f"Updated {changed} fields")
store.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Done.")
