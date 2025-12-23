#!/usr/bin/env python3
"""
MY-DOGE Biometric Analysis System (MBAS) - 主程序入口
"""

import argparse
import sys
import os
import logging
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from health.database import initialize_db, get_biometric_data, get_trend_data
from health.entry import main as entry_main
from health.analyst import BiometricAnalyst, main as analyst_main
from health.config import HealthConfig, get_default_config

def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mbas.log'),
            logging.StreamHandler()
        ]
    )

def import_csv_data():
    """导入CSV测试数据"""
    csv_file = 'mbas_test_data.csv'
    if os.path.exists(csv_file):
        print(f"正在导入测试数据: {csv_file}")
        # 通过entry模块的import_from_csv函数导入
        from health.entry import import_from_csv
        success = import_from_csv(csv_file)
        if success:
            print(f"✅ 测试数据导入成功")
        else:
            print(f"❌ 测试数据导入失败")
        return success
    else:
        print(f"⚠️ 未找到测试数据文件: {csv_file}")
        return False

def generate_report(date=None, api_key=None, profile=None, base_url=None, model=None):
    """生成健康报告"""
    print(f"正在生成健康报告: {date or '最新数据'}")
    
    # 创建配置实例
    config = get_default_config()
    
    # 如果指定了profile，设置它
    if profile and config.set_profile(profile):
        print(f"📋 使用配置profile: {profile}")
    else:
        current_profile = config.get_current_profile()
        if current_profile:
            print(f"📋 使用默认配置profile: {current_profile.name}")
    
    # 创建分析师实例，传递命令行参数（最高优先级）
    analyst = BiometricAnalyst(
        config=config,
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    
    # 生成报告
    report_data = analyst.generate_daily_report(target_date=date)
    
    if report_data['success']:
        # 保存报告
        filepath = analyst.save_report_to_file(report_data)
        
        if filepath:
            print(f"✅ 健康报告生成成功: {filepath}")
            
            # 显示报告类型
            report_type = report_data.get('report_type', 'unknown')
            if report_type == 'circuit_breaker':
                print(f"🔴 熔断警报: {report_data['report_content']}")
            elif report_type == 'ai_analysis':
                print("🤖 AI分析报告已生成")
            elif report_type == 'basic_analysis':
                print("📊 基础分析报告已生成")
            
            # 显示使用的配置信息
            current_profile = config.get_current_profile()
            if current_profile:
                print(f"📋 使用的配置: {current_profile.name}")
            
            return True
        else:
            print("❌ 报告保存失败")
            return False
    else:
        print(f"❌ 报告生成失败: {report_data.get('error', '未知错误')}")
        return False

def show_dashboard(days=7):
    """显示仪表板"""
    from health.database import get_biometric_data, get_trend_data
    
    print(f"\n{'='*60}")
    print("MY-DOGE Biometric Analysis System - 仪表板")
    print(f"{'='*60}")
    
    # 获取最新数据
    records = get_biometric_data(limit=days)
    
    if not records:
        print("暂无数据")
        return
    
    # 显示最新记录
    latest = records[0]
    print(f"\n📅 最新记录: {latest.get('date', 'N/A')}")
    print(f"  体重: {latest.get('weight', 'N/A')}kg (目标: <93.0kg)")
    print(f"  总睡眠: {latest.get('total_sleep_min', 'N/A')}分钟")
    
    deep_sleep_ratio = latest.get('deep_sleep_ratio', 0)
    print(f"  深度睡眠: {latest.get('deep_sleep_min', 'N/A')}分钟 ({deep_sleep_ratio:.1%})")
    
    print(f"  HRV_0800: {latest.get('hrv_0800', 'N/A')}ms")
    print(f"  疲劳评分: {latest.get('fatigue_score', 'N/A')}/10")
    
    # 检查警报条件
    hrv_0800 = latest.get('hrv_0800', 0)
    if hrv_0800 < 40:
        print(f"  🔴 警报: HRV临界低值 ({hrv_0800}ms)")
    elif hrv_0800 < 50:
        print(f"  🟡 警告: HRV偏低 ({hrv_0800}ms)")
    
    # 显示趋势
    trend_data = get_trend_data(days=min(days, 30))
    if trend_data['count'] >= 2:
        print(f"\n📈 趋势分析 ({trend_data['count']}天):")
        
        # 体重趋势
        if len(trend_data['weights']) >= 2:
            weight_change = trend_data['weights'][-1] - trend_data['weights'][0]
            if weight_change < 0:
                print(f"  体重趋势: ↓ {abs(weight_change):.1f}kg")
            else:
                print(f"  体重趋势: ↑ {abs(weight_change):.1f}kg")
        
        # HRV趋势
        if len(trend_data['hrv_0800_values']) >= 2:
            hrv_change = trend_data['hrv_0800_values'][-1] - trend_data['hrv_0800_values'][0]
            if hrv_change > 0:
                print(f"  HRV趋势: ↑ {abs(hrv_change):.1f}ms")
            else:
                print(f"  HRV趋势: ↓ {abs(hrv_change):.1f}ms")
    
    print(f"\n💾 数据库: data/health_monitor.db")
    print(f"📁 报告目录: reports/")
    print(f"{'='*60}")

def list_profiles():
    """列出所有可用的配置profile"""
    from health.config import get_default_config
    config = get_default_config()
    
    print(f"\n{'='*60}")
    print("MY-DOGE 可用配置profile")
    print(f"{'='*60}")
    
    if not config.profiles:
        print("⚠️ 未找到任何配置profile，请检查models_config.json文件")
        return
    
    current_profile = config.get_current_profile()
    
    for i, profile in enumerate(config.profiles, 1):
        status = "✓" if current_profile and profile.name == current_profile.name else " "
        print(f"{i}. [{status}] {profile.name}")
        print(f"   模型: {profile.model}")
        print(f"   API地址: {profile.base_url}")
        print(f"   API密钥: {'已设置' if profile.api_key and len(profile.api_key) > 10 else '未设置或无效'}")
        print()
    
    print(f"默认profile: {config.default_profile}")
    print(f"代理设置: {'启用' if config.proxy_settings.get('enabled', False) else '禁用'}")
    if config.proxy_settings.get('enabled', False):
        print(f"代理地址: {config.proxy_settings.get('url', 'N/A')}")
    print(f"{'='*60}")

def validate_config():
    """验证配置有效性"""
    from health.config import get_default_config
    config = get_default_config()
    
    print(f"\n{'='*60}")
    print("MY-DOGE 配置验证")
    print(f"{'='*60}")
    
    success = config.validate_config(verbose=True)
    
    if success:
        print(f"\n✅ 配置验证通过，系统可以正常运行")
    else:
        print(f"\n❌ 配置存在问题，请根据上述错误进行修复")
    
    print(f"{'='*60}")
    return success

def show_config():
    """显示配置摘要"""
    from health.config import get_default_config
    config = get_default_config()
    config.show_config_summary()

def reload_config():
    """重新加载配置文件"""
    from health.config import get_default_config
    config = get_default_config()
    return config.reload_config()

def init_config():
    """初始化配置文件"""
    import shutil
    
    template_file = "models_config.template.json"
    target_file = "models_config.json"
    
    print(f"\n{'='*60}")
    print("MY-DOGE 配置文件初始化")
    print(f"{'='*60}")
    
    if os.path.exists(target_file):
        print(f"⚠️  配置文件已存在: {target_file}")
        print(f"   如果要重新初始化，请先备份或删除现有文件")
        return False
    
    if not os.path.exists(template_file):
        print(f"❌ 模板文件不存在: {template_file}")
        print(f"   请确保项目包含模板文件")
        return False
    
    try:
        shutil.copy2(template_file, target_file)
        print(f"✅ 配置文件已创建: {target_file}")
        print(f"   请编辑此文件并填写您的API密钥和其他配置")
        print(f"   注意: {target_file} 已添加到.gitignore，不会被提交到版本控制")
        return True
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='MY-DOGE Biometric Analysis System (MBAS) - 生物特征监测系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  python main.py --dashboard              # 显示仪表板
  python main.py --import-csv            # 导入测试数据
  python main.py --report                # 生成健康报告
  python main.py --entry                 # 交互式数据录入
  python main.py --init                  # 初始化数据库
  python main.py --list-profiles         # 列出所有配置profile
  python main.py --report --profile "🧠 DeepSeek Reasoner (R1 - Pro)"  # 使用指定profile生成报告
  
配置管理命令:
  python main.py --validate-config       # 验证配置有效性
  python main.py --show-config           # 显示配置摘要
  python main.py --reload-config         # 重新加载配置文件
  python main.py --init-config           # 初始化配置文件（从模板创建）
        '''
    )
    
    parser.add_argument('--dashboard', action='store_true', help='显示仪表板')
    parser.add_argument('--import-csv', action='store_true', help='导入CSV测试数据')
    parser.add_argument('--report', action='store_true', help='生成健康报告')
    parser.add_argument('--date', type=str, help='指定报告日期 (YYYY-MM-DD)')
    parser.add_argument('--entry', action='store_true', help='交互式数据录入')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--days', type=int, default=7, help='仪表板显示天数')
    parser.add_argument('--api-key', type=str, help='DeepSeek API密钥（最高优先级）')
    parser.add_argument('--base-url', type=str, help='API基础URL（最高优先级）')
    parser.add_argument('--model', type=str, help='使用的模型（最高优先级）')
    parser.add_argument('--profile', type=str, help='指定使用的配置profile名称')
    parser.add_argument('--view-data', action='store_true', help='查看数据记录')
    parser.add_argument('--limit', type=int, default=10, help='查看数据记录的数量')
    parser.add_argument('--list-profiles', action='store_true', help='列出所有可用的配置profile')
    parser.add_argument('--validate-config', action='store_true', help='验证配置有效性')
    parser.add_argument('--show-config', action='store_true', help='显示配置摘要')
    parser.add_argument('--reload-config', action='store_true', help='重新加载配置文件')
    parser.add_argument('--init-config', action='store_true', help='初始化配置文件（从模板创建）')
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging()
    
    # 如果没有指定任何操作，显示帮助
    if not any([args.dashboard, args.import_csv, args.report, args.entry, 
                args.init, args.view_data, args.list_profiles,
                args.validate_config, args.show_config, args.reload_config, args.init_config]):
        parser.print_help()
        return 0
    
    try:
        # 初始化数据库
        if args.init or args.import_csv or args.report or args.entry or args.view_data:
            print("🛠️ 初始化数据库...")
            initialize_db()
        
        # 导入CSV数据
        if args.import_csv:
            success = import_csv_data()
            if not success:
                return 1
        
        # 交互式数据录入
        if args.entry:
            print("📝 进入交互式数据录入模式...")
            # 调用entry模块的主函数
            from health.entry import main as entry_main
            return entry_main()
        
        # 列出profile
        if args.list_profiles:
            list_profiles()
            return 0
        
        # 查看数据
        if args.view_data:
            records = get_biometric_data(limit=args.limit)
            if records:
                print(f"\n📊 数据记录 (最近{len(records)}条):")
                for i, record in enumerate(records, 1):
                    print(f"\n记录 #{i}:")
                    print(f"  日期: {record.get('date')}")
                    print(f"  体重: {record.get('weight')}kg")
                    print(f"  睡眠: {record.get('total_sleep_min')}分钟")
                    print(f"  深度睡眠: {record.get('deep_sleep_min')}分钟 ({record.get('deep_sleep_ratio', 0):.1%})")
                    print(f"  HRV: {record.get('hrv_0000')}/{record.get('hrv_0400')}/{record.get('hrv_0800')}/{record.get('hrv_1200')}ms")
                    print(f"  疲劳: {record.get('fatigue_score')}/10")
            else:
                print("暂无数据")
        
        # 生成报告
        if args.report:
            success = generate_report(
                date=args.date, 
                api_key=args.api_key,
                profile=args.profile,
                base_url=args.base_url,
                model=args.model
            )
            if not success:
                return 1
        
        # 显示仪表板
        if args.dashboard:
            show_dashboard(days=args.days)
        
        # 配置验证
        if args.validate_config:
            success = validate_config()
            return 0 if success else 1
        
        # 显示配置摘要
        if args.show_config:
            show_config()
            return 0
        
        # 重新加载配置
        if args.reload_config:
            success = reload_config()
            return 0 if success else 1
        
        # 初始化配置文件
        if args.init_config:
            success = init_config()
            return 0 if success else 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        return 0
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        logging.exception("系统错误:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
