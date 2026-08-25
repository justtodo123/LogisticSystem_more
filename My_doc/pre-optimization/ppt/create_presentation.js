const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "华中科技大学软件学院";
pres.title = "DeepSeek 路径优化 - 智能物流平台";

// ==================== Color Scheme ====================
const C = {
  primary:    "1A3C6D",
  secondary:  "2B6CB0",
  accent:     "48BB78",
  accent2:    "ED8936",
  purple:     "805AD5",
  red:        "E53E3E",
  dark:       "1A202C",
  medium:     "4A5568",
  light:      "A0AEC0",
  bgLight:    "F7FAFC",
  bgWhite:    "FFFFFF",
  divider:    "E2E8F0",
  warnBg:     "FFFBEB",
  warnBorder: "F6E05E",
  infoBg:     "EBF4FF",
  infoBorder: "90CDF4",
  greenBg:    "F0FFF4",
  greenBorder:"9AE6B4",
};

// ==================== Helpers ====================

function sectionTitle(slide, title) {
    slide.addText(title, {
        x: 0.6, y: 0.30, w: 8.8, h: 0.60,
        fontSize: 30, bold: true, color: C.primary,
        fontFace: "Microsoft YaHei",
    });
    slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.6, y: 0.90, w: 1.0, h: 0.04,
        fill: { color: C.accent }, line: { type: "none" },
    });
}

function tagLine(slide, text, y) {
    slide.addText(text, {
        x: 0.6, y: y || 0.95, w: 8.8, h: 0.28,
        fontSize: 10, italic: true, color: C.light,
        fontFace: "Microsoft YaHei",
    });
}

function card(slide, x, y, w, h, fill, shadow) {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x, y, w, h, fill: { color: fill || C.bgWhite },
        rectRadius: 0.06,
        shadow: shadow || { type: "outer", blur: 3, offset: 1.5, color: "000000", opacity: 0.06 },
        line: { type: "none" },
    });
}

function accentBar(slide, x, y, w, h, color) {
    slide.addShape(pres.shapes.RECTANGLE, {
        x, y, w: w || 0.05, h, fill: { color: color || C.accent },
        line: { type: "none" },
    });
}

function statBox(slide, x, y, w, h, value, label, bgColor) {
    card(slide, x, y, w, h, bgColor, { type: "outer", blur: 4, offset: 2, color: "000000", opacity: 0.12 });
    slide.addText(value, {
        x, y: y + 0.10, w, h: 0.52,
        fontSize: 28, bold: true, color: "FFFFFF", align: "center", fontFace: "Arial",
    });
    slide.addText(label, {
        x, y: y + 0.60, w, h: 0.30,
        fontSize: 11, color: "CADCFC", align: "center", fontFace: "Microsoft YaHei",
    });
}

function flowArrow(slide, x, y, w) {
    slide.addText("▶", {
        x, y, w: w || 0.30, h: 0.28,
        fontSize: 11, color: C.accent, align: "center", fontFace: "Arial",
    });
}

// ================================================================
// SLIDE 1: Cover
// ================================================================
const s1 = pres.addSlide();
s1.background = { fill: C.primary };
s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0,    w: 10, h: 0.07, fill: { color: C.accent  }, line: { type: "none" } });
s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.55, w: 10, h: 0.07, fill: { color: C.accent  }, line: { type: "none" } });

s1.addText("DeepSeek 路径优化", {
    x: 0.8, y: 1.6, w: 8.4, h: 1.0,
    fontSize: 46, bold: true, color: "FFFFFF", align: "center", fontFace: "Microsoft YaHei",
});
s1.addText("智能物流平台", {
    x: 0.8, y: 2.7, w: 8.4, h: 0.85,
    fontSize: 38, color: "A3C4F3", align: "center", fontFace: "Microsoft YaHei",
});
s1.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 3.70, w: 3.0, h: 0.02, fill: { color: C.accent }, line: { type: "none" },
});
s1.addText("华中科技大学软件学院  ·  2026 年 6 月 教学实训项目", {
    x: 0.8, y: 4.0, w: 8.4, h: 0.50,
    fontSize: 16, color: "CADCFC", align: "center", fontFace: "Microsoft YaHei",
});
s1.addText("2 人团队  ·  4 周开发周期  ·  前后端分离", {
    x: 0.8, y: 5.0, w: 8.4, h: 0.40,
    fontSize: 12, color: "718096", align: "center", fontFace: "Microsoft YaHei",
});

// ================================================================
// SLIDE 2: Table of Contents
// ================================================================
const s2 = pres.addSlide();
s2.background = { fill: C.bgLight };
sectionTitle(s2, "演示目录");
tagLine(s2, "演示路径：项目背景 → 架构设计 → 核心流程 → 扩展亮点 → 总结展望");

const toc = [
    { num: "01", ch: "开场", title: "项目定位与演示路线", time: "~1.0 min" },
    { num: "02", ch: "Vibe Coding", title: "AI 协作开发 · 代码生成与审查", time: "~1.0 min" },
    { num: "03", ch: "系统架构", title: "技术栈 · 6层架构 · 数据库设计", time: "~2.0 min" },
    { num: "04", ch: "核心流程 ★", title: "F007→F021→F005→F006→F010 全链路", time: "~3.5 min" },
    { num: "05", ch: "P1 扩展", title: "异常重规划 · 到货确认 · DeepSeek AI", time: "~2.0 min" },
    { num: "06", ch: "亮点展望", title: "项目创新 · 总结 · Q&A", time: "~1.5 min" },
];

