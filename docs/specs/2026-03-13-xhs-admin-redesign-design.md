# 小红书Agent 管理后台重设计 — 设计规格

> 日期：2026-03-13
> 项目路径：`/Volumes/4T固态/Claude Code Text/小红书/demo/`
> 状态：设计完成，待实施
> 前置依赖：UI 全面重设计（2026-03-12）已完成验收

---

## 1. 背景与问题

当前管理后台存在两类问题：

### 1.1 侧边栏臃肿

- 「用户须知与免责声明」占用大量空间（~30行长文本），用 `st.expander` 展开后几乎填满侧边栏
- 意见反馈表单（文本框 + 评分滑块 + 按钮）展开后也很长
- 整体缺乏层次感，功能入口和展示信息混杂

### 1.2 管理面板无独立视图

- 管理面板（~330 行代码）直接放在主页面底部，管理员需要滚过全部内容生成区才能看到
- 使用默认 `st.metric` 指标卡片，与已重设计的 Apple 克制风不统一
- 事件日志只显示邀请码，无法直观看到哪个用户在什么时间做了什么操作

## 2. 设计目标

- 管理后台从主页面分离为**独立视图**，通过 `st.session_state` 切换
- 侧边栏**精简重组**，保留核心功能，长内容改为链接
- 管理页面视觉风格与已完成的 Apple 克制风 UI 重设计**完全统一**
- 混合使用自定义 HTML 指标卡片 + Streamlit 原生图表/表格

## 3. 设计系统

沿用 UI 重设计中的 Design Tokens（`2026-03-12-xhs-ui-redesign-design.md` 第3节），不新增 token。

关键 token 速查：

| Token | 值 | 用途 |
|-------|------|------|
| `--bg-secondary` | `#f5f5f7` | 卡片背景 |
| `--bg-selected` | `#fff1f3` | 管理后台入口高亮 |
| `--text-primary` | `#1d1d1f` | 主文字 |
| `--text-secondary` | `#86868b` | 副文字、英文标签 |
| `--text-tertiary` | `#c7c7cc` | 版本号等 |
| `--accent` | `#ff2442` | 活跃 Tab、按钮 |
| `--success` | `#34c759` | 成功/健康指标 |
| `--divider` | `#f0f0f0` | 分割线 |

## 4. 侧边栏重设计

### 4.1 现有元素处理

侧边栏元素**从上到下**排列顺序：

| 序号 | 元素 | 处理方式 | 说明 |
|------|------|----------|------|
| 1 | 欢迎信息（手机号+邀请码） | **保留** | 管理员视图显示完整手机号 |
| 2 | 📊 管理后台入口 | **新增**（仅管理员） | 粉色高亮按钮，紧跟欢迎信息下方 |
| 3 | 所在城市输入 | **保留** | 文本输入框 + 确认提示 |
| 4 | 会员额度显示 | **保留** | 额度条 + 状态色 |
| 5 | 📜 历史记录 | **保留** | 保持现有 `st.button` + session_state 展开逻辑不变 |
| 6 | 📝 意见反馈 | **保留** | 保持现有 `st.expander` 折叠表单不变 |
| 7 | 📋 用户须知与免责声明 | **改为链接** | 一行文字，不再 expander 展开长文 |
| 8 | 退出登录 | **保留** | 底部按钮 |
| 9 | 版本号 | **保留** | `Demo v5.0 · 内测版` |

### 4.2 管理后台入口按钮

仅当 `st.session_state.invite_code in ADMIN_CODES` 时显示：

```
┌─────────────────────────────┐
│ 📊  管理后台              → │
│   背景: #fff1f3              │
│   文字: #ff2442, 600        │
│   圆角: 10px                │
└─────────────────────────────┘
```

点击后设置 `st.session_state.admin_view = True`，主页面切换为管理视图。管理视图中，侧边栏同位置的按钮变为「← 返回内容生成」（点击后 `admin_view = False`）。

### 4.3 用户须知处理

将完整免责声明文本移至单独页面或 dialog，侧边栏只保留一行：

```
用户须知 · 免责声明
```

字号 11px，颜色 `--text-tertiary`，居中对齐。点击后使用 `st.expander` 展示完整文本（不使用 `st.dialog`，避免 Streamlit 版本兼容问题）。

## 5. 管理后台独立视图

### 5.1 页面切换机制

```python
# 新增 session_state 变量
if "admin_view" not in st.session_state:
    st.session_state.admin_view = False

# 主页面逻辑
if st.session_state.admin_view and st.session_state.invite_code in ADMIN_CODES:
    render_admin_panel()  # 独立管理视图
else:
    # 原有内容生成流程（不变）
    ...
```

### 5.2 页头

```
┌──────────────────────────────────────┐
│  ADMIN                               │
│  （标签：14px, 600, #ff2442,          │
│    背景 #fff1f3, 圆角 4px）           │
│                                      │
│  数据分析                             │
│  （22px, 600, #1d1d1f）              │
│                                      │
│  Analytics Dashboard                  │
│  （13px, 400, #86868b）              │
└──────────────────────────────────────┘
```

### 5.3 指标卡片（自定义 HTML）

替换现有 `st.metric`，使用自定义 HTML 卡片，风格与主页面统一：

```
┌──────────┐ ┌──────────┐ ┌──────────┐
│ 总用户    │ │ 总生成    │ │ 今日      │
│ Users    │ │ Generated│ │ Today    │
│          │ │          │ │          │
│    42    │ │   186    │ │    7     │
│ (28px)   │ │ (28px)   │ │(28px红)  │
└──────────┘ └──────────┘ └──────────┘

┌──────────┐ ┌──────────┐ ┌──────────┐
│ 近7日     │ │ 提取成功率│ │ 反馈      │
│ 7-Day    │ │ Rate     │ │ Feedback │
│          │ │          │ │          │
│    28    │ │   87%    │ │    12    │
│ (28px)   │ │(28px绿)  │ │ (28px)   │
└──────────┘ └──────────┘ └──────────┘
```

