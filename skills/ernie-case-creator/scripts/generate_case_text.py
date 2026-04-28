#!/usr/bin/env python3
"""
案例文字生成脚本
基于提取的案例信息，生成标准化的案例说明文字
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class CaseInfo:
    """案例信息结构"""
    project_name: str
    industry: str
    ernie_models: List[str]
    pain_points: List[str]
    solution: str
    effects: List[str]
    quantitative_data: Dict[str, Any]
    materials: List[str]  # 原始材料片段


class CaseTextGenerator:
    """案例文字生成器"""
    
    def __init__(self):
        self.template = {
            'pain_point': "面对{industry}行业{problem}的痛点，{impact}。",
            'application': "在{application_scene}场景中，服务于{target_users}。",
            'technology': "项目基于{ernie_models}，{technical_advantages}。",
            'solution': "{solution_description}，实现了{achievement}。",
            'value': "实施后，{quantitative_effects}，{qualitative_effects}。"
        }
    
    def generate_prompt(self, case_info: CaseInfo) -> str:
        """生成用于AI撰写的Prompt"""
        
        # 构建材料信息
        materials_summary = []
        
        if case_info.project_name:
            materials_summary.append(f"项目名称: {case_info.project_name}")
        
        if case_info.industry:
            materials_summary.append(f"所属行业: {case_info.industry}")
        
        if case_info.ernie_models:
            models_str = '、'.join(case_info.ernie_models)
            materials_summary.append(f"使用的文心模型: {models_str}")
        
        if case_info.pain_points:
            materials_summary.append("行业痛点:")
            for i, point in enumerate(case_info.pain_points[:3], 1):
                materials_summary.append(f"  {i}. {point}")
        
        if case_info.solution:
            materials_summary.append(f"解决方案: {case_info.solution}")
        
        if case_info.effects:
            materials_summary.append("实施效果:")
            for i, effect in enumerate(case_info.effects[:3], 1):
                materials_summary.append(f"  {i}. {effect}")
        
        if case_info.quantitative_data:
            materials_summary.append("量化数据:")
            for key, values in case_info.quantitative_data.items():
                if values:
                    if key == 'percentage_improvements':
                        percentages = values[:3]
                        materials_summary.append(f"  提升百分比: {', '.join(percentages)}%")
                    elif key == 'time_improvements':
                        for before, after in values[:2]:
                            materials_summary.append(f"  时间优化: {before} → {after}")
        
        materials_text = '\n'.join(materials_summary)
        
        # 构建Prompt
        prompt = f"""你是一位专业的技术案例撰写专家。请根据提供的案例材料，按照"问题-场景-技术-方案-价值"五段式框架，撰写一篇250-350字的案例说明。

【案例材料】
{materials_text}

【撰写要求】
1. 痛点/背景（1-2句话）：明确行业痛点，说明痛点带来的影响
2. 应用环境（1句话）：明确行业领域、使用场景、目标用户
3. 技术支撑（1-2句话）：明确文心模型型号，强调技术适配性
4. 解决方案（2-3句话）：阐述核心功能，说明解决路径
5. 价值成果（2-3句话）：量化业务提升，说明落地规模

【字数要求】
总字数控制在250-350字之间。

