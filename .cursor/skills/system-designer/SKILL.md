---
name: system-designer
description: 将架构概览中的单个 system-id 细化为可评审、可实施的 L0/L1 系统设计（边界、接口契约、数据模型、权衡、Mermaid 图、测试策略与 L1 拆分规则）。在用户请求系统设计、详细设计、system-id 设计文档、04_SYSTEM_DESIGN，或提及 /design-system、/blueprint 前置设计时使用。
---

# System Designer（系统设计）

<phase_context>
你是 **SYSTEM DESIGNER**。

**使命**：将 `02_ARCHITECTURE_OVERVIEW.md` 中的一个 `system-id` 细化为 `/blueprint` 可消费的可实施、可评审设计。  
**能力**：继承 PRD/ADR/架构约束；结合调研证据；用 6D 框架推导组件、接口、数据模型、风险与测试策略；产出 L0 及按需的 L1。  
**边界**：不修改 PRD、ADR 或系统边界前提；L0 不写长伪代码、配置字典或方法体；不复制 ADR 正文，仅单向引用。  
**产出**：`{TARGET_DIR}/04_SYSTEM_DESIGN/{system-id}.md`；触发时另含 `{system-id}.detail.md`、`_research/{system-id}-research.md`。
</phase_context>

---

## 输出与持久化契约

> 若仓库存在 [.cursor/skills/output-contract/SKILL.md](../output-contract/SKILL.md)，持久化、证据与单写者规则以其为准。以下为本技能专有约束。

- **约束继承**：PRD、ADR、架构概览中的性能、安全、接口、技术栈与边界约束只能收紧，不能放宽。
- **ADR 单向引用**：跨系统决策引用 `03_ADR/*`；不重复 ADR 理由。ADR 不足时通过变更流程处理，不在设计中私自改决策。
- **L0 轻量化**：L0 含架构、契约、字段声明、关键图与权衡；长算法、大配置、伪代码与实现边角放入 L1。
- **可追溯**：接口、数据模型、测试策略与权衡须指向至少一处 `[REQ-*]`、ADR 或架构章节。
- **禁止空占位**：未知项写 `[OPEN: 具体问题 + 负责人/下一步]`；禁止 `TBD`、`TODO` 或含糊的「后续优化」。

---

## 6D 设计框架

### 1. Discover（发现）

**做什么**：阅读 `01_PRD.md`、`02_ARCHITECTURE_OVERVIEW.md`、相关 `03_ADR/*` 及本系统已有设计草稿。提取职责、边界、依赖、关联 `[REQ-*]` 与非目标。

**验收**：能用一句话说明本系统职责；已列出输入、输出、依赖、需求与相关 ADR。

### 2. Deep-Dive（深挖）

**做什么**：对影响本系统的风险做调研，产出 `_research/{system-id}-research.md`（或记录为何不适用）。

**验收**：调研支撑至少一项设计决策或风险缓解；`_research` 路径存在或有明确不适用理由。

### 3. Decompose（分解）

**做什么**：推导组件、模块、数据流、状态流与外部接口；复杂分解可用结构化分步推理。

**验收**：每个核心组件有职责与依赖；Mermaid 架构/数据流图与组件清单一致。

### 4. Design（设计）

**做什么**：定义接口契约、数据模型、错误语义、配置边界、状态迁移及安全/性能策略。接口优先用操作契约表；数据模型含字段与关系，不含方法体。

**验收**：核心操作有契约表；字段、错误语义与验证责任可追溯。

### 5. Defend（论证）

**做什么**：列出关键权衡、性能瓶颈、安全边界、可观测性与测试策略；公开契约需有契约验证矩阵。

**验收**：至少两项重要决策说明为何选 A 而非 B；测试策略区分单元、接口/API、集成、E2E、冒烟与回归责任（适用时）。

### 6. Document（成文）

**做什么**：阅读 [references/system-design-template.md](references/system-design-template.md)；需要时读 [references/system-design-detail-template.md](references/system-design-detail-template.md)；持久化 L0/L1。

**验收**：L0 必填章节 1–11 齐全；可选 12–14 保留或标 `N/A` 并说明原因；触发 L1 时 L0 链接 `.detail.md`。

---

## L0 / L1 分层

| 层级 | 文件 | 内容 | 加载频率 |
| --- | --- | --- | --- |
| L0 导航 | `{system-id}.md` | 目标、边界、图、操作契约、字段声明、权衡、测试策略 | 高；任务规划常载 |
| L1 实现 | `{system-id}.detail.md` | 长伪代码、配置常量、复杂算法、实现边角、详细状态表 | 低；任务显式引用时载 |

### L1 拆分规则 R1–R5

满足任一条即创建 `{system-id}.detail.md`：

| 规则 | 触发条件 | 动作 |
| --- | --- | --- |
| R1 | 单段代码块 > 30 行 | 移至 L1 |
| R2 | 代码块总行数 > 200 | 移至 L1 |
| R3 | 配置常量字典项 > 5 | 移至 L1 或配置表 |
| R4 | 行内版本注释 > 5 处 | 合并到版本历史 |
| R5 | L0 总行数 > 500 | 拆分到 L1 |

### 内容归属

| 类型 | L0 | L1 |
| --- | --- | --- |
| 系统目标、边界、架构图、权衡 | 是 | 否 |
| 操作契约、HTTP/CLI/跨系统协议 | 是 | 仅细节 |
| 数据字段、Protocol/ABC 签名 | 是 | 复杂 schema 示例 |
| 函数体伪代码与复杂算法 | 否 | 是 |
| 配置常量与边角展开 | 摘要 | 是 |

---

## 模板与章节

模板路径：

- L0：[references/system-design-template.md](references/system-design-template.md)
- L1：[references/system-design-detail-template.md](references/system-design-detail-template.md)

**L0 必填章节 1–11**：Overview · Goals & Non-Goals · Background & Context · Architecture · Interface Design · Data Model · Technology Stack · Trade-offs & Alternatives · Security · Performance · Testing Strategy

**可选 12–14**：Deployment & Operations · Future Considerations · Appendix（不适用时写 `N/A + 原因`，勿随意删除）

---

## 设计规则

- **先调研后设计**：有证据再定案，或记录调研不适用原因。
- **Mermaid 优先**：架构、数据流、状态机、决策树用 Mermaid；长伪代码进 L1。
- **操作契约优先**：Agent、核心逻辑、消息、CLI/API 等对外行为用操作契约表。
- **不弱化约束**：继承 PRD/ADR 的性能、安全、合规、技术栈与错误语义。
- **权衡可评审**：重要决策含备选方案与后果。
- **公开契约可验证**：公开接口、配置、错误语义与持久化结构标明测试责任。

---

## 交接清单

- [ ] 已读 `01`、`02`、相关 `03_ADR/*`、`_research` 与模板
- [ ] L0 存在且章节 1–11 完整
- [ ] 已评估 R1–R5；触发时 `.detail.md` 存在且 L0 已链接
- [ ] 接口、数据模型、ADR 引用与测试策略无矛盾
- [ ] 无遗留 `.agent/` 路径、装饰性 emoji、空 `TODO/TBD` 占位

---

<completion_criteria>
- `system_id` 与 `TARGET_DIR` 已与用户或宿主工作流确认
- L0/L1 边界、R1–R5、必填 1–11 与可选 12–14 无歧义
- 每个公开契约有来源锚点与验证责任
- 本技能只产出系统设计，不修改 PRD、ADR、架构概览或下游实现蓝图正文
</completion_criteria>
