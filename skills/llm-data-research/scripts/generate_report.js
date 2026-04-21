#!/usr/bin/env node
/**
 * 大模型数据服务市场调研 - Word 报告生成脚本
 * 用法: NODE_PATH=$(npm root -g) \
 *        node generate_report.js --data JSON文件 [--output 输出目录]
 */

// ── 环境检查 ─────────────────────────────────────────────
try {
  require("docx");
} catch (e) {
  console.error("❌ 缺少 docx 包，请运行: npm install -g docx");
  process.exit(1);
}

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, WidthType, BorderStyle, ShadingType,
  Header, Footer, PageNumber, NumberFormat, PageBreak,
  LevelFormat, convertInchesToTwip,
} = require("docx");
const fs   = require("fs");
const path = require("path");
const os   = require("os");

// ── 常量 ─────────────────────────────────────────────────
const PAGE_WIDTH_DXA    = 11906;   // A4 宽
const PAGE_HEIGHT_DXA   = 16838;   // A4 高
const MARGIN_DXA        = 1134;    // 2cm 页边距
const CONTENT_WIDTH_DXA = PAGE_WIDTH_DXA - 2 * MARGIN_DXA;  // 9638

const COLOR_NAVY        = "1A3A6B";  // 深蓝主色
const COLOR_ACCENT      = "E67E22";  // 橙色强调（与 Excel 一致）
const COLOR_HEADER_FILL = "1A3A6B";  // 表头背景
const COLOR_ALT_FILL    = "EEF3FB";  // 隔行填充
const COLOR_WHITE       = "FFFFFF";
const COLOR_TEXT_DARK   = "2C3E50";
const COLOR_TEXT_GRAY   = "7F8C8D";

const FONT_BODY         = "微软雅黑";
const FONT_SIZE_BODY    = 22;   // 11pt
const FONT_SIZE_SMALL   = 20;   // 10pt
const FONT_SIZE_H1      = 34;   // 17pt
const FONT_SIZE_H2      = 28;   // 14pt
const FONT_SIZE_H3      = 24;   // 12pt
const FONT_SIZE_COVER   = 52;   // 26pt 封面主标题

// ── 边框辅助 ─────────────────────────────────────────────
function thinBorder(color = "CCCCCC") {
  return { style: BorderStyle.SINGLE, size: 6, color };
}

function cellBorders(color = "CCCCCC") {
  const b = thinBorder(color);
  return { top: b, bottom: b, left: b, right: b };
}

// ── 表格辅助 ─────────────────────────────────────────────
function makeHeaderRow(headers, colWidths) {
  return new TableRow({
    tableHeader: true,
    children: headers.map((h, i) =>
      new TableCell({
        width: { size: colWidths[i], type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, color: "auto", fill: COLOR_HEADER_FILL },
        borders: cellBorders(COLOR_HEADER_FILL),
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: String(h),
            bold: true,
            color: COLOR_WHITE,
            size: FONT_SIZE_SMALL,
            font: FONT_BODY,
          })],
        })],
      })
    ),
  });
}

function makeDataRow(cells, colWidths, isAlt) {
  const fill = isAlt ? COLOR_ALT_FILL : COLOR_WHITE;
  return new TableRow({
    children: cells.map((c, i) =>
      new TableCell({
        width: { size: colWidths[i], type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, color: "auto", fill },
        borders: cellBorders(),
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          children: [new TextRun({
            text: String(c ?? ""),
            size: FONT_SIZE_SMALL,
            font: FONT_BODY,
            color: COLOR_TEXT_DARK,
          })],
        })],
      })
    ),
  });
}

function makeTable(headers, rows, colWidths) {
  const totalWidth = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      makeHeaderRow(headers, colWidths),
      ...rows.map((row, idx) => makeDataRow(row, colWidths, idx % 2 === 1)),
    ],
  });
}

// ── 段落辅助 ─────────────────────────────────────────────
function sectionHeading(text, level = 1) {
  const size  = level === 1 ? FONT_SIZE_H1 : level === 2 ? FONT_SIZE_H2 : FONT_SIZE_H3;
  const hlevel = level === 1 ? HeadingLevel.HEADING_1
               : level === 2 ? HeadingLevel.HEADING_2
               : HeadingLevel.HEADING_3;
  return new Paragraph({
    heading: hlevel,
    spacing: { before: level === 1 ? 360 : 240, after: level === 1 ? 200 : 140 },
    children: [new TextRun({
      text,
      bold: true,
      color: COLOR_NAVY,
      size,
      font: FONT_BODY,
    })],
  });
}

function bodyPara(text, { bold = false, color = COLOR_TEXT_DARK, size = FONT_SIZE_BODY, spacing = {} } = {}) {
  return new Paragraph({
    spacing: { after: 120, ...spacing },
    children: [new TextRun({ text: String(text ?? ""), bold, color, size, font: FONT_BODY })],
  });
}

