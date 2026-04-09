#!/usr/bin/env node
/**
 * Benchmark 自动化测试脚本 v8
 *
 * 更新说明：
 * - v8: 支持从Excel表头读取模型配置，动态列分配
 * - v7: 添加交互式模型选择
 * - v6: 添加附件上传功能
 * - v5: 添加电量检查和自动充电功能
 * - 默认从第 1 行开始（含表头则为第 2 行）
 * - 支持用户自定义选择模型
 * - 支持自定义 Excel 文件路径
 * - 支持 --auto 模式自动等待登录
 */

const { chromium } = require('playwright');
const XLSX = require('xlsx');
const readline = require('readline');
const fs = require('fs');
const path = require('path');

// 自动模式标志
const AUTO_MODE = process.argv.includes('--auto');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(prompt) {
  return new Promise(resolve => rl.question(prompt, resolve));
}

// 平台上所有可用的模型列表
const ALL_MODELS = [
  { name: 'ERNIE-5.0-Thinking', keyword: 'ERNIE-5.0-Thinking', desc: '免费创意写作效果好' },
  { name: 'ERNIE-4.5-Turbo', keyword: 'ERNIE-4.5-Turbo', desc: '免费速度快' },
  { name: 'seedance-1.5-pro', keyword: 'seedance-1.5-pro', desc: '音画同步视频生成' },
  { name: 'seed-2.0', keyword: 'seed-2.0', desc: '免费多模态理解' },
  { name: 'gpt-5.4', keyword: 'gpt-5.4', desc: 'OpenAI新作' },
  { name: 'GPT-5.2', keyword: 'GPT-5.2', desc: '全能助手' },
  { name: 'GPT-5.1', keyword: 'GPT-5.1', desc: '日常对话' },
  { name: 'nano-banana-2', keyword: 'nano-banana-2', desc: '图像生成' },
  { name: 'gemini-3-pro-preview', keyword: 'gemini-3-pro-preview', desc: '多模态理解' },
  { name: 'nano-banana-pro', keyword: 'nano-banana-pro', desc: '图像理解' },
  { name: 'claude-opus-4.6', keyword: 'claude-opus-4.6', desc: '代码分析' },
  { name: 'claude-sonnet-4.5', keyword: 'claude-sonnet-4.5', desc: '长文本分析' },
  { name: 'DeepSeek-V3.2', keyword: 'DeepSeek-V3.2', desc: '免费快速通用' },
  { name: 'Qwen3-235B-Thinking', keyword: 'Qwen3-235B-Thinking', desc: '免费推理数学' }
];

// 默认配置
const DEFAULT_CONFIG = {
  excelFile: 'benchmark.xlsx',
  startRow: 1,           // 从第1行开始（0-indexed），含表头则为第2行
  timeout: 480,          // 8分钟超时（480秒）
  targetUrl: 'https://aichat.infoflow.baidu.com/emira/c/d77ij4mig7p7s6rbqa7g?hi_type=system',
  otherDir: 'other',      // 附件文件目录
  promptCol: 3,          // prompt列（D列，索引3）
  attachmentCol: 6,      // 附件列（G列，索引6）
  modelStartCol: 7       // 模型结果起始列（H列，索引7）
};

// 从Excel表头解析模型配置
function parseModelsFromHeader(headerRow) {
  const models = [];
  const startCol = DEFAULT_CONFIG.modelStartCol;

  for (let i = startCol; i < headerRow.length; i++) {
    const cellValue = headerRow[i];
    if (cellValue && cellValue.toString().trim() !== '') {
      const modelName = cellValue.toString().trim();
      // 查找模型关键字
      const foundModel = ALL_MODELS.find(m =>
        modelName.includes(m.keyword) || m.keyword.includes(modelName)
      );
      models.push({
        name: modelName,
        keyword: foundModel ? foundModel.keyword : modelName,
        colIndex: i
      });
    }
  }

  return models;
}

