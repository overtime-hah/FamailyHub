/* 健康与宠物模块 */
let healthTab = "records"; // records / pets

async function init_health_page() {
  healthTab = "records";
  await loadHealthTab();
}

async function loadHealthTab() {
  const container = document.getElementById("page-content");
  const tabs = [
    { key: "records", label: "🏥 健康档案" },
    { key: "pets", label: "🐾 宠物管理" },
  ];
  let header = `<div class="page-header"><h1>健康与宠物</h1></div>
  <div class="flex-row gap-sm mb-md">`;
  tabs.forEach(t => {
    const cls = healthTab === t.key ? "btn-primary" : "btn-secondary";
    header += `<button class="btn btn-sm ${cls}" onclick="switchHealthTab('${t.key}')">${t.label}</button>`;
  });
  header += `</div><div id="health-content"><div class="spinner"></div></div>`;
  container.innerHTML = header;

  try {
    if (healthTab === "records") await loadRecords();
    else await loadPets();
  } catch (err) {
    if (err && err.aborted) return;
    document.getElementById("health-content").innerHTML = '<div class="empty-state"><p>' + escapeHtml(err.message) + '</p></div>';
  }
}

window.switchHealthTab = async function(key) {
  healthTab = key;
  await loadHealthTab();
};

// ─── 健康档案 ───────────────────────────────────────────

async function loadRecords() {
  const data = await api.get("/api/health/records");
  const div = document.getElementById("health-content");
  let html = `<button class="btn btn-primary btn-sm mb-md" onclick="healthForm()">+ 添加记录</button><div class="card-list">`;
  if (data.records.length === 0) html += `<div class="empty-state"><p>暂无健康记录</p></div>`;
  data.records.forEach(r => {
    html += `<div class="card-list-item flex-between">
      <div class="flex-row gap-md">
        <span class="badge badge-blue">${escapeHtml(r.record_type)}</span>
        <div>
          <div style="font-weight:600">${escapeHtml(r.value)} ${escapeHtml(r.unit)}</div>
          <div class="text-sm text-secondary">${escapeHtml(r.username)} · ${fmtDate(r.record_date)}</div>
          ${r.note ? `<div class="text-sm mt-sm">${escapeHtml(r.note)}</div>` : ''}
        </div>
      </div>
      <div class="flex-row gap-sm">
        <button class="btn btn-ghost btn-sm" onclick="editHealth(${r.id})">编辑</button>
        <button class="btn btn-ghost btn-sm" onclick="delHealth(${r.id})">删除</button>
      </div>
    </div>`;
  });
  html += `</div>`;
  div.innerHTML = html;
  window._healthData = data.records;
}

