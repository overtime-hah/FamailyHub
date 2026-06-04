# FamilyHub - 家庭信息共享平台

一个基于 Flask 的家庭内部信息共享 Web 应用，采用 Apple 设计语言，无前端框架依赖。

## 功能特性

| 模块 | 说明 |
|------|------|
| 🏠 家庭动态 | 时间线、公告置顶、生日提醒 |
| 📅 共享日历 | 月视图、重复事件、颜色标记 |
| ✅ 清单任务 | 购物清单、家务待办、心愿单 |
| 📝 笔记知识 | 家庭 Wiki、食谱、留言板 |
| 📷 家庭相册 | 多图上传、瀑布流、评论 |
| 📁 文件柜 | 文件夹分类、多格式上传 |
| 💰 记账本 | 收支记录、分类统计、账单提醒 |
| 📍 位置共享 | GPS/IP/手动定位 |
| ❤️ 健康档案 | 体征记录、宠物管理 |
| 👨‍👩‍👧‍👦 家庭管理 | 成员角色、邀请码、密码管理 |

## 技术栈

- **后端**: Flask 2.0.3 + SQLAlchemy 1.4 + JWT
- **数据库**: SQLite（自动创建，零配置）
- **前端**: 原生 JavaScript + Apple 设计风格 CSS
- **兼容**: Python 3.6.8+（CentOS 7 / Windows / macOS）

## 快速开始

### 环境要求

| 项目 | 版本要求 |
|------|----------|
| Python | 3.6.8+ |
| pip | 任意版本 |
| gcc | 编译依赖包需要 |
| python3-devel | 编译依赖包需要 |

### Windows 启动

```bash
cd FamilyHub
pip install -r requirements.txt
python run.py
```

### CentOS 7 启动（Python 3.6.8）

> **已验证环境**: Python 3.6.8 + pip 21.3.1

```bash
# 0. 安装系统编译依赖（必须，否则 greenlet 等包编译失败）
sudo yum install -y gcc python3-devel

# 1. 确认 Python 环境
python3 -V          # Python 3.6.8
pip3 -V             # pip 21.3.1

# 2. 进入项目目录
cd /opt/FamilyHub   # 或你部署的实际路径

# 3. 安装 Python 依赖
pip3 install -r requirements.txt

# 4. 启动服务
python3 run.py
```

服务启动后输出：
```
*** FamilyHub Starting ***
URL: http://0.0.0.0:417
```

浏览器访问 `http://服务器IP:417` 即可。

> **云服务器注意**: 需在安全组/防火墙放行 **417** 端口。

### CentOS 7 防火墙放行端口

```bash
# firewalld
sudo firewall-cmd --zone=public --add-port=417/tcp --permanent
sudo firewall-cmd --reload

# 或 iptables
sudo iptables -I INPUT -p tcp --dport 417 -j ACCEPT
sudo service iptables save
```

### CentOS 7 生产环境部署（systemd）

```bash
# 1. 安装依赖
sudo yum install -y gcc python3-devel
pip3 install -r requirements.txt

# 2. 创建 systemd 服务文件
sudo tee /etc/systemd/system/familyhub.service << 'SERVICE'
[Unit]
Description=FamilyHub - 家庭信息共享平台
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/FamilyHub
ExecStart=/usr/local/bin/python3 /opt/FamilyHub/run.py
Restart=always
RestartSec=3
Environment=FLASK_HOST=0.0.0.0
Environment=FLASK_PORT=417

[Install]
WantedBy=multi-user.target
SERVICE

# 3. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable --now familyhub

# 4. 查看状态
sudo systemctl status familyhub

# 5. 查看日志
sudo journalctl -u familyhub -f
```

### CentOS 7 使用 gunicorn 多进程部署（可选）

```bash
# 安装 gunicorn
pip3 install gunicorn

# 启动（4 个 worker）
gunicorn -w 4 -b 0.0.0.0:417 "run:app"

# systemd 方式
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:417 "run:app"
```

> **注意**: 使用 gunicorn 多进程时，内存速率限制器每个 worker 独立，限制值会按 worker 数量放大。

## 预置账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 可管理成员、查看邀请码 |
| 成人 | user1 | user123 | 普通成人成员 |
| 儿童 | child1 | child123 | 受限功能（隐藏记账、位置） |

## 邀请码机制

- 管理员登录后 → 家庭管理 → 查看/刷新邀请码
- 新用户注册时输入邀请码加入已有家庭
- 留空邀请码则创建新家庭

## 安全特性

