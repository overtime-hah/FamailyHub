# FamilyHub 变更日志

## 项目信息
- **项目名称**: FamilyHub - 家庭信息共享平台
- **创建日期**: 2026-05-25
- **技术栈**: Flask + SQLite + 原生 JavaScript
- **UI 风格**: Apple 设计语言，无前端框架依赖

---

## 快速开始

### 环境要求
- Python 3.6+（Windows / macOS / CentOS 7 均支持）
- pip

### Windows 启动
```bash
cd FamilyHub
pip install -r requirements.txt
python run.py
```

### CentOS 7 启动（Python 3.6.8）

> **重要**: CentOS 7 需要先安装编译工具，否则 greenlet 等包会编译失败。

```bash
# 0. 安装系统编译依赖（必须，否则 pip 安装报错）
sudo yum install -y gcc python3-devel

# 1. 确认环境
python3 -V          # Python 3.6.8
pip3 -V             # 确认 pip3 可用

# 2. 安装 Python 依赖
cd /opt/FamilyHub
pip3 install -r requirements.txt

# 3. 开发/测试启动
python3 run.py

# 4. 生产环境（gunicorn 方式）
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
```

### 生产环境 systemd 服务
```bash
sudo tee /etc/systemd/system/familyhub.service << 'SERVICE'
[Unit]
Description=FamilyHub
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/FamilyHub
ExecStart=/usr/bin/python3 /opt/FamilyHub/run.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable --now familyhub
sudo systemctl status familyhub
```

### 访问地址
- 浏览器打开 **http://服务器IP:5000**
- 云服务器需在安全组放行 5000 端口

### 预置账号
| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 成人 | user1 | user123 |
| 儿童 | child1 | child123 |

### 邀请码
- 管理员登录后 → 左侧「家庭」→ 查看/刷新邀请码
- 新用户注册时输入邀请码加入已有家庭
- 留空邀请码则创建新家庭

### 功能导航
| 菜单 | 功能说明 |
|------|----------|
| 动态 | 家庭时间线、公告、生日提醒 |
| 日历 | 共享月视图日历 |
| 清单 | 购物清单 + 待办 + 心愿单 |
| 笔记 | Wiki、食谱、留言板 |
| 相册 | 上传、瀑布流、评论 |
| 文件柜 | 文件夹、文件上传/下载 |
| 记账 | 收支记录、分类统计 |
| 位置 | GPS / IP / 手动定位 |
| 健康 | 健康档案 + 宠物 |
| 家庭 | 成员管理、角色、密码 |

### 数据库
- SQLite，自动创建于 `instance/familyhub.db`
- 首次启动自动写入种子数据
- 重置数据：删除 `instance/` 目录后重启

### 日志
- 每日日志 `logs/YYYY-MM-DD.json`
- 超过 30 天自动清理
- 本文件同步记录变更

### 项目结构
```
FamilyHub/
├── run.py                 # 启动入口
├── config.py              # 配置
├── requirements.txt       # 依赖（Python 3.6+）
├── CHANGELOG.md           # 本文件
├── logs/                  # 日志（自动维护）
├── instance/              # SQLite（自动生成）
└── app/
    ├── __init__.py        # 应用工厂 + 种子数据
    ├── models.py          # 数据模型
    ├── auth.py            # JWT 认证
    ├── log_manager.py     # 日志管理
    ├── routes/            # 10 个 API 蓝图
    ├── static/
    │   ├── css/apple.css
    │   ├── js/            # 核心 + 模块
    │   └── uploads/
    └── templates/         # 2 个 HTML
```

### 依赖版本说明
Python 3.6 兼容版本（已锁定）：
```
Flask==2.0.3              # Flask 3.x 需要 Python 3.8+
Flask-SQLAlchemy==2.5.1   # 3.x 需要 Python 3.8+
Flask-CORS==3.0.10        # 4.x 需要 Python 3.8+
Flask-JWT-Extended==4.4.4
Werkzeug==2.0.3           # 3.x 需要 Python 3.8+
Pillow==8.4.0
SQLAlchemy==1.4.46        # 2.x 需要 Python 3.7+
PyJWT==2.4.0
```

---

## 变更记录

### [2026-05-25] 项目初始化
- 项目基础架构搭建（Flask 应用工厂模式）
- 20 个完整数据模型 (SQLAlchemy ORM)
- JWT 认证系统（注册/登录/token刷新/密码修改）
- 70+ REST API 接口（10 个功能模块）
- Apple 设计风格前端 UI（响应式布局，无框架依赖）
- 日志管理系统（30 天自动清理）
- 哈希路由 + 动态模块加载 SPA
- 管理员成员管理（编辑信息、重置密码、角色分配）
- 位置上报：GPS / IP 定位 / 手动输入 三种方式
- API pageId 守卫机制（过期异步响应自动丢弃）
- CentOS 7 / Python 3.6.8 兼容适配

### 功能模块清单
| 模块 | 后端 | 前端 | 状态 |
|------|------|------|------|
| 认证与家庭管理 | auth.py, routes/family.py | family.js | ✅ |
| 动态流与公告 | routes/feed.py | feed.js | ✅ |
| 共享日历 | routes/calendar.py | calendar.js | ✅ |
| 清单与任务 | routes/tasks.py | tasks.js | ✅ |
| 笔记与知识库 | routes/notes.py | notes.js | ✅ |
| 相册 | routes/album.py | album.js | ✅ |
| 文件柜 | routes/files.py | files.js | ✅ |
| 共享记账 | routes/finance.py | finance.js | ✅ |
| 位置与安全 | routes/location.py | location.js | ✅ |
| 健康与宠物 | routes/health.py | health.js | ✅ |

### 种子数据
- 家庭: 温暖小窝（邀请码: ABC123）
- 用户: admin（管理员）/ user1（成人）/ child1（儿童）
- 示例数据: 日历事件、购物清单、待办、笔记、食谱、留言、记账、宠物
## [2026-06-03]

- ✨ **added**: FamilyHub 服务启动
## [2026-06-04]

- ✨ **added**: FamilyHub 服务启动  

---
*日志自动维护，超过30天的日志条目将自动归档*

- 🔧 **modified**: requirements.txt - 降级依赖包以兼容 CentOS 7 Python 3.6.8 (Flask 3.0→2.0, Werkzeug 3.0→2.0 等)
- 🔧 **modified**: CHANGELOG.md - 重写为完整使用手册，包含 CentOS 7 systemd 部署指南和依赖版本说明
- 🐛 **fixed**: CentOS 7 greenlet 编译失败 - requirements.txt 锁定 greenlet==2.0.2，文档补充 gcc/python3-devel 前置依赖

## [2026-06-04]

- ✨ **added**: 移动端退出登录按钮（底部 TabBar 新增「退出」入口）
- ✨ **added**: 10 分钟无操作自动退出登录（桌面端 + 移动端均生效）
- ✨ **added**: 全局速率限制（每 IP 并发 ≤ 30，每分钟请求 ≤ 1000）
- ✨ **added**: 服务器默认监听地址改为 `0.0.0.0`（支持局域网访问）
- ✨ **added**: API 接口文档补充完整请求/响应示例
- ✨ **added**: 新增 README.md 项目文档