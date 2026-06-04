# FamilyHub API 接口完整文档

> **Base URL:** `http://0.0.0.0:417`（局域网内任意设备可访问）
> **认证方式:** JWT Bearer Token  
> **Content-Type:** `application/json`（文件上传除外用 `multipart/form-data`）

---

## 一、Token 获取流程

### 1. 密码加密说明

| 项目 | 说明 |
|------|------|
| 算法 | PBKDF2-SHA256 |
| 库 | `werkzeug.security.generate_password_hash` |
| 迭代次数 | 约 600,000 次 |
| 盐值 | 每次自动生成随机盐 |
| 存储格式 | `pbkdf2:sha256:600000$盐值$哈希值` |

**关键点：**
- 密码明文**永远不存数据库**
- 相同密码每次哈希结果不同（盐值随机）
- 不可逆，无法从哈希反推密码
- 前端传密码用明文即可，HTTPS 环境下安全传输

### 2. Token 获取方式

```
方式一：登录 → POST /api/auth/login → 返回 access_token
方式二：注册 → POST /api/auth/register → 返回 access_token
```

### 3. Token 使用方式

所有需要认证的接口，在 Header 中携带：

```
Authorization: Bearer <access_token>
```

- Token 有效期：**24 小时**
- 过期后调用接口返回 `401`
- 可通过 `POST /api/auth/refresh` 刷新

---

## 二、认证接口

---

### POST /api/auth/login — 登录获取 Token

**需要 Token：** ❌ 不需要

**请求参数：**

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| username | string | ✅ | 用户名，最长 80 字符 | `"admin"` |
| password | string | ✅ | 密码，最长 128 字符 | `"admin123"` |

**请求示例：**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| access_token | string | JWT Token，后续请求用此值鉴权 |
| user.id | int | 用户 ID |
| user.username | string | 用户名 |
| user.email | string | 邮箱 |
| user.nickname | string | 昵称 |
| user.birthday | string \| null | 生日，格式 `YYYY-MM-DD`，无则为 null |
| user.avatar_url | string | 头像 URL，无则为空字符串 |
| user.family_id | int | 所属家庭 ID |
| user.role | string | 角色：`admin`（管理员）/ `adult`（成人）/ `child`（儿童） |

**响应示例：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@familyhub.local",
    "nickname": "爸爸",
    "birthday": null,
    "avatar_url": "",
    "family_id": 1,
    "role": "admin"
  }
}
```

**错误响应：**

| 状态码 | msg | 原因 |
|--------|-----|------|
| 400 | `"用户名和密码不能为空"` | username 或 password 为空 |
| 400 | `"输入内容过长"` | username > 80 或 password > 128 字符 |
| 401 | `"用户名或密码错误"` | 用户不存在或密码错误 |
| 403 | `"你尚未加入任何家庭"` | 用户存在但未加入任何家庭 |
| 429 | `"登录尝试过于频繁，请5分钟后重试"` | 同一 IP 5 分钟内登录超过 5 次 |

---

### POST /api/auth/register — 注册并获取 Token

**需要 Token：** ❌ 不需要

**请求参数：**

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| username | string | ✅ | 用户名，唯一，最长 100 字符 | `"newuser"` |
| email | string | ✅ | 邮箱，唯一，需符合邮箱格式 | `"new@example.com"` |
| password | string | ✅ | 密码，至少 6 位，最长 200 字符 | `"mypassword"` |
| nickname | string | ❌ | 昵称，最长 100 字符，不填默认等于 username | `"小新"` |
| invite_code | string | ❌ | 邀请码，6 位大写字母+数字，填了加入已有家庭 | `"ABC123"` |
| family_name | string | ❌ | 家庭名称，不填邀请码时用于创建新家庭 | `"温暖的家"` |

**请求示例 — 创建新家庭：**
```json
{
  "username": "newuser",
  "email": "new@example.com",
  "password": "mypassword",
  "nickname": "小新",
  "family_name": "温暖的家"
}
```

**请求示例 — 加入已有家庭：**
```json
{
  "username": "newuser",
  "email": "new@example.com",
  "password": "mypassword",
  "invite_code": "ABC123"
}
```

**成功响应 201：**

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | `"创建家庭成功"` 或 `"加入家庭成功"` |
| access_token | string | JWT Token |
| user | object | 用户信息，结构同登录接口 |

**错误响应：**

| 状态码 | msg | 原因 |
|--------|-----|------|
| 400 | `"以下字段不能为空: username, email"` | 必填字段缺失 |
| 400 | `"邮箱格式无效"` | email 不符合格式 |
| 400 | `"密码至少6位"` | password 不足 6 位 |
| 404 | `"邀请码无效"` | invite_code 对应的家庭不存在 |
| 409 | `"用户名已存在"` | username 已被注册 |
| 409 | `"邮箱已被注册"` | email 已被注册 |
| 429 | `"注册尝试过于频繁，请1小时后重试"` | 同一 IP 1 小时内注册超过 3 次 |

---

### POST /api/auth/refresh — 刷新 Token

**需要 Token：** ✅

**请求参数：** 无

**请求示例：**
```bash
curl -X POST http://0.0.0.0:417/api/auth/refresh \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| access_token | string | 新的 JWT Token |

**响应示例：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0ODk1MjAwMCwianRpIjoiM2FlZGFiY2QtMTIzNC01Njc4LTkwMTItMzQ1Njc4OTBhYmNkIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MSwibmJmIjoxNzQ4OTUyMDAwLCJleHAiOjE3NDkwMzg0MDB9.new_signature_here"
}
```

---

### GET /api/auth/me — 获取当前用户信息

**需要 Token：** ✅

**请求参数：** 无

**请求示例：**
```bash
curl http://0.0.0.0:417/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| user.id | int | 用户 ID |
| user.username | string | 用户名 |
| user.email | string | 邮箱 |
| user.nickname | string | 昵称 |
| user.birthday | string \| null | 生日 `YYYY-MM-DD` |
| user.avatar_url | string | 头像 URL |
| user.family_id | int | 家庭 ID |
| user.role | string | 角色 |

**响应示例：**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@familyhub.local",
    "nickname": "爸爸",
    "birthday": null,
    "avatar_url": "",
    "family_id": 1,
    "role": "admin"
  }
}
```

---

### PUT /api/auth/password — 修改密码

**需要 Token：** ✅

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | ✅ | 当前密码，最长 128 字符 |
| new_password | string | ✅ | 新密码，至少 6 位，最长 128 字符 |

**请求示例：**
```json
{
  "old_password": "admin123",
  "new_password": "newpass456"
}
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | `"密码已修改"` |

**响应示例：**
```json
{
  "msg": "密码已修改"
}
```

**错误响应：**

| 状态码 | msg |
|--------|-----|
| 400 | `"旧密码和新密码不能为空"` |
| 400 | `"新密码至少6位"` |
| 400 | `"输入内容过长"` |
| 401 | `"旧密码错误"` |
| 429 | `"密码修改尝试过于频繁，请1小时后重试"` |

---

## 三、家庭管理 /api/family

> 以下所有接口均需 Token ✅

---

### GET /api/family/info — 获取家庭信息

**请求参数：** 无

**请求示例：**
```bash
curl http://0.0.0.0:417/api/family/info \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| family.id | int | 家庭 ID |
| family.name | string | 家庭名称 |
| family.invite_code | string | 邀请码，6 位 |
| family.created_at | string | 创建时间 ISO 格式 |
| family.member_count | int | 成员数量 |
| members[] | array | 成员列表 |
| members[].id | int | 家庭成员记录 ID |
| members[].user_id | int | 用户 ID |
| members[].family_id | int | 家庭 ID |
| members[].role | string | 角色：`admin`/`adult`/`child` |
| members[].joined_at | string | 加入时间 |
| members[].user.id | int | 用户 ID |
| members[].user.username | string | 用户名 |
| members[].user.email | string | 邮箱 |
| members[].user.nickname | string | 昵称 |
| members[].user.birthday | string \| null | 生日 |
| members[].user.avatar_url | string | 头像 URL |
| members[].user.family_id | int | 家庭 ID |
| members[].user.role | string | 角色 |

**响应示例：**
```json
{
  "family": {
    "id": 1,
    "name": "温暖小窝",
    "invite_code": "ABC123",
    "created_at": "2026-06-04T10:00:00",
    "member_count": 3
  },
  "members": [
    {
      "id": 1,
      "user_id": 1,
      "family_id": 1,
      "role": "admin",
      "joined_at": "2026-06-04T10:00:00",
      "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@familyhub.local",
        "nickname": "爸爸",
        "birthday": null,
        "avatar_url": "",
        "family_id": 1,
        "role": "admin"
      }
    },
    {
      "id": 2,
      "user_id": 2,
      "family_id": 1,
      "role": "adult",
      "joined_at": "2026-06-04T10:00:00",
      "user": {
        "id": 2,
        "username": "user1",
        "email": "user1@familyhub.local",
        "nickname": "妈妈",
        "birthday": null,
        "avatar_url": "",
        "family_id": 1,
        "role": "adult"
      }
    }
  ]
}
```

---

### GET /api/family/invite-code — 获取邀请码

**权限：** 仅管理员

**请求参数：** 无

**请求示例：**
```bash
curl http://0.0.0.0:417/api/family/invite-code \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| invite_code | string | 当前邀请码，6 位大写字母+数字 |

**响应示例：**
```json
{
  "invite_code": "ABC123"
}
```

**错误：** 403 `"仅管理员可查看邀请码"`

---

### POST /api/family/invite-code — 刷新邀请码

**权限：** 仅管理员

**请求参数：** 无

**请求示例：**
```bash
curl -X POST http://0.0.0.0:417/api/family/invite-code \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| invite_code | string | 新生成的邀请码 |

**响应示例：**
```json
{
  "invite_code": "XYZ789"
}
```

---

### PUT /api/family/members/{member_id}/role — 修改成员角色

**权限：** 仅管理员

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| member_id | int | 家庭成员记录 ID（不是 user_id） |

**请求参数：**

| 字段 | 类型 | 必填 | 说明 | 可选值 |
|------|------|------|------|--------|
| role | string | ✅ | 新角色 | `"admin"` / `"adult"` / `"child"` |

**请求示例：**
```json
{
  "role": "adult"
}
```

**成功响应 200：** `{"msg": "角色已更新"}`

**响应示例：**
```json
{
  "msg": "角色已更新"
}
```

**错误：** 404 `"成员不存在"` / 400 `"无效的角色"`

---

### DELETE /api/family/members/{member_id} — 移出成员

**权限：** 仅管理员，不能移出自己

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| member_id | int | 家庭成员记录 ID |

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/family/members/3 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：** `{"msg": "成员已移出"}`

**响应示例：**
```json
{
  "msg": "成员已移出"
}
```

**错误：** 400 `"不能移出自己"`

---

### PUT /api/family/members/{member_id}/profile — 管理员修改成员信息

**权限：** 仅管理员

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| member_id | int | 家庭成员记录 ID |

**请求参数（全部可选）：**

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| nickname | string | ❌ | 新昵称，最长 100 字符 | `"小明"` |
| email | string | ❌ | 新邮箱，需唯一 | `"new@email.com"` |
| birthday | string \| null | ❌ | 生日 `YYYY-MM-DD`，传 null 清除 | `"2018-05-15"` |
| avatar_url | string | ❌ | 头像 URL | `"https://..."` |

**请求示例：**
```json
{
  "nickname": "小明同学",
  "birthday": "2018-05-15"
}
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| user | object | 更新后的用户信息（结构同登录接口的 user） |

**响应示例：**
```json
{
  "user": {
    "id": 3,
    "username": "child1",
    "email": "child1@familyhub.local",
    "nickname": "小明同学",
    "birthday": "2018-05-15",
    "avatar_url": "",
    "family_id": 1,
    "role": "child"
  }
}
```

---

### PUT /api/family/members/{member_id}/password — 管理员重置密码

**权限：** 仅管理员，无需旧密码

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| member_id | int | 家庭成员记录 ID |

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| new_password | string | ✅ | 新密码，至少 6 位 |

**请求示例：**
```json
{
  "new_password": "newpass123"
}
```

**成功响应 200：** `{"msg": "密码已重置"}`

**响应示例：**
```json
{
  "msg": "密码已重置"
}
```

---

### PUT /api/family/profile — 修改个人信息

**请求参数（全部可选）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | ❌ | 昵称 |
| birthday | string \| null | ❌ | 生日 `YYYY-MM-DD` |
| avatar_url | string | ❌ | 头像 URL |

**请求示例：**
```json
{
  "nickname": "新昵称",
  "birthday": "1990-01-15"
}
```

**成功响应 200：** `{"user": {...}}`

**响应示例：**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@familyhub.local",
    "nickname": "新昵称",
    "birthday": "1990-01-15",
    "avatar_url": "",
    "family_id": 1,
    "role": "admin"
  }
}
```

---

### POST /api/family/leave — 退出家庭

**请求参数：** 无

**请求示例：**
```bash
curl -X POST http://0.0.0.0:417/api/family/leave \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：** `{"msg": "已退出家庭"}`

**响应示例：**
```json
{
  "msg": "已退出家庭"
}
```

**错误：** 400 `"你是唯一的管理员，请先将管理员权限转移给其他成员"`

---

## 四、家庭动态 /api/feed

---

### GET /api/feed/list — 获取动态列表

**需要 Token：** ✅

**请求参数（Query）：**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | ❌ | 1 | 页码 |
| per_page | int | ❌ | 30 | 每页条数 |