// 解析命令行参数
function parseArgs() {
  const args = process.argv.slice(2);
  const config = { ...DEFAULT_CONFIG };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === '--file' || arg === '-f') {
      config.excelFile = args[++i];
    } else if (arg === '--start-row' || arg === '-s') {
      config.startRow = parseInt(args[++i]) - 1;  // 转换为 0-indexed
    } else if (arg === '--timeout' || arg === '-t') {
      config.timeout = parseInt(args[++i]);
    } else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    }
  }

  return { config };
}

function printHelp() {
  console.log(`
Benchmark 自动化测试工具 v8

用法: node skill.js [选项]

选项:
  -f, --file <file>          指定 Excel 文件路径
                             例如: --file /path/to/benchmark.xlsx
  -s, --start-row <row>      指定开始行号（含表头）
                             例如: --start-row 2 表示从第2行开始（默认）
  -t, --timeout <seconds>    指定单个模型最长等待时间（秒）
                             例如: --timeout 480 表示最长等待8分钟（默认）
  --auto                     自动模式，跳过交互式确认
  -h, --help                 显示帮助信息

Excel 表格格式:
  - D列 (索引3): prompt（测试输入）
  - G列 (索引6): other（附件文件名，用 / 分隔多个文件）
  - H列起: 模型名称（表头填写模型名，结果保存在对应列）

  例如表头:
  | A | B | C | D (prompt) | E | F | G (other) | H (ERNIE-5.0) | I (gpt-5.4) | J (claude) | ...

平台支持的所有模型:
${ALL_MODELS.map((m, i) => `  ${(i + 1).toString().padStart(2)}. ${m.name} - ${m.desc}`).join('\n')}

示例:
  # 使用默认配置
  node skill.js

  # 指定 Excel 文件
  node skill.js --file benchmark.xlsx

  # 自动模式
  node skill.js --file benchmark.xlsx --auto
`);
}

// 列索引转换为字母
function colToLetter(col) {
  let letter = '';
  while (col >= 0) {
    letter = String.fromCharCode((col % 26) + 65) + letter;
    col = Math.floor(col / 26) - 1;
  }
  return letter;
}

