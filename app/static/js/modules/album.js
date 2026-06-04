/* 相册模块 */
async function init_album_page() {
  const container = document.getElementById("page-content");
  container.innerHTML = `<div class="spinner"></div>`;
  try {
    const data = await api.get("/api/album/albums");
    renderAlbumList(container, data.albums || []);
  } catch (err) {
    if (err && err.aborted) return;
    container.innerHTML = '<div class="empty-state"><p>' + err.message + '</p></div>';
  }
}

function renderAlbumList(container, albums) {
  let html = `<div class="page-header flex-between">
    <div><h1>家庭相册</h1><p>珍藏每一刻美好</p></div>
    <button class="btn btn-primary btn-sm" onclick="albumForm()">+ 新建相册</button>
  </div><div class="grid-3">`;

  if (albums.length === 0) html += `<div class="empty-state"><p>还没有相册</p></div>`;
  albums.forEach(a => {
    html += `<div class="card" style="cursor:pointer" data-album-id="${a.id}" data-album-name="${escapeHtml(a.name)}">
      <div style="font-size:40px;text-align:center;padding:20px 0">📷</div>
      <div style="font-weight:600">${escapeHtml(a.name)}</div>
      <div class="text-sm text-secondary">${a.photo_count} 张照片 · by ${escapeHtml(a.creator_name)}</div>
      <button class="btn btn-ghost btn-sm mt-sm" data-del-album="${a.id}">删除</button>
    </div>`;
  });
  html += `</div>`;
  container.innerHTML = html;

  // 绑定事件
  container.querySelectorAll("[data-album-id]").forEach(card => {
    card.addEventListener("click", function(e) {
      if (e.target.closest("[data-del-album]")) return;
      viewAlbum(parseInt(this.dataset.albumId), this.dataset.albumName);
    });
  });
  container.querySelectorAll("[data-del-album]").forEach(btn => {
    btn.addEventListener("click", function(e) {
      e.stopPropagation();
      delAlbum(parseInt(this.dataset.delAlbum));
    });
  });
};

