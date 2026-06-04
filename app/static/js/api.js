/* HTML 转义 — 防止 XSS */
function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = String(str);
  return div.innerHTML;
}

/* 封装 Fetch API，自动附加 JWT Token */
const api = {
  /** 获取存储的 token */
  _token() {
    return localStorage.getItem("access_token") || "";
  },

  /** 基础请求方法 — 页面切换后自动丢弃过期响应 */
  async _request(method, url, data = null) {
    const pageId = window.__pageId || 0;
    const headers = { "Authorization": "Bearer " + this._token() };
    const opts = { method, headers };

    if (data instanceof FormData) {
      opts.body = data;
    } else if (data !== null) {
      headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(data);
    }

    try {
      const res = await fetch(url, opts);

      // 页面已切换，丢弃此响应
      if (window.__pageId !== pageId) {
        throw { aborted: true };
      }

      if (res.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.hash = "";
        window.location.reload();
        throw new Error("登录已过期，请重新登录");
      }
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json.msg || "请求失败 (" + res.status + ")");
      }
      return json;
    } catch (err) {
      if (err && err.aborted) throw err;  // 静默丢弃，不打印
      if (err.message && err.message.includes("Failed to fetch")) {
        throw new Error("网络连接失败，请检查网络");
      }
      throw err;
    }
  },

  get(url)       { return this._request("GET", url); },
  post(url, data) { return this._request("POST", url, data); },
  put(url, data)  { return this._request("PUT", url, data); },
  del(url)        { return this._request("DELETE", url); },
};

/* Toast 提示 */
function showToast(msg, type = "success") {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.className = `toast toast-${type} show`;
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => { toast.classList.remove("show"); }, 2500);
}

/* Modal 辅助 */
function openModal(html) {
  let overlay = document.getElementById("modal-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "modal-overlay";
    overlay.className = "modal-overlay";
    overlay.addEventListener("click", function(e) {
      if (e.target === this) closeModal();
    });
    document.body.appendChild(overlay);
  }
  overlay.innerHTML = `<div class="modal">${html}</div>`;
  overlay.classList.add("active");
}

function closeModal() {
  const overlay = document.getElementById("modal-overlay");
  if (overlay) overlay.classList.remove("active");
}

/* 头像辅助 */
function avatarHtml(name, size = "") {
  const initial = (name || "?").charAt(0).toUpperCase();
  return `<span class="avatar ${size}">${initial}</span>`;
}

/* 格式化时间 */
function timeAgo(dt) {
  if (!dt) return "";
  const d = new Date(dt);
  const now = new Date();
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60) return "刚刚";
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}天前`;
  return d.toLocaleDateString("zh-CN");
}

/* 格式化日期 */
function fmtDate(d) { return d ? new Date(d).toLocaleDateString("zh-CN") : ""; }
function fmtDateTime(d) { return d ? new Date(d).toLocaleString("zh-CN") : ""; }

/* 确认弹窗 */
function confirmDialog(msg) {
  return new Promise((resolve) => {
    openModal(`
      <h2>确认操作</h2>
      <p style="color:var(--text-secondary)">${escapeHtml(msg)}</p>
      <div class="modal-actions">
        <button class="btn btn-secondary" id="confirmCancelBtn">取消</button>
        <button class="btn btn-danger" id="confirmOkBtn">确认</button>
      </div>
    `);
    document.getElementById("confirmOkBtn").addEventListener("click", () => {
      closeModal();
      resolve(true);
    });
    document.getElementById("confirmCancelBtn").addEventListener("click", () => {
      closeModal();
      resolve(false);
    });
  });
}

/* 全局未捕获异常处理 */
window.addEventListener("unhandledrejection", function(event) {
  console.error("Unhandled promise rejection:", event.reason);
  if (event.reason && event.reason.message && !event.reason.aborted) {
    showToast(event.reason.message, "error");
  }
});
