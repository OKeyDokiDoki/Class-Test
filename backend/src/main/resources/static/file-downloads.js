const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const bytes = n => (n / 1024 / 1024).toFixed(2) + ' MiB';
let database;
async function db() {
  if (!database) database = new Promise((resolve, reject) => {
    const open = indexedDB.open('file-demo-downloads', 1);
    open.onupgradeneeded = () => open.result.createObjectStore('tasks', { keyPath: 'id' });
    open.onsuccess = () => resolve(open.result); open.onerror = () => reject(open.error);
  });
  return database;
}
async function store(mode, action) {
  const connection = await db();
  return new Promise((resolve, reject) => {
    const tx = connection.transaction('tasks', mode), req = action(tx.objectStore('tasks'));
    tx.oncomplete = () => resolve(req.result); tx.onerror = () => reject(tx.error); tx.onabort = () => reject(tx.error || new Error('保存下载任务失败'));
  });
}
function persisted(task) {
  return { id: task.id, file: task.file, handle: task.handle, offset: task.offset, etag: task.etag, localModified: task.localModified };
}
export class DownloadManager {
  constructor(container, log, slow) { this.container = container; this.log = log; this.slow = slow; this.tasks = new Map(); }
  async restore() {
    for (const saved of await store('readonly', s => s.getAll())) {
      const task = { ...saved, running: false, message: '已恢复保存的断点；点击继续下载。' };
      this.tasks.set(task.id, task); this.render(task);
    }
  }
  async create(file) {
    if (!window.showSaveFilePicker) throw new Error('续传下载需要桌面 Chrome / Edge 和 localhost 或 HTTPS；也可以点击普通下载。');
    if (this.tasks.has(file.id)) { this.log('已有下载任务，请在任务卡片中点击继续。'); return; }
    // Invoke the picker directly from the click gesture, before other asynchronous work.
    const handle = await window.showSaveFilePicker({ suggestedName: file.name });
    const task = { id: file.id, file, handle, offset: 0, etag: '"' + file.sha256 + '"', localModified: null, running: false };
    await store('readwrite', s => s.put(persisted(task)));
    this.tasks.set(task.id, task); this.render(task); await this.run(task);
  }
  render(task, current = task.offset) {
    let view = task.view;
    if (!view) {
      const card = document.createElement('div'); card.className = 'task'; card.dataset.fileId = task.id;
      const title = document.createElement('strong'); title.textContent = task.file.name;
      const progress = document.createElement('progress'); progress.max = 100; progress.setAttribute('aria-label', '下载进度 ' + task.file.name);
      const state = document.createElement('p'), resume = document.createElement('button'), pause = document.createElement('button'), forget = document.createElement('button');
      resume.textContent = '继续下载'; pause.textContent = '暂停下载'; forget.textContent = '移除任务（保留本地文件）'; forget.className = 'secondary';
      resume.onclick = () => this.run(task).catch(e => this.log(e.message));
      pause.onclick = () => { task.paused = true; task.controller?.abort(); };
      forget.onclick = async () => {
        if (task.running) return;
        await store('readwrite', s => s.delete(task.id)); this.tasks.delete(task.id); card.remove();
      };
      card.append(title, progress, state, resume, pause, forget); this.container.append(card);
      task.view = view = { card, progress, state, resume, pause, forget };
    }
    const percent = task.file.size ? current / task.file.size * 100 : (task.finished ? 100 : 0);
    view.progress.value = percent;
    view.state.textContent = `${bytes(current)} / ${bytes(task.file.size)}（${percent.toFixed(1)}%） ${task.message || ''}`;
    view.resume.disabled = task.running || task.finished; view.pause.disabled = !task.running; view.forget.disabled = task.running;
  }
  async run(task) {
    if (task.running || task.finished) return;
    task.running = true; task.paused = false; task.controller = new AbortController();
    task.message = '连接中…'; this.render(task);
    let writer = null, reader = null, current = task.offset, streamComplete = false;
    try {
      if (task.handle.requestPermission && await task.handle.requestPermission({ mode: 'readwrite' }) !== 'granted')
        throw new Error('需要允许写入所选文件，才能继续下载。');
      const local = await task.handle.getFile();
      if (task.offset > 0 && (local.size !== task.offset || local.lastModified !== task.localModified))
        throw new Error('本地断点文件已被修改，请移除任务并重新选择保存位置。');
      if (task.offset === task.file.size && (task.file.size > 0 || task.localModified !== null)) {
        task.finished = true; task.message = '下载已完成。'; return;
      }
      const headers = task.offset ? { Range: `bytes=${task.offset}-`, 'If-Range': task.etag } : {};
      let response;
      for (let attempt = 0; attempt < 3; attempt++) {
        response = await fetch('/api/files/' + task.id + '/download', { headers, signal: task.controller.signal });
        if (![429, 503].includes(response.status) || attempt === 2) break;
        const delay = Math.min(5, Number(response.headers.get('Retry-After')) || 2);
        await response.body?.cancel(); task.message = '服务繁忙，稍后自动重试…'; this.render(task); await wait(delay * 1000);
      }
      if (!response.ok) throw new Error('下载请求失败：HTTP ' + response.status);
      if (response.headers.get('ETag') !== task.etag) { await response.body?.cancel(); throw new Error('服务器文件版本变化，请重新下载。'); }
      if (task.offset && (response.status !== 206 || response.headers.get('Content-Range') !== `bytes ${task.offset}-${task.file.size - 1}/${task.file.size}`)) {
        await response.body?.cancel(); throw new Error('服务器未返回正确的续传范围，已停止以保护本地断点。');
      }
      if (Number(response.headers.get('Content-Length')) !== task.file.size - task.offset) {
        await response.body?.cancel(); throw new Error('下载长度不符合预期。');
      }
      task.controller.signal.throwIfAborted();
      writer = await task.handle.createWritable({ keepExistingData: task.offset > 0 });
      await writer.truncate(task.offset); await writer.seek(task.offset);
      reader = response.body.getReader();
      task.message = task.offset ? `HTTP 206：从字节 ${task.offset} 继续。` : '下载中；暂停时保存断点。'; this.render(task);
      this.log(`${task.file.name}：HTTP ${response.status}，起始字节 ${task.offset}。`);
      while (true) {
        const { value, done } = await reader.read();
        if (done) { streamComplete = true; break; }
        if (task.paused) break;
        if (current + value.byteLength > task.file.size) throw new Error('下载内容超出预期大小。');
        await writer.write(value); current += value.byteLength; this.render(task, current);
        if (this.slow()) await wait(18);
      }
      if (streamComplete && current !== task.file.size) throw new Error('网络提前结束，保存已有内容后可以继续。');
    } catch (e) {
      task.message = task.paused || e.name === 'AbortError' ? '已暂停。' : e.message;
      if (!task.paused && e.name !== 'AbortError') this.log('下载：' + e.message);
    } finally {
      task.controller.abort();
      try { await reader?.cancel(); } catch (_) { /* disconnected */ }
      if (writer) {
        try {
          // close() commits temporary writes. Save the offset only AFTER the commit.
          // Abrupt refresh discards uncommitted writes and restores the previous checkpoint.
          await writer.close(); const saved = await task.handle.getFile();
          if (saved.size !== current) throw new Error('本地文件长度与断点不一致。');
          task.offset = current; task.localModified = saved.lastModified;
          await store('readwrite', s => s.put(persisted(task)));
          if (streamComplete && current === task.file.size) {
            task.finished = true; task.message = '下载完成；可用 SHA-256 与列表中的原文件校验值比对。';
          } else task.message += ` 已保存断点 ${current} 字节，可刷新后继续。`;
        } catch (e) {
          try { await writer.abort(); } catch (_) { /* close may already have completed */ }
          task.message = '保存断点失败：' + e.message + '。请检查本地文件，必要时重新下载。'; this.log(task.message);
        }
      }
      task.running = false; this.render(task);
    }
  }
}
