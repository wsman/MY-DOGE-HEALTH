#!/usr/bin/env python3
"""
MY-DOGE BIO-MONITOR - 个人生物信息量化监测系统
主入口文件：集成数据库初始化、配置检查和GUI启动
"""

import sys
import os
import logging
import json
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_directories():
    """检查必要的目录结构"""
    directories = ['data', 'reports', 'src/bio', 'src/interface']
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目录: {directory}")
    
    logger.info("目录结构检查完成")

def check_config_file():
    """检查配置文件，如果不存在则从模板创建"""
    config_file = Path("models_config.json")
    template_file = Path("models_config.template.json")
    
    if config_file.exists():
        logger.info(f"配置文件已存在: {config_file}")
        return True
    elif template_file.exists():
        logger.warning(f"配置文件不存在，从模板创建: {config_file}")
        
        # 读取模板内容
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 写入配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            logger.info("配置文件创建成功，请编辑 models_config.json 填入您的 API Key")
            return False  # 需要用户编辑配置
        except Exception as e:
            logger.error(f"创建配置文件失败: {e}")
            return False
    else:
        logger.error("配置文件模板也不存在，无法创建配置文件")
        return False

def validate_api_key():
    """验证API Key配置"""
    config_file = Path("models_config.json")
    
    if not config_file.exists():
        logger.error("配置文件不存在，请先创建 models_config.json")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查是否有API Key配置
        api_key_set = False
        for profile in config.get('profiles', []):
            if profile.get('api_key') and profile['api_key'] != 'YOUR_API_KEY_HERE':
                api_key_set = True
                break
        
        if not api_key_set:
            logger.warning("⚠️  未配置有效的DeepSeek API Key")
            logger.warning("   请编辑 models_config.json，将 'YOUR_API_KEY_HERE' 替换为您的API Key")
            return False
        
        logger.info("API Key配置检查通过")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
        return False
    except Exception as e:
        logger.error(f"验证配置文件时发生错误: {e}")
        return False

def initialize_database():
    """初始化数据库"""
    try:
        # 导入数据库模块
        from src.bio.database import initialize_db
        
        logger.info("正在初始化数据库...")
        success = initialize_db()
        
        if success:
            logger.info("数据库初始化成功")
            return True
        else:
            logger.error("数据库初始化失败")
            return False
            
    except ImportError as e:
        logger.error(f"导入数据库模块失败: {e}")
        logger.error("请确保已安装所有依赖: pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"数据库初始化时发生错误: {e}")
        return False

def check_dependencies():
    """检查依赖包是否已安装"""
    required_packages = [
        'PyQt6',
        'openai',
        'pandas',
        'sqlite3'  # Python内置，通常不需要检查
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            elif package == 'PyQt6':
                import PyQt6
            elif package == 'openai':
                import openai
            elif package == 'pandas':
                import pandas
            logger.debug(f"✅ {package} 已安装")
        except ImportError:
            if package != 'sqlite3':  # sqlite3是Python内置，不应该缺失
                missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"缺少必要的依赖包: {', '.join(missing_packages)}")
        logger.error("请运行: pip install -r requirements.txt")
        return False
    
    logger.info("所有依赖包检查通过")
    return True

def start_gui():
    """启动GUI界面"""
    try:
        # 导入GUI模块
        from src.interface.bio_dashboard import main as gui_main
        
        logger.info("正在启动GUI界面...")
        gui_main()
        return True
        
    except ImportError as e:
        logger.error(f"导入GUI模块失败: {e}")
        logger.error("请确保文件 src/interface/bio_dashboard.py 存在")
        return False
    except Exception as e:
        logger.error(f"启动GUI时发生错误: {e}")
        return False

def show_welcome_banner():
    """显示欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    ███╗   ███╗██╗   ██╗    ██████╗  ██████╗  ██████╗ ███████╗║
║    ████╗ ████║╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██╔════╝ ██╔════╝║
║    ██╔████╔██║ ╚████╔╝     ██║  ██║██║   ██║██║  ███╗█████╗  ║
║    ██║╚██╔╝██║  ╚██╔╝      ██║  ██║██║   ██║██║   ██║██╔══╝  ║
║    ██║ ╚═╝ ██║   ██║       ██████╔╝╚██████╔╝╚██████╔╝███████╗║
║    ╚═╝     ╚═╝   ╚═╝       ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝║
║                                                              ║
║       生物信息量化监测系统 - 内务部健康管理平台              ║
║       MY-DOGE BIO-MONITOR - Health Intelligence Platform     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    
版本: 1.0.0
工作目录: {}
    
系统初始化中...
    """.format(os.getcwd())
    
    print(banner)

def main():
    """主函数"""
    try:
        # 显示欢迎横幅
        show_welcome_banner()
        
        # 步骤1: 检查目录结构
        logger.info("步骤1: 检查目录结构")
        check_directories()
        
        # 步骤2: 检查依赖
        logger.info("步骤2: 检查依赖包")
        if not check_dependencies():
            print("\n❌ 依赖包检查失败，请安装所需依赖")
            print("运行: pip install -r requirements.txt")
            input("按回车键退出...")
            return 1
        
        # 步骤3: 检查配置文件
        logger.info("步骤3: 检查配置文件")
        config_exists = check_config_file()
        
        if not config_exists:
            print("\n⚠️  配置文件已从模板创建，请编辑 models_config.json")
            print("   将 'YOUR_API_KEY_HERE' 替换为您的DeepSeek API Key")
            input("\n按回车键继续（系统将以本地模式运行）...")
        
        # 步骤4: 验证API Key（可选，不强制）
        validate_api_key()
        
        # 步骤5: 初始化数据库
        logger.info("步骤4: 初始化数据库")
        if not initialize_database():
            print("\n❌ 数据库初始化失败")
            input("按回车键退出...")
            return 1
        
        # 步骤6: 启动GUI
        logger.info("步骤5: 启动GUI界面")
        print("\n" + "="*60)
        print("✅ 系统初始化完成，正在启动图形界面...")
        print("="*60 + "\n")
        
        # 注意：start_gui()会进入PyQt事件循环，直到窗口关闭
        success = start_gui()
        
        if not success:
            print("\n❌ GUI启动失败")
            input("按回车键退出...")
            return 1
        
        # GUI正常关闭
        print("\n" + "="*60)
        print("感谢使用 MY-DOGE BIO-MONITOR")
        print("="*60 + "\n")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断，程序退出")
        return 130
    except Exception as e:
        logger.error(f"程序运行发生未预期错误: {e}", exc_info=True)
        print(f"\n❌ 程序运行发生错误: {e}")
        input("按回车键退出...")
        return 1

if __name__ == "__main__":
    # 设置当前工作目录为脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 运行主程序
    exit_code = main()
    sys.exit(exit_code)
