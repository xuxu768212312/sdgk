const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak
} = require("docx");

// ── Data ──────────────────────────────────────────────────────────────────
const target = 119781;

// Tier 1: 冲 (24) — rank 93k–114.5k
const chong = [
  [93036, "济南大学", "新闻传播学类(济南走读)", 4],
  [93128, "山东工商学院", "财务管理", 24],
  [93218, "山东农业大学", "网络与新媒体", 50],
  [94077, "青岛理工大学", "会计学(临沂校区)", 210],
  [94111, "南通大学", "建筑学", 4],
  [94377, "山东工商学院", "审计学", 27],
  [94453, "山东农业大学", "金融学", 125],
  [94483, "鲁东大学", "历史学(师范类)", 81],
  [94564, "徐州工程学院", "汉语言文学", 6],
  [94632, "南京工业大学", "城乡规划", 3],
  [94821, "青岛理工大学", "英语", 71],
  [94964, "青岛理工大学", "日语", 5],
  [95199, "滨州医学院", "中医学(国医传承班)", 36],
  [95247, "山东财经大学", "文化产业管理(地方专项计划)", 10],
  [95840, "山东农业大学", "国际经济与贸易", 45],
  [96051, "南京审计大学金审学院", "审计学", 3],
  [96464, "山东政法学院", "审计学", 85],
  [96493, "山东财经大学", "文化产业管理(济南走读)", 10],
  [96536, "济南大学", "应用心理学(师范类)", 39],
  [96685, "烟台大学", "汉语国际教育", 40],
  [96724, "聊城大学", "思想政治教育(师范类)", 167],
  [97090, "青岛大学", "金融学(地方专项计划)", 10],
  [97800, "山东科技大学", "金融学", 53],
  [98095, "曲阜师范大学", "文化产业管理", 18],
];

// Tier 2: 稳 (40) — rank 114.5k–134k
const wen = [
  [114738, "山东建筑大学", "广告学", 18],
  [114925, "山东理工大学", "英语", 79],
  [115107, "鲁东大学", "汉语国际教育", 80],
  [115231, "曲阜师范大学", "物流管理(地方专项计划)", 10],
  [115311, "南京特殊教育师范学院", "思想政治教育(师范类)", 2],
  [115490, "山东理工大学", "金融学(数字金融方向)", 66],
  [116523, "济南大学", "城乡规划(智慧城规创新班,济南走读)", 10],
  [116664, "青岛理工大学", "供应链管理", 16],
  [116974, "山东理工大学", "国际经济与贸易(数字贸易方向)", 60],
  [117073, "山东科技大学", "建筑学(地方专项计划)", 15],
  [117107, "山东理工大学", "工商管理", 155],
  [117311, "青岛大学", "经济学(数量经济学拔尖人才创新班)", 10],
  [117518, "山东管理学院", "会计学", 140],
  [117551, "山东政法学院", "经济学", 48],
  [117587, "青岛农业大学", "传播学", 55],
  [117605, "济南大学", "日语(济南走读)", 4],
  [117903, "山东航空学院", "汉语言文学(师范类)", 133],
  [118886, "江苏海洋大学", "食品质量与安全", 1],
  [119001, "山东理工大学", "社会工作(新文科实验班)", 60],
  [119040, "齐鲁师范学院", "财务管理", 55],
  [119128, "临沂大学", "汉语国际教育(师范类)", 48],
  [119439, "曲阜师范大学", "旅游管理", 48],
  [119487, "临沂大学", "英语(师范类)", 155],
  [119568, "潍坊学院", "思想政治教育(师范类)", 39],
  [119714, "山东青年政治学院", "会计学", 60],
  [119759, "青岛农业大学", "英语", 120],
  [119920, "济南大学", "药学", 68],
  [120197, "山东科技大学", "供应链管理(地方专项计划)", 15],
  [120377, "聊城大学", "会计学", 91],
  [120520, "青岛大学", "金融学", 10],
  [120585, "德州学院", "知识产权", 60],
  [120786, "齐鲁师范学院", "思想政治教育(师范类)", 80],
  [120894, "南京特殊教育师范学院", "学前教育(师范类)", 1],
  [120913, "济南大学", "旅游管理(济南走读)", 10],
  [120922, "鲁东大学", "国际经济与贸易", 71],
  [121174, "山东第一医科大学", "临床药学", 130],
  [121357, "南京特殊教育师范学院", "网络与新媒体", 2],
  [132040, "山东青年政治学院", "财务管理", 60],
  [132060, "南京特殊教育师范学院", "英语(师范类)", 5],
  [132084, "山东农业工程学院", "会计学", 37],
];

