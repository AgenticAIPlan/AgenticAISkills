# Matrix and Cases

当前项目中，生态案例和硬件兼容矩阵都是已实现模块，Skill 可围绕这些真实结构进行维护。

## 生态案例

案例页位于 `src/pages/AllCases.tsx`，数据管理位于 `src/hooks/useCasesData.ts`。

当前真实能力包括：

- 案例新增、编辑、删除
- 关键词搜索
- 按行业、硬件筛选
- 最多 3 条置顶
- 首页/列表按置顶优先、再按时间排序

案例默认字段以 `title`、`description`、`industry`、`hardware`、`url` 为主，不应擅自扩展复杂 schema。

## 硬件兼容矩阵

矩阵组件位于 `src/components/AdaptationMatrix.tsx`，数据文件示例位于 `matrix-data.json`。

### 结构

- `models[]`：模型或平台
- `hardwares[]`：硬件厂商与具体型号
- `matrix{}`：以 `itemId_hardwareId` 为键的适配状态映射

### 当前状态值

前端显式支持以下状态：

- `已跑通`
- `适配中`
- `规划中`

Skill 在维护矩阵时必须把状态收敛到这三个值，避免写入前端未识别的新标签。

## 适配信息维护建议

- 新增硬件或模型前，先确认页面是否已支持相应展示结构
- 没有证据支撑时，不要把状态直接写成“已跑通”
- 若只是演示数据，应在交付说明中注明“示例数据/演示数据”，避免被误当成生产事实
