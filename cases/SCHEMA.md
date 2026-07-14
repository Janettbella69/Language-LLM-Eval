# Case 字段口径

每行一个 JSON 对象(JSONL):

| 字段 | 说明 |
|---|---|
| `id` | `<维度>-<子类>-<序号>`,如 `A-KAS-01` |
| `dim` | 维度路径,如 `grammar/kasus`、`idiomatic/register` |
| `type` | `gen`(生成任务)/ `judge`(判断任务) |
| `prompt` | 发给被测模型的原始 prompt(中文或德语,模拟真实用户) |
| `target` | 这条 case 埋的考察点(一句话) |
| `gold_criteria` | 标注判据:什么算 pass、什么算 major——标注时**只对照这里** |
| `failure_hypothesis` | 预期的失败模式(**实测前只是假设**,不进报告) |
| `reviewed` | 德语审校状态:`false` = 未过人工审校,不得用于正式跑测 |

## 审校规则

1. 种子 case 由 AI 起草,**德语专业人工审校后**才置 `reviewed: true`。
2. 审校看三点:prompt 德语是否地道、考察点是否真实存在(不是伪规则)、gold_criteria 是否可操作。
3. 扩充 case 时保持每维度的 gen/judge 比例约 6:4。
