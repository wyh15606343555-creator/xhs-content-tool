# 小红书Agent UI 全面重设计 — 设计规格

> 日期：2026-03-12
> 项目路径：`/Volumes/4T固态/Claude Code Text/小红书/demo/`
> 状态：设计完成，待实施

---

## 1. 背景与问题

当前 UI 存在以下问题：

1. **登录页简陋**：渐变圆球 Logo、尖括号标题、技术化副标题，缺乏品牌识别度
2. **行业选择卡片粗糙**：有边框、需要点两次（预览→确认）、描述文字冗余
3. **模式选择信息过载**：两张大卡片塞满功能清单，像说明书不像产品
4. **内容生成区域混乱**：4 个步骤线性排列页面过长，步骤间无进度感，标题/正文两列挤在一起
5. **整体配色/间距不够精致**：边框过多、渐变过重、间距不统一

## 2. 设计目标

- **Apple 克制风** + 国际化：白底 + `#f5f5f7` 灰色卡片，中英双语，小红书红仅作克制点缀
- 面向混合用户群（商家运营 + 个体博主），兼顾专业感和易用性
- 参考 Notion/Linear 的极简排版：大量留白、清晰层次、无多余装饰
- 不改变业务逻辑和数据流，仅改 UI 层

## 3. 设计系统（Design Tokens）

### 3.1 颜色

| Token | 值 | 用途 |
|-------|------|------|
| `--bg-primary` | `#ffffff` | 页面背景 |
| `--bg-secondary` | `#f5f5f7` | 卡片背景、输入框背景 |
| `--bg-selected` | `#fff1f3` | 选中状态背景 |
| `--text-primary` | `#1d1d1f` | 主文字 |
| `--text-secondary` | `#86868b` | 副文字、英文标签 |
| `--text-tertiary` | `#c7c7cc` | 占位文字、禁用状态 |
| `--accent` | `#ff2442` | 主强调色（按钮、选中边框、Step标签） |
| `--accent-orange` | `#ff8c00` | 原创模式强调色 |
| `--success` | `#34c759` | 完成状态、FREE 标签 |
| `--border` | `#e5e5ea` | 仅在需要区分层次时使用的淡边框 |
| `--divider` | `#f0f0f0` | 分割线 |

### 3.2 排版

| 元素 | 字号 | 字重 | 颜色 | 备注 |
|------|------|------|------|------|
| 页面标题 | 24px | 600 | `--text-primary` | letter-spacing: -0.5px |
| 段落标题 | 18px | 600 | `--text-primary` | letter-spacing: -0.3px |
| 英文副标题 | 13px | 400 | `--text-secondary` | 紧跟中文标题下方 |
| 正文 | 14px | 400 | `--text-primary` | |
| 标签文字 | 12px | 500 | `--text-primary` | 中文标签 |
| 英文标签 | 12px | 400 | `--text-secondary` | 跟在中文标签后 |
| 小标签/tag | 10-11px | 400 | `--text-secondary` | 功能标签、状态标签 |
| Step 标签 | 11px | 600 | `--accent` | 背景 `--bg-selected` |

### 3.3 间距与圆角

| 元素 | 圆角 | 内边距 |
|------|------|--------|
| 大卡片（步骤容器） | 16px | 20px |
| 中卡片（行业选择、模式选择） | 14px | 18px 12px |
| 小卡片（折叠摘要、状态栏） | 10-12px | 12px 16px |
| 输入框 | 10px | 12px 16px |
| 按钮 | 10-12px | 12-14px |
| 标签 tag | 4px | 2px 8px |

### 3.4 设计原则

- **无边框优先**：卡片用灰底（`#f5f5f7`）区分层次，不用边框。仅选中状态用 `box-shadow: 0 0 0 2px #ff2442`
- **中英双语**：所有标题/标签采用「中文 English」格式，增加国际感
- **红色克制**：`#ff2442` 仅用于按钮、选中状态、Step标签，不用于背景渐变
- **渐变禁用**：去掉所有 `linear-gradient`，图标/按钮用纯色