async function main() {
  console.log('========================================');
  console.log('Benchmark 自动化测试脚本 v8');
  console.log('========================================\n');

  const { config } = parseArgs();

  // 检查 Excel 文件是否存在
  if (!fs.existsSync(config.excelFile)) {
    console.error(`错误: Excel 文件不存在: ${config.excelFile}`);
    console.log('\n请将您的 Excel 文件放到当前目录，或使用 --file 参数指定文件路径。');
    process.exit(1);
  }

  // 读取 Excel
  const workbook = XLSX.readFile(config.excelFile);
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  const data = XLSX.utils.sheet_to_json(sheet, { header: 1 });

  console.log(`读取到 ${data.length} 行数据\n`);

  // 从表头解析模型配置
  const headerRow = data[0];
  const selectedModels = parseModelsFromHeader(headerRow);

  if (selectedModels.length === 0) {
    console.error('错误: 未在表头中找到模型配置');
    console.log('\n请在 Excel 表格的 G 列起填写模型名称作为表头。');
    console.log('例如: G列=ERNIE-5.0-Thinking, H列=gpt-5.4, I列=claude-sonnet-4.5');
    process.exit(1);
  }

  // 显示配置信息
  console.log('配置信息:');
  console.log(`  Excel 文件: ${config.excelFile}`);
  console.log(`  开始行: ${config.startRow + 1}`);
  console.log(`  超时时间: ${config.timeout} 秒`);
  console.log(`  测试模型数: ${selectedModels.length}`);
  console.log('\n从表头读取的模型:');
  selectedModels.forEach((m, i) => console.log(`  ${i + 1}. ${m.name} (列: ${colToLetter(m.colIndex)})`));
  console.log('');

  // 启动浏览器
  console.log('启动浏览器...');
  const browser = await chromium.launch({
    headless: false,
    slowMo: 150
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });
  const page = await context.newPage();

  // 打开页面
  console.log('打开页面...');
  await page.goto(config.targetUrl, {
    waitUntil: 'domcontentloaded',
    timeout: 30000
  });

  await page.waitForTimeout(3000);

  // 检查是否需要登录
  const currentUrl = page.url();
  if (currentUrl.includes('uuap') || currentUrl.includes('login')) {
    if (AUTO_MODE) {
      console.log('\n检测到需要登录，自动等待30秒...');
      await page.waitForTimeout(30000);
    } else {
      console.log('\n请在浏览器中完成登录，登录完成后按回车继续...');
      await question('');
      await page.waitForTimeout(3000);
    }
  }

  // 初始电量检查
  await checkAndCharge(page, 10);

  console.log('\n开始测试...\n');

  // 遍历每一行
  for (let rowIdx = config.startRow; rowIdx < data.length; rowIdx++) {
    const row = data[rowIdx];
    const prompt = row[3];  // prompt 列是第4列（索引3）
    const attachmentFile = row[6];  // other 列是第7列（索引6）

    if (!prompt || prompt.toString().trim() === '') {
      console.log(`\n第${rowIdx + 1}行 prompt 为空，结束测试`);
      break;
    }

    console.log('========================================');
    console.log(`处理第 ${rowIdx + 1} 行`);
    console.log(`Prompt: ${prompt.toString().substring(0, 50)}...`);
    if (attachmentFile && attachmentFile.toString().trim() !== '') {
      console.log(`附件: ${attachmentFile}`);
    }
    console.log('========================================');

    // 遍历每个模型
    for (let modelIdx = 0; modelIdx < selectedModels.length; modelIdx++) {
      const model = selectedModels[modelIdx];
      console.log(`\n>>> 模型 ${modelIdx + 1}/${selectedModels.length}: ${model.name}`);

      // 每次测试前检查电量
      await checkAndCharge(page, 10);

      try {
        // 1. 创建新对话
        console.log('  [1] 创建新对话...');
        const newChatBtn = await page.$('button:has-text("新对话")');
        if (newChatBtn) {
          const isVisible = await newChatBtn.isVisible();
          if (isVisible) {
            await newChatBtn.click();
            await page.waitForTimeout(1500);
          }
        }

        // 2. 点击模型选择器
        console.log('  [2] 打开模型选择器...');
        const allBtns = await page.$$('button[aria-haspopup="dialog"]');
        let modelSelector = null;

        for (const btn of allBtns) {
          const isVisible = await btn.isVisible();
          const text = await btn.textContent();
          if (isVisible && text && text.trim().length > 0) {
            modelSelector = btn;
            break;
          }
        }

        if (!modelSelector) {
          throw new Error('未找到模型选择器');
        }

        await modelSelector.click();
        await page.waitForTimeout(1500);

        // 3. 选择模型
        console.log(`  [3] 选择模型: ${model.name}...`);

        // 先尝试直接查找
        let modelBtnHandle = await page.evaluateHandle((keyword) => {
          const dialog = document.querySelector('[role="dialog"]');
          if (!dialog) return null;
          const buttons = dialog.querySelectorAll('button');
          for (const btn of buttons) {
            if (btn.textContent.includes(keyword)) {
              return btn;
            }
          }
          return null;
        }, model.keyword);

        let modelBtn = modelBtnHandle.asElement();

        // 如果没找到，尝试滚动模型列表
        if (!modelBtn) {
          console.log(`  [3] 滚动查找模型: ${model.name}...`);
          await page.evaluate(() => {
            const dialog = document.querySelector('[role="dialog"]');
            if (dialog) {
              // 查找可滚动的容器
              const scrollContainer = dialog.querySelector('[class*="overflow"]') ||
                                      dialog.querySelector('[style*="overflow"]') ||
                                      dialog.querySelector('div[max-height]') ||
                                      dialog;
              if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight;
              }
            }
          });
          await page.waitForTimeout(500);

          // 再次查找
          modelBtnHandle = await page.evaluateHandle((keyword) => {
            const dialog = document.querySelector('[role="dialog"]');
            if (!dialog) return null;
            const buttons = dialog.querySelectorAll('button');
            for (const btn of buttons) {
              if (btn.textContent.includes(keyword)) {
                return btn;
              }
            }
            return null;
          }, model.keyword);

          modelBtn = modelBtnHandle.asElement();
        }

        if (modelBtn) {
          await modelBtn.click();
          await page.waitForTimeout(1000);
        } else {
          throw new Error(`未找到模型: ${model.name}`);
        }

        // 4. 上传附件（如果有）
        if (attachmentFile && attachmentFile.toString().trim() !== '') {
          console.log('  [4] 上传附件...');
          await uploadAttachments(page, attachmentFile.toString().trim(), config.otherDir);
          // 上传后等待页面稳定
          await page.waitForTimeout(2000);
        }

        // 5. 输入并发送
        console.log(`  [${attachmentFile && attachmentFile.toString().trim() !== '' ? '5' : '4'}] 输入并发送...`);

        // 使用 evaluate 直接操作 DOM（更可靠）
        const inputResult = await page.evaluate((promptText) => {
          const input = document.querySelector('.ProseMirror');
          if (!input) {
            return { success: false, error: '未找到输入框' };
          }

          // 清空并聚焦
          input.innerHTML = '';
          input.focus();

          // 使用 document.execCommand 插入文本
          document.execCommand('insertText', false, promptText);

          return {
            success: true,
            content: input.textContent?.substring(0, 50)
          };
        }, prompt.toString());

        if (!inputResult.success) {
          throw new Error(inputResult.error);
        }

        console.log(`  输入框内容: "${inputResult.content}..."`);
        await page.waitForTimeout(500);

        await page.keyboard.press('Enter');
        console.log('  已发送');

        // 6. 等待响应完成（最长8分钟）
        console.log(`  [${attachmentFile && attachmentFile.toString().trim() !== '' ? '6' : '5'}] 等待响应...`);
        const response = await waitForResponseComplete(page, config.timeout, prompt.toString());

        console.log(`  响应长度: ${response.length} 字符`);

        // 保存结果（使用模型配置中的列索引）
        const colLetter = colToLetter(model.colIndex);
        const cell = colLetter + (rowIdx + 1);
        sheet[cell] = { t: 's', v: response };
        XLSX.writeFile(workbook, config.excelFile);
        console.log(`  已保存到 ${cell}`);

      } catch (error) {
        console.error(`  错误: ${error.message}`);
        const colLetter = colToLetter(model.colIndex);
        const cell = colLetter + (rowIdx + 1);
        sheet[cell] = { t: 's', v: `错误: ${error.message}` };
        XLSX.writeFile(workbook, config.excelFile);
      }
    }

    console.log(`\n第${rowIdx + 1}行完成\n`);
  }

  console.log('\n========================================');
  console.log('全部测试完成！');
  console.log('========================================');

  await question('\n按回车关闭浏览器...');
  rl.close();
  await browser.close();
}