| 特性 | 说明 |
|------|------|
| JWT 认证 | Token 有效期 24 小时 |
| 密码加密 | PBKDF2-SHA256（约 60 万次迭代） |
| 登录限制 | 同 IP 5 分钟内最多 5 次 |
| 注册限制 | 同 IP 1 小时内最多 3 次 |
| 密码修改限制 | 同 IP 1 小时内最多 5 次 |
| 全局并发限制 | 每 IP 并发 ≤ 30 |
| 全局频率限制 | 每 IP 每分钟 ≤ 1000 次 |
| 自动退出 | 10 分钟无操作自动跳转登录页 |
| 请求大小限制 | 单次请求体最大 16 MB |
| CORS | 仅允许指定来源 |

## 项目结构

```
FamilyHub/
├── run.py                    # 启动入口
├── config.py                 # 配置文件
├── requirements.txt          # Python 依赖（锁定版本）
├── README.md                 # 本文件
├── CHANGELOG.md              # 变更日志 + 使用手册
├── API_DOCS_FULL.md          # API 接口文档（70+ 接口）
├── logs/                     # 日志（自动维护，保留 7 天）
├── instance/                 # SQLite 数据库（自动创建）
└── app/
    ├── __init__.py           # 应用工厂 + 全局中间件 + 速率限制
    ├── models.py             # 数据模型（20 个表）
    ├── auth.py               # JWT 认证接口
    ├── security.py           # 速率限制工具类
    ├── response.py           # 统一响应格式
    ├── log_manager.py        # 变更日志管理
    ├── logger.py             # 调试日志配置（按日切片）
    ├── routes/               # API 蓝图（10 个模块）
    │   ├── family.py         # 家庭管理
    │   ├── feed.py           # 家庭动态
    │   ├── calendar.py       # 共享日历
    │   ├── tasks.py          # 清单任务
    │   ├── notes.py          # 笔记知识
    │   ├── album.py          # 家庭相册
    │   ├── files.py          # 文件柜
    │   ├── finance.py        # 记账本
    │   ├── location.py       # 位置共享
    │   └── health.py         # 健康档案
    ├── static/
    │   ├── css/apple.css     # 全局样式（Apple 设计语言）
    │   ├── js/
    │   │   ├── api.js        # API 请求封装（JWT、Toast、Modal）
    │   │   ├── auth.js       # 登录/注册页逻辑
    │   │   ├── router.js     # 哈希路由 + 动态模块加载
    │   │   ├── dashboard.js  # 主页逻辑 + 自动退出 + 移动端退出
    │   │   └── modules/      # 各功能模块 JS（10 个文件）
    │   └── uploads/          # 上传文件存储
    └── templates/
        ├── login.html        # 登录/注册页
        └── index.html        # 主应用 SPA 壳
```

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `FLASK_HOST` | `0.0.0.0` | 监听地址（0.0.0.0 = 所有网卡） |
| `FLASK_PORT` | `417` | 监听端口 |
| `FLASK_DEBUG` | `0` | 调试模式（`1` = 开启） |
| `SECRET_KEY` | 随机生成 | Flask 会话密钥 |
| `JWT_SECRET_KEY` | 随机生成 | JWT 签名密钥 |
| `DATABASE_URL` | `sqlite:///instance/familyhub.db` | 数据库连接串 |
| `CORS_ORIGINS` | `http://0.0.0.0:417,...` | CORS 允许来源（逗号分隔） |

## 日志

| 日志类型 | 路径 | 说明 |
|----------|------|------|
| 调试日志 | `logs/debug.log` | 按日切片，保留 7 天 |
| 变更日志 | `logs/YYYY-MM-DD.json` | 超过 30 天自动清理 |

## 重置数据

```bash
rm -rf instance/
python3 run.py   # 自动重建数据库 + 写入种子数据
```

## API 文档

详见 [API_DOCS_FULL.md](./API_DOCS_FULL.md)，包含 70+ 接口的完整请求/响应示例。

## 常见问题

### CentOS 7 pip 安装报错 `error: command 'gcc' failed`

```bash
sudo yum install -y gcc python3-devel
pip3 install -r requirements.txt
```

### 端口被占用

```bash
# 查看占用端口的进程
lsof -i :417
# 或
netstat -tlnp | grep 417

# 杀掉进程后重启
kill -9 <PID>
python3 run.py
```

### 忘记管理员密码

```bash
# 删除数据库重置
rm -rf instance/
python3 run.py
```

### 云服务器无法访问

1. 确认安全组已放行 417 端口
2. 确认防火墙已放行：`sudo firewall-cmd --list-ports`
3. 确认服务监听 0.0.0.0：`netstat -tlnp | grep 417`

## 许可证

MIT License