toc.forEach((item, i) => {
    const ty = 1.45 + i * 0.78;
    card(s2, 0.6, ty, 8.8, 0.68, i % 2 === 0 ? C.bgWhite : "EDF2F7");

    accentBar(s2, 0.6, ty, null, 0.68, i === 3 ? C.accent2 : C.accent);
    s2.addText(item.num, {
        x: 0.80, y: ty + 0.10, w: 0.65, h: 0.48,
        fontSize: 26, bold: true, color: i === 3 ? C.accent2 : C.accent, fontFace: "Arial",
    });
    s2.addText(item.ch, {
        x: 1.55, y: ty + 0.10, w: 2.20, h: 0.48,
        fontSize: 17, bold: true, color: C.dark, fontFace: "Microsoft YaHei",
    });
    s2.addText(item.title, {
        x: 3.80, y: ty + 0.16, w: 4.20, h: 0.38,
        fontSize: 12, color: C.medium, fontFace: "Microsoft YaHei",
    });
    s2.addText(item.time, {
        x: 8.30, y: ty + 0.16, w: 0.95, h: 0.38,
        fontSize: 11, color: C.light, align: "right", fontFace: "Microsoft YaHei",
    });
});

// ================================================================
// SLIDE 3: Vibe Coding Development Practice
// ================================================================
const s3 = pres.addSlide();
s3.background = { fill: C.bgLight };
sectionTitle(s3, "Vibe Coding 开发实践");
tagLine(s3, "自然语言驱动编程 · AI 作为协作伙伴 · 需求→生成→审查→合入 人机闭环");

// Left: 4-step flow diagram (vertical)
card(s3, 0.50, 1.25, 4.60, 4.15);
accentBar(s3, 0.50, 1.25, null, 4.15, C.purple);

s3.addText("人机协作工作流", {
    x: 0.75, y: 1.32, w: 4.10, h: 0.38,
    fontSize: 16, bold: true, color: C.primary, fontFace: "Microsoft YaHei",
});

const vibeSteps = [
    {
        icon: "💬", phase: "Phase 1", title: "需求对话",
        desc: "自然语言描述功能需求\nAI 理解 → 生成设计方案\n多轮确认细节后进入生成",
        color: C.accent, bgColor: C.greenBg, borderColor: C.greenBorder,
    },
    {
        icon: "🤖", phase: "Phase 2", title: "AI 代码生成",
        desc: "模型/服务/路由/测试/文档\n自动规范检查（Lint/Format）\n批量生成完整功能模块",
        color: C.secondary, bgColor: C.infoBg, borderColor: C.infoBorder,
    },
    {
        icon: "🔍", phase: "Phase 3", title: "人工审查迭代",
        desc: "逐模块 Code Review\n修正架构偏差与逻辑错误\n多轮对话迭代优化",
        color: C.accent2, bgColor: C.warnBg, borderColor: C.warnBorder,
    },
    {
        icon: "✅", phase: "Phase 4", title: "确认合入",
        desc: "单元测试全通过\n前后端联调验证\n合并分支 → 进入下一阶段",
        color: C.accent, bgColor: C.greenBg, borderColor: C.greenBorder,
    },
];

vibeSteps.forEach((step, i) => {
    const vy = 1.85 + i * 0.84;

    s3.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.72, y: vy, w: 4.15, h: 0.72,
        fill: { color: step.bgColor },
        line: { color: step.borderColor, pt: 0.5 },
        rectRadius: 0.05,
    });

    s3.addText(step.icon, {
        x: 0.82, y: vy + 0.08, w: 0.48, h: 0.55,
        fontSize: 24,
    });
    s3.addText(step.phase, {
        x: 1.32, y: vy + 0.04, w: 0.85, h: 0.18,
        fontSize: 8, bold: true, color: step.color, fontFace: "Arial",
    });
    s3.addText(step.title, {
        x: 2.18, y: vy + 0.04, w: 2.50, h: 0.18,
        fontSize: 12, bold: true, color: C.dark, fontFace: "Microsoft YaHei",
    });
    s3.addText(step.desc, {
        x: 0.90, y: vy + 0.26, w: 3.80, h: 0.42,
        fontSize: 9, color: C.medium, fontFace: "Microsoft YaHei",
    });

    // arrow connector
    if (i < vibeSteps.length - 1) {
        s3.addText("▼", {
            x: 0.82, y: vy + 0.74, w: 0.22, h: 0.12,
            fontSize: 8, color: C.accent, fontFace: "Arial",
        });
    }
});

// Right: Human-AI Interaction Model + Stats
card(s3, 5.30, 1.25, 4.20, 2.00);
accentBar(s3, 5.30, 1.25, null, 2.00, C.secondary);
s3.addText("人机交互模式", {
    x: 5.55, y: 1.32, w: 3.70, h: 0.35,
    fontSize: 15, bold: true, color: C.primary, fontFace: "Microsoft YaHei",
});

const interactionItems = [
    { who: "👨‍💻 人", role: "需求定义 + 架构决策 + Code Review" },
    { who: "🤖 AI", role: "代码生成 + 测试编写 + 文档输出" },
    { who: "📋 规范", role: "Lint/Format/类型检查 自动保障" },
];

interactionItems.forEach((item, i) => {
    const iy = 1.78 + i * 0.45;
    s3.addText(item.who, {
        x: 5.55, y: iy, w: 1.15, h: 0.35,
        fontSize: 12, bold: true, color: C.primary, fontFace: "Microsoft YaHei",
    });
    s3.addText(item.role, {
        x: 6.75, y: iy, w: 2.55, h: 0.35,
        fontSize: 10, color: C.medium, fontFace: "Microsoft YaHei",
    });
});

// Right bottom: Stats cards
card(s3, 5.30, 3.50, 4.20, 1.90);
accentBar(s3, 5.30, 3.50, null, 1.90, C.accent);
s3.addText("Vibe Coding 项目实践数据", {
    x: 5.55, y: 3.57, w: 3.70, h: 0.32,
    fontSize: 14, bold: true, color: C.primary, fontFace: "Microsoft YaHei",
});

const vibeStats = [
    { col: 0, value: "~80%", label: "AI 辅助生成代码" },
    { col: 1, value: "3-5x", label: "开发效率提升" },
    { col: 0, value: "90%+", label: "首次 Review 通过率" },
    { col: 1, value: "100%", label: "Lint/Format 合规" },
];

vibeStats.forEach((stat) => {
    const sx = 5.45 + stat.col * 2.00;
    const sy = stat.col === 0 ? 4.00 : 4.00;
    const syOff = (stat.col === 0 && stat.value === "90%+") ? 4.55 : 4.00;

    s3.addText(stat.value, {
        x: sx, y: stat.value === "90%+" ? 4.55 : 4.00, w: 1.80, h: 0.40,
        fontSize: 18, bold: true, color: C.primary, align: "center", fontFace: "Arial",
    });
    s3.addText(stat.label, {
        x: sx, y: stat.value === "90%+" ? 4.92 : 4.40, w: 1.80, h: 0.22,
        fontSize: 9, color: C.medium, align: "center", fontFace: "Microsoft YaHei",
    });
});

// Bottom: Key principle
card(s3, 0.50, 4.80, 9.00, 0.56, C.infoBg);
s3.addShape(pres.shapes.RECTANGLE, {
    x: 0.50, y: 4.80, w: 0.05, h: 0.56, fill: { color: C.purple }, line: { type: "none" },
});
s3.addText([
    { text: "💡 核心理念：", options: { bold: true, fontSize: 11, color: C.purple } },
    { text: "AI 负责高效率生成与规范化检查 · 人负责架构决策与逻辑正确性审查 · 编写 prompts 本身即为系统设计过程", options: { fontSize: 10, color: C.medium } },
], {
    x: 0.75, y: 4.84, w: 8.50, h: 0.48,
    fontFace: "Microsoft YaHei",
});

// ================================================================
// SLIDE 4: Project Background & Business Loop
// ================================================================
const s4 = pres.addSlide();
s4.background = { fill: C.bgLight };
sectionTitle(s4, "项目背景与业务闭环");

// Left: Background card
card(s4, 0.5, 1.20, 4.30, 4.10);
accentBar(s4, 0.5, 1.20, null, 4.10, C.secondary);

s4.addText("项目背景", {
    x: 0.75, y: 1.30, w: 3.80, h: 0.40,
    fontSize: 17, bold: true, color: C.primary, fontFace: "Microsoft YaHei",
});

const bgLines = [
    { label: "性质", text: "华中科技大学软件学院 · 大三教学实训" },
    { label: "团队", text: "2 人团队（1 前端 + 1 后端）" },
    { label: "周期", text: "4 周（6 月），严格阶段推进" },
    { label: "目标", text: "构建三级物流网络调度演示系统，形成可部署、可演示、可验收的前后端分离系统" },
    { label: "网络", text: "L0 存储中心 → L1 分拣中心 → L2 配送节点" },
];

bgLines.forEach((item, i) => {
    const by = 1.85 + i * 0.62;
    s4.addText(item.label, {
        x: 0.80, y: by, w: 0.70, h: 0.24,
        fontSize: 12, bold: true, color: C.secondary, fontFace: "Microsoft YaHei",
    });
    s4.addText(item.text, {
        x: 1.55, y: by, w: 3.00, h: 0.50,
        fontSize: 11, color: C.medium, fontFace: "Microsoft YaHei", valign: "top",
    });
});

// Right: Business Loop - vertical flow
card(s4, 5.20, 1.20, 4.30, 4.10);
accentBar(s4, 5.20, 1.20, null, 4.10, C.accent);
s4.addText("核心业务闭环", {
    x: 5.45, y: 1.30, w: 3.80, h: 0.40,
    fontSize: 17, bold: true, color: C.primary, fontFace: "Microsoft YaHei",
});

const loopSteps = [
    { title: "订单导入", desc: "批量 Excel / 逐条添加" },
    { title: "F007 全局调度", desc: "规则评分 + 启发式算法 → global_schedules" },
    { title: "F021 智能打包", desc: "L0→L1 按节点对合并 / L1→L2 按同订单合并" },
    { title: "F005 节点间调度", desc: "两次串行调度 · 车辆+司机分配 → batches" },
    { title: "F006 路径规划", desc: "Haversine + 2-opt → routes" },
    { title: "F010 路线可视化", desc: "SVG 渲染 · 节点+路线+包裹点展示" },
];

loopSteps.forEach((step, i) => {
    const ly = 1.85 + i * 0.54;
    const isEven = i % 2 === 0;
    s4.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 5.50, y: ly, w: 3.70, h: 0.42,
        fill: { color: isEven ? C.greenBg : C.infoBg },
        line: { color: isEven ? C.greenBorder : C.infoBorder, pt: 0.5 },
        rectRadius: 0.04,
    });
    if (i < loopSteps.length - 1) {
        s4.addText("▼", {
            x: 5.65, y: ly + 0.38, w: 0.22, h: 0.16,
            fontSize: 7, color: C.accent, fontFace: "Arial",
        });
    }
    s4.addText(step.title, {
        x: 5.65, y: ly + 0.03, w: 3.40, h: 0.22,
        fontSize: 12, bold: true, color: C.dark, fontFace: "Microsoft YaHei",
    });
    s4.addText(step.desc, {
        x: 5.65, y: ly + 0.23, w: 3.40, h: 0.17,
        fontSize: 9, color: C.medium, fontFace: "Microsoft YaHei",
    });
});

// ================================================================
// SLIDE 5: Tech Architecture (6-layer)
// ================================================================
const s5 = pres.addSlide();
s5.background = { fill: C.bgLight };
sectionTitle(s5, "技术架构总览");
tagLine(s5, "6 层分层架构 · 各层技术栈与职责 · 比喻：建筑蓝图层层递进");

const layers = [
    { icon: "🖥️", name: "前端层", tech: "Vue 3.4 / TypeScript 5 / Vite 5", desc: "Element Plus 2.x  ·  Pinia 2.x  ·  Axios  ·  Vue Router 4.x  ·  SVG 可视化", color: "4299E1" },
    { icon: "🔗", name: "传输层", tech: "Axios → Vite Proxy → REST + JSON", desc: "JWT 认证  ·  RBAC 权限  ·  统一响应 {code,message,data,meta}  ·  timeout ≥ 15s", color: C.accent },
    { icon: "🛣️", name: "路由层", tech: "FastAPI Router（14 个模块）", desc: "路由分发  ·  JWT 中间件  ·  RBAC Guard  ·  依赖注入  ·  统一异常处理", color: C.accent2 },
    { icon: "⚙️", name: "服务层", tech: "Service Layer（18 个服务文件）", desc: "schedule_service  ·  dispatch_service  ·  route_service  ·  deepseek_service  ·  state_machine", color: C.purple },
    { icon: "🧮", name: "算法层", tech: "NumPy + Haversine + 2-opt 纯函数", desc: "global_schedule.py  ·  packaging.py  ·  node_dispatch.py  ·  route_planning.py", color: C.red },
    { icon: "🗄️", name: "数据层", tech: "SQLAlchemy 2.0 + SQLite", desc: "15 张表  ·  Alembic 迁移  ·  Pydantic v2 校验  ·  双标识策略（id 内部 / code 对外）", color: C.secondary },
];

