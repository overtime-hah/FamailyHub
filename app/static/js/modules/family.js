/* 家庭管理模块 */
async function init_family_page() {
  const container = document.getElementById("page-content");
  container.innerHTML = '<div class="spinner"></div>';
  try {
    const data = await api.get("/api/family/info");
    renderFamily(container, data);
  } catch (err) {
    if (err && err.aborted) return;
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">!</div><p>' + escapeHtml(err.message) + '</p></div>';
  }
}

function renderFamily(container, data) {
  const family = data.family || {};
  const members = data.members || [];
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const roleMap = { admin: "管理员", adult: "成人", child: "儿童" };

  let html = '<div class="page-header"><h1>家庭管理</h1><p>' + escapeHtml(family.name) + '</p></div>';

  // 邀请码（仅管理员可见）
  if (user.role === "admin") {
    html += '<div class="card mb-md">';
    html += '<div class="flex-between">';
    html += '<div><div style="font-weight:600;font-size:16px">邀请码</div><div class="text-sm text-secondary mt-sm">分享此码给家人加入</div></div>';
    html += '<div class="flex-row gap-sm">';
    html += '<span style="font-size:24px;font-weight:700;letter-spacing:4px;font-family:monospace">' + escapeHtml(family.invite_code || "") + '</span>';
    html += '<button class="btn btn-secondary btn-sm" id="copy-invite">复制</button>';
    html += '<button class="btn btn-ghost btn-sm" id="regen-invite">刷新</button>';
    html += '</div></div></div>';
  }

  // 成员列表
  html += '<div class="card"><div style="font-weight:600;font-size:16px;margin-bottom:12px">家庭成员 (' + members.length + ')</div>';
  members.forEach(function(m) {
    const u = m.user || {};
    const name = u.nickname || u.username || "未知";
    const isMe = u.id === user.id;
    html += '<div class="list-item flex-between">';
    html += '<div class="flex-row gap-md">';
    html += avatarHtml(name, "avatar-sm");
    html += '<div>';
    html += '<div><strong>' + escapeHtml(name) + '</strong> <span class="text-sm text-secondary">@' + escapeHtml(u.username || "") + '</span>' + (isMe ? ' <span class="badge badge-blue">我</span>' : "") + '</div>';
    html += '<div class="text-sm text-secondary">' + escapeHtml(u.email || "") + ' · ' + (roleMap[m.role] || m.role) + ' · 加入于 ' + fmtDate(m.joined_at) + '</div>';
    html += '</div></div>';

    // 管理员操作 (非本人)
    if (user.role === "admin" && !isMe) {
      html += '<div class="flex-row gap-sm">';
      html += '<select class="select" style="width:auto;padding:4px 8px;font-size:12px" data-role-member="' + m.id + '">';
      html += '<option value="admin" ' + (m.role === "admin" ? "selected" : "") + '>管理员</option>';
      html += '<option value="adult" ' + (m.role === "adult" ? "selected" : "") + '>成人</option>';
      html += '<option value="child" ' + (m.role === "child" ? "selected" : "") + '>儿童</option>';
      html += '</select>';
      html += '<button class="btn btn-ghost btn-sm" data-edit-member="' + m.id + '">编辑</button>';
      html += '<button class="btn btn-ghost btn-sm" data-reset-pwd="' + m.id + '" data-member-name="' + escapeHtml(name) + '">改密</button>';
      html += '<button class="btn btn-ghost btn-sm" data-remove-member="' + m.id + '" data-member-name="' + escapeHtml(name) + '">移出</button>';
      html += '</div>';
    }
    html += '</div>';
  });
  html += '</div>';

  // 个人信息修改
  html += '<div class="card mt-md"><div style="font-weight:600;font-size:16px;margin-bottom:12px">我的信息</div>';
  html += '<div class="form-group"><label>昵称</label><input class="input" id="prof-nickname" value="' + escapeHtml(user.nickname || "") + '"></div>';
  html += '<div class="form-group"><label>生日</label><input class="input" type="date" id="prof-birthday" value="' + escapeHtml(user.birthday || "") + '"></div>';
  html += '<div class="form-group"><label>头像 URL</label><input class="input" id="prof-avatar" value="' + escapeHtml(user.avatar_url || "") + '"></div>';
  html += '<button class="btn btn-primary btn-sm" id="prof-save">更新信息</button>';
  html += '</div>';

  // 修改密码
  html += '<div class="card mt-md"><div style="font-weight:600;font-size:16px;margin-bottom:12px">修改密码</div>';
  html += '<div class="form-group"><label>旧密码</label><input class="input" type="password" id="pwd-old" placeholder="输入当前密码"></div>';
  html += '<div class="form-group"><label>新密码</label><input class="input" type="password" id="pwd-new" placeholder="至少6位"></div>';
  html += '<button class="btn btn-primary btn-sm" id="pwd-save">修改密码</button>';
  html += '</div>';

  // 退出家庭
  html += '<div class="card mt-md" style="border:1px solid var(--red)">';
  html += '<div style="font-weight:600;color:var(--red);margin-bottom:8px">危险操作</div>';
  html += '<button class="btn btn-danger btn-sm" id="leave-family">退出家庭</button>';
  html += '</div>';

  container.innerHTML = html;

  // --- 事件绑定 ---

  // 复制邀请码
  const copyBtn = document.getElementById("copy-invite");
  if (copyBtn) {
    copyBtn.addEventListener("click", function() {
      navigator.clipboard.writeText(family.invite_code).then(function() { showToast("已复制"); });
    });
  }
  // 刷新邀请码
  const regenBtn = document.getElementById("regen-invite");
  if (regenBtn) {
    regenBtn.addEventListener("click", async function() {
      try { await api.post("/api/family/invite-code", {}); showToast("邀请码已刷新"); init_family_page(); }
      catch (err) { showToast(err.message, "error"); }
    });
  }

  // 角色变更
  container.querySelectorAll("[data-role-member]").forEach(function(sel) {
    sel.addEventListener("change", async function() {
      try {
        await api.put("/api/family/members/" + this.dataset.roleMember + "/role", { role: this.value });
        showToast("角色已更新"); init_family_page();
      } catch (err) { showToast(err.message, "error"); }
    });
  });

  // 编辑成员
  container.querySelectorAll("[data-edit-member]").forEach(function(btn) {
    btn.addEventListener("click", function() { editMember(parseInt(this.dataset.editMember)); });
  });

  // 重置密码
  container.querySelectorAll("[data-reset-pwd]").forEach(function(btn) {
    btn.addEventListener("click", function() { resetMemberPwd(parseInt(this.dataset.resetPwd), this.dataset.memberName); });
  });

  // 移出成员
  container.querySelectorAll("[data-remove-member]").forEach(function(btn) {
    btn.addEventListener("click", async function() {
      const mid = parseInt(this.dataset.removeMember);
      const mname = this.dataset.memberName;
      if (!await confirmDialog("确定将 " + mname + " 移出家庭？")) return;
      try {
        await api.del("/api/family/members/" + mid);
        showToast("已移出"); init_family_page();
      } catch (err) { showToast(err.message, "error"); }
    });
  });

  // 更新个人信息
  document.getElementById("prof-save").addEventListener("click", async function() {
    try {
      const body = {
        nickname: document.getElementById("prof-nickname").value.trim(),
        birthday: document.getElementById("prof-birthday").value || null,
        avatar_url: document.getElementById("prof-avatar").value.trim(),
      };
      await api.put("/api/family/profile", body);
      const u = JSON.parse(localStorage.getItem("user") || "{}");
      u.nickname = body.nickname || u.username;
      u.birthday = body.birthday;
      u.avatar_url = body.avatar_url;
      localStorage.setItem("user", JSON.stringify(u));
      const nameEl = document.getElementById("user-name");
      if (nameEl) nameEl.textContent = u.nickname;
      showToast("信息已更新");
    } catch (err) { showToast(err.message, "error"); }
  });

  // 修改密码
  document.getElementById("pwd-save").addEventListener("click", async function() {
    const oldPwd = document.getElementById("pwd-old").value;
    const newPwd = document.getElementById("pwd-new").value;
    if (!oldPwd || !newPwd) return showToast("请填写旧密码和新密码", "error");
    if (newPwd.length < 6) return showToast("新密码至少6位", "error");
    try {
      await api.put("/api/auth/password", { old_password: oldPwd, new_password: newPwd });
      document.getElementById("pwd-old").value = "";
      document.getElementById("pwd-new").value = "";
      showToast("密码已修改");
    } catch (err) { showToast(err.message, "error"); }
  });

  // 退出家庭
  document.getElementById("leave-family").addEventListener("click", async function() {
    if (!await confirmDialog("确定退出家庭？此操作不可撤销！")) return;
    try {
      await api.post("/api/family/leave");
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/";
    } catch (err) { showToast(err.message, "error"); }
  });

  // 保存成员数据供编辑使用
  window._familyData = data;
}

