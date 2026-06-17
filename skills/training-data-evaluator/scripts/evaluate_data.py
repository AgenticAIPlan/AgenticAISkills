#!/usr/bin/env python3
"""
大模型训练数据评估系统 v2.0
- 支持数据类型分类（代码/数学/推理/轨迹等）
- 技术风格UI
- 累加模式报告
"""
import os
import json
import glob
import hashlib
import re
from datetime import datetime
from collections import Counter, defaultdict
import zipfile
import tarfile

WORKSPACE = "/Users/huangneng/ComateProjects/comate-zulu-demo-1777450538695"
OUTPUT_DIR = f"{WORKSPACE}/data_eval/reports"
HISTORY_FILE = f"{WORKSPACE}/data_eval/eval_history.json"

# 数据类型关键词（基于代码数据扩量攻坚需求文档）
# 预训练数据类型
PRETRAIN_TYPES = {
    "技术文档": ["api", "文档", "documentation", "doc", "sdk", "cli", "framework", "框架", "官方文档"],
    "教程/实践": ["tutorial", "教程", "step-by-step", "全栈", "项目教程", "practice", "实战"],
    "Q&A/Debug": ["stackoverflow", "qa", "问答", "debug", "bug", "报错", "error", "fix", "解决方案", "知乎"],
    "博客/技术文章": ["blog", "博客", "架构", "性能优化", "工程经验", "architecture", "optimization"],
    "Demo/示例": ["demo", "example", "示例", "showcase", "playground", "组件示例", "sample"],
}

# 中训练数据类型
MIDTRAIN_TYPES = {
    "SWE-工程": ["swe", "bugfix", "feature", "refactor", "重构", "单测", "test generation", "依赖升级"],
    "Agent轨迹": ["agent", "trajectory", "轨迹", "tool", "工具调用", "shell", "git", "docker"],
}

# 后训练数据类型
POSTTRAIN_TYPES = {
    "RL数据": ["rl", "reward", "preference", "反馈", "评分", "human", "标注"],
}

# 基础数据类型
BASIC_TYPES = {
    "源代码": ["github", "repo", "commit", "patch", "python", "java", "javascript", "go", "rust", "c++", "function", "class", "import", "代码"],
    "数学/Math": ["math", "数学", "equation", "公式", "proof", "证明", "theorem", "定理", "calculate", "计算"],
    "推理/Reasoning": ["reasoning", "推理", "logic", "逻辑", "think", "思考", "thinking", "step", "步骤", "conclusion", "结论"],
    "GUI交互": ["gui", "desktop", "window", "click", "mouse", "screen", "截图", "thunderbird", "libreoffice"],
    "多模态": ["image", "图片", "video", "视频", "audio", "音频", "visual", "视觉"],
    "对话数据": ["dialogue", "对话", "chat", "conversation", "问答"],
}

def classify_data_type(file_path, content_sample=""):
    """分类数据类型（支持多标签）"""
    detected_types = []
    content_lower = content_sample.lower() if content_sample else ""
    file_lower = file_path.lower()
    
    # 检查预训练类型
    for dtype, keywords in PRETRAIN_TYPES.items():
        for kw in keywords:
            if kw.lower() in file_lower or kw.lower() in content_lower:
                detected_types.append(f"预训练/{dtype}")
                break
    
    # 检查中训练类型
    for dtype, keywords in MIDTRAIN_TYPES.items():
        for kw in keywords:
            if kw.lower() in file_lower or kw.lower() in content_lower:
                detected_types.append(f"中训练/{dtype}")
                break
    
    # 检查后训练类型
    for dtype, keywords in POSTTRAIN_TYPES.items():
        for kw in keywords:
            if kw.lower() in file_lower or kw.lower() in content_lower:
                detected_types.append(f"后训练/{dtype}")
                break
    
    # 检查基础类型
    for dtype, keywords in BASIC_TYPES.items():
        for kw in keywords:
            if kw.lower() in file_lower or kw.lower() in content_lower:
                detected_types.append(dtype)
                break
    
    # 去重并返回
    detected_types = list(dict.fromkeys(detected_types))
    return detected_types if detected_types else ["通用/General"]