layers.forEach((layer, i) => {
    const ly = 1.35 + i * 0.66;
    card(s5, 0.5, ly, 9.0, 0.57);
    accentBar(s5, 0.5, ly, null, 0.57, layer.color);

    s5.addText(layer.icon, {
        x: 0.70, y: ly + 0.10, w: 0.45, h: 0.38,
        fontSize: 20, align: "center",
    });
    s5.addText(layer.name, {
        x: 1.20, y: ly + 0.08, w: 0.95, h: 0.22,
        fontSize: 12.5, bold: true, color: layer.color, fontFace: "Microsoft YaHei",
    });
    s5.addText(layer.tech, {
        x: 2.20, y: ly + 0.08, w: 3.80, h: 0.22,
        fontSize: 12, bold: true, color: C.dark, fontFace: "Consolas",
    });
    s5.addText(layer.desc, {
        x: 0.70, y: ly + 0.32, w: 8.60, h: 0.20,
        fontSize: 9, color: C.medium, fontFace: "Microsoft YaHei",
    });
});

// ================================================================
// SLIDE 6: Core Scheduling Chain ★
// ================================================================
const s6 = pres.addSlide();
s6.background = { fill: C.bgLight };
sectionTitle(s6, "核心调度链路（串行依赖）");
tagLine(s6, "这是整个系统最关键的业务流程，必须严格按顺序执行");

const flowSteps = [
    { step: "Step 1", title: "F007 全局调度", detail: "规则评分\nscore = w1×距离\n+ w2×时间\n+ w3×包裹数", color: C.accent },
    { step: "Step 2", title: "F021 智能打包", detail: "L0→L1 按节点对合并\nL1→L2 按同订单合并\n更新订单状态\npending→delivering", color: C.secondary },
    { step: "Step 3", title: "F005 第一次调度", detail: "层级 L0→L1\n查询 packed 包裹\n分配车辆+空闲司机\nlevel_phase = 0", color: C.accent2 },
    { step: "Step 4", title: "F005 第二次调度", detail: "层级 L1→L2\ndemo_mode=true\n或 L0→L1 送达完成\nlevel_phase = 1", color: C.purple },
    { step: "Step 5", title: "F006 路径规划", detail: "Haversine 球面距离\n2-opt 局部搜索优化\n写入 route_segments\n返回 batch_code", color: C.red },
    { step: "Step 6", title: "F010 可视化", detail: "SVG 渲染输出\n节点 + 路线 + 包裹点\n状态流转闭环\n模拟送达驱动", color: C.primary },
];

flowSteps.forEach((step, i) => {
    const fx = 0.35 + i * 1.56;
    const fw = 1.46;

    // arrow between cards
    if (i < flowSteps.length - 1) {
        flowArrow(s6, fx + fw - 0.05, 2.10);
    }

    // card body
    s6.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: fx, y: 1.35, w: fw, h: 2.55,
        fill: { color: step.color },
        shadow: { type: "outer", blur: 4, offset: 2, color: "000000", opacity: 0.15 },
        rectRadius: 0.07,
    });

    s6.addText(step.step, {
        x: fx, y: 1.42, w: fw, h: 0.24,
        fontSize: 9, bold: true, color: "FFFFFF", align: "center", fontFace: "Arial",
    });
    s6.addText(step.title, {
        x: fx + 0.06, y: 1.68, w: fw - 0.12, h: 0.40,
        fontSize: 11, bold: true, color: "FFFFFF", align: "center", fontFace: "Microsoft YaHei",
    });
    s6.addText(step.detail, {
        x: fx + 0.06, y: 2.15, w: fw - 0.12, h: 1.60,
        fontSize: 8.5, color: "E8F0FE", align: "center", fontFace: "Microsoft YaHei",
    });
});

// Warning box at bottom
card(s6, 0.5, 4.10, 9.0, 1.20, C.warnBg);
s6.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.10, w: 9.0, h: 0.03, fill: { color: C.warnBorder }, line: { type: "none" },
});

s6.addText([
    { text: "⚠ 关键约束\n", options: { bold: true, fontSize: 13, color: C.dark, breakLine: true } },
    { text: "① F005 第一次失败 → 批次 status=failed，不执行第二次  |  ", options: { fontSize: 10.5, color: C.medium } },
    { text: "② demo_mode=true 可跳过 L1 等待，连续执行两次 F005  |  ", options: { fontSize: 10.5, color: C.medium } },
    { text: "③ 单次调度 ≤ 10s 返回  ·  确定性算法（同输入可复现）", options: { fontSize: 10.5, color: C.medium } },
], {
    x: 0.75, y: 4.20, w: 8.50, h: 1.00,
    fontFace: "Microsoft YaHei",
});

// ================================================================
// SLIDE 7: Database Design & State Transitions
// ================================================================
const s7 = pres.addSlide();
s7.background = { fill: C.bgLight };
sectionTitle(s7, "数据库设计与状态流转");

// Top half: Table groups
const tableGroups = [
    { title: "系统表", color: "718096", tables: ["users"] },
    { title: "基础数据", color: C.secondary, tables: ["nodes", "storage_centers", "sorting_centers", "orders", "goods", "packages", "vehicles", "drivers"] },
    { title: "调度结果", color: C.accent, tables: ["global_schedules", "dispatch_batches", "node_dispatches", "routes"] },
    { title: "异常日志", color: C.accent2, tables: ["exception_events", "log_events"] },
];

