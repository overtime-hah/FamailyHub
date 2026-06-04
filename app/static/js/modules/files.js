/* 文件柜模块 */
async function init_files_page() {
  const container = document.getElementById("page-content");
  container.innerHTML = `<div class="spinner"></div>`;
  try {
    const data = await api.get("/api/files/folders");
    renderFolders(container, data.folders || []);
  } catch (err) {
    if (err && err.aborted) return;
    container.innerHTML = '<div class="empty-state"><p>' + escapeHtml(err.message) + '</p></div>';
  }
}

function renderFolders(container, folders) {
  let html = `<div class="page-header flex-between">
    <div><h1>文件柜</h1><p>重要文件安全存放</p></div>
    <button class="btn btn-primary btn-sm" onclick="folderForm()">+ 新建文件夹</button>
  </div><div class="grid-3">`;

  if (folders.length === 0) html += `<div class="empty-state"><p>还没有文件夹</p></div>`;
  folders.forEach(f => {
    html += `<div class="card" style="cursor:pointer" data-folder-id="${f.id}" data-folder-name="${escapeHtml(f.name)}">
      <div style="font-size:40px;text-align:center;padding:20px 0">📁</div>
      <div style="font-weight:600">${escapeHtml(f.name)}</div>
      <div class="text-sm text-secondary">${f.file_count} 个文件</div>
      <button class="btn btn-ghost btn-sm mt-sm" data-del-folder="${f.id}">删除</button>
    </div>`;
  });
  html += `</div>`;
  container.innerHTML = html;

  container.querySelectorAll(".card[data-folder-id]").forEach(card => {
    card.addEventListener("click", function(e) {
      if (e.target.closest("[data-del-folder]")) return;
      viewFolder(Number(this.dataset.folderId), this.dataset.folderName);
    });
  });
  container.querySelectorAll("[data-del-folder]").forEach(btn => {
    btn.addEventListener("click", function(e) {
      e.stopPropagation();
      delFolder(Number(this.dataset.delFolder));
    });
  });
}

window.folderForm = function() {
  openModal(`
    <h2>新建文件夹</h2>
    <div class="form-group"><label>文件夹名</label><input class="input" id="fld-name" placeholder="如：医疗、合同"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="fld-save">创建</button>
    </div>
  `);
  document.getElementById("fld-save").addEventListener("click", async function() {
    const name = document.getElementById("fld-name").value.trim();
    if (!name) return showToast("名称不能为空", "error");
    try {
      await api.post("/api/files/folders", { name });
      closeModal(); showToast("文件夹已创建"); init_files_page();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.delFolder = async function(id) {
  if (!await confirmDialog("删除文件夹会删除其中的所有文件！")) return;
  try {
    await api.del(`/api/files/folders/${id}`);
    init_files_page(); showToast("已删除");
  } catch (err) { showToast(err.message, "error"); }
};

// ─── 查看文件夹 ────────────────────────────────────────

window.viewFolder = async function(folderId, folderName) {
  const container = document.getElementById("page-content");
  container.innerHTML = `<div class="spinner"></div>`;
  try {
    const data = await api.get(`/api/files/folders/${folderId}/files`);
    renderFiles(container, folderId, folderName, data.files || []);
  } catch (err) {
    if (err && err.aborted) return;
    container.innerHTML = '<div class="empty-state"><p>' + escapeHtml(err.message) + '</p></div>';
  }
};

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1048576).toFixed(1) + " MB";
}

function renderFiles(container, folderId, folderName, files) {
  let html = `<div class="page-header flex-between">
    <div><button class="btn btn-ghost btn-sm mb-sm" onclick="init_files_page()">← 返回文件夹列表</button>
    <h1>${escapeHtml(folderName)}</h1><p class="text-secondary">${files.length} 个文件</p></div>
    <button class="btn btn-primary btn-sm" id="upload-btn">+ 上传文件</button>
  </div>
  <input type="file" id="file-input" multiple style="display:none">
  <div class="card-list">`;

  if (files.length === 0) html += `<div class="empty-state"><p>还没有文件</p></div>`;
  files.forEach(f => {
    html += `<div class="card-list-item flex-between">
      <div class="flex-row gap-md">
        <span style="font-size:28px">📄</span>
        <div>
          <div style="font-weight:600">${escapeHtml(f.original_name)}</div>
          <div class="text-sm text-secondary">${formatSize(f.size)} · ${escapeHtml(f.uploader_name)} · ${timeAgo(f.upload_time)}</div>
        </div>
      </div>
      <div class="flex-row gap-sm">
        <a href="${f.url}" class="btn btn-secondary btn-sm" download>下载</a>
        <button class="btn btn-ghost btn-sm" data-del-file="${f.id}" data-folder-id="${folderId}" data-folder-name="${escapeHtml(folderName)}">删除</button>
      </div>
    </div>`;
  });
  html += `</div>`;
  container.innerHTML = html;

  container.querySelectorAll("[data-del-file]").forEach(btn => {
    btn.addEventListener("click", function() {
      delFile(Number(this.dataset.delFile), Number(this.dataset.folderId), this.dataset.folderName);
    });
  });

  const uploadBtn = document.getElementById("upload-btn");
  const fileInput = document.getElementById("file-input");
  if (uploadBtn) {
    uploadBtn.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", async function() {
      const fList = this.files;
      if (!fList.length) return;
      const formData = new FormData();
      for (let f of fList) formData.append("files", f);
      try {
        await api.post(`/api/files/folders/${folderId}/files`, formData);
        showToast(`上传了 ${fList.length} 个文件`);
        viewFolder(folderId, folderName);
      } catch (err) { showToast(err.message, "error"); }
    });
  }
}

window.delFile = async function(fileId, folderId, folderName) {
  if (!await confirmDialog("确定删除？")) return;
  try {
    await api.del(`/api/files/files/${fileId}`);
    showToast("已删除");
    viewFolder(folderId, folderName);
  } catch (err) { showToast(err.message, "error"); }
};
