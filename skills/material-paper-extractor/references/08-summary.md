# Cross-Paper Summary Prompt

## Purpose

Generate a consolidated cross-paper evaluation summary based on all individual paper evaluation reports.

## Input

Read all: `{output_base}/07_evaluate/*_evaluation.md`
Optionally: `{output_base}/08_summary/stats.md`

## Output Path

**IMPORTANT: Output MUST be written to exactly this path:**
`{output_base}/08_summary/evaluation_summary.md`

## Report Structure

### Section 1: 概述

- Number of papers
- Overall quality rating (优秀/良好/一般/需改进)
- Paper IDs and material systems list

### Section 2: 整体数据统计

- Total papers, materials, property measurements
- Per-paper table: file → materials → properties → brief conclusion

### Section 3: 共性问题分析（按严重程度排序）

- **高频**：出现在 ≥3 篇
- **中频**：出现在 2 篇
- **低频**：出现在 1 篇

Each issue: description, frequency, example (paper ID + source), impact analysis.

### Section 4: 准确提取领域总结

Fields consistently extracted correctly across papers.

### Section 5: 优化建议优先级矩阵

| 优先级 | Action Item | 影响范围 | 实施难度 | 预期收益 |
|--------|-------------|----------|----------|----------|

P0: 影响多数论文 / P1: 影响部分 / P2: 少数改进

### Section 6: 各论文评估摘要

2-3 sentence summary per paper.

## Constraints

- All analysis based on evaluation reports only — no speculation
- Cite specific paper IDs
- Write in Chinese
- Output report directly — no preamble
