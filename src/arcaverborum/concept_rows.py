"""Bounded concept transports for querying lexical rows in the browser's SQLite DB."""
from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

ROWS_PER_PAGE = 1000
MAX_RAW_PAGE = 8 * 1024 * 1024
MAX_COMPRESSED_PAGE = 1024 * 1024


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def signature(manifest):
    return {key: manifest[key] for key in ['fields', 'source_files', 'shards']}


def array_rows(stream, limit=MAX_RAW_PAGE):
    """Stream a JSON array with bounded row buffers, rejecting malformed input."""
    decoder, buffer, eof = json.JSONDecoder(), '', False
    def fill():
        nonlocal buffer, eof
        text = stream.read(65536)
        eof = not text
        buffer += text
        if len(buffer.encode('utf-8')) > limit:
            raise ValueError('Concept transport input row exceeds limit')
    def nonspace():
        nonlocal buffer
        buffer = buffer.lstrip()
        while not buffer and not eof:
            fill()
            buffer = buffer.lstrip()
        return buffer[:1]
    fill()
    if nonspace() != '[':
        raise ValueError('Expected a lexical row array')
    buffer = buffer[1:]
    if nonspace() == ']':
        buffer = buffer[1:]
    else:
        while True:
            while True:
                try:
                    row, end = decoder.raw_decode(buffer)
                    break
                except json.JSONDecodeError:
                    if eof:
                        raise ValueError('Truncated or invalid lexical JSON') from None
                    fill()
            if not isinstance(row, list):
                raise ValueError('Expected a lexical row')
            buffer = buffer[end:]
            yield row
            separator = nonspace()
            if separator == ']':
                buffer = buffer[1:]
                break
            if separator != ',':
                raise ValueError('Missing lexical row separator')
            buffer = buffer[1:]
            if not nonspace() or buffer.startswith(']'):
                raise ValueError('Missing lexical row after comma')
    if nonspace():
        raise ValueError('Trailing lexical JSON content')


def spec(path, **extra):
    return dict(url=path.name, bytes=path.stat().st_size, sha256=sha(path), **extra)


def build(root, publish=True):
    root = Path(root)
    web = root / 'web'
    path = web / 'data/manifest.json'
    manifest = json.loads(path.read_text())
    inputs = signature(manifest)
    digest = hashlib.sha256(json.dumps(dict(inputs=inputs, code=sha(__file__), rows=ROWS_PER_PAGE),
                                       sort_keys=True).encode()).hexdigest()[:24]
    destination = web / 'data/concept-rows' / digest
    destination.parent.mkdir(exist_ok=True)
    if not destination.exists():
        scratch = root / 'output/concept-rows'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            db = sqlite3.connect(Path(temp) / 'rows.sqlite')
            db.execute('PRAGMA cache_size=-16384')
            db.execute('PRAGMA temp_store=FILE')
            db.execute('PRAGMA mmap_size=0')
            db.execute('PRAGMA journal_mode=OFF')
            db.execute('CREATE TABLE rows(cid TEXT,id TEXT PRIMARY KEY,payload TEXT)')
            fields = manifest['fields']
            ci, identity = fields.index('concept_id'), fields.index('ID')
            for family, info in manifest['shards'].items():
                source = web / info['url']
                if source.stat().st_size != info['bytes'] or sha(source) != info['sha256']:
                    raise ValueError(f'Changed family shard: {family}')
                with gzip.open(source, 'rt', encoding='utf-8') as stream:
                    for row in array_rows(stream):
                        if len(row) != len(fields):
                            raise ValueError('Lexical field count differs')
                        if row[ci]:
                            db.execute('INSERT INTO rows VALUES(?,?,?)',
                                       (row[ci], row[identity], json.dumps(row, ensure_ascii=False,
                                                                        separators=(',', ':'))))
                db.commit()
            db.execute('CREATE INDEX by_concept ON rows(cid,id)')
            stage = Path(temp) / 'public'
            stage.mkdir()
            concepts = {}
            for (cid,) in db.execute('SELECT DISTINCT cid FROM rows ORDER BY cid'):
                if not cid or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in cid):
                    raise ValueError('Invalid concept asset identifier')
                pages, batch, size, total = [], [], 2, 0
                def flush():
                    nonlocal batch, size
                    target = stage / f'{cid}-{len(pages):03}.json.gz'
                    target.write_bytes(gzip.compress(b'[' + b','.join(batch) + b']', compresslevel=6, mtime=0))
                    if target.stat().st_size > MAX_COMPRESSED_PAGE:
                        raise ValueError('Concept transport page exceeds compressed limit')
                    pages.append(spec(target, rows=len(batch), raw_bytes=size))
                    batch, size = [], 2
                for (payload,) in db.execute('SELECT payload FROM rows WHERE cid=? ORDER BY id', (cid,)):
                    encoded = payload.encode('utf-8')
                    if len(encoded) + 2 > MAX_RAW_PAGE:
                        raise ValueError('Oversized concept row')
                    if batch and (len(batch) >= ROWS_PER_PAGE or size + len(encoded) + 1 > MAX_RAW_PAGE):
                        flush()
                    size += len(encoded) + bool(batch)
                    batch.append(encoded)
                    total += 1
                if batch:
                    flush()
                if total > 100000:
                    raise ValueError('Concept exceeds browser result limit')
                concepts[cid] = dict(rows=total, pages=pages)
            db.close()
            index = dict(schema=1, build_id=digest, inputs=inputs, concepts=concepts,
                         max_page_rows=ROWS_PER_PAGE, max_raw_bytes=MAX_RAW_PAGE,
                         max_compressed_bytes=MAX_COMPRESSED_PAGE)
            (stage / 'manifest.json').write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')) + '\n')
            if (stage / 'manifest.json').stat().st_size > 4 * 1024 * 1024:
                raise ValueError('Concept transport index exceeds limit')
            publishing = destination.with_name('.' + digest + '.publishing')
            if publishing.exists():
                shutil.rmtree(publishing)
            try:
                shutil.copytree(stage, publishing)
                publishing.rename(destination)
            finally:
                shutil.rmtree(publishing, ignore_errors=True)
    index = json.loads((destination / 'manifest.json').read_text())
    # Immutable caches and snapshot drift fail closed before pointer publication.
    if index['inputs'] != inputs or signature(json.loads(path.read_text())) != inputs:
        raise ValueError('Concept transport snapshot drift')
    for concept in index['concepts'].values():
        for info in concept['pages']:
            target = destination / info['url']
            if target.stat().st_size != info['bytes'] or sha(target) != info['sha256']:
                raise ValueError('Corrupt concept transport cache')
    if publish:
        manifest = json.loads(path.read_text())
        manifest['concept_rows'] = dict(spec(destination / 'manifest.json'),
                                       url=f'data/concept-rows/{digest}/manifest.json', build_id=digest)
        temporary = path.with_suffix('.pending')
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(path)
    return destination
