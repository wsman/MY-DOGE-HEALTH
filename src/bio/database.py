import os
import sqlite3
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_db_path() -> str:
    """获取数据库文件路径"""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(current_dir, '..', 'data', 'bio_data.db')
    return os.path.abspath(db_path)

def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接对象"""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)

def initialize_db() -> bool:
    """初始化数据库，创建 biometric_logs 表（按照任务要求的Schema）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建 biometric_logs 表（严格按照任务要求的Schema）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biometric_logs (
            date DATE PRIMARY KEY,
            timestamp TEXT,               -- 报告生成时间（只存储时间，如21:29:38）
            tags TEXT,                    -- 标签，例如 'health,deepseek'
            analyst TEXT,                 -- 分析师，例如 'deepseek-reasoner'
            total_sleep_min INTEGER,      -- 总睡眠分钟 (需在UI将小时转换为分钟)
            deep_sleep_min INTEGER,       -- 深度睡眠分钟
            deep_sleep_ratio REAL,        -- 深度睡眠占比 (自动计算: deep / total)
            hrv_0000 INTEGER,             -- 0点 HRV (基准负载)
            hrv_0200 INTEGER,             -- 2点 HRV
            hrv_0400 INTEGER,             -- 4点 HRV (巅峰修复)
            hrv_0600 INTEGER,             -- 6点 HRV
            hrv_0800 INTEGER,             -- 8点 HRV (苏醒状态)
            weight REAL,                  -- 体重 (目标 < 93kg)
            fatigue_score INTEGER,        -- 主观疲劳度 (1-10)
            carb_limit_check BOOLEAN,     -- 睡前4小时禁碳水执行状态 (0/1)
            interventions TEXT,           -- 干预措施，以逗号分隔的字符串，例如 '冷水洗脸,镁补充'
            title TEXT,                   -- 报告标题（不包含《》）
            report_content TEXT           -- 存储生成的 AI 报告
        )
    ''')
    
    # 创建索引以优化查询
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON biometric_logs(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_weight ON biometric_logs(weight)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deep_sleep_ratio ON biometric_logs(deep_sleep_ratio)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyst ON biometric_logs(analyst)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON biometric_logs(timestamp)')
    
    # 尝试添加 interventions 列（如果表已存在且没有该列）
    try:
        cursor.execute('ALTER TABLE biometric_logs ADD COLUMN interventions TEXT')
        logger.info("已添加 interventions 列到 biometric_logs 表")
    except sqlite3.OperationalError as e:
        # 列已存在或其他操作错误，忽略
        logger.debug(f"添加 interventions 列时忽略错误: {e}")
    
    conn.commit()
    conn.close()
    logger.info(f"数据库初始化完成: {get_db_path()}")
    return True

def save_daily_log(data_dict: Dict[str, Any]) -> bool:
    """接收字典数据，自动计算 deep_sleep_ratio，存入数据库
    
    Args:
        data_dict: 包含日期和各项指标的字典，必须包含以下字段：
            - date: 日期字符串 'YYYY-MM-DD' 或 datetime.date 对象
            - total_sleep_min: 总睡眠分钟（整数）
            - deep_sleep_min: 深度睡眠分钟（整数）
            - hrv_0000: 0点 HRV（整数）
            - hrv_0200: 2点 HRV（整数）
            - hrv_0400: 4点 HRV（整数）
            - hrv_0600: 6点 HRV（整数）
            - hrv_0800: 8点 HRV（整数）
            - weight: 体重（浮点数）
            - fatigue_score: 疲劳度评分（整数，1-10）
            - carb_limit_check: 禁碳水执行状态（布尔值或整数 0/1）
            - report_content: AI报告内容（字符串，可选）
            - timestamp: 报告生成时间（可选，默认为当前时间，格式HH:MM:SS）
            - tags: 标签（可选，默认为'health,deepseek'）
            - analyst: 分析师（可选，默认为'deepseek-reasoner'）
            - title: 报告标题（可选，不包含《》）
    
    Returns:
        bool: 保存是否成功
    """
    required_fields = [
        'date', 'total_sleep_min', 'deep_sleep_min', 
        'hrv_0000', 'hrv_0200', 'hrv_0400', 'hrv_0600', 'hrv_0800', 'weight',
        'fatigue_score', 'carb_limit_check'
    ]
    
    # 检查必填字段
    for field in required_fields:
        if field not in data_dict:
            logger.error(f"缺少必填字段: {field}")
            return False
    
    # 处理日期格式
    date_value = data_dict['date']
    if isinstance(date_value, date):
        date_str = date_value.isoformat()
    elif isinstance(date_value, str):
        # 验证日期字符串格式
        try:
            datetime.strptime(date_value, '%Y-%m-%d')
            date_str = date_value
        except ValueError:
            logger.error(f"日期格式错误，应为 'YYYY-MM-DD': {date_value}")
            return False
    else:
        logger.error(f"日期类型错误: {type(date_value)}")
        return False
    
    # 计算深度睡眠占比
    total_sleep = data_dict['total_sleep_min']
    deep_sleep = data_dict['deep_sleep_min']
    if total_sleep > 0:
        deep_sleep_ratio = deep_sleep / total_sleep
    else:
        deep_sleep_ratio = 0.0
    
    # 处理可选字段
    hrv_0200 = data_dict.get('hrv_0200', 0)
    hrv_0600 = data_dict.get('hrv_0600', 0)
    report_content = data_dict.get('report_content', '')
    
    # 处理新字段
    timestamp = data_dict.get('timestamp')
    if timestamp is None:
        timestamp = datetime.now().strftime('%H:%M:%S')
    
    tags = data_dict.get('tags')
    if tags is None:
        tags = 'health,deepseek'
    
    analyst = data_dict.get('analyst')
    if analyst is None:
        analyst = 'deepseek-reasoner'
    
    interventions = data_dict.get('interventions', '')
    title = data_dict.get('title', '')
    
    # 处理布尔值转换
    carb_limit_check = data_dict['carb_limit_check']
    if isinstance(carb_limit_check, bool):
        carb_limit_int = 1 if carb_limit_check else 0
    elif isinstance(carb_limit_check, str):
        carb_limit_int = 1 if carb_limit_check.lower() in ('true', '1', 'yes') else 0
    elif isinstance(carb_limit_check, int):
        carb_limit_int = 1 if carb_limit_check else 0
    else:
        logger.error(f"carb_limit_check 类型错误: {type(carb_limit_check)}")
        return False
    
    # 验证数据范围
    if total_sleep < 0 or total_sleep > 1440:  # 24小时
        logger.error(f"总睡眠分钟超出合理范围: {total_sleep}")
        return False
    
    if deep_sleep < 0 or deep_sleep > total_sleep:
        logger.error(f"深度睡眠分钟超出合理范围: {deep_sleep} (总睡眠: {total_sleep})")
        return False
    
    if data_dict['fatigue_score'] < 1 or data_dict['fatigue_score'] > 10:
        logger.error(f"疲劳度评分超出范围 1-10: {data_dict['fatigue_score']}")
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 使用 UPSERT (SQLite 3.24+ 支持)
        cursor.execute('''
            INSERT INTO biometric_logs 
            (date, timestamp, tags, analyst, total_sleep_min, deep_sleep_min, deep_sleep_ratio,
             hrv_0000, hrv_0200, hrv_0400, hrv_0600, hrv_0800,
             weight, fatigue_score, carb_limit_check, interventions, title, report_content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                timestamp = excluded.timestamp,
                tags = excluded.tags,
                analyst = excluded.analyst,
                total_sleep_min = excluded.total_sleep_min,
                deep_sleep_min = excluded.deep_sleep_min,
                deep_sleep_ratio = excluded.deep_sleep_ratio,
                hrv_0000 = excluded.hrv_0000,
                hrv_0200 = excluded.hrv_0200,
                hrv_0400 = excluded.hrv_0400,
                hrv_0600 = excluded.hrv_0600,
                hrv_0800 = excluded.hrv_0800,
                weight = excluded.weight,
                fatigue_score = excluded.fatigue_score,
                carb_limit_check = excluded.carb_limit_check,
                interventions = excluded.interventions,
                title = excluded.title,
                report_content = excluded.report_content
        ''', (
            date_str, timestamp, tags, analyst, total_sleep, deep_sleep, deep_sleep_ratio,
            data_dict['hrv_0000'], hrv_0200, data_dict['hrv_0400'], hrv_0600, data_dict['hrv_0800'],
            data_dict['weight'], data_dict['fatigue_score'], carb_limit_int, interventions, title, report_content
        ))
        
        conn.commit()
        logger.info(f"数据已保存/更新: {date_str}")
        return True
    except Exception as e:
        logger.error(f"插入数据失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_recent_logs(days: int = 7) -> List[Dict[str, Any]]:
    """返回最近 N 天的数据，用于 AI 分析趋势
    
    Args:
        days: 最近多少天的数据
    
    Returns:
        list: 数据记录列表，按日期倒序排列
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM biometric_logs 
            ORDER BY date DESC 
            LIMIT ?
        ''', (days,))
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        result = []
        for row in rows:
            record = dict(zip(columns, row))
            # 转换布尔值
            record['carb_limit_check'] = bool(record['carb_limit_check'])
            result.append(record)
        
        return result
    except Exception as e:
        logger.error(f"查询数据失败: {e}")
        return []
    finally:
        conn.close()

