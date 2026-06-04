/* 简单哈希路由与模块加载器 */
const Router = {
  _currentHash: "",
  _pending: false,  // 导航锁，防止并发

  /** 动态加载 JS 文件 */
  async _loadScript(src) {
    if (document.querySelector(`script[data-module="${src}"]`)) {
      return;
    }
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.setAttribute("data-module", src);
      s.onload = () => resolve();
      s.onerror = () => reject(new Error("无法加载模块: " + src));
      document.head.appendChild(s);
    });
  },

  /** 导航到指定 hash */
  async navigate(hash) {
    if (!hash || hash === "#") hash = "#/feed";

    // 如果已经在目标页面，忽略
    if (hash === this._currentHash && this._currentHash !== "") return;

    // 如果正在导航中，排队等下次
    if (this._pending) {
      this._queuedHash = hash;
      return;
    }

    this._pending = true;
    this._currentHash = hash;

    // 递增页面版本号，旧页面的异步回调通过 pageGuard 检查后会自动丢弃
    window.__pageId = (window.__pageId || 0) + 1;

    // 更新导航高亮
    document.querySelectorAll(".nav-item, .tab-item").forEach(el => {
      el.classList.toggle("active", el.getAttribute("href") === hash || el.dataset.hash === hash);
    });

    const container = document.getElementById("page-content");
    if (!container) { this._pending = false; return; }

    container.innerHTML = '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:60vh"><div class="spinner"></div><p style="text-align:center;color:var(--text-secondary);margin-top:12px;font-family:var(--font)">正在加载...</p></div>';

    try {
      const moduleName = hash.replace("#/", "") || "feed";
      const moduleFile = `static/js/modules/${moduleName}.js`;

      await this._loadScript(moduleFile);

      const initFnName = "init_" + moduleName + "_page";
      if (typeof window[initFnName] === "function") {
        await window[initFnName]();
      } else {
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">?</div><p>模块尚未实现</p></div>';
      }
    } catch (err) {
      console.error("Router error:", err);
      container.innerHTML = '<div class="empty-state"><div class="empty-icon">!</div><p>加载失败: ' + err.message + '</p></div>';
    }

    this._pending = false;

    // 如果导航期间有新请求，处理它
    if (this._queuedHash && this._queuedHash !== this._currentHash) {
      const queued = this._queuedHash;
      this._queuedHash = null;
      this.navigate(queued);
    }
  },

  /** 启动路由监听 */
  start() {
    window.addEventListener("hashchange", () => {
      this.navigate(window.location.hash);
    });
    // 初始导航
    const initHash = window.location.hash || "#/feed";
    this.navigate(initHash);
  }
};