// 等待响应完成
async function waitForResponseComplete(page, maxTimeout, userPrompt = '') {
  // 初始等待
  await page.waitForTimeout(3000);

  let lastLength = 0;
  let stableCount = 0;
  let noChangeCount = 0;

  // 最多等待 maxTimeout 秒（默认300秒 = 5分钟）
  for (let i = 0; i < maxTimeout; i++) {
    await page.waitForTimeout(1000);

    // 检测响应内容
    const result = await page.evaluate((promptText) => {
      // 方法1: 找所有 markdown 容器，获取最后一个
      const markdownElements = document.querySelectorAll('[class*="markdown"]');

      if (markdownElements.length > 0) {
        // 找到最后一个有内容的元素
        for (let i = markdownElements.length - 1; i >= 0; i--) {
          const text = markdownElements[i].textContent?.trim();
          if (text && text.length > 0) {
            // 排除用户输入的内容（通常在特定class中）
            const classStr = markdownElements[i].className || '';
            // bg-[rgba(73,87,242,.04)] 是思考过程的class，跳过
            if (!classStr.includes('bg-[rgba(73,87,242')) {
              // 排除与用户输入相同的内容
              if (promptText && text === promptText) {
                continue;
              }
              return {
                found: true,
                content: text,
                length: text.length
              };
            }
          }
        }
      }

      // 方法2: 找 whitespace-pre-wrap 元素
      const preWrapElements = document.querySelectorAll('div.whitespace-pre-wrap');
      if (preWrapElements.length > 0) {
        // 获取最后一个非用户输入的
        for (let i = preWrapElements.length - 1; i >= 0; i--) {
          const text = preWrapElements[i].textContent?.trim();
          if (text && text.length > 10) {
            // 排除与用户输入相同的内容
            if (promptText && text === promptText) {
              continue;
            }
            return {
              found: true,
              content: text,
              length: text.length
            };
          }
        }
      }

      return { found: false, content: '', length: 0 };
    }, userPrompt);

    if (result.found && result.length > 0) {
      // 检测内容是否稳定（连续15次长度不变，即15秒）
      if (result.length === lastLength) {
        stableCount++;
        if (stableCount >= 15) {
          console.log(`  响应完成 (${i + 1}秒, 长度: ${result.length})`);
          return result.content;
        }
      } else if (result.length > lastLength) {
        // 内容还在增长
        lastLength = result.length;
        stableCount = 0;
        noChangeCount = 0;
      } else {
        // 内容变短了（可能是新对话），重置
        lastLength = result.length;
        stableCount = 0;
      }
    } else {
      noChangeCount++;
      if (noChangeCount > 10) {
        // 10秒没检测到内容变化，可能已经完成
        if (lastLength > 0) {
          return await getLastResponse(page, userPrompt);
        }
      }
    }
  }

  // 超时，返回当前内容
  console.log(`  达到超时时间 (${maxTimeout}秒)，返回当前内容`);
  return await getLastResponse(page, userPrompt);
}

