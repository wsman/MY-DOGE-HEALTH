import argparse
import csv
import os
import sys
from datetime import datetime
import logging
from .database import initialize_db, insert_biometric_data, get_biometric_data

logger = logging.getLogger(__name__)

def validate_data(data):
    """验证数据有效性"""
    errors = []
    
    # 检查必填字段
    required_fields = ['date', 'weight', 'total_sleep_min', 'deep_sleep_min', 
                       'rem_sleep_min', 'hrv_0000', 'hrv_0400', 'hrv_0800', 
                       'hrv_1200', 'fatigue_score', 'carb_limit_exec']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors.append(f"缺少必填字段: {field}")
    
    if errors:
        return False, errors
    
    # 验证数值范围
    if data['weight'] <= 0 or data['weight'] > 200:
        errors.append("体重应在0-200kg之间")
    
    if data['total_sleep_min'] < 0 or data['total_sleep_min'] > 1440:
        errors.append("总睡眠时间应在0-1440分钟之间")
    
    if data['deep_sleep_min'] < 0 or data['deep_sleep_min'] > data['total_sleep_min']:
        errors.append("深度睡眠时间不能超过总睡眠时间")
    
    if data['rem_sleep_min'] < 0 or data['rem_sleep_min'] > data['total_sleep_min']:
        errors.append("REM睡眠时间不能超过总睡眠时间")
    
    for hrv_field in ['hrv_0000', 'hrv_0400', 'hrv_0800', 'hrv_1200']:
        value = data[hrv_field]
        if value < 0 or value > 200:
            errors.append(f"{hrv_field}应在0-200ms之间")
    
    if data['fatigue_score'] < 1 or data['fatigue_score'] > 10:
        errors.append("疲劳评分应在1-10之间")
    
    return len(errors) == 0, errors

def calculate_derived_fields(data):
    """计算衍生字段"""
    # 计算深度睡眠比例
    if data['total_sleep_min'] > 0:
        data['deep_sleep_ratio'] = data['deep_sleep_min'] / data['total_sleep_min']
    else:
        data['deep_sleep_ratio'] = 0
    
    # 计算HRV变化
    data['hrv_delta'] = data['hrv_0800'] - data['hrv_0000']
    
    return data

def import_from_csv(csv_path):
    """从CSV文件导入数据"""
    if not os.path.exists(csv_path):
        logger.error(f"CSV文件不存在: {csv_path}")
        return False
    
    success_count = 0
    fail_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # 转换数据类型
                    data = {
                        'date': row['date'],
                        'weight': float(row['weight']),
                        'total_sleep_min': int(row['total_sleep_min']),
                        'deep_sleep_min': int(row['deep_sleep_min']),
                        'rem_sleep_min': int(row['rem_sleep_min']),
                        'hrv_0000': int(row['hrv_0000']),
                        'hrv_0400': int(row['hrv_0400']),
                        'hrv_0800': int(row['hrv_0800']),
                        'hrv_1200': int(row['hrv_1200']),
                        'fatigue_score': int(row['fatigue_score']),
                        'carb_limit_exec': row['carb_limit_exec'].lower() in ('true', '1', 'yes'),
                        'tags': row.get('tags', '')
                    }
                    
                    # 验证数据
                    is_valid, errors = validate_data(data)
                    if not is_valid:
                        logger.warning(f"第{row_num}行数据验证失败: {errors}")
                        fail_count += 1
                        continue
                    
                    # 计算衍生字段
                    data = calculate_derived_fields(data)
                    
                    # 插入数据库
                    if insert_biometric_data(data):
                        success_count += 1
                        logger.info(f"第{row_num}行数据导入成功: {data['date']}")
                    else:
                        fail_count += 1
                        logger.error(f"第{row_num}行数据插入失败: {data['date']}")
                        
                except (ValueError, KeyError) as e:
                    fail_count += 1
                    logger.error(f"第{row_num}行数据格式错误: {e}")
        
        logger.info(f"CSV导入完成: 成功{success_count}条，失败{fail_count}条")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"读取CSV文件失败: {e}")
        return False

