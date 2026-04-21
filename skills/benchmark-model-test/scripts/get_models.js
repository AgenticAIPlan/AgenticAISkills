#!/usr/bin/env node
/**
 * 获取平台上所有可用的模型列表
 */

const { chromium } = require('playwright');
const fs = require('fs');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(prompt) {
  return new Promise(resolve => rl.question(prompt, resolve));
}

async function getModels() {
  // 获取平台地址
  let targetUrl = process.env.PLATFORM_URL || '';
  if (!targetUrl) {
    targetUrl = await question('请输入模型平台地址: ');
  }
  targetUrl = targetUrl.trim();
  if (!targetUrl) {
    console.error('错误: 必须输入平台地址');
    rl.close();
    process.exit(1);
  }

  console.log('启动浏览器...');
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  console.log('打开平台页面...');
  await page.goto(targetUrl, {
    waitUntil: 'domcontentloaded',
    timeout: 30000
  });

  await page.waitForTimeout(3000);

  // 检查是否需要登录
  const currentUrl = page.url();
  if (currentUrl.includes('login')) {
    console.log('\n请在浏览器中完成登录...');
    await question('登录完成后按回车继续...');
    await page.waitForTimeout(2000);
  }

  console.log('\n点击模型选择器...');
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
    console.log('未找到模型选择器');
    await browser.close();
    rl.close();
    return;
  }

  await modelSelector.click();
  await page.waitForTimeout(2000);

  console.log('\n获取模型列表...');

  // 滚动加载所有模型
  await page.evaluate(async () => {
    const dialog = document.querySelector('[role="dialog"]');
    if (dialog) {
      const scrollContainer = dialog.querySelector('[class*="overflow"]') ||
                              dialog.querySelector('[style*="overflow"]') ||
                              dialog.querySelector('div[max-height]') ||
                              dialog;

      // 多次滚动以确保加载所有模型
      for (let i = 0; i < 10; i++) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
        await new Promise(r => setTimeout(r, 500));
      }
    }
  });

  await page.waitForTimeout(1000);

  // 获取所有模型名称
  const models = await page.evaluate(() => {
    const dialog = document.querySelector('[role="dialog"]');
    if (!dialog) return [];

    const buttons = dialog.querySelectorAll('button');
    const modelList = [];

    buttons.forEach(btn => {
      const text = btn.textContent?.trim();
      // 过滤掉空内容和特殊按钮
      if (text && text.length > 0 && text.length < 100) {
        modelList.push(text);
      }
    });

    return [...new Set(modelList)]; // 去重
  });

  console.log('\n========================================');
  console.log('找到 ' + models.length + ' 个模型:');
  console.log('========================================');
  models.forEach((m, i) => console.log(`  ${(i + 1).toString().padStart(3)}. ${m}`));

  // 保存到文件
  fs.writeFileSync('models.json', JSON.stringify(models, null, 2));
  console.log('\n已保存到 models.json');

  await question('\n按回车关闭浏览器...');
  rl.close();
  await browser.close();
}

getModels().catch(err => {
  console.error('错误:', err);
  rl.close();
  process.exit(1);
});