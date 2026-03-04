"""
小红书通用内容 Agent — 配置模块
行业配置 · SVG图标 · 常量 · Session State 默认值
"""

from pathlib import Path


# ═══════════════════════════════════════════════════════
#  数据库路径
# ═══════════════════════════════════════════════════════
DB_PATH = Path(__file__).parent / "xhs_agent.db"


# ═══════════════════════════════════════════════════════
#  Pro 配额上限
# ═══════════════════════════════════════════════════════
PRO_GEN_LIMIT = 50


# ═══════════════════════════════════════════════════════
#  管理员邀请码
# ═══════════════════════════════════════════════════════
ADMIN_CODES = {"ADMIN01"}


# ═══════════════════════════════════════════════════════
#  行业 SVG 图标（Lucide 风格，28×28）
# ═══════════════════════════════════════════════════════
ICON_ATTRS = 'xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"'

INDUSTRY_ICONS: dict[str, str] = {
    # 健身私教 — 哑铃
    "fitness": f'<svg {ICON_ATTRS}><path d="M6.5 6.5h11"/><path d="M6.5 17.5h11"/><path d="M12 6.5v11"/><rect x="2" y="8" width="4" height="8" rx="1"/><rect x="18" y="8" width="4" height="8" rx="1"/><rect x="4" y="6" width="2" height="12" rx="0.5"/><rect x="18" y="6" width="2" height="12" rx="0.5"/></svg>',
    # 美容美发 — 剪刀
    "beauty": f'<svg {ICON_ATTRS}><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>',
    # 教育培训 — 学位帽
    "education": f'<svg {ICON_ATTRS}><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 1.1 2.7 3 6 3s6-1.9 6-3v-5"/></svg>',
    # 餐饮美食 — 餐具
    "food": f'<svg {ICON_ATTRS}><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 002-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 00-5 5v6c0 1.1.9 2 2 2h3zm0 0v7"/></svg>',
    # 医疗美容 — 闪光星
    "medical_beauty": f'<svg {ICON_ATTRS}><path d="M12 3l1.912 5.813a2 2 0 001.275 1.275L21 12l-5.813 1.912a2 2 0 00-1.275 1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L3 12l5.813-1.912a2 2 0 001.275-1.275L12 3z"/></svg>',
    # 服装销售 — 衬衫
    "fashion": f'<svg {ICON_ATTRS}><path d="M20.38 3.46L16 2 13.01 5H11L8 2 3.62 3.46a2 2 0 00-1.34 1.65l-.67 6.72A2 2 0 003.6 14h2.8L8 22h8l1.6-8h2.8a2 2 0 001.99-2.17l-.67-6.72a2 2 0 00-1.34-1.65z"/></svg>',
    # 法律咨询 — 天平
    "legal": f'<svg {ICON_ATTRS}><path d="M12 3v19"/><path d="M5 8l7-5 7 5"/><path d="M5 8v0a4 4 0 004 4h0"/><path d="M19 8v0a4 4 0 01-4 4h0"/><path d="M1 8l4 8h0a4 4 0 008 0h0l-4-8"/><path d="M19 8l-4 8h0a4 4 0 008 0h0l4-8"/></svg>',
    # 摄影工作室 — 相机
    "photography": f'<svg {ICON_ATTRS}><path d="M14.5 4h-5L7 7H4a2 2 0 00-2 2v9a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
    # 民宿酒店 — 建筑
    "hotel": f'<svg {ICON_ATTRS}><path d="M6 22V4a2 2 0 012-2h8a2 2 0 012 2v18z"/><path d="M6 12H4a2 2 0 00-2 2v6a2 2 0 002 2h2"/><path d="M18 9h2a2 2 0 012 2v9a2 2 0 01-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></svg>',
    # 珠宝黄金 — 宝石
    "jewelry": f'<svg {ICON_ATTRS}><path d="M6 3h12l4 6-10 13L2 9z"/><path d="M11 3l1 6"/><path d="M13 3l-1 6"/><path d="M2 9h20"/><path d="M6 3L12 9"/><path d="M18 3l-6 6"/></svg>',
    # 宠物服务 — 爪印
    "pet": f'<svg {ICON_ATTRS}><circle cx="11" cy="4" r="2"/><circle cx="18" cy="8" r="2"/><circle cx="20" cy="16" r="2"/><path d="M9 10a5 5 0 015 5v3.5a3.5 3.5 0 01-6.84 1.045Q6.52 17.48 4.46 16.84A3.5 3.5 0 015.5 10z"/></svg>',
    # 旅游出行 — 飞机
    "travel": f'<svg {ICON_ATTRS}><path d="M17.8 19.2L16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></svg>',
}