// 获取最后的响应内容
async function getLastResponse(page, userPrompt = '') {
  const content = await page.evaluate((promptText) => {
    const markdownElements = document.querySelectorAll('[class*="markdown"]');

    for (let i = markdownElements.length - 1; i >= 0; i--) {
      const text = markdownElements[i].textContent?.trim();
      const classStr = markdownElements[i].className || '';
      if (text && text.length > 0 && !classStr.includes('bg-[rgba(73,87,242')) {
        // 排除与用户输入相同的内容
        if (promptText && text === promptText) {
          continue;
        }
        return text;
      }
    }

    return '未能获取响应内容';
  }, userPrompt);

  return content;
}

// ============ 电量检查和充电功能 ============

/**
 * 检查电量并充电
 */
async function checkAndCharge(page, minCharge = 10) {
  console.log('\n🔋 检查电量...');

  try {
    await page.waitForTimeout(2000);

    // 使用精确的选择器获取电量
    const chargeInfo = await page.evaluate(() => {
      // 查找电量数字的 span 元素（特定类名）
      const spans = document.querySelectorAll('span');
      for (const span of spans) {
        const classStr = span.className || '';
        if (classStr.includes('text-xs') && classStr.includes('font-bold') && classStr.includes('tabular-nums')) {
          const text = span.textContent?.trim();
          const num = parseInt(text);
          if (!isNaN(num) && num >= 0 && num <= 100) {
            return { found: true, value: num, method: 'exact-selector' };
          }
        }
      }

      // 备用方法：查找右上角的数字
      const allSpans = document.querySelectorAll('span');
      for (const span of allSpans) {
        const text = span.textContent?.trim();
        if (/^\d+$/.test(text)) {
          const num = parseInt(text);
          const rect = span.getBoundingClientRect();
          // 右上角区域
          if (rect.top < 100 && rect.left > 1100 && num >= 0 && num <= 100) {
            return { found: true, value: num, method: 'position-fallback' };
          }
        }
      }

      return { found: false, value: -1, method: 'not-found' };
    });

    if (chargeInfo.found) {
      console.log(`  📊 当前电量: ${chargeInfo.value}`);
    } else {
      console.log('  ⚠️ 未找到电量信息');
      return { charged: false, currentCharge: -1 };
    }

    // 如果电量低于阈值，进行充电
    if (chargeInfo.value < minCharge) {
      console.log(`  ⚡ 电量不足 (${chargeInfo.value} < ${minCharge})，开始充电...`);
      return await doCharge(page, chargeInfo.value);
    }

    console.log(`  ✅ 电量充足 (${chargeInfo.value} >= ${minCharge})`);
    return { charged: false, currentCharge: chargeInfo.value };

  } catch (error) {
    console.error(`  ❌ 检查电量失败: ${error.message}`);
    return { charged: false, currentCharge: -1 };
  }
}

