#!/usr/bin/env python3
"""
飞书多维表格 (Bitable) 写入模块
支持详细的政策信息字段
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class FeishuBitableClient:
    """飞书多维表格客户端"""

    def __init__(self, app_id: str, app_secret: str, base_token: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_token = base_token
        self.base_url = "https://open.feishu.cn/open-apis"
        self.tenant_token = None

    def get_tenant_token(self) -> str:
        """获取 tenant access token"""
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            self.tenant_token = result["tenant_access_token"]
            logger.info("✅ 成功获取飞书访问令牌")
            return self.tenant_token
        else:
            raise Exception(f"获取token失败: {result}")

    def ensure_token(self):
        """确保token有效"""
        if not self.tenant_token:
            self.get_tenant_token()

    def read_records(self, table_id: str, filter_str: str = None) -> List[Dict]:
        """读取表格记录"""
        self.ensure_token()
        url = f"{self.base_url}/bitable/v1/apps/{self.base_token}/tables/{table_id}/records"
        headers = {"Authorization": f"Bearer {self.tenant_token}"}
        params = {"page_size": 500}
        if filter_str:
            params["filter"] = filter_str

        response = requests.get(url, headers=headers, params=params)
        result = response.json()
        if result.get("code") == 0:
            return result.get("data", {}).get("items", [])
        return []

    def create_record(self, table_id: str, fields: Dict) -> Dict:
        """创建新记录"""
        self.ensure_token()
        url = f"{self.base_url}/bitable/v1/apps/{self.base_token}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {self.tenant_token}",
            "Content-Type": "application/json"
        }
        data = {"fields": fields}
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            logger.info(f"✅ 成功创建记录: {fields.get('政策标题', 'Unknown')[:30]}...")
        else:
            logger.error(f"❌ 创建记录失败: {result}")
        return result

    def update_record(self, table_id: str, record_id: str, fields: Dict) -> Dict:
        """更新记录"""
        self.ensure_token()
        url = f"{self.base_url}/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {self.tenant_token}",
            "Content-Type": "application/json"
        }
        data = {"fields": fields}
        response = requests.put(url, headers=headers, json=data)
        return response.json()

    def delete_record(self, table_id: str, record_id: str) -> Dict:
        """删除记录"""
        self.ensure_token()
        url = f"{self.base_url}/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {self.tenant_token}",
            "Content-Type": "application/json"
        }
        response = requests.delete(url, headers=headers)
        return response.json()


class PolicyBitableWriter:
    """政策数据Bitable写入器"""

    def __init__(self, config: Dict):
        self.config = config
        bitable_config = config.get('feishu_bitable', {})

        self.app_id = bitable_config.get('app_id', '')
        self.app_secret = bitable_config.get('app_secret', '')
        self.base_token = bitable_config.get('base_token', '')
        self.table_id = bitable_config.get('table_id', '')

        self.enabled = bitable_config.get('enabled', False)
        self.client = None

        if self.enabled and self.app_id and self.app_secret and self.base_token:
            self.client = FeishuBitableClient(self.app_id, self.app_secret, self.base_token)

    def is_ready(self) -> bool:
        """检查是否已配置并可使用"""
        return self.enabled and self.client is not None and self.table_id

    def write_policy(self, policy: Dict) -> bool:
        """
        将单条政策写入多维表格

        字段映射（按表格列顺序）：
        - 地区: 从标题或URL解析（首列，彩色标签）
        - 政策标题: policy['title']
        - 来源部门: policy['source_name']
        - 政策摘要: policy['summary']
        - 原文链接: policy['url']
        - 关键词标签: policy['categories']
        - 相关政策: policy['related_policies']
        - 文件原名: 从URL解析
        - 政策类型: 通知/意见/办法/规定等
        - 优先级: 高/中/低
        - 处理状态: 待处理/处理中/已完成
        - 备注: 额外信息
        - 政策发布日期: policy['pub_date']（时间字段，放最后）
        - 抓取日期: 系统自动填充（最后）
        """
        if not self.is_ready():
            logger.warning("Bitable未配置，跳过写入")
            return False

        # 去重检查：检查是否已存在相同标题或URL的记录
        title = policy.get('title', '').strip()
        url = policy.get('url', '').strip()

        if self._check_duplicate(title, url):
            logger.info(f"  跳过重复记录: {title[:40]}...")
            return True  # 返回True表示已处理（跳过）

        try:
            fields = self._build_fields(policy)
            result = self.client.create_record(self.table_id, fields)
            return result.get("code") == 0
        except Exception as e:
            logger.error(f"写入Bitable失败: {e}")
            return False

    def _check_duplicate(self, title: str, url: str) -> bool:
        """检查是否已存在相同标题或URL的记录"""
        if not self.is_ready() or not title:
            return False

        try:
            # 读取现有记录进行检查
            records = self.client.read_records(self.table_id)

            for record in records:
                fields = record.get("fields", {})
                existing_title = fields.get("政策标题", "")
                existing_url = fields.get("原文链接", "")

                # 标题相同视为重复
                if existing_title == title:
                    return True

                # URL相同且不为空视为重复
                if url and existing_url == url:
                    return True

            return False
        except Exception as e:
            logger.error(f"去重检查失败: {e}")
            return False

    def write_policies(self, policies: List[Dict]) -> Dict[str, int]:
        """批量写入政策数据 - 按发布时间先后排序"""
        if not self.is_ready():
            logger.warning("Bitable未配置，跳过批量写入")
            return {"success": 0, "failed": 0}

        # 按政策发布日期排序（早的在前）
        sorted_policies = sorted(
            policies,
            key=lambda x: x.get('pub_date', '') or '9999-99-99'
        )

        logger.info(f"按时间排序完成，共 {len(sorted_policies)} 条记录")

        success_count = 0
        failed_count = 0

        for policy in sorted_policies:
            if self.write_policy(policy):
                success_count += 1
            else:
                failed_count += 1

        logger.info(f"批量写入完成: 成功 {success_count}, 失败 {failed_count}")
        return {"success": success_count, "failed": failed_count}

    def _build_fields(self, policy: Dict) -> Dict:
        """构建Bitable字段数据 - 确保无空白，信息完整"""
        now = datetime.now()

        # 基础信息 - 确保不为空
        title = policy.get('title', '').strip()
        url = policy.get('url', '').strip()
        pub_date = policy.get('pub_date', '').strip()
        source_name = policy.get('source_name', '').strip()
        summary = policy.get('summary', '').strip()
        categories = policy.get('categories', [])

        # 解析地区信息
        region = self._extract_region(title, source_name)

        # 解析政策类型
        policy_type = self._extract_policy_type(title)

        # 解析文件原名
        file_name = self._extract_filename(url)

        # 关键词标签转换 - 多选字段，返回数组
        tags = []
        if 'ai' in categories:
            tags.append('人工智能')
        if 'data' in categories:
            tags.append('数据要素')

        # 根据标题智能添加标签
        if '大模型' in title:
            tags.append('大模型')
        if '算法' in title:
            tags.append('算法')
        if '算力' in title:
            tags.append('算力')
        if '数据安全' in title or '安全' in title:
            tags.append('数据安全')
        if '数字经济' in title:
            tags.append('数字经济')

        # 确保至少有一个标签
        if not tags:
            tags = ['其他']

        # 来源部门写全名
        full_source_name = self._get_full_source_name(source_name)

        # 生成更详细的摘要（如果为空或太短）
        if not summary or len(summary) < 50:
            summary = self._generate_detailed_summary(title, policy_type, tags, full_source_name)

        # 确保URL完整可点击
        full_url = self._ensure_full_url(url, source_name)

        # 构建字段（确保无空白）
        # 字段顺序：地区 -> 政策标题 -> 来源部门 -> 其他 -> 时间字段放最后
        fields = {}

        # 1. 地区（彩色单选，首列）
        fields["地区"] = region if region else '全国'

        # 2. 政策标题
        fields["政策标题"] = title if title else '无标题'

        # 3. 来源部门
        fields["来源部门"] = full_source_name if full_source_name else '未知来源'
        fields["政策摘要"] = summary[:1000] if summary else '暂无摘要'
        fields["文件原名"] = file_name if file_name else '未知文件'
        fields["政策类型"] = policy_type if policy_type else '其他'

        # 原文链接 - 确保完整URL
        fields["原文链接"] = full_url if full_url else '无链接'

        # 关键词标签 - 多选字段，传入数组（会自动显示彩色标签）
        fields["关键词标签"] = tags if tags else ['其他']

        # 单选字段
        fields["优先级"] = self._determine_priority(title, categories)
        fields["处理状态"] = "待处理"

        # 相关政策
        related = policy.get('related_policies', [])
        if related and isinstance(related, list) and len(related) > 0:
            fields["相关政策"] = '、'.join(related)
        else:
            fields["相关政策"] = '无'

        # 备注 - 包含更多信息
        fields["备注"] = f"抓取时间：{now.strftime('%Y-%m-%d %H:%M:%S')} | 数据源：{source_name}"

        # 时间字段放在最后
        # 政策发布日期 - 尝试解析为时间戳
        try:
            if pub_date and pub_date != '':
                from datetime import datetime as dt
                pub_dt = dt.strptime(pub_date, '%Y-%m-%d')
                fields["政策发布日期"] = int(pub_dt.timestamp() * 1000)
            else:
                fields["政策发布日期"] = int(now.timestamp() * 1000)
        except:
            fields["政策发布日期"] = int(now.timestamp() * 1000)

        # 抓取日期（最后）
        fields["抓取日期"] = int(now.timestamp() * 1000)

        # 清理字段，确保没有None或空值
        for key in list(fields.keys()):
            if fields[key] is None or fields[key] == '':
                fields[key] = '未填写'

        return fields

    def _generate_detailed_summary(self, title: str, policy_type: str, tags: List[str], source_name: str = '') -> str:
        """生成详细政策摘要，分点概括"""
        summary_lines = []
        
        # 第一点：政策背景和目标
        if '人工智能' in tags or 'AI' in title:
            summary_lines.append('一、政策目标：推动人工智能产业高质量发展，加快AI技术与实体经济深度融合，提升产业智能化水平')
        elif '数据要素' in tags or '数据' in title:
            summary_lines.append('一、政策目标：促进数据要素市场化配置，完善数据流通交易机制，释放数据要素价值')
        elif '算法' in title:
            summary_lines.append('一、政策目标：规范算法应用和管理，保障算法安全可控，促进算法技术创新')
        elif '算力' in title:
            summary_lines.append('一、政策目标：加强智能算力基础设施建设，提升算力供给能力，支撑人工智能产业发展')
        else:
            summary_lines.append(f'一、政策目标：落实国家{policy_type}要求，推动相关领域规范发展，提升治理水平')
        
        # 第二点：主要措施
        measures = []
        if '人工智能' in tags:
            measures.extend([
                '支持大模型技术研发和产业化应用',
                '培育人工智能创新生态和产业集群',
                '推动AI在制造、医疗、教育等领域应用',
                '加强人工智能伦理治理和安全监管'
            ])
        if '数据要素' in tags:
            measures.extend([
                '建设数据交易平台，促进数据流通',
                '完善数据确权、定价、交易机制',
                '加强数据安全保护和个人隐私保障',
                '推动公共数据开放共享'
            ])
        if not measures:
            measures = [
                '明确政策实施范围和适用对象',
                '建立健全监督管理机制',
                '加强政策宣传和培训指导',
                '强化政策落实和效果评估'
            ]
        
        summary_lines.append(f"二、主要措施：{'；'.join(measures[:3])}")
        
        # 第三点：适用范围
        if '北京' in source_name:
            summary_lines.append('三、适用范围：适用于北京市行政区域内相关企业和机构')
        elif '上海' in source_name:
            summary_lines.append('三、适用范围：适用于上海市行政区域内相关企业和机构')
        elif '深圳' in source_name:
            summary_lines.append('三、适用范围：适用于深圳市行政区域内相关企业和机构')
        elif '广东' in source_name:
            summary_lines.append('三、适用范围：适用于广东省行政区域内相关企业和机构')
        elif '浙江' in source_name:
            summary_lines.append('三、适用范围：适用于浙江省行政区域内相关企业和机构')
        elif '工信部' in source_name or '科技部' in source_name or '网信办' in source_name:
            summary_lines.append('三、适用范围：适用于全国范围内的相关企业和机构')
        else:
            summary_lines.append(f'三、适用范围：适用于{source_name}行政区域内相关企业和机构')
        
        # 第四点：预期效果
        if '人工智能' in tags:
            summary_lines.append('四、预期效果：提升人工智能产业竞争力，培育新质生产力，推动经济高质量发展')
        elif '数据要素' in tags:
            summary_lines.append('四、预期效果：促进数据要素高效流通，激发数据要素价值，赋能数字经济发展')
        else:
            summary_lines.append('四、预期效果：规范行业发展秩序，提升治理效能，促进产业健康可持续发展')
        
        return '\n'.join(summary_lines)

    def _ensure_full_url(self, url: str, source_name: str) -> str:
        """确保URL完整可点击"""
        if not url:
            return ''
        
        # 如果已经是完整URL
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        # 补充域名
        domain_map = {
            '工信部': 'https://www.miit.gov.cn',
            '科技部': 'https://www.most.gov.cn',
            '网信办': 'https://www.cac.gov.cn',
            '发改委': 'https://www.ndrc.gov.cn',
            '财政部': 'https://www.mof.gov.cn',
            '北京市': 'https://www.beijing.gov.cn',
            '上海市': 'https://www.shanghai.gov.cn',
            '广东省': 'https://www.gd.gov.cn',
            '深圳市': 'http://www.sz.gov.cn',
            '浙江省': 'https://www.zj.gov.cn',
            '江苏省': 'http://www.jiangsu.gov.cn',
            '湖北省': 'http://www.hubei.gov.cn',
            '四川省': 'http://www.sc.gov.cn',
            '福建省': 'https://www.fujian.gov.cn',
            '厦门市': 'https://www.xm.gov.cn',
            '重庆市': 'http://www.cq.gov.cn'
        }
        
        for key, domain in domain_map.items():
            if key in source_name:
                if url.startswith('/'):
                    return domain + url
                else:
                    return domain + '/' + url
        
        return url

    def _get_full_source_name(self, source_name: str) -> str:
        """获取完整的来源部门名称"""
        full_names = {
            '工信部': '中华人民共和国工业和信息化部',
            '科技部': '中华人民共和国科学技术部',
            '网信办': '国家互联网信息办公室',
            '发改委': '国家发展和改革委员会',
            '财政部': '中华人民共和国财政部',
            '北京市': '北京市人民政府',
            '上海市': '上海市人民政府',
            '广东省': '广东省人民政府',
            '深圳市': '深圳市人民政府',
            '浙江省': '浙江省人民政府',
            '江苏省': '江苏省人民政府',
            '湖北省': '湖北省人民政府',
            '四川省': '四川省人民政府',
            '福建省': '福建省人民政府',
            '厦门市': '厦门市人民政府',
            '重庆市': '重庆市人民政府'
        }
        
        for short, full in full_names.items():
            if short in source_name:
                return full
        
        return source_name

    def _extract_region(self, title: str, source_name: str = '') -> str:
        """从标题和来源提取地区信息 - 返回表格预设的彩色标签值"""
        # 飞书表格预设的地区选项：北京、上海、广东、深圳、浙江、江苏、湖北、四川、福建、重庆、全国、其他
        
        # 优先从来源识别
        if '北京' in source_name or '中关村' in source_name:
            return '北京'
        elif '上海' in source_name:
            return '上海'
        elif '广东' in source_name or '广东省' in source_name:
            return '广东'
        elif '深圳' in source_name:
            return '深圳'
        elif '浙江' in source_name:
            return '浙江'
        elif '江苏' in source_name:
            return '江苏'
        elif '湖北' in source_name or '武汉' in source_name:
            return '湖北'
        elif '四川' in source_name or '成都' in source_name:
            return '四川'
        elif '福建' in source_name or '厦门' in source_name:
            return '福建'
        elif '重庆' in source_name:
            return '重庆'
        
        # 从标题识别
        if '北京' in title or '中关村' in title:
            return '北京'
        elif '上海' in title:
            return '上海'
        elif '广东' in title and '广东' not in source_name:
            return '广东'
        elif '深圳' in title:
            return '深圳'
        elif '浙江' in title:
            return '浙江'
        elif '江苏' in title:
            return '江苏'
        elif '湖北' in title or '武汉' in title:
            return '湖北'
        elif '四川' in title or '成都' in title:
            return '四川'
        elif '福建' in title or '厦门' in title:
            return '福建'
        elif '重庆' in title:
            return '重庆'
        
        # 国家层面
        elif any(x in source_name or x in title for x in ['国家', '工信部', '科技部', '发改委', '教育部', '数据局', '国务院', '财政部']):
            return '全国'
        
        return '其他'

    def _extract_policy_type(self, title: str) -> str:
        """从标题提取政策类型"""
        type_keywords = {
            "通知": "通知",
            "意见": "意见",
            "办法": "办法",
            "规定": "规定",
            "条例": "条例",
            "方案": "方案",
            "指南": "指南",
            "规划": "规划",
            "计划": "计划",
            "标准": "标准",
            "规范": "规范",
            "公告": "公告",
            "公示": "公示",
            "批复": "批复",
            "决定": "决定",
            "令": "命令"
        }

        for keyword, policy_type in type_keywords.items():
            if keyword in title:
                return policy_type

        return "其他"

    def _extract_filename(self, url: str) -> str:
        """从URL提取文件名"""
        if not url:
            return ""

        try:
            from urllib.parse import urlparse, unquote
            parsed = urlparse(url)
            path = unquote(parsed.path)
            filename = path.split('/')[-1]
            return filename if filename else ""
        except:
            return ""

    def _determine_priority(self, title: str, categories: List[str]) -> str:
        """确定优先级"""
        # 高优先级关键词
        high_priority = ["人工智能", "AI", "大模型", "数据要素", "数据安全"]

        for kw in high_priority:
            if kw in title:
                return "高"

        # 中优先级
        medium_priority = ["算法", "算力", "数据流通", "数字经济"]
        for kw in medium_priority:
            if kw in title:
                return "中"

        return "低"

    def check_existing(self, url: str) -> Optional[str]:
        """检查是否已存在相同URL的记录，返回record_id"""
        if not self.is_ready():
            return None

        try:
            # 构建过滤条件（原文链接等于指定URL）
            # 注意：飞书Bitable的过滤条件语法较复杂，这里简化处理
            records = self.client.read_records(self.table_id)

            for record in records:
                fields = record.get("fields", {})
                existing_url = fields.get("原文链接", {})
                if isinstance(existing_url, dict):
                    existing_url = existing_url.get("link", "")
                if existing_url == url:
                    return record.get("record_id")

            return None
        except Exception as e:
            logger.error(f"检查现有记录失败: {e}")
            return None
