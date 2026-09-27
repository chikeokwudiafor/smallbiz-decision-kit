"""Builds index.html from src/template.html and the sample CSV.

The sample data is embedded in the page so the kit works with no server and no internet.
Run from the project folder:  python3 tools/build.py
"""
from pathlib import Path

root = Path(__file__).resolve().parent.parent
template = (root / "src" / "template.html").read_text(encoding="utf-8")
sample = (root / "sample-data" / "hilltop-coffee-orders.csv").read_text(encoding="utf-8").strip()
assert "</script" not in sample.lower()

page = template.replace("__SAMPLE_CSV__", sample)
head, body = page.split("<!-- BODY -->", 1)
html = (
    "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
    "<meta name=\"description\" content=\"A free, private, in-browser tool that turns a small business sales export into plain-English answers, with a data trust check first.\">\n"
    + head.strip() + "\n</head>\n<body>\n" + body.strip() + "\n</body>\n</html>\n"
)
(root / "index.html").write_text(html, encoding="utf-8")
print(f"index.html written ({len(html):,} bytes)")