let gx = 0.5;
const gw = 2.15;
tableGroups.forEach((group) => {
    // group header
    s7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: gx, y: 1.15, w: gw, h: 0.38,
        fill: { color: group.color }, rectRadius: 0.04,
    });
    s7.addText(group.title, {
        x: gx, y: 1.15, w: gw, h: 0.38,
        fontSize: 11.5, bold: true, color: "FFFFFF", align: "center", fontFace: "Microsoft YaHei",
    });

    let ty = 1.60;
    group.tables.forEach((tbl) => {
        s7.addShape(pres.shapes.RECTANGLE, {
            x: gx, y: ty, w: gw, h: 0.28,
            fill: { color: C.bgWhite }, line: { color: C.divider, pt: 0.4 },
        });
        s7.addText(tbl, {
            x: gx + 0.10, y: ty + 0.01, w: gw - 0.20, h: 0.26,
            fontSize: 9.5, color: C.dark, fontFace: "Consolas",
        });
        ty += 0.33;
    });
    gx += gw + 0.13;
});

// Bottom half: State transitions
card(s7, 0.5, 3.65, 9.0, 1.75, C.infoBg);
s7.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.65, w: 9.0, h: 0.03, fill: { color: C.infoBorder }, line: { type: "none" },
});

s7.addText("核心实体状态流转", {
    x: 0.75, y: 3.72, w: 8.50, h: 0.30,
    fontSize: 14, bold: true, color: C.primary, fontFace: "Microsoft YaHei",
});

const stateFlows = [
    { entity: "订单", flow: "pending  →  delivering  →  completed / exception" },
    { entity: "货物", flow: "pending_pack  →  packed  →  in_transit  →  pending_pack(L1)  →  delivered(L2)" },
    { entity: "包裹", flow: "pending_pack  →  packed  →  in_transit  →  delivered" },
    { entity: "车辆", flow: "idle  →  delivering  →  idle" },
    { entity: "批次", flow: "pending  →  l0_l1_done  →  completed / failed" },
];

stateFlows.forEach((sf, i) => {
    const sy = 4.10 + i * 0.24;
    s7.addText(sf.entity, {
        x: 0.80, y: sy, w: 0.80, h: 0.22,
        fontSize: 10.5, bold: true, color: C.secondary, fontFace: "Microsoft YaHei",
    });
    s7.addText(sf.flow, {
        x: 1.65, y: sy, w: 7.60, h: 0.22,
        fontSize: 10, color: C.dark, fontFace: "Consolas", bold: true,
    });
});

s7.addText("所有状态变更统一走 transition_*_status()，非法转换立即抛出 ValueError 拒绝", {
    x: 0.80, y: 5.22, w: 8.40, h: 0.18,
    fontSize: 9, italic: true, color: C.light, fontFace: "Microsoft YaHei",
});

// ================================================================
// SLIDE 8: System UI Showcase (4-grid)
// ================================================================
const s8 = pres.addSlide();
s8.background = { fill: C.bgLight };
sectionTitle(s8, "系统界面展示");
tagLine(s8, "核心功能界面一览 · 调度工作台 · 方案预览 · 路线可视化 · 批次详情");

const screens = [
    {
        title: "调度工作台 Dashboard",
        items: ["调度状态总览", "订单统计看板", "快速操作入口", "异常事件提醒"],
    },
    {
        title: "全局调度方案预览",
        items: ["draft → confirm 两阶段", "评分明细展示", "货物路径可展开", "方案对比与选择"],
    },
    {
        title: "SVG 路线可视化",
        items: ["节点分布图渲染", "包裹起止点标注", "行驶路线颜色标记", "虚拟坐标系统 (30.5N,114.3E)"],
    },
    {
        title: "批次调度详情",
        items: ["L0→L1 / L1→L2 两阶段", "车辆-司机-任务明细", "包裹状态跟踪", "批次状态流转展示"],
    },
];

const scw = 4.30;
const sch = 2.25;
const positions = [
    [0.50, 1.35], [5.20, 1.35],
    [0.50, 3.80], [5.20, 3.80],
];

screens.forEach((sc, i) => {
    const [sx, sy] = positions[i];
    card(s8, sx, sy, scw, sch);

    s8.addShape(pres.shapes.RECTANGLE, {
        x: sx, y: sy, w: scw, h: 0.04,
        fill: { color: i === 2 ? C.accent2 : C.accent }, line: { type: "none" },
    });

    // icon placeholder
    s8.addText(i === 0 ? "📊" : i === 1 ? "📋" : i === 2 ? "🗺️" : "🚛", {
        x: sx + 0.15, y: sy + 0.15, w: 0.50, h: 0.35,
        fontSize: 22,
    });
    s8.addText(sc.title, {
        x: sx + 0.60, y: sy + 0.18, w: 3.50, h: 0.32,
        fontSize: 13, bold: true, color: C.primary, fontFace: "Microsoft YaHei",
    });

    // dashed divider
    s8.addShape(pres.shapes.RECTANGLE, {
        x: sx + 0.15, y: sy + 0.58, w: scw - 0.30, h: 0.01,
        fill: { color: C.divider }, line: { type: "none" },
    });

    // feature list in 2 columns
    sc.items.forEach((item, j) => {
        const col = j % 2;
        const row = Math.floor(j / 2);
        const ix = sx + 0.18 + col * 2.08;
        const iy = sy + 0.72 + row * 0.42;
        s8.addText("● " + item, {
            x: ix, y: iy, w: 1.95, h: 0.38,
            fontSize: 9.5, color: C.medium, fontFace: "Microsoft YaHei",
        });
    });
});

// Slide 8 bottom note
s8.addText("💡 现场可打开系统实机演示：登录 dispatcher → 创建订单 → 全局调度 → 查看路线图", {
    x: 0.60, y: 5.35, w: 8.80, h: 0.22,
    fontSize: 9.5, italic: true, color: C.light, fontFace: "Microsoft YaHei",
});