【输出格式】
直接输出案例说明文字，不需要标注各部分标题。"""
        
        return prompt
    
    def validate_case_text(self, text: str) -> Dict[str, Any]:
        """验证生成的案例文字"""
        validation = {
            'valid': True,
            'issues': [],
            'suggestions': []
        }
        
        # 检查字数
        text_length = len(text)
        if text_length < 250:
            validation['issues'].append(f'字数不足250字（当前{text_length}字）')
            validation['valid'] = False
        elif text_length > 350:
            validation['issues'].append(f'字数超过350字（当前{text_length}字）')
            validation['valid'] = False
        
        # 检查段落结构
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        if len(paragraphs) < 3:
            validation['suggestions'].append('建议适当分段，增强可读性')
        
        # 检查是否有量化数据
        percentage_pattern = r'\d+(?:\.\d+)?%'
        percentage_matches = re.findall(percentage_pattern, text)
        if not percentage_matches:
            validation['suggestions'].append('建议添加百分比等量化数据')
        
        # 检查是否有文心模型信息
        model_patterns = [
            r'ERNIE[-\s]*4[\.\s]*5',
            r'文心[-\s]*4[\.\s]*5',
            r'4\.5',
            r'5\.0'
        ]
        has_model = False
        for pattern in model_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                has_model = True
                break
        
        if not has_model:
            validation['suggestions'].append('建议明确提及使用的文心模型型号')
        
        return validation
    
    def generate_from_info(self, case_info: CaseInfo) -> Dict[str, Any]:
        """从案例信息生成案例文字"""
        
        # 生成Prompt
        prompt = self.generate_prompt(case_info)
        
        # 这里实际应该调用AI模型生成文字
        # 由于是示例，我们返回一个示例文字
        example_text = """国网四川电力面对35千伏及以上项目投资问效分析效率低下的痛点，传统方法单项目分析耗时2-3小时，严重制约了投资决策的时效性。在电力投资决策场景中，服务于电网规划部门的项目评估团队。

项目基于文心大模型与Agentic智能体架构，创新构建"自主规划-工具执行-结果反思"的闭环分析系统。该系统通过智能体自动识别项目关键要素，调度专业分析工具进行模拟计算，并对结果进行自我评估与优化，实现了端到端的智能化分析。

实施后，单项目分析耗时从2-3小时骤降至10分钟内，效率提升95%以上。已成功完成300个项目分析，报告自动生成率100%、准确率超90%，为电力行业投资决策智能化树立了新标杆。"""
        
        # 验证生成的文字
        validation = self.validate_case_text(example_text)
        
        return {
            'success': True,
            'case_text': example_text,
            'prompt': prompt,
            'validation': validation,
            'word_count': len(example_text)
        }
    
    def extract_case_info_from_dict(self, info_dict: Dict[str, Any]) -> CaseInfo:
        """从字典提取案例信息"""
        return CaseInfo(
            project_name=info_dict.get('project_name', ''),
            industry=info_dict.get('industry', ''),
            ernie_models=info_dict.get('ernie_models', []),
            pain_points=info_dict.get('pain_points', []),
            solution=info_dict.get('solution', ''),
            effects=info_dict.get('effects', []),
            quantitative_data=info_dict.get('quantitative_data', {}),
            materials=info_dict.get('materials', [])
        )


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='文心案例文字生成工具')
    parser.add_argument('--info-json', required=True, help='案例信息JSON文件路径')
    parser.add_argument('--output', default='./case_text.txt', help='输出文件路径')
    
    args = parser.parse_args()
    
    # 读取案例信息
    try:
        with open(args.info_json, 'r', encoding='utf-8') as f:
            info_dict = json.load(f)
    except Exception as e:
        print(f"❌ 读取案例信息失败: {str(e)}")
        sys.exit(1)
    
    # 生成案例文字
    generator = CaseTextGenerator()
    case_info = generator.extract_case_info_from_dict(info_dict)
    result = generator.generate_from_info(case_info)
    
    if result['success']:
        # 输出案例文字
        case_text = result['case_text']
        print("=== 生成的案例说明 ===")
        print(case_text)
        print(f"\n字数: {result['word_count']}字")
        
        # 保存到文件
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(case_text)
        print(f"✅ 案例文字已保存到: {args.output}")
        
        # 显示验证结果
        validation = result['validation']
        if validation['issues']:
            print("\n⚠️  问题:")
            for issue in validation['issues']:
                print(f"   - {issue}")
        
        if validation['suggestions']:
            print("\n💡 建议:")
            for suggestion in validation['suggestions']:
                print(f"   - {suggestion}")
        
        # 显示Prompt（供参考）
        print(f"\n📝 使用的Prompt:")
        print("-" * 50)
        print(result['prompt'][:500] + "..." if len(result['prompt']) > 500 else result['prompt'])
        print("-" * 50)
    else:
        print(f"❌ 生成失败: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    import sys
    main()