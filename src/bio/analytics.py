import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def calculate_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """计算干预措施与生物指标的相关性
    
    解析 'interventions' 文本列，将其转换为布尔列。
    分组比较有干预措施和无干预措施时的平均 hrv_0800 和 deep_sleep_ratio。
    
    Args:
        df: 包含历史数据的pandas DataFrame，必须包含以下列：
            - interventions: 干预措施文本（逗号分隔）
            - hrv_0800: 8点 HRV 值
            - deep_sleep_ratio: 深度睡眠占比
            - date: 日期（datetime类型）
    
    Returns:
        dict: 包含相关性分析结果的字典，结构如下：
            {
                'impact_scores': {
                    '冷水洗脸': {'hrv_impact': 5.2, 'sleep_impact': 0.03, 'samples': 10},
                    '镁补充': {'hrv_impact': 3.8, 'sleep_impact': 0.05, 'samples': 8},
                    ...
                },
                'baseline': {
                    'hrv_0800_mean': 65.0,
                    'deep_sleep_ratio_mean': 0.15,
                    'samples': 20
                },
                'summary': "镁补充增加深睡占比+5%，冷水洗脸提升HRV+5.2ms"
            }
    """
    if df.empty:
        logger.warning("DataFrame为空，无法计算相关性")
        return {
            'impact_scores': {},
            'baseline': {'hrv_0800_mean': 0, 'deep_sleep_ratio_mean': 0, 'samples': 0},
            'summary': '无数据可用'
        }
    
    # 确保必要的列存在
    required_columns = ['interventions', 'hrv_0800', 'deep_sleep_ratio']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"缺少必要列: {missing_columns}")
        return {
            'impact_scores': {},
            'baseline': {'hrv_0800_mean': 0, 'deep_sleep_ratio_mean': 0, 'samples': 0},
            'summary': f'数据缺失列: {missing_columns}'
        }
    
    # 复制DataFrame以避免修改原始数据
    df_analysis = df.copy()
    
    # 确保数值列类型正确
    df_analysis['hrv_0800'] = pd.to_numeric(df_analysis['hrv_0800'], errors='coerce')
    df_analysis['deep_sleep_ratio'] = pd.to_numeric(df_analysis['deep_sleep_ratio'], errors='coerce')
    
    # 移除缺失值
    df_analysis = df_analysis.dropna(subset=['hrv_0800', 'deep_sleep_ratio'])
    
    if df_analysis.empty:
        logger.warning("清洗后数据为空，无法计算相关性")
        return {
            'impact_scores': {},
            'baseline': {'hrv_0800_mean': 0, 'deep_sleep_ratio_mean': 0, 'samples': 0},
            'summary': '清洗后无有效数据'
        }
    
    # 解析干预措施文本，转换为布尔列
    # 首先获取所有唯一的干预措施
    all_interventions = set()
    for interventions_str in df_analysis['interventions'].fillna(''):
        if isinstance(interventions_str, str) and interventions_str.strip():
            interventions = [i.strip() for i in interventions_str.split(',') if i.strip()]
            all_interventions.update(interventions)
    
    # 为每个干预措施创建布尔列
    intervention_columns = {}
    for intervention in all_interventions:
        if intervention:  # 确保非空
            col_name = f'intervention_{intervention}'
            # 创建布尔列：如果干预措施字符串包含该干预措施则为True
            df_analysis[col_name] = df_analysis['interventions'].apply(
                lambda x: intervention in str(x) if pd.notnull(x) else False
            )
            intervention_columns[intervention] = col_name
    
    # 计算基线（无任何干预措施的数据）
    # 首先找出没有任何干预措施的行
    if intervention_columns:
        no_intervention_mask = df_analysis[[col for col in intervention_columns.values()]].sum(axis=1) == 0
    else:
        # 如果没有定义干预措施，则所有行都视为无干预
        no_intervention_mask = pd.Series(True, index=df_analysis.index)
    
    baseline_data = df_analysis[no_intervention_mask]
    
    if len(baseline_data) > 0:
        baseline_hrv = baseline_data['hrv_0800'].mean()
        baseline_sleep = baseline_data['deep_sleep_ratio'].mean()
        baseline_samples = len(baseline_data)
    else:
        # 如果没有基线数据，使用全体数据的平均值
        baseline_hrv = df_analysis['hrv_0800'].mean()
        baseline_sleep = df_analysis['deep_sleep_ratio'].mean()
        baseline_samples = len(df_analysis)
        logger.warning("无基线数据（无干预措施记录），使用全体数据平均值作为基线")
    
    # 计算每个干预措施的影响
    impact_scores = {}
    
    for intervention, col_name in intervention_columns.items():
        # 有该干预措施的数据
        with_intervention = df_analysis[df_analysis[col_name]]
        
        if len(with_intervention) >= 3:  # 至少需要3个样本才有统计意义
            # 计算平均值
            hrv_mean = with_intervention['hrv_0800'].mean()
            sleep_mean = with_intervention['deep_sleep_ratio'].mean()
            
            # 计算相对于基线的变化
            hrv_impact = hrv_mean - baseline_hrv
            sleep_impact = sleep_mean - baseline_sleep
            
            # 计算百分比变化
            hrv_pct = (hrv_impact / baseline_hrv * 100) if baseline_hrv != 0 else 0
            sleep_pct = (sleep_impact / baseline_sleep * 100) if baseline_sleep != 0 else 0
            
            impact_scores[intervention] = {
                'hrv_impact': round(hrv_impact, 1),
                'sleep_impact': round(sleep_impact, 3),
                'hrv_pct': round(hrv_pct, 1),
                'sleep_pct': round(sleep_pct, 1),
                'samples': len(with_intervention),
                'hrv_mean': round(hrv_mean, 1),
                'sleep_mean': round(sleep_mean, 3)
            }
        else:
            logger.debug(f"干预措施 '{intervention}' 样本不足 ({len(with_intervention)}个)，跳过计算")
    
    # 生成总结文本
    summary_parts = []
    
    # 按影响大小排序
    if impact_scores:
        # 按深睡影响排序
        sorted_by_sleep = sorted(
            [(k, v) for k, v in impact_scores.items() if v['sleep_pct'] > 0],
            key=lambda x: x[1]['sleep_pct'],
            reverse=True
        )
        # 按HRV影响排序
        sorted_by_hrv = sorted(
            [(k, v) for k, v in impact_scores.items() if v['hrv_pct'] > 0],
            key=lambda x: x[1]['hrv_pct'],
            reverse=True
        )
        
        if sorted_by_sleep:
            top_sleep = sorted_by_sleep[0]
            summary_parts.append(f"{top_sleep[0]}增加深睡占比+{top_sleep[1]['sleep_pct']}%")
        
        if sorted_by_hrv:
            top_hrv = sorted_by_hrv[0]
            summary_parts.append(f"{top_hrv[0]}提升HRV+{top_hrv[1]['hrv_pct']}%")
    
    if not summary_parts:
        summary_parts.append("未发现显著正向影响")
    
    summary = "，".join(summary_parts)
    
    # 构建返回结果
    result = {
        'impact_scores': impact_scores,
        'baseline': {
            'hrv_0800_mean': round(baseline_hrv, 1),
            'deep_sleep_ratio_mean': round(baseline_sleep, 3),
            'samples': baseline_samples
        },
        'summary': summary,
        'total_samples': len(df_analysis),
        'interventions_found': list(intervention_columns.keys())
    }
    
    logger.info(f"相关性分析完成：分析了 {len(df_analysis)} 条记录，发现 {len(impact_scores)} 个有效干预措施")
    return result


def get_intervention_comparison_data(df: pd.DataFrame, top_n: int = 3) -> Dict[str, Any]:
    """获取干预措施对比数据，用于绘制柱状图
    
    Args:
        df: 包含历史数据的DataFrame
        top_n: 返回前N个最有影响的干预措施
    
    Returns:
        dict: 包含对比数据的字典，用于图表绘制
    """
    # 先计算相关性
    correlation_result = calculate_correlations(df)
    
    impact_scores = correlation_result.get('impact_scores', {})
    baseline = correlation_result.get('baseline', {})
    
    # 选择最有影响的干预措施（按深睡影响和HRV影响的加权平均）
    interventions = []
    for name, data in impact_scores.items():
        # 计算综合影响分数
        composite_score = abs(data['sleep_pct']) * 0.7 + abs(data['hrv_pct']) * 0.3
        interventions.append({
            'name': name,
            'data': data,
            'composite_score': composite_score
        })
    
    # 按综合影响排序
    interventions.sort(key=lambda x: x['composite_score'], reverse=True)
    top_interventions = interventions[:top_n]
    
    # 准备图表数据
    categories = ['基线'] + [item['name'] for item in top_interventions]
    
    # HRV数据
    hrv_data = [baseline.get('hrv_0800_mean', 0)]
    hrv_labels = [f"基线\n{baseline.get('hrv_0800_mean', 0):.1f}ms"]
    
    # 深睡占比数据（转换为百分比）
    sleep_data = [baseline.get('deep_sleep_ratio_mean', 0) * 100]
    sleep_labels = [f"基线\n{baseline.get('deep_sleep_ratio_mean', 0)*100:.1f}%"]
    
    for item in top_interventions:
        data = item['data']
        hrv_value = data.get('hrv_mean', 0)
        sleep_value = data.get('sleep_mean', 0) * 100  # 转换为百分比
        
        hrv_data.append(hrv_value)
        sleep_data.append(sleep_value)
        
        # 添加变化标签
        hrv_change = data.get('hrv_pct', 0)
        sleep_change = data.get('sleep_pct', 0)
        
        hrv_labels.append(f"{item['name']}\n{hrv_value:.1f}ms ({hrv_change:+.1f}%)")
        sleep_labels.append(f"{item['name']}\n{sleep_value:.1f}% ({sleep_change:+.1f}%)")
    
    return {
        'categories': categories,
        'hrv_data': hrv_data,
        'sleep_data': sleep_data,
        'hrv_labels': hrv_labels,
        'sleep_labels': sleep_labels,
        'baseline': baseline,
        'top_interventions': [item['name'] for item in top_interventions],
        'summary': correlation_result.get('summary', ''),
        'total_samples': correlation_result.get('total_samples', 0)
    }


