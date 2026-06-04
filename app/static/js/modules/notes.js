/* 笔记模块：Wiki、食谱、留言板 */
let notesTab = "wiki";

async function init_notes_page() {
  notesTab = "wiki";
  await loadNotesTab();
}

async function loadNotesTab() {
  const container = document.getElementById("page-content");
  const tabs = [
    { key: "wiki", label: "📖 家庭 Wiki" },
    { key: "recipes", label: "🍳 食谱" },
    { key: "messages", label: "💬 留言板" },
  ];
  let header = `<div class="page-header"><h1>笔记与知识库</h1></div>
  <div class="flex-row gap-sm mb-md">`;
  tabs.forEach(t => {
    const cls = notesTab === t.key ? "btn-primary" : "btn-secondary";
    header += `<button class="btn btn-sm ${cls}" onclick="switchNotesTab('${t.key}')">${t.label}</button>`;
  });
  header += `</div><div id="notes-content"><div class="spinner"></div></div>`;
  container.innerHTML = header;

  try {
    if (notesTab === "wiki") await loadWiki();
    else if (notesTab === "recipes") await loadRecipes();
    else await loadMessages();
  } catch (err) {
    if (err && err.aborted) return;
    document.getElementById("notes-content").innerHTML = '<div class="empty-state"><p>' + err.message + '</p></div>';
  }
}

window.switchNotesTab = async function(key) {
  notesTab = key;
  await loadNotesTab();
};

// ─── Wiki ───────────────────────────────────────────────

async function loadWiki() {
  const data = await api.get("/api/notes/wiki");
  const div = document.getElementById("notes-content");
  let html = `<div class="search-bar">
    <input class="input" id="wiki-search" placeholder="🔍 搜索笔记..." style="flex:1" oninput="filterWiki()">
    <button class="btn btn-primary btn-sm" onclick="wikiForm()">+ 新建</button>
  </div><div class="card-list" id="wiki-list">`;
  data.notes.forEach(n => {
    html += wikiCard(n);
  });
  html += `</div>`;
  div.innerHTML = html;
  window._wikiData = data.notes;
}

function wikiCard(n) {
  return `<div class="card-list-item">
    <div class="flex-between mb-sm">
      <div><strong>${n.title}</strong> ${n.category ? `<span class="badge badge-blue">${n.category}</span>` : ''}</div>
      <div class="flex-row gap-sm">
        <button class="btn btn-ghost btn-sm" onclick="editWiki(${n.id})">编辑</button>
        <button class="btn btn-ghost btn-sm" onclick="delWiki(${n.id})">删除</button>
      </div>
    </div>
    <div class="text-sm text-secondary">${n.author_name} · ${timeAgo(n.updated_at)}</div>
    ${n.content_md ? `<div class="text-sm mt-sm" style="white-space:pre-wrap;max-height:120px;overflow:hidden">${n.content_md}</div>` : ''}
  </div>`;
}

window.filterWiki = function() {
  const q = document.getElementById("wiki-search").value.toLowerCase();
  const container = document.getElementById("wiki-list");
  const notes = window._wikiData || [];
  container.innerHTML = notes.filter(n => n.title.includes(q) || n.content_md.includes(q) || n.category.includes(q))
    .map(n => wikiCard(n)).join("") || '<div class="empty-state"><p>没有匹配结果</p></div>';
};

