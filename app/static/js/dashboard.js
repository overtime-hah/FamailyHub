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

  // 退出登录
  document.getElementById("btn-logout").addEventListener("click", function() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "/";
  });

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
