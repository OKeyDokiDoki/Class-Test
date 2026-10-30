"""Real HTTP verification and bounded concurrent downloads; Python standard library only."""
import argparse
import concurrent.futures
import hashlib
import http.client
import json
import platform
import random
import statistics
import threading
import time
import urllib.parse
import uuid
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://localhost:8081')
    parser.add_argument('--mib', type=int, default=64)
    parser.add_argument('--concurrency', type=int, default=20)
    parser.add_argument('--out', default='file-transfer-results')
    args = parser.parse_args()
    if not 16 <= args.mib <= 256 or not 1 <= args.concurrency <= 32:
        parser.error('Use 16-256 MiB and 1-32 concurrent clients.')
    base = urllib.parse.urlsplit(args.base)
    if base.scheme not in ('http', 'https') or base.username or base.password:
        parser.error('Use an HTTP(S) base URL without credentials.')
    output = Path(args.out); output.mkdir(parents=True, exist_ok=True)
    prefix = base.path.rstrip('/') + '/api/files'

    def connection():
        cls = http.client.HTTPSConnection if base.scheme == 'https' else http.client.HTTPConnection
        return cls(base.hostname, base.port, timeout=30)

    def raw(method, path, body=None, headers=None):
        conn = connection()
        try:
            conn.request(method, prefix + path, body, headers or {})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def request(method, path, body=None):
        encoded = json.dumps(body).encode() if body is not None else None
        status, _, payload = raw(method, path, encoded, {'Content-Type': 'application/json'})
        value = json.loads(payload)
        if status >= 300:
            raise RuntimeError(f'{method} {path}: {status} {value}')
        return value['data']

    def multipart(entries):
        boundary = uuid.uuid4().hex; data = bytearray()
        for field, name, content in entries:
            data.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode())
            data.extend(content); data.extend(b'\r\n')
        data.extend(f'--{boundary}--\r\n'.encode())
        return data, {'Content-Type': 'multipart/form-data; boundary=' + boundary}

    def stats():
        return request('GET', '/download-stats')

    def idle():
        for _ in range(100):
            value = stats()
            if value['active'] == 0:
                return value
            time.sleep(.05)
        raise AssertionError('Download slots did not return to zero after disconnects.')

    report = {'status': 'RUNNING', 'runtime': platform.python_version(), 'os': platform.system(), 'checks': []}
    def passed(name):
        report['checks'].append(name); print('PASS:', name, flush=True)

    source = output / 'recording-large.bin'
    rng = random.Random(20261030); digest = hashlib.sha256()
    with source.open('wb') as stream:
        for _ in range(args.mib):
            block = rng.randbytes(1024 * 1024); stream.write(block); digest.update(block)
    expected = digest.hexdigest(); size = source.stat().st_size; chunk_size = 4 * 1024 * 1024
    session = request('POST', '/uploads', {'name': source.name, 'size': size, 'chunkSize': chunk_size, 'sha256': expected})
    upload_id = session['id']; total = session['totalChunks']
    with source.open('rb') as stream:
        first = stream.read(chunk_size)
        damaged = bytes([first[0] ^ 1]) + first[1:]
        payload, headers = multipart([('file', 'chunk', damaged)])
        status, _, body = raw('PUT', f'/uploads/{upload_id}/chunks/0?sha256={hashlib.sha256(first).hexdigest()}', payload, headers)
        error = json.loads(body)
        assert status == 422 and error['code'] == 'CHUNK_CHECKSUM_MISMATCH' and error['data']['indexes'] == [0], error
        passed('damaged transmission returns 422 and exact repair index')
        for index in list(reversed([i for i in range(total) if i != 1])):
            stream.seek(index * chunk_size); block = stream.read(chunk_size)
            payload, headers = multipart([('file', 'chunk', block)])
            status, _, body = raw('PUT', f'/uploads/{upload_id}/chunks/{index}?sha256={hashlib.sha256(block).hexdigest()}', payload, headers)
            assert status == 200, body
        status, _, body = raw('POST', f'/uploads/{upload_id}/complete')
        error = json.loads(body)
        assert status == 409 and error['code'] == 'CHUNK_REPAIR_REQUIRED' and error['data']['indexes'] == [1], error
        passed('completion reports missing indexes; healthy chunks retained')
        stream.seek(chunk_size); block = stream.read(chunk_size)
        payload, headers = multipart([('file', 'chunk', block)])
        status, _, body = raw('PUT', f'/uploads/{upload_id}/chunks/1?sha256={hashlib.sha256(block).hexdigest()}', payload, headers)
        assert status == 200, body
    info = request('POST', f'/uploads/{upload_id}/complete')
    assert info['sha256'] == expected and info['size'] == size
    assert request('POST', f'/uploads/{upload_id}/complete')['id'] == info['id']
    passed('out-of-order chunks repaired and merged with full SHA-256; idempotent completion')

    path = '/' + info['id'] + '/download'; etag = '"' + expected + '"'
    partial = output / 'recording-downloaded.bin'
    conn = connection(); conn.request('GET', prefix + path); response = conn.getresponse()
    assert response.status == 200
    with partial.open('wb') as stream:
        stream.write(response.read(2 * 1024 * 1024 + 123))
    conn.close(); offset = partial.stat().st_size
    conn = connection(); conn.request('GET', prefix + path, headers={'Range': f'bytes={offset}-', 'If-Range': etag})
    response = conn.getresponse()
    assert response.status == 206 and response.getheader('Content-Range') == f'bytes {offset}-{size-1}/{size}'
    with partial.open('ab') as stream:
        while block := response.read(64 * 1024): stream.write(block)
    conn.close()
    with partial.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected
    passed('interrupted download resumes with Range/If-Range and byte-identical SHA-256')
    conn = connection(); conn.request('GET', prefix + path, headers={'Range': 'bytes=1-', 'If-Range': '"old-version"'})
    response = conn.getresponse(); assert response.status == 200; conn.close()
    assert raw('GET', path, headers={'Range': f'bytes={size}-'})[0] == 416
    passed('changed If-Range returns 200; invalid offset returns 416')

    payload, headers = multipart([('files', f'small-{i}.txt', f'small file {i}'.encode()) for i in range(3)])
    status, _, body = raw('POST', '/batch', payload, headers)
    small = json.loads(body)['data']; assert status == 200 and len(small) == 3 and all(x['file'] for x in small)
    ids = [x['file']['id'] for x in small]
    status, _, body = raw('POST', '/batch-download', json.dumps(ids).encode(), {'Content-Type': 'application/json'})
    import io, zipfile
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        assert status == 200 and len(archive.namelist()) == 3
        assert sorted(archive.read(name) for name in archive.namelist()) == [f'small file {i}'.encode() for i in range(3)]
    passed('small-file batch upload and streamed ZIP retain all content')
    idle()

    barrier = threading.Barrier(args.concurrency)
    def worker(index):
        barrier.wait(timeout=15); started = time.perf_counter(); digest = hashlib.sha256(); count = 0
        conn = connection()
        try:
            conn.request('GET', prefix + path); response = conn.getresponse(); assert response.status == 200, response.status
            while block := response.read(64 * 1024):
                digest.update(block); count += len(block); time.sleep(.001)
            assert count == size and digest.hexdigest() == expected
            return time.perf_counter() - started
        finally:
            conn.close()
    observed = 0; started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        jobs = [pool.submit(worker, i) for i in range(args.concurrency)]
        while not all(job.done() for job in jobs):
            observed = max(observed, stats()['active']); time.sleep(.05)
        durations = [job.result() for job in jobs]
    elapsed = time.perf_counter() - started
    assert args.concurrency == 1 or observed >= 2, 'Requests never overlapped'
    report['concurrent'] = {'clients': args.concurrency, 'success': len(durations), 'bytesPerFile': size,
        'observedPeakActive': observed, 'wallSeconds': round(elapsed, 3), 'aggregateMiBPerSecond': round(size*args.concurrency/1024**2/elapsed, 2),
        'p95Seconds': round(sorted(durations)[min(len(durations)-1, int(.95*len(durations)))], 3), 'allSha256Match': True}
    passed(f'{args.concurrency} concurrent full downloads; every SHA-256 matches')
    idle()

    held = []; limit = stats()['maxConcurrent']
    try:
        for _ in range(limit):
            conn = connection(); conn.request('GET', prefix + path); response = conn.getresponse()
            assert response.status == 200; held.append((conn, response))
        status, headers, body = raw('GET', path)
        assert status == 429 and headers.get('Retry-After') == '2', (status, body[:200])
        passed('capacity limit rejects excess with 429 and Retry-After')
    finally:
        for conn, response in held: conn.close()
    report['finalStats'] = idle()
    passed('disconnects release all active download slots')
    report.update(status='PASS', fileBytes=size, fileId=info['id'], sha256=expected, resumeOffset=offset)
    (output/'validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
