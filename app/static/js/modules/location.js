/* 位置模块 - 支持 GPS / IP定位 / 手动输入 */
let locMap = null;
let locMarkers = [];

async function init_location_page() {
  const container = document.getElementById("page-content");
  container.innerHTML = '<div class="spinner"></div>';
  try {
    const data = await api.get("/api/location/members");
    renderLocation(container, data.members || []);
  } catch (err) {
    if (err && err.aborted) return;
    container.innerHTML = '<div class="empty-state"><p>' + escapeHtml(err.message) + '</p></div>';
  }
}

async function renderLocation(container, members) {
  let html = '<div class="page-header flex-between">';
  html += '<div><h1>位置共享</h1><p>查看家人在哪里</p></div>';
  html += '<button class="btn btn-primary btn-sm" onclick="showLocationPanel()">上报位置</button>';
  html += '</div>';

  // 地图
  html += '<div class="card mb-md"><div id="loc-map" class="map-container"></div></div>';

  // 成员位置卡片
  html += '<div class="card-list">';
  members.forEach(function(m) {
    const loc = m.location;
    const hasLoc = loc && loc.latitude;
    html += '<div class="card-list-item">';
    html += '<div class="flex-row gap-md">';
    html += avatarHtml(m.username, "avatar-sm");
    html += '<div style="flex:1"><strong>' + escapeHtml(m.username) + '</strong> <span class="badge badge-blue">' + escapeHtml(m.role) + '</span>';
    html += '<div class="text-sm text-secondary">';
    if (hasLoc) {
      html += '位置: ' + loc.latitude.toFixed(4) + ', ' + loc.longitude.toFixed(4);
      html += ' · ' + timeAgo(loc.timestamp);
    } else {
      html += '未上报位置';
    }
    html += '</div></div></div></div>';
  });
  html += '</div>';
  container.innerHTML = html;

  // 延迟初始化地图
  setTimeout(function() { initMap(members); }, 300);
}

// ─── 位置上报面板 ─────────────────────────────────────

window.showLocationPanel = function() {
  openModal(
    '<h2>上报我的位置</h2>' +
    '<p class="text-sm text-secondary mb-md">选择一种方式获取你的位置，电脑端推荐使用 IP 定位或手动输入</p>' +

    // 方式1: GPS
    '<div class="card mb-md" style="cursor:pointer" id="loc-gps-card">' +
    '<div class="flex-row gap-md">' +
    '<span style="font-size:28px">🛰️</span>' +
    '<div style="flex:1"><strong>GPS 定位</strong><div class="text-sm text-secondary">最准确，需要浏览器授权定位权限（手机端推荐）</div></div>' +
    '<span style="font-size:20px;color:var(--text-secondary)">›</span>' +
    '</div></div>' +

    // 方式2: IP定位
    '<div class="card mb-md" style="cursor:pointer" id="loc-ip-card">' +
    '<div class="flex-row gap-md">' +
    '<span style="font-size:28px">🌐</span>' +
    '<div style="flex:1"><strong>IP 定位</strong><div class="text-sm text-secondary">通过网络IP地址大致定位，无需授权（电脑端推荐）</div></div>' +
    '<span style="font-size:20px;color:var(--text-secondary)">›</span>' +
    '</div></div>' +

    // 方式3: 手动输入
    '<div class="card mb-md" style="cursor:pointer" id="loc-manual-card">' +
    '<div class="flex-row gap-md">' +
    '<span style="font-size:28px">📍</span>' +
    '<div style="flex:1"><strong>手动输入坐标</strong><div class="text-sm text-secondary">直接输入经纬度坐标</div></div>' +
    '<span style="font-size:20px;color:var(--text-secondary)">›</span>' +
    '</div></div>' +

    '<div class="modal-actions">' +
    '<button class="btn btn-secondary" onclick="closeModal()">关闭</button>' +
    '</div>'
  );

  // 绑定三种方式的点击事件
  document.getElementById("loc-gps-card").addEventListener("click", function() {
    closeModal();
    reportByGPS();
  });
  document.getElementById("loc-ip-card").addEventListener("click", function() {
    closeModal();
    reportByIP();
  });
  document.getElementById("loc-manual-card").addEventListener("click", function() {
    closeModal();
    reportManual();
  });
};

// ─── GPS 定位 ──────────────────────────────────────────