function labelValuePara(label, value) {
  return new Paragraph({
    spacing: { after: 100 },
    children: [
      new TextRun({ text: label + "：", bold: true, color: COLOR_NAVY, size: FONT_SIZE_SMALL, font: FONT_BODY }),
      new TextRun({ text: String(value ?? ""), size: FONT_SIZE_SMALL, font: FONT_BODY, color: COLOR_TEXT_DARK }),
    ],
  });
}

function bulletPara(text) {
  return new Paragraph({
    spacing: { after: 100 },
    indent: { left: 360, hanging: 240 },
    children: [
      new TextRun({ text: "• ", bold: true, color: COLOR_ACCENT, size: FONT_SIZE_BODY, font: FONT_BODY }),
      new TextRun({ text: String(text ?? ""), size: FONT_SIZE_BODY, font: FONT_BODY, color: COLOR_TEXT_DARK }),
    ],
  });
}

function spacer(size = 160) {
  return new Paragraph({ spacing: { before: size, after: 0 }, children: [] });
}

function divider() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "DDDDDD" } },
    spacing: { before: 160, after: 160 },
    children: [],
  });
}

// ── 章节渲染器 ────────────────────────────────────────────

function renderCoverPage(meta) {
  return [
    spacer(convertInchesToTwip(1.5)),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 240 },
      children: [new TextRun({
        text: "大模型数据服务市场洞察报告",
        bold: true, color: COLOR_NAVY,
        size: FONT_SIZE_COVER, font: FONT_BODY,
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({
        text: "LLM Data Service Market Insight Report",
        color: COLOR_TEXT_GRAY, size: 28, font: FONT_BODY,
      })],
    }),
    spacer(convertInchesToTwip(0.5)),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 160 },
      children: [new TextRun({
        text: `采集日期：${meta.report_date}`,
        color: COLOR_TEXT_DARK, size: FONT_SIZE_BODY, font: FONT_BODY,
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 160 },
      children: [new TextRun({
        text: `数据量：${meta.data_summary}`,
        color: COLOR_TEXT_GRAY, size: FONT_SIZE_SMALL, font: FONT_BODY,
      })],
    }),
    spacer(convertInchesToTwip(0.5)),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 80 },
      children: [new TextRun({
        text: "仅供内部参考 · 请勿对外传播",
        color: COLOR_ACCENT, bold: true, size: FONT_SIZE_SMALL, font: FONT_BODY,
      })],
    }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

function renderTableSection(section) {
  if (!section?.table) return [];
  const { headers, rows } = section.table;
  // 均分列宽
  const colW = Math.floor(CONTENT_WIDTH_DXA / headers.length);
  const colWidths = headers.map((_, i) =>
    i === headers.length - 1
      ? CONTENT_WIDTH_DXA - colW * (headers.length - 1)
      : colW
  );
  return [
    sectionHeading(section.title, 1),
    makeTable(headers, rows || [], colWidths),
    spacer(),
  ];
}

function renderVendorAssessment(section) {
  if (!section?.items?.length) return [sectionHeading(section.title, 1), spacer()];
  const items = section.items;
  const colWidths = [2200, CONTENT_WIDTH_DXA - 2200];
  const elems = [sectionHeading(section.title, 1)];
  for (const item of items) {
    elems.push(sectionHeading(item.vendor || "（未知数商）", 2));
    const rows = [
      ["生产能力规模", item.production_scale || "—"],
      ["专家储备质量", item.expert_pool || "—"],
      ["业务侧重方向", item.business_focus || "—"],
      ["大厂绑定程度", item.client_binding || "—"],
      ["数据来源", item.source || "—"],
    ];
    elems.push(makeTable(["维度", "评估结果"], rows, colWidths));
    elems.push(spacer());
  }
  return elems;
}

function renderOverseasStrategy(section) {
  if (!section?.items?.length) return [sectionHeading(section.title, 1), spacer()];
  const elems = [sectionHeading(section.title, 1)];
  for (const item of section.items) {
    elems.push(sectionHeading(item.company || "（未知公司）", 2));
    elems.push(labelValuePara("最新信号", item.signal));
    elems.push(labelValuePara("战略含义", item.implication));
    elems.push(labelValuePara("来源", item.source));
    elems.push(spacer(80));
  }
  return elems;
}

function renderVendorDirections(section) {
  if (!section?.items?.length) return [sectionHeading(section.title, 1), spacer()];
  const colWidths = [1800, CONTENT_WIDTH_DXA - 1800];
  const elems = [sectionHeading(section.title, 1)];
  for (const item of section.items) {
    elems.push(sectionHeading(item.vendor || "（未知厂商）", 2));
    const rows = [
      ["战略方向", item.direction || "—"],
      ["核心数据类型", item.core_data_type || "—"],
      ["关键信号", item.key_signal || "—"],
      ["推断逻辑", item.reasoning || "—"],
    ];
    elems.push(makeTable(["维度", "内容"], rows, colWidths));
    elems.push(spacer());
  }
  return elems;
}

