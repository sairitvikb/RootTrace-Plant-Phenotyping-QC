import argparse
import json
from pathlib import Path
from .core import evaluate, read_traits, report, write_html


def main():
    parser = argparse.ArgumentParser(description='Flag unusual sleap-roots CSV traits for human review.')
    parser.add_argument('csv', type=Path, help='Input CSV with plant_name, frame_idx, primary_length, lateral_count')
    parser.add_argument('--output', type=Path, default=Path('outputs'))
    parser.add_argument('--jump-pct', type=float, default=35.0)
    args = parser.parse_args()
    rows = read_traits(args.csv)
    flags = evaluate(rows, jump_pct=args.jump_pct)
    result = report(rows, flags, args.csv, args.jump_pct)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    write_html(result, args.output / 'report.html')
    print(f"Analyzed {len(rows)} observations. Flagged {result['summary']['flagged_frames']} frames.")
    print(f'Reports: {args.output / "report.html"} | {args.output / "report.json"}')


if __name__ == '__main__':
    main()
