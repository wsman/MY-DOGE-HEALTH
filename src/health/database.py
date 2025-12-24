import os
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_db_path():
    """获取数据库文件路径"""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(current_dir, '..', 'data', 'health_monitor.db')
    return os.path.abspath(db_path)

def get_db_connection():
    """获取数据库连接对象"""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)

def initialize_db():
    """初始化数据库，创建 biometric_logs 表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建 biometric_logs 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biometric_logs (
            date DATE PRIMARY KEY,
            weight REAL,
            total_sleep_min INTEGER,
            deep_sleep_min INTEGER,
            rem_sleep_min INTEGER,
            hrv_0000 INTEGER,
            hrv_0200 INTEGER,
            hrv_0400 INTEGER,
            hrv_0600 INTEGER,
            hrv_0800 INTEGER,
            fatigue_score INTEGER,
            carb_limit_exec BOOLEAN,
            tags TEXT,
            interventions TEXT
        )
    ''')
    
    # 创建索引以优化查询
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON biometric_logs(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hrv_0800 ON biometric_logs(hrv_0800)')
    
    conn.commit()
    conn.close()
    logger.info(f"数据库初始化完成: {get_db_path()}")
    return True

def insert_biometric_data(data_dict):
    """插入或更新生物特征数据
    
    Args:
        data_dict: 包含字段值的字典
    Returns:
        bool: 插入/更新是否成功
    """
    required_fields = ['date', 'weight', 'total_sleep_min', 'deep_sleep_min', 
                       'rem_sleep_min', 'hrv_0000', 'hrv_0200', 'hrv_0400', 
                       'hrv_0600', 'hrv_0800', 'fatigue_score', 'carb_limit_exec']
    
    # 检查必填字段
    for field in required_fields:
        if field not in data_dict:
            logger.error(f"缺少必填字段: {field}")
            return False
    
    # 计算衍生字段
    deep_sleep_ratio = data_dict.get('deep_sleep_ratio')
    if deep_sleep_ratio is None:
        if data_dict['total_sleep_min'] > 0:
            deep_sleep_ratio = data_dict['deep_sleep_min'] / data_dict['total_sleep_min']
        else:
            deep_sleep_ratio = 0
    
    hrv_delta = data_dict.get('hrv_delta')
    if hrv_delta is None:
        hrv_delta = data_dict['hrv_0800'] - data_dict['hrv_0000']
    
    # 准备插入数据
    fields = required_fields + ['tags', 'interventions']
    values = [data_dict.get(field) for field in fields]
    
    # 确保interventions字段存在，默认为空字符串
    if values[-1] is None:
        values[-1] = ''
    
    # 处理布尔值转换
    carb_limit_exec_idx = fields.index('carb_limit_exec')
    if isinstance(values[carb_limit_exec_idx], bool):
        values[carb_limit_exec_idx] = 1 if values[carb_limit_exec_idx] else 0
    elif isinstance(values[carb_limit_exec_idx], str):
        values[carb_limit_exec_idx] = 1 if values[carb_limit_exec_idx].lower() in ('true', '1', 'yes') else 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 使用 UPSERT (SQLite 3.24+ 支持)
        placeholders = ', '.join(['?'] * len(fields))
        update_clause = ', '.join([f"{field} = excluded.{field}" for field in fields if field != 'date'])
        
        cursor.execute(f'''
            INSERT INTO biometric_logs ({', '.join(fields)})
            VALUES ({placeholders})
            ON CONFLICT(date) DO UPDATE SET
            {update_clause}
        ''', values)
        
        conn.commit()
        logger.info(f"数据已保存/更新: {data_dict['date']}")
        return True
    except Exception as e:
        logger.error(f"插入数据失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_biometric_data(date=None, limit=7):
    """获取生物特征数据
    
    Args:
        date: 特定日期 (YYYY-MM-DD)，如果为None则获取最新数据
        limit: 返回的记录数限制
    
    Returns:
        list: 数据记录列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if date:
            cursor.execute('''
                SELECT * FROM biometric_logs 
                WHERE date = ?
                ORDER BY date DESC
            ''', (date,))
        else:
            cursor.execute('''
                SELECT * FROM biometric_logs 
                ORDER BY date DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        result = []
        for row in rows:
            record = dict(zip(columns, row))
            # 转换布尔值
            record['carb_limit_exec'] = bool(record['carb_limit_exec'])
            # 计算衍生字段
            if record['total_sleep_min'] > 0:
                record['deep_sleep_ratio'] = record['deep_sleep_min'] / record['total_sleep_min']
            else:
                record['deep_sleep_ratio'] = 0
            record['hrv_delta'] = record['hrv_0800'] - record['hrv_0000']
            result.append(record)
        
        return result
    except Exception as e:
        logger.error(f"查询数据失败: {e}")
        return []
    finally:
        conn.close()

def get_trend_data(days=7):
    """获取趋势数据
    
    Args:
        days: 过去多少天的数据
    
    Returns:
        dict: 包含weight和hrv_0800趋势的数据
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT date, weight, hrv_0800 
            FROM biometric_logs 
            ORDER BY date DESC 
            LIMIT ?
        ''', (days,))
        
        rows = cursor.fetchall()
        
        # 反转顺序，使时间从旧到新
        rows.reverse()
        
        dates = [row[0] for row in rows]
        weights = [row[1] for row in rows]
        hrv_values = [row[2] for row in rows]
        
        return {
            'dates': dates,
            'weights': weights,
            'hrv_0800_values': hrv_values,
            'count': len(rows)
        }
    except Exception as e:
        logger.error(f"获取趋势数据失败: {e}")
        return {'dates': [], 'weights': [], 'hrv_0800_values': [], 'count': 0}
    finally:
        conn.close()

if __name__ == "__main__":
    # 测试数据库初始化
    logging.basicConfig(level=logging.INFO)
    initialize_db()
    print("数据库初始化测试完成")