def analyze_intervention_effectiveness(df: pd.DataFrame) -> str:
    """生成干预措施有效性分析报告（文本格式）
    
    Args:
        df: 包含历史数据的DataFrame
    
    Returns:
        str: 分析报告文本
    """
    result = calculate_correlations(df)
    
    if not result.get('impact_scores'):
        return "📊 干预措施效能分析报告\n\n暂无足够数据进行分析。请记录更多包含干预措施的数据。"
    
    impact_scores = result['impact_scores']
    baseline = result['baseline']
    summary = result['summary']
    
    report_lines = [
        "📊 干预措施效能分析报告",
        "=" * 40,
        f"分析样本：{result['total_samples']} 天数据",
        f"基线（无干预）：HRV={baseline['hrv_0800_mean']}ms, 深睡占比={baseline['deep_sleep_ratio_mean']*100:.1f}%",
        "",
        "📈 各干预措施影响："
    ]
    
    # 按深睡影响排序
    sorted_interventions = sorted(
        impact_scores.items(),
        key=lambda x: x[1]['sleep_pct'],
        reverse=True
    )
    
    for name, data in sorted_interventions:
        hrv_sign = "+" if data['hrv_pct'] > 0 else ""
        sleep_sign = "+" if data['sleep_pct'] > 0 else ""
        
        report_lines.append(
            f"• {name} (n={data['samples']}): "
            f"HRV {hrv_sign}{data['hrv_pct']:.1f}% ({data['hrv_mean']}ms), "
            f"深睡 {sleep_sign}{data['sleep_pct']:.1f}% ({data['sleep_mean']*100:.1f}%)"
        )
    
    report_lines.extend([
        "",
        "💡 总结：",
        summary,
        "",
        "📋 建议：",
        "1. 持续追踪有效干预措施",
        "2. 建议每次只改变一个变量以准确归因",
        "3. 结合主观感受评估干预效果"
    ])
    
    return "\n".join(report_lines)


# 测试函数
if __name__ == "__main__":
    # 创建测试数据
    test_dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    
    # 模拟干预措施
    interventions_list = [
        '',
        '冷水洗脸',
        '镁补充',
        '冷水洗脸,镁补充',
        'NSDR',
        '冥想',
        '冷水洗脸,NSDR',
        '镁补充,冥想'
    ]
    
    np.random.seed(42)
    test_data = []
    
    for i, date in enumerate(test_dates):
        # 基线HRV和深睡
        base_hrv = 65 + np.random.normal(0, 5)
        base_sleep = 0.15 + np.random.normal(0, 0.02)
        
        # 随机选择干预措施
        intervention = np.random.choice(interventions_list, p=[0.3, 0.2, 0.2, 0.1, 0.1, 0.05, 0.03, 0.02])
        
        # 应用干预效果
        hrv_effect = 0
        sleep_effect = 0
        
        if '冷水洗脸' in intervention:
            hrv_effect += np.random.normal(3, 1)
        if '镁补充' in intervention:
            sleep_effect += np.random.normal(0.03, 0.01)
        if 'NSDR' in intervention:
            hrv_effect += np.random.normal(2, 1)
            sleep_effect += np.random.normal(0.02, 0.01)
        if '冥想' in intervention:
            hrv_effect += np.random.normal(4, 1.5)
        
        final_hrv = max(40, base_hrv + hrv_effect)
        final_sleep = max(0.05, min(0.35, base_sleep + sleep_effect))
        
        test_data.append({
            'date': date,
            'interventions': intervention,
            'hrv_0800': final_hrv,
            'deep_sleep_ratio': final_sleep
        })
    
    test_df = pd.DataFrame(test_data)
    
    print("测试数据前5行:")
    print(test_df.head())
    print("\n" + "="*50 + "\n")
    
    # 测试相关性分析
    print("进行干预措施相关性分析...")
    result = calculate_correlations(test_df)
    
    print(f"基线数据: HRV={result['baseline']['hrv_0800_mean']:.1f}ms, "
          f"深睡={result['baseline']['deep_sleep_ratio_mean']*100:.1f}%")
    print(f"总结: {result['summary']}")
    print("\n详细影响分数:")
    for name, data in result['impact_scores'].items():
        print(f"  {name}: HRV {data['hrv_pct']:+.1f}%, 深睡 {data['sleep_pct']:+.1f}% (n={data['samples']})")
    
    print("\n" + "="*50 + "\n")
    
    # 测试对比数据获取
    print("获取对比数据用于图表...")
    comparison_data = get_intervention_comparison_data(test_df, top_n=3)
    print(f"类别: {comparison_data['categories']}")
    print(f"HRV数据: {comparison_data['hrv_data']}")
    print(f"深睡数据: {comparison_data['sleep_data']}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试分析报告
    print("生成分析报告...")
    report = analyze_intervention_effectiveness(test_df)
    print(report)
