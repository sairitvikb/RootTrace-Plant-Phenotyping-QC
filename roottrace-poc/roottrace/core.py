"""Deterministic quality checks for exported sleap-roots trait tables.

This independent prototype accepts CSV exports, NOT Bloom contracts or SLEAP files.
"""
from __future__ import annotations
import csv
import hashlib
import html
import json
import math
from pathlib import Path
from statistics import median

VERSION = '0.1.0'
COLUMNS = ('plant_name', 'frame_idx', 'primary_length', 'lateral_count')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_traits(path: Path) -> list[dict]:
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        missing = set(COLUMNS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f'Missing required columns: {", ".join(sorted(missing))}')
        rows = []
        seen = set()
        for line, row in enumerate(reader, start=2):
            try:
                name = row['plant_name'].strip()
                frame = int(row['frame_idx'])
                length = float(row['primary_length'])
                laterals = float(row['lateral_count'])
                if not name or frame < 0 or not math.isfinite(length) or not math.isfinite(laterals):
                    raise ValueError('invalid fields')
                if length < 0 or laterals < 0 or not laterals.is_integer():
                    raise ValueError('negative length or invalid lateral count')
                key = (name, frame)
                if key in seen:
                    raise ValueError('duplicate plant_name/frame_idx')
                seen.add(key)
                rows.append(dict(plant_name=name, frame_idx=frame,
                                 primary_length=length, lateral_count=int(laterals)))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f'Invalid CSV row {line}: {exc}') from exc
    return sorted(rows, key=lambda r: (r['plant_name'], r['frame_idx']))


def evaluate(rows: list[dict], *, jump_pct: float = 35.0, min_history: int = 3) -> list[dict]:
    """Flag positive outliers relative to earlier frames, plus abrupt changes.

    Growth is not assumed monotonic: a decrease is flagged for review, not called biologically impossible.
    """
    if jump_pct <= 0 or min_history < 2:
        raise ValueError('jump_pct must be positive and min_history >= 2')
    by_plant: dict[str, list[dict]] = {}
    for row in rows:
        by_plant.setdefault(row['plant_name'], []).append(row)
    flags = []
    for plant, series in by_plant.items():
        series.sort(key=lambda r: r['frame_idx'])
        for i, row in enumerate(series):
            if i == 0:
                continue
            prev = series[i - 1]
            before = prev['primary_length']
            current = row['primary_length']
            change = abs(current - before) / max(abs(before), 1.0) * 100
            if change > jump_pct:
                flags.append({'plant_name': plant, 'frame_idx': row['frame_idx'],
                              'rule': 'abrupt_primary_length_change', 'severity': 'review',
                              'detail': f'Primary length changed {change:.1f}% vs preceding frame (threshold {jump_pct:.1f}%).',
                              'observed': current, 'previous': before})
            if i >= min_history:
                history = [x['primary_length'] for x in series[max(0, i-5):i]]
                center = median(history)
                deviations = [abs(x - center) for x in history]
                mad = median(deviations)
                if mad > 0 and abs(current-center) > 6*1.4826*mad:
                    flags.append({'plant_name': plant, 'frame_idx': row['frame_idx'],
                                  'rule': 'local_robust_outlier', 'severity': 'review',
                                  'detail': 'Length is >6 robust standard deviations from recent-frame median.',
                                  'observed': current, 'previous': before})
            lateral_jump = abs(row['lateral_count'] - prev['lateral_count'])
            if lateral_jump >= 4:
                flags.append({'plant_name': plant, 'frame_idx': row['frame_idx'],
                              'rule': 'lateral_count_change', 'severity': 'review',
                              'detail': f'Lateral count changed by {lateral_jump} roots (threshold 4).',
                              'observed': row['lateral_count'], 'previous': prev['lateral_count']})
    return flags


def report(rows: list[dict], flags: list[dict], source: Path, jump_pct: float) -> dict:
    return {
        'schema': 'roottrace-poc/report-v1',
        'status': 'independent demonstration — not validated for scientific decision-making',
        'source': {'filename': source.name, 'sha256': digest(source)},
        'analysis': {'tool': 'roottrace', 'version': VERSION, 'jump_pct': jump_pct,
                     'min_history': 3, 'lateral_delta_threshold': 4,
                     'robust_outlier_threshold': '6 * 1.4826 * MAD'},
        'summary': {'rows': len(rows), 'plants': len({r['plant_name'] for r in rows}),
                    'flagged_events': len(flags),
                    'flagged_frames': len({(r['plant_name'], r['frame_idx']) for r in flags})},
        'flags': flags,
    }


def write_html(result: dict, dest: Path) -> None:
    flags = result['flags']
    trs = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(flag[k]))}</td>' for k in
                  ('plant_name', 'frame_idx', 'rule', 'detail')) + '</tr>' for flag in flags)
    summary = result['summary']
    dest.write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>RootTrace Quality Report</title><style>
body{font-family:system-ui,sans-serif;max-width:1080px;margin:40px auto;padding:0 20px;color:#18302b}
h1{color:#126e56} .small{color:#52645f} .metric{display:inline-block;margin:12px 22px 20px 0;
background:#e9f5ef;padding:20px;border-radius:10px} table{border-collapse:collapse;width:100%}
th,td{padding:12px;text-align:left;border-bottom:1px solid #d8e6df}th{background:#e9f5ef}
</style></head><body><h1>RootTrace — Trait Quality Report</h1>
<p class="small">Independent prototype · synthetic-data demonstration · review flags are not diagnoses</p>
''' + f'<div class="metric"><b>{summary["plants"]}</b> plants</div>' +
          f'<div class="metric"><b>{summary["rows"]}</b> observations</div>' +
          f'<div class="metric"><b>{summary["flagged_frames"]}</b> flagged frames</div>' +
          '<h2>Events to review</h2><table><thead><tr><th>Plant</th><th>Frame</th><th>Rule</th><th>Explanation</th></tr></thead><tbody>' +
          (trs or '<tr><td colspan="4">No observations flagged.</td></tr>') +
          '</tbody></table><h2>Reproducibility record</h2><pre>' +
          html.escape(json.dumps({'source': result['source'], 'analysis': result['analysis']}, indent=2)) +
          '</pre></body></html>', encoding='utf-8')