**请求示例：**
```bash
curl "http://0.0.0.0:417/api/feed/list?page=1&per_page=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| feeds[] | array | 动态列表 |
| feeds[].id | int | 动态 ID |
| feeds[].family_id | int | 家庭 ID |
| feeds[].user_id | int | 发布者用户 ID |
| feeds[].username | string | 发布者昵称 |
| feeds[].content | string | 动态内容 |
| feeds[].type | string | 类型：`announcement`/`member`/`event`/`task`/`photo`/`info` |
| feeds[].is_pinned | bool | 是否置顶 |
| feeds[].created_at | string | 创建时间 |
| upcoming_birthdays[] | array | 7 天内即将到来的生日 |
| upcoming_birthdays[].user_id | int | 用户 ID |
| upcoming_birthdays[].username | string | 昵称 |
| upcoming_birthdays[].birthday | string | 生日 `YYYY-MM-DD` |
| upcoming_birthdays[].days_left | int | 还有几天（0=今天，1=明天） |
| total | int | 总条数 |
| pages | int | 总页数 |

**响应示例：**
```json
{
  "feeds": [
    {
      "id": 1,
      "family_id": 1,
      "user_id": 1,
      "username": "爸爸",
      "content": "欢迎加入温暖小窝！这是我们的家庭共享空间 🏠",
      "type": "announcement",
      "is_pinned": true,
      "created_at": "2026-06-04T10:00:00"
    },
    {
      "id": 2,
      "family_id": 1,
      "user_id": 2,
      "username": "妈妈",
      "content": "妈妈加入了家庭",
      "type": "member",
      "is_pinned": false,
      "created_at": "2026-06-04T09:50:00"
    }
  ],
  "upcoming_birthdays": [
    {
      "user_id": 3,
      "username": "小明",
      "birthday": "2018-05-15",
      "days_left": 11
    }
  ],
  "total": 3,
  "pages": 1
}
```

---

### POST /api/feed/announcement — 发布公告

**权限：** 仅管理员

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | ✅ | 公告内容 |

**请求示例：**
```json
{
  "content": "明天家里大扫除，请大家准备好清洁工具！"
}
```

**成功响应 201：** `{"feed": {...}}`

**响应示例：**
```json
{
  "feed": {
    "id": 4,
    "family_id": 1,
    "user_id": 1,
    "username": "爸爸",
    "content": "明天家里大扫除，请大家准备好清洁工具！",
    "type": "announcement",
    "is_pinned": false,
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### DELETE /api/feed/{feed_id} — 删除动态

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| feed_id | int | 动态 ID |

**权限：** 管理员可删除任意动态，普通成员只能删除自己的

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/feed/2 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：** `{"msg": "已删除"}`

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

## 五、共享日历 /api/calendar

---

### GET /api/calendar/events — 获取月度事件

**需要 Token：** ✅

**请求参数（Query）：**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| year | int | ❌ | 当前年 | 年份 |
| month | int | ❌ | 当前月 | 月份 1-12 |

**请求示例：**
```bash
curl "http://0.0.0.0:417/api/calendar/events?year=2026&month=6" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| events[] | array | 事件列表 |
| events[].id | int | 事件 ID |
| events[].family_id | int | 家庭 ID |
| events[].creator_id | int | 创建者用户 ID |
| events[].creator_name | string | 创建者昵称 |
| events[].title | string | 事件标题 |
| events[].start | string | 开始时间 `YYYY-MM-DDTHH:MM:SS` |
| events[].end | string | 结束时间 |
| events[].all_day | bool | 是否全天事件 |
| events[].location | string | 地点 |
| events[].description | string | 描述 |
| events[].repeat_rule | string | 重复规则：`none`/`daily`/`weekly`/`monthly`/`yearly` |
| events[].color | string | 颜色，如 `"#ff9500"` |
| events[].created_at | string | 创建时间 |

**响应示例：**
```json
{
  "events": [
    {
      "id": 1,
      "family_id": 1,
      "creator_id": 1,
      "creator_name": "爸爸",
      "title": "家庭聚餐",
      "start": "2026-06-06T10:00:00",
      "end": "2026-06-06T12:00:00",
      "all_day": false,
      "location": "家里",
      "description": "周末家庭聚餐",
      "repeat_rule": "none",
      "color": "#ff9500",
      "created_at": "2026-06-04T10:00:00"
    },
    {
      "id": 2,
      "family_id": 1,
      "creator_id": 2,
      "creator_name": "妈妈",
      "title": "小明家长会",
      "start": "2026-06-09T09:00:00",
      "end": "2026-06-09T11:00:00",
      "all_day": false,
      "location": "学校",
      "description": "期中家长会",
      "repeat_rule": "none",
      "color": "#007aff",
      "created_at": "2026-06-04T10:00:00"
    }
  ]
}
```

---

### POST /api/calendar/events — 创建事件

**请求参数：**

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| title | string | ✅ | 事件标题 | `"家庭聚餐"` |
| start | string | ✅ | 开始时间 ISO 格式 | `"2026-06-05T10:00:00"` |
| end | string | ✅ | 结束时间 ISO 格式 | `"2026-06-05T12:00:00"` |
| all_day | bool | ❌ | 是否全天，默认 false | `false` |
| location | string | ❌ | 地点 | `"家里"` |
| description | string | ❌ | 描述 | `"周末聚餐"` |
| repeat_rule | string | ❌ | 重复规则，默认 `"none"` | `"weekly"` |
| color | string | ❌ | 颜色，默认 `"#007aff"` | `"#ff9500"` |

**请求示例：**
```json
{
  "title": "家庭聚餐",
  "start": "2026-06-06T10:00:00",
  "end": "2026-06-06T12:00:00",
  "all_day": false,
  "location": "家里",
  "description": "周末家庭聚餐",
  "repeat_rule": "none",
  "color": "#ff9500"
}
```

**成功响应 201：** `{"event": {...}}`

**响应示例：**
```json
{
  "event": {
    "id": 3,
    "family_id": 1,
    "creator_id": 1,
    "creator_name": "爸爸",
    "title": "家庭聚餐",
    "start": "2026-06-06T10:00:00",
    "end": "2026-06-06T12:00:00",
    "all_day": false,
    "location": "家里",
    "description": "周末家庭聚餐",
    "repeat_rule": "none",
    "color": "#ff9500",
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### PUT /api/calendar/events/{event_id} — 更新事件

所有字段同创建接口，全部可选。

**请求示例：**
```json
{
  "title": "家庭聚餐（改期）",
  "start": "2026-06-07T10:00:00",
  "end": "2026-06-07T12:00:00"
}
```

**响应示例：**
```json
{
  "event": {
    "id": 3,
    "family_id": 1,
    "creator_id": 1,
    "creator_name": "爸爸",
    "title": "家庭聚餐（改期）",
    "start": "2026-06-07T10:00:00",
    "end": "2026-06-07T12:00:00",
    "all_day": false,
    "location": "家里",
    "description": "周末家庭聚餐",
    "repeat_rule": "none",
    "color": "#ff9500",
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### DELETE /api/calendar/events/{event_id} — 删除事件

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/calendar/events/3 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：** `{"msg": "已删除"}`

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

## 六、清单任务 /api/tasks

---

### GET /api/tasks/shopping — 购物清单

**需要 Token：** ✅

**请求参数（Query）：**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | ❌ | 1 | 页码 |
| per_page | int | ❌ | 20 | 每页条数 |

**请求示例：**
```bash
curl "http://0.0.0.0:417/api/tasks/shopping?page=1&per_page=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| items[] | array | 物品列表 |
| items[].id | int | 物品 ID |
| items[].family_id | int | 家庭 ID |
| items[].added_by | int | 添加者用户 ID |
| items[].adder_name | string | 添加者昵称 |
| items[].name | string | 物品名称 |
| items[].quantity | string | 数量，如 `"2瓶"` |
| items[].bought | bool | 是否已购买 |
| items[].created_at | string | 创建时间 |
| total | int | 总条数 |
| page | int | 当前页 |
| pages | int | 总页数 |

**响应示例：**
```json
{
  "items": [
    {
      "id": 1,
      "family_id": 1,
      "added_by": 1,
      "adder_name": "爸爸",
      "name": "牛奶",
      "quantity": "2瓶",
      "bought": false,
      "created_at": "2026-06-04T10:00:00"
    },
    {
      "id": 2,
      "family_id": 1,
      "added_by": 2,
      "adder_name": "妈妈",
      "name": "面包",
      "quantity": "1袋",
      "bought": true,
      "created_at": "2026-06-04T10:00:00"
    }
  ],
  "total": 3,
  "page": 1,
  "pages": 1
}
```

---

### POST /api/tasks/shopping — 添加购物物品

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| name | string | ✅ | 物品名称 | `"牛奶"` |
| quantity | string | ❌ | 数量，默认 `"1"` | `"2瓶"` |

**请求示例：**
```json
{
  "name": "牛奶",
  "quantity": "2瓶"
}
```

**成功响应 201：** `{"item": {...}}`

**响应示例：**
```json
{
  "item": {
    "id": 4,
    "family_id": 1,
    "added_by": 1,
    "adder_name": "爸爸",
    "name": "牛奶",
    "quantity": "2瓶",
    "bought": false,
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### PUT /api/tasks/shopping/{item_id} — 更新购物物品

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| bought | bool | ❌ | 标记已买/未买 |
| name | string | ❌ | 修改名称 |
| quantity | string | ❌ | 修改数量 |

**请求示例：**
```json
{
  "bought": true
}
```

**响应示例：**
```json
{
  "item": {
    "id": 1,
    "family_id": 1,
    "added_by": 1,
    "adder_name": "爸爸",
    "name": "牛奶",
    "quantity": "2瓶",
    "bought": true,
    "created_at": "2026-06-04T10:00:00"
  }
}
```

---

### DELETE /api/tasks/shopping/{item_id} — 删除购物物品

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/tasks/shopping/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

### GET /api/tasks/chores — 家务待办

**请求参数：** `page`、`per_page`（同购物清单）

**请求示例：**
```bash
curl "http://0.0.0.0:417/api/tasks/chores?page=1&per_page=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| tasks[] | array | 待办列表 |
| tasks[].id | int | 待办 ID |
| tasks[].family_id | int | 家庭 ID |
| tasks[].creator_id | int | 创建者用户 ID |
| tasks[].assignee_id | int | 负责人用户 ID |
| tasks[].assignee_name | string | 负责人昵称 |
| tasks[].title | string | 待办标题 |
| tasks[].due_date | string \| null | 截止日期 `YYYY-MM-DD` |
| tasks[].completed | bool | 是否完成 |
| tasks[].created_at | string | 创建时间 |
| total / page / pages | int | 分页信息 |

**响应示例：**
```json
{
  "tasks": [
    {
      "id": 1,
      "family_id": 1,
      "creator_id": 1,
      "assignee_id": 1,
      "assignee_name": "爸爸",
      "title": "倒垃圾",
      "due_date": "2026-06-04",
      "completed": false,
      "created_at": "2026-06-04T10:00:00"
    },
    {
      "id": 2,
      "family_id": 1,
      "creator_id": 2,
      "assignee_id": 1,
      "assignee_name": "爸爸",
      "title": "修理水龙头",
      "due_date": "2026-06-07",
      "completed": false,
      "created_at": "2026-06-04T10:00:00"
    },
    {
      "id": 3,
      "family_id": 1,
      "creator_id": 1,
      "assignee_id": 2,
      "assignee_name": "妈妈",
      "title": "整理衣柜",
      "due_date": "2026-06-05",
      "completed": true,
      "created_at": "2026-06-04T10:00:00"
    }
  ],
  "total": 3,
  "page": 1,
  "pages": 1
}
```

---

### POST /api/tasks/chores — 创建待办

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| title | string | ✅ | 待办标题 | `"倒垃圾"` |
| due_date | string | ❌ | 截止日期 `YYYY-MM-DD` | `"2026-06-05"` |
| assignee_id | int | ❌ | 负责人用户 ID，默认当前用户 | `1` |

**请求示例：**
```json
{
  "title": "倒垃圾",
  "due_date": "2026-06-05",
  "assignee_id": 1
}
```

**响应示例：**
```json
{
  "task": {
    "id": 4,
    "family_id": 1,
    "creator_id": 1,
    "assignee_id": 1,
    "assignee_name": "爸爸",
    "title": "倒垃圾",
    "due_date": "2026-06-05",
    "completed": false,
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### PUT /api/tasks/chores/{task_id} — 更新待办

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| completed | bool | ❌ | 标记完成/未完成 |
| title | string | ❌ | 修改标题 |
| assignee_id | int | ❌ | 修改负责人 |
| due_date | string | ❌ | 修改截止日期 |

**请求示例：**
```json
{
  "completed": true
}
```

**响应示例：**
```json
{
  "task": {
    "id": 1,
    "family_id": 1,
    "creator_id": 1,
    "assignee_id": 1,
    "assignee_name": "爸爸",
    "title": "倒垃圾",
    "due_date": "2026-06-04",
    "completed": true,
    "created_at": "2026-06-04T10:00:00"
  }
}
```

---

### DELETE /api/tasks/chores/{task_id} — 删除待办

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/tasks/chores/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

### GET /api/tasks/wishes — 心愿单

**请求示例：**
```bash
curl http://0.0.0.0:417/api/tasks/wishes \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| wishes[] | array | 心愿列表 |
| wishes[].id | int | 心愿 ID |
| wishes[].user_id | int | 心愿主人用户 ID |
| wishes[].username | string | 心愿主人昵称 |
| wishes[].family_id | int | 家庭 ID |
| wishes[].name | string | 心愿名称 |
| wishes[].link | string | 购买链接 |
| wishes[].note | string | 备注 |
| wishes[].created_at | string | 创建时间 |

**响应示例：**
```json
{
  "wishes": [
    {
      "id": 1,
      "user_id": 1,
      "username": "爸爸",
      "family_id": 1,
      "name": "机械键盘",
      "link": "https://example.com/keyboard",
      "note": "Cherry MX 茶轴",
      "created_at": "2026-06-04T10:00:00"
    },
    {
      "id": 2,
      "user_id": 2,
      "username": "妈妈",
      "family_id": 1,
      "name": "瑜伽垫",
      "link": "https://example.com/mat",
      "note": "加厚防滑款",
      "created_at": "2026-06-04T10:00:00"
    }
  ]
}
```

---

### POST /api/tasks/wishes — 添加心愿

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| name | string | ✅ | 心愿名称 | `"机械键盘"` |
| link | string | ❌ | 购买链接 | `"https://..."` |
| note | string | ❌ | 备注 | `"Cherry MX 茶轴"` |

**请求示例：**
```json
{
  "name": "机械键盘",
  "link": "https://example.com/keyboard",
  "note": "Cherry MX 茶轴"
}
```

**响应示例：**
```json
{
  "wish": {
    "id": 3,
    "user_id": 1,
    "username": "爸爸",
    "family_id": 1,
    "name": "机械键盘",
    "link": "https://example.com/keyboard",
    "note": "Cherry MX 茶轴",
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### PUT /api/tasks/wishes/{wish_id} — 更新心愿（仅限自己的）

**请求示例：**
```json
{
  "note": "Cherry MX 红轴，静音版"
}
```

**响应示例：**
```json
{
  "wish": {
    "id": 1,
    "user_id": 1,
    "username": "爸爸",
    "family_id": 1,
    "name": "机械键盘",
    "link": "https://example.com/keyboard",
    "note": "Cherry MX 红轴，静音版",
    "created_at": "2026-06-04T10:00:00"
  }
}
```

---

### DELETE /api/tasks/wishes/{wish_id} — 删除心愿（自己的或管理员）

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/tasks/wishes/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

## 七、笔记知识 /api/notes

---

### GET /api/notes/wiki — 家庭 Wiki

**需要 Token：** ✅

**请求参数（Query）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | ❌ | 搜索关键词（匹配标题和内容） |
| category | string | ❌ | 分类筛选 |
| page | int | ❌ | 页码，默认 1 |
| per_page | int | ❌ | 每页条数，默认 20 |

**请求示例：**
```bash
curl "http://0.0.0.0:417/api/notes/wiki?q=WiFi&category=家电" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| notes[] | array | 笔记列表 |
| notes[].id | int | 笔记 ID |
| notes[].family_id | int | 家庭 ID |
| notes[].author_id | int | 作者用户 ID |
| notes[].author_name | string | 作者昵称 |
| notes[].title | string | 标题 |
| notes[].content_md | string | 内容（Markdown 格式） |
| notes[].category | string | 分类，如 `"家电"`、`"急救"` |
| notes[].created_at | string | 创建时间 |
| notes[].updated_at | string | 更新时间 |
| total / page / pages | int | 分页信息 |

**响应示例：**
```json
{
  "notes": [
    {
      "id": 1,
      "family_id": 1,
      "author_id": 1,
      "author_name": "爸爸",
      "title": "WiFi 信息",
      "content_md": "**WiFi名称**: WarmHome\n**密码**: 12345678\n\n管理地址: http://192.168.1.1",
      "category": "家电",
      "created_at": "2026-06-04T10:00:00",
      "updated_at": "2026-06-04T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "pages": 1
}
```

---

### POST /api/notes/wiki — 创建笔记

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | ✅ | 标题 |
| content_md | string | ❌ | 内容，支持 Markdown |
| category | string | ❌ | 分类 |

**请求示例：**
```json
{
  "title": "急救电话",
  "content_md": "火警: 119\n急救: 120\n报警: 110\n\n小区物业: 8888-1234",
  "category": "急救"
}
```

**响应示例：**
```json
{
  "note": {
    "id": 3,
    "family_id": 1,
    "author_id": 1,
    "author_name": "爸爸",
    "title": "急救电话",
    "content_md": "火警: 119\n急救: 120\n报警: 110\n\n小区物业: 8888-1234",
    "category": "急救",
    "created_at": "2026-06-04T15:30:00",
    "updated_at": "2026-06-04T15:30:00"
  }
}
```

---

### PUT /api/notes/wiki/{note_id} — 更新笔记

所有字段可选，同创建接口。

**请求示例：**
```json
{
  "content_md": "**WiFi名称**: WarmHome\n**密码**: 12345678\n\n管理地址: http://192.168.1.1\n\n**注意**: 密码已修改"
}
```

**响应示例：**
```json
{
  "note": {
    "id": 1,
    "family_id": 1,
    "author_id": 1,
    "author_name": "爸爸",
    "title": "WiFi 信息",
    "content_md": "**WiFi名称**: WarmHome\n**密码**: 12345678\n\n管理地址: http://192.168.1.1\n\n**注意**: 密码已修改",
    "category": "家电",
    "created_at": "2026-06-04T10:00:00",
    "updated_at": "2026-06-04T15:30:00"
  }
}
```

---

### DELETE /api/notes/wiki/{note_id} — 删除笔记

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/notes/wiki/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

### GET /api/notes/recipes — 食谱

**请求参数：** `q`（搜索菜名）、`page`、`per_page`

**请求示例：**
```bash
curl "http://0.0.0.0:417/api/notes/recipes?q=番茄" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| recipes[] | array | 食谱列表 |
| recipes[].id | int | 食谱 ID |
| recipes[].family_id | int | 家庭 ID |
| recipes[].author_id | int | 作者用户 ID |
| recipes[].author_name | string | 作者昵称 |
| recipes[].name | string | 菜名 |
| recipes[].ingredients | string | 配料 |
| recipes[].steps | string | 步骤 |
| recipes[].image_url | string | 图片 URL |
| recipes[].created_at | string | 创建时间 |

**响应示例：**
```json
{
  "recipes": [
    {
      "id": 1,
      "family_id": 1,
      "author_id": 2,
      "author_name": "妈妈",
      "name": "番茄炒蛋",
      "ingredients": "番茄2个, 鸡蛋3个, 盐适量, 糖少许",
      "steps": "1. 鸡蛋打散加盐\n2. 番茄切块\n3. 先炒蛋出锅\n4. 炒番茄出汁后加入蛋翻炒",
      "image_url": "",
      "created_at": "2026-06-04T10:00:00"
    }
  ]
}
```

---

### POST /api/notes/recipes — 创建食谱

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| name | string | ✅ | 菜名 | `"番茄炒蛋"` |
| ingredients | string | ❌ | 配料 | `"番茄2个, 鸡蛋3个"` |
| steps | string | ❌ | 步骤 | `"1. 打蛋\n2. 切番茄"` |
| image_url | string | ❌ | 图片链接 | `""` |

**请求示例：**
```json
{
  "name": "番茄炒蛋",
  "ingredients": "番茄2个, 鸡蛋3个, 盐适量, 糖少许",
  "steps": "1. 鸡蛋打散加盐\n2. 番茄切块\n3. 先炒蛋出锅\n4. 炒番茄出汁后加入蛋翻炒",
  "image_url": ""
}
```

**响应示例：**
```json
{
  "recipe": {
    "id": 2,
    "family_id": 1,
    "author_id": 1,
    "author_name": "爸爸",
    "name": "番茄炒蛋",
    "ingredients": "番茄2个, 鸡蛋3个, 盐适量, 糖少许",
    "steps": "1. 鸡蛋打散加盐\n2. 番茄切块\n3. 先炒蛋出锅\n4. 炒番茄出汁后加入蛋翻炒",
    "image_url": "",
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### PUT /api/notes/recipes/{recipe_id} — 更新食谱

**请求示例：**
```json
{
  "steps": "1. 鸡蛋打散加盐\n2. 番茄切块\n3. 先炒蛋出锅\n4. 炒番茄出汁后加入蛋翻炒\n5. 出锅前加少许糖提鲜"
}
```

**响应示例：**
```json
{
  "recipe": {
    "id": 1,
    "family_id": 1,
    "author_id": 2,
    "author_name": "妈妈",
    "name": "番茄炒蛋",
    "ingredients": "番茄2个, 鸡蛋3个, 盐适量, 糖少许",
    "steps": "1. 鸡蛋打散加盐\n2. 番茄切块\n3. 先炒蛋出锅\n4. 炒番茄出汁后加入蛋翻炒\n5. 出锅前加少许糖提鲜",
    "image_url": "",
    "created_at": "2026-06-04T10:00:00"
  }
}
```

---

### DELETE /api/notes/recipes/{recipe_id} — 删除食谱

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/notes/recipes/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

### GET /api/notes/messages — 留言板

**请求示例：**
```bash
curl http://0.0.0.0:417/api/notes/messages \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| messages[] | array | 顶层留言列表（按时间倒序） |
| messages[].id | int | 留言 ID |
| messages[].family_id | int | 家庭 ID |
| messages[].author_id | int | 作者用户 ID |
| messages[].author_name | string | 作者昵称 |
| messages[].content | string | 留言内容 |
| messages[].parent_id | int \| null | 父留言 ID，null 表示顶层留言 |
| messages[].created_at | string | 创建时间 |
| messages[].reply_count | int | 回复数量 |
| messages[].replies[] | array | 回复列表（按时间正序） |
| messages[].replies[].id | int | 回复 ID |
| messages[].replies[].author_name | string | 回复者昵称 |
| messages[].replies[].content | string | 回复内容 |
| messages[].replies[].parent_id | int | 所回复的留言 ID |
| messages[].replies[].created_at | string | 回复时间 |

**响应示例：**
```json
{
  "messages": [
    {
      "id": 1,
      "family_id": 1,
      "author_id": 1,
      "author_name": "爸爸",
      "content": "晚上想吃什么？",
      "parent_id": null,
      "created_at": "2026-06-04T07:00:00",
      "reply_count": 2,
      "replies": [
        {
          "id": 2,
          "author_name": "妈妈",
          "content": "火锅怎么样？",
          "parent_id": 1,
          "created_at": "2026-06-04T08:00:00"
        },
        {
          "id": 3,
          "author_name": "小明",
          "content": "好耶！吃火锅！",
          "parent_id": 1,
          "created_at": "2026-06-04T09:00:00"
        }
      ]
    }
  ]
}
```

---

### POST /api/notes/messages — 发送留言/回复

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | ✅ | 留言内容 |
| parent_id | int | ❌ | 父留言 ID，不传=新留言，传值=回复该留言 |

**请求示例 — 新留言：**
```json
{
  "content": "明天记得买牛奶哦！"
}
```

**请求示例 — 回复留言：**
```json
{
  "content": "好的，我记下了！",
  "parent_id": 1
}
```

**响应示例：**
```json
{
  "message": {
    "id": 4,
    "family_id": 1,
    "author_id": 1,
    "author_name": "爸爸",
    "content": "明天记得买牛奶哦！",
    "parent_id": null,
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### DELETE /api/notes/messages/{msg_id} — 删除留言

**权限：** 作者或管理员

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/notes/messages/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

## 八、家庭相册 /api/album

---

### GET /api/album/albums — 相册列表

**需要 Token：** ✅

**请求示例：**
```bash
curl http://0.0.0.0:417/api/album/albums \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| albums[] | array | 相册列表 |
| albums[].id | int | 相册 ID |
| albums[].family_id | int | 家庭 ID |
| albums[].creator_id | int | 创建者用户 ID |
| albums[].creator_name | string | 创建者昵称 |
| albums[].name | string | 相册名称 |
| albums[].photo_count | int | 照片数量 |
| albums[].created_at | string | 创建时间 |

**响应示例：**
```json
{
  "albums": [
    {
      "id": 1,
      "family_id": 1,
      "creator_id": 1,
      "creator_name": "爸爸",
      "name": "家庭相册",
      "photo_count": 0,
      "created_at": "2026-06-04T10:00:00"
    }
  ]
}
```

---

### POST /api/album/albums — 创建相册

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 相册名称 |

**请求示例：**
```json
{
  "name": "旅行相册"
}
```

**响应示例：**
```json
{
  "album": {
    "id": 2,
    "family_id": 1,
    "creator_id": 1,
    "creator_name": "爸爸",
    "name": "旅行相册",
    "photo_count": 0,
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### DELETE /api/album/albums/{album_id} — 删除相册（含所有照片文件）

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/album/albums/2 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "相册已删除"
}
```

---

### GET /api/album/albums/{album_id}/photos — 获取照片列表

**请求示例：**
```bash
curl http://0.0.0.0:417/api/album/albums/1/photos \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| photos[] | array | 照片列表 |
| photos[].id | int | 照片 ID |
| photos[].album_id | int | 相册 ID |
| photos[].album_name | string | 相册名称 |
| photos[].uploader_id | int | 上传者用户 ID |
| photos[].uploader_name | string | 上传者昵称 |
| photos[].filename | string | 服务器文件名（UUID） |
| photos[].url | string | 访问路径，如 `"/uploads/abc123.jpg"` |
| photos[].description | string | 照片描述 |
| photos[].taken_at | string \| null | 拍摄时间 |
| photos[].upload_time | string | 上传时间 |
| photos[].comment_count | int | 评论数 |
| photos[].comments[] | array | 评论列表 |
| photos[].comments[].id | int | 评论 ID |
| photos[].comments[].photo_id | int | 照片 ID |
| photos[].comments[].user_id | int | 评论者用户 ID |
| photos[].comments[].username | string | 评论者昵称 |
| photos[].comments[].content | string | 评论内容 |
| photos[].comments[].created_at | string | 评论时间 |

**响应示例：**
```json
{
  "photos": [
    {
      "id": 1,
      "album_id": 1,
      "album_name": "家庭相册",
      "uploader_id": 1,
      "uploader_name": "爸爸",
      "filename": "abc123-def456.jpg",
      "url": "/uploads/abc123-def456.jpg",
      "description": "全家福",
      "taken_at": "2026-06-04T12:00:00",
      "upload_time": "2026-06-04T15:30:00",
      "comment_count": 1,
      "comments": [
        {
          "id": 1,
          "photo_id": 1,
          "user_id": 2,
          "username": "妈妈",
          "content": "拍得真好！",
          "created_at": "2026-06-04T16:00:00"
        }
      ]
    }
  ]
}
```

---

### POST /api/album/albums/{album_id}/photos — 上传照片

**Content-Type:** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| photos | file[] | ✅ | 图片文件，支持 png/jpg/jpeg/gif，最多 16MB |
| description | string | ❌ | 照片描述 |
| taken_at | string | ❌ | 拍摄时间 ISO 格式 |

**请求示例（curl）：**
```bash
curl -X POST http://0.0.0.0:417/api/album/albums/1/photos \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "photos=@photo1.jpg" \
  -F "photos=@photo2.jpg" \
  -F "description=全家福" \
  -F "taken_at=2026-06-04T12:00:00"
```

**成功响应 201：**

| 字段 | 类型 | 说明 |
|------|------|------|
| photos[] | array | 上传成功的照片列表 |
| msg | string | 如 `"上传了 2 张照片"` |

**响应示例：**
```json
{
  "photos": [
    {
      "id": 2,
      "album_id": 1,
      "filename": "uuid-photo-1.jpg",
      "url": "/uploads/uuid-photo-1.jpg",
      "description": "全家福",
      "taken_at": "2026-06-04T12:00:00",
      "upload_time": "2026-06-04T15:30:00"
    },
    {
      "id": 3,
      "album_id": 1,
      "filename": "uuid-photo-2.jpg",
      "url": "/uploads/uuid-photo-2.jpg",
      "description": "全家福",
      "taken_at": "2026-06-04T12:00:00",
      "upload_time": "2026-06-04T15:30:00"
    }
  ],
  "msg": "上传了 2 张照片"
}
```

---

### PUT /api/album/photos/{photo_id} — 更新照片描述

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| description | string | ❌ | 新描述 |

**请求示例：**
```json
{
  "description": "2026年全家福"
}
```

**响应示例：**
```json
{
  "photo": {
    "id": 1,
    "album_id": 1,
    "filename": "abc123-def456.jpg",
    "url": "/uploads/abc123-def456.jpg",
    "description": "2026年全家福",
    "taken_at": "2026-06-04T12:00:00",
    "upload_time": "2026-06-04T15:30:00"
  }
}
```

---

### DELETE /api/album/photos/{photo_id} — 删除照片

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/album/photos/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "照片已删除"
}
```

---

### POST /api/album/photos/{photo_id}/comments — 添加评论

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | ✅ | 评论内容 |

**请求示例：**
```json
{
  "content": "拍得真好！"
}
```

**成功响应 201：** `{"comment": {...}}`

**响应示例：**
```json
{
  "comment": {
    "id": 2,
    "photo_id": 1,
    "user_id": 2,
    "username": "妈妈",
    "content": "拍得真好！",
    "created_at": "2026-06-04T16:00:00"
  }
}
```

---

## 九、文件柜 /api/files

---

### GET /api/files/folders — 文件夹列表

**需要 Token：** ✅

**请求示例：**
```bash
curl http://0.0.0.0:417/api/files/folders \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| folders[] | array | 文件夹列表 |
| folders[].id | int | 文件夹 ID |
| folders[].family_id | int | 家庭 ID |
| folders[].name | string | 文件夹名称 |
| folders[].file_count | int | 文件数量 |
| folders[].created_at | string | 创建时间 |

**响应示例：**
```json
{
  "folders": [
    {
      "id": 1,
      "family_id": 1,
      "name": "医疗",
      "file_count": 0,
      "created_at": "2026-06-04T10:00:00"
    },
    {
      "id": 2,
      "family_id": 1,
      "name": "教育",
      "file_count": 0,
      "created_at": "2026-06-04T10:00:00"
    },
    {
      "id": 3,
      "family_id": 1,
      "name": "合同",
      "file_count": 0,
      "created_at": "2026-06-04T10:00:00"
    }
  ]
}
```

---

### POST /api/files/folders — 创建文件夹

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 文件夹名称 |

**请求示例：**
```json
{
  "name": "保险"
}
```

**响应示例：**
```json
{
  "folder": {
    "id": 4,
    "family_id": 1,
    "name": "保险",
    "file_count": 0,
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### DELETE /api/files/folders/{folder_id} — 删除文件夹（含所有文件）

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/files/folders/3 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "文件夹已删除"
}
```

---

### GET /api/files/folders/{folder_id}/files — 获取文件列表

**请求示例：**
```bash
curl http://0.0.0.0:417/api/files/folders/1/files \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| files[] | array | 文件列表 |
| files[].id | int | 文件 ID |
| files[].folder_id | int | 文件夹 ID |
| files[].folder_name | string | 文件夹名称 |
| files[].uploader_id | int | 上传者用户 ID |
| files[].uploader_name | string | 上传者昵称 |
| files[].filename | string | 服务器文件名（UUID） |
| files[].original_name | string | 原始文件名 |
| files[].size | int | 文件大小（字节） |
| files[].url | string | 访问路径 `/uploads/xxx` |
| files[].upload_time | string | 上传时间 |

**响应示例：**
```json
{
  "files": [
    {
      "id": 1,
      "folder_id": 1,
      "folder_name": "医疗",
      "uploader_id": 1,
      "uploader_name": "爸爸",
      "filename": "uuid-file-1.pdf",
      "original_name": "体检报告.pdf",
      "size": 1024000,
      "url": "/uploads/uuid-file-1.pdf",
      "upload_time": "2026-06-04T15:30:00"
    }
  ]
}
```

---

### POST /api/files/folders/{folder_id}/files — 上传文件

**Content-Type:** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| files | file[] | ✅ | 文件，支持 png/jpg/jpeg/gif/pdf/doc/docx/xls/xlsx/txt/zip |

**请求示例（curl）：**
```bash
curl -X POST http://0.0.0.0:417/api/files/folders/1/files \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "files=@report.pdf" \
  -F "files=@contract.docx"
```

**成功响应 201：**

| 字段 | 类型 | 说明 |
|------|------|------|
| files[] | array | 上传成功的文件列表 |
| msg | string | 如 `"上传了 2 个文件"` |

**响应示例：**
```json
{
  "files": [
    {
      "id": 2,
      "folder_id": 1,
      "filename": "uuid-file-2.pdf",
      "original_name": "report.pdf",
      "size": 2048000,
      "url": "/uploads/uuid-file-2.pdf",
      "upload_time": "2026-06-04T15:30:00"
    },
    {
      "id": 3,
      "folder_id": 1,
      "filename": "uuid-file-3.docx",
      "original_name": "contract.docx",
      "size": 512000,
      "url": "/uploads/uuid-file-3.docx",
      "upload_time": "2026-06-04T15:30:00"
    }
  ],
  "msg": "上传了 2 个文件"
}
```

---

### DELETE /api/files/files/{file_id} — 删除文件

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/files/files/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "文件已删除"
}
```

---

## 十、记账本 /api/finance

---

### GET /api/finance/transactions — 收支记录

**需要 Token：** ✅

**请求参数（Query）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| month | string | ❌ | 月份筛选，格式 `YYYY-MM` |
| type | string | ❌ | 类型筛选：`income`/`expense` |
| category | string | ❌ | 分类筛选 |
| page | int | ❌ | 页码 |
| per_page | int | ❌ | 每页条数 |

**请求示例：**
```bash
curl "http://0.0.0.0:417/api/finance/transactions?month=2026-06&type=expense" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| transactions[] | array | 记录列表 |
| transactions[].id | int | 记录 ID |
| transactions[].family_id | int | 家庭 ID |
| transactions[].user_id | int | 记录者用户 ID |
| transactions[].username | string | 记录者昵称 |
| transactions[].type | string | 类型：`income`/`expense` |
| transactions[].category | string | 分类，如 `"餐饮"`、`"购物"` |
| transactions[].amount | float | 金额 |
| transactions[].note | string | 备注 |
| transactions[].date | string | 日期 `YYYY-MM-DD` |
| transactions[].created_at | string | 创建时间 |
| summary.income | float | 收入合计 |
| summary.expense | float | 支出合计 |
| summary.balance | float | 结余（收入-支出） |
| by_category[] | array | 按分类统计 |
| by_category[].category | string | 分类名 |
| by_category[].amount | float | 该分类总金额 |
| total / page / pages | int | 分页信息 |

**响应示例：**
```json
{
  "transactions": [
    {
      "id": 1,
      "family_id": 1,
      "user_id": 1,
      "username": "爸爸",
      "type": "expense",
      "category": "餐饮",
      "amount": 128.5,
      "note": "周末外出吃饭",
      "date": "2026-06-02",
      "created_at": "2026-06-02T20:00:00"
    },
    {
      "id": 2,
      "family_id": 1,
      "user_id": 2,
      "username": "妈妈",
      "type": "expense",
      "category": "购物",
      "amount": 350.0,
      "note": "超市采购",
      "date": "2026-06-03",
      "created_at": "2026-06-03T15:00:00"
    },
    {
      "id": 3,
      "family_id": 1,
      "user_id": 1,
      "username": "爸爸",
      "type": "income",
      "category": "工资",
      "amount": 15000.0,
      "note": "月薪",
      "date": "2026-06-04",
      "created_at": "2026-06-04T10:00:00"
    }
  ],
  "summary": {
    "income": 15000.0,
    "expense": 478.5,
    "balance": 14521.5
  },
  "by_category": [
    {
      "category": "餐饮",
      "amount": 128.5
    },
    {
      "category": "购物",
      "amount": 350.0
    }
  ],
  "total": 3,
  "page": 1,
  "pages": 1
}
```

---

### POST /api/finance/transactions — 创建收支记录

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| type | string | ✅ | 类型 | `"expense"` 或 `"income"` |
| amount | float | ✅ | 金额，必须大于 0 | `128.5` |
| category | string | ❌ | 分类，默认 `"其他"` | `"餐饮"` |
| date | string | ❌ | 日期 `YYYY-MM-DD`，默认今天 | `"2026-06-01"` |
| note | string | ❌ | 备注 | `"周末外出吃饭"` |

**请求示例：**
```json
{
  "type": "expense",
  "amount": 128.5,
  "category": "餐饮",
  "date": "2026-06-04",
  "note": "周末外出吃饭"
}
```

**响应示例：**
```json
{
  "transaction": {
    "id": 4,
    "family_id": 1,
    "user_id": 1,
    "username": "爸爸",
    "type": "expense",
    "category": "餐饮",
    "amount": 128.5,
    "note": "周末外出吃饭",
    "date": "2026-06-04",
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### PUT /api/finance/transactions/{tx_id} — 更新记录

所有字段可选，同创建接口。

**请求示例：**
```json
{
  "amount": 150.0,
  "note": "周末外出吃饭（含酒水）"
}
```

**响应示例：**
```json
{
  "transaction": {
    "id": 1,
    "family_id": 1,
    "user_id": 1,
    "username": "爸爸",
    "type": "expense",
    "category": "餐饮",
    "amount": 150.0,
    "note": "周末外出吃饭（含酒水）",
    "date": "2026-06-02",
    "created_at": "2026-06-02T20:00:00"
  }
}
```

---

### DELETE /api/finance/transactions/{tx_id} — 删除记录

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/finance/transactions/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

### GET /api/finance/bills — 账单提醒

**请求示例：**
```bash
curl http://0.0.0.0:417/api/finance/bills \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| bills[] | array | 账单列表 |
| bills[].id | int | 账单 ID |
| bills[].family_id | int | 家庭 ID |
| bills[].creator_id | int | 创建者用户 ID |
| bills[].title | string | 账单名称 |
| bills[].amount | float | 金额 |
| bills[].due_day | int | 每月到期日 1-31 |
| bills[].last_reminded | string \| null | 上次提醒日期 |
| bills[].days_until_due | int | 距离下次到期还有几天 |

**响应示例：**
```json
{
  "bills": [
    {
      "id": 1,
      "family_id": 1,
      "creator_id": 1,
      "title": "房租",
      "amount": 3500.0,
      "due_day": 1,
      "last_reminded": null,
      "days_until_due": 27
    },
    {
      "id": 2,
      "family_id": 1,
      "creator_id": 1,
      "title": "网费",
      "amount": 99.0,
      "due_day": 15,
      "last_reminded": null,
      "days_until_due": 11
    }
  ]
}
```

---

### POST /api/finance/bills — 创建账单

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| title | string | ✅ | 账单名称 | `"房租"` |
| amount | float | ❌ | 金额，默认 0 | `3500.0` |
| due_day | int | ❌ | 到期日 1-31，默认 1 | `15` |

**请求示例：**
```json
{
  "title": "房租",
  "amount": 3500.0,
  "due_day": 1
}
```

**响应示例：**
```json
{
  "bill": {
    "id": 3,
    "family_id": 1,
    "creator_id": 1,
    "title": "房租",
    "amount": 3500.0,
    "due_day": 1,
    "last_reminded": null,
    "days_until_due": 27
  }
}
```

---

### PUT /api/finance/bills/{bill_id} — 更新账单

**请求示例：**
```json
{
  "amount": 3600.0
}
```

**响应示例：**
```json
{
  "bill": {
    "id": 1,
    "family_id": 1,
    "creator_id": 1,
    "title": "房租",
    "amount": 3600.0,
    "due_day": 1,
    "last_reminded": null,
    "days_until_due": 27
  }
}
```

---

### DELETE /api/finance/bills/{bill_id} — 删除账单

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/finance/bills/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

## 十一、位置共享 /api/location

---

### POST /api/location/report — 上报位置

**需要 Token：** ✅

**请求参数：**

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| latitude | float | ✅ | 纬度，范围 -90 到 90 | `39.9042` |
| longitude | float | ✅ | 经度，范围 -180 到 180 | `116.4074` |

**说明：** 已有位置则更新，没有则创建（upsert）

**请求示例：**
```json
{
  "latitude": 39.9042,
  "longitude": 116.4074
}
```

**成功响应 200：** `{"location": {...}}`

**响应示例：**
```json
{
  "location": {
    "id": 1,
    "user_id": 1,
    "latitude": 39.9042,
    "longitude": 116.4074,
    "timestamp": "2026-06-04T15:30:00"
  }
}
```

---

### GET /api/location/members — 获取所有成员位置

**请求示例：**
```bash
curl http://0.0.0.0:417/api/location/members \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| members[] | array | 成员列表 |
| members[].user_id | int | 用户 ID |
| members[].username | string | 昵称 |
| members[].role | string | 角色 |
| members[].avatar_url | string | 头像 URL |
| members[].location | object \| null | 位置信息，null 表示未上报 |
| members[].location.id | int | 位置记录 ID |
| members[].location.latitude | float | 纬度 |
| members[].location.longitude | float | 经度 |
| members[].location.timestamp | string | 上报时间 |

**响应示例：**
```json
{
  "members": [
    {
      "user_id": 1,
      "username": "爸爸",
      "role": "admin",
      "avatar_url": "",
      "location": {
        "id": 1,
        "latitude": 39.9042,
        "longitude": 116.4074,
        "timestamp": "2026-06-04T15:30:00"
      }
    },
    {
      "user_id": 2,
      "username": "妈妈",
      "role": "adult",
      "avatar_url": "",
      "location": {
        "id": 2,
        "latitude": 39.9088,
        "longitude": 116.3974,
        "timestamp": "2026-06-04T15:25:00"
      }
    },
    {
      "user_id": 3,
      "username": "小明",
      "role": "child",
      "avatar_url": "",
      "location": null
    }
  ]
}
```

---

### GET /api/location/my-history — 获取自己的位置

**请求示例：**
```bash
curl http://0.0.0.0:417/api/location/my-history \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：** `{"location": {...}}` 或 `{"location": null}`

**响应示例：**
```json
{
  "location": {
    "id": 1,
    "user_id": 1,
    "latitude": 39.9042,
    "longitude": 116.4074,
    "timestamp": "2026-06-04T15:30:00"
  }
}
```

**成功响应 200：** `{"location": {...}}` 或 `{"location": null}`

---

## 十二、健康档案 /api/health

---

### GET /api/health/records — 健康记录

**需要 Token：** ✅

**请求参数（Query）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | int | ❌ | 按成员筛选 |
| record_type | string | ❌ | 按类型筛选 |
| page | int | ❌ | 页码 |
| per_page | int | ❌ | 每页条数 |

**请求示例：**
```bash
curl "http://0.0.0.0:417/api/health/records?user_id=1&record_type=weight" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| records[] | array | 记录列表 |
| records[].id | int | 记录 ID |
| records[].user_id | int | 成员用户 ID |
| records[].username | string | 成员昵称 |
| records[].family_id | int | 家庭 ID |
| records[].record_type | string | 记录类型：`height`/`weight`/`blood_pressure`/`vaccine`/`other` |
| records[].value | string | 数值，如 `"75"`、`"120/80"` |
| records[].unit | string | 单位，如 `"kg"`、`"cm"`、`"mmHg"` |
| records[].record_date | string | 记录日期 `YYYY-MM-DD` |
| records[].note | string | 备注 |
| records[].created_at | string | 创建时间 |
| total / page / pages | int | 分页信息 |

**响应示例：**
```json
{
  "records": [
    {
      "id": 1,
      "user_id": 1,
      "username": "爸爸",
      "family_id": 1,
      "record_type": "weight",
      "value": "75",
      "unit": "kg",
      "record_date": "2026-06-04",
      "note": "",
      "created_at": "2026-06-04T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "pages": 1
}
```

---

### POST /api/health/records — 创建健康记录

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| record_type | string | ✅ | 记录类型 | `"weight"` |
| value | string | ✅ | 数值 | `"75"` |
| user_id | int | ❌ | 成员用户 ID，默认当前用户 | `1` |
| unit | string | ❌ | 单位 | `"kg"` |
| record_date | string | ❌ | 日期 `YYYY-MM-DD`，默认今天 | `"2026-06-03"` |
| note | string | ❌ | 备注 | `""` |

**请求示例：**
```json
{
  "record_type": "weight",
  "value": "75",
  "user_id": 1,
  "unit": "kg",
  "record_date": "2026-06-04",
  "note": ""
}
```

**响应示例：**
```json
{
  "record": {
    "id": 2,
    "user_id": 1,
    "username": "爸爸",
    "family_id": 1,
    "record_type": "weight",
    "value": "75",
    "unit": "kg",
    "record_date": "2026-06-04",
    "note": "",
    "created_at": "2026-06-04T15:30:00"
  }
}
```

---

### PUT /api/health/records/{record_id} — 更新记录

**请求示例：**
```json
{
  "value": "76",
  "note": "体重增加"
}
```

**响应示例：**
```json
{
  "record": {
    "id": 1,
    "user_id": 1,
    "username": "爸爸",
    "family_id": 1,
    "record_type": "weight",
    "value": "76",
    "unit": "kg",
    "record_date": "2026-06-04",
    "note": "体重增加",
    "created_at": "2026-06-04T10:00:00"
  }
}
```

---

### DELETE /api/health/records/{record_id} — 删除记录

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/health/records/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

### GET /api/health/pets — 宠物列表

**请求示例：**
```bash
curl http://0.0.0.0:417/api/health/pets \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应 200：**

| 字段 | 类型 | 说明 |
|------|------|------|
| pets[] | array | 宠物列表 |
| pets[].id | int | 宠物 ID |
| pets[].family_id | int | 家庭 ID |
| pets[].name | string | 宠物名字 |
| pets[].species | string | 品种 |
| pets[].deworming_date | string \| null | 驱虫日期 `YYYY-MM-DD` |
| pets[].vaccine_date | string \| null | 疫苗日期 `YYYY-MM-DD` |
| pets[].note | string | 备注 |
| pets[].created_at | string | 创建时间 |
| pets[].deworming_soon | bool | 驱虫是否 7 天内到期 |
| pets[].vaccine_soon | bool | 疫苗是否 7 天内到期 |

**响应示例：**
```json
{
  "pets": [
    {
      "id": 1,
      "family_id": 1,
      "name": "毛球",
      "species": "英短蓝猫",
      "deworming_date": "2026-07-04",
      "vaccine_date": "2026-08-03",
      "note": "活泼好动",
      "created_at": "2026-06-04T10:00:00",
      "deworming_soon": false,
      "vaccine_soon": false
    }
  ]
}
```

---

### POST /api/health/pets — 创建宠物

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| name | string | ✅ | 宠物名字 | `"毛球"` |
| species | string | ❌ | 品种 | `"英短蓝猫"` |
| deworming_date | string | ❌ | 驱虫日期 `YYYY-MM-DD` | `"2026-07-03"` |
| vaccine_date | string | ❌ | 疫苗日期 `YYYY-MM-DD` | `"2026-08-02"` |
| note | string | ❌ | 备注 | `"活泼好动"` |

**请求示例：**
```json
{
  "name": "毛球",
  "species": "英短蓝猫",
  "deworming_date": "2026-07-04",
  "vaccine_date": "2026-08-03",
  "note": "活泼好动"
}
```

**响应示例：**
```json
{
  "pet": {
    "id": 2,
    "family_id": 1,
    "name": "毛球",
    "species": "英短蓝猫",
    "deworming_date": "2026-07-04",
    "vaccine_date": "2026-08-03",
    "note": "活泼好动",
    "created_at": "2026-06-04T15:30:00",
    "deworming_soon": false,
    "vaccine_soon": false
  }
}
```

---

### PUT /api/health/pets/{pet_id} — 更新宠物

**请求示例：**
```json
{
  "deworming_date": "2026-08-04",
  "note": "已驱虫，状态良好"
}
```

**响应示例：**
```json
{
  "pet": {
    "id": 1,
    "family_id": 1,
    "name": "毛球",
    "species": "英短蓝猫",
    "deworming_date": "2026-08-04",
    "vaccine_date": "2026-08-03",
    "note": "已驱虫，状态良好",
    "created_at": "2026-06-04T10:00:00",
    "deworming_soon": false,
    "vaccine_soon": false
  }
}
```

---

### DELETE /api/health/pets/{pet_id} — 删除宠物

**请求示例：**
```bash
curl -X DELETE http://0.0.0.0:417/api/health/pets/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例：**
```json
{
  "msg": "已删除"
}
```

---

## 十三、通用响应格式

### 成功响应

```json
{
  "字段名": 数据
}
```

### 错误响应

```json
{
  "msg": "错误描述"
}
```

### HTTP 状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 201 | 已创建 |
| 400 | 请求参数错误 |
| 401 | 未认证（Token 缺失/过期/无效） |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 冲突（重复数据） |
| 413 | 请求体过大（>16MB） |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

---

## 十四、调用示例

### curl 完整流程

```bash
# 1. 登录获取 Token
curl -X POST http://0.0.0.0:417/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 响应: {"access_token":"eyJhbG...","user":{...}}

# 2. 保存 Token 到变量
TOKEN="eyJhbG..."

# 3. 调用需要认证的接口
curl http://0.0.0.0:417/api/family/info \
  -H "Authorization: Bearer $TOKEN"

# 4. 创建数据
curl -X POST http://0.0.0.0:417/api/tasks/chores \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"倒垃圾","due_date":"2026-06-05"}'

# 5. 上传文件
curl -X POST http://0.0.0.0:417/api/files/folders/1/files \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@report.pdf"
```

### Python 完整流程

```python
import requests

BASE = "http://0.0.0.0:417"

# 1. 登录
r = requests.post(f"{BASE}/api/auth/login", json={
    "username": "admin",
    "password": "admin123"
})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. 获取家庭信息
r = requests.get(f"{BASE}/api/family/info", headers=headers)
print(r.json())

# 3. 创建日历事件
r = requests.post(f"{BASE}/api/calendar/events", headers=headers, json={
    "title": "家庭聚餐",
    "start": "2026-06-05T10:00:00",
    "end": "2026-06-05T12:00:00",
})
print(r.json())

# 4. 上传照片
with open("photo.jpg", "rb") as f:
    r = requests.post(
        f"{BASE}/api/album/albums/1/photos",
        headers={"Authorization": f"Bearer {token}"},
        files={"photos": f},
        data={"description": "全家福"}
    )
print(r.json())
```

### JavaScript 完整流程

```javascript
const BASE = "http://0.0.0.0:417";

// 1. 登录
const loginRes = await fetch(`${BASE}/api/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "admin", password: "admin123" })
});
const { access_token } = await loginRes.json();

// 2. 封装请求头
const authHeaders = {
  "Content-Type": "application/json",
  "Authorization": `Bearer ${access_token}`
};

// 3. 调用接口
const family = await (await fetch(`${BASE}/api/family/info`, {
  headers: authHeaders
})).json();
console.log(family);

// 4. 上传文件
const formData = new FormData();
formData.append("photos", fileInput.files[0]);
await fetch(`${BASE}/api/album/albums/1/photos`, {
  method: "POST",
  headers: { "Authorization": `Bearer ${access_token}` },
  body: formData
});
```
