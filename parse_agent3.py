import re, html
from pathlib import Path

html_text = Path('agent3.html').read_text(encoding='utf-8', errors='ignore')

html_text = re.sub(r'<script.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
html_text = re.sub(r'<style.*?</style>', '', html_text, flags=re.DOTALL | re.IGNORECASE)


def extract(tag, limit=None):
    pattern = re.compile(rf'<{tag}[^>]*>(.*?)</{tag}>', re.IGNORECASE | re.DOTALL)
    items = []
    for raw in pattern.findall(html_text):
        text = re.sub(r'<[^>]+>', ' ', raw)
        text = html.unescape(text)
        cleaned = ' '.join(text.split())
        if cleaned:
            items.append(cleaned)
    if limit is not None:
        items = items[:limit]
    return items

sections = {
    'h1': extract('h1'),
    'h2': extract('h2'),
    'h3': extract('h3'),
    'p': extract('p', 80),
    'li': extract('li', 80),
    'strong': extract('strong', 80),
}

for tag, values in sections.items():
    print(f'== {tag.upper()} ==')
    for v in values:
        print(v)
    print()
