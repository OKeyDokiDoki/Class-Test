import { DownloadManager } from './file-downloads.js';
const $ = id => document.getElementById(id);
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const bytes = n => (n / 1024 / 1024).toFixed(2) + ' MiB';
const json = body => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
let paused = false, running = false, activeUpload = null, uploadXhr = null;
function log(text) { $('log').textContent = `${new Date().toLocaleTimeString()} ${text}\n` + $('log').textContent; }
function apiError(value, status) {
  const error = new Error(value.message || value.detail || `HTTP ${status}`);
  Object.assign(error, { status, code: value.code, data: value.data }); return error;
}
async function request(path, options = {}) {
  const r = await fetch('/api/files' + path, options), value = await r.json();
  if (!r.ok) throw apiError(value, r.status);
  return value.data;
}
function transfer(path, form, method, progress, onXhr = () => {}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest(); onXhr(xhr); xhr.open(method, '/api/files' + path); xhr.responseType = 'json';
    xhr.upload.onprogress = event => { if (event.lengthComputable) progress(event.loaded / event.total); };
    xhr.onload = () => xhr.status >= 200 && xhr.status < 300 ? resolve(xhr.response.data) : reject(apiError(xhr.response || {}, xhr.status));
    xhr.onerror = () => reject(new Error('网络中断，可继续重试'));
    xhr.onabort = () => reject(new DOMException('已暂停', 'AbortError'));
    xhr.send(form);
  });
}
async function digest(blob) {
  const value = await crypto.subtle.digest('SHA-256', await blob.arrayBuffer());
  return Array.from(new Uint8Array(value), n => n.toString(16).padStart(2, '0')).join('');
}
const downloads = new DownloadManager($('downloads'), log, () => $('slow').checked);
downloads.restore().catch(e => log('恢复下载任务失败：' + e.message));
async function refresh() {
  const files = await request(''); $('files').replaceChildren();
  for (const file of files) {
    const row = document.createElement('tr'), select = document.createElement('input');
    select.type = 'checkbox'; select.value = file.id; select.dataset.size = file.size; select.disabled = file.size > 2 * 1024 ** 2;
    const first = document.createElement('td'); first.append(select); row.append(first);
    const name = document.createElement('td'); name.textContent = file.name;
    const hash = document.createElement('code'); hash.textContent = file.sha256; name.append(document.createElement('br'), hash); row.append(name);
    const size = document.createElement('td'); size.textContent = bytes(file.size); row.append(size);
    const td = document.createElement('td'), link = document.createElement('a'), button = document.createElement('button');
    link.href = '/api/files/' + file.id + '/download'; link.textContent = '普通下载';
    button.textContent = '续传下载'; button.onclick = () => downloads.create(file).catch(e => log('下载：' + e.message));
    td.append(link, button); row.append(td); $('files').append(row);
  }
}
$('upload').onclick = async () => {
  if (running) return;
  const file = $('large').files[0]; if (!file) return log('请先选择大文件。');
  if (file.size > 20 * 1024 ** 3) return log('文件超过 20 GiB。');
  const expectedHash = $('hash').value.trim();
  if (expectedHash && !/^[0-9a-f]{64}$/i.test(expectedHash)) return log('完整 SHA-256 格式不正确。');
  running = true; paused = false; $('upload').disabled = true; $('large').disabled = true; $('cancel').disabled = true; $('pause').disabled = false;
  let confirmed = 0;
  const progress = (sent = 0) => {
    const count = Math.min(file.size, confirmed + sent), percent = file.size ? count / file.size * 100 : 0;
    $('progress').value = percent; $('state').textContent = `已传 ${bytes(count)} / ${bytes(file.size)}（${percent.toFixed(1)}%）`;
  };
  try {
    const fingerprint = await digest(new Blob([file.slice(0, 65536), file.slice(Math.max(0, file.size - 65536))]));
    const key = 'file-upload:' + JSON.stringify([file.name, file.size, file.lastModified, fingerprint, expectedHash]);
    let uploadId = localStorage.getItem(key), status;
    if (uploadId) {
      try { status = await request('/uploads/' + uploadId); }
      catch (e) { if (e.status !== 404) throw e; localStorage.removeItem(key); uploadId = null; }
    }
    if (status?.completed) { localStorage.removeItem(key); log('该上传已完成。'); await refresh(); return; }
    if (!uploadId) {
      const session = await request('/uploads', json({ name: file.name, size: file.size, chunkSize: 5 * 1024 ** 2, sha256: expectedHash || null }));
      uploadId = session.id; localStorage.setItem(key, uploadId); status = { session, uploaded: [], chunkHashes: {} };
    }
    const { chunkSize, totalChunks } = status.session, uploaded = new Set(status.uploaded);
    const part = i => file.slice(i * chunkSize, Math.min(file.size, (i + 1) * chunkSize));
    confirmed = [...uploaded].reduce((n, i) => n + part(i).size, 0); progress();
    activeUpload = { id: uploadId, key };
    log(`上传会话 ${uploadId}；后台已有 ${uploaded.size}/${totalChunks} 片。`);
    let injected = false;
    async function send(i) {
      const chunk = part(i), sha256 = await digest(chunk);
      if (paused) throw new DOMException('已暂停', 'AbortError');
      for (let attempt = 0; attempt < 3; attempt++) {
        if (paused) throw new DOMException('已暂停', 'AbortError');
        let payload = chunk;
        if ($('corrupt').checked && !injected && chunk.size) {
          const changed = new Uint8Array(await chunk.arrayBuffer()); changed[0] ^= 1; payload = new Blob([changed]); injected = true;
          log(`演示：修改分片 ${i} 的一个字节，保留原 SHA-256。`);
        }
        const form = new FormData(); form.append('file', payload, 'chunk');
        try {
          await transfer(`/uploads/${uploadId}/chunks/${i}?sha256=${sha256}`, form, 'PUT', ratio => progress(chunk.size * ratio), xhr => uploadXhr = xhr);
          uploaded.add(i); confirmed += chunk.size; progress(); return;
        } catch (e) {
          progress();
          if (paused || e.name === 'AbortError') throw e;
          const retryable = e.code === 'CHUNK_CHECKSUM_MISMATCH' || !e.status || e.status >= 500 || e.status === 429;
          if (!retryable || attempt === 2) throw e;
          log(`分片 ${i}：${e.code || e.message}；自动重传第 ${attempt + 1} 次。后台要求重传 ${JSON.stringify(e.data?.indexes || [i])}。`);
          await wait(300 * (attempt + 1));
        } finally { uploadXhr = null; }
      }
    }
    for (let i = 0; i < totalChunks; i++) {
      if (paused) throw new DOMException('已暂停', 'AbortError');
      if (uploaded.has(i)) {
        if (status.chunkHashes[i] !== await digest(part(i))) throw new Error('所选文件与已上传内容不一致，请取消后重新上传');
      } else { await send(i); if ($('slow').checked) await wait(350); }
    }
    for (let repairRound = 0; repairRound < 4; repairRound++) {
      if (paused) throw new DOMException('已暂停', 'AbortError');
      $('state').textContent = '传输 100%；后台正在校验、合并和保存…';
      try {
        const result = await request('/uploads/' + uploadId + '/complete', { method: 'POST' });
        localStorage.removeItem(key); activeUpload = null; $('progress').value = 100;
        $('state').textContent = '上传完成；完整 SHA-256：' + result.sha256;
        log('上传与后台合并成功：' + result.name); await refresh(); break;
      } catch (e) {
        if (e.code !== 'CHUNK_REPAIR_REQUIRED' || repairRound === 3) throw e;
        log('合并前发现缺失 / 损坏分片，后台要求重传：' + e.data.indexes.join(', '));
        for (const i of e.data.indexes) {
          if (uploaded.delete(i)) confirmed -= part(i).size;
          progress(); await send(i);
        }
      }
    }
  } catch (e) {
    progress();
    if (e.name === 'AbortError' || paused) { $('state').textContent = `已暂停，后台确认保存 ${bytes(confirmed)}；重新选择同一文件可继续。`; log('上传已暂停，未完成分片会重传。'); }
    else log('上传失败：' + e.message + '；可点击继续上传重试。');
  } finally { running = false; uploadXhr = null; $('upload').disabled = false; $('large').disabled = false; $('pause').disabled = true; $('cancel').disabled = !activeUpload; }
};
$('pause').onclick = () => { paused = true; uploadXhr?.abort(); };
$('cancel').onclick = async () => {
  if (!activeUpload || running) return;
  try {
    await request('/uploads/' + activeUpload.id, { method: 'DELETE' }); localStorage.removeItem(activeUpload.key); activeUpload = null;
    $('cancel').disabled = true; $('progress').value = 0; $('state').textContent = '已取消，临时分片已清理。';
  } catch (e) { log(e.message); }
};
$('batch').onclick = async () => {
  const files = Array.from($('small').files);
  if (!files.length || files.length > 100 || files.some(f => f.size > 2 * 1024 ** 2) || files.reduce((n,f) => n+f.size,0) > 64 * 1024 ** 2)
    return log('请选择 1–100 个文件；单个 ≤ 2 MiB，总计 ≤ 64 MiB。');
  $('batch').disabled = true;
  try {
    const form = new FormData(); files.forEach(f => form.append('files', f));
    const result = await transfer('/batch', form, 'POST', ratio => {
      $('batch-progress').value = ratio * 100;
      $('batch-state').textContent = `批量传输 ${(ratio * 100).toFixed(1)}%` + (ratio === 1 ? '；后台正在逐个保存…' : '');
    });
    for (const item of result) log(item.name + '：' + (item.file ? '成功 ' + item.file.id : item.error));
    $('batch-state').textContent = `处理完成：成功 ${result.filter(x => x.file).length}，失败 ${result.filter(x => !x.file).length}。`; await refresh();
  } catch (e) { log(e.message); } finally { $('batch').disabled = false; }
};
$('zip').onclick = async () => {
  const selected = Array.from($('files').querySelectorAll('input:checked'));
  if (!selected.length || selected.length > 100 || selected.reduce((n,x) => n + Number(x.dataset.size), 0) > 64 * 1024 ** 2)
    return log('请选择总计 ≤ 64 MiB 的 1–100 个小文件。');
  $('zip').disabled = true;
  try {
    const r = await fetch('/api/files/batch-download', json(selected.map(x => x.value)));
    if (!r.ok) throw new Error('批量下载失败：HTTP ' + r.status);
    const url = URL.createObjectURL(await r.blob()), a = document.createElement('a');
    a.href = url; a.download = 'files.zip'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 10000); log('ZIP 下载完成。');
  } catch (e) { log(e.message); } finally { $('zip').disabled = false; }
};
async function stats() {
  const s = await request('/download-stats');
  $('stats').textContent = `正在下载 ${s.active} / ${s.maxConcurrent}　峰值并发 ${s.peakActive}　已完成 ${s.completed}　中断 / 非成功响应 ${s.failed}　繁忙拒绝 ${s.rejected}`;
}
$('refresh').onclick = () => refresh().catch(e => log(e.message));
$('stats-refresh').onclick = () => stats().catch(e => log(e.message));
refresh().catch(e => log('后端连接失败：' + e.message)); stats().catch(e => log(e.message));
