/* 共享日历模块 */
let calYear, calMonth;

async function init_calendar_page() {
  const now = new Date();
  calYear = now.getFullYear();
  calMonth = now.getMonth() + 1;
  await loadCalendar();
}

async function loadCalendar() {
  const container = document.getElementById("page-content");
  container.innerHTML = `<div class="spinner"></div>`;
  try {
    const data = await api.get(`/api/calendar/events?year=${calYear}&month=${calMonth}`);
    renderCalendar(container, data.events || []);
  } catch (err) {
    if (err && err.aborted) return;
    container.innerHTML = '<div class="empty-state"><p>' + escapeHtml(err.message) + '</p></div>';
  }
}

function renderCalendar(container, events) {
  const monthNames = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"];
  const dayNames = ["日","一","二","三","四","五","六"];

  let html = `<div class="page-header flex-between">
    <div><h1>共享日历</h1><p class="text-secondary">${calYear}年${monthNames[calMonth-1]}</p></div>
    <div class="flex-row gap-sm">
      <button class="btn btn-ghost btn-sm" onclick="calPrevMonth()">◀</button>
      <button class="btn btn-secondary btn-sm" onclick="calGoToday()">今天</button>
      <button class="btn btn-ghost btn-sm" onclick="calNextMonth()">▶</button>
    </div>
  </div>`;

  // 月视图 (仅桌面端)
  html += `<div class="card mb-md calendar-desktop">`;
  html += `<div class="calendar-grid">`;
  dayNames.forEach(d => { html += `<div class="calendar-day-header">${d}</div>`; });

  // 计算日历格子
  const firstDay = new Date(calYear, calMonth - 1, 1).getDay();
  const daysInMonth = new Date(calYear, calMonth, 0).getDate();
  const daysInPrev = new Date(calYear, calMonth - 1, 0).getDate();
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;

  // 上月填充
  for (let i = firstDay - 1; i >= 0; i--) {
    html += `<div class="calendar-day other-month">${daysInPrev - i}</div>`;
  }
  // 本月
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${calYear}-${String(calMonth).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const isToday = dateStr === todayStr;
    const cls = isToday ? "today" : "";

    // 当天事件
    let dots = "";
    events.forEach(ev => {
      const evStart = new Date(ev.start).toISOString().slice(0, 10);
      if (evStart === dateStr) {
        dots += `<span class="event-dot" style="background:${escapeHtml(ev.color)}"></span>`;
      }
    });

    html += `<div class="calendar-day ${cls}" onclick="calDayClick('${dateStr}')">
      <div>${d}</div><div>${dots}</div>
    </div>`;
  }
  // 下月填充
  const remaining = 42 - firstDay - daysInMonth;
  for (let d = 1; d <= remaining; d++) {
    html += `<div class="calendar-day other-month">${d}</div>`;
  }
  html += `</div></div>`;

  // 新增事件按钮
  html += `<button class="btn btn-primary mb-md" onclick="calShowForm()">+ 新建事件</button>`;

  // 事件列表
  const sorted = [...events].sort((a,b) => new Date(a.start) - new Date(b.start));
  html += `<div class="card-list">`;
  if (sorted.length === 0) {
    html += `<div class="empty-state"><p>本月暂无事件</p></div>`;
  }
  sorted.forEach(ev => {
    html += `<div class="card-list-item flex-between">
      <div class="flex-row gap-md">
        <span class="color-dot" style="background:${escapeHtml(ev.color)}"></span>
        <div>
          <div style="font-weight:600">${escapeHtml(ev.title)}</div>
          <div class="text-sm text-secondary">${fmtDateTime(ev.start)} ${ev.location ? '· '+escapeHtml(ev.location) : ''}</div>
        </div>
      </div>
      <button class="btn btn-ghost btn-sm" data-del-event="${ev.id}">删除</button>
    </div>`;
  });
  html += `</div>`;

  container.innerHTML = html;

  container.querySelectorAll("[data-del-event]").forEach(btn => {
    btn.addEventListener("click", function() {
      calDelEvent(this.dataset.delEvent);
    });
  });
}

window.calPrevMonth = function() {
  if (calMonth === 1) { calYear--; calMonth = 12; }
  else { calMonth--; }
  loadCalendar();
};
window.calNextMonth = function() {
  if (calMonth === 12) { calYear++; calMonth = 1; }
  else { calMonth++; }
  loadCalendar();
};
window.calGoToday = function() {
  const now = new Date(); calYear = now.getFullYear(); calMonth = now.getMonth() + 1;
  loadCalendar();
};
window.calDayClick = function(dateStr) {
  calShowForm(dateStr);
};

window.calShowForm = function(defStart) {
  const startVal = defStart ? defStart + "T09:00" : "";
  openModal(`
    <h2>${defStart ? '新增事件' : '新建事件'}</h2>
    <div class="form-group"><label>标题</label><input class="input" id="ev-title" placeholder="事件标题"></div>
    <div class="form-group"><label>开始时间</label><input class="input" type="datetime-local" id="ev-start" value="${startVal}"></div>
    <div class="form-group"><label>结束时间</label><input class="input" type="datetime-local" id="ev-end"></div>
    <div class="form-group"><label>地点</label><input class="input" id="ev-loc" placeholder="事件地点"></div>
    <div class="form-group"><label>备注</label><textarea class="textarea" id="ev-desc" placeholder="备注"></textarea></div>
    <div class="form-group"><label>颜色</label>
      <select class="select" id="ev-color">
        <option value="#007aff">🔵 蓝色</option>
        <option value="#ff9500">🟠 橙色</option>
        <option value="#34c759">🟢 绿色</option>
        <option value="#ff3b30">🔴 红色</option>
        <option value="#5856d6">🟣 紫色</option>
      </select>
    </div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="ev-save">保存</button>
    </div>
  `);
  document.getElementById("ev-save").addEventListener("click", async function() {
    const title = document.getElementById("ev-title").value.trim();
    const start = document.getElementById("ev-start").value;
    const end = document.getElementById("ev-end").value;
    if (!title || !start || !end) return showToast("请填写必填项", "error");
    try {
      await api.post("/api/calendar/events", {
        title, start, end,
        location: document.getElementById("ev-loc").value,
        description: document.getElementById("ev-desc").value,
        color: document.getElementById("ev-color").value,
      });
      closeModal();
      showToast("事件已创建");
      loadCalendar();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.calDelEvent = async function(id) {
  if (!await confirmDialog("确定删除此事件？")) return;
  try {
    await api.del(`/api/calendar/events/${id}`);
    showToast("已删除");
    loadCalendar();
  } catch (err) { showToast(err.message, "error"); }
};