// ================================================================
// SLIDE 9: Exception Handling & Arrival Confirmation
// ================================================================
const s9 = pres.addSlide();
s9.background = { fill: C.bgLight };
sectionTitle(s9, "异常处理与到货确认");

// Left: Exception types
card(s9, 0.50, 1.20, 4.40, 2.20);
accentBar(s9, 0.50, 1.20, null, 2.20, C.accent2);
s9.addText("⚠ 异常类型与重规划", {
    x: 0.75, y: 1.28, w: 3.90, h: 0.35,
    fontSize: 15, bold: true, color: C.accent2, fontFace: "Microsoft YaHei",
});

const exceptionRows = [
    { type: "道路异常 · 包裹异常", action: "→ reroute", desc: "仅重新执行 F006 路径规划", color: C.warnBg },
    { type: "节点异常（容量/存储/维修）", action: "→ redispatch", desc: "重新执行 F007+F005+F006 全链路", color: "FFF5F5" },
];

exceptionRows.forEach((ex, i) => {
    const ey = 1.75 + i * 0.60;
    s9.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.70, y: ey, w: 3.95, h: 0.50,
        fill: { color: ex.color }, rectRadius: 0.04,
        line: { color: i === 0 ? C.warnBorder : "FEB2B2", pt: 0.5 },
    });
    s9.addText(ex.type, {
        x: 0.80, y: ey + 0.02, w: 2.80, h: 0.22,
        fontSize: 11, bold: true, color: C.dark, fontFace: "Microsoft YaHei",
    });
    s9.addText(ex.action, {
        x: 0.80, y: ey + 0.26, w: 1.30, h: 0.20,
        fontSize: 10.5, bold: true, color: i === 0 ? "D69E2E" : C.red, fontFace: "Microsoft YaHei",
    });
    s9.addText(ex.desc, {
        x: 2.10, y: ey + 0.26, w: 2.40, h: 0.20,
        fontSize: 9.5, color: C.medium, fontFace: "Microsoft YaHei",
    });
});

s9.addText("版本化机制：version+1 → parent_id 指向原版 → is_replan=true → 原方案完整保留可对比", {
    x: 0.80, y: 2.95, w: 3.80, h: 0.35,
    fontSize: 10, color: C.medium, fontFace: "Microsoft YaHei",
});

// Right: Arrival Confirmation
card(s9, 5.10, 1.20, 4.40, 2.20);
accentBar(s9, 5.10, 1.20, null, 2.20, C.purple);
s9.addText("📦 节点到货确认 (P1-08)", {
    x: 5.35, y: 1.28, w: 3.90, h: 0.35,
    fontSize: 15, bold: true, color: C.purple, fontFace: "Microsoft YaHei",
});

const arrivalFlows = [
    { node: "包裹到达 L1", normal: "货物 → pending_pack → F021 重打包 → 继续 L1→L2", bad: "货物 → exception → 记录异常事件" },
    { node: "包裹到达 L2", normal: "货物 → delivered → 订单完成", bad: "货物 → exception → 订单标记异常" },
];

arrivalFlows.forEach((af, i) => {
    const ay = 1.77 + i * 0.75;
    s9.addText(af.node, {
        x: 5.30, y: ay, w: 4.00, h: 0.22,
        fontSize: 11, bold: true, color: C.dark, fontFace: "Microsoft YaHei",
    });
    // normal path
    s9.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 5.30, y: ay + 0.25, w: 3.95, h: 0.22,
        fill: { color: C.greenBg }, rectRadius: 0.03,
        line: { color: C.greenBorder, pt: 0.4 },
    });
    s9.addText("✅ 正常: " + af.normal, {
        x: 5.36, y: ay + 0.25, w: 3.83, h: 0.22,
        fontSize: 8.5, color: C.medium, fontFace: "Microsoft YaHei",
    });
    // exception path
    s9.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 5.30, y: ay + 0.50, w: 3.95, h: 0.22,
        fill: { color: "FFF5F5" }, rectRadius: 0.03,
        line: { color: "FEB2B2", pt: 0.4 },
    });
    s9.addText("⚠ 异常: " + af.bad, {
        x: 5.36, y: ay + 0.50, w: 3.83, h: 0.22,
        fontSize: 8.5, color: C.medium, fontFace: "Microsoft YaHei",
    });
});

// Bottom: Arrival Confirm API
card(s9, 0.50, 3.65, 9.00, 0.80, C.infoBg);
s9.addShape(pres.shapes.RECTANGLE, {
    x: 0.50, y: 3.65, w: 9.00, h: 0.03, fill: { color: C.infoBorder }, line: { type: "none" },
});
s9.addText("到货确认API端点", {
    x: 0.75, y: 3.72, w: 8.50, h: 0.20,
    fontSize: 11, bold: true, color: C.primary, fontFace: "Microsoft YaHei",
});
s9.addText("POST /api/simulation/confirm-arrival  |  POST /api/simulation/confirm-arrival-batch  |  GET /api/simulation/arrival-packages", {
    x: 0.80, y: 3.95, w: 8.40, h: 0.22,
    fontSize: 10, color: C.dark, fontFace: "Consolas", bold: true,
});
s9.addText("支持单包裹确认 / 批量确认 / 正常确认 / 异常确认 → 状态级联联动所有关联实体", {
    x: 0.80, y: 4.20, w: 8.40, h: 0.18,
    fontSize: 9.5, color: C.medium, fontFace: "Microsoft YaHei",
});

// Bottom: Key design
card(s9, 0.50, 4.70, 9.00, 0.70, C.warnBg);
s9.addText([
    { text: "💡 设计要点：", options: { bold: true, fontSize: 10.5, color: C.dark } },
    { text: "异常确认可将所有关联的货物和包裹级联置 exception · 正常确认自动驱动状态流转 · 所有转换走 transition_* 函数", options: { fontSize: 9.5, color: C.medium } },
], {
    x: 0.75, y: 4.80, w: 8.50, h: 0.50,
    fontFace: "Microsoft YaHei",
});

// ================================================================
// SLIDE 10: DeepSeek AI Assistant
// ================================================================
const s10 = pres.addSlide();
s10.background = { fill: C.bgLight };
sectionTitle(s10, "DeepSeek AI 助手");