/**
 * 执行充电操作
 */
async function doCharge(page, currentCharge) {
  try {
    console.log('  [充电] 查找"立即充电"按钮...');

    // 查找包含"立即充电"的 span 元素
    const chargeBtns = await page.$$('span');
    let chargeBtn = null;

    for (const btn of chargeBtns) {
      const text = await btn.textContent();
      if (text?.trim() === '立即充电') {
        const isVisible = await btn.isVisible().catch(() => false);
        if (isVisible) {
          chargeBtn = btn;
          break;
        }
      }
    }

    if (!chargeBtn) {
      console.log('  ❌ 未找到"立即充电"按钮');
      return { charged: false, currentCharge };
    }

    console.log('  [充电] 找到"立即充电"按钮，点击...');
    await chargeBtn.click();
    await page.waitForTimeout(1500);

    // 处理弹窗
    return await handleChargeDialog(page, currentCharge);

  } catch (error) {
    console.error(`  ❌ 充电失败: ${error.message}`);
    return { charged: false, currentCharge };
  }
}

/**
 * 处理充电弹窗
 */
async function handleChargeDialog(page, currentCharge) {
  console.log('  [充电] 检查是否有确认弹窗...');
  await page.waitForTimeout(1000);

  // 查找弹窗中的"立即充电"按钮（BUTTON标签，bg-violet-600 类）
  const confirmBtn = await page.$('button.bg-violet-600:has-text("立即充电")');

  if (confirmBtn) {
    const isVisible = await confirmBtn.isVisible().catch(() => false);
    if (isVisible) {
      console.log('  [充电] 点击弹窗确认按钮...');
      await confirmBtn.click();
      await page.waitForTimeout(3000);
    }
  } else {
    // 备用方法：查找 dialog 中包含"立即充电"的按钮
    const dialogBtn = await page.evaluateHandle(() => {
      const dialog = document.querySelector('[role="dialog"]');
      if (dialog) {
        const buttons = dialog.querySelectorAll('button');
        for (const btn of buttons) {
          if (btn.textContent?.includes('立即充电')) {
            return btn;
          }
        }
      }
      return null;
    });

    if (dialogBtn) {
      const isVisible = await dialogBtn.isVisible().catch(() => false);
      if (isVisible) {
        console.log('  [充电] 点击弹窗确认按钮...');
        await dialogBtn.click();
        await page.waitForTimeout(3000);
      }
    }
  }

  // 验证充电结果
  console.log('  [充电] 等待充电完成...');
  await page.waitForTimeout(5000);

  const newChargeInfo = await page.evaluate(() => {
    const spans = document.querySelectorAll('span');
    for (const span of spans) {
      const classStr = span.className || '';
      if (classStr.includes('text-xs') && classStr.includes('font-bold') && classStr.includes('tabular-nums')) {
        const text = span.textContent?.trim();
        const num = parseInt(text);
        if (!isNaN(num) && num >= 0 && num <= 100) {
          return { found: true, value: num };
        }
      }
    }
    return { found: false, value: -1 };
  });

  if (newChargeInfo.found && newChargeInfo.value > currentCharge) {
    console.log(`  ✅ 充电成功！电量: ${currentCharge} -> ${newChargeInfo.value}`);
    return { charged: true, currentCharge: newChargeInfo.value };
  } else if (newChargeInfo.found) {
    console.log(`  ⚠️ 电量未变化 (${currentCharge} -> ${newChargeInfo.value})，充电请求已发送`);
    return { charged: true, currentCharge: newChargeInfo.value };
  } else {
    console.log('  ⚠️ 无法获取新电量，充电请求已发送');
    return { charged: true, currentCharge: -1 };
  }
}