# ═══════════════════════════════════════════════════════
#  行业模板库（12 个行业，每个均支持竞品参考 + 原创生成双模式）
# ═══════════════════════════════════════════════════════
INDUSTRIES = {

    "fitness": {
        "label": "健身私教",
        "desc": "上门私教 / 减脂增肌 / 产后恢复",

        # ── 竞品参考模式 (Mode A) ──
        "system_prompt": (
            "你是专业的健身私教小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留原文核心卖点（效果数据、课程亮点、真实反馈）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：专业权威+亲切真实，口语化，适当使用 emoji\n"
            "4. 融入城市本地元素（地标、商圈、区域名）\n"
            "5. 保留并优化话题标签（#xxx）\n"
            "6. 强调「效果」「专业」「上门服务」「变化」等高转化词\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        # ── 原创生成模式 (Mode B) ──
        "profile_fields": [
            {"key": "studio_name",  "label": "工作室/品牌名", "placeholder": "如：FitPro私教中心"},
            {"key": "service_type", "label": "主营项目",      "placeholder": "如：上门私教 / 减脂增肌 / 产后恢复"},
            {"key": "coach_cred",   "label": "教练资质",      "placeholder": "如：ACE认证 / 5年经验 / 体育院校毕业"},
            {"key": "price_range",  "label": "课程价格",      "placeholder": "如：单次300元 / 10次课2800元"},
        ],
        "brief_placeholder": "如：学员小李3个月减脂18斤，腰围小了两圈，今天拍了对比照，想做成功案例展示",
        "create_system_prompt": (
            "你是专业的健身私教小红书文案创作专家。\n\n"
            "根据教练/工作室信息和今日主题，创作一篇原创小红书笔记。\n\n"
            "创作要求：\n"
            "1. 风格：专业权威+真实亲切，口语化，适当使用 emoji\n"
            "2. 结构：效果钩子标题 + 痛点共鸣 + 课程/教练介绍 + 成功案例/数据 + 预约引导\n"
            "3. 多用「效果翻倍」「专属方案」「上门服务」「真实蜕变」等高转化词\n"
            "4. 可加入学员真实反馈或前后数据对比\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，突出效果）\n"
            "【正文】原创正文"
        ),

        # ── 图片处理提示词 ──
        "image_prompt": (
            "Remove ALL text, titles, captions, watermarks, logos, and any overlaid "
            "text or graphics from this fitness/workout image completely. "
            "Reconstruct the areas behind removed text naturally. "
            "Do NOT change any people, faces, poses, clothing, gym equipment, or background. "
            "The output should look like a clean, professional fitness photo."
        ),
    },

    "beauty": {
        "label": "美容美发",
        "desc": "护肤 / 美甲 / 发型设计 / 美容院",

        "system_prompt": (
            "你是专业的美容美发小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（效果对比、技术亮点、价格、使用感受）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：精致时尚、有种草感，口语化，适当使用 emoji\n"
            "4. 强调「变美」「蜕变」「显白」「专业技术」等高转化词\n"
            "5. 可加入使用前后对比的描述\n"
            "6. 融入城市消费和审美特点\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",     "label": "店铺/工作室名", "placeholder": "如：颜研美容工作室"},
            {"key": "main_service",   "label": "主营项目",      "placeholder": "如：皮肤管理 / 美甲 / 睫毛 / 发型设计"},
            {"key": "tech_highlight", "label": "技术亮点",      "placeholder": "如：韩国进口仪器 / 10年技师 / 进口材料"},
            {"key": "price_range",    "label": "价格区间",      "placeholder": "如：皮肤管理基础护理188元起"},
        ],
        "brief_placeholder": "如：最近做了一个学员的皮肤管理，毛孔明显收缩，素颜都亮了很多，想展示效果吸引新客",
        "create_system_prompt": (
            "你是专业的美容美发小红书文案创作专家。\n\n"
            "根据店铺信息和今日主题，创作一篇原创小红书笔记。\n\n"
            "创作要求：\n"
            "1. 风格：精致时尚、有种草感，口语化，多用 emoji\n"
            "2. 结构：变美钩子标题 + 皮肤/发型痛点 + 项目/技术介绍 + 效果描述 + 预约引导\n"
            "3. 多用「蜕变」「显白」「焕然一新」「专业护理」等种草词\n"
            "4. 可加入 before/after 效果对比描述\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现变美感）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Remove ALL text, watermarks, logos, price information, and overlaid graphics "
            "from this beauty/hair/cosmetic image completely. "
            "Reconstruct the areas naturally. "
            "Keep the hairstyle, makeup, beauty results, and the person exactly the same. "
            "The result should look glamorous and professional."
        ),
    },

    "education": {
        "label": "教育培训",
        "desc": "技能培训 / 考证备考 / 儿童教育",

        "system_prompt": (
            "你是专业的教育培训小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（课程内容、学员成果、师资力量、价格）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：专业可信、激励感强，适当使用 emoji\n"
            "4. 强调「学会」「提升」「改变」「拿证」「成功上岸」等激励词\n"
            "5. 加入学员成果数据（考试通过率、学员人数、薪资提升幅度、获证数量等具体数字）\n"
            "6. 结尾引导报名/咨询\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "institution",  "label": "机构名称",    "placeholder": "如：启航职业培训中心"},
            {"key": "main_course",  "label": "主营课程",    "placeholder": "如：健身教练证 / 营养师证 / 育婴师证"},
            {"key": "pass_rate",    "label": "通过率/成果", "placeholder": "如：一次性通过率95% / 已培训2000+学员"},
            {"key": "price_range",  "label": "课程价格",    "placeholder": "如：周末班3980元 / 全程班5800元"},
        ],
        "brief_placeholder": "如：本月又有8名学员拿到了NSCA健身教练认证，想做成功案例展示，吸引更多学员报名",
        "create_system_prompt": (
            "你是专业的教育培训小红书文案创作专家。\n\n"
            "根据机构信息和今日主题，创作一篇原创小红书笔记。\n\n"
            "创作要求：\n"
            "1. 风格：专业可信、激励感强，适当使用 emoji\n"
            "2. 结构：成功钩子标题 + 学员痛点共鸣 + 课程/机构介绍 + 学员成果/数据 + 报名引导\n"
            "3. 多用「学会」「提升」「改变」「拿证」「成功上岸」等激励词\n"
            "4. 加入具体学员成功案例和数据\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现成功感）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Remove ALL text, watermarks, logos, and overlaid graphics "
            "from this education/training image completely. "
            "Reconstruct the areas naturally. "
            "Keep the students, teachers, learning materials, and classroom setting exactly the same. "
            "The result should look professional and inspiring."
        ),
    },

    "food": {
        "label": "餐饮美食",
        "desc": "餐厅 / 咖啡馆 / 烘焙甜品 / 探店",

        "system_prompt": (
            "你是专业的餐饮探店小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（招牌菜名称与价格、环境特色、人均消费、地址区域）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：有食欲感、温馨治愈，口语化，适当使用 emoji\n"
            "4. 融入当地商圈、地标元素，增加本地属性\n"
            "5. 多用「宝藏小店」「必点」「隐藏菜单」「氛围感」「性价比」等高流量词\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",  "label": "店名",       "placeholder": "如：猫窝咖啡"},
            {"key": "store_style", "label": "风格/特色",  "placeholder": "如：日系复古 / 宠物友好 / 手冲精品"},
            {"key": "price_range", "label": "人均消费",   "placeholder": "如：人均35元"},
            {"key": "location",    "label": "所在商圈",   "placeholder": "如：三里屯附近 / 朝阳望京"},
        ],
        "brief_placeholder": "如：新上了西西里柠檬拿铁，搭草莓奶油可颂，周末限定，想做一篇种草文",
        "create_system_prompt": (
            "你是专业的餐饮探店小红书文案创作专家。\n\n"
            "根据商家提供的店铺信息和今日主题，创作一篇原创小红书笔记。\n\n"
            "创作要求：\n"
            "1. 风格：有食欲感、温馨治愈，口语化，适当使用 emoji\n"
            "2. 结构：钩子标题 + 场景带入 + 产品描述 + 推荐理由 + 价格/地址引导\n"
            "3. 多用「宝藏小店」「必点」「隐藏菜单」「氛围感」等高流量词\n"
            "4. 结尾加推荐话题标签（5-8个）\n"
            "5. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，吸引眼球）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Enhance this food/restaurant photo to look like professional food photography: "
            "boost color vibrancy — make golden/warm tones richer, greens fresher, reds deeper. "
            "Sharpen food textures to emphasize juiciness, crispiness, or creaminess. "
            "Improve depth of field to naturally blur the background and highlight the main dish. "
            "Enhance lighting to create a warm, inviting atmosphere. "
            "Remove any text overlays, watermarks, or distracting elements. "
            "Do NOT change the food items, plating, or restaurant setting."
        ),
    },

    "medical_beauty": {
        "label": "医疗美容",
        "desc": "皮肤管理 / 医美项目 / 美容诊所",

        "system_prompt": (
            "你是专业的医疗美容小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心信息（项目名称、效果体验、价格、机构资质）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：专业可信 + 真实亲切，避免过度营销\n"
            "4. 合规：不夸大效果、不承诺疗效、不用医疗绝对化用语\n"
            "   禁止使用：「绝对」「保证」「永久」「根治」「最好」「100%」「零风险」等绝对化用语\n"
            "   推荐替代：「改善」「缓解」「提升」「优化」「帮助」等温和表达\n"
            "5. 强调「专业」「安全」「正规资质」「个性化方案」等信任词\n"
            "6. 融入城市本地元素，增加本地属性\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",    "label": "机构名称", "placeholder": "如：纯粹医美·光感肌肤管理"},
            {"key": "main_service",  "label": "主营项目", "placeholder": "如：水光针 / 热玛吉 / 皮肤管理"},
            {"key": "price_range",   "label": "项目价格", "placeholder": "如：水光针单次980起"},
            {"key": "highlights",    "label": "核心优势", "placeholder": "如：正规医疗资质 / 院长亲诊 / 韩国进口材料"},
        ],
        "brief_placeholder": "如：最近做了一批水光针客户，效果很好，皮肤喝饱水那种感觉，想发真实反馈种草",
        "create_system_prompt": (
            "你是专业的医疗美容小红书文案创作专家。\n\n"
            "根据机构信息和今日主题，创作一篇原创小红书笔记。\n\n"
            "创作要求：\n"
            "1. 风格：专业可信 + 真实亲切，避免过度营销语气\n"
            "2. 合规：不夸大效果、不承诺疗效、不用医疗绝对化用语\n"
            "   禁止使用：「绝对」「保证」「永久」「根治」「最好」「100%」「零风险」等绝对化用语\n"
            "   推荐替代：「改善」「缓解」「提升」「优化」「帮助」等温和表达\n"
            "3. 内容：项目介绍 + 体验感受 + 效果描述（用形容词）+ 预约引导\n"
            "4. 强调「专业」「安全」「正规资质」「个性化方案」等信任词\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现效果感）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Enhance this medical beauty/skincare clinic photo for social media: "
            "improve lighting to create a clean, professional, clinical yet welcoming atmosphere. "
            "Remove any text overlays, watermarks, or branding from the image. "
            "The result should look trustworthy, professional, and aspirational."
        ),
    },

    "fashion": {
        "label": "服装销售",
        "desc": "实体门店 / 网店直播 / 穿搭种草 / 新品上架",

        "system_prompt": (
            "你是专业的服装穿搭小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（款式特点、面料质感、适合场合、价格、搭配建议）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：时尚有种草力，口语化，多用穿搭场景，适当使用 emoji\n"
            "4. 多用「显瘦」「显白」「气质」「百搭」「穿搭公式」等种草词\n"
            "5. 融入本地消费场景（商场 / 街边店 / 市集），增加本地属性\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",    "label": "店铺名称",   "placeholder": "如：衣柜研究所 / 小熊女装"},
            {"key": "main_category", "label": "主营品类",   "placeholder": "如：休闲女装 / 男装 / 童装 / 男女皆有"},
            {"key": "style_tag",     "label": "风格标签",   "placeholder": "如：百搭休闲 / 韩系甜美 / 职场通勤 / 运动户外"},
            {"key": "price_range",   "label": "价格区间",   "placeholder": "如：单品59-199元 / 全场百元以内"},
        ],
        "brief_placeholder": "如：刚到一批春款碎花连衣裙，版型显瘦，颜色好看，价格才89元，想做种草吸引进店",
        "create_system_prompt": (
            "你是专业的服装穿搭小红书文案创作专家，擅长为本地实体服装店创作种草内容。\n\n"
            "根据店铺信息和今日主题，创作一篇原创小红书穿搭种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：接地气、有种草力，口语化，真实感强，适当使用 emoji\n"
            "2. 结构：视觉钩子标题 + 穿搭场景代入 + 款式亮点（颜色/版型/面料）+ 搭配建议 + 到店/购买引导\n"
            "3. 多用「显瘦」「显白」「气质」「百搭」「性价比」「新款」等高转化词\n"
            "4. 可以描述不同穿搭场景（逛街/上班/约会/周末休闲）\n"
            "5. 结尾引导到店试穿或私信询价，加话题标签（5-8个）\n"
            "6. 字数：正文300-500字，语言贴近本地消费者\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，突出款式或价格亮点）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Enhance this clothing/fashion product photo for social media: "
            "improve lighting and colors to make the clothing look more appealing and true-to-color. "
            "Clean up the background if possible. Sharpen fabric texture details. "
            "Remove any text overlays, price tags, or watermarks. "
            "Make the colors look vivid and the fabric look high quality. "
            "The result should look like a clean product photo suitable for a clothing store post."
        ),
    },

    "legal": {
        "label": "法律咨询",
        "desc": "离婚婚姻 / 劳动纠纷 / 合同房产 / 交通事故",

        "system_prompt": (
            "你是专业的法律行业小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心法律知识点（法条依据、维权步骤、注意事项、常见误区）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：专业可信+通俗易懂，把法律术语翻译成大白话，适当使用 emoji\n"
            "4. 多用「划重点」「避坑指南」「99%的人不知道」「律师教你」等吸引词\n"
            "5. 合规：不提供具体案件的法律意见，引导咨询专业律师\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "lawyer_name",   "label": "律师/律所名称", "placeholder": "如：张律师 / XX律师事务所"},
            {"key": "specialty",     "label": "擅长领域",     "placeholder": "如：婚姻家事 / 劳动仲裁 / 合同纠纷 / 刑事辩护"},
            {"key": "service_area",  "label": "服务地区",     "placeholder": "如：北京 / 全国线上咨询"},
            {"key": "highlights",    "label": "执业亮点",     "placeholder": "如：执业10年 / 胜诉率高 / 免费初次咨询"},
        ],
        "brief_placeholder": "如：很多人不知道被公司裁员可以拿N+1赔偿，想科普劳动法维权的正确步骤",
        "create_system_prompt": (
            "你是专业的法律行业小红书文案创作专家。\n\n"
            "根据律师/律所信息和今日主题，创作一篇原创小红书法律科普笔记。\n\n"
            "创作要求：\n"
            "1. 风格：专业权威+通俗易懂，用大白话讲法律，适当使用 emoji\n"
            "2. 结构：痛点钩子标题 + 常见误区/真实场景 + 法律知识点（分点列出）+ 维权建议 + 咨询引导\n"
            "3. 多用「划重点」「避坑」「维权指南」「律师提醒」「法律小课堂」等吸引词\n"
            "4. 引用相关法条时注明出处（如《劳动合同法》第47条），增强可信度\n"
            "5. 合规：不对具体案件下结论，文末提醒「具体情况建议咨询专业律师」\n"
            "6. 结尾加话题标签（5-8个）\n"
            "7. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，有痛点感）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Enhance this legal/lawyer/law firm photo for social media: "
            "improve lighting to create a professional, trustworthy atmosphere. "
            "Make the image look clean, authoritative, and approachable. "
            "Enhance clarity and sharpness. "
            "Remove any text overlays or watermarks. "
            "The result should convey professionalism and reliability."
        ),
    },

    "photography": {
        "label": "摄影工作室",
        "desc": "写真 / 婚纱 / 儿童 / 商业摄影",

        "system_prompt": (
            "你是专业的摄影工作室小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（摄影风格、出片效果、套餐价格、拍摄体验）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：有质感、有故事感，口语化，适当使用 emoji\n"
            "4. 多用「光影」「质感」「记录美好」「专属」「出片率高」等种草词\n"
            "5. 融入城市文艺场景，增加本地属性\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",   "label": "工作室名称", "placeholder": "如：光影印记摄影工作室"},
            {"key": "main_service", "label": "主营类型",   "placeholder": "如：个人写真 / 情侣写真 / 儿童摄影"},
            {"key": "photo_style",  "label": "拍摄风格",   "placeholder": "如：日系胶片 / 韩系清新 / 复古港风"},
            {"key": "price_range",  "label": "套餐价格",   "placeholder": "如：单人写真套餐599起"},
        ],
        "brief_placeholder": "如：最近出了一组日系胶片风格的闺蜜写真，在复古咖啡馆拍的，特别好看，想吸引新客预约",
        "create_system_prompt": (
            "你是专业的摄影工作室小红书文案创作专家。\n\n"
            "根据工作室信息和今日主题，创作一篇原创小红书种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：有质感、有故事感，口语化，适当使用 emoji\n"
            "2. 结构：视觉吸引标题 + 拍摄场景故事 + 风格/技术描述 + 出片效果 + 预约引导\n"
            "3. 多用「光影」「质感」「记录美好」「专属」「出片率高」等种草词\n"
            "4. 可以描述拍摄体验和拿到照片时的感受\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现画面感）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Enhance this portrait/photography studio photo for social media: "
            "improve overall tone, contrast, and warmth to match the intended artistic style. "
            "Enhance skin tones naturally. "
            "Remove any watermarks, studio logos, or text overlays completely. "
            "The result should look like a professionally edited portrait photo."
        ),
    },

    "hotel": {
        "label": "民宿&酒店",
        "desc": "精品民宿 / 特色酒店 / 亲子酒店 / 度假村",

        # ── 竞品参考模式 (Mode A) ──
        "system_prompt": (
            "你是专业的民宿/酒店小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（地理位置、环境氛围、特色房型、配套设施、价格）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：有情调、有故事感，口语化，适当使用 emoji\n"
            "4. 多用「氛围感」「治愈系」「宝藏住所」「出片率高」「私藏地」等种草词\n"
            "5. 融入城市/地区旅游场景，增加在地属性\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        # ── 原创生成模式 (Mode B) ──
        "profile_fields": [
            {"key": "hotel_name",   "label": "民宿/酒店名称", "placeholder": "如：山间云舍民宿"},
            {"key": "hotel_type",   "label": "类型/风格",     "placeholder": "如：山景民宿 / 海景精品酒店 / 亲子主题"},
            {"key": "price_range",  "label": "每晚价格",      "placeholder": "如：大床房每晚388元起"},
            {"key": "location",     "label": "地理位置",      "placeholder": "如：峨眉山脚下 / 大理古城附近"},
        ],
        "brief_placeholder": "如：周末入住了一对来度蜜月的客人，他们特别喜欢山景房，拍了很多照片，想展示环境吸引更多预定",
        "create_system_prompt": (
            "你是专业的民宿/酒店小红书文案创作专家。\n\n"
            "根据民宿/酒店信息和今日主题，创作一篇原创小红书种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：有情调、有故事感，口语化，适当使用 emoji\n"
            "2. 结构：场景钩子标题 + 初到感受/打卡亮点 + 房间/设施描述 + 周边配套 + 预订引导\n"
            "3. 多用「氛围感」「治愈」「宝藏住所」「出片率高」「打卡地」等高流量种草词\n"
            "4. 可描述入住体验、早餐、景色、周边游玩等细节\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现氛围感或地标感）\n"
            "【正文】原创正文"
        ),

        # ── 图片处理提示词 ──
        "image_prompt": (
            "Enhance this hotel/B&B/accommodation photo for social media: "
            "improve lighting, warmth, and atmosphere to make the space look inviting and cozy. "
            "Enhance natural light, make colors richer, and improve clarity of architectural details. "
            "Remove any text overlays, watermarks, price tags, or logos completely. "
            "The result should look like a professional interior or landscape photography shot "
            "that makes viewers want to book a stay."
        ),
    },

    "jewelry": {
        "label": "珠宝黄金",
        "desc": "黄金 / 翡翠 / 钻石 / 银饰 / 珠宝定制",

        # ── 竞品参考模式 (Mode A) ──
        "system_prompt": (
            "你是专业的珠宝黄金小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（材质工艺、设计亮点、价格/克价、品牌/店铺信息）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：精致优雅有品位感，口语化，适当使用 emoji\n"
            "4. 多用「质感」「有重量感」「送礼首选」「传家款」「保值」「每日佩戴」等种草词\n"
            "5. 融入节日/送礼/纪念日等消费场景\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        # ── 原创生成模式 (Mode B) ──
        "profile_fields": [
            {"key": "store_name",    "label": "品牌/店铺名", "placeholder": "如：福满堂黄金珠宝"},
            {"key": "main_product",  "label": "主营品类",    "placeholder": "如：黄金饰品 / 翡翠玉石 / 钻石定制"},
            {"key": "price_range",   "label": "价格/克价",   "placeholder": "如：黄金今日克价640元 / 钻石戒指5000元起"},
            {"key": "highlights",    "label": "品牌/工艺亮点", "placeholder": "如：国家认证 / 手工镶嵌 / 支持以旧换新"},
        ],
        "brief_placeholder": "如：新到了一批足金999蝴蝶结项链，轻奢感很强，今天主推，适合送女朋友，想做种草笔记",
        "create_system_prompt": (
            "你是专业的珠宝黄金小红书文案创作专家。\n\n"
            "根据店铺信息和今日主题，创作一篇原创小红书种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：精致有品位感，口语化，适当使用 emoji\n"
            "2. 结构：视觉吸引标题 + 材质/工艺介绍 + 佩戴效果/上身感 + 送礼/纪念日场景 + 购买引导\n"
            "3. 多用「质感」「有重量感」「保值」「送礼首选」「轻奢风」等高转化词\n"
            "4. 可结合节日、纪念日、自我犒赏等消费动机\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现品质感或礼赠感）\n"
            "【正文】原创正文"
        ),

        # ── 图片处理提示词 ──
        "image_prompt": (
            "Enhance this jewelry/gold/gemstone product photo for social media: "
            "improve lighting to make the metal shine brilliantly and gemstones sparkle vividly. "
            "Enhance color saturation of gold tones, gem colors, and metallic luster. "
            "Clean up the background for a professional, studio-quality look. "
            "Remove any text overlays, price tags, watermarks, or logos completely. "
            "The result should look like a high-end jewelry catalog photo that conveys luxury and quality."
        ),
    },

    "pet": {
        "label": "宠物服务",
        "desc": "宠物店 / 宠物医院 / 美容寄养 / 用品",

        # ── 竞品参考模式 (Mode A) ──
        "system_prompt": (
            "你是专业的宠物行业小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（服务项目、宠物品种、价格、环境/设备）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：温馨治愈、有爱，口语化，适当使用 emoji\n"
            "4. 多用「毛孩子」「铲屎官必看」「宝宝」「呵护」「放心托付」等情感词\n"
            "5. 融入宠物主人的情感共鸣场景\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        # ── 原创生成模式 (Mode B) ──
        "profile_fields": [
            {"key": "store_name",    "label": "店铺/机构名称", "placeholder": "如：毛茸茸宠物生活馆"},
            {"key": "main_service",  "label": "主营服务",      "placeholder": "如：宠物美容 / 寄养托管 / 宠物医疗"},
            {"key": "pet_type",      "label": "服务宠物种类",  "placeholder": "如：猫咪/犬类/兔子/小动物均可"},
            {"key": "price_range",   "label": "价格区间",      "placeholder": "如：基础洗澡美容68元起"},
        ],
        "brief_placeholder": "如：今天给一只泰迪做了全套SPA造型，主人看到后超感动，想展示效果吸引新客",
        "create_system_prompt": (
            "你是专业的宠物行业小红书文案创作专家。\n\n"
            "根据店铺信息和今日主题，创作一篇原创小红书种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：温馨治愈、有爱，口语化，多用 emoji\n"
            "2. 结构：萌宠钩子标题 + 铲屎官痛点共鸣 + 服务/产品介绍 + 效果/体验描述 + 预约/到店引导\n"
            "3. 多用「毛孩子」「铲屎官必看」「放心托付」「宝宝超乖」等情感高频词\n"
            "4. 可融入宠物趣事或主人情感共鸣\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，突出萌感或安心感）\n"
            "【正文】原创正文"
        ),

        # ── 图片处理提示词 ──
        "image_prompt": (
            "Enhance this pet/animal photo for social media: "
            "improve brightness and warmth to make the pet look adorable and healthy. "
            "Sharpen fur texture and eye clarity to bring out the cuteness. "
            "Improve background cleanliness without changing the setting. "
            "Remove any text overlays, watermarks, price tags, or logos completely. "
            "The result should look like a heartwarming, high-quality pet photo."
        ),
    },

    "travel": {
        "label": "旅游出行",
        "desc": "景区 / 旅行社 / 定制游 / 周边游攻略",

        # ── 竞品参考模式 (Mode A) ──
        "system_prompt": (
            "你是专业的旅游出行小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心信息（目的地、行程亮点、价格、交通/住宿建议）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：有画面感、有向往感，口语化，适当使用 emoji\n"
            "4. 多用「宝藏目的地」「私藏攻略」「错峰出行」「治愈系」「打卡胜地」等种草词\n"
            "5. 融入出发城市/路线的本地感，增强实用性\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        # ── 原创生成模式 (Mode B) ──
        "profile_fields": [
            {"key": "agency_name",   "label": "旅行社/品牌名", "placeholder": "如：悦途定制旅行"},
            {"key": "destination",   "label": "目的地/线路",   "placeholder": "如：云南大理丽香5日游 / 周边亲子游"},
            {"key": "price_range",   "label": "价格/人均",     "placeholder": "如：成人1980元/人 / 亲子家庭套餐3800元"},
            {"key": "highlights",    "label": "行程亮点",      "placeholder": "如：含接机/特色民宿/古城游览/私家团"},
        ],
        "brief_placeholder": "如：上周带了一个家庭客户去大理玩，天气超好，苍山洱海都拍到了，客户超满意，想做成案例展示",
        "create_system_prompt": (
            "你是专业的旅游出行小红书文案创作专家。\n\n"
            "根据旅行社/线路信息和今日主题，创作一篇原创小红书种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：有画面感、有向往感，口语化，适当使用 emoji\n"
            "2. 结构：景色/体验钩子标题 + 出行场景代入 + 行程/亮点介绍 + 费用/服务说明 + 咨询/报名引导\n"
            "3. 多用「宝藏目的地」「私藏攻略」「治愈系」「打卡胜地」「不踩坑」等高流量词\n"
            "4. 可融入真实出行体验感受和细节描写\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现向往感或实用感）\n"
            "【正文】原创正文"
        ),

        # ── 图片处理提示词 ──
        "image_prompt": (
            "Enhance this travel/landscape/tourism photo for social media: "
            "boost colors, saturation, and contrast to make scenery look vivid and breathtaking. "
            "Improve sky clarity, enhance natural colors of mountains, water, and greenery. "
            "Remove any text overlays, watermarks, tour agency logos, or price information completely. "
            "The result should look like a stunning travel photography shot that inspires viewers to visit."
        ),
    },
}


# ═══════════════════════════════════════════════════════
#  Session State 默认值
# ═══════════════════════════════════════════════════════
DEFAULTS = dict(
    authed=False,
    invite_code="",
    industry_id=None,
    selected_mode=None,    # "rewrite" 或 "create"，由用户选择
    city="",
    # Mode A：竞品参考
    note_title="",
    note_text="",
    note_images=[],
    rewrite_result="",
    edited_images=[],
    content_ready=False,
    rewrite_done=False,
    images_done=False,
    extract_log="",
    # Mode A 批量
    batch_results=[],   # [{url, title, text, images, rewrite, edited_images}, ...]
    # Mode B：原创生成
    store_profile={},
    daily_brief="",
    create_images=[],
    dynamic_image_prompt="",
    scene_images=[],
    scene_prompt="",
    feedback_submitted=False,
    scene_tier="",
)


# ═══════════════════════════════════════════════════════
#  HTTP User-Agent 池
# ═══════════════════════════════════════════════════════
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.6167.178 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "MicroMessenger/8.0.47(0x18002f30) NetType/WIFI Language/zh_CN",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/18.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 15; SM-S928B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.6778.135 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "discover/8.49.0 (iPhone13,4; iOS 17.4; Scale/3.0)",
]


# ═══════════════════════════════════════════════════════
#  无效标题过滤集合
# ═══════════════════════════════════════════════════════
GARBAGE_TITLES = {"小红书", "小红书 - 你的生活指南", "发现 - 小红书", ""}