def analyze_thinking_data(file_path):
    """分析Thinking数据"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 统计JSON对象
    pattern = r'\{\s*"is_stream"'
    matches = list(re.finditer(pattern, content))
    
    total_prompt_len = 0
    total_completion_len = 0
    detected_models = set()
    
    # 检测模型关键词
    model_patterns = [
        (r'claude-sonnet-4[\.\-]5', 'Claude Sonnet 4.5'),
        (r'claude-3[\.\-]5[\.\-]sonnet', 'Claude 3.5 Sonnet'),
        (r'claude-3[\.\-]opus', 'Claude 3 Opus'),
        (r'gpt-4o', 'GPT-4o'),
        (r'gpt-4[\.\-]turbo', 'GPT-4 Turbo'),
        (r'gpt-4', 'GPT-4'),
        (r'deepseek[\.\-]v3', 'DeepSeek-V3'),
        (r'deepseek[\.\-]coder', 'DeepSeek-Coder'),
        (r'qwen[\.\-]2[\.\-]5', 'Qwen 2.5'),
        (r'qwen[\.\-]coder', 'Qwen-Coder'),
        (r'glm-4', 'GLM-4'),
        (r'ernie-4', 'ERNIE 4.0'),
        (r'llama-3', 'Llama 3'),
    ]
    
    for pattern, model_name in model_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            detected_models.add(model_name)
    
    for i, match in enumerate(matches[:100]):  # 采样分析
        start = match.start()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(content)
        
        obj_str = content[start:end].strip().rstrip(',')
        try:
            obj = json.loads(obj_str)
            total_prompt_len += len(str(obj.get('prompt', '')))
            total_completion_len += len(str(obj.get('completion', '')))
            # 从JSON中检测模型
            if 'model' in obj:
                detected_models.add(str(obj['model']))
        except:
            pass
    
    count = len(matches)
    avg_prompt = total_prompt_len / max(count, 1)
    avg_completion = total_completion_len / max(count, 1)
    
    result = {
        "type": "推理/Reasoning",
        "subtype": "Thinking数据",
        "count": count,
        "size_mb": len(content) / 1024 / 1024,
        "tokens_est": len(content) / 4,
        "thinking_count": content.count('thinking'),
        "signature_count": content.count('signature'),
        "avg_prompt_len": avg_prompt,
        "avg_completion_len": avg_completion,
    }
    
    if detected_models:
        result["models"] = list(detected_models)
    
    return result

def analyze_agent_trajectory(file_path):
    """分析Agent轨迹数据"""
    results = {"type": "轨迹/Trajectory"}
    detected_agents = set()
    detected_models = set()
    
    # 解压分析
    if file_path.endswith('.zip'):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            os.system(f'ditto -x -k "{file_path}" "{tmpdir}" 2>/dev/null')
            
            # 统计文件
            json_files = glob.glob(f"{tmpdir}/**/*.json", recursive=True)
            jsonl_files = glob.glob(f"{tmpdir}/**/*.jsonl", recursive=True)
            
            results["json_count"] = len(json_files)
            results["jsonl_count"] = len(jsonl_files)
            results["size_mb"] = os.path.getsize(file_path) / 1024 / 1024
            
            # 分析语言分布和检测智能体/模型
            languages = []
            for jf in json_files[:50]:
                try:
                    with open(jf) as f:
                        data = json.load(f)
                        lang = data.get('language', 'unknown')
                        if isinstance(lang, list):
                            languages.extend(lang)
                        else:
                            languages.append(lang)
                        
                        # 检测智能体类型
                        agent_type = data.get('agent_type', data.get('agent', ''))
                        if agent_type:
                            detected_agents.add(str(agent_type))
                        
                        # 检测工具使用
                        tools = data.get('tools_used', data.get('tools', []))
                        if tools:
                            for tool in tools if isinstance(tools, list) else [tools]:
                                if isinstance(tool, dict):
                                    detected_agents.add(tool.get('name', 'unknown_tool'))
                                else:
                                    detected_agents.add(str(tool))
                        
                        # 检测模型
                        model = data.get('model', data.get('llm_model', ''))
                        if model:
                            detected_models.add(str(model))
                except:
                    pass
            
            # 解析jsonl文件中的智能体和模型信息
            for jf in jsonl_files[:10]:
                try:
                    with open(jf, 'r') as f:
                        content = f.read()
                        # 用正则提取agent
                        agent_match = re.search(r'"agent"\s*:\s*"([^"]+)"', content)
                        if agent_match:
                            detected_agents.add(agent_match.group(1))
                        # 用正则提取model
                        model_match = re.search(r'"model"\s*:\s*"([^"]+)"', content)
                        if model_match:
                            detected_models.add(model_match.group(1))
                except:
                    pass
            
            results["languages"] = dict(Counter(languages))
            results["type"] = "轨迹/Trajectory"
            results["subtype"] = "Agent Coding轨迹"
            
            # 添加检测到的智能体和模型
            if detected_agents:
                results["agents"] = list(detected_agents)
            if detected_models:
                results["models"] = list(detected_models)
    
    return results

def analyze_gui_trajectory(file_path):
    """分析GUI轨迹数据"""
    results = {"type": "GUI/桌面", "subtype": "GUI Agent轨迹"}
    detected_agents = set()
    collect_methods = set()
    
    if file_path.endswith('.zip'):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            os.system(f'ditto -x -k "{file_path}" "{tmpdir}" 2>/dev/null')
            
            # 统计应用
            apps = []
            for item in os.listdir(tmpdir):
                if os.path.isdir(f"{tmpdir}/{item}"):
                    apps.append(item)
            
            # 统计文件
            all_files = glob.glob(f"{tmpdir}/**/*", recursive=True)
            json_files = [f for f in all_files if f.endswith('.json')]
            png_files = [f for f in all_files if f.endswith('.png')]
            
            # 从每个应用目录采样一个trajectory.json
            for app in apps:
                traj_files = glob.glob(f"{tmpdir}/{app}/**/trajectory.json", recursive=True)
                if traj_files:
                    try:
                        with open(traj_files[0], 'r') as f:
                            content = f.read()
                            # 提取应用名
                            app_match = re.search(r'"application"\s*:\s*"([^"]+)"', content)
                            if app_match:
                                detected_agents.add(app_match.group(1))
                            # 提取收集方式
                            collect_match = re.search(r'"collect_method"\s*:\s*"([^"]+)"', content)
                            if collect_match:
                                collect_methods.add(collect_match.group(1))
                    except:
                        pass
            
            results["apps"] = apps
            results["app_count"] = len(apps)
            results["json_count"] = len(json_files)
            results["screenshot_count"] = len(png_files)
            results["size_mb"] = os.path.getsize(file_path) / 1024 / 1024
            
            # 统计trajectory文件作为样本数
            traj_files = glob.glob(f"{tmpdir}/**/trajectory.json", recursive=True)
            results["count"] = len(traj_files)
            
            # 估算tokens (基于文件大小，每4字节约1 token)
            results["tokens_est"] = results["size_mb"] * 1024 * 1024 / 4
            
            if detected_agents:
                results["agents"] = list(detected_agents)
            if collect_methods:
                results["collect_method"] = list(collect_methods)
    
    return results

def analyze_swebench(file_path):
    """分析SWE-bench数据"""
    results = {"type": "SWE/工程", "subtype": "SWE-bench格式"}
    
    if file_path.endswith('.zip'):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            os.system(f'ditto -x -k "{file_path}" "{tmpdir}" 2>/dev/null')
            
            json_files = glob.glob(f"{tmpdir}/**/*.json", recursive=True)
            results["json_count"] = len(json_files)
            results["size_mb"] = os.path.getsize(file_path) / 1024 / 1024
            
            # 分析样本
            if json_files:
                with open(json_files[0]) as f:
                    data = json.load(f)
                    results["sample_repo"] = data.get('repo', 'unknown')
                    results["sample_lang"] = data.get('language', 'unknown')
    
    return results

def analyze_task_data(file_path):
    """分析任务数据"""
    results = {"type": "轨迹/Trajectory", "subtype": "任务轨迹"}
    
    if file_path.endswith('.zip') or file_path.endswith('.rar'):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            if file_path.endswith('.zip'):
                os.system(f'ditto -x -k "{file_path}" "{tmpdir}" 2>/dev/null')
            else:
                os.system(f'unrar x "{file_path}" "{tmpdir}" 2>/dev/null')
            
            traj_files = glob.glob(f"{tmpdir}/**/trajectory.json", recursive=True)
            qa_files = glob.glob(f"{tmpdir}/**/qa.json", recursive=True)
            
            results["trajectory_count"] = len(traj_files)
            results["qa_count"] = len(qa_files)
            results["size_mb"] = os.path.getsize(file_path) / 1024 / 1024
    
    return results

def calculate_scores(analysis):
    """计算评分"""
    scores = {}
    reasons = []
    suggestions = []
    
    data_types = analysis.get("data_types", ["通用/General"])
    primary_type = data_types[0] if data_types else "通用/General"
    count = analysis.get("count", analysis.get("trajectory_count", analysis.get("json_count", 1)))
    size_mb = analysis.get("size_mb", 0)
    tokens = analysis.get("tokens_est", size_mb * 1024 * 1024 / 4)
    
    # 数据规模评分
    if tokens > 50_000_000:  # 50M+ tokens
        scores["规模"] = 95
        reasons.append(f"规模大({tokens/1e6:.0f}M tokens)")
    elif tokens > 10_000_000:  # 10M+ tokens
        scores["规模"] = 85
        reasons.append(f"规模中等({tokens/1e6:.0f}M tokens)")
    elif tokens > 1_000_000:  # 1M+ tokens
        scores["规模"] = 75
        reasons.append(f"规模较小({tokens/1e6:.0f}M tokens)")
        suggestions.append("建议扩充数据规模至10M+ tokens")
    else:
        scores["规模"] = 60
        reasons.append(f"规模小({tokens/1e6:.1f}M tokens)")
        suggestions.append("数据规模不足，需大幅扩充")
    
    # 数据质量评分（基于数据类型）
    is_pretrain = any("预训练" in t for t in data_types)
    is_midtrain = any("中训练" in t for t in data_types)
    is_posttrain = any("后训练" in t for t in data_types)
    
    if "推理/Reasoning" in primary_type or "thinking" in str(analysis.get("name", "")).lower():
        scores["质量"] = 95
        scores["稀缺性"] = 98
        scores["训练价值"] = 98
        reasons.append("Thinking/推理数据稀缺性高")
        reasons.append("高价值推理链数据，适合用于推理能力训练")
    elif is_midtrain and "Agent轨迹" in str(data_types):
        scores["质量"] = 88
        scores["稀缺性"] = 85
        scores["训练价值"] = 92
        reasons.append("Coding Agent轨迹数据，适合构建Agent能力")
        reasons.append("包含多步推理、工具调用等关键能力数据")
        if count < 100:
            suggestions.append("建议扩充样本量至100+，覆盖更多场景")
    elif is_midtrain and "SWE" in str(data_types):
        scores["质量"] = 90
        scores["稀缺性"] = 75
        scores["训练价值"] = 88
        reasons.append("SWE工程数据，适合软件工程能力训练")
        if count < 50:
            suggestions.append("样本量有限，建议补充更多issue类型")
    elif is_pretrain:
        scores["质量"] = 85
        scores["稀缺性"] = 70
        scores["训练价值"] = 85
        reasons.append("预训练级数据，补充代码工程知识")
        if "技术文档" in str(data_types):
            reasons.append("技术文档数据，有助于模型理解API和框架使用")
        if "Q&A" in str(data_types):
            reasons.append("Q&A数据，有助于debug和问题解决能力")
    elif "GUI交互" in primary_type:
        scores["质量"] = 85
        scores["稀缺性"] = 80
        scores["训练价值"] = 85
        reasons.append("GUI交互轨迹数据稀缺")
        reasons.append(f"覆盖{analysis.get('app_count', '多')}个应用场景")
    elif "源代码" in primary_type:
        scores["质量"] = 80
        scores["稀缺性"] = 60
        scores["训练价值"] = 75
        reasons.append("源代码数据，基础训练素材")
    else:
        scores["质量"] = 75
        scores["稀缺性"] = 60
        scores["训练价值"] = 70
        reasons.append("数据类型较通用")
        suggestions.append("需明确数据用途和目标场景")
    
    # 完整性评分
    scores["完整性"] = 85
    
    # 场景覆盖评分（新增）
    languages = analysis.get("languages", {})
    if languages:
        lang_count = len(languages)
        if lang_count >= 5:
            scores["场景覆盖"] = 90
            reasons.append(f"覆盖{lang_count}种编程语言，语言多样性好")
        elif lang_count >= 3:
            scores["场景覆盖"] = 80
            reasons.append(f"覆盖{lang_count}种编程语言")
        else:
            scores["场景覆盖"] = 70
    else:
        scores["场景覆盖"] = 75
    
    # 总分
    total = sum(scores.values()) / len(scores)
    
    return scores, total, reasons, suggestions

def generate_report(datasets):
    """生成技术风格HTML报告"""
    
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>训练数据评估报告</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        /* Vim Default Color Scheme */
        :root {
            --bg: #1c1c1c;
            --bg-dark: #121212;
            --card: #262626;
            --border: #3a3a3a;
            --text: #d0d0d0;
            --muted: #808080;
            
            /* Vim syntax colors */
            --vim-comment: #5f875f;      /* 绿色注释 */
            --vim-keyword: #d75f5f;      /* 红色关键字 */
            --vim-string: #d7af5f;       /* 黄色字符串 */
            --vim-number: #af87af;       /* 紫色数字 */
            --vim-function: #87afd7;     /* 蓝色函数 */
            --vim-type: #afaf87;         /* 黄绿类型 */
            --vim-special: #87af87;      /* 绿色特殊 */
            --vim-error: #ff5f5f;        /* 红色错误 */
        }
        
        body { 
            font-family: 'Consolas', 'DejaVu Sans Mono', 'Monaco', 'Menlo', monospace;
            background: var(--bg); color: var(--text); 
            padding: 24px; line-height: 1.4;
            font-size: 14px;
        }
        
        .container { max-width: 1200px; margin: 0 auto; }
        
        /* Header - Vim command mode style */
        .header { 
            border-bottom: 1px solid var(--border); 
            padding-bottom: 12px; margin-bottom: 20px; 
        }
        .header h1 { 
            font-size: 18px; font-weight: bold; 
            color: var(--vim-function); 
            display: flex; align-items: center; gap: 8px;
        }
        .header h1::before { content: ":"; color: var(--vim-keyword); font-weight: bold; }
        .meta { color: var(--vim-comment); font-size: 12px; margin-top: 6px; }
        
        /* Summary Table */
        .summary-table { 
            width: 100%; border-collapse: collapse; margin-bottom: 24px;
        }
        .summary-table th { 
            text-align: left; padding: 10px 8px; 
            border-bottom: 1px solid var(--border);
            font-weight: bold; color: var(--vim-keyword); 
            font-size: 12px;
        }
        .summary-table td { 
            padding: 10px 8px; border-bottom: 1px solid var(--border);
        }
        .summary-table tr:hover td { background: var(--card); }
        
        /* Data Type Tags - Vim highlight groups */
        .tag { 
            display: inline-block; padding: 1px 5px; margin-right: 3px;
            border-radius: 2px; font-size: 11px;
            background: var(--bg-dark); color: var(--vim-function);
            border: 1px solid var(--border);
        }
        .tag-pre { color: var(--vim-special); border-color: var(--vim-special); }
        .tag-mid { color: var(--vim-string); border-color: var(--vim-string); }
        .tag-post { color: var(--vim-keyword); border-color: var(--vim-keyword); }
        
        /* Model & Agent Tags */
        .tag-model { color: var(--vim-number); border-color: var(--vim-number); background: rgba(175, 135, 175, 0.1); }
        .tag-agent { color: var(--vim-type); border-color: var(--vim-type); background: rgba(175, 175, 135, 0.1); }
        
        /* Score - Vim number highlight */
        .score { font-weight: bold; }
        .score-high { color: var(--vim-special); }
        .score-mid { color: var(--vim-string); }
        .score-low { color: var(--vim-error); }
        
        /* Grade Badge */
        .grade { 
            display: inline-block; padding: 1px 6px; border-radius: 2px;
            font-size: 12px; font-weight: bold;
        }
        .grade-a { background: var(--bg-dark); color: var(--vim-special); border: 1px solid var(--vim-special); }
        .grade-b { background: var(--bg-dark); color: var(--vim-string); border: 1px solid var(--vim-string); }
        .grade-c { background: var(--bg-dark); color: var(--vim-error); border: 1px solid var(--vim-error); }
        
        /* Recommendation */
        .action { font-size: 12px; font-weight: bold; }
        .action-buy { color: var(--vim-special); }
        .action-expand { color: var(--vim-string); }
        .action-verify { color: var(--vim-function); }
        
        /* Dataset Cards */
        .dataset-grid { display: grid; gap: 12px; }
        
        .card {
            background: var(--card); border: 1px solid var(--border);
            border-radius: 2px; padding: 14px;
        }
        .card:hover { border-color: var(--vim-function); }
        
        .card-header { 
            display: flex; justify-content: space-between; align-items: flex-start; 
            margin-bottom: 10px; 
        }
        .card-title { font-size: 14px; font-weight: bold; color: var(--vim-function); }
        .card-types { margin-top: 4px; }
        .card-score { font-size: 24px; font-weight: bold; font-family: inherit; }
        
        /* Stats Grid */
        .stats { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); 
            gap: 6px; margin: 10px 0; 
        }
        .stat { 
            background: var(--bg-dark); padding: 8px; border-radius: 2px;
            border: 1px solid var(--border);
        }
        .stat-label { font-size: 10px; color: var(--vim-comment); text-transform: uppercase; }
        .stat-value { font-size: 13px; color: var(--vim-number); margin-top: 2px; }
        
        /* Dimensions - Vim statusline style */
        .dims { margin-top: 10px; }
        .dim { display: flex; align-items: center; gap: 6px; margin: 4px 0; }
        .dim-name { width: 60px; font-size: 11px; color: var(--vim-comment); }
        .dim-bar { flex: 1; height: 3px; background: var(--bg-dark); border-radius: 1px; }
        .dim-fill { height: 100%; border-radius: 1px; background: var(--vim-function); }
        .dim-val { width: 26px; font-size: 12px; text-align: right; color: var(--vim-number); }
        
        /* Analysis Section - Vim fold style */
        .analysis { 
            margin-top: 10px; padding: 10px; 
            background: var(--bg-dark); border-radius: 2px; 
            border-left: 2px solid var(--vim-comment);
        }
        .analysis-title { 
            font-size: 11px; color: var(--vim-comment); 
            text-transform: uppercase; margin-bottom: 6px; 
        }
        .analysis-list { margin: 0; padding-left: 14px; }
        .analysis-list li { 
            font-size: 12px; color: var(--text); margin: 3px 0; 
        }
        
        /* Footer - Vim command line style */
        .footer { 
            margin-top: 30px; padding-top: 12px; 
            border-top: 1px solid var(--border); 
            color: var(--vim-comment); font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TRAINING DATA EVALUATION</h1>
            <div class="meta">
                ''' + datetime.now().strftime('%Y-%m-%d %H:%M') + ''' | ''' + str(len(datasets)) + ''' datasets
            </div>
        </div>
'''
    
    # 汇总表格
    html += '''
        <table class="summary-table">
            <tr>
                <th>Dataset</th>
                <th>Type</th>
                <th>Size</th>
                <th>Tokens</th>
                <th>Score</th>
                <th>Grade</th>
                <th>Recommendation</th>
            </tr>
'''
    
    for ds in sorted(datasets, key=lambda x: x.get('total_score', 0), reverse=True):
        name = ds.get('name', 'Unknown')
        dtype = ds.get('type', 'General')
        subtype = ds.get('subtype', '')
        size_mb = ds.get('size_mb', 0)
        tokens = ds.get('tokens_est', 0)
        total_score = ds.get('total_score', 0)
        grade = 'A' if total_score >= 85 else 'B' if total_score >= 70 else 'C'
        rec = ds.get('recommendation', 'maybe')
        rec_text = '✓ 推荐' if rec == 'yes' else '⚠ 待定' if rec == 'maybe' else '✗ 不推荐'
        
        html += f'''
            <tr>
                <td>{name[:30]}</td>
                <td>{dtype}</td>
                <td>{size_mb:.1f} MB</td>
                <td>{tokens/1e6:.1f}M</td>
                <td class="score-{grade.lower()}">{total_score:.0f}</td>
                <td>{grade}</td>
                <td>{rec_text}</td>
            </tr>
'''
    
    html += '''
        </table>
        
        <div class="dataset-grid">
'''
    
    # 详细卡片
    for i, ds in enumerate(sorted(datasets, key=lambda x: x.get('total_score', 0), reverse=True)):
        name = ds.get('name', 'Unknown')
        data_types = ds.get('data_types', ['通用/General'])
        scores = ds.get('scores', {})
        total_score = ds.get('total_score', 0)
        grade = 'A' if total_score >= 85 else 'B' if total_score >= 70 else 'C'
        
        # 生成数据类型标签
        type_tags = ''
        for dt in data_types[:3]:  # 最多显示3个
            if '预训练' in dt:
                type_tags += f'<span class="tag tag-pre">{dt}</span>'
            elif '中训练' in dt:
                type_tags += f'<span class="tag tag-mid">{dt}</span>'
            elif '后训练' in dt:
                type_tags += f'<span class="tag tag-post">{dt}</span>'
            else:
                type_tags += f'<span class="tag">{dt}</span>'
        
        # 统计数据 - 统一显示所有维度
        tokens_val = f"{ds.get('tokens_est', 0)/1e6:.1f}M" if ds.get('tokens_est') else "-"
        size_val = f"{ds.get('size_mb', 0):.1f}MB" if ds.get('size_mb') else "-"
        samples_val = f"{ds.get('count', 0):,}" if ds.get('count') else "-"
        
        # 编程语言
        languages = ds.get('languages', {})
        if languages:
            lang_str = ', '.join(list(languages.keys())[:3])
        else:
            lang_str = "-"
        
        stats_html = f'''
        <div class="stat"><div class="stat-label">Tokens</div><div class="stat-value">{tokens_val}</div></div>
        <div class="stat"><div class="stat-label">Size</div><div class="stat-value">{size_val}</div></div>
        <div class="stat"><div class="stat-label">Samples</div><div class="stat-value">{samples_val}</div></div>
        <div class="stat"><div class="stat-label">Language</div><div class="stat-value">{lang_str}</div></div>
        '''
        
        # 模型信息 - 显示所有检测到的模型（不折叠）
        models = ds.get('models', [])
        models_html = ''
        if models:
            for m in models:
                models_html += f'<span class="tag tag-model">{m}</span>'
        else:
            models_html = '<span class="tag" style="color:var(--muted);">-</span>'
        
        # 智能体信息 - 显示所有检测到的智能体（不折叠）
        agents = ds.get('agents', [])
        agents_html = ''
        if agents:
            for a in agents:
                agents_html += f'<span class="tag tag-agent">{a}</span>'
        else:
            agents_html = '<span class="tag" style="color:var(--muted);">-</span>'
        
        # 收集方式
        collect = ds.get('collect_method', [])
        collect_html = ', '.join(collect) if collect else '-'
        
        # 评分维度
        dims_html = ''
        for dim_name, dim_score in scores.items():
            fill_width = dim_score
            dims_html += f'''
            <div class="dim">
                <span class="dim-name">{dim_name}</span>
                <div class="dim-bar"><div class="dim-fill" style="width:{fill_width}%"></div></div>
                <span class="dim-val">{dim_score}</span>
            </div>'''
        
        # 原因和建议
        reasons = ds.get('reasons', [])
        suggestions = ds.get('suggestions', [])
        
        analysis_html = ''
        if reasons:
            reasons_list = '\n'.join([f'<li>{r}</li>' for r in reasons[:3]])
            analysis_html += f'''
            <div class="analysis">
                <div class="analysis-title">Reasons</div>
                <ul class="analysis-list">{reasons_list}</ul>
            </div>'''
        
        if suggestions:
            suggestions_list = '\n'.join([f'<li>{s}</li>' for s in suggestions[:2]])
            analysis_html += f'''
            <div class="analysis">
                <div class="analysis-title">Suggestions</div>
                <ul class="analysis-list">{suggestions_list}</ul>
            </div>'''
        
        # 采购建议
        rec = ds.get('recommendation', 'maybe')
        if rec == 'yes':
            action = '<span class="action action-buy">BUY</span>'
        elif rec == 'maybe':
            action = '<span class="action action-expand">EXPAND</span>'
        else:
            action = '<span class="action action-verify">VERIFY</span>'
        
        html += f'''
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="card-title">{name}</div>
                    <div class="card-types">{type_tags}</div>
                </div>
                <div class="card-score score-{"high" if grade=="A" else "mid" if grade=="B" else "low"}">{total_score:.0f}</div>
            </div>
            
            <div class="stats">{stats_html}</div>
            
            {f'<div style="margin:8px 0;">{models_html}</div>' if models_html else ''}
            {f'<div style="margin:8px 0;">{agents_html}</div>' if agents_html else ''}
            
            <div class="dims">{dims_html}</div>
            
            {analysis_html}
            
            <div style="margin-top:12px;">{action}</div>
        </div>
'''
    
    html += '''
        </div>
        
        <div class="footer">
            Training Data Evaluator v2.1 | Technical Style
        </div>
    </div>
</body>
</html>
'''
    
    return html

def main():
    """主评估流程"""
    print("正在扫描数据文件...")
    
    # 扫描所有数据文件
    data_files = []
    for ext in ['*.zip', '*.rar', '*.txt']:
        data_files.extend(glob.glob(f"{WORKSPACE}/{ext}"))
    
    print(f"发现 {len(data_files)} 个数据文件")
    
    datasets = []
    
    for file_path in data_files:
        file_name = os.path.basename(file_path)
        print(f"\n分析: {file_name}")
        
        analysis = {"name": file_name, "file_path": file_path}
        
        # 首先进行数据类型分类
        data_types = classify_data_type(file_path)
        analysis["data_types"] = data_types
        
        # 根据文件名判断分析方式
        if "thinking" in file_name.lower():
            result = analyze_thinking_data(file_path)
            analysis.update(result)
            analysis["data_types"] = ["推理/Reasoning", "中训练/Agent轨迹"]
            analysis["recommendation"] = "yes"
        elif "gui" in file_name.lower():
            # GUI轨迹数据优先匹配
            result = analyze_gui_trajectory(file_path)
            analysis.update(result)
            analysis["data_types"] = ["中训练/Agent轨迹", "GUI交互"]
            analysis["recommendation"] = "yes"
        elif "agent coding" in file_name.lower() or "轨迹" in file_name:
            result = analyze_agent_trajectory(file_path)
            analysis.update(result)
            analysis["data_types"] = ["中训练/Agent轨迹", "中训练/SWE-工程", "源代码"]
            analysis["recommendation"] = "maybe"
        elif "swebench" in file_name.lower() or "swe" in file_name.lower():
            result = analyze_swebench(file_path)
            analysis.update(result)
            analysis["data_types"] = ["中训练/SWE-工程", "源代码"]
            analysis["recommendation"] = "maybe"
        elif "l3" in file_name.lower() or "l4" in file_name.lower() or "抽检" in file_name:
            result = analyze_task_data(file_path)
            analysis.update(result)
            analysis["data_types"] = ["中训练/SWE-工程", "中训练/Agent轨迹"]
            analysis["recommendation"] = "maybe"
        elif "网页" in file_name.lower() or "站点" in file_name.lower():
            # 网页站点代码数据
            analysis["size_mb"] = os.path.getsize(file_path) / 1024 / 1024
            analysis["data_types"] = ["预训练/技术文档", "预训练/Demo/示例", "源代码"]
            analysis["recommendation"] = "maybe"
        else:
            # 通用分析
            analysis["size_mb"] = os.path.getsize(file_path) / 1024 / 1024
            analysis["recommendation"] = "maybe"
        
        # 设置主类型
        analysis["type"] = analysis["data_types"][0] if analysis.get("data_types") else "通用/General"
        
        # 计算评分
        scores, total, reasons, suggestions = calculate_scores(analysis)
        analysis["scores"] = scores
        analysis["total_score"] = total
        analysis["reasons"] = reasons
        analysis["suggestions"] = suggestions
        
        datasets.append(analysis)
        print(f"  类型: {analysis.get('data_types', [])}")
        print(f"  评分: {total:.1f}")
    
    # 保存历史
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump({
            "last_update": datetime.now().isoformat(),
            "datasets": datasets
        }, f, ensure_ascii=False, indent=2)
    
    # 生成报告
    html = generate_report(datasets)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = f"{OUTPUT_DIR}/index.html"
    with open(report_path, 'w') as f:
        f.write(html)
    
    print(f"\n✅ 报告已生成: {report_path}")
    return report_path

if __name__ == "__main__":
    main()
