const { Document, Packer, Paragraph, TextRun, AlignmentType,
        HeadingLevel, BorderStyle, ShadingType, ImageRun, Table,
        TableRow, TableCell, WidthType, VerticalAlign } = require('docx');
const fs = require('fs');
const { imageSize: sizeOf } = require('image-size');

// ─── Color System ───
const C = {
  title: "1E3A5F", subtitle: "3B82F6", body: "374151", muted: "9CA3AF",
  accent: "2563EB", success: "059669", warn: "D97706",
  codeHead: "1F2937", codeBg: "F8FAFC", quoteBg: "EFF6FF",
  tableHead: "DBEAFE", tableAlt: "F9FAFB",
};
const FONT = "PingFang SC";
const CODE_FONT = "JetBrains Mono";

// ─── Helpers ───
function heading1(text) {
  return new Paragraph({
    spacing: { before: 240, after: 400, line: 276 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, size: 44, bold: true, font: FONT, color: C.title })]
  });
}
function heading2(text) {
  return new Paragraph({
    spacing: { before: 400, after: 200, line: 276 },
    border: { left: { style: BorderStyle.SINGLE, size: 14, color: C.subtitle, space: 10 } },
    children: [new TextRun({ text, size: 32, bold: true, font: FONT, color: C.subtitle })]
  });
}
function heading3(text) {
  return new Paragraph({
    spacing: { before: 280, after: 160, line: 276 },
    children: [new TextRun({ text, size: 28, bold: true, font: FONT, color: C.title })]
  });
}
function body(...runs) {
  return new Paragraph({
    spacing: { after: 200, line: 432 },
    children: runs.map(r => typeof r === 'string'
      ? new TextRun({ text: r, font: FONT, size: 23, color: C.body })
      : r)
  });
}
function bold(text) { return new TextRun({ text, font: FONT, size: 23, color: C.body, bold: true }); }
function accent(text) { return new TextRun({ text, font: FONT, size: 23, color: C.accent, bold: true }); }
function code(text) { return new TextRun({ text, font: CODE_FONT, size: 21, color: C.accent, bold: true }); }
function divider() {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 360, after: 360 },
    children: [new TextRun({ text: "· · ·", color: "D1D5DB", size: 24 })]
  });
}
function quote(text) {
  return new Paragraph({
    indent: { left: 480, right: 480 },
    spacing: { before: 240, after: 240, line: 380 },
    border: { left: { style: BorderStyle.SINGLE, size: 10, color: C.subtitle, space: 10 } },
    shading: { fill: C.quoteBg, type: ShadingType.CLEAR },
    children: [new TextRun({ text, italics: true, size: 22, color: C.body, font: FONT })]
  });
}
function codeBlock(lang, lines) {
  const header = new Paragraph({
    spacing: { before: 280, after: 0 },
    shading: { fill: C.codeHead, type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    border: {
      top: { style: BorderStyle.SINGLE, size: 1, color: "E5E7EB" },
      left: { style: BorderStyle.SINGLE, size: 1, color: "E5E7EB" },
      right: { style: BorderStyle.SINGLE, size: 1, color: "E5E7EB" },
    },
    children: [
      new TextRun({ text: "  ●", color: "EF4444", size: 14, font: CODE_FONT }),
      new TextRun({ text: " ●", color: "F59E0B", size: 14, font: CODE_FONT }),
      new TextRun({ text: " ●", color: "10B981", size: 14, font: CODE_FONT }),
      new TextRun({ text: `   ${lang}`, font: CODE_FONT, size: 16, color: C.muted }),
    ]
  });
  const codeLines = lines.map(l => new Paragraph({
    spacing: { before: 0, after: 0, line: 300 },
    shading: { fill: C.codeBg, type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    border: {
      left: { style: BorderStyle.SINGLE, size: 1, color: "E5E7EB" },
      right: { style: BorderStyle.SINGLE, size: 1, color: "E5E7EB" },
    },
    children: [new TextRun({ text: `  ${l}`, font: CODE_FONT, size: 19, color: C.body })]
  }));
  const footer = new Paragraph({
    spacing: { before: 0, after: 280 },
    shading: { fill: C.codeBg, type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    border: {
      left: { style: BorderStyle.SINGLE, size: 1, color: "E5E7EB" },
      right: { style: BorderStyle.SINGLE, size: 1, color: "E5E7EB" },
      bottom: { style: BorderStyle.SINGLE, size: 1, color: "E5E7EB" },
    },
    children: [new TextRun({ text: " ", size: 8 })]
  });
  return [header, ...codeLines, footer];
}

function embedImage(imgPath, caption) {
  const buf = fs.readFileSync(imgPath);
  const dim = sizeOf(buf);
  const maxW = 451;
  const w = Math.min(dim.width, maxW);
  const h = dim.height * (w / dim.width);
  const result = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 360, after: caption ? 120 : 360 },
      children: [new ImageRun({ type: "png", data: buf, transformation: { width: w, height: h } })]
    }),
  ];
  if (caption) {
    result.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 360 },
      children: [new TextRun({ text: `▲ ${caption}`, color: C.muted, size: 18, font: FONT })]
    }));
  }
  return result;
}

function metricCard(num, label) {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 320, after: 0 },
      shading: { fill: C.quoteBg, type: ShadingType.CLEAR },
      children: [new TextRun({ text: num, font: "DIN Alternate", size: 56, bold: true, color: C.accent })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 320 },
      shading: { fill: C.quoteBg, type: ShadingType.CLEAR },
      children: [new TextRun({ text: label, font: FONT, size: 22, color: "6B7280" })]
    })
  ];
}

// ─── Article Content ───
const children = [
  // Banner
  ...embedImage('banner.png', ''),

  // Title
  heading1("一小时，让 Claude Code\n拥有 Gemini 画图能力"),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 520 },
    children: [new TextRun({ text: "作者：你起来我讲两句 ｜ 2026-04-05", color: C.muted, size: 20, font: FONT })]
  }),

  // Hook
  body("Claude Code 什么都好，就是不能画图。"),
  body("每次需要生成配图的时候，我都得切到 Gemini 手动操作一遍，复制提示词、等生成、下载图片、再拖回项目目录。来回折腾，流程断裂。"),
  body("我想要的很简单：", bold("在 Claude Code 里输一句话，图片自动生成到本地。")),
  body("但 Gemini 没有开放免费的图像生成 API（Nano Banana 的 API 有配额限制），直接调 API 还得处理认证、计费、限流。而且我只是偶尔用用，不想为此付费。"),
  body("所以我换了个思路：", accent("用浏览器自动化模拟真人操作"), "，复用已登录的 Google 账号，走 Web 端的免费额度。一小时搞定，效果还不错。"),

  divider(),

  // Section 1
  heading2("思路：为什么不直接调 API"),
  body("Gemini 的图像生成模型叫 ", accent("Nano Banana"), "（内部代号，现在已经是公开名称了）。它有 API，但免费层每天只有 ", bold("20 张图片"), " 的额度，而且需要申请 API Key、配置认证。"),
  body("而 Web 端（gemini.google.com）的免费额度更宽松，登录 Google 账号就能用。关键是：", bold("我已经登录了"), "。"),
  body("所以方案很直接："),
  quote("用 Playwright 打开一个持久化的浏览器实例，复用已登录的 Google 会话，模拟点击「制作图片」工具，输入提示词，等图片生成完成后自动下载。"),
  body("整个过程对 Google 来说，就是一个正常用户在用 Gemini 画图。没有 API 调用，没有异常请求模式，", bold("不触发任何风控规则"), "。"),

  divider(),

  // Section 2
  heading2("避免封号：三个关键设计"),
  heading3("1. 持久化登录，不重复认证"),
  body("每次启动都用同一个 ", code("userdata/"), " 目录，浏览器会自动加载已保存的 Cookie 和会话。不需要每次都走登录流程，避免了频繁登录触发 Google 的安全验证。"),
  ...codeBlock("Python", [
    "# 首次登录（手动操作，只需一次）",
    "uv run python scripts/gemini_image.py login",
    "",
    "# 之后每次都自动复用会话",
    "uv run python scripts/gemini_image.py \"画一只猫\"",
  ]),

  heading3("2. 模拟真人操作节奏"),
  body("代码里的每个操作都有合理的延迟：输入文字时每个字符间隔 30ms，点击按钮后等待 0.5-1 秒，发送后等待页面自然响应。不是机器人式的瞬间操作，而是", bold("模拟人类的操作节奏"), "。"),
  body("同时禁用了 Playwright 的自动化标记："),
  ...codeBlock("Python", [
    "args=[",
    "    \"--disable-blink-features=AutomationControlled\",",
    "    \"--no-sandbox\",",
    "]",
  ]),

  heading3("3. 走正常 UI 流程，不碰内部 API"),
  body("我没有直接构造 ", code("StreamGenerate"), " 请求（虽然录制时已经分析出了完整的请求结构）。原因很简单：直接调内部 API 容易被检测到异常的请求头或参数格式。"),
  body("相反，整个流程完全通过 UI 操作完成：点击输入框 → 点击「工具」→ 点击「制作图片」→ 输入文字 → 点击发送。", bold("和你手动操作一模一样"), "。"),

  divider(),

  // Section 3
  heading2("技术实现：一小时的逆向工程"),

  ...embedImage('architecture.png', '图 1：整体工作流程'),

  heading3("Step 1：录制请求，搞清楚 Gemini 的工作方式"),
  body("先写了一个 ", code("recorder.py"), "，用 Playwright 打开 Gemini，拦截所有网络请求，同时注入 JS 追踪页面点击。然后手动操作一遍「生成图片」的完整流程。"),
  body("录制结果告诉我几个关键信息："),
  body("• 发送 prompt 后，URL 会变成 ", code("/app/{session_id}"), "（页面导航）"),
  body("• 图片生成完成后，DOM 中出现 ", code("img.image.loaded"), " 元素"),
  body("• 图片的 src 是 ", code("blob:"), " URL，不能直接下载"),
  body("• 页面上有下载按钮，点击后会触发浏览器下载流"),

  heading3("Step 2：构建生成器"),
  body("基于录制数据，构建了 ", code("GeminiImageGenerator"), " 类。核心逻辑分三步："),

  ...embedImage('sequence.png', '图 2：生成流程时序图'),

  body(bold("发送阶段"), "：激活「制作图片」工具 → 输入 prompt → 点击发送按钮"),
  body(bold("等待阶段"), "：轮询 DOM 检测 ", code("img.image.loaded"), " 元素，同时监控发送按钮状态（消失=生成中，恢复=生成完成）"),
  body(bold("下载阶段"), "：优先点击下载按钮拦截下载流，如果失败则用 Canvas 提取图像数据"),

  heading3("Step 3：封装为 Skill"),
  body("最后把整个东西封装成 Claude Code 的 Skill 格式。一个 ", code("SKILL.md"), " 定义触发条件和使用方式，一个 ", code("scripts/gemini_image.py"), " 是核心脚本。"),
  body("放到 ", code("~/.claude/skills/gemini-image/"), " 目录下，Claude Code 就能自动识别并调用。"),

  divider(),

  // Section 4
  heading2("踩过的坑"),
  heading3("页面导航导致事件监听丢失"),
  body("最开始我用 Playwright 的 ", code("on('response')"), " 拦截图片 URL。但发送 prompt 后页面会导航到新 URL，所有事件监听器全部失效。"),
  body("解决方案：", bold("放弃 response 拦截，改为 DOM 轮询"), "。每 3 秒扫描一次页面，检查 ", code("img.image.loaded"), " 元素。简单粗暴但可靠。"),

  heading3("blob URL 无法直接下载"),
  body("生成的图片 src 是 ", code("blob:https://gemini.google.com/..."), "，用 ", code("fetch()"), " 去请求会被 CORS 拦截。"),
  body("最终方案：", bold("点击页面上的下载按钮"), "，用 Playwright 的 ", code("expect_download()"), " 拦截浏览器下载流。如果下载按钮找不到，回退到 Canvas 方式（", code("drawImage → toDataURL → base64"), "）。"),

  heading3("生成完成的判断"),
  body("图片生成需要 30-60 秒，怎么知道什么时候完成？试过检测 loading indicator、检测 StreamGenerate 响应，都不靠谱。"),
  body("最终发现：", bold("发送按钮的状态是最可靠的信号"), "。生成中按钮变成停止图标，生成完成后恢复为发送图标。配合 ", code("img.image.loaded"), " 的 DOM 检测，双重确认。"),

  divider(),

  // Section 5
  heading2("效果"),
  ...metricCard("1行", "一句话生成图像"),
  ...codeBlock("Bash", [
    "uv run python scripts/gemini_image.py \"赛博朋克风格的东京街头\"",
  ]),
  body("Headless 模式运行，不弹浏览器窗口。30-60 秒后图片自动保存到本地。"),
  body("在 Claude Code 里，直接说「用 Gemini 画一张 xxx」就会自动触发 Skill，生成图片并返回文件路径。写公众号文章时再也不用手动切换工具了。"),

  divider(),

  // Section 6
  heading2("写在最后"),
  body("这个方案的核心思想很简单：", bold("不要和平台对抗，而是模拟正常用户行为"), "。"),
  body("持久化登录、合理的操作间隔、走正常 UI 流程——这些设计不是为了「绕过」什么，而是为了让自动化操作和手动操作在平台眼里没有区别。"),
  body("代码已开源，感兴趣的可以看看："),
  body(accent("github.com/uk0/gemini-skill")),
  body("如果你也在用 Claude Code，试试把它加到你的 Skills 里。一句话画图，真的很爽。"),

  // CTA
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 400, after: 200 },
    children: [
      new TextRun({ text: "觉得有用？点个 ", font: FONT, size: 23, color: C.body }),
      new TextRun({ text: "Star ⭐", font: FONT, size: 23, color: C.accent, bold: true }),
      new TextRun({ text: " 支持一下", font: FONT, size: 23, color: C.body }),
    ]
  }),

  // ─── Copyright ───
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 600, after: 200 },
    children: [new TextRun({ text: "━━━━━━━━━━━━━━━━━━━━", color: "D1D5DB", size: 20 })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 80 },
    shading: { fill: C.tableAlt, type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: [new TextRun({ text: "📝 原创声明", bold: true, size: 22, color: C.title, font: FONT })]
  }),
  new Paragraph({
    spacing: { before: 0, after: 80 },
    shading: { fill: C.tableAlt, type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: [new TextRun({ text: "本文为原创内容，首发于微信公众号「你起来我讲两句」。", size: 20, color: C.body, font: FONT })]
  }),
  new Paragraph({
    spacing: { before: 160, after: 80 },
    shading: { fill: C.tableAlt, type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: [new TextRun({ text: "🔒 转载须知", bold: true, size: 22, color: C.title, font: FONT })]
  }),
  new Paragraph({
    spacing: { before: 0, after: 80 },
    shading: { fill: C.tableAlt, type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: [new TextRun({ text: "• 转载请联系公众号获取授权，未经许可不得转载、摘编或以其他方式使用。", size: 19, color: "6B7280", font: FONT })]
  }),
  new Paragraph({
    spacing: { before: 0, after: 200 },
    shading: { fill: C.tableAlt, type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: [new TextRun({ text: "• 经授权转载时须注明出处，保留原文链接，且不得修改文章内容。", size: 19, color: "6B7280", font: FONT })]
  }),
];

// ─── Build Document ───
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: 23, color: C.body } }
    }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  const outPath = 'gemini-skill-wechat-article.docx';
  fs.writeFileSync(outPath, buf);
  console.log(`✅ 文章已生成: ${outPath}`);
  console.log(`   大小: ${(buf.length / 1024).toFixed(1)} KB`);
});
