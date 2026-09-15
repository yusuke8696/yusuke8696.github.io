"""Run after committing HTML edits; dates describe the last commit touching each page."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
pages = [Path('index.html'), *sorted(Path(root / 'articles').rglob('*.html'))]
dates = {}
for page in pages:
    relative = page.relative_to(root).as_posix() if page.is_absolute() else page.as_posix()
    date = subprocess.check_output(
        ['git', 'log', '-1', '--format=%cs', '--', relative], cwd=root, text=True
    ).strip()
    if not date:
        raise SystemExit(f'Commit the HTML first: {relative}')
    dates[relative] = date
(root / '_data').mkdir(exist_ok=True)
(root / '_data/sitemap_dates.json').write_text(
    json.dumps(dates, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
)