// AI Capability Cards - 2x2 grid
const aiCards = [
    { icon: "🤖", title: "自然语言调度 F014", api: "POST /api/ai/parse", status: "✅ 前端已接入", desc: "输入自然语言 → DeepSeek 解析 → 算法参数 → 自动调用调度链路", color: C.accent },
    { icon: "📝", title: "方案解释 F015", api: "POST /api/ai/explain", status: "✅ 前端已接入", desc: "对调度方案生成自然语言分析：为什么这样分配？距离/时间/包裹数综合评估", color: C.secondary },
    { icon: "🔍", title: "方案审查 F016", api: "POST /api/ai/review", status: "⚠ 后端已实现", desc: "AI 审查调度方案的合理性，指出潜在瓶颈与改进建议", color: C.purple },
    { icon: "🚨", title: "异常分析 F017", api: "POST /api/ai/analyze-exception", status: "⚠ 后端已实现", desc: "对异常事件进行 AI 分析，给出推荐处理方式与配置建议", color: C.accent2 },
];

const acw = 4.30;
const ach = 1.45;
const apositions = [
    [0.50, 1.15], [5.20, 1.15],
    [0.50, 2.80], [5.20, 2.80],
];

aiCards.forEach((cardData, i) => {
    const [ax, ay] = apositions[i];
    card(s10, ax, ay, acw, ach);
    accentBar(s10, ax, ay, null, ach, cardData.color);

    s10.addText(cardData.icon, {
        x: ax + 0.10, y: ay + 0.10, w: 0.50, h: 0.40,
        fontSize: 22,
    });
    s10.addText(cardData.title, {
        x: ax + 0.55, y: ay + 0.08, w: 2.70, h: 0.28,
        fontSize: 13, bold: true, color: C.primary, fontFace: "Microsoft YaHei",
    });
    s10.addText(cardData.api, {
        x: ax + 3.30, y: ay + 0.08, w: 0.85, h: 0.28,
        fontSize: 9, color: C.light, fontFace: "Consolas", align: "right",
    });
    s10.addShape(pres.shapes.RECTANGLE, {
        x: ax + 0.12, y: ay + 0.52, w: acw - 0.24, h: 0.01,
        fill: { color: C.divider }, line: { type: "none" },
    });
    s10.addText(cardData.desc, {
        x: ax + 0.18, y: ay + 0.58, w: 3.50, h: 0.80,
        fontSize: 10, color: C.medium, fontFace: "Microsoft YaHei",
    });
    s10.addText(cardData.status, {
        x: ax + 0.18, y: ay + 1.20, w: 1.80, h: 0.18,
        fontSize: 9, color: cardData.status.startsWith("✅") ? C.accent : C.accent2,
        fontFace: "Microsoft YaHei",
    });
});

// Bottom: degradation strategy
card(s10, 0.50, 4.45, 9.00, 0.95, "FFF5F5");
s10.addShape(pres.shapes.RECTANGLE, {
    x: 0.50, y: 4.45, w: 9.00, h: 0.03, fill: { color: "FEB2B2" }, line: { type: "none" },
});
s10.addText("🛡️ DeepSeek 降级策略", {
    x: 0.75, y: 4.53, w: 8.50, h: 0.26,
    fontSize: 13, bold: true, color: C.red, fontFace: "Microsoft YaHei",
});
s10.addText([
    { text: "API 调用失败 → meta.degraded=true → 使用默认算法参数完成调度 → 前端 ElAlert 明确提示用户 → ", options: { fontSize: 10.5, color: C.medium } },
    { text: "绝不伪造 AI 成功结果", options: { fontSize: 10.5, bold: true, color: C.red } },
], {
    x: 0.75, y: 4.84, w: 8.50, h: 0.45,
    fontFace: "Microsoft YaHei",
});

// ================================================================
// SLIDE 11: Project Highlights
// ================================================================
const s11 = pres.addSlide();
s11.background = { fill: C.bgLight };
sectionTitle(s11, "项目亮点与创新");

const highlights = [
    { icon: "🔄", title: "确定性可复现", desc: "不使用随机种子\n同输入必然同输出\n验收友好 · 可追溯" },
    { icon: "🏗️", title: "离线自包含", desc: "Haversine + 2-opt\n不依赖任何地图 API\n虚拟城市坐标系统" },
    { icon: "📊", title: "版本化重规划", desc: "异常触发重调度\n完整版本链追溯\n原方案完整保留对比" },
    { icon: "🤖", title: "AI 深度集成", desc: "自然语言驱动调度\n方案解释 + 审查\n不伪造AI结果降级兜底" },
    { icon: "⚡", title: "工程化实践", desc: "双标识策略 id/code\n状态机 transition_*\n契约先行 · 严格分层" },
];

const hw = 1.70;
const hgap = 0.17;
const hx0 = 0.45;
highlights.forEach((item, i) => {
    const hx = hx0 + i * (hw + hgap);
    card(s11, hx, 1.25, hw, 2.95);
    s11.addShape(pres.shapes.RECTANGLE, {
        x: hx, y: 1.25, w: hw, h: 0.06, fill: { color: C.accent }, line: { type: "none" },
    });

    s11.addText(item.icon, {
        x: hx, y: 1.45, w: hw, h: 0.55,
        fontSize: 32, align: "center",
    });
    s11.addText(item.title, {
        x: hx + 0.06, y: 2.10, w: hw - 0.12, h: 0.35,
        fontSize: 13, bold: true, color: C.primary, align: "center", fontFace: "Microsoft YaHei",
    });
    s11.addShape(pres.shapes.RECTANGLE, {
        x: hx + 0.30, y: 2.48, w: hw - 0.60, h: 0.01,
        fill: { color: C.divider }, line: { type: "none" },
    });
    s11.addText(item.desc, {
        x: hx + 0.06, y: 2.60, w: hw - 0.12, h: 1.50,
        fontSize: 9.5, color: C.medium, align: "center", fontFace: "Microsoft YaHei",
    });
});

