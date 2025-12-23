import os
import logging
from openai import OpenAI
from datetime import datetime
from typing import Optional, Dict, Any
from .database import get_biometric_data, get_trend_data
from .config import HealthConfig, get_default_config
import pandas as pd

logger = logging.getLogger(__name__)

class BiometricAnalyst:
    def __init__(self, config: Optional[HealthConfig] = None, api_key: Optional[str] = None, 
                 base_url: Optional[str] = None, model: Optional[str] = None):
        """初始化生物特征分析师
        
        优先级：命令行参数 > 环境变量 > 配置文件 > 默认值
        
        Args:
            config: HealthConfig配置实例，如果为None则使用默认配置
            api_key: DeepSeek API密钥（命令行参数，最高优先级）
            base_url: API基础URL（命令行参数，最高优先级）
            model: 使用的模型（命令行参数，最高优先级）
        """
        # 加载配置
        self.config = config or get_default_config()
        
        # 应用命令行参数（最高优先级）
        if api_key is not None:
            self.config.api_key = api_key
        if base_url is not None:
            self.config.base_url = base_url
        if model is not None:
            self.config.model = model
        
        # 设置实例变量以便访问
        self.model = self.config.model
        
        # 验证配置
        if not self.config.api_key:
            logger.warning("未设置DeepSeek API Key，部分功能可能受限")
        
        # 初始化OpenAI客户端
        if self.config.api_key:
            # 为代理支持创建自定义HTTP客户端（如果需要）
            proxy_dict = self.config.get_proxy_dict()
            if proxy_dict:
                # 导入httpx库用于代理支持
                try:
                    import httpx
                    # 设置代理到环境变量，让httpx自动使用
                    proxy_url = proxy_dict.get("http") or proxy_dict.get("https")
                    if proxy_url:
                        # 设置环境变量，这样httpx会自动使用
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
        
        current_profile = self.config.get_current_profile()
        profile_name = current_profile.name if current_profile else "默认配置"
        logger.info(f"初始化生物特征分析师（内务部部长模式），使用配置: {profile_name}")
        logger.info(f"模型: {self.model}")
        logger.info(f"代理设置: {'启用' if self.config.get_proxy_dict() else '禁用'}")

    def _circuit_breaker_check(self, hrv_0800: int) -> Optional[str]:
        """熔断机制检查：如果HRV过低，直接返回警报
        
        Args:
            hrv_0800: 上午8点的HRV值
        
        Returns:
            如果触发熔断则返回警报消息，否则返回None
        """
        if hrv_0800 < 40:
            alert_msg = "🔴 警告：系统处于崩溃边缘。立即停止开发，执行物理冷却。"
            logger.warning(f"熔断机制触发: HRV_0800={hrv_0800}ms")
            return alert_msg
        elif hrv_0800 < 50:
            warning_msg = "🟡 警告：HRV值偏低，建议降低当日量化开发强度。"
            logger.info(f"HRV预警: HRV_0800={hrv_0800}ms")
            return warning_msg
        
        return None

    def _prepare_analysis_context(self, today_data: Dict[str, Any], trend_data: Dict[str, Any]) -> str:
        """准备分析上下文数据
        
        Args:
            today_data: 当日数据
            trend_data: 趋势数据
        
        Returns:
            格式化后的上下文字符串
        """
        context_lines = []
        
        # 当日数据概览
        context_lines.append("【当日核心数据】")
        context_lines.append(f"日期: {today_data.get('date', 'N/A')}")
        context_lines.append(f"体重: {today_data.get('weight', 'N/A')}kg (目标: <93.0kg)")
        context_lines.append(f"总睡眠: {today_data.get('total_sleep_min', 'N/A')}分钟")
        context_lines.append(f"深度睡眠: {today_data.get('deep_sleep_min', 'N/A')}分钟 (占比: {today_data.get('deep_sleep_ratio', 0):.1%})")
        context_lines.append(f"HRV时序: {today_data.get('hrv_0000', 'N/A')} → {today_data.get('hrv_0400', 'N/A')} → {today_data.get('hrv_0800', 'N/A')} → {today_data.get('hrv_1200', 'N/A')}ms")
        context_lines.append(f"HRV变化: Δ={today_data.get('hrv_delta', 'N/A')}ms")
        context_lines.append(f"疲劳评分: {today_data.get('fatigue_score', 'N/A')}/10")
        context_lines.append(f"碳水限制执行: {'是' if today_data.get('carb_limit_exec') else '否'}")
        
        if today_data.get('tags'):
            context_lines.append(f"异常标记: {today_data.get('tags')}")
        
        # 趋势分析
        if trend_data['count'] > 0:
            context_lines.append("\n【7日趋势分析】")
            context_lines.append(f"数据覆盖: 最近{trend_data['count']}天")
            
            # 体重趋势
            if len(trend_data['weights']) >= 2:
                weight_change = trend_data['weights'][-1] - trend_data['weights'][0]
                weight_trend = "下降" if weight_change < 0 else "上升"
                context_lines.append(f"体重趋势: {weight_trend} {abs(weight_change):.1f}kg")
            
            # HRV趋势
            if len(trend_data['hrv_0800_values']) >= 2:
                hrv_change = trend_data['hrv_0800_values'][-1] - trend_data['hrv_0800_values'][0]
                hrv_trend = "改善" if hrv_change > 0 else "恶化"
                context_lines.append(f"HRV趋势: {hrv_trend} {abs(hrv_change):.1f}ms")
                
                # 识别模式
                if today_data.get('hrv_0400', 0) > today_data.get('hrv_0000', 0) + 50:
                    context_lines.append(f"夜间恢复信号: 凌晨4点HRV尖峰 ({today_data.get('hrv_0400', 'N/A')}ms)")
        
        # 关键指标检查
        context_lines.append("\n【关键指标状态】")
        
        # 深度睡眠占比检查
        deep_sleep_ratio = today_data.get('deep_sleep_ratio', 0)
        if deep_sleep_ratio >= 0.15:
            context_lines.append(f"✓ 深度睡眠占比达标: {deep_sleep_ratio:.1%} (>15%)")
        else:
            context_lines.append(f"✗ 深度睡眠占比不足: {deep_sleep_ratio:.1%} (<15%)")
        
        # 体重目标检查
        weight = today_data.get('weight', 0)
        if weight < 93.0:
            context_lines.append(f"✓ 体重目标达标: {weight}kg (<93.0kg)")
        else:
            context_lines.append(f"✗ 体重目标超标: {weight}kg (≥93.0kg)")
        
        # HRV恢复检查
        if today_data.get('hrv_0400', 0) > today_data.get('hrv_0000', 0) + 30:
            context_lines.append(f"✓ 夜间恢复迹象: 凌晨4点HRV显著提升")
        else:
            context_lines.append(f"✗ 夜间恢复不足: 凌晨4点HRV无明显提升")
        
        return "\n".join(context_lines)

    def _generate_system_prompt(self) -> str:
        """生成系统提示词"""
        return """你是内务部部长，负责管理MY-DOGE系统的生理健康监测。
你的任务是基于提供的生物特征数据，以军事化、严谨的口吻生成健康评估报告。

【核心职责】
1. 数据驱动决策：每项结论必须基于具体数据指标
2. 风险预警：及时发现并警告潜在健康风险
3. 行动建议：提供具体、可执行的改善建议
4. 趋势分析：识别生理状态的变化趋势

【报告结构要求】
1. 核心指标快报：总结关键指标状态
2. 生理系统诊断：分析各系统功能状态
3. 量化任务对冲建议：根据生理状态调整工作强度

【分析重点】
1. HRV波动模式：特别关注凌晨4点的异常高值（生理修复尖峰）
2. 深度睡眠占比：与HRV恢复的匹配度
3. 体重趋势：与疲劳状态的相关性
4. 疲劳评分与HRV的背离情况

请保持报告简洁、专业，使用军事化术语。"""

    def _generate_user_prompt(self, context: str) -> str:
        """生成用户提示词"""
        return f"""以下是操作员的生物特征数据：

{context}

请基于以上数据生成健康评估报告。报告需要包含：
1. 【核心指标快报】：总结当日关键指标状态
2. 【生理系统诊断】：分析自主神经系统、恢复状态、代谢状态
3. 【量化任务对冲建议】：根据HRV和疲劳状态，给出今日工作强度建议（例如：HRV低于50时降低开发强度）

请使用军事化、严谨的口吻，引用具体数据支持你的分析。"""

    def generate_daily_report(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """生成每日健康报告
        
        Args:
            target_date: 目标日期（YYYY-MM-DD），如果为None则使用最新数据
        
        Returns:
            包含报告内容和元数据的字典
        """
        logger.info(f"开始生成健康报告: {target_date or '最新数据'}")
        
        # 获取数据
        records = get_biometric_data(date=target_date, limit=1)
        if not records:
            logger.error(f"未找到目标日期的数据: {target_date}")
            return {
                'success': False,
                'error': f"未找到目标日期的数据: {target_date}",
                'report_type': 'error'
            }
        
        today_data = records[0]
        trend_data = get_trend_data(days=7)
        
        # 熔断机制检查
        hrv_0800 = today_data.get('hrv_0800', 0)
        circuit_breaker_msg = self._circuit_breaker_check(hrv_0800)
        
        if circuit_breaker_msg:
            logger.info("触发熔断机制，生成硬编码警报")
            return {
                'success': True,
                'date': today_data.get('date'),
                'report_type': 'circuit_breaker',
                'report_content': circuit_breaker_msg,
                'metadata': {
                    'hrv_0800': hrv_0800,
                    'trigger_reason': f'HRV_0800={hrv_0800}ms < 40ms'
                }
            }
        
        # 如果没有API密钥，生成基础报告
        if not self.client:
            logger.warning("未配置API密钥，生成基础报告")
            return self._generate_basic_report(today_data, trend_data)
        
        # 准备分析上下文
        context = self._prepare_analysis_context(today_data, trend_data)
        
        try:
            logger.info("调用DeepSeek API进行健康分析...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._generate_system_prompt()},
                    {"role": "user", "content": self._generate_user_prompt(context)}
                ],
                stream=False,
                temperature=0.3,  # 低温度以保证一致性
                max_tokens=1500
            )
            
            ai_report = response.choices[0].message.content
            logger.info("DeepSeek分析完成")
            
            return {
                'success': True,
                'date': today_data.get('date'),
                'report_type': 'ai_analysis',
                'report_content': ai_report,
                'metadata': {
                    'model': self.model,
                    'context_summary': {
                        'weight': today_data.get('weight'),
                        'total_sleep': today_data.get('total_sleep_min'),
                        'deep_sleep_ratio': today_data.get('deep_sleep_ratio'),
                        'hrv_0800': hrv_0800,
                        'fatigue_score': today_data.get('fatigue_score')
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            # API失败时回退到基础报告
            return self._generate_basic_report(today_data, trend_data)

    def _generate_basic_report(self, today_data: Dict[str, Any], trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成基础报告（当API不可用时）
        
        Args:
            today_data: 当日数据
            trend_data: 趋势数据
        
        Returns:
            基础报告字典
        """
        date_str = today_data.get('date', '未知日期')
        weight = today_data.get('weight', 0)
        hrv_0800 = today_data.get('hrv_0800', 0)
        fatigue = today_data.get('fatigue_score', 0)
        deep_sleep_ratio = today_data.get('deep_sleep_ratio', 0)
        
        # 生成基础报告
        report_lines = []
        report_lines.append(f"# MY-DOGE 健康监测基础报告")
        report_lines.append(f"**日期**: {date_str}")
        report_lines.append("")
        
        report_lines.append("## 【核心指标快报】")
        report_lines.append(f"- 体重: {weight}kg {'✓ 达标' if weight < 93.0 else '✗ 超标'}")
        report_lines.append(f"- HRV_0800: {hrv_0800}ms {'✓ 正常' if hrv_0800 >= 50 else '⚠️ 偏低'}")
        report_lines.append(f"- 疲劳评分: {fatigue}/10")
        report_lines.append(f"- 深度睡眠占比: {deep_sleep_ratio:.1%} {'✓ 达标' if deep_sleep_ratio >= 0.15 else '✗ 不足'}")
        
        report_lines.append("")
        report_lines.append("## 【生理系统诊断】")
        
        # 自主神经系统评估
        if hrv_0800 >= 60:
            report_lines.append("- 自主神经系统: 恢复良好，应激能力正常")
        elif hrv_0800 >= 40:
            report_lines.append("- 自主神经系统: 轻度疲劳，恢复能力下降")
        else:
            report_lines.append("- 自主神经系统: 严重疲劳，需要立即休息")
        
        # 恢复状态评估
        if fatigue <= 3:
            report_lines.append("- 恢复状态: 充分恢复，可承担高强度任务")
        elif fatigue <= 6:
            report_lines.append("- 恢复状态: 部分恢复，建议适度工作")
        else:
            report_lines.append("- 恢复状态: 恢复不足，需要降低工作强度")
        
        # 代谢状态评估
        if weight < 93.0:
            report_lines.append("- 代谢状态: 体重控制良好，能量平衡正常")
        else:
            report_lines.append("- 代谢状态: 体重超标，需加强能量管理")
        
        report_lines.append("")
        report_lines.append("## 【量化任务对冲建议】")
        
        # 基于HRV的工作强度建议
        if hrv_0800 >= 60:
            report_lines.append("- 工作强度: 可维持正常开发强度")
            report_lines.append("- 建议: 保持当前节奏，注意定时休息")
        elif hrv_0800 >= 50:
            report_lines.append("- 工作强度: 建议降低20%开发强度")
            report_lines.append("- 建议: 增加休息间隔，避免长时间连续工作")
        elif hrv_0800 >= 40:
            report_lines.append("- 工作强度: 建议降低50%开发强度")
            report_lines.append("- 建议: 优先处理关键任务，避免复杂逻辑开发")
        else:
            report_lines.append("- 工作强度: 建议暂停开发工作")
            report_lines.append("- 建议: 立即休息，进行物理恢复活动")
        
        report_content = "\n".join(report_lines)
        
        return {
            'success': True,
            'date': date_str,
            'report_type': 'basic_analysis',
            'report_content': report_content,
            'metadata': {
                'note': '基于规则的基础分析（API不可用）',
                'critical_metrics': {
                    'weight': weight,
                    'hrv_0800': hrv_0800,
                    'fatigue_score': fatigue,
                    'deep_sleep_ratio': deep_sleep_ratio
                }
            }
        }

    def save_report_to_file(self, report_data: Dict[str, Any], output_dir: str = "reports") -> str:
        """保存报告到文件
        
        Args:
            report_data: generate_daily_report返回的报告数据
            output_dir: 输出目录
        
        Returns:
            文件路径
        """
        if not report_data.get('success'):
            logger.error("报告数据无效，无法保存")
            return ""
        
        os.makedirs(output_dir, exist_ok=True)
        
        date_str = report_data.get('date', datetime.now().strftime("%Y-%m-%d"))
        report_type = report_data.get('report_type', 'unknown')
        
        # 生成文件名
        if report_type == 'circuit_breaker':
            filename = f"health_alert_{date_str}.md"
        else:
            filename = f"health_report_{date_str}.md"
        
        filepath = os.path.join(output_dir, filename)
        
        # 添加报告头信息
        full_report = f"""# MY-DOGE Biometric Analysis System - 健康监测报告

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**报告日期**: {date_str}
**报告类型**: {report_type}

"""
        
        full_report += report_data['report_content']
        
        # 添加元数据（作为注释）
        if 'metadata' in report_data:
            full_report += f"\n\n<!-- 报告元数据: {report_data['metadata']} -->"
        
        # 保存文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_report)
            
            logger.info(f"报告已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
            return ""

def main():
    """命令行入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MY-DOGE 生物特征分析引擎')
    parser.add_argument('--date', type=str, help='分析日期 (YYYY-MM-DD)，默认为最新数据')
    parser.add_argument('--output-dir', type=str, default='reports', help='报告输出目录')
    parser.add_argument('--api-key', type=str, help='DeepSeek API密钥（可选）')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建分析师实例
    analyst = BiometricAnalyst(api_key=args.api_key)
    
    # 生成报告
    report_data = analyst.generate_daily_report(target_date=args.date)
    
    if report_data['success']:
        # 保存报告
        filepath = analyst.save_report_to_file(report_data, args.output_dir)
        
        if filepath:
            print(f"✅ 健康报告生成成功: {filepath}")
            
            # 显示报告摘要
            print("\n=== 报告摘要 ===")
            print(f"日期: {report_data['date']}")
            print(f"类型: {report_data['report_type']}")
            
            if report_data['report_type'] == 'circuit_breaker':
                print(f"警报: {report_data['report_content']}")
            else:
                # 显示前几行
                lines = report_data['report_content'].split('\n')[:10]
                for line in lines:
                    print(line)
        else:
            print("❌ 报告保存失败")
            return 1
    else:
        print(f"❌ 报告生成失败: {report_data.get('error', '未知错误')}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
