"""Normalize question/answer/explanation formatting across all questions*.jsonl
files into questions_clean.jsonl (ids preserved)."""
import glob, html, json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = ["questions.jsonl", "questions_append.jsonl", "questions_ms_english.jsonl"]

BLANK = re.compile(r"<blank[^>]*>_?")
TAG = re.compile(r"</?(?:table|tr|td|th|tbody|thead|p|div|br|span|b|i|u|em|strong)\b[^>]*>",
                 re.I)
IMG = re.compile(r"<img[^>]*>", re.I)
OPT = re.compile(r"(?<!^)(?<![\n(（\w])\s*([A-D])[.．、]\s*(?=\S)")
SPACES = re.compile(r"[ \t\u3000\xa0]+")
BLANKLINES = re.compile(r"\n{3,}")
STARTS_NEW = re.compile(r"^([A-D][.．、]|[(（]\d|\d+\s*[.．、]|[①-⑳]|【)")
ENDS_LINE = re.compile(r'[。．.!?！？;；:：…”"】）)]$')
CJK = re.compile(r"[\u3000-\u9fff\uff00-\uffef]")


def join_wrapped(s):
    """Merge hard line breaks that split a single sentence (PDF extraction)."""
    out = []
    for line in s.split("\n"):
        if (out and out[-1] and line and not STARTS_NEW.match(line)
                and not ENDS_LINE.search(out[-1])):
            sep = "" if CJK.search(out[-1][-1]) and CJK.search(line[0]) else " "
            out[-1] = out[-1] + sep + line
        else:
            out.append(line)
    return "\n".join(out)


def clean(text):
    if not text:
        return ""
    s = text.replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    s = IMG.sub("", s)
    s = BLANK.sub("____", s)
    s = TAG.sub(lambda m: "\n" if m.group(0).lower().startswith(("</tr", "<br", "</p", "</div")) else " ", s)
    s = html.unescape(s)
    s = "\n".join(SPACES.sub(" ", line).strip() for line in s.split("\n"))
    s = re.sub(r"[ \t]+([，。；：？！、）】》．])", r"\1", s)
    s = join_wrapped(s)
    s = re.sub(r"([（【《])\s+", r"\1", s)
    s = re.sub(r"选项\s*[:：]\s*", "\n", s)
    # put each multiple-choice option on its own line
    if re.search(r"\bA[.．、]", s) and re.search(r"\bC[.．、]", s):
        s = OPT.sub(lambda m: "\n" + m.group(1) + ". ", s)
    s = BLANKLINES.sub("\n\n", s)
    return s.strip()


def main():
    rows = []
    for name in SRC:
        path = os.path.join(BASE, name)
        if not os.path.exists(path):
            continue
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            if r["source"].startswith("初中英语题库"):
                r["source"] = "初中英语题库（7-9年级）"
            r["question"] = clean(r["question"])[:6000]
            r["answer"] = clean(r["answer"])[:3000]
            r["explanation"] = clean(r["explanation"])[:8000]
            if len(r["question"]) < 5:
                continue
            rows.append(r)

    out = os.path.join(BASE, "questions_clean.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(len(rows))


if __name__ == "__main__":
    main()