## 4. 各页面设计

### 4.1 登录页

**品牌标识**：
- Logo：红色方块（36×36px，圆角10px，背景`#ff2442`）内放白色粗体字母 "R"
- 名称：`RedNote Agent`（font-size: 22px, font-weight: 600, color: `--text-primary`）
- Logo 和名称水平排列（`inline-flex`, gap: 10px）
- 副标题：`AI-powered content creation for Xiaohongshu`（13px, `--text-secondary`）

**表单区域**：
- 最大宽度 300px，居中显示
- 每个字段：中文标签 + 英文标签（`手机号 Phone`），font-size: 12px, font-weight: 500
- 输入框：灰底（`#f5f5f7`）无边框，border-radius: 10px，padding: 12px 16px
- 字段间距：16px
- 按钮：`开始使用`，背景 `#ff2442`，白色文字，border-radius: 12px，padding: 14px，font-weight: 600
- 按钮上方间距：24px

**底部**：
- `内测阶段 · 仅限受邀用户`（11px, `--text-tertiary`），居中，margin-top: 20px

**移除**：
- 渐变圆球 Logo
- 尖括号包裹的标题 `<小红书>`
- 技术化副标题 `内测版本 · 邀请码 + 手机号注册`
- 表单标题 `登录 / 注册`
- 输入框边框

### 4.2 行业选择页

**页面头部**：
- Step 标签：`Step 1`（11px, font-weight: 600, color: `--accent`, background: `--bg-selected`, padding: 2px 8px, border-radius: 4px）
- 标题：`选择行业`（24px, font-weight: 600），margin-top: 8px
- 副标题：`Choose the industry that best describes your business`（13px, `--text-secondary`）

**移除**：
- 顶部品牌标识重复（登录后不再需要）
- 流程步骤文字说明 `选择行业 → 选择工作方式 → ...`
- "第一步："前缀

**行业网格**：
- 3 列布局（`st.columns(3)`），gap: 10px
- 每个卡片：灰底（`#f5f5f7`）无边框，border-radius: 14px，padding: 18px 12px
- 卡片内容：emoji（28px） + 中文名（13px, font-weight: 500） + 英文名（11px, `--text-secondary`）
- 垂直居中，text-align: center

**选中状态**：
- 背景变为 `#fff1f3`
- box-shadow: `0 0 0 2px #ff2442`
- 中文名颜色变为 `#ff2442`，font-weight: 600
- 英文名颜色变为 `#ff8a9e`

**自定义行业卡片**：
- 与标准卡片同尺寸
- 虚线边框：`border: 1px dashed #d1d1d6`
- emoji: ✨，文字颜色为 `--text-secondary`

**交互变更**：
- 单击选中（去掉预览→确认的两步交互）
- 选中后底部显示确认栏

**底部确认栏**：
- 灰底卡片（`#f5f5f7`, border-radius: 12px, padding: 14px 16px）
- 左侧：emoji + 行业名 + "已选择"文字
- 右侧：`下一步 →` 按钮（`#ff2442` 背景，border-radius: 8px, padding: 8px 20px）
- 使用 `st.columns` 实现左右布局

**行业卡片英文名映射**：

| 中文 | 英文 |
|------|------|
| 房产中介 | Real Estate |
| 餐饮美食 | Dining |
| 美业 | Beauty |
| 健身运动 | Fitness |
| 母婴育儿 | Parenting |
| 教育培训 | Education |
| 宠物 | Pets |
| 旅游民宿 | Travel |
| 婚庆摄影 | Wedding |
| 汽车 | Auto |
| 家居装修 | Home Design |

### 4.3 模式选择页

**页面头部**（同行业选择页格式）：
- Step 标签：`Step 2`
- 标题：`选择模式`
- 副标题：`How would you like to create content?`

