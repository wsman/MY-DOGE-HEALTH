"""
MY-DOGE Biometric Analysis System (MBAS) - 健康监测模块
"""

__version__ = "1.0.0"
__author__ = "wsman"
__email__ = "wsman0325@gmail.com"
__description__ = "生物特征监测与分析系统"

from .database import (
    initialize_db,
    get_db_connection,
    insert_biometric_data,
    get_biometric_data,
    get_trend_data
)

from .entry import (
    validate_data,
    calculate_derived_fields,
    import_from_csv,
    interactive_input,
    main as entry_main
)

from .analyst import (
    BiometricAnalyst,
    main as analyst_main
)

from .config import (
    HealthConfig,
    get_default_config
)

__all__ = [
    # 数据库模块
    'initialize_db',
    'get_db_connection',
    'insert_biometric_data',
    'get_biometric_data',
    'get_trend_data',
    
    # 数据录入模块
    'validate_data',
    'calculate_derived_fields',
    'import_from_csv',
    'interactive_input',
    'entry_main',
    
    # 分析模块
    'BiometricAnalyst',
    'analyst_main',
    
    # 配置模块
    'HealthConfig',
    'get_default_config',
]
