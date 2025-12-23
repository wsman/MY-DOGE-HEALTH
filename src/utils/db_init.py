"""
数据库初始化工具模块
提供统一的数据库检查和创建功能，确保两个数据库（bio_data.db和health_monitor.db）都存在
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_database_paths():
    """获取两个数据库文件的路径"""
    data_dir = Path('data')
    return {
        'bio_data': data_dir / 'bio_data.db',
        'health_monitor': data_dir / 'health_monitor.db'
    }

def ensure_databases_exist():
    """
    确保两个数据库都存在，如果不存在则创建
    
    Returns:
        tuple: (bool, list) 第一个元素表示是否成功，第二个元素是创建的数据库名称列表
    """
    db_paths = get_database_paths()
    created = []
    
    # 确保data目录存在
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # 检查并创建bio_data.db
    if not db_paths['bio_data'].exists():
        logger.info("bio_data.db 不存在，正在创建...")
        try:
            # 导入bio数据库模块
            from src.bio.database import initialize_db as init_bio
            success = init_bio()
            if success:
                created.append('bio_data')
                logger.info("bio_data.db 创建成功")
            else:
                logger.error("bio_data.db 创建失败")
                return False, created
        except Exception as e:
            logger.error(f"创建 bio_data.db 时发生错误: {e}")
            return False, created
    else:
        logger.debug("bio_data.db 已存在")
    
    # 检查并创建health_monitor.db
    if not db_paths['health_monitor'].exists():
        logger.info("health_monitor.db 不存在，正在创建...")
        try:
            # 导入health数据库模块
            from src.health.database import initialize_db as init_health
            success = init_health()
            if success:
                created.append('health_monitor')
                logger.info("health_monitor.db 创建成功")
            else:
                logger.error("health_monitor.db 创建失败")
                return False, created
        except Exception as e:
            logger.error(f"创建 health_monitor.db 时发生错误: {e}")
            return False, created
    else:
        logger.debug("health_monitor.db 已存在")
    
    # 如果创建了至少一个数据库，记录总结信息
    if created:
        logger.info(f"成功创建数据库: {', '.join(created)}")
    
    return True, created

def check_databases_exist():
    """
    检查两个数据库文件是否存在（不创建）
    
    Returns:
        dict: 每个数据库的存在状态
    """
    db_paths = get_database_paths()
    status = {}
    
    for name, path in db_paths.items():
        exists = path.exists()
        status[name] = exists
        logger.debug(f"数据库 {name}: {'存在' if exists else '不存在'}")
    
    return status

def initialize_all_databases():
    """
    强制初始化所有数据库（无论是否存在）
    
    Returns:
        bool: 是否全部初始化成功
    """
    logger.info("正在初始化所有数据库...")
    
    try:
        # 初始化bio_data.db
        from src.bio.database import initialize_db as init_bio
        success_bio = init_bio()
        
        if not success_bio:
            logger.error("bio_data.db 初始化失败")
            return False
        logger.info("bio_data.db 初始化成功")
        
        # 初始化health_monitor.db
        from src.health.database import initialize_db as init_health
        success_health = init_health()
        
        if not success_health:
            logger.error("health_monitor.db 初始化失败")
            return False
        logger.info("health_monitor.db 初始化成功")
        
        return True
    except Exception as e:
        logger.error(f"初始化数据库时发生错误: {e}")
        return False

def show_database_status():
    """
    显示数据库状态信息
    
    Returns:
        str: 格式化的状态信息
    """
    status = check_databases_exist()
    db_paths = get_database_paths()
    
    lines = []
    lines.append("数据库状态:")
    lines.append("-" * 40)
    
    for name, exists in status.items():
        status_icon = "✅" if exists else "❌"
        status_text = "存在" if exists else "不存在"
        path = db_paths[name]
        lines.append(f"{status_icon} {name}: {status_text} ({path})")
    
    # 检查文件大小
    lines.append("\n文件大小:")
    for name, path in db_paths.items():
        if path.exists():
            size_kb = path.stat().st_size / 1024
            lines.append(f"  {name}: {size_kb:.1f} KB")
        else:
            lines.append(f"  {name}: 文件不存在")
    
    return "\n".join(lines)

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("测试数据库初始化工具...")
    
    # 显示当前状态
    status_text = show_database_status()
    print(status_text)
    
    # 确保数据库存在
    print("\n正在检查并创建数据库（如果需要）...")
    success, created = ensure_databases_exist()
    
    if success:
        if created:
            print(f"创建了 {len(created)} 个数据库: {', '.join(created)}")
        else:
            print("所有数据库都已存在，无需创建")
    else:
        print("数据库创建失败")
    
    # 再次显示状态
    print("\n最终状态:")
    status_text = show_database_status()
    print(status_text)