def interactive_input():
    """交互式数据输入"""
    print("\n=== MY-DOGE 生物特征数据录入 ===")
    print("请输入每日生理数据 (按Ctrl+C退出)\n")
    
    data = {}
    
    try:
        # 日期输入
        while True:
            date_str = input("日期 (YYYY-MM-DD, 默认为今天): ").strip()
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                data['date'] = date_str
                break
            except ValueError:
                print("日期格式错误，请使用 YYYY-MM-DD 格式")
        
        # 体重
        while True:
            try:
                weight = float(input("体重 (kg, 目标 < 93.0): ").strip())
                if 0 < weight <= 200:
                    data['weight'] = weight
                    break
                else:
                    print("体重应在0-200kg之间")
            except ValueError:
                print("请输入有效的数字")
        
        # 睡眠数据
        while True:
            try:
                total_sleep = int(input("总睡眠时间 (分钟): ").strip())
                if 0 <= total_sleep <= 1440:
                    data['total_sleep_min'] = total_sleep
                    break
                else:
                    print("总睡眠时间应在0-1440分钟之间")
            except ValueError:
                print("请输入整数")
        
        while True:
            try:
                deep_sleep = int(input("深度睡眠时间 (分钟): ").strip())
                if 0 <= deep_sleep <= data['total_sleep_min']:
                    data['deep_sleep_min'] = deep_sleep
                    break
                else:
                    print(f"深度睡眠时间不能超过总睡眠时间 ({data['total_sleep_min']}分钟)")
            except ValueError:
                print("请输入整数")
        
        while True:
            try:
                rem_sleep = int(input("REM睡眠时间 (分钟): ").strip())
                if 0 <= rem_sleep <= data['total_sleep_min']:
                    data['rem_sleep_min'] = rem_sleep
                    break
                else:
                    print(f"REM睡眠时间不能超过总睡眠时间 ({data['total_sleep_min']}分钟)")
            except ValueError:
                print("请输入整数")
        
        # HRV数据
        hrv_fields = ['0000', '0400', '0800', '1200']
        for field in hrv_fields:
            while True:
                try:
                    hrv_value = int(input(f"HRV_{field} (ms): ").strip())
                    if 0 <= hrv_value <= 200:
                        data[f'hrv_{field}'] = hrv_value
                        break
                    else:
                        print("HRV值应在0-200ms之间")
                except ValueError:
                    print("请输入整数")
        
        # 疲劳评分
        while True:
            try:
                fatigue = int(input("疲劳评分 (1-10): ").strip())
                if 1 <= fatigue <= 10:
                    data['fatigue_score'] = fatigue
                    break
                else:
                    print("疲劳评分应在1-10之间")
            except ValueError:
                print("请输入整数")
        
        # 碳水限制执行情况
        while True:
            carb_input = input("睡前4h禁碳水执行情况 (y/n): ").strip().lower()
            if carb_input in ('y', 'yes', 'true', '1'):
                data['carb_limit_exec'] = True
                break
            elif carb_input in ('n', 'no', 'false', '0'):
                data['carb_limit_exec'] = False
                break
            else:
                print("请输入 y/n")
        
        # 标签
        tags = input("标签 (可选, 用逗号分隔): ").strip()
        data['tags'] = tags if tags else ''
        
        # 验证并计算衍生字段
        is_valid, errors = validate_data(data)
        if not is_valid:
            print("数据验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        data = calculate_derived_fields(data)
        
        # 显示汇总信息
        print("\n=== 数据汇总 ===")
        print(f"日期: {data['date']}")
        print(f"体重: {data['weight']}kg (目标: <93.0kg)")
        print(f"总睡眠: {data['total_sleep_min']}分钟")
        print(f"深度睡眠: {data['deep_sleep_min']}分钟 ({data['deep_sleep_ratio']:.1%})")
        print(f"HRV变化: {data['hrv_0000']} → {data['hrv_0800']} (Δ={data['hrv_delta']})")
        print(f"疲劳评分: {data['fatigue_score']}/10")
        print(f"碳水限制: {'是' if data['carb_limit_exec'] else '否'}")
        
        confirm = input("\n确认保存数据？ (y/n): ").strip().lower()
        if confirm in ('y', 'yes'):
            if insert_biometric_data(data):
                print("✅ 数据保存成功！")
                return True
            else:
                print("❌ 数据保存失败")
                return False
        else:
            print("数据已取消")
            return False
            
    except KeyboardInterrupt:
        print("\n\n输入已取消")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='MY-DOGE Biometric Analysis System - 数据录入工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  python -m src.health.entry                    # 交互式输入
  python -m src.health.entry --import-csv mbas_test_data.csv  # 从CSV导入
  python -m src.health.entry --view             # 查看最近记录
        '''
    )
    
    parser.add_argument('--import-csv', type=str, help='从CSV文件导入数据')
    parser.add_argument('--view', action='store_true', help='查看最近7天的记录')
    parser.add_argument('--date', type=str, help='查看特定日期的记录 (YYYY-MM-DD)')
    parser.add_argument('--limit', type=int, default=7, help='查看记录的数量限制')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化数据库
    initialize_db()
    
    if args.import_csv:
        # CSV导入模式
        print(f"正在从CSV文件导入数据: {args.import_csv}")
        success = import_from_csv(args.import_csv)
        if success:
            print("✅ CSV导入完成")
        else:
            print("❌ CSV导入失败")
        sys.exit(0 if success else 1)
    
    elif args.view:
        # 查看模式
        records = get_biometric_data(date=args.date, limit=args.limit)
        if not records:
            print("未找到数据")
            sys.exit(1)
        
        print(f"\n=== 生物特征数据记录 ===")
        for i, record in enumerate(records, 1):
            print(f"\n记录 #{i}:")
            print(f"  日期: {record['date']}")
            print(f"  体重: {record['weight']}kg")
            print(f"  总睡眠: {record['total_sleep_min']}分钟")
            print(f"  深度睡眠: {record['deep_sleep_min']}分钟 ({record.get('deep_sleep_ratio', 0):.1%})")
            print(f"  HRV: {record['hrv_0000']}/{record['hrv_0400']}/{record['hrv_0800']}/{record['hrv_1200']}ms")
            print(f"  HRV变化: Δ={record.get('hrv_delta', 0)}ms")
            print(f"  疲劳评分: {record['fatigue_score']}/10")
            print(f"  碳水限制: {'是' if record['carb_limit_exec'] else '否'}")
            if record.get('tags'):
                print(f"  标签: {record['tags']}")
        
        sys.exit(0)
    
    else:
        # 交互式输入模式
        success = interactive_input()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
