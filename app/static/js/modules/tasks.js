/* 清单与任务模块：购物清单、家务待办、心愿单 */
let tasksTab = "shopping"; // shopping / chores / wishes

async function init_tasks_page() {
  tasksTab = "shopping";
  await loadTasksTab();
}

async function loadTasksTab() {
  const container = document.getElementById("page-content");
  container.innerHTML = `<div class="spinner"></div>`;

  const tabs = [
    { key: "shopping", label: "🛒 购物清单" },
    { key: "chores", label: "📋 家务待办" },
    { key: "wishes", label: "🎁 心愿单" },
  ];

  let header = `<div class="page-header"><h1>清单与任务</h1></div>
  <div class="flex-row gap-sm mb-md">`;
  tabs.forEach(t => {
    const cls = tasksTab === t.key ? "btn-primary" : "btn-secondary";
    header += `<button class="btn btn-sm ${cls}" onclick="switchTasksTab('${t.key}')">${t.label}</button>`;
  });
  header += `</div><div id="tasks-content"><div class="spinner"></div></div>`;
  container.innerHTML = header;

  try {
    if (tasksTab === "shopping") await loadShopping();
    else if (tasksTab === "chores") await loadChores();
    else await loadWishes();
  } catch (err) {
    if (err && err.aborted) return;
    document.getElementById("tasks-content").innerHTML = '<div class="empty-state"><p>' + err.message + '</p></div>';
  }
}

window.switchTasksTab = async function(key) {
  tasksTab = key;
  await loadTasksTab();
};

// ─── 购物清单 ───────────────────────────────────────────

async function loadShopping() {
  const data = await api.get("/api/tasks/shopping");
  const div = document.getElementById("tasks-content");
  let html = `<div class="flex-row gap-sm mb-md">
    <input class="input" id="shop-name" placeholder="添加物品..." style="flex:1">
    <input class="input" id="shop-qty" placeholder="数量" style="width:80px">
    <button class="btn btn-primary btn-sm" id="shop-add">添加</button>
  </div><div class="card-list">`;

  if (data.items.length === 0) html += `<div class="empty-state"><p>购物清单为空</p></div>`;
  data.items.forEach(item => {
    const checked = item.bought ? "checked" : "";
    const strike = item.bought ? 'style="text-decoration:line-through;opacity:0.6"' : "";
    html += `<div class="card-list-item flex-row gap-md">
      <label class="checkbox-wrap"><input type="checkbox" ${checked} onchange="toggleShop(${item.id},this.checked)"><span class="checkbox-custom"></span></label>
      <div style="flex:1" ${strike}>${escapeHtml(item.name)} <span class="text-secondary text-sm">x${escapeHtml(item.quantity)}</span></div>
      <button class="btn btn-ghost btn-sm" onclick="delShop(${item.id})">删除</button>
    </div>`;
  });
  html += `</div>`;
  div.innerHTML = html;

  document.getElementById("shop-add").addEventListener("click", async function() {
    const name = document.getElementById("shop-name").value.trim();
    const qty = document.getElementById("shop-qty").value.trim() || "1";
    if (!name) return showToast("请输入物品名", "error");
    try {
      await api.post("/api/tasks/shopping", { name, quantity: qty });
      document.getElementById("shop-name").value = "";
      document.getElementById("shop-qty").value = "";
      loadShopping();
    } catch (err) { showToast(err.message, "error"); }
  });
}

window.toggleShop = async function(id, bought) {
  try {
    await api.put(`/api/tasks/shopping/${id}`, { bought });
  } catch (err) { showToast(err.message, "error"); }
};
window.delShop = async function(id) {
  try {
    await api.del(`/api/tasks/shopping/${id}`);
    loadShopping();
    showToast("已删除");
  } catch (err) { showToast(err.message, "error"); }
};

// ─── 家务待办 ───────────────────────────────────────────

async function loadChores() {
  const data = await api.get("/api/tasks/chores");
  const familyData = await api.get("/api/family/info");
  const members = familyData.members || [];
  const div = document.getElementById("tasks-content");

  let html = `<button class="btn btn-primary btn-sm mb-md" onclick="choreForm()">+ 新建待办</button><div class="card-list">`;
  if (data.tasks.length === 0) html += `<div class="empty-state"><p>暂无待办</p></div>`;
  data.tasks.forEach(t => {
    const checked = t.completed ? "checked" : "";
    const strike = t.completed ? 'style="text-decoration:line-through;opacity:0.6"' : "";
    html += `<div class="card-list-item flex-row gap-md">
      <label class="checkbox-wrap"><input type="checkbox" ${checked} onchange="toggleChore(${t.id},this.checked)"><span class="checkbox-custom"></span></label>
      <div style="flex:1" ${strike}>
        <div style="font-weight:600">${escapeHtml(t.title)}</div>
        <div class="text-sm text-secondary">${escapeHtml(t.assignee_name)} · ${t.due_date ? '截止 '+fmtDate(t.due_date) : '无截止'}</div>
      </div>
      <button class="btn btn-ghost btn-sm" onclick="delChore(${t.id})">删除</button>
    </div>`;
  });
  html += `</div>`;
  div.innerHTML = html;
}

