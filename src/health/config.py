import os
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class ProfileConfig:
    """API配置profile"""
    name: str
    base_url: str
    model: str
    api_key: str

@dataclass
class MetricConfig:
    """健康指标配置"""
    name: str
    unit: str
    target: float
    type: str  # 'min' or 'max'

@dataclass
class HealthConfig:
    """健康监测系统配置类"""
    
    # 配置文件和路径
    config_file: Optional[str] = None  # 配置文件路径，如果为None则从环境变量或默认路径加载
    
    # 数据库配置
    db_path: str = "data/health_monitor.db"
    
    # API配置（从配置文件加载）
    profile_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    
    # 报告配置
    report_output_dir: str = "reports"
    default_report_days: int = 7
    
    # 健康目标阈值（默认值，会被配置文件覆盖）
    weight_target_max: float = 93.0  # 体重目标上限（kg）
    deep_sleep_ratio_min: float = 0.15  # 深度睡眠最小占比
    hrv_critical_threshold: int = 40  # HRV临界阈值（ms）
    hrv_warning_threshold: int = 50   # HRV警告阈值（ms）
    
    # 数据验证范围
    weight_min: float = 0
    weight_max: float = 200
    sleep_min_min: int = 0
    sleep_max_min: int = 1440  # 24小时
    hrv_min: int = 0
    hrv_max: int = 200
    fatigue_score_min: int = 1
    fatigue_score_max: int = 10
    
    # 从models_config.json加载的配置
    profiles: List[ProfileConfig] = field(default_factory=list)
    default_profile: str = "🚀 DeepSeek Chat (Standard)"
    macro_settings: Dict[str, Any] = field(default_factory=lambda: {"lookback_days": 120, "volatility_window": 20})
    health_metrics: Dict[str, MetricConfig] = field(default_factory=dict)
    proxy_settings: Dict[str, Any] = field(default_factory=lambda: {"enabled": False, "url": "http://127.0.0.1:7890"})
    
    def __post_init__(self):
        """初始化后处理"""
        # 确定配置文件路径（优先级：实例参数 > 环境变量 > 默认值）
        if self.config_file is None:
            self.config_file = os.getenv("MBAS_CONFIG_PATH", "models_config.json")
        
        # 加载优先级：配置文件 > 环境变量 > 默认值
        self._load_from_config_file()
        self._load_from_env()
        
        # 应用选择的profile（如果有）
        self._apply_selected_profile()
    
    def _load_from_config_file(self):
        """从配置文件加载配置"""
        # 确保config_file不为None
        config_file = self.config_file or "models_config.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 加载profiles
                self.profiles = []
                for profile_data in config_data.get("profiles", []):
                    profile = ProfileConfig(
                        name=profile_data.get("name", ""),
                        base_url=profile_data.get("base_url", ""),
                        model=profile_data.get("model", ""),
                        api_key=profile_data.get("api_key", "")
                    )
                    self.profiles.append(profile)
                
                # 加载其他配置
                self.default_profile = config_data.get("default_profile", self.default_profile)
                self.macro_settings = config_data.get("macro_settings", self.macro_settings)
                
                # 加载健康指标
                self.health_metrics = {}
                metrics_data = config_data.get("health_metrics", {})
                for key, data in metrics_data.items():
                    self.health_metrics[key] = MetricConfig(
                        name=data.get("name", ""),
                        unit=data.get("unit", ""),
                        target=float(data.get("target", 0)),
                        type=data.get("type", "max")
                    )
                
                # 更新内部阈值（如果配置文件中存在）
                if 'weight' in self.health_metrics:
                    self.weight_target_max = self.health_metrics['weight'].target
                if 'deep_sleep' in self.health_metrics:
                    self.deep_sleep_ratio_min = self.health_metrics['deep_sleep'].target
                # HRV阈值暂时保留硬编码或从环境变量加载，因为配置文件中只有一个HRV目标
                
                # 加载代理设置
                self.proxy_settings = config_data.get("proxy_settings", self.proxy_settings)
                
                print(f"✅ 配置文件加载成功: {config_file}")
                
            except json.JSONDecodeError as e:
                print(f"❌ 配置文件格式错误 {config_file}: {e}")
                print(f"   请确保文件是有效的JSON格式")
            except Exception as e:
                print(f"❌ 加载配置文件 {config_file} 失败: {e}")
        else:
            print(f"⚠️  配置文件不存在: {config_file}")
            print(f"   请创建配置文件或设置MBAS_CONFIG_PATH环境变量")
            print(f"   可以使用模板: cp models_config.template.json {config_file}")
    
    def _load_from_env(self):
        """从环境变量加载配置（覆盖配置文件）"""
        # DeepSeek API配置
        env_api_key = os.getenv("DEEPSEEK_API_KEY")
        if env_api_key:
            self.api_key = env_api_key
        
        env_base_url = os.getenv("DEEPSEEK_BASE_URL")
        if env_base_url:
            self.base_url = env_base_url
        
        env_model = os.getenv("DEEPSEEK_MODEL")
        if env_model:
            self.model = env_model
        
        # 报告配置
        env_report_dir = os.getenv("MBAS_REPORT_DIR")
        if env_report_dir:
            self.report_output_dir = env_report_dir
        
        # 健康目标（可自定义）
        env_weight_target = os.getenv("MBAS_WEIGHT_TARGET")
        if env_weight_target:
            try:
                self.weight_target_max = float(env_weight_target)
            except ValueError:
                pass
        
        env_hrv_critical = os.getenv("MBAS_HRV_CRITICAL")
        if env_hrv_critical:
            try:
                self.hrv_critical_threshold = int(env_hrv_critical)
            except ValueError:
                pass
        
        # 代理设置（环境变量覆盖）
        env_proxy_enabled = os.getenv("MBAS_PROXY_ENABLED")
        if env_proxy_enabled:
            self.proxy_settings["enabled"] = env_proxy_enabled.lower() in ("true", "1", "yes")
        
        env_proxy_url = os.getenv("MBAS_PROXY_URL")
        if env_proxy_url:
            self.proxy_settings["url"] = env_proxy_url
    
    def _apply_selected_profile(self):
        """应用选择的profile配置"""
        # 如果没有指定profile，使用默认profile
        target_profile_name = self.profile_name or self.default_profile
        
        # 查找匹配的profile
        for profile in self.profiles:
            if profile.name == target_profile_name:
                # 仅当没有环境变量覆盖时应用profile配置
                if not os.getenv("DEEPSEEK_API_KEY") and not self.api_key:
                    self.api_key = profile.api_key
                if not os.getenv("DEEPSEEK_BASE_URL"):
                    self.base_url = profile.base_url
                if not os.getenv("DEEPSEEK_MODEL"):
                    self.model = profile.model
                break
    
    def set_profile(self, profile_name: str) -> bool:
        """设置当前使用的profile"""
        for profile in self.profiles:
            if profile.name == profile_name:
                self.profile_name = profile_name
                self._apply_selected_profile()
                return True
        return False
    
    def get_current_profile(self) -> Optional[ProfileConfig]:
        """获取当前使用的profile"""
        target_profile_name = self.profile_name or self.default_profile
        for profile in self.profiles:
            if profile.name == target_profile_name:
                return profile
        return None
    
    def get_proxy_dict(self) -> Optional[Dict[str, str]]:
        """获取代理配置字典（如果启用）"""
        if self.proxy_settings.get("enabled", False):
            url = self.proxy_settings.get("url")
            if url and isinstance(url, str):
                return {
                    "http": url,
                    "https": url
                }
        return None
    
    def validate_config(self, verbose: bool = False) -> bool:
        """验证配置有效性
        
        Args:
            verbose: 是否显示详细信息
            
        Returns:
            配置是否有效
        """
        errors = []
        warnings = []
        
        # 1. 检查API配置
        if not self.api_key:
            errors.append("未设置DeepSeek API Key（可通过环境变量DEEPSEEK_API_KEY或配置文件设置）")
        elif len(self.api_key) < 10:
            warnings.append("API密钥可能过短或无效")
        
        # 2. 检查配置文件加载状态
        if not self.profiles:
            warnings.append("未加载任何配置profile，请检查配置文件或环境变量设置")
        
        # 3. 检查当前profile
        current_profile = self.get_current_profile()
        if current_profile is None and self.profiles:
            errors.append(f"默认profile '{self.default_profile}' 不存在于配置文件中")
        elif current_profile is not None:
            if verbose:
                print(f"当前使用的profile: {current_profile.name}")
        
        # 4. 检查健康目标阈值
        if self.weight_target_max <= 0:
            errors.append(f"体重目标必须大于0，当前为{self.weight_target_max}")
        elif self.weight_target_max < 50:
            warnings.append(f"体重目标设置过低 ({self.weight_target_max}kg)，请确认")
        
        if self.hrv_critical_threshold <= 0:
            errors.append(f"HRV临界阈值必须大于0，当前为{self.hrv_critical_threshold}")
        
        if self.hrv_warning_threshold <= self.hrv_critical_threshold:
            errors.append(f"HRV警告阈值({self.hrv_warning_threshold})必须大于临界阈值({self.hrv_critical_threshold})")
        
        # 5. 检查代理配置
        if self.proxy_settings.get("enabled", False):
            proxy_url = self.proxy_settings.get("url", "")
            if not proxy_url:
                errors.append("代理已启用但未设置代理URL")
            elif not proxy_url.startswith(("http://", "https://")):
                warnings.append(f"代理URL格式可能不正确: {proxy_url}")
        
        # 6. 检查数据库路径
        db_path = self.get_db_absolute_path()
        if not os.path.exists(os.path.dirname(db_path)):
            warnings.append(f"数据库目录不存在: {os.path.dirname(db_path)}")
        
        # 7. 检查报告目录
        if not os.path.exists(self.report_output_dir):
            warnings.append(f"报告输出目录不存在: {self.report_output_dir}")
        
        # 输出结果
        if errors:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            
            if warnings and verbose:
                print("\n⚠️  配置警告:")
                for warning in warnings:
                    print(f"  - {warning}")
            return False
        else:
            if verbose:
                print("✅ 配置验证通过")
                if warnings:
                    print("\n⚠️  配置警告（不影响运行）:")
                    for warning in warnings:
                        print(f"  - {warning}")
                else:
                    print("  无警告")
            
            return True
    
    def get_db_absolute_path(self) -> str:
        """获取数据库绝对路径"""
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(current_dir, '..', self.db_path)
    
    def show_config_summary(self):
        """显示配置摘要"""
        print(f"\n{'='*60}")
        print("MY-DOGE 配置摘要")
        print(f"{'='*60}")
        
        # 配置文件信息
        config_file = self.config_file or "models_config.json"
        if os.path.exists(config_file):
            print(f"📄 配置文件: {config_file} (存在)")
        else:
            print(f"📄 配置文件: {config_file} (不存在)")
        
        # API配置
        current_profile = self.get_current_profile()
        if current_profile:
            print(f"📋 当前profile: {current_profile.name}")
            print(f"  模型: {self.model}")
            print(f"  API地址: {self.base_url}")
            api_key_display = f"{self.api_key[:10]}..." if self.api_key and len(self.api_key) > 10 else "未设置"
            print(f"  API密钥: {api_key_display}")
        else:
            print(f"📋 当前profile: 无")
            print(f"  模型: {self.model}")
            print(f"  API地址: {self.base_url}")
            print(f"  API密钥: {'未设置' if not self.api_key else '已设置'}")
        
        # 加载的profiles数量
        print(f"📊 加载的profiles: {len(self.profiles)}个")
        
        # 健康目标
        print(f"🎯 健康目标:")
        print(f"  体重上限: {self.weight_target_max}kg")
        print(f"  HRV临界阈值: {self.hrv_critical_threshold}ms")
        print(f"  HRV警告阈值: {self.hrv_warning_threshold}ms")
        
        # 代理设置
        proxy_enabled = self.proxy_settings.get("enabled", False)
        print(f"🔗 代理设置: {'启用' if proxy_enabled else '禁用'}")
        if proxy_enabled:
            print(f"  代理URL: {self.proxy_settings.get('url', 'N/A')}")
        
        # 目录设置
        print(f"📁 目录设置:")
        print(f"  数据库: {self.db_path}")
        print(f"  报告输出: {self.report_output_dir}")
        
        print(f"{'='*60}")
    
    def reload_config(self) -> bool:
        """重新加载配置文件
        
        Returns:
            是否成功重新加载
        """
        print(f"🔄 重新加载配置文件...")
        try:
            # 保存当前profile名称以便恢复
            current_profile_name = None
            if self.profile_name:
                current_profile_name = self.profile_name
            else:
                current_profile = self.get_current_profile()
                if current_profile is not None:
                    current_profile_name = current_profile.name
            
            # 重新加载配置
            self._load_from_config_file()
            self._load_from_env()
            self._apply_selected_profile()
            
            # 恢复之前的profile（如果存在）
            if current_profile_name:
                self.set_profile(current_profile_name)
            
            print(f"✅ 配置文件重新加载成功")
            return True
        except Exception as e:
            print(f"❌ 重新加载配置文件失败: {e}")
            return False
    
    def save_config(self) -> bool:
        """保存当前配置到配置文件
        
        Returns:
            是否成功保存
        """
        config_file = self.config_file or "models_config.json"
        
        try:
            # 读取现有配置文件内容
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                config_data = {}
            
            # 更新健康指标部分
            if not config_data.get("health_metrics"):
                config_data["health_metrics"] = {}
            
            for key, metric in self.health_metrics.items():
                if key not in config_data["health_metrics"]:
                    config_data["health_metrics"][key] = {}
                
                config_data["health_metrics"][key]["name"] = metric.name
                config_data["health_metrics"][key]["unit"] = metric.unit
                config_data["health_metrics"][key]["target"] = metric.target
                config_data["health_metrics"][key]["type"] = metric.type
            
            # 写入配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            
            print(f"✅ 配置文件保存成功: {config_file}")
            return True
            
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
            return False
    
    def update_metric_target(self, metric_key: str, target_value: float) -> bool:
        """更新指定指标的目标值
        
        Args:
            metric_key: 指标键名 (如 'weight', 'deep_sleep', 'hrv')
            target_value: 新的目标值
            
        Returns:
            是否成功更新
        """
        if metric_key not in self.health_metrics:
            print(f"❌ 指标 '{metric_key}' 不存在")
            return False
        
        # 更新内存中的配置
        self.health_metrics[metric_key].target = target_value
        
        # 同时更新内部阈值（兼容性）
        if metric_key == 'weight':
            self.weight_target_max = target_value
        elif metric_key == 'deep_sleep':
            self.deep_sleep_ratio_min = target_value
        
        return True


def get_default_config() -> HealthConfig:
    """获取默认配置实例"""
    return HealthConfig()