// Tier 3: 保 (26) — rank 134k–152k
const bao = [
  [134119, "齐鲁工业大学", "日语(地方专项计划)", 10],
  [134202, "齐鲁师范学院", "马克思主义理论", 30],
  [134218, "徐州工程学院", "市场营销", 2],
  [134230, "齐鲁师范学院", "历史学(师范类)", 77],
  [134374, "临沂大学", "社会工作", 40],
  [134389, "徐州工程学院", "电子商务", 1],
  [134481, "山东女子学院", "审计学", 40],
  [134494, "山东农业大学", "会计学(中外合作办学)", 130],
  [134578, "山东建筑大学", "市场营销", 63],
  [134814, "临沂大学", "应用心理学(师范类)", 80],
  [134883, "济宁医学院", "针灸推拿学", 54],
  [135162, "山东农业工程学院", "审计学", 21],
  [135352, "山东政法学院", "编辑出版学", 18],
  [135985, "山东政法学院", "英语", 53],
  [136004, "山东工商学院", "经济学", 32],
  [136102, "菏泽学院", "汉语言文学(师范类)", 83],
  [136204, "青岛农业大学", "物流管理", 125],
  [136291, "山东航空学院", "财务管理", 126],
  [136336, "南京传媒学院", "新闻传播学类", 2],
  [136340, "山东政法学院", "日语", 8],
  [136352, "山东女子学院", "财务管理", 40],
  [136391, "德州学院", "思想政治教育(师范类)", 33],
  [136593, "青岛农业大学", "日语", 60],
  [136687, "山东师范大学", "物流管理(中外合作办学)", 90],
  [136869, "齐鲁师范学院", "英语(师范类)", 80],
  [137133, "菏泽学院", "知识产权", 85],
];

// Tier 4: 垫 (6) — rank 152k+
const di = [
  [152128, "齐鲁工业大学", "市场营销(菏泽校区)", 135],
  [152132, "德州学院", "英语(师范类)", 42],
  [152732, "德州学院", "小学教育(师范类)", 40],
  [153072, "盐城师范学院", "物流管理", 5],
  [153203, "山东交通学院", "英语", 58],
  [153371, "聊城大学", "园林", 64],
];

// ── Colour constants ──────────────────────────────────────────────────────
const CHONG_COLOR = "FCE4D6"; // light orange
const WEN_COLOR   = "D5E8D4"; // light green
const BAO_COLOR   = "D6EAF8"; // light blue
const DI_COLOR    = "E8DAEF"; // light purple
const HEADER_BG   = "2E4057";
const HEADER_FG   = "FFFFFF";

// ── Helper functions ──────────────────────────────────────────────────────
const bdr = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
const borders = { top: bdr, bottom: bdr, left: bdr, right: bdr };
const margins = { top: 40, bottom: 40, left: 80, right: 80 };

function probText(tier) {
  switch (tier) {
    case "冲": return "20-40%";
    case "稳": return "60-80%";
    case "保": return "90%+";
    case "垫": return "99%+";
    default: return "";
  }
}

function tierColor(tier) {
  switch (tier) {
    case "冲": return CHONG_COLOR;
    case "稳": return WEN_COLOR;
    case "保": return BAO_COLOR;
    case "垫": return DI_COLOR;
    default: return "FFFFFF";
  }
}

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: HEADER_BG, type: ShadingType.CLEAR },
    margins,
    verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text, bold: true, color: HEADER_FG, font: "Microsoft YaHei", size: 18 })] })],
  });
}

function dataCell(text, width, fill, align) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins,
    verticalAlign: "center",
    children: [new Paragraph({ alignment: align || AlignmentType.LEFT, children: [new TextRun({ text: String(text), font: "Microsoft YaHei", size: 18 })] })],
  });
}