function renderKeyInsights(section) {
  if (!section?.items?.length) return [sectionHeading(section.title, 1), spacer()];
  const elems = [sectionHeading(section.title, 1)];
  for (let i = 0; i < section.items.length; i++) {
    const item = section.items[i];
    const confColor = item.confidence === "高" ? "27AE60"
                    : item.confidence === "中" ? "F39C12"
                    : "C0392B";
    elems.push(new Paragraph({
      spacing: { before: 160, after: 80 },
      children: [
        new TextRun({ text: `洞察 ${i + 1}  `, bold: true, color: COLOR_NAVY, size: FONT_SIZE_BODY, font: FONT_BODY }),
        new TextRun({ text: `[${item.confidence || "—"}可信度]`, bold: true, color: confColor, size: FONT_SIZE_SMALL, font: FONT_BODY }),
      ],
    }));
    elems.push(bodyPara(item.insight, { bold: true, size: FONT_SIZE_BODY }));
    elems.push(labelValuePara("数据支撑", item.support));
    elems.push(labelValuePara("来源", item.source));
    if (i < section.items.length - 1) elems.push(divider());
  }
  elems.push(spacer());
  return elems;
}

function renderTrendChanges(section) {
  if (!section?.items?.length) return [sectionHeading(section.title, 1), spacer()];
  const elems = [sectionHeading(section.title, 1)];
  for (const item of section.items) {
    elems.push(bulletPara(item));
  }
  elems.push(spacer());
  return elems;
}

// ── 文档构建 ──────────────────────────────────────────────
function buildDocument(data) {
  const meta = data.meta || {};
  const secs = data.sections || {};
  const reportDate = meta.report_date || new Date().toISOString().slice(0, 10);

  // 页眉
  const header = new Header({
    children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "BBBBBB" } },
      spacing: { after: 120 },
      children: [
        new TextRun({ text: `大模型数据服务市场洞察报告  ${reportDate}`, size: 18, color: COLOR_TEXT_GRAY, font: FONT_BODY }),
      ],
    })],
  });

  // 页脚
  const footer = new Footer({
    children: [new Paragraph({
      border: { top: { style: BorderStyle.SINGLE, size: 6, color: "BBBBBB" } },
      spacing: { before: 120 },
      children: [
        new TextRun({ text: "大模型数据服务市场调研 | 仅供内部参考  ", size: 18, color: COLOR_TEXT_GRAY, font: FONT_BODY }),
        new TextRun({ children: [PageNumber.CURRENT], size: 18, color: COLOR_TEXT_GRAY, font: FONT_BODY }),
        new TextRun({ text: " / ", size: 18, color: COLOR_TEXT_GRAY, font: FONT_BODY }),
        new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, color: COLOR_TEXT_GRAY, font: FONT_BODY }),
      ],
    })],
  });

  // 章节内容
  const children = [
    ...renderCoverPage(meta),
    ...renderTableSection(secs.market_size),
    ...renderTableSection(secs.recruitment_signals),
    ...renderVendorAssessment(secs.vendor_assessment),
    ...renderOverseasStrategy(secs.overseas_strategy),
    ...renderVendorDirections(secs.vendor_directions),
    ...renderTableSection(secs.service_provider_landscape),
    ...renderKeyInsights(secs.key_insights),
    ...renderTrendChanges(secs.trend_changes),
  ];

  return new Document({
    styles: {
      default: {
        document: {
          run: { font: FONT_BODY, size: FONT_SIZE_BODY, color: COLOR_TEXT_DARK },
        },
      },
    },
    sections: [{
      properties: {
        page: {
          size:   { width: PAGE_WIDTH_DXA, height: PAGE_HEIGHT_DXA },
          margin: { top: MARGIN_DXA, bottom: MARGIN_DXA, left: MARGIN_DXA, right: MARGIN_DXA },
        },
      },
      headers: { default: header },
      footers: { default: footer },
      children,
    }],
  });
}

// ── 主函数 ────────────────────────────────────────────────
async function main() {
  const args = process.argv.slice(2);
  let dataFile = null;
  let outputDir = path.join(os.homedir(), "Downloads");

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--data"   && args[i + 1]) { dataFile  = args[++i]; }
    if (args[i] === "--output" && args[i + 1]) { outputDir = args[++i]; }
  }

  if (!dataFile) {
    console.error("用法: node generate_report.js --data JSON文件 [--output 输出目录]");
    process.exit(1);
  }

  // 解析路径（支持 ~）
  dataFile  = dataFile.replace(/^~/, os.homedir());
  outputDir = outputDir.replace(/^~/, os.homedir());

  const raw  = fs.readFileSync(dataFile, "utf8");
  const data = JSON.parse(raw);

  const doc    = buildDocument(data);
  const buffer = await Packer.toBuffer(doc);

  const reportDate = (data.meta?.report_date || new Date().toISOString().slice(0, 10));
  const filename   = `大模型数据市场洞察报告_${reportDate}.docx`;
  const outPath    = path.join(outputDir, filename);

  fs.writeFileSync(outPath, buffer);
  console.log(`Word 报告已保存: ${outPath}`);
  return outPath;
}

main().catch(err => { console.error("生成报告失败:", err.message); process.exit(1); });