window.healthForm = async function(record) {
  const isEdit = !!record;
  const familyData = await api.get("/api/family/info");
  const members = familyData.members || [];
  const opts = members.map(m => {
    const name = (m.user && m.user.nickname) || m.user.username || "未知";
    const sel = record && record.user_id === m.user_id ? "selected" : "";
    return `<option value="${m.user_id}" ${sel}>${escapeHtml(name)}</option>`;
  }).join("");

  openModal(`
    <h2>${isEdit ? '编辑记录' : '添加健康记录'}</h2>
    <div class="form-group"><label>成员</label><select class="select" id="hr-user">${opts}</select></div>
    <div class="form-group"><label>记录类型</label><select class="select" id="hr-type"><option>height</option><option>weight</option><option>blood_pressure</option><option>vaccine</option><option>other</option></select></div>
    <div class="form-group"><label>数值</label><input class="input" id="hr-value" value="${isEdit ? escapeHtml(record.value) : ''}" placeholder="如：175"></div>
    <div class="form-group"><label>单位</label><input class="input" id="hr-unit" value="${isEdit ? escapeHtml(record.unit) : ''}" placeholder="cm, kg, mmHg..."></div>
    <div class="form-group"><label>日期</label><input class="input" type="date" id="hr-date" value="${isEdit ? record.record_date : new Date().toISOString().slice(0,10)}"></div>
    <div class="form-group"><label>备注</label><input class="input" id="hr-note" value="${isEdit ? escapeHtml(record.note || '') : ''}"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="hr-save">保存</button>
    </div>
  `);
  document.getElementById("hr-save").addEventListener("click", async function() {
    const value = document.getElementById("hr-value").value.trim();
    if (!value) return showToast("数值不能为空", "error");
    const body = {
      user_id: parseInt(document.getElementById("hr-user").value),
      record_type: document.getElementById("hr-type").value,
      value, unit: document.getElementById("hr-unit").value,
      record_date: document.getElementById("hr-date").value,
      note: document.getElementById("hr-note").value,
    };
    try {
      if (isEdit) { await api.put(`/api/health/records/${record.id}`, body); }
      else { await api.post("/api/health/records", body); }
      closeModal(); showToast("已保存"); loadRecords();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.editHealth = function(id) {
  const records = window._healthData || [];
  const r = records.find(x => x.id === id);
  if (r) healthForm(r);
};
window.delHealth = async function(id) {
  try {
    await api.del(`/api/health/records/${id}`);
    loadRecords(); showToast("已删除");
  } catch (err) { showToast(err.message, "error"); }
};

// ─── 宠物管理 ───────────────────────────────────────────

async function loadPets() {
  const data = await api.get("/api/health/pets");
  const div = document.getElementById("health-content");
  let html = `<button class="btn btn-primary btn-sm mb-md" onclick="petForm()">+ 添加宠物</button><div class="grid-2">`;
  if (data.pets.length === 0) html += `<div class="empty-state"><p>还没有宠物</p></div>`;
  data.pets.forEach(p => {
    const dewSoon = p.deworming_soon ? '<span class="badge badge-orange">驱虫即将到期</span>' : '';
    const vacSoon = p.vaccine_soon ? '<span class="badge badge-red">疫苗即将到期</span>' : '';
    html += `<div class="card">
      <div style="font-size:40px;text-align:center">🐾</div>
      <div style="font-weight:600;font-size:16px">${escapeHtml(p.name)}</div>
      <div class="text-sm text-secondary">${escapeHtml(p.species || '未知品种')}</div>
      <div class="text-sm mt-sm">驱虫: ${p.deworming_date ? fmtDate(p.deworming_date) : '未设置'} ${dewSoon}</div>
      <div class="text-sm">疫苗: ${p.vaccine_date ? fmtDate(p.vaccine_date) : '未设置'} ${vacSoon}</div>
      ${p.note ? `<div class="text-sm text-secondary mt-sm">${escapeHtml(p.note)}</div>` : ''}
      <div class="flex-row gap-sm mt-sm">
        <button class="btn btn-ghost btn-sm" onclick="editPet(${p.id})">编辑</button>
        <button class="btn btn-ghost btn-sm" onclick="delPet(${p.id})">删除</button>
      </div>
    </div>`;
  });
  html += `</div>`;
  div.innerHTML = html;
  window._petData = data.pets;
}

window.petForm = function(pet) {
  const isEdit = !!pet;
  openModal(`
    <h2>${isEdit ? '编辑宠物' : '添加宠物'}</h2>
    <div class="form-group"><label>名字</label><input class="input" id="pet-name" value="${isEdit ? escapeHtml(pet.name) : ''}"></div>
    <div class="form-group"><label>品种</label><input class="input" id="pet-species" value="${isEdit ? escapeHtml(pet.species || '') : ''}" placeholder="英短, 金毛..."></div>
    <div class="form-group"><label>驱虫日期</label><input class="input" type="date" id="pet-deworm" value="${isEdit ? pet.deworming_date||'' : ''}"></div>
    <div class="form-group"><label>疫苗日期</label><input class="input" type="date" id="pet-vaccine" value="${isEdit ? pet.vaccine_date||'' : ''}"></div>
    <div class="form-group"><label>备注</label><input class="input" id="pet-note" value="${isEdit ? escapeHtml(pet.note || '') : ''}"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="pet-save">保存</button>
    </div>
  `);
  document.getElementById("pet-save").addEventListener("click", async function() {
    const name = document.getElementById("pet-name").value.trim();
    if (!name) return showToast("名字不能为空", "error");
    const body = {
      name, species: document.getElementById("pet-species").value,
      deworming_date: document.getElementById("pet-deworm").value || null,
      vaccine_date: document.getElementById("pet-vaccine").value || null,
      note: document.getElementById("pet-note").value,
    };
    try {
      if (isEdit) { await api.put(`/api/health/pets/${pet.id}`, body); }
      else { await api.post("/api/health/pets", body); }
      closeModal(); showToast("已保存"); loadPets();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.editPet = function(id) {
  const pets = window._petData || [];
  const p = pets.find(x => x.id === id);
  if (p) petForm(p);
};
window.delPet = async function(id) {
  if (!await confirmDialog("确定删除？")) return;
  try {
    await api.del(`/api/health/pets/${id}`);
    loadPets(); showToast("已删除");
  } catch (err) { showToast(err.message, "error"); }
};
