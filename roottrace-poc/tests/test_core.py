import csv
from pathlib import Path
import pytest
from roottrace.core import read_traits, evaluate, report


def test_flags_sudden_spike():
    rows = [dict(plant_name='A', frame_idx=i, primary_length=x, lateral_count=2)
            for i, x in enumerate([100, 103, 105, 108, 190])]
    flags = evaluate(rows)
    assert any(f['frame_idx'] == 4 and f['rule'] == 'abrupt_primary_length_change' for f in flags)


def test_smooth_growth_not_flagged():
    rows = [dict(plant_name='B', frame_idx=i, primary_length=100+i*3, lateral_count=2)
            for i in range(8)]
    assert evaluate(rows) == []


def test_lateral_count_jump():
    rows = [dict(plant_name='C', frame_idx=i, primary_length=100+i, lateral_count=x)
            for i, x in enumerate([1, 2, 7])]
    assert any(f['rule'] == 'lateral_count_change' for f in evaluate(rows))


def test_duplicate_rejected(tmp_path):
    csvfile = tmp_path / 'duplicate.csv'
    csvfile.write_text('plant_name,frame_idx,primary_length,lateral_count\nA,0,10,1\nA,0,11,2\n')
    with pytest.raises(ValueError, match='duplicate'):
        read_traits(csvfile)


def test_invalid_values_rejected(tmp_path):
    csvfile = tmp_path / 'invalid.csv'
    csvfile.write_text('plant_name,frame_idx,primary_length,lateral_count\nA,0,nan,1\n')
    with pytest.raises(ValueError, match='Invalid'):
        read_traits(csvfile)


def test_hash_provenance(tmp_path):
    csvfile = tmp_path / 'input.csv'
    csvfile.write_text('header\n')
    result = report([], [], csvfile, 35.0)
    assert len(result['source']['sha256']) == 64
    assert result['analysis']['jump_pct'] == 35.0
