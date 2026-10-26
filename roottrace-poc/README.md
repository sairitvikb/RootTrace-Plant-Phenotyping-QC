# RootTrace — Reproducible Plant Phenotyping Quality Monitor

**Independent research-software-engineering proof of concept**, inspired by the Pereira Lab's publicly described SLEAP → sleap-roots → Bloom workflow. **Not affiliated with or endorsed by the lab.**

## Research question

Can we automatically flag unusual *downstream root trait* measurements and give researchers a reproducible, explainable quality report before analysis or database write-back?

## What this demo actually does

- Reads a CSV export with `plant_name`, `frame_idx`, `primary_length`, `lateral_count`, compatible with a subset of documented sleap-roots trait CSV fields.
- Finds abrupt frame-to-frame primary-length changes, large lateral-count changes, and robust local length outliers.
- Produces an offline HTML report for review, with per-flag explanations.
- Produces a JSON audit report including the input SHA-256 hash, tool version and configurable thresholds.
- Includes six automated unit tests and deterministic synthetic example data.

**Non-goals:** Does not run SLEAP neural inference, consume `.slp` files, integrate with Bloom, write `ResultEnvelope`, implement the lab's `sleap-roots-contracts` schema, or validate the scientific efficacy of chosen thresholds. This is a standalone complementary demonstration, not a proposed replacement for existing SLEAP QC or prediction viewer.

## Run

From the repository root, using Python 3.10+:

```bash
python -m roottrace data/synthetic_traits.csv --output outputs
```

Open `outputs/report.html` in a browser. Read `outputs/report.json` for machine-readable results.

To customize the abrupt-change threshold:

```bash
python -m roottrace data/synthetic_traits.csv --jump-pct 25 --output outputs
```

To test:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

## Interpretation and limitations

All measurements and events in `data/synthetic_traits.csv` are **synthetic**, not Salk data. Numbers represent the native measurement units of the CSV (often pixels), **not mm** unless calibrated upstream. Every anomaly is a **human-review suggestion**, not proof of an error: biological growth is not guaranteed monotonic; missing timepoints, varying measurement intervals, occlusions, and experimental context matter. Hard-coded thresholds are demonstration defaults and require calibration to real labeled datasets. A SHA-256 hash proves file-byte identity, not that the source annotations or model are scientifically valid. For full experimental reproducibility, record upstream model weights hashes, dataset identifiers, processing parameters, and relevant software/environment versions.

## Where it could go next

1. Use genuine `sleap-roots` sample CSVs and ask scientists which cases constitute useful review flags.
2. Develop tests on annotated, representative datasets, measuring precision/recall and false-alert rates.
3. Align a read-only import/export adapter with the *current* `sleap-roots-contracts` schema and its provenance semantics; do not pretend this JSON is their `ResultEnvelope`.
4. Prototype an optional UI integration within a Bloom-compatible review process, subject to maintainer guidance.

## Related upstream projects

- https://github.com/talmolab/sleap
- https://github.com/talmolab/sleap-roots
- https://github.com/talmolab/sleap-roots-contracts
- https://roots.sleap.ai/latest/getting-started/quickstart/

The independent demo code is original. Consult and follow upstream contribution guidelines before proposing integration.
