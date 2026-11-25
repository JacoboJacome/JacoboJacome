"""Writes dev/preview-{dark,light}{,-phone}.html: the README as GitHub would show it, one variant per file."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
readme = (ROOT / "README.md").read_text(encoding="utf-8")
for theme, bg, fg in (("dark", "#0d1117", "#e6edf3"), ("light", "#ffffff", "#1f2328")):
    for phone in (False, True):
        body = re.sub(r"<source[^>]*>", "", readme)
        def pick(m):
            name = m.group(1)
            if phone and (ROOT / "assets" / f"{name}-phone-{theme}.svg").exists():
                return f'src="../assets/{name}-phone-{theme}.svg"'
            return f'src="../assets/{name}-{theme}.svg"'
        body = re.sub(r'src="assets/(.+?)-light\.svg"', pick, body)
        body = body.replace("<details>", "<details open>")
        width = 380 if phone else 830
        html = (f'<html><body style="margin:0;background:{bg};color:{fg};font-family:Segoe UI,sans-serif">'
                f'<div style="width:{width}px;padding:16px">{body}</div></body></html>')
        (ROOT / "dev" / f"preview-{theme}{'-phone' if phone else ''}.html").write_text(html, encoding="utf-8")