卡片样式：
- 背景：`#f5f5f7`
- 圆角：14px
- 内边距：16px
- 标签：11px, `--text-secondary`，中英双语
- 数值：28px, 600, `--text-primary`（特殊：今日用 `--accent`，成功率用 `--success`）

### 5.4 图表区域（Streamlit 原生）

保留现有 Streamlit 原生图表，不用自定义 HTML：
- **每日生成趋势**：`st.line_chart`
- **行业热度排行**：`st.bar_chart`
- **模式分布**：`st.bar_chart`
- **图片档位分布**：`st.bar_chart`
- **每小时活跃**：`st.bar_chart`

图表区域标题使用统一风格：
- 中文标题：14px, 600, `--text-primary`
- 英文副标题：11px, 400, `--text-secondary`

### 5.5 Tab 式模块切换

用胶囊形 Tab 切换管理子模块，替代当前的线性排列：

```
┌─────────────────────────────────────────────────────┐
│ [👥 用户]  [🏆 行业]  [💰 充值]  [💬 反馈]  [🔍 日志] │
└─────────────────────────────────────────────────────┘
```

Tab 样式：
- 字号：15px
- 内边距：10px 22px
- 圆角：24px
- 活跃 Tab：背景 `--accent`，白色文字，600 字重
- 非活跃 Tab：背景 `#f5f5f7`，`--text-primary` 文字，500 字重
- 间距：10px

实现方式：使用 Streamlit `st.tabs`，通过 CSS 覆盖 `.stTabs [data-baseweb="tab-list"]` 和 `.stTabs [data-baseweb="tab"]` 样式为胶囊形（去除下划线、加圆角背景）。

### 5.6 各 Tab 内容

#### Tab 1: 👥 用户

- 注册用户列表（`st.dataframe`）
- 用户活跃排行（`st.dataframe`）
- 会员配额使用（`st.dataframe`）
- **手机号显示完整号码**（不掩码），供管理员查看

#### Tab 2: 🏆 行业

- 行业热度排行（`st.bar_chart`）
- 模式分布（`st.bar_chart`）
- 图片档位分布（`st.bar_chart`）
- 自定义行业使用统计（`st.dataframe`）

#### Tab 3: 💰 充值

- 充值管理表单（现有 `admin_recharge_form` 保留）
- 会员配额使用概览

#### Tab 4: 💬 反馈

- 最近反馈列表（`st.dataframe`）

#### Tab 5: 🔍 日志

- 事件日志表格（`st.dataframe`）
- **字段增强**：
  - 手机号：显示完整手机号（关联 users 表查询），不再只显示邀请码
  - 时间：精确到秒（`YYYY-MM-DD HH:MM:SS`），不再截断到分钟
  - 操作：事件类型中文化显示（如 `login` → `登录`，`generate` → `生成文案`，`extract_link` → `提取链接`）
- 每小时活跃分布图

### 5.7 日志事件类型中文映射

```python
EVENT_TYPE_LABELS = {
    "login": "登录",
    "generate": "生成文案",
    "extract_link": "提取链接",
    "feedback": "提交反馈",
    "admin_recharge": "管理员充值",
    "view_history": "查看历史",
    "reuse_history": "复用历史文案",
}
```

## 6. 数据查询

所有数据查询逻辑保持不变，仅调整展示层：
- 查询在独立管理视图函数中执行
- 数据库连接在函数内打开/关闭（现有 `get_db()` 模式）
- 不新增表或字段

日志查询增强 — 关联 users 表获取手机号：

```sql
SELECT e.*, COALESCE(u.phone, '—') as phone
FROM event_log e
LEFT JOIN users u ON e.invite_code = u.invite_code
ORDER BY e.created_at DESC
LIMIT 50
```

## 7. 不变的部分

- 所有业务逻辑和数据流不变
- 数据库结构不变
- 普通用户的内容生成流程不变
- 登录/注册逻辑不变
- 图表使用 Streamlit 原生组件（`st.line_chart`, `st.bar_chart`, `st.dataframe`）

## 8. Streamlit 实现约束

- 使用 `st.markdown(unsafe_allow_html=True)` 注入自定义 HTML/CSS（指标卡片、页头）
- 图表和表格使用 Streamlit 原生组件，不自定义
- Tab 使用 `st.tabs`，通过 CSS 覆盖样式
- 不使用 `st.dialog`（版本兼容考虑），用户须知保留 `st.expander`
- 页面切换通过 `st.session_state.admin_view` 布尔值控制
- CSS 变量沿用已注入的 `:root` design tokens（UI 重设计已实现）

## 9. 实施范围

仅修改 `app.py` 一个文件，涉及三个区域：

| 区域 | 说明 | 改动 |
|------|------|------|
| 侧边栏区域 | `with st.sidebar:` 代码块 | 精简重组，新增管理后台入口按钮，用户须知从 expander 改为一行链接 |
| 主页面分支 | 侧边栏之后、内容生成流程之前 | 新增 `admin_view` 分支判断，管理视图调用独立函数 |
| 管理面板区域 | 当前位于文件底部的管理后台代码 | 提取为 `render_admin_panel()` 独立函数，重写 UI 层（自定义指标卡片 + Tab 切换） |

预计新增代码：~80 行（管理视图函数头 + Tab 切换 + HTML 卡片模板）
预计减少代码：~50 行（侧边栏长文本移除、`st.metric` 替换为统一模板）