function buildTable(tier, data, startNum, totalWidth) {
  const colWidths = [480, 640, 1800, 3800, 900, 600, 640];
  // sum = 8860 — fits within 9026 A4 content width
  const rows = data.map(([rk, sn, mn, pc], i) => {
    const n = startNum + i;
    const fill = tierColor(tier);
    return new TableRow({
      children: [
        dataCell(n, colWidths[0], fill, AlignmentType.CENTER),
        dataCell(tier, colWidths[1], fill, AlignmentType.CENTER),
        dataCell(sn, colWidths[2], fill),
        dataCell(mn, colWidths[3], fill),
        dataCell(rk, colWidths[4], fill, AlignmentType.CENTER),
        dataCell(pc, colWidths[5], fill, AlignmentType.CENTER),
        dataCell(probText(tier), colWidths[6], fill, AlignmentType.CENTER),
      ],
    });
  });

  const headerRow = new TableRow({
    children: [
      headerCell("序号", colWidths[0]),
      headerCell("梯度", colWidths[1]),
      headerCell("学校", colWidths[2]),
      headerCell("专业", colWidths[3]),
      headerCell("最低位次", colWidths[4]),
      headerCell("计划", colWidths[5]),
      headerCell("概率", colWidths[6]),
    ],
  });

  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...rows],
  });
}

// ── Build document ────────────────────────────────────────────────────────
const TOTAL = 9026;

const children = [];

// Title
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "徐徐 · 2026年高考96志愿方案", bold: true, font: "Microsoft YaHei", size: 36 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: "参考位次：119,781（530分）  |  选科：生物+历史+政治  |  地域：山东为主，可接受江苏", font: "Microsoft YaHei", size: 20, color: "666666" })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 }, children: [new TextRun({ text: "数据来源：2025年山东高考常规批第1次投档数据", font: "Microsoft YaHei", size: 18, color: "999999" })] }));

// Gradient legend
const legendParas = [
  [CHONG_COLOR, "冲（20-40%）", "位次略低于目标院校，冲刺录取"],
  [WEN_COLOR,   "稳（60-80%）", "位次与目标持平，稳妥录取"],
  [BAO_COLOR,   "保（90%+）",   "位次高于目标，确保录取"],
  [DI_COLOR,    "垫（99%+）",   "大幅高于目标，防止滑档"],
];

children.push(new Paragraph({ spacing: { before: 0, after: 80 }, children: [new TextRun({ text: "梯度说明", bold: true, font: "Microsoft YaHei", size: 20 })] }));

for (const [color, label, desc] of legendParas) {
  children.push(new Paragraph({ spacing: { after: 40 }, children: [
    new TextRun({ text: `  ${label}  `, bold: true, font: "Microsoft YaHei", size: 18, color: "333333" }),
    new TextRun({ text: `— ${desc}`, font: "Microsoft YaHei", size: 18, color: "666666" }),
  ] }));
}

children.push(new Paragraph({ spacing: { after: 40 }, children: [
  new TextRun({ text: "  梯度比例：", bold: true, font: "Microsoft YaHei", size: 18 }),
  new TextRun({ text: "冲24 + 稳40 + 保26 + 垫6 = 96", font: "Microsoft YaHei", size: 18 }),
] }));
children.push(new Paragraph({ spacing: { after: 200 }, children: [
  new TextRun({ text: "  整体滑档风险：", bold: true, font: "Microsoft YaHei", size: 18 }),
  new TextRun({ text: "< 1%（垫底志愿录取概率99%+）", font: "Microsoft YaHei", size: 18, color: "2E7D32" }),
] }));

