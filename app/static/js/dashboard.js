/* 主 SPA 导航逻辑 */
document.addEventListener("DOMContentLoaded", function() {
  // 检查登录状态
  const token = localStorage.getItem("access_token");
  const userStr = localStorage.getItem("user");
  if (!token || !userStr) {
    window.location.href = "/";
    return;
  }

  let user;
  try { user = JSON.parse(userStr); } catch(e) { user = null; }
  if (!user) { window.location.href = "/"; return; }

  // 渲染用户信息
  document.getElementById("user-name").textContent = user.nickname || user.username;
  const roleMap = { admin: "管理员", adult: "成人", child: "儿童" };
  document.getElementById("user-role").textContent = roleMap[user.role] || "成员";

  // 根据角色隐藏敏感菜单项
  if (user.role === "child") {
    document.querySelectorAll(".nav-item-sensitive").forEach(el => el.style.display = "none");
    document.querySelectorAll(".tab-item-sensitive").forEach(el => el.style.display = "none");
  }

  // 侧边栏导航点击
  document.querySelectorAll(".nav-item[data-hash]").forEach(item => {
    item.addEventListener("click", function(e) {
      e.preventDefault();
      const hash = this.dataset.hash;
      if (window.location.hash === hash) {
        // 同页面重复点击也强制刷新
        Router.navigate(hash);
      } else {
        window.location.hash = hash;
      }
    });
  });

  // 底部 TabBar 导航点击
  document.querySelectorAll(".tab-item[data-hash]").forEach(item => {
    item.addEventListener("click", function(e) {
      e.preventDefault();
      const hash = this.dataset.hash;
      if (window.location.hash === hash) {
        Router.navigate(hash);
      } else {
        window.location.hash = hash;
      }
    });
  });

  // 退出登录（桌面侧边栏 + 移动端 TabBar）
  function doLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "/";
  }
  document.getElementById("btn-logout").addEventListener("click", doLogout);
  var btnLogoutMobile = document.getElementById("btn-logout-mobile");
  if (btnLogoutMobile) {
    btnLogoutMobile.addEventListener("click", function(e) {
      e.preventDefault();
      doLogout();
    });
  }

  // ── 10 分钟无操作自动退出 ──────────────────────
  var IDLE_TIMEOUT = 10 * 60 * 1000; // 10 分钟
  var idleTimer = null;

  function resetIdleTimer() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function() {
      // 清除登录状态并跳转
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      alert("您已超过 10 分钟未操作，请重新登录");
      window.location.href = "/";
    }, IDLE_TIMEOUT);
  }

  // 监听用户操作事件
  ["mousedown", "mousemove", "keydown", "scroll", "touchstart", "click"].forEach(function(evt) {
    document.addEventListener(evt, resetIdleTimer, { passive: true });
  });
  resetIdleTimer(); // 初始化计时器

  // Lightbox 点击关闭
  const lightbox = document.getElementById("lightbox");
  if (lightbox) {
    lightbox.addEventListener("click", function(e) {
      if (e.target === this || e.target.tagName === "IMG") {
        this.classList.remove("active");
      }
    });
  }

  // 启动路由
  Router.start();

  // 请求通知权限
  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }
});