// 上传附件文件（支持多文件，用 / 分隔）
async function uploadAttachments(page, fileNames, otherDir) {
  // 分割文件名（支持 / 分隔）
  const files = fileNames.split('/').map(f => f.trim()).filter(f => f);
  const totalFiles = files.length;

  console.log(`  [附件] 准备上传 ${totalFiles} 个文件: ${files.join(', ')}`);

  let successCount = 0;

  for (let i = 0; i < files.length; i++) {
    const fileName = files[i];
    const filePath = path.join(process.cwd(), otherDir, fileName);

    // 检查文件是否存在
    if (!fs.existsSync(filePath)) {
      console.log(`  [附件] 文件不存在: ${fileName}`);
      continue;
    }

    console.log(`  [附件] 上传第 ${i + 1}/${totalFiles} 个: ${fileName}`);

    try {
      // 判断文件类型
      const ext = path.extname(fileName).toLowerCase();
      const isImage = ['.jpg', '.jpeg', '.png', '.gif', '.webp'].includes(ext);

      // 根据文件类型选择正确的 file input
      // input[0]: 文档类型 (.txt, .pdf, .doc, .docx, .csv, .xlsx, .xls)
      // input[1]: 图片类型 (image/jpeg, image/png, image/jpg)
      const fileInputs = await page.$$('input[type="file"]');
      let targetInput = null;

      if (isImage && fileInputs.length > 1) {
        // 图片用第二个 input (accept=image/*)
        targetInput = fileInputs[1];
      } else if (fileInputs.length > 0) {
        // 文档用第一个 input
        targetInput = fileInputs[0];
      }

      if (targetInput) {
        // 直接设置文件
        await targetInput.setInputFiles(filePath);
        console.log(`  [附件] 已上传: ${fileName} (${isImage ? '图片' : '文档'})`);
        await page.waitForTimeout(1500);
        successCount++;
        continue;
      }

      // 如果没有找到 file input，尝试点击添加附件按钮
      console.log('  [附件] 尝试点击添加附件按钮...');
      const uploadBtn = await page.$('button[title="添加附件"]');
      if (uploadBtn) {
        await uploadBtn.click();
        await page.waitForTimeout(500);

        // 再次查找 file input
        const fileInputsAfterClick = await page.$$('input[type="file"]');
        if (fileInputsAfterClick.length > 0) {
          const inputIndex = isImage && fileInputsAfterClick.length > 1 ? 1 : 0;
          await fileInputsAfterClick[inputIndex].setInputFiles(filePath);
          console.log(`  [附件] 已上传: ${fileName}`);
          await page.waitForTimeout(1500);
          successCount++;
          continue;
        }
      }

      console.log(`  [附件] 上传失败: ${fileName}`);

    } catch (error) {
      console.log(`  [附件] 上传失败: ${fileName} - ${error.message}`);
    }
  }

  console.log(`  [附件] 上传完成: ${successCount}/${totalFiles} 个文件`);
  return successCount > 0;
}

main().catch(console.error);
