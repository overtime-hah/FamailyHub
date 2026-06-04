/* 共享记账模块 */
let financeMonth = new Date().toISOString().slice(0, 7);
let financeTab = "transactions"; // transactions / bills

async function init_finance_page() {
  financeTab = "transactions";
  await loadFinanceTab();
}

async function loadFinanceTab() {
  const container = document.getElementById("page-content");
  const tabs = [
    { key: "transactions", label: "💳 收支记录" },
    { key: "bills", label: "📋 账单提醒" },
  ];
  let header = `<div class="page-header"><h1>共享记账</h1></div>
  <div class="flex-row gap-sm mb-md">`;
  tabs.forEach(t => {
    const cls = financeTab === t.key ? "btn-primary" : "btn-secondary";
    header += `<button class="btn btn-sm ${cls}" onclick="switchFinanceTab('${t.key}')">${t.label}</button>`;
  });
  header += `</div><div id="fin-content"><div class="spinner"></div></div>`;
  container.innerHTML = header;

  try {
    if (financeTab === "transactions") await loadTransactions();
    else await loadBills();
  } catch (err) {
    if (err && err.aborted) return;
    document.getElementById("fin-content").innerHTML = '<div class="empty-state"><p>' + escapeHtml(err.message) + '</p></div>';
  }
}

window.switchFinanceTab = async function(key) {
  financeTab = key;
  await loadFinanceTab();
};

// ─── 收支记录 ───────────────────────────────────────────

async function loadTransactions() {
  const data = await api.get(`/api/finance/transactions?month=${financeMonth}`);
  const div = document.getElementById("fin-content");
  const s = data.summary || {};

  // 月份选择
  let html = `<div class="flex-row gap-sm mb-md">
    <input class="input" type="month" id="fin-month" value="${financeMonth}" onchange="finMonthChange(this.value)" style="width:200px">
    <button class="btn btn-primary btn-sm" onclick="txForm()">+ 记一笔</button>
  </div>`;

  // 摘要卡片
  html += `<div class="grid-3 mb-md">
    <div class="card" style="text-align:center"><div class="text-sm text-secondary">收入</div><div style="font-size:22px;font-weight:700;color:var(--green)">¥${s.income.toFixed(2)}</div></div>
    <div class="card" style="text-align:center"><div class="text-sm text-secondary">支出</div><div style="font-size:22px;font-weight:700;color:var(--red)">¥${s.expense.toFixed(2)}</div></div>
    <div class="card" style="text-align:center"><div class="text-sm text-secondary">结余</div><div style="font-size:22px;font-weight:700;color:${s.balance>=0?'var(--green)':'var(--red)'}">¥${s.balance.toFixed(2)}</div></div>
  </div>`;

  // 分类柱状图
  if (data.by_category && data.by_category.length > 0) {
    const maxAmt = Math.max(...data.by_category.map(c => c.amount));
    html += `<div class="card mb-md"><div style="font-weight:600;margin-bottom:8px">分类支出</div><div class="bar-chart">`;
    data.by_category.forEach(c => {
      const h = maxAmt > 0 ? (c.amount / maxAmt * 100) : 0;
      html += `<div class="bar-col"><div class="bar-value">¥${c.amount.toFixed(0)}</div><div class="bar-fill" style="height:${h}%"></div><div class="bar-label">${escapeHtml(c.category)}</div></div>`;
    });
    html += `</div></div>`;
  }

  // 记录列表
  html += `<div class="card-list">`;
  if (data.transactions.length === 0) html += `<div class="empty-state"><p>暂无记录</p></div>`;
  data.transactions.forEach(tx => {
    const sign = tx.type === "income" ? "+" : "-";
    const color = tx.type === "income" ? "var(--green)" : "var(--red)";
    html += `<div class="card-list-item flex-between">
      <div class="flex-row gap-md">
        <span class="badge ${tx.type==='income'?'badge-green':'badge-blue'}">${escapeHtml(tx.category)}</span>
        <div>
          <div>${escapeHtml(tx.note || tx.category)}</div>
          <div class="text-sm text-secondary">${escapeHtml(tx.username)} · ${fmtDate(tx.date)}</div>
        </div>
      </div>
      <div style="font-weight:600;color:${color};font-size:16px">${sign}¥${tx.amount.toFixed(2)}</div>
      <button class="btn btn-ghost btn-sm" onclick="delTx(${tx.id})">删除</button>
    </div>`;
  });
  html += `</div>`;
  div.innerHTML = html;
}

