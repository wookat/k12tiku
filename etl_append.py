"""Append newer sources (GAOKAO-Bench-Updates 2023-2024, LiveK12Bench 2026 mock exams)
into questions_append.jsonl with ids continuing after the existing max."""
import json, os, glob

START_ID = int(os.environ.get("START_ID", "29546"))
BASE = os.path.dirname(os.path.abspath(__file__))
rows = []

def _s(v):
    if v is None:
        return ""
    if isinstance(v, dict):
        return "\n".join(f"{k}: {_s(x)}" for k, x in v.items()).strip()
    if isinstance(v, (list, tuple)):
        return "\n".join(_s(x) for x in v).strip()
    return str(v).strip()

def add(stage, subject, qtype, difficulty, question, answer, explanation, source, grade=""):
    q = _s(question)
    if len(q) < 5:
        return
    rows.append({
        "stage": stage, "grade": grade, "subject": subject,
        "qtype": qtype or "", "difficulty": difficulty or "",
        "question": q[:6000], "answer": _s(answer)[:3000],
        "explanation": _s(explanation)[:8000], "source": source,
    })

# ---- GAOKAO-Bench-Updates: 2023/2024 gaokao MCQs ----
SUBJ = {"English": "英语", "Biology": "生物", "Chemistry": "化学", "Chinese": "语文",
        "Geography": "地理", "History": "历史", "Math": "数学", "Physics": "物理",
        "Political": "政治"}
for path in sorted(glob.glob("/tmp/gbu/Data/*/*.json")):
    name = os.path.basename(path)
    subject = next((v for k, v in SUBJ.items() if k in name), None)
    if not subject:
        continue
    qtype = "选择题" if "MCQ" in name else ("填空题" if "Fill" in name else "解答题")
    data = json.load(open(path, encoding="utf-8"))
    for e in data.get("example", []):
        year = e.get("year", "")
        cat = _s(e.get("category", "")).split("\n")[0][:20]
        add("高中", subject, qtype, "", e.get("question", ""), e.get("answer", ""),
            e.get("analysis", ""), f"高考真题 {year} {cat}".strip())

# ---- LiveK12Bench: 2026 fresh high-school mock/exam papers (STEM) ----
LSUBJ = {"math": "数学", "physics": "物理", "chemistry": "化学", "biology": "生物"}
LSET = {"2603": "2026年3月模拟/联考", "2605": "2026年5月模拟/联考"}
for split in ["zh_2603", "zh_2605"]:
    for r in json.load(open(f"/tmp/lk12_{split}.json", encoding="utf-8")):
        subj = LSUBJ.get(r["subject"], r["subject"])
        setno = r["id"].split("_")[1]
        add("高中", subj, r.get("question_type", ""), "",
            r["question"], r["answer"], r.get("solution", ""),
            LSET.get(setno, "模拟题"))

out = os.path.join(BASE, "questions_append.jsonl")
with open(out, "w", encoding="utf-8") as f:
    for i, r in enumerate(rows):
        r["id"] = START_ID + i + 1
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

from collections import Counter
c = Counter((r["stage"], r["subject"], r["source"].split()[0]) for r in rows)
print(len(rows))
for k, v in sorted(c.items()):
    print(k, v)
