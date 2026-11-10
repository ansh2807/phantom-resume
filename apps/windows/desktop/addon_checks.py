"""Bounded local addon smoke checks; no document or network submission."""
from pathlib import Path
import tempfile, sqlite3, secrets, gc
from contextlib import closing

def run_checks():
    from payload.fec import FecCodec
    from payload.split import ChannelShareSplit
    from payload.encrypt import AtsKeyedCipher
    from persistence.db import apply_migrations
    rows=[]
    def check(name,ok):
        rows.append({'name':name,'passed':bool(ok)})
    payload=b'\0Synthetic fixture'+bytes(range(256))+b'\0'
    codec=FecCodec(); shards=codec.encode(payload)
    check('FEC two distinct replicas',codec.decode(shards[1:])==payload)
    check('FEC duplicate rejected',codec.decode([shards[0],shards[0]]) is None)
    split=ChannelShareSplit(2,3); chunks=split.split_chunked(payload)
    check('Shamir binary multi-chunk recovery',split.recombine_chunked([c[:2] for c in chunks])==payload)
    cipher=AtsKeyedCipher(secrets.token_bytes(32)); blob=cipher.encrypt('local-test',payload)
    check('Cipher recovery',cipher.decrypt('local-test',blob)==payload)
    check('Cipher wrong context rejected',cipher.decrypt('other-test',blob) is None)
    tampered=bytes([blob[0]^1])+blob[1:]
    check('Cipher header tampering rejected',cipher.decrypt('local-test',tampered) is None)
    with tempfile.TemporaryDirectory(prefix='phantom-addon-') as tmp:
        db=Path(tmp)/'synthetic.db';apply_migrations(str(db));apply_migrations(str(db))
        with closing(sqlite3.connect(db)) as conn:
            check('Fresh migration and rerun',len(conn.execute('PRAGMA table_info(submissions)').fetchall())==17)
        gc.collect()
    return {'passed':sum(r['passed'] for r in rows),'failed':sum(not r['passed'] for r in rows),'checks':rows,
            'scope':'Local synthetic checks only. Addon API uses no document channels. No live ATS tested.',
            'unimplemented':['acrostic_verbs','synonym_sets','attention_path','calibrator']}
