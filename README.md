# 大学生大创申报助手

可安装的 Codex Skill：`college-innovation-project-skill`。默认中文，支持从通知解析、方向与选题到原模板申报草稿和审查。它由 Codex 执行工作流，不是独立网站，也不包含自动提交或独立大模型服务。

## 安装

将安装包解压，保留完整的 `college-innovation-project-skill` 文件夹。默认可复制到 `$CODEX_HOME/skills/`；未设置CODEX_HOME时为 `~/.codex/skills/`。包内安装脚本执行同样的本地复制，不联网、不改其他配置、不覆盖已有同名技能：

```bash
python3 /解压路径/college-innovation-project-skill/scripts/install.py
```

可先预览或指定目录（destination指技能集合目录，不是具体技能目录）：

```bash
python3 /解压路径/college-innovation-project-skill/scripts/install.py --dry-run
python3 /解压路径/college-innovation-project-skill/scripts/install.py --destination /你的技能集合目录
```

若同名目录已存在，先检查旧版本并手动备份，不盲目覆盖。安装后新建会话查看技能是否可用；若列表未刷新，重新打开Codex再确认。安装脚本仅在执行时复制技能，不会修改其他Codex配置。

也可以从GitHub克隆后安装（私有仓库需要相应访问权限）：

```bash
git clone https://github.com/longkou1988/college-innovation-project-skill.git
python3 college-innovation-project-skill/scripts/install.py
```

## WorkBuddy导入

WorkBuddy市场需要额外的顶层元数据。请使用Release中的 `college-innovation-project-skill-workbuddy.zip`，不要上传旧的Codex安装包。兼容包补充version、display_name、display_name_en、description_zh、description_en、author和category；原始SKILL.md保留Codex格式。

在WorkBuddy上传兼容ZIP即可；`scripts/install.py`只负责Codex本地安装。尚未执行WorkBuddy服务端导入或市场审核。

重新构建兼容包：

```bash
python3 scripts/build_workbuddy.py --output /输出目录/college-innovation-project-skill-workbuddy.zip
```

字段存于 `packaging/workbuddy.json`，按[WorkBuddy官方Skill指南](https://open.workbuddy.cn/docs/skill)及实际导入错误配置。

## 使用

在Codex中输入：

> 请使用 $college-innovation-project-skill，读取我上传的本年度申报通知、指南、申报书及信息表，帮助我完成大创项目选题和申报。

可以追加“电气工程及其自动化、大二、3人团队、有Python基础、无实验室”“已有方向，直接推荐5个选题”“按既定选题写草稿”等。已有材料和决定不会重复询问。主要步骤：规则摘要→确定真实项目类型→必要专业/资源信息→5个方向（无方向时）→5个具体选题→方案蓝图→映射原表→草稿与审查。

通知可以是文件或完整粘贴文本。没有真实模板也可先写内容草稿，但不会称已完成模板填报。默认保留项目状态在本次输出目录，学生资料不写入技能包。用户中途更换方向、类型或资源后，仅更新受影响内容。

## 文件能力与限制

核心技能无需额外Python包。可选 `inspect_office.py` 使用Python标准库只读提取DOCX/XLSX；PDF/OCR、保留版式的Office写回和视觉排版核验依赖运行环境已有工具。环境不支持时会给可粘贴文本草稿并说明限制，不用改扩展名伪装文档。不执行宏，不自动安装依赖或上传文件。

推荐把本年度通知、原模板、信息表一起提供。内置2026材料是经原通知/附件核对的文字摘要，仅用于明确请求的演练，不附带原文件，不代表其他学校规则或当前开放申报。

## 目录与职责

```text
college-innovation-project-skill/
├── SKILL.md                        入口、流程及边界
├── agents/openai.yaml              显示名称与默认调用提示
├── README.md                       安装与使用
├── references/
│   ├── workflow.md                 规则溯源、交互与变更
│   ├── topic-design.md             5方向/5题目及方案设计
│   ├── application-writing.md      文档处理、模板映射与写作
│   ├── review-checklist.md         资格/内容/数字/格式审查
│   ├── state-schema.md             状态字段约定
│   └── example-2026.md             历史示例摘要
├── assets/
│   ├── project-context.json        本次项目状态种子
│   └── topic-card.md               12项选题分析结构
├── scripts/
│   ├── inspect_office.py           Office结构提取
│   └── install.py                  不覆盖旧文件的本地安装
├── examples/example-session.md     从输入到待补草稿的完整演练
└── tests/
    ├── test_scripts.py             辅助脚本功能测试
    ├── scenarios.md                工作流行为回归输入与标准
    └── validation-report.md        本版本实际检查结果与局限
```

运行辅助脚本测试：`python3 -m unittest discover -s /技能路径/tests -p 'test_*.py'`。行为场景需在模型会话中实际执行；结构检查通过不等于所有生成内容自动正确。