window.reportByGPS = function() {
  if (!navigator.geolocation) {
    showToast("浏览器不支持 GPS 定位，请尝试 IP 定位", "error");
    return;
  }
  showToast("正在获取 GPS 位置...", "success");

  // 设置超时 (10秒)
  const opts = { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 };

  navigator.geolocation.getCurrentPosition(
    function(pos) {
      sendLocation(pos.coords.latitude, pos.coords.longitude);
    },
    function(err) {
      let msg = "GPS 定位失败: ";
      switch (err.code) {
        case err.PERMISSION_DENIED: msg += "权限被拒绝，请允许浏览器定位"; break;
        case err.POSITION_UNAVAILABLE: msg += "无法获取位置信息"; break;
        case err.TIMEOUT: msg += "定位超时"; break;
        default: msg += err.message;
      }
      showToast(msg + "，可尝试 IP 定位", "error");
    },
    opts
  );
};

// ─── IP 定位 ───────────────────────────────────────────

window.reportByIP = function() {
  showToast("正在通过 IP 获取位置...", "success");

  // 使用 ip-api.com 免费接口 (无需 API Key，每分钟 45 次限制)
  fetch("http://ip-api.com/json/?fields=lat,lon,city,country")
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.lat && data.lon) {
        sendLocation(data.lat, data.lon);
        showToast("IP 定位成功 (" + (data.city || "") + ", " + (data.country || "") + ")", "success");
      } else {
        showToast("IP 定位失败，请尝试手动输入", "error");
      }
    })
    .catch(function() {
      showToast("IP 定位服务不可用，请检查网络或尝试手动输入", "error");
    });
};

// ─── 手动输入 ──────────────────────────────────────────

window.reportManual = function() {
  openModal(
    '<h2>手动输入坐标</h2>' +
    '<p class="text-sm text-secondary mb-md">你可以在手机地图 App（如高德、百度地图）中长按任意位置获取经纬度</p>' +
    '<div class="form-group"><label>经度 (Longitude)</label><input class="input" id="man-lng" placeholder="例如: 116.4074" type="number" step="any"></div>' +
    '<div class="form-group"><label>纬度 (Latitude)</label><input class="input" id="man-lat" placeholder="例如: 39.9042" type="number" step="any"></div>' +
    '<div class="modal-actions">' +
    '<button class="btn btn-secondary" onclick="closeModal()">取消</button>' +
    '<button class="btn btn-primary" id="man-save">上报</button>' +
    '</div>'
  );
  document.getElementById("man-save").addEventListener("click", function() {
    const lng = parseFloat(document.getElementById("man-lng").value);
    const lat = parseFloat(document.getElementById("man-lat").value);
    if (isNaN(lng) || isNaN(lat)) return showToast("请输入有效坐标", "error");
    if (lng < -180 || lng > 180 || lat < -90 || lat > 90) return showToast("坐标范围无效", "error");
    closeModal();
    sendLocation(lat, lng);
  });
};

// ─── 发送位置到后端 ───────────────────────────────────

function sendLocation(lat, lng) {
  api.post("/api/location/report", { latitude: lat, longitude: lng })
    .then(function() {
      showToast("位置已上报");
      init_location_page();
    })
    .catch(function(err) {
      if (!err.aborted) showToast(err.message, "error");
    });
}

// ─── Leaflet 地图 ──────────────────────────────────────

function initMap(members) {
  const mapEl = document.getElementById("loc-map");
  if (!mapEl) return;

  if (locMap) { locMap.remove(); locMap = null; }
  mapEl.innerHTML = "";

  const withLoc = members.filter(function(m) { return m.location && m.location.latitude; });
  if (withLoc.length === 0) {
    mapEl.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-secondary)">暂无位置数据，点击"上报位置"开始</div>';
    return;
  }

  if (!window.L) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(link);
    const script = document.createElement("script");
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.onload = function() { drawMap(mapEl, withLoc); };
    document.head.appendChild(script);
  } else {
    drawMap(mapEl, withLoc);
  }
}

function drawMap(mapEl, withLoc) {
  locMap = L.map(mapEl).setView([35, 105], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
    maxZoom: 18,
  }).addTo(locMap);

  const colors = ["#007aff", "#ff9500", "#34c759", "#ff3b30", "#5856d6"];
  locMarkers.forEach(function(m) { m.remove(); });
  locMarkers = [];

  withLoc.forEach(function(m, i) {
    const loc = m.location;
    const marker = L.circleMarker([loc.latitude, loc.longitude], {
      radius: 10, fillColor: colors[i % colors.length],
      color: "#fff", weight: 2, fillOpacity: 0.85,
    }).addTo(locMap);
    marker.bindPopup("<strong>" + escapeHtml(m.username) + "</strong><br>" + timeAgo(loc.timestamp));
    locMarkers.push(marker);
  });

  if (withLoc.length > 0) {
    const bounds = withLoc.map(function(m) { return [m.location.latitude, m.location.longitude]; });
    locMap.fitBounds(bounds, { padding: [30, 30], maxZoom: 14 });
  }
}
