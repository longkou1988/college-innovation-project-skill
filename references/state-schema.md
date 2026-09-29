# ProjectContext 字段约定

[初始JSON](../assets/project-context.json) 是可复制的状态种子，不是自动验证的JSON Schema。按项目需要填充，不要求向用户展示全部JSON。只保存业务状态与依据，不保存隐含推理。

- `schema_version`：本状态约定版本。
- `project_id`、`revision`、`stage`：项目身份、递增版本和当前阶段。
- `sources`：每项含id、name、path_or_url、role、organization、year、batch、published_at、scope、version、read_status。未知用null。
- `evidence`：每项含id、kind（四类证据之一）、claim、source_id、locator、quote_or_user_statement、status。AI建议不能引用虚构来源。用户确认方案不使其变为已经取得的成果。
- `rules`：每个值采用`{value, evidence_ids, qualifier, status}`，包括school、year、batch、application_level、recommendation_path、project_types、eligible_students、team_size、leader_requirements、advisor_requirements、enterprise_advisor_required、duration、start_end_dates、application_limit、priority_areas、prohibited_conditions、funding_rules、deadline、submission_materials、review_process、midterm_requirements、completion_requirements、change_process。
- `track`：原名、依据及用户选择；不存在于通知中的类型不得直接选用。
- `student_profile`：school、college、major_raw、major_normalized、major_category、major_code、grade、team_members、advisors、resources、skills。需要才记录个人信息，未知不造。
- `interests/directions/topics`：候选及稳定ID；`selected_direction/selected_topic`记录选项、用户消息依据或代选授权。
- `blueprint`：title、background、problem、research_object、goals、tasks、methods、route、innovations、schedule、outputs、resources、roles、budget、risks；任务关联ID。
- `form_schema`：来源版本、按顺序排列的fields，各字段含位置/限制/填写主体/来源映射/状态。
- `gaps`：field、reason、blocking_scope、needed_input；仅阻塞依赖它的部分。
- `draft`：版本、文件路径、所用规则/蓝图/模板版本、status。
- `review`：项目、状态、证据、修复动作、最终结论。
- `stale`：因变更需更新的部分；`changes`记录变更摘要及影响。

阶段建议：intake → rules → profile → direction → topic → blueprint → drafting → reviewed。这不是硬性问答闸门；已有信息允许跳过问题、保留解析步骤。恢复时读状态及其来源，核对最新输入，更新后清除已解决的stale条目。保存前确认JSON能解析，避免覆盖他人编辑。
