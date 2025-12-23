import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from openai import OpenAI
from ..health.config import HealthConfig, get_default_config

logger = logging.getLogger(__name__)

class BioStrategist:
    """生物特征策略分析师（内务部部长兼首席军医）"""
    
    def __init__(self, config: Optional[HealthConfig] = None):
        """初始化策略分析师
        
        Args:
            config: 配置实例，如果为None则使用默认配置
        """
        self.config = config or get_default_config()
        
        # 初始化OpenAI客户端
        if self.config.api_key:
            proxy_dict = self.config.get_proxy_dict()
            if proxy_dict:
                try:
                    import httpx
                    proxy_url = proxy_dict.get("http") or proxy_dict.get("https")
                    if proxy_url:
                        os.environ["HTTP_PROXY"] = proxy_url
                        os.environ["HTTPS_PROXY"] = proxy_url
                    
                    http_client = httpx.Client(timeout=30.0)
                    self.client = OpenAI(
                        api_key=self.config.api_key,
                        base_url=self.config.base_url,
                        http_client=http_client
                    )
                except ImportError:
                    logger.warning("未安装httpx库，代理支持需要安装: pip install httpx")
                    self.client = OpenAI(
                        api_key=self.config.api_key,
                        base_url=self.config.base_url
                    )
            else:
                self.client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url
                )
        else:
            self.client = None
            logger.warning("未设置DeepSeek API Key，无法生成AI报告")
        
        logger.info(f"初始化生物特征策略分析师（内务部部长兼首席军医）")
        logger.info(f"模型: {self.config.model}")
        logger.info(f"API端点: {self.config.base_url}")
    
    def _apply_rules_of_engagement(self, current_data: Dict[str, Any]) -> List[str]:
        """应用自动对冲规则（Rules of Engagement）
        
        Args:
            current_data: 当日数据
            
        Returns:
            list: 规则触发建议列表
        """
        recommendations = []
        
        # 规则1: 禁令触发
        deep_sleep_min = current_data.get('deep_sleep_min', 0)
        hrv_0800 = current_data.get('hrv_0800', 0)
        if deep_sleep_min < 45 and hrv_0800 < 50:
            recommendations.append("🚨 禁令触发：今日脑力任务难度下调 30%")
            logger.info(f"规则触发：深度睡眠{deep_sleep_min}min < 45min 且 HRV 8点{hrv_0800}ms < 50ms")
        
        # 规则2: 体重对冲
        weight = current_data.get('weight', 0)
        if weight > 93.0:
            recommendations.append("⚡ 体重对冲：启动内务部紧急预案：冷水洗脸 + 哺乳动物潜水反射")
            logger.info(f"规则触发：体重{weight}kg > 93.0kg")
        
        # 规则3: 异常处理
        hrv_0400 = current_data.get('hrv_0400', 0)
        if hrv_0400 > 120:
            recommendations.append("🔄 系统重置日：检测到HRV_0400异常高值，建议减少高压演练")
            logger.info(f"规则触发：HRV 4点{hrv_0400}ms > 120ms")
        
        return recommendations
    
    def _analyze_hrv_pattern(self, current_data: Dict[str, Any]) -> str:
        """分析HRV日内曲线形态
        
        Args:
            current_data: 当日数据
            
        Returns:
            str: 曲线形态描述
        """
        hrv_0000 = current_data.get('hrv_0000', 0)
        hrv_0400 = current_data.get('hrv_0400', 0)
        hrv_0800 = current_data.get('hrv_0800', 0)
        
        # 计算变化
        delta_0000_0400 = hrv_0400 - hrv_0000
        delta_0400_0800 = hrv_0800 - hrv_0400
        
        # 判断曲线形态
        if delta_0000_0400 > 20 and delta_0400_0800 < -10:
            return "V型反转：夜间修复良好，但早晨压力反弹"
        elif delta_0000_0400 > 10 and delta_0400_0800 > 10:
            return "持续上升：全天恢复态势良好"
        elif delta_0000_0400 < 0 and delta_0400_0800 < 0:
            return "持续低迷：全天压力积累"
        elif delta_0000_0400 > 30:
            return "夜间修复尖峰：系统在凌晨4点进行深度修复"
        else:
            return "平稳波动：无明显修复或压力信号"
    
    def _analyze_daily_trend(self, current_data: Dict[str, Any], history_data: List[Dict[str, Any]]) -> str:
        """分析隔日趋势
        
        Args:
            current_data: 当日数据
            history_data: 历史数据（包含昨日）
            
        Returns:
            str: 趋势分析结果
        """
        if len(history_data) < 2:
            return "数据不足，无法进行隔日对比"
        
        # 获取昨日数据（历史数据按日期倒序排列，history_data[0]是当前数据）
        if len(history_data) > 1:
            yesterday_data = history_data[1]
        else:
            return "昨日数据缺失"
        
        # 计算关键指标变化
        current_weight = current_data.get('weight', 0)
        yesterday_weight = yesterday_data.get('weight', 0)
        weight_change = current_weight - yesterday_weight
        
        current_hrv_0800 = current_data.get('hrv_0800', 0)
        yesterday_hrv_0800 = yesterday_data.get('hrv_0800', 0)
        hrv_change = current_hrv_0800 - yesterday_hrv_0800
        
        current_deep_ratio = current_data.get('deep_sleep_ratio', 0)
        yesterday_deep_ratio = yesterday_data.get('deep_sleep_ratio', 0)
        deep_ratio_change = current_deep_ratio - yesterday_deep_ratio
        
        # 判断总体趋势
        positive_signals = 0
        negative_signals = 0
        
        if weight_change < 0:  # 体重下降
            positive_signals += 1
        elif weight_change > 0.5:  # 体重显著上升
            negative_signals += 1
        
        if hrv_change > 5:  # HRV改善
            positive_signals += 1
        elif hrv_change < -5:  # HRV恶化
            negative_signals += 1
        
        if deep_ratio_change > 0.05:  # 深度睡眠占比改善
            positive_signals += 1
        elif deep_ratio_change < -0.05:  # 深度睡眠占比恶化
            negative_signals += 1
        
        if positive_signals > negative_signals:
            return f"充电状态：身体正在恢复（正面信号:{positive_signals}/负面信号:{negative_signals}）"
        elif negative_signals > positive_signals:
            return f"漏电状态：身体持续消耗（负面信号:{negative_signals}/正面信号:{positive_signals}）"
        else:
            return f"平衡状态：身体维持现状（正面/负面信号各{positive_signals}）"
    
    def _prepare_prompt_data(self, current_data: Dict[str, Any], history_data: List[Dict[str, Any]]) -> str:
        """准备发送给DeepSeek的Prompt数据
        
        Args:
            current_data: 当日数据
            history_data: 历史数据
            
        Returns:
            str: 格式化的Prompt文本
        """
        # 基本信息
        prompt = f"""# MY-DOGE 政府 - 内务部部长兼首席军医健康战备报告

## 角色定义
你是MY-DOGE政府的内务部部长兼首席军医，负责元首（用户）的个人健康管理。

## KPI 阈值上下文
1. 深度睡眠占比 (η_deep) 及格线：15%
2. 体重 (W) 警戒线：93.0 kg
3. HRV (0点/8点) 基准线：> 60ms

## 自动对冲规则 (Rules of Engagement)
以下是基于今日数据的规则触发状态：
"""
        
        # 应用对冲规则
        rules = self._apply_rules_of_engagement(current_data)
        if rules:
            for rule in rules:
                prompt += f"- {rule}\n"
        else:
            prompt += "- 无规则触发\n"
        
        # 今日核心数据
        prompt += f"""
## 今日核心数据（{current_data.get('date', '未知日期')}）

### 睡眠指标
- 总睡眠时长：{current_data.get('total_sleep_min', 0)} 分钟（{current_data.get('total_sleep_min', 0)/60:.1f}小时）
- 深度睡眠时长：{current_data.get('deep_sleep_min', 0)} 分钟
- 深度睡眠占比：{current_data.get('deep_sleep_ratio', 0):.1%}（目标：>15%）

### 神经指标（HRV）
- 0点 HRV（基准负载）：{current_data.get('hrv_0000', 0)} ms
- 4点 HRV（巅峰修复）：{current_data.get('hrv_0400', 0)} ms
- 8点 HRV（苏醒状态）：{current_data.get('hrv_0800', 0)} ms
- 12点 HRV（日间恢复）：{current_data.get('hrv_1200', 0)} ms

### 代谢指标
- 体重：{current_data.get('weight', 0)} kg（目标：<93.0kg）
- 主观疲劳度：{current_data.get('fatigue_score', 0)}/10
- 睡前4小时禁碳水执行：{'是' if current_data.get('carb_limit_check') else '否'}
"""
        
        # 分析维度
        prompt += f"""
## 分析维度要求

### 1. 日内复盘
请分析HRV从0点 -> 4点 -> 8点的曲线形态：
- 当前曲线形态：{self._analyze_hrv_pattern(current_data)}
- 请详细解释此形态的生理意义

### 2. 隔日趋势
请对比昨日数据，判断身体是在"充电"还是"漏电"：
- 趋势判断：{self._analyze_daily_trend(current_data, history_data)}
- 请提供具体的数据对比分析

### 3. 系统整体评估
请基于以下数据进行全面评估：
1. 深度睡眠占比是否达标？对恢复质量的影响
2. 体重是否超过警戒线？对代谢压力的影响
3. HRV基准线是否达标？对神经弹性的影响
4. 疲劳度与HRV的匹配度？是否存在主观与客观指标的背离

## 报告格式要求
请以"内务部部长"的口吻生成《健康战备报告》，并严格遵循以下格式：

**报告标题**: 使用一句话总结核心战备状态（作为报告的标题）

报告内容包含：
1. **核心战备状态**（红/黄/绿三级警报）
2. **各系统诊断**（睡眠系统、神经系统、代谢系统）
3. **战术建议**（具体、可执行的改善措施）
4. **量化任务对冲**（根据生理状态调整今日工作强度）

请保持报告专业、简洁，使用军事化术语，所有结论必须基于上述数据。
"""
        
        # 添加历史数据摘要（如果存在）
        if len(history_data) > 1:
            prompt += "\n## 历史数据摘要（最近7天）\n"
            prompt += "| 日期 | 体重(kg) | HRV_0800(ms) | 深睡占比 |\n"
            prompt += "|------|----------|--------------|----------|\n"
            
            for i, record in enumerate(history_data[:7]):  # 最多显示7天
                if i >= 7:
                    break
                date_str = record.get('date', '未知')
                weight = record.get('weight', 0)
                hrv_0800 = record.get('hrv_0800', 0)
                deep_ratio = record.get('deep_sleep_ratio', 0)
                prompt += f"| {date_str} | {weight} | {hrv_0800} | {deep_ratio:.1%} |\n"
        
        return prompt
    
    def _call_deepseek_api(self, prompt: str) -> Optional[str]:
        """调用DeepSeek API生成报告
        
        Args:
            prompt: 完整的提示词
            
        Returns:
            str: AI生成的报告内容，失败时返回None
        """
        if not self.client:
            logger.error("OpenAI客户端未初始化，无法调用API")
            return None
        
        try:
            logger.info("正在调用DeepSeek API生成健康战备报告...")
            
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是MY-DOGE政府的内务部部长兼首席军医，负责元首的个人健康管理。请基于提供的生物特征数据，生成专业、严谨的健康战备报告，使用军事化术语。\n\n报告格式要求：\n1. 报告标题格式必须为'YYYY-MM-DD_一句话总结核心战备状态'，例如'2025-12-22_生理战线全面承压：睡眠、代谢、神经三方警报'（注意：不要使用《》书名号，YYYY-MM-DD必须使用数据中提供的日期，不要使用当前日期）\n2. 报告内容必须精简，直接进入主题，不要包含以下内容：\n   - 不要写'致：元首阁下'、'发件人：内务部部长兼首席军医'、'事由：健康战备状态评估报告'等信函格式\n   - 不要写'内务部部长兼首席军医 签署'、'备战宗旨：数据驱动，精准干预，保障元首作为最高指挥官的持久战力。'等签署和宗旨表述\n3. 报告结构：\n   - 核心战备状态（红/黄/绿三级警报）\n   - 各系统诊断（睡眠系统、神经系统、代谢系统）\n   - 战术建议（具体、可执行的改善措施）\n   - 量化任务对冲（根据生理状态调整今日工作强度）\n4. 保持报告专业、简洁，使用军事化术语，所有结论必须基于数据。\n5. 重要：报告标题中的日期必须与数据中的日期完全一致，不要使用当前日期。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream=False,
                temperature=0.3,  # 较低温度保证一致性
                max_tokens=2000
            )
            
            ai_report = response.choices[0].message.content
            logger.info("DeepSeek API调用成功")
            return ai_report
            
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            return None
    
    def _generate_fallback_report(self, current_data: Dict[str, Any], history_data: List[Dict[str, Any]]) -> str:
        """生成备用报告（当API不可用时）
        
        Args:
            current_data: 当日数据
            history_data: 历史数据
            
        Returns:
            str: 备用报告内容
        """
        date_str = current_data.get('date', datetime.now().date().isoformat())
        
        report = f"""# MY-DOGE 健康战备报告（本地生成）
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**报告日期**: {date_str}
**报告类型**: 本地规则分析（API不可用）

## 🔴 核心战备状态

### 关键指标评估
"""
        
        # KPI评估
        weight = current_data.get('weight', 0)
        deep_ratio = current_data.get('deep_sleep_ratio', 0)
        hrv_0800 = current_data.get('hrv_0800', 0)
        
        if weight <= 93.0 and deep_ratio >= 0.15 and hrv_0800 >= 60:
            report += "- 战备状态: 🟢 绿色（所有指标达标）\n"
        elif weight > 93.0 or deep_ratio < 0.15 or hrv_0800 < 50:
            report += "- 战备状态: 🔴 红色（关键指标超标）\n"
        else:
            report += "- 战备状态: 🟡 黄色（部分指标需关注）\n"
        
        # 各系统诊断
        report += f"""
## 📊 各系统诊断

### 睡眠系统
- 深度睡眠占比: {deep_ratio:.1%} {'✅ 达标' if deep_ratio >= 0.15 else '❌ 不足'}
- 总睡眠时长: {current_data.get('total_sleep_min', 0)}分钟
- 修复质量: {'良好' if deep_ratio >= 0.15 else '需改善'}

### 神经系统
- HRV基准线（8点）: {hrv_0800}ms {'✅ 正常' if hrv_0800 >= 60 else '⚠️ 偏低'}
- HRV曲线形态: {self._analyze_hrv_pattern(current_data)}
- 神经弹性: {'充足' if hrv_0800 >= 60 else '下降'}

### 代谢系统
- 体重: {weight}kg {'✅ 达标' if weight <= 93.0 else '❌ 超标'}
- 疲劳度: {current_data.get('fatigue_score', 0)}/10
- 碳水管理: {'执行良好' if current_data.get('carb_limit_check') else '需加强'}
"""
        
        # 自动对冲规则
        rules = self._apply_rules_of_engagement(current_data)
        if rules:
            report += "\n## ⚡ 自动对冲规则触发\n"
            for rule in rules:
                report += f"- {rule}\n"
        
        # 趋势分析
        trend = self._analyze_daily_trend(current_data, history_data)
        report += f"\n## 📈 隔日趋势分析\n"
        report += f"- 身体状态: {trend}\n"
        
        # 战术建议
        report += """
## 🎯 战术建议

### 立即执行
1. 根据对冲规则调整今日工作强度
2. 确保饮水充足（目标: 2.5L/天）
3. 安排午间小憩（如HRV偏低）

### 中期改善
1. 优化睡眠环境（温度18-20°C，完全黑暗）
2. 调整晚餐时间（睡前3小时完成进食）
3. 增加日间光照（上午30分钟户外）

### 量化任务对冲
"""
        
        # 工作强度建议
        if hrv_0800 < 50:
            report += "- 今日脑力任务强度: 下调30-50%\n"
            report += "- 避免复杂决策任务\n"
            report += "- 增加休息间隔（每45分钟休息5分钟）\n"
        elif hrv_0800 < 60:
            report += "- 今日脑力任务强度: 维持正常，但增加监控\n"
            report += "- 避免长时间连续工作\n"
            report += "- 安排轻度有氧活动（如散步）\n"
        else:
            report += "- 今日脑力任务强度: 可正常执行\n"
            report += "- 保持当前节奏，注意劳逸结合\n"
        
        report += f"\n---\n*报告生成方式: 本地规则引擎 | 下次AI分析需配置API密钥*"
        
        return report
    
    def _fix_title_date(self, title: str, correct_date: str) -> str:
        """修正标题中的日期，确保与数据日期一致
        
        Args:
            title: 原始标题
            correct_date: 正确的日期 (YYYY-MM-DD)
            
        Returns:
            str: 修正后的标题
        """
        if not title or not correct_date:
            return title
        
        # 尝试匹配标题中的日期格式 YYYY-MM-DD
        import re
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        matches = re.findall(date_pattern, title)
        
        if matches:
            # 替换第一个找到的日期为正确日期
            for match in matches:
                title = title.replace(match, correct_date)
                break
        else:
            # 如果标题中没有日期，在开头添加正确日期
            if not title.startswith(correct_date):
                title = f"{correct_date}_{title}"
        
        return title
    
    def _save_report_to_file(self, report_content: str, date_str: str, report_type: str) -> Optional[str]:
        """保存报告到 reports 文件夹
        
        Args:
            report_content: 报告内容
            date_str: 报告日期字符串
            report_type: 报告类型 ('ai_analysis' 或 'local_analysis')
            
        Returns:
            str: 保存的文件路径，失败时返回 None
        """
        try:
            # 确保 reports 目录存在
            import os
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            # 生成文件名：report_by_[model]_[date]_[time].md
            import re
            model_name = "unknown"
            if self.config and self.config.model:
                model_name = re.sub(r'[^\w\-]', '_', self.config.model)
            
            timestamp = datetime.now().strftime('%H-%M-%S')
            filename = f"report_by_{model_name}_{date_str}_{timestamp}.md"
            filepath = os.path.join(reports_dir, filename)
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"报告已保存到文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存报告到文件失败: {e}")
            return None
    
    def generate_health_report(self, current_data: Dict[str, Any], history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成健康战备报告
        
        Args:
            current_data: 当日数据字典
            history_data: 历史数据列表（按日期倒序排列）
            
        Returns:
            dict: 包含报告内容和元数据的字典
        """
        logger.info(f"开始生成健康战备报告，日期: {current_data.get('date', '未知')}")
        
        # 验证数据完整性
        required_fields = ['date', 'total_sleep_min', 'deep_sleep_min', 'weight', 'hrv_0000', 'hrv_0400', 'hrv_0800']
        for field in required_fields:
            if field not in current_data:
                logger.error(f"缺少必要字段: {field}")
                return {
                    'success': False,
                    'error': f'缺少必要字段: {field}',
                    'date': current_data.get('date', '未知')
                }
        
        # 准备Prompt数据
        prompt = self._prepare_prompt_data(current_data, history_data)
        
        # 尝试调用API生成报告
        ai_report = None
        if self.client:
            ai_report = self._call_deepseek_api(prompt)
        
        # 如果API调用成功，使用AI报告；否则使用备用报告
        if ai_report:
            report_type = 'ai_analysis'
            report_content = ai_report
            logger.info("使用AI生成的报告")
        else:
            report_type = 'local_analysis'
            report_content = self._generate_fallback_report(current_data, history_data)
            logger.info("使用本地生成的备用报告")
        
        # 提取规则触发状态
        rules_triggered = self._apply_rules_of_engagement(current_data)
        
        # 从报告中提取标题（一句话总结）
        report_title = "健康战备报告"
        lines = report_content.strip().split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#') and len(line.strip()) > 10:
                # 找到第一个非空且不是标题标记的行作为标题
                report_title = line.strip()
                # 清理标题，移除可能的前后符号
                report_title = report_title.replace('**', '').strip()
                # 移除《》书名号
                report_title = report_title.replace('《', '').replace('》', '')
                break
        
        # 获取日期用于修正标题
        title_date_str = current_data.get('date', datetime.now().date().isoformat())
        if not title_date_str:
            title_date_str = datetime.now().date().isoformat()
        
        # 修正标题中的日期：确保标题中的日期与数据日期一致
        report_title = self._fix_title_date(report_title, title_date_str)
        
        # 自动保存报告到文件（使用相同的日期）
        saved_filepath = self._save_report_to_file(report_content, title_date_str, report_type)
        
        # 返回报告数据
        result = {
            'success': True,
            'date': title_date_str,
            'report_type': report_type,
            'report_content': report_content,
            'report_title': report_title,  # 新增：一句话总结标题（不包含《》）
            'saved_filepath': saved_filepath,  # 新增：保存的文件路径
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'rules_triggered': rules_triggered,
                'hrv_pattern': self._analyze_hrv_pattern(current_data),
                'daily_trend': self._analyze_daily_trend(current_data, history_data),
                'key_metrics': {
                    'weight': current_data.get('weight'),
                    'deep_sleep_ratio': current_data.get('deep_sleep_ratio'),
                    'hrv_0800': current_data.get('hrv_0800'),
                    'fatigue_score': current_data.get('fatigue_score')
                }
            }
        }
        
        return result


# 便捷函数
def get_default_strategist() -> BioStrategist:
    """获取默认策略分析师实例"""
    return BioStrategist()


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试数据
    test_current = {
        'date': '2025-12-23',
        'total_sleep_min': 480,
        'deep_sleep_min': 72,
        'deep_sleep_ratio': 0.15,
        'hrv_0000': 65,
        'hrv_0400': 85,
        'hrv_0800': 70,
        'hrv_1200': 75,
        'weight': 92.5,
        'fatigue_score': 3,
        'carb_limit_check': True
    }
    
    test_history = [
        test_current,
        {
            'date': '2025-12-22',
            'total_sleep_min': 450,
            'deep_sleep_min': 60,
            'deep_sleep_ratio': 0.133,
            'hrv_0000': 60,
            'hrv_0400': 80,
            'hrv_0800': 65,
            'hrv_1200': 70,
            'weight': 92.8,
            'fatigue_score': 4,
            'carb_limit_check': False
        }
    ]
    
    # 创建策略分析师
    strategist = BioStrategist()
    
    # 生成报告
    result = strategist.generate_health_report(test_current, test_history)
    
    if result['success']:
        print(f"报告生成成功，类型: {result['report_type']}")
        print(f"日期: {result['date']}")
        print("\n=== 报告内容（前500字符）===")
        print(result['report_content'][:500] + "...")
        
        # 显示触发的规则
        if result['metadata']['rules_triggered']:
            print("\n=== 触发的规则 ===")
            for rule in result['metadata']['rules_triggered']:
                print(f"- {rule}")
    else:
        print(f"报告生成失败: {result.get('error')}")
