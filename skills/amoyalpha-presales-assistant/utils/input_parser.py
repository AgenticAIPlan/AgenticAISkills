#!/usr/bin/env python3
"""
客户类型自动识别工具。
优先使用关键词规则引擎，模糊情况记录供上层 LLM 判断。
"""

import re

# 关键词规则（优先级：政府 > 技术型 > 头部企业）
GOVERNMENT_PATTERNS = [
    r"(市|区|县|省|国|镇|乡|街道)(人民政府|政府|政务)",
    r"(局|委|办|厅|部|署|院|馆|站|所|中心|管委会|管理局|监督局|执法局)",
    r"(公安|卫健|教育|民政|税务|市监|城管|交通|水利|农业|林业|自然资源)",
    r"(人大|政协|纪委|监委|发改|财政|审计|统计)",
    r"政务|政府采购|招投标|政采云|公共资源交易",
]

TECH_PATTERNS = [
    r"(AI|人工智能|机器学习|深度学习)(公司|企业|团队|创业)",
    r"(SaaS|PaaS|IaaS)(公司|平台|产品)",
    r"(开发者|工程师|算法)(平台|工具|社区)",
    r"(大模型|LLM|AIGC)(公司|团队|产品)",
    r"API|SDK|开源|GitHub|PyTorch|TensorFlow",
    r"(科技|智能|数智|AI)(有限公司|股份|集团).*?(成立|成员|人员)\s*\d+(人|名)",
    r"初创|创业|融资|轮次|天使轮|A轮|B轮|C轮",
]

ENTERPRISE_PATTERNS = [
    r"(集团|股份|控股)(有限公司|公司)",
    r"(上市|主板|创业板|科创板|港股|纳斯达克)",
    r"(行业|领域)(龙头|领先|第一|头部|标杆)",
    r"(百强|500强|千亿|百亿|十亿)(企业|公司|营收)",
    r"(制造|金融|零售|物流|医疗|能源|化工|建筑)(集团|企业|公司)",
]


def detect_client_type(text: str) -> dict:
    """
    自动识别客户类型。

    返回:
        dict: {
            "type": "government" | "enterprise" | "tech" | "unknown",
            "confidence": "high" | "medium" | "low",
            "matched_keywords": [...],
            "needs_llm": bool
        }
    """
    text_lower = text.lower()
    results = {
        "government": [],
        "tech": [],
        "enterprise": [],
    }

    for pattern in GOVERNMENT_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            results["government"].extend(
                [m if isinstance(m, str) else "".join(m) for m in matches]
            )

    for pattern in TECH_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            results["tech"].extend(
                [m if isinstance(m, str) else "".join(m) for m in matches]
            )

    for pattern in ENTERPRISE_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            results["enterprise"].extend(
                [m if isinstance(m, str) else "".join(m) for m in matches]
            )

    gov_score = len(results["government"])
    tech_score = len(results["tech"])
    ent_score = len(results["enterprise"])

    # 判断逻辑：政府优先，然后技术型，然后头部企业
    if gov_score > 0:
        client_type = "government"
        confidence = "high" if gov_score >= 2 else "medium"
        matched = results["government"]
    elif tech_score > 0 and tech_score >= ent_score:
        client_type = "tech"
        confidence = "high" if tech_score >= 2 else "medium"
        matched = results["tech"]
    elif ent_score > 0:
        client_type = "enterprise"
        confidence = "high" if ent_score >= 2 else "medium"
        matched = results["enterprise"]
    else:
        client_type = "unknown"
        confidence = "low"
        matched = []

    return {
        "type": client_type,
        "confidence": confidence,
        "matched_keywords": list(set(matched))[:5],
        "needs_llm": confidence == "low" or client_type == "unknown",
    }


def parse_client_info(raw_input: str) -> dict:
    """
    解析用户输入的客户信息，提取结构化字段。

    返回包含客户基本信息的字典。
    """
    result = {
        "raw_input": raw_input,
        "client_type_detection": detect_client_type(raw_input),
        "extracted": {
            "company_name": None,
            "industry": None,
            "size": None,
            "contact_context": None,
        },
    }

    # 简单提取公司名（以"有限公司"/"集团"/"局"/"委"等结尾的词组）
    company_patterns = [
        r"[\u4e00-\u9fa5a-zA-Z0-9]+(?:有限公司|股份公司|集团|局|委|办|厅|部|管委会|研究院)",
    ]
    for pattern in company_patterns:
        match = re.search(pattern, raw_input)
        if match:
            result["extracted"]["company_name"] = match.group(0)
            break

    return result
