/* 登录页逻辑 */
document.addEventListener("DOMContentLoaded", function() {
  // 如果已登录，跳转到 /app
  if (localStorage.getItem("access_token")) {
    window.location.href = "/app";
    return;
  }

  const tabBtns = document.querySelectorAll(".auth-tab");
  const loginForm = document.getElementById("login-form");
  const regForm = document.getElementById("reg-form");
  const loginBtn = document.getElementById("login-btn");
  const regBtn = document.getElementById("reg-btn");
  const loginErr = document.getElementById("login-error");
  const regErr = document.getElementById("reg-error");

  // Tab 切换
  tabBtns.forEach(btn => {
    btn.addEventListener("click", function() {
      tabBtns.forEach(b => b.classList.remove("active"));
      this.classList.add("active");
      const tab = this.dataset.tab;
      if (tab === "login") { loginForm.style.display = "block"; regForm.style.display = "none"; }
      else { loginForm.style.display = "none"; regForm.style.display = "block"; }
      loginErr.textContent = "";
      regErr.textContent = "";
    });
  });

  // 登录
  loginBtn.addEventListener("click", async function() {
    loginErr.textContent = "";
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;
    if (!username || !password) { loginErr.textContent = "请输入用户名和密码"; return; }

    loginBtn.disabled = true; loginBtn.textContent = "登录中...";
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.msg || "登录失败");
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      window.location.href = "/app";
    } catch (err) {
      loginErr.textContent = err.message;
    } finally {
      loginBtn.disabled = false; loginBtn.textContent = "登录";
    }
  });

  // 注册
  regBtn.addEventListener("click", async function() {
    regErr.textContent = "";
    const username = document.getElementById("reg-username").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;
    const nickname = document.getElementById("reg-nickname").value.trim();
    const inviteCode = document.getElementById("reg-invite").value.trim();
    const familyName = document.getElementById("reg-family").value.trim();

    if (!username || !email || !password) { regErr.textContent = "请填写必填项"; return; }
    if (password.length < 6) { regErr.textContent = "密码至少6位"; return; }

    regBtn.disabled = true; regBtn.textContent = "注册中...";
    try {
      const body = { username, email, password, nickname: nickname || username };
      if (inviteCode) { body.invite_code = inviteCode; }
      else { body.family_name = familyName || undefined; }

      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.msg || "注册失败");
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      window.location.href = "/app";
    } catch (err) {
      regErr.textContent = err.message;
    } finally {
      regBtn.disabled = false; regBtn.textContent = "创建家庭";
    }
  });
});