window.finMonthChange = function(val) {
  financeMonth = val;
  loadTransactions();
};

window.txForm = function() {
  openModal(`
    <h2>记一笔</h2>
    <div class="form-group"><label>类型</label><select class="select" id="tx-type"><option value="expense">支出</option><option value="income">收入</option></select></div>
    <div class="form-group"><label>类别</label><select class="select" id="tx-cat"><option>餐饮</option><option>交通</option><option>购物</option><option>医疗</option><option>工资</option><option>其他</option></select></div>
    <div class="form-group"><label>金额</label><input class="input" type="number" step="0.01" id="tx-amount" placeholder="0.00"></div>
    <div class="form-group"><label>日期</label><input class="input" type="date" id="tx-date" value="${new Date().toISOString().slice(0,10)}"></div>
    <div class="form-group"><label>备注</label><input class="input" id="tx-note" placeholder="备注"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="tx-save">保存</button>
    </div>
  `);
  document.getElementById("tx-save").addEventListener("click", async function() {
    const amount = parseFloat(document.getElementById("tx-amount").value);
    if (!amount || amount <= 0) return showToast("金额无效", "error");
    try {
      await api.post("/api/finance/transactions", {
        type: document.getElementById("tx-type").value,
        category: document.getElementById("tx-cat").value,
        amount,
        date: document.getElementById("tx-date").value,
        note: document.getElementById("tx-note").value,
      });
      closeModal(); showToast("已记录"); loadTransactions();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.delTx = async function(id) {
  try {
    await api.del(`/api/finance/transactions/${id}`);
    loadTransactions(); showToast("已删除");
  } catch (err) { showToast(err.message, "error"); }
};

// ─── 账单提醒 ───────────────────────────────────────────

async function loadBills() {
  const data = await api.get("/api/finance/bills");
  const div = document.getElementById("fin-content");
  let html = `<button class="btn btn-primary btn-sm mb-md" onclick="billForm()">+ 添加账单</button><div class="card-list">`;
  if (data.bills.length === 0) html += `<div class="empty-state"><p>暂无账单提醒</p></div>`;
  data.bills.forEach(b => {
    const soon = b.days_until_due !== undefined && b.days_until_due <= 3;
    html += `<div class="card-list-item flex-between">
      <div class="flex-row gap-md">
        ${soon ? '<span class="badge badge-red">即将到期</span>' : ''}
        <div>
          <div style="font-weight:600">${escapeHtml(b.title)}</div>
          <div class="text-sm text-secondary">每月${b.due_day}日 · ¥${b.amount.toFixed(2)} · ${b.days_until_due!==undefined ? b.days_until_due+'天后' : ''}</div>
        </div>
      </div>
      <button class="btn btn-ghost btn-sm" onclick="delBill(${b.id})">删除</button>
    </div>`;
  });
  html += `</div>`;
  div.innerHTML = html;
}

window.billForm = function() {
  openModal(`
    <h2>添加账单提醒</h2>
    <div class="form-group"><label>账单名</label><input class="input" id="bill-title" placeholder="如：房租"></div>
    <div class="form-group"><label>金额</label><input class="input" type="number" step="0.01" id="bill-amount" placeholder="0.00"></div>
    <div class="form-group"><label>每月几号到期</label><input class="input" type="number" id="bill-day" value="1" min="1" max="31"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" id="bill-save">保存</button>
    </div>
  `);
  document.getElementById("bill-save").addEventListener("click", async function() {
    const title = document.getElementById("bill-title").value.trim();
    const day = parseInt(document.getElementById("bill-day").value);
    if (!title) return showToast("名称不能为空", "error");
    if (day < 1 || day > 31) return showToast("日期无效", "error");
    try {
      await api.post("/api/finance/bills", {
        title, amount: parseFloat(document.getElementById("bill-amount").value) || 0, due_day: day,
      });
      closeModal(); showToast("已添加"); loadBills();
    } catch (err) { showToast(err.message, "error"); }
  });
};

window.delBill = async function(id) {
  try {
    await api.del(`/api/finance/bills/${id}`);
    loadBills(); showToast("已删除");
  } catch (err) { showToast(err.message, "error"); }
};