window.wikiForm = function(note) {
  const isEdit = !!note;
  openModal(`
    <h2>${isEdit ? '编辑笔记' : '新建笔记'}</h2>
    <div class="form-group"><label>标题</label><input class="input" id="wiki-title" value="${isEdit ? escapeHtml(note.title) : ''}"></div>
    <div class="form-group"><label>分类</label><input class="input" id="wiki-cat" placeholder="家电, 急救, WiFi..." value="${isEdit ? escapeHtml(note.category) : ''}"></div>
    <div class="form-group"><label>内容 (Markdown)</label><textarea class="textarea" id="wiki-md" style="min-height:160px">${isEdit ? escapeHtml(note.content_md) : ''}</textarea></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="wiki-save">保存</button>
    </div>
  `);
  document.getElementById("wiki-save").addEventListener("click", async function() {
    const title = document.getElementById("wiki-title").value.trim();
    if (!title) return showToast("标题不能为空", "error");
    const body = {
      title,
      content_md: document.getElementById("wiki-md").value,
      category: document.getElementById("wiki-cat").value.trim(),
    };
    try {
      if (isEdit) { await api.put(`/api/notes/wiki/${note.id}`, body); }
      else { await api.post("/api/notes/wiki", body); }
      closeModal(); showToast("已保存"); loadWiki();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.editWiki = async function(id) {
  const notes = window._wikiData || [];
  const note = notes.find(n => n.id === id);
  if (note) wikiForm(note);
};

window.delWiki = async function(id) {
  if (!await confirmDialog("确定删除此笔记？")) return;
  await api.del(`/api/notes/wiki/${id}`);
  loadWiki(); showToast("已删除");
};

// ─── 食谱 ───────────────────────────────────────────────

async function loadRecipes() {
  const data = await api.get("/api/notes/recipes");
  const div = document.getElementById("notes-content");
  let html = `<button class="btn btn-primary btn-sm mb-md" onclick="recipeForm()">+ 添加食谱</button><div class="card-list">`;
  if (data.recipes.length === 0) html += `<div class="empty-state"><p>还没有食谱</p></div>`;
  data.recipes.forEach(r => {
    html += `<div class="card-list-item">
      <div class="flex-between mb-sm">
        <strong>${r.name}</strong>
        <div class="flex-row gap-sm">
          <button class="btn btn-ghost btn-sm" onclick="editRecipe(${r.id})">编辑</button>
          <button class="btn btn-ghost btn-sm" onclick="delRecipe(${r.id})">删除</button>
        </div>
      </div>
      <div class="text-sm"><strong>配料:</strong> ${r.ingredients || '暂无'}</div>
      <div class="text-sm mt-sm" style="white-space:pre-wrap"><strong>步骤:</strong> ${r.steps || '暂无'}</div>
      <div class="text-sm text-secondary">by ${r.author_name} · ${timeAgo(r.created_at)}</div>
    </div>`;
  });
  html += `</div>`;
  div.innerHTML = html;
  window._recipeData = data.recipes;
}

window.recipeForm = function(recipe) {
  const isEdit = !!recipe;
  openModal(`
    <h2>${isEdit ? '编辑食谱' : '添加食谱'}</h2>
    <div class="form-group"><label>菜名</label><input class="input" id="rec-name" value="${isEdit ? escapeHtml(recipe.name) : ''}"></div>
    <div class="form-group"><label>配料</label><textarea class="textarea" id="rec-ing" placeholder="番茄2个, 鸡蛋3个...">${isEdit ? escapeHtml(recipe.ingredients) : ''}</textarea></div>
    <div class="form-group"><label>步骤</label><textarea class="textarea" id="rec-steps" placeholder="1. ... 2. ..." style="min-height:120px">${isEdit ? escapeHtml(recipe.steps) : ''}</textarea></div>
    <div class="form-group"><label>图片链接</label><input class="input" id="rec-img" value="${isEdit ? escapeHtml(recipe.image_url) : ''}"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="rec-save">保存</button>
    </div>
  `);
  document.getElementById("rec-save").addEventListener("click", async function() {
    const name = document.getElementById("rec-name").value.trim();
    if (!name) return showToast("菜名不能为空", "error");
    const body = {
      name, ingredients: document.getElementById("rec-ing").value,
      steps: document.getElementById("rec-steps").value,
      image_url: document.getElementById("rec-img").value,
    };
    try {
      if (isEdit) { await api.put(`/api/notes/recipes/${recipe.id}`, body); }
      else { await api.post("/api/notes/recipes", body); }
      closeModal(); showToast("已保存"); loadRecipes();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.editRecipe = function(id) {
  const recipes = window._recipeData || [];
  const r = recipes.find(x => x.id === id);
  if (r) recipeForm(r);
};
window.delRecipe = async function(id) {
  if (!await confirmDialog("确定删除？")) return;
  await api.del(`/api/notes/recipes/${id}`);
  loadRecipes(); showToast("已删除");
};

// ─── 留言板 ─────────────────────────────────────────────

async function loadMessages() {
  const data = await api.get("/api/notes/messages");
  const div = document.getElementById("notes-content");
  let html = `<div class="flex-row gap-sm mb-md">
    <input class="input" id="msg-input" placeholder="说点什么..." style="flex:1">
    <button class="btn btn-primary btn-sm" id="msg-send">发送</button>
  </div><div class="card-list">`;
  if (data.messages.length === 0) html += `<div class="empty-state"><p>还没有留言</p></div>`;
  data.messages.forEach(m => {
    html += `<div class="card-list-item">
      <div class="flex-row gap-md mb-sm">
        ${avatarHtml(m.author_name, 'avatar-sm')}
        <div><strong>${m.author_name}</strong> <span class="text-sm text-secondary">${timeAgo(m.created_at)}</span></div>
      </div>
      <div>${m.content}</div>
      <div class="mt-sm flex-row gap-sm">
        <button class="btn btn-ghost btn-sm" onclick="replyMsg(${m.id},'${m.author_name}')">💬 回复 (${m.reply_count||0})</button>
      </div>`;
    (m.replies || []).forEach(r => {
      html += `<div class="ml-md mt-sm" style="margin-left:24px;padding:8px 12px;background:var(--input-bg);border-radius:10px">
        <strong>${r.author_name}</strong>: ${r.content}
        <span class="text-sm text-secondary"> · ${timeAgo(r.created_at)}</span>
      </div>`;
    });
    html += `</div>`;
  });
  html += `</div>`;
  div.innerHTML = html;

  document.getElementById("msg-send").addEventListener("click", async function() {
    const content = document.getElementById("msg-input").value.trim();
    if (!content) return;
    try {
      await api.post("/api/notes/messages", { content });
      document.getElementById("msg-input").value = "";
      loadMessages();
    } catch (err) { showToast(err.message, "error"); }
  });
}

window.replyMsg = function(parentId, author) {
  openModal(`
    <h2>回复 ${escapeHtml(author)}</h2>
    <textarea class="textarea" id="reply-content" placeholder="写下回复..." style="min-height:80px"></textarea>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="reply-save">回复</button>
    </div>
  `);
  document.getElementById("reply-save").addEventListener("click", async function() {
    const content = document.getElementById("reply-content").value.trim();
    if (!content) return;
    try {
      await api.post("/api/notes/messages", { content, parent_id: parentId });
      closeModal(); showToast("已回复"); loadMessages();
    } catch (err) { showToast(err.message, "error"); }
  });
};
