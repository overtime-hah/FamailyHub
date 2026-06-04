/* 动态流模块 */
async function init_feed_page() {
  const container = document.getElementById("page-content");
  container.innerHTML = `<div class="spinner"></div>`;
  try {
    const data = await api.get("/api/feed/list");
    renderFeed(container, data);
  } catch (err) {
    if (err && err.aborted) return;
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">!</div><p>' + err.message + '</p></div>';
  }
}

function renderFeed(container, data) {
  let html = `<div class="page-header"><h1>家庭动态</h1><p>记录每一个重要时刻</p></div>`;

  // 即将到来的生日
  if (data.upcoming_birthdays && data.upcoming_birthdays.length > 0) {
    html += `<div class="card mb-md" style="border-left:4px solid var(--orange)">`;
    html += `<div style="font-weight:600;font-size:15px;margin-bottom:8px">🎂 即将到来的生日</div>`;
    data.upcoming_birthdays.forEach(b => {
      const label = b.days_left === 0 ? "今天" : b.days_left === 1 ? "明天" : `${b.days_left}天后`;
      html += `<div class="flex-row" style="justify-content:space-between;padding:4px 0">
        <span>${avatarHtml(b.username,'avatar-sm')} <strong>${escapeHtml(b.username)}</strong></span>
        <span class="badge badge-orange">${label} · ${fmtDate(b.birthday)}</span>
      </div>`;
    });
    html += `</div>`;
  }

  // 公告输入（仅管理员）
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  if (user.role === "admin") {
    html += `<div class="card mb-md"><div class="flex-row gap-sm">
      <input class="input" id="announce-input" placeholder="发布一条公告..." style="flex:1">
      <button class="btn btn-primary btn-sm" id="announce-btn">发布</button>
    </div></div>`;
  }

  // 动态时间线
  html += `<div class="card"><div class="timeline">`;
  if (data.feeds && data.feeds.length > 0) {
    data.feeds.forEach(f => {
      const dotClass = f.is_pinned ? "timeline-dot pinned" : "timeline-dot";
      const badge = f.is_pinned ? ' <span class="badge badge-orange">置顶</span>' : '';
      html += `<div class="timeline-item">
        <div class="${dotClass}"></div>
        <div class="timeline-time">${timeAgo(f.created_at)}${badge}</div>
        <div style="font-size:14px">
          <strong>${escapeHtml(f.username)}</strong> ${escapeHtml(f.content)}
        </div>
      </div>`;
    });
  } else {
    html += `<div class="empty-state"><div class="empty-icon">📭</div><p>还没有动态</p></div>`;
  }
  html += `</div></div>`;

  container.innerHTML = html;

  // 公告发布
  const announceBtn = document.getElementById("announce-btn");
  if (announceBtn) {
    announceBtn.addEventListener("click", async function() {
      const input = document.getElementById("announce-input");
      const content = input.value.trim();
      if (!content) return showToast("请输入内容", "error");
      try {
        await api.post("/api/feed/announcement", { content });
        input.value = "";
        showToast("公告已发布");
        init_feed_page();
      } catch (err) { showToast(err.message, "error"); }
    });
  }
}