window.toggleChore = async function(id, completed) {
  try {
    await api.put(`/api/tasks/chores/${id}`, { completed });
  } catch (err) { showToast(err.message, "error"); }
};
window.delChore = async function(id) {
  try {
    await api.del(`/api/tasks/chores/${id}`);
    loadChores(); showToast("已删除");
  } catch (err) { showToast(err.message, "error"); }
};

window.choreForm = async function() {
  const familyData = await api.get("/api/family/info");
  const members = familyData.members || [];
  const opts = members.map(m => {
    const name = (m.user && m.user.nickname) || m.user.username || "未知";
    return `<option value="${m.user_id}">${escapeHtml(name)}</option>`;
  }).join("");

  openModal(`
    <h2>新建待办</h2>
    <div class="form-group"><label>标题</label><input class="input" id="chore-title" placeholder="待办事项"></div>
    <div class="form-group"><label>指派给</label><select class="select" id="chore-assign">${opts}</select></div>
    <div class="form-group"><label>截止日期</label><input class="input" type="date" id="chore-due"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="chore-save">保存</button>
    </div>
  `);
  document.getElementById("chore-save").addEventListener("click", async function() {
    const title = document.getElementById("chore-title").value.trim();
    if (!title) return showToast("标题不能为空", "error");
    try {
      await api.post("/api/tasks/chores", {
        title,
        assignee_id: parseInt(document.getElementById("chore-assign").value),
        due_date: document.getElementById("chore-due").value || null,
      });
      closeModal(); showToast("待办已创建"); loadChores();
    } catch (err) { showToast(err.message, "error"); }
  });
};

// ─── 心愿单 ─────────────────────────────────────────────

async function loadWishes() {
  const data = await api.get("/api/tasks/wishes");
  const div = document.getElementById("tasks-content");
  let html = `<button class="btn btn-primary btn-sm mb-md" onclick="wishForm()">+ 添加心愿</button><div class="card-list">`;
  if (data.wishes.length === 0) html += `<div class="empty-state"><p>还没有心愿</p></div>`;
  data.wishes.forEach(w => {
    const meId = JSON.parse(localStorage.getItem("user") || "{}").id;
    const canEdit = w.user_id === meId;
    html += `<div class="card-list-item">
      <div class="flex-between mb-sm">
        <div><strong>${escapeHtml(w.name)}</strong> <span class="text-secondary text-sm">— ${escapeHtml(w.username)}</span></div>
        ${canEdit ? `<div class="flex-row gap-sm"><button class="btn btn-ghost btn-sm" onclick="delWish(${w.id})">删除</button></div>` : ''}
      </div>
      ${w.note ? `<div class="text-sm text-secondary">${escapeHtml(w.note)}</div>` : ''}
      ${w.link ? `<a href="${escapeHtml(w.link)}" target="_blank" class="text-sm" style="color:var(--blue)">🔗 链接</a>` : ''}
    </div>`;
  });
  html += `</div>`;
  div.innerHTML = html;
}

window.wishForm = function() {
  openModal(`
    <h2>添加心愿</h2>
    <div class="form-group"><label>名称</label><input class="input" id="wish-name" placeholder="想要什么"></div>
    <div class="form-group"><label>链接</label><input class="input" id="wish-link" placeholder="购买链接 (可选)"></div>
    <div class="form-group"><label>备注</label><textarea class="textarea" id="wish-note" placeholder="补充说明 (可选)"></textarea></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="wish-save">保存</button>
    </div>
  `);
  document.getElementById("wish-save").addEventListener("click", async function() {
    const name = document.getElementById("wish-name").value.trim();
    if (!name) return showToast("名称不能为空", "error");
    try {
      await api.post("/api/tasks/wishes", {
        name, link: document.getElementById("wish-link").value,
        note: document.getElementById("wish-note").value,
      });
      closeModal(); showToast("心愿已添加"); loadWishes();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.delWish = async function(id) {
  try {
    await api.del(`/api/tasks/wishes/${id}`);
    loadWishes(); showToast("已删除");
  } catch (err) { showToast(err.message, "error"); }
};