**模式卡片布局**：纵向堆叠，gap: 12px（不再是两列并排）

**单个模式卡片结构**：
- 灰底（`#f5f5f7`），border-radius: 16px，padding: 20px
- 横向布局：左图标 + 中间内容 + 右箭头
- 左图标：44×44px 方块，border-radius: 12px，纯色背景（竞品模式`#ff2442`，原创模式`#ff8c00`），居中 emoji
- 中间内容：
  - 第一行：中文名（15px, font-weight: 600） + 英文名（11px, `--text-secondary`） + FREE标签（10px, color: `#34c759`, background: `#f0faf0`）
  - 第二行：一句话流程描述（12px, `--text-secondary`）
  - 第三行：功能标签 tags（10px, background: `#ebebed`, padding: 2px 8px, border-radius: 4px）
- 右箭头：`›`（18px, `--text-tertiary`），垂直居中

**竞品参考模式**：
- 图标背景：`#ff2442`，emoji: 🔄
- 名称：`竞品参考 Rewrite`
- 描述：`粘贴竞品链接 → AI分析爆文结构 → 改写为你的风格`
- 标签：`文案改写` `去水印` `防查重`

**原创生成模式**：
- 图标背景：`#ff8c00`，emoji: ✨
- 名称：`原创生成 Create`
- 描述：`填写店铺信息 → AI创作专属文案 → 美化照片或生成配图`
- 标签：`AI文案` `照片美化` + `AI配图 Pro`（Pro标签用橙色：color `#ff8c00`, background `#fff8f0`）

**选中后状态栏**（行业选择确认栏后也复用此组件）：
- 灰底（`#f5f5f7`），border-radius: 10px，padding: 12px 16px
- 内容：绿色圆点 + 行业emoji + 行业名 · 模式名 · 城市名
- 右侧：`切换` 文字链接（color `#ff2442`）

### 4.4 内容生成区域（Step 3-4）

**顶部进度条**：
- 水平排列 4 个步骤节点，节点间用横线连接
- 每个节点：圆形（24px）+ 步骤名文字
- 状态样式：
  - 已完成：绿色圆（`#34c759`）+ ✓ + 绿色连接线 + 绿色文字
  - 当前步骤：红色圆（`#ff2442`）+ 数字 + 红色文字
  - 未到达：灰色圆（`#e5e5ea`）+ 数字 + 灰色文字 + 灰色连接线
- 步骤名称（Mode A / 竞品参考）：`提取` `文案` `图片` `下载`
- 步骤名称（Mode B / 原创生成）：`信息` `文案` `图片` `下载`
- 使用 `st.columns` 实现，连接线用 `st.markdown` 的 CSS 绘制

**当前步骤展示**：
- 灰底大卡片（`#f5f5f7`, border-radius: 16px, padding: 20px）包裹当前步骤所有内容
- 卡片头部：中文标题（18px, 600） + 英文副标题（12px, `--text-secondary`） + 右侧功能标签
- 卡片内部元素用白底（`#ffffff`, border-radius: 10px）区分

**已完成步骤折叠**：
- 灰底小卡片（`#f5f5f7`, border-radius: 12px, padding: 14px 16px）
- 左侧：绿色 ✓ + 步骤名 + 摘要信息（如"1 条笔记 · 3 张图片"）
- 右侧：`查看` 文字链接，点击展开详情
- 使用 `st.expander` 实现，自定义样式

**"继续"按钮**：
- 在当前步骤卡片底部
- 文字格式：`继续 · [下一步名称] →`（如 `继续 · 图片处理 →`）
- 样式：`#ff2442` 背景，白色文字，border-radius: 10px，padding: 12px，全宽

**各步骤内部布局调整**：