// Bottom stats row
const statData = [
    { value: "138", label: "后端 .py 文件" },
    { value: "107", label: "前端 .ts/.vue 文件" },
    { value: "15", label: "数据库表" },
    { value: "8", label: "阶段全部验收" },
    { value: "2", label: "人完成交付" },
];

statData.forEach((sd, i) => {
    const sx = 0.50 + i * 1.90;
    s11.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: sx, y: 4.50, w: 1.72, h: 0.90,
        fill: { color: i === 4 ? C.accent : C.primary },
        shadow: { type: "outer", blur: 4, offset: 2, color: "000000", opacity: 0.10 },
        rectRadius: 0.06,
    });
    s11.addText(sd.value, {
        x: sx, y: 4.55, w: 1.72, h: 0.45,
        fontSize: 26, bold: true, color: "FFFFFF", align: "center", fontFace: "Arial",
    });
    s11.addText(sd.label, {
        x: sx, y: 5.05, w: 1.72, h: 0.25,
        fontSize: 10, color: "CADCFC", align: "center", fontFace: "Microsoft YaHei",
    });
});

// ================================================================
// SLIDE 12: Summary & Outlook
// ================================================================
const s12 = pres.addSlide();
s12.background = { fill: C.primary };
s12.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0,    w: 10, h: 0.06, fill: { color: C.accent  }, line: { type: "none" } });
s12.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.55, w: 10, h: 0.06, fill: { color: C.accent  }, line: { type: "none" } });

s12.addText("总结与展望", {
    x: 0.8, y: 0.45, w: 8.4, h: 0.70,
    fontSize: 36, bold: true, color: "FFFFFF", align: "center", fontFace: "Microsoft YaHei",
});
s12.addShape(pres.shapes.RECTANGLE, {
    x: 3.8, y: 1.18, w: 2.4, h: 0.02, fill: { color: C.accent }, line: { type: "none" },
});

// Achievement box
s12.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.7, y: 1.50, w: 8.6, h: 1.55,
    fill: { color: "1E4D8C" }, rectRadius: 0.06,
});

s12.addText("项目成果", {
    x: 1.00, y: 1.55, w: 8.00, h: 0.30,
    fontSize: 17, bold: true, color: "FFFFFF", fontFace: "Microsoft YaHei",
});

const achievements = [
    "✅ P0 功能 100% 完成（8 个阶段全部验收通过，核心调度链路完整闭环）",
    "✅ P1 增强交付（到货确认、UI 美化、AI 解释/审查/异常分析，答辩可用）",
    "✅ 前后端单元测试覆盖核心业务逻辑，状态机严密，非法转换即时拒绝",
    "✅ 代码规范、架构清晰、可扩展性强 · 4 周内从零到完整可演示系统",
];

achievements.forEach((ach, i) => {
    s12.addText(ach, {
        x: 1.00, y: 1.95 + i * 0.27, w: 8.00, h: 0.25,
        fontSize: 11.5, color: "CADCFC", fontFace: "Microsoft YaHei",
    });
});

// Future plans - two columns
// Left: P1 remaining
s12.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.70, y: 3.35, w: 4.10, h: 1.55,
    fill: { color: "1E4D8C" }, rectRadius: 0.06,
});
s12.addText("🔮 P1 剩余 · P2 规划", {
    x: 0.95, y: 3.42, w: 3.60, h: 0.28,
    fontSize: 14, bold: true, color: "FFFFFF", fontFace: "Microsoft YaHei",
});
s12.addText([
    { text: "• P1: 方案审查 F016 前端接入\n", options: { fontSize: 11, color: "A3C4F3", breakLine: true } },
    { text: "• P1: 方案对比 F009\n", options: { fontSize: 11, color: "A3C4F3", breakLine: true } },
    { text: "• P2: 运营统计看板 F018-F020\n", options: { fontSize: 11, color: "A3C4F3", breakLine: true } },
    { text: "• P2: Dashboard 数据可视化\n", options: { fontSize: 11, color: "A3C4F3", breakLine: true } },
    { text: "• P2: 绩效报表生成", options: { fontSize: 11, color: "A3C4F3" } },
], {
    x: 0.95, y: 3.80, w: 3.60, h: 1.00,
    fontFace: "Microsoft YaHei",
});

// Right: Tech evolution
s12.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.20, y: 3.35, w: 4.10, h: 1.55,
    fill: { color: "1E4D8C" }, rectRadius: 0.06,
});
s12.addText("🚀 技术演进方向", {
    x: 5.45, y: 3.42, w: 3.60, h: 0.28,
    fontSize: 14, bold: true, color: "FFFFFF", fontFace: "Microsoft YaHei",
});
s12.addText([
    { text: "• AI 模型：DQN/MLP+LSTM 调度优化\n", options: { fontSize: 11, color: "A3C4F3", breakLine: true } },
    { text: "• 地图：高德 API 集成（amap_service）\n", options: { fontSize: 11, color: "A3C4F3", breakLine: true } },
    { text: "• 可视化：Canvas 轨迹动画\n", options: { fontSize: 11, color: "A3C4F3", breakLine: true } },
    { text: "• 部署：Docker 一键启动\n", options: { fontSize: 11, color: "A3C4F3", breakLine: true } },
    { text: "• 扩展：MySQL 生产数据库", options: { fontSize: 11, color: "A3C4F3" } },
], {
    x: 5.45, y: 3.80, w: 3.60, h: 1.00,
    fontFace: "Microsoft YaHei",
});

// Thank you
s12.addText("感谢聆听  ·  Q & A", {
    x: 0.8, y: 5.10, w: 8.4, h: 0.40,
    fontSize: 18, color: "A3C4F3", align: "center", fontFace: "Microsoft YaHei",
});

// ================================================================
// EXPORT
// ================================================================
const outputPath = "D:/Git Demo/LogisticSystem/My_doc/ppt/项目演示PPT_v3.pptx";

pres.writeFile({ fileName: outputPath })
    .then(() => console.log("SUCCESS: " + outputPath))
    .catch(err => console.error("ERROR:", err));