// --- 管理员操作：修改成员信息 ---

function editMember(memberId) {
  const data = window._familyData;
  if (!data) return;
  let fm = null;
  data.members.forEach(function(m) { if (m.id === memberId) fm = m; });
  if (!fm || !fm.user) return;
  const u = fm.user;

  openModal(
    '<h2>编辑成员信息</h2>' +
    '<div class="form-group"><label>昵称</label><input class="input" id="em-nickname" value="' + escapeHtml(u.nickname || "") + '"></div>' +
    '<div class="form-group"><label>邮箱</label><input class="input" type="email" id="em-email" value="' + escapeHtml(u.email || "") + '"></div>' +
    '<div class="form-group"><label>生日</label><input class="input" type="date" id="em-birthday" value="' + escapeHtml(u.birthday || "") + '"></div>' +
    '<div class="form-group"><label>头像 URL</label><input class="input" id="em-avatar" value="' + escapeHtml(u.avatar_url || "") + '"></div>' +
    '<div class="modal-actions">' +
    '<button class="btn btn-secondary" id="em-cancel">取消</button>' +
    '<button class="btn btn-primary" id="em-save">保存</button>' +
    '</div>'
  );
  document.getElementById("em-cancel").addEventListener("click", closeModal);
  document.getElementById("em-save").addEventListener("click", async function() {
    try {
      await api.put("/api/family/members/" + memberId + "/profile", {
        nickname: document.getElementById("em-nickname").value.trim(),
        email: document.getElementById("em-email").value.trim(),
        birthday: document.getElementById("em-birthday").value || null,
        avatar_url: document.getElementById("em-avatar").value.trim(),
      });
      closeModal(); showToast("成员信息已更新"); init_family_page();
    } catch (err) { showToast(err.message, "error"); }
  });
}