// Separator
children.push(new Paragraph({
  spacing: { after: 200 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E4057", space: 1 } },
  children: [],
}));

// ── 冲 ──
children.push(new Paragraph({ spacing: { before: 200, after: 100 }, children: [new TextRun({ text: "一、冲（24个志愿 · 位次 93,000~114,500 · 录取概率20-40%）", bold: true, font: "Microsoft YaHei", size: 22, color: "D35400" })] }));
children.push(buildTable("冲", chong, 1, TOTAL));

// ── 稳 ──
children.push(new Paragraph({ spacing: { before: 400, after: 100, pageBreakBefore: true }, children: [new TextRun({ text: "二、稳（40个志愿 · 位次 114,500~134,000 · 录取概率60-80%）", bold: true, font: "Microsoft YaHei", size: 22, color: "27AE60" })] }));
children.push(buildTable("稳", wen, 25, TOTAL));

// ── 保 ──
children.push(new Paragraph({ spacing: { before: 400, after: 100, pageBreakBefore: true }, children: [new TextRun({ text: "三、保（26个志愿 · 位次 134,000~152,000 · 录取概率90%+）", bold: true, font: "Microsoft YaHei", size: 22, color: "2980B9" })] }));
children.push(buildTable("保", bao, 65, TOTAL));

// ── 垫 ──
children.push(new Paragraph({ spacing: { before: 400, after: 100, pageBreakBefore: true }, children: [new TextRun({ text: "四、垫（6个志愿 · 位次 152,000+ · 录取概率99%+）", bold: true, font: "Microsoft YaHei", size: 22, color: "8E44AD" })] }));
children.push(buildTable("垫", di, 91, TOTAL));

// ── Notes ──
children.push(new Paragraph({ spacing: { before: 600, after: 200, pageBreakBefore: true }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E4057", space: 1 } }, children: [] }));
children.push(new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "重要说明", bold: true, font: "Microsoft YaHei", size: 24 })] }));

const notes = [
  "本方案基于 2025 年山东高考投档数据（常规批第 1 次）生成，2026 年实际投档位次会有浮动，仅供参考。",
  "位次法为核心策略：跨年比较只用位次不用分数（赋分制原因）。考生位次 119,781 为 2025 年 530 分对应位次。",
  "梯度比例 24:40:26:6（冲:稳:保:垫），整体滑档概率 < 1%。",
  "选科生物+历史+政治，无法报考要求物理+化学的理工医类专业，表中专业均适合偏文组合。",
  "山东为主，少量江苏院校（南京特殊教育师范学院、江苏海洋大学、徐州工程学院、盐城师范学院等）。",
  "正式填报前请核对：①2026 年招生计划 ②体检受限情况 ③单科成绩要求 ④学费及中外合作办学费用。",
  "建议将本方案作为初稿，根据个人专业偏好、家庭经济条件和高校2026年最新招生章程做调整。",
];

for (const note of notes) {
  children.push(new Paragraph({ spacing: { after: 80 }, indent: { left: 360 }, children: [
    new TextRun({ text: "• ", font: "Microsoft YaHei", size: 20 }),
    new TextRun({ text: note, font: "Microsoft YaHei", size: 20 }),
  ] }));
}

// ── Disclaimer ──
children.push(new Paragraph({ spacing: { before: 400 }, alignment: AlignmentType.CENTER, children: [
  new TextRun({ text: "本方案由 AI 基于历史数据生成，不构成录取承诺。最终以山东省教育招生考试院官方发布为准。", font: "Microsoft YaHei", size: 16, color: "999999", italics: true }),
] }));

// ── Assemble ──
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Microsoft YaHei", size: 20 } } },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1134, right: 1000, bottom: 900, left: 1000 }, // in DXA
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "徐徐 · 2026高考96志愿方案", font: "Microsoft YaHei", size: 16, color: "999999" })] })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
          new TextRun({ text: "第 ", font: "Microsoft YaHei", size: 16, color: "999999" }),
          new TextRun({ children: [PageNumber.CURRENT], font: "Microsoft YaHei", size: 16, color: "999999" }),
          new TextRun({ text: " 页", font: "Microsoft YaHei", size: 16, color: "999999" }),
        ] })] }),
    },
    children,
  }],
});

// ── Output ──
const outDir = "C:/Users/76821/Desktop/山东高考知识库/students/徐徐/志愿方案";
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

Packer.toBuffer(doc).then(buffer => {
  const outPath = `${outDir}/2026-06-23_96志愿方案.docx`;
  fs.writeFileSync(outPath, buffer);
  console.log(`Done: ${outPath}`);
  console.log(`Size: ${(buffer.length / 1024).toFixed(1)} KB`);
});
