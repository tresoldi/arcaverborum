"""Concept transports preserve rows, bound chunks and fail closed on drift."""
import gzip
import io
import json

import pytest

from arcaverborum import concept_rows


def fixture(root):
    data = root / 'web/data'
    data.mkdir(parents=True)
    rows = [['id1', 'a', 'ɣ', 'source'], ['id2', 'b', 'm', 'profile'],
            ['id3', 'a', 'n', 'source'], ['id4', '', 'p', 'unclean']]
    source = data / 'family.json.gz'
    source.write_bytes(gzip.compress(json.dumps(rows, ensure_ascii=False).encode(), mtime=0))
    manifest = dict(fields=['ID', 'concept_id', 'Segments', 'Segments_Source'],
                    source_files={'forms.csv': 'fixed'}, shards={'Family': dict(
                        url='data/family.json.gz', forms=4, bytes=source.stat().st_size,
                        sha256=concept_rows.sha(source))})
    (data / 'manifest.json').write_text(json.dumps(manifest))
    return rows, source


def test_streams_json_across_chunks_and_rejects_bad_arrays():
    class Tiny(io.StringIO):
        def read(self, size=-1):
            return super().read(min(size, 3))
    assert list(concept_rows.array_rows(Tiny(' [["ɣ",1], ["a",2]] \n'))) == [['ɣ', 1], ['a', 2]]
    for bad in ['[[1],]', '[[1]', '[[1]] trailing', '[{}]', '[[1] [2]]']:
        with pytest.raises(ValueError):
            list(concept_rows.array_rows(Tiny(bad)))
    with pytest.raises(ValueError, match='exceeds limit'):
        list(concept_rows.array_rows(io.StringIO('[["' + 'x' * 100 + '"]]'), limit=32))


def test_transport_preserves_all_mapped_rows_and_chunks_deterministically(tmp_path, monkeypatch):
    rows, _ = fixture(tmp_path)
    monkeypatch.setattr(concept_rows, 'ROWS_PER_PAGE', 1)
    result = concept_rows.build(tmp_path)
    index = json.loads((result / 'manifest.json').read_text())
    restored = []
    for info in index['concepts'].values():
        for page in info['pages']:
            raw = gzip.decompress((result / page['url']).read_bytes())
            assert len(raw) == page['raw_bytes']
            assert concept_rows.sha(result / page['url']) == page['sha256']
            restored.extend(json.loads(raw))
    assert sorted(restored) == sorted(row for row in rows if row[1])
    assert sum(len(c['pages']) for c in index['concepts'].values()) == 3
    assert concept_rows.build(tmp_path) == result
    assert json.loads((tmp_path / 'web/data/manifest.json').read_text())['concept_rows']['build_id'] == result.name


def test_changed_input_and_corrupt_cache_do_not_republish(tmp_path):
    _, source = fixture(tmp_path)
    result = concept_rows.build(tmp_path)
    manifest = tmp_path / 'web/data/manifest.json'
    before = manifest.read_bytes()
    (result / 'a-000.json.gz').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='Corrupt'):
        concept_rows.build(tmp_path)
    assert manifest.read_bytes() == before
    # Different bytes at a pinned family path are rejected on a fresh build too.
    source.write_bytes(b'changed')
    import shutil
    shutil.rmtree(result)
    with pytest.raises(ValueError, match='Changed family'):
        concept_rows.build(tmp_path)
    assert manifest.read_bytes() == before