def get_all_logs() -> List[Dict[str, Any]]:
    """获取所有日志数据（用于导出或分析）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM biometric_logs ORDER BY date DESC')
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        result = []
        for row in rows:
            record = dict(zip(columns, row))
            record['carb_limit_check'] = bool(record['carb_limit_check'])
            result.append(record)
        
        return result
    except Exception as e:
        logger.error(f"查询所有数据失败: {e}")
        return []
    finally:
        conn.close()

def delete_log(target_date: str) -> bool:
    """删除指定日期的记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM biometric_logs WHERE date = ?', (target_date,))
        conn.commit()
        deleted = cursor.rowcount > 0
        
        if deleted:
            logger.info(f"已删除记录: {target_date}")
        else:
            logger.warning(f"未找到记录: {target_date}")
            
        return deleted
    except Exception as e:
        logger.error(f"删除记录失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_date_range() -> Dict[str, Optional[str]]:
    """获取数据集的日期范围"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT MIN(date), MAX(date) FROM biometric_logs')
        row = cursor.fetchone()
        
        return {
            'min_date': row[0],
            'max_date': row[1]
        }
    except Exception as e:
        logger.error(f"获取日期范围失败: {e}")
        return {'min_date': None, 'max_date': None}
    finally:
        conn.close()

def get_intervention_stats():
    """获取所有历史数据（包括干预措施）的pandas DataFrame
    
    Returns:
        pandas.DataFrame: 包含所有历史数据的DataFrame，如果出错则返回None
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error("需要安装pandas库: pip install pandas")
        return None
    
    conn = get_db_connection()
    try:
        # 使用pandas直接读取SQL查询结果
        query = '''
            SELECT 
                date, 
                timestamp,
                tags,
                analyst,
                total_sleep_min,
                deep_sleep_min,
                deep_sleep_ratio,
                hrv_0000,
                hrv_0200,
                hrv_0400,
                hrv_0600,
                hrv_0800,
                weight,
                fatigue_score,
                carb_limit_check,
                interventions,
                title,
                report_content
            FROM biometric_logs 
            ORDER BY date
        '''
        df = pd.read_sql_query(query, conn)
        
        # 将date列转换为datetime类型
        df['date'] = pd.to_datetime(df['date'])
        
        # 确保carb_limit_check为布尔类型
        df['carb_limit_check'] = df['carb_limit_check'].astype(bool)
        
        # 确保数值列类型正确
        numeric_columns = ['total_sleep_min', 'deep_sleep_min', 'deep_sleep_ratio', 
                          'hrv_0000', 'hrv_0200', 'hrv_0400', 'hrv_0600', 'hrv_0800',
                          'weight', 'fatigue_score']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        logger.info(f"成功加载 {len(df)} 条干预统计数据")
        return df
        
    except Exception as e:
        logger.error(f"获取干预统计数据失败: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # 测试数据库初始化
    logging.basicConfig(level=logging.INFO)
    initialize_db()
    print("数据库初始化测试完成")
    
    # 测试插入一条数据
    test_data = {
        'date': datetime.now().date().isoformat(),
        'total_sleep_min': 480,  # 8小时
        'deep_sleep_min': 72,    # 1.2小时
        'hrv_0000': 65,
        'hrv_0200': 70,
        'hrv_0400': 85,
        'hrv_0600': 75,
        'hrv_0800': 70,
        'weight': 92.5,
        'fatigue_score': 3,
        'carb_limit_check': True,
        'report_content': '测试报告内容'
    }
    
    if save_daily_log(test_data):
        print("测试数据插入成功")
    else:
        print("测试数据插入失败")
    
    # 测试查询最近7天数据
    recent = get_recent_logs(7)
    print(f"最近 {len(recent)} 条记录:")
    for record in recent:
        print(f"  {record['date']}: 体重={record['weight']}kg, 深睡占比={record['deep_sleep_ratio']:.1%}")