function resetMemberPwd(memberId, name) {
  openModal(
    '<h2>重置 ' + escapeHtml(name) + ' 的密码</h2>' +
    '<div class="form-group"><label>新密码</label><input class="input" type="password" id="rp-new" placeholder="至少6位"></div>' +
    '<div class="form-group"><label>确认密码</label><input class="input" type="password" id="rp-confirm" placeholder="再次输入"></div>' +
    '<div class="modal-actions">' +
    '<button class="btn btn-secondary" id="rp-cancel">取消</button>' +
    '<button class="btn btn-primary" id="rp-save">重置</button>' +
    '</div>'
  );
  document.getElementById("rp-cancel").addEventListener("click", closeModal);
  document.getElementById("rp-save").addEventListener("click", async function() {
    const p1 = document.getElementById("rp-new").value;
    const p2 = document.getElementById("rp-confirm").value;
    if (!p1 || !p2) return showToast("请填写密码", "error");
    if (p1 !== p2) return showToast("两次密码不一致", "error");
    if (p1.length < 6) return showToast("密码至少6位", "error");
    try {
      await api.put("/api/family/members/" + memberId + "/password", { new_password: p1 });
      closeModal(); showToast("密码已重置");
    } catch (err) { showToast(err.message, "error"); }
  });
}