| 步骤 | 当前 | 新设计 |
|------|------|--------|
| 提取/输入 | URL输入框 + 按钮横排 | URL输入框全宽 + 按钮行单独一行 |
| 文案处理 | 标题/正文两列并排 | 标题/正文纵向排列，各带编辑/锁定控件 |
| 图片处理 | 原图/处理后两列 | 保持两列，但用白底卡片包裹 |
| 下载 | 三个下载按钮横排 | 保持横排，去掉边框改为灰底 |

### 4.5 反馈区域

- 标题：`使用反馈 Feedback`（跟随新标题格式）
- 评分和文本框样式跟随新设计系统（灰底无边框输入框）
- 按钮：`提交反馈`，跟随新按钮样式

## 5. CSS 架构变更

### 5.1 新增 CSS 变量

在 `st.markdown` 的 `<style>` 块顶部定义 CSS 变量：

```css
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f7;
    --bg-selected: #fff1f3;
    --text-primary: #1d1d1f;
    --text-secondary: #86868b;
    --text-tertiary: #c7c7cc;
    --accent: #ff2442;
    --accent-orange: #ff8c00;
    --success: #34c759;
    --border: #e5e5ea;
    --divider: #f0f0f0;
    --radius-lg: 16px;
    --radius-md: 14px;
    --radius-sm: 10px;
    --radius-xs: 4px;
}
```

### 5.2 移除的 CSS

- 所有 `linear-gradient` 按钮样式
- `.ind-card` 的浮动动画（`@keyframes float`）
- `.step-num` 的渐变圆圈样式
- 输入框的边框样式（改为灰底无边框）
- 按钮 hover 的渐变效果（改为 `opacity: 0.9` 或 `filter: brightness(0.95)`）

### 5.3 新增的 CSS 类

```css
/* Step 标签 */
.step-tag {
    font-size: 11px; font-weight: 600;
    color: var(--accent); background: var(--bg-selected);
    padding: 2px 8px; border-radius: var(--radius-xs);
    display: inline-block;
}

/* 灰底卡片 */
.card-gray {
    background: var(--bg-secondary);
    border-radius: var(--radius-lg);
    padding: 20px;
}

/* 选中卡片 */
.card-selected {
    background: var(--bg-selected);
    box-shadow: 0 0 0 2px var(--accent);
}

/* 功能标签 */
.tag {
    font-size: 10px; color: var(--text-secondary);
    background: #ebebed; padding: 2px 8px;
    border-radius: var(--radius-xs);
    display: inline-block;
}

/* 进度条节点 */
.progress-dot-done { background: var(--success); color: white; }
.progress-dot-active { background: var(--accent); color: white; }
.progress-dot-pending { background: var(--border); color: #999; }
.progress-line-done { background: var(--success); }
.progress-line-pending { background: var(--border); }

/* 状态栏 */
.status-bar {
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
}
```

## 6. 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app.py` | 修改 | CSS变量替换、登录页重写、行业选择重写、模式选择重写、进度条组件、步骤折叠逻辑 |
| `config.py` | 修改 | 新增 `INDUSTRY_EN_NAMES` 英文名映射字典 |

## 7. 不改动的部分

- 所有业务逻辑（提取、改写、图片处理、下载）不变
- 数据库结构不变
- utils.py 不变
- 侧边栏不在本次范围（将在管理后台重设计中一并处理）
- 管理面板不在本次范围（有独立设计规格）

## 8. Streamlit 实现约束

由于 Streamlit 框架限制，以下设计需要特殊处理：

- **行业卡片单击选中**：使用 `st.button` + session_state，点击直接选中并显示确认栏（去掉两步交互需要调整 `st.button` 回调逻辑）
- **进度条**：使用 `st.columns` + `st.markdown` 的内联 HTML/CSS 绘制，不依赖 JavaScript
- **折叠已完成步骤**：使用 `st.expander` 自定义样式实现
- **模式卡片箭头**：通过 `st.markdown` 内联 HTML 实现横向布局，`st.button` 覆盖整个卡片区域
- **底部确认栏/状态栏**：使用 `st.columns` + `st.markdown` + `st.button` 组合