window.albumForm = function() {
  openModal(`
    <h2>新建相册</h2>
    <div class="form-group"><label>相册名称</label><input class="input" id="alb-name" placeholder="相册名称"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="alb-save">创建</button>
    </div>
  `);
  document.getElementById("alb-save").addEventListener("click", async function() {
    const name = document.getElementById("alb-name").value.trim();
    if (!name) return showToast("名称不能为空", "error");
    try {
      await api.post("/api/album/albums", { name });
      closeModal(); showToast("相册已创建"); init_album_page();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.delAlbum = async function(id) {
  if (!await confirmDialog("删除相册会同时删除所有照片！")) return;
  try {
    await api.del(`/api/album/albums/${id}`);
    showToast("已删除"); init_album_page();
  } catch (err) { showToast(err.message, "error"); }
};

// ─── 查看相册（照片列表） ──────────────────────────────

window.viewAlbum = async function(albumId, albumName) {
  const container = document.getElementById("page-content");
  container.innerHTML = `<div class="spinner"></div>`;
  try {
    const data = await api.get(`/api/album/albums/${albumId}/photos`);
    renderPhotos(container, albumId, albumName, data.photos || []);
  } catch (err) {
    if (err && err.aborted) return;
    container.innerHTML = '<div class="empty-state"><p>' + err.message + '</p></div>';
  }
};

function renderPhotos(container, albumId, albumName, photos) {
  let html = `<div class="page-header flex-between">
    <div><button class="btn btn-ghost btn-sm mb-sm" id="back-to-albums">← 返回相册列表</button>
    <h1>${escapeHtml(albumName)}</h1><p class="text-secondary">${photos.length} 张照片</p></div>
    <button class="btn btn-primary btn-sm" id="upload-btn">+ 上传照片</button>
  </div>
  <input type="file" id="photo-file-input" accept="image/*" multiple style="display:none">
  <div class="masonry">`;

  if (photos.length === 0) html += `<div class="empty-state"><p>还没有照片</p></div>`;
  photos.forEach(p => {
    html += `<div class="masonry-item" data-photo-url="${escapeHtml(p.url)}">
      <img src="${p.url}" alt="${escapeHtml(p.description)}" loading="lazy">
      <div style="padding:8px;font-size:12px">
        <div>${escapeHtml(p.description)}</div>
        <div class="text-secondary">${escapeHtml(p.uploader_name)} · ${timeAgo(p.upload_time)}</div>
        ${p.comments.map(c => `<div style="margin-top:4px"><strong>${escapeHtml(c.username)}:</strong> ${escapeHtml(c.content)}</div>`).join("")}
        <div class="flex-row gap-sm mt-sm">
          <button class="btn btn-ghost btn-sm" data-comment-photo="${p.id}">💬</button>
          <button class="btn btn-ghost btn-sm" data-del-photo="${p.id}" data-del-album-id="${albumId}">删除</button>
        </div>
      </div>
    </div>`;
  });
  html += `</div>`;
  container.innerHTML = html;

  // 返回按钮
  document.getElementById("back-to-albums").addEventListener("click", init_album_page);

  // 照片 lightbox
  container.querySelectorAll("[data-photo-url]").forEach(item => {
    item.addEventListener("click", function(e) {
      if (e.target.closest("[data-comment-photo]") || e.target.closest("[data-del-photo]")) return;
      openLightbox(this.dataset.photoUrl);
    });
  });

  // 评论按钮
  container.querySelectorAll("[data-comment-photo]").forEach(btn => {
    btn.addEventListener("click", function(e) {
      e.stopPropagation();
      commentPhoto(parseInt(this.dataset.commentPhoto));
    });
  });

  // 删除按钮
  container.querySelectorAll("[data-del-photo]").forEach(btn => {
    btn.addEventListener("click", function(e) {
      e.stopPropagation();
      delPhoto(parseInt(this.dataset.delPhoto), parseInt(this.dataset.delAlbumId));
    });
  });

  // 上传按钮
  const uploadBtn = document.getElementById("upload-btn");
  const fileInput = document.getElementById("photo-file-input");
  if (uploadBtn) {
    uploadBtn.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", async function() {
      const files = this.files;
      if (!files.length) return;
      const formData = new FormData();
      for (let f of files) formData.append("photos", f);
      try {
        await api.post(`/api/album/albums/${albumId}/photos`, formData);
        showToast(`上传了 ${files.length} 张照片`);
        viewAlbum(albumId, albumName);
      } catch (err) { showToast(err.message, "error"); }
    });
  }
}

window.openLightbox = function(url) {
  document.getElementById("lightbox-img").src = url;
  document.getElementById("lightbox").classList.add("active");
};

window.commentPhoto = function(photoId) {
  openModal(`
    <h2>添加评论</h2>
    <textarea class="textarea" id="comment-text" placeholder="写下评论..."></textarea>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="comment-save">评论</button>
    </div>
  `);
  document.getElementById("comment-save").addEventListener("click", async function() {
    const content = document.getElementById("comment-text").value.trim();
    if (!content) return;
    try {
      await api.post(`/api/album/photos/${photoId}/comments`, { content });
      closeModal(); showToast("评论已添加");
      // 刷新当前页面 (由 viewAlbum 的 albumId/name 从页面状态恢复)
      const btn = document.querySelector('[onclick*="init_album_page"]');
      if (btn) window.location.hash = "#/album";
      else window.location.reload();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.delPhoto = async function(photoId, albumId) {
  if (!await confirmDialog("确定删除？")) return;
  try {
    await api.del(`/api/album/photos/${photoId}`);
    showToast("已删除");
    const container = document.getElementById("page-content");
    const albumName = container.querySelector("h1")?.textContent || "";
    viewAlbum(albumId, albumName);
  } catch (err) { showToast(err.message, "error"); }
};
