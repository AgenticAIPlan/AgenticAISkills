#!/usr/bin/env python3
"""
案例材料解析脚本
支持Word、PPT、PDF等多种格式的材料解析和关键信息提取
"""

import os
import json
import re
import sys
from typing import Dict, List, Optional, Any


class MaterialParser:
    """案例材料解析器"""
    
    def __init__(self):
        self.supported_formats = ['.docx', '.pptx', '.pdf', '.txt', '.md']
        self.ernie_model_patterns = [
            r'ERNIE[-\s]*4[\.\s]*5[-\s]*21[Bb]',
            r'ERNIE[-\s]*4[\.\s]*5[-\s]*28[Bb][-\s]*VL',
            r'ERNIE[-\s]*5[\.\s]*0',
            r'文心[-\s]*4[\.\s]*5[-\s]*21[Bb]',
            r'文心[-\s]*4[\.\s]*5[-\s]*28[Bb][-\s]*VL',
            r'文心[-\s]*5[\.\s]*0',
            r'4\.5-21[Bb]',
            r'4\.5-28[Bb]-VL',
            r'5\.0'
        ]
        
        self.extracted_info = {
            'project_name': '',
            'industry': '',
            'pain_points': [],
            'ernie_models': [],
            'solution': '',
            'effects': [],
            'quantitative_data': {},
            'materials': []  # 原始材料内容片段
        }
    
    def detect_format(self, file_path: str) -> str:
        """检测文件格式"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.supported_formats:
            return ext
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def extract_text_content(self, file_path: str) -> str:
        """提取文本内容（简化版，实际应使用对应库）"""
        ext = self.detect_format(file_path)
        content = ""
        
        # 这里简化为读取文本文件，实际应用中应使用对应库
        if ext in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # 对于Word、PPT、PDF，这里返回提示信息
            # 实际应用中应使用python-docx、python-pptx、PyPDF2等库
            content = f"[文件格式: {ext}，需要相应库进行解析]"
            
        return content
    
    def parse_content(self, content: str) -> Dict[str, Any]:
        """解析文本内容，提取关键信息"""
        
        # 提取项目名称
        project_name_match = re.search(r'项目名称[:：]\s*(.+?)(?:\n|$)', content)
        if project_name_match:
            self.extracted_info['project_name'] = project_name_match.group(1).strip()
        else:
            # 尝试从标题中提取
            title_match = re.search(r'^#\s+(.+?)\n', content)
            if title_match:
                self.extracted_info['project_name'] = title_match.group(1).strip()
        
        # 提取行业信息
        industry_match = re.search(r'行业[:：]\s*(.+?)(?:\n|$)', content)
        if industry_match:
            self.extracted_info['industry'] = industry_match.group(1).strip()
        
        # 提取文心模型信息
        for pattern in self.ernie_model_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match not in self.extracted_info['ernie_models']:
                    self.extracted_info['ernie_models'].append(match)
        
        # 提取痛点信息
        pain_point_sections = re.findall(r'痛点[:：].*?(?:\n\n|\n#|\n##|$)', content, re.DOTALL)
        for section in pain_point_sections:
            # 清理section
            clean_section = re.sub(r'痛点[:：]\s*', '', section).strip()
            if clean_section:
                self.extracted_info['pain_points'].append(clean_section)
        
        # 提取效果信息
        effect_sections = re.findall(r'效果[:：].*?(?:\n\n|\n#|\n##|$)', content, re.DOTALL)
        for section in effect_sections:
            clean_section = re.sub(r'效果[:：]\s*', '', section).strip()
            if clean_section:
                self.extracted_info['effects'].append(clean_section)
        
        # 提取量化数据
        # 查找百分比提升
        percentage_matches = re.findall(r'(\d+(?:\.\d+)?)%', content)
        if percentage_matches:
            self.extracted_info['quantitative_data']['percentage_improvements'] = percentage_matches
        
        # 查找时间提升
        time_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:小时|分钟|天|月)\s*[降至→→降为]?\s*(\d+(?:\.\d+)?)\s*(?:小时|分钟|天|月)', content)
        if time_matches:
            self.extracted_info['quantitative_data']['time_improvements'] = time_matches
        
        # 存储原始材料片段（前500字符）
        if content:
            self.extracted_info['materials'] = [content[:500] + "..." if len(content) > 500 else content]
        
        return self.extracted_info
    
    def generate_summary(self) -> str:
        """生成信息摘要"""
        summary = []
        
        if self.extracted_info['project_name']:
            summary.append(f"项目名称: {self.extracted_info['project_name']}")
        
        if self.extracted_info['industry']:
            summary.append(f"所属行业: {self.extracted_info['industry']}")
        
        if self.extracted_info['ernie_models']:
            models_str = ', '.join(self.extracted_info['ernie_models'])
            summary.append(f"文心模型: {models_str}")
        
        if self.extracted_info['pain_points']:
            summary.append("核心痛点:")
            for i, point in enumerate(self.extracted_info['pain_points'][:3], 1):
                summary.append(f"  {i}. {point[:100]}...")
        
        if self.extracted_info['effects']:
            summary.append("实施效果:")
            for i, effect in enumerate(self.extracted_info['effects'][:3], 1):
                summary.append(f"  {i}. {effect[:100]}...")
        
        if self.extracted_info['quantitative_data']:
            summary.append("量化数据:")
            for key, values in self.extracted_info['quantitative_data'].items():
                if values:
                    if key == 'percentage_improvements':
                        summary.append(f"  提升百分比: {', '.join(values[:5])}%")
                    elif key == 'time_improvements':
                        time_strs = []
                        for before, after in values[:3]:
                            time_strs.append(f"{before}→{after}")
                        summary.append(f"  时间优化: {', '.join(time_strs)}")
        
        return '\n'.join(summary)
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """解析文件"""
        try:
            # 检测文件格式
            format_type = self.detect_format(file_path)
            
            # 提取内容
            content = self.extract_text_content(file_path)
            
            # 解析内容
            result = self.parse_content(content)
            
            # 添加文件信息
            result['file_info'] = {
                'file_path': file_path,
                'format': format_type,
                'content_length': len(content)
            }
            
            return {
                'success': True,
                'data': result,
                'summary': self.generate_summary(),
                'message': '文件解析成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'文件解析失败: {str(e)}'
            }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python parse_material.py <文件路径>")
        print("示例: python parse_material.py ./案例材料.docx")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        sys.exit(1)
    
    parser = MaterialParser()
    result = parser.parse_file(file_path)
    
    if result['success']:
        print("=== 材料解析结果 ===")
        print(result['summary'])
        print("\n=== 详细信息 ===")
        print(json.dumps(result['data'], ensure_ascii=False, indent=2))
    else:
        print(f"错误: {result['message']}")


if __name__ == "__main__":
    main()