# MY-DOGE Biometric Analysis System (MBAS)

**个人生物信息量化监测系统 - 内务部健康管理平台**

## 📋 项目概述

MY-DOGE Biometric Analysis System (MBAS) 是一个专业的个人健康监测与分析平台，采用军事化管理理念，通过量化生物特征指标、AI智能分析和可视化报告，为用户提供全面的健康状态评估和战术建议。

**核心价值**：将主观健康感受转化为客观数据指标，通过AI分析提供可执行的健康管理方案。

## 🎯 核心功能概览

| 功能模块 | 核心能力 | 技术实现 |
|---------|---------|---------|
| **数据采集** | 多维度生物特征录入（睡眠、HRV、代谢指标） | PyQt6 GUI + SQLite数据库 |
| **AI分析** | DeepSeek API智能健康报告生成 | OpenAI客户端 + 自定义提示词工程 |
| **可视化** | 实时KPI仪表盘 + 趋势图表 | Matplotlib + PyQt6集成 |
| **数据管理** | 双数据库CRUD操作 + CSV导入导出 | SQLite + Pandas数据处理 |
| **规则引擎** | 自动健康状态评估 + 对冲建议 | 基于阈值的规则系统 |

## 🏗️ 系统架构

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    MY-DOGE Biometric Analysis System         │
├──────────────┬────────────────┬─────────────────────────────┤
│   数据层     │   业务层        │       表示层                │
├──────────────┼────────────────┼─────────────────────────────┤
│ bio_data.db  │ BioStrategist  │  BioDashboard (PyQt6 GUI)   │
│ health_monitor.db │ HealthAnalyst  │  DatabaseManager         │
│ CSV文件      │ RuleEngine     │  CLI命令行工具              │
└──────────────┴────────────────┴─────────────────────────────┘
        │               │                    │
        ▼               ▼                    ▼
┌──────────────┐ ┌──────────────┐ ┌─────────────────────┐
│  数据持久化  │ │ AI分析引擎    │ │  多模态用户交互     │
│  双数据库冗余│ │ 自动对冲规则  │ │  实时可视化反馈    │
│  数据备份恢复│ │ 熔断机制      │ │  响应式界面设计    │
└──────────────┘ └──────────────┘ └─────────────────────┘
```

### 目录结构

```
MY-DOGE-HEALTH/
├── main.py                    # CLI主入口点
├── run_bio_monitor.py        # GUI启动器
├── models_config.json        # API配置文件（从模板创建）
├── models_config.template    # 配置模板文件
├── requirements.txt          # Python依赖列表
├── README.md                 # 项目文档
├── data/                     # 数据库存储目录
│   ├── bio_data.db          # 主数据库（完整记录）
│   └── health_monitor.db    # 兼容数据库（核心指标）
├── reports/                  # AI报告输出目录
└── src/                      # 源代码目录
    ├── bio/                  # 生物特征分析模块
    │   ├── bio_strategist.py # AI策略分析师（核心逻辑）
    │   ├── analytics.py      # 统计分析工具
    │   └── database.py       # bio_data.db管理
    ├── health/              # 健康数据管理模块
    │   ├── config.py        # 配置管理系统
    │   ├── database.py      # health_monitor.db管理
    │   ├── analyst.py       # 基础分析引擎
    │   ├── entry.py         # 数据录入工具
    │   └── __init__.py
    └── interface/           # 用户界面模块
        ├── bio_dashboard.py # PyQt6主仪表板
        └── database_manager.py # 数据库管理界面
```

## 🔧 核心模块详解

### 1. 生物特征分析模块 (`src/bio/`)

#### `bio_strategist.py` - AI策略分析师
**职责**：集成DeepSeek API，生成军事化风格的健康报告
**关键功能**：
- 数据预处理和上下文构建
- AI提示词工程和API调用
- 报告后处理和规则应用
- 熔断机制实现（HRV < 40ms触发紧急警报）

#### `analytics.py` - 统计分析工具
**职责**：历史数据分析和干预措施效能评估
**关键功能**：
- 指标相关性计算
- 干预措施效果量化
- 趋势分析和模式识别

#### `database.py` - 主数据库管理
**职责**：管理`bio_data.db`的完整数据记录
**关键功能**：
- 数据库初始化和Schema管理
- 数据CRUD操作（支持UPSERT）
- 历史数据查询和统计
- 干预措施数据导出

### 2. 健康数据管理模块 (`src/health/`)

#### `config.py` - 配置管理系统
**职责**：统一管理API配置、健康目标和系统设置
**关键功能**：
- 四级配置优先级（命令行 > 环境变量 > 配置文件 > 默认值）
- Profile管理和热重载
- 代理设置和网络配置
- 健康指标阈值管理

#### `analyst.py` - 基础分析引擎
**职责**：当API不可用时提供基于规则的基础分析
**关键功能**：
- 熔断机制检查
- 趋势数据准备
- 基础报告生成
- 数据验证和范围检查

#### `entry.py` - 数据录入工具
**职责**：提供命令行数据录入功能
**关键功能**：
- 交互式数据输入
- CSV批量导入
- 数据验证和格式化
- 衍生字段计算

### 3. 用户界面模块 (`src/interface/`)

#### `bio_dashboard.py` - 主仪表板
**职责**：提供完整的图形化数据录入和监控界面
**关键功能**：
- 响应式数据录入表单
- 实时KPI仪表盘（进度条+图表）
- 多线程报告生成（防止界面冻结）
- 历史数据自动填充
- 干预措施追踪界面

#### `database_manager.py` - 数据库管理界面
**职责**：可视化数据库操作工具
**关键功能**：
- 双数据库统一管理
- 记录CRUD操作
- CSV导入导出
- 报告内容查看器

## 🔌 后端API调用详解

### DeepSeek API集成架构

```
数据准备 → 提示词工程 → API调用 → 响应处理 → 报告生成
    │           │           │          │          │
    ▼           ▼           ▼          ▼          ▼
本地数据   系统提示词   OpenAI客户端  JSON解析   格式化输出
验证过滤   用户上下文   代理支持     错误处理   规则应用
```

### API调用流程

1. **客户端初始化** (`bio_strategist.py` / `health/analyst.py`)
```python
# 支持代理的客户端初始化
if config.proxy_settings.get("enabled", False):
    import httpx
    proxy_url = config.proxy_settings.get("url")
    http_client = httpx.Client(
        proxies={"http://": proxy_url, "https://": proxy_url},
        timeout=30.0
    )
    self.client = OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        http_client=http_client
    )
else:
    self.client = OpenAI(
        api_key=config.api_key,
        base_url=config.base_url
    )
```

2. **提示词工程** (`BioStrategist._prepare_prompt_data()`)
```python
system_prompt = """你是MY-DOGE政府的内务部部长兼首席军医...
报告格式要求：
1. 报告标题格式必须为'YYYY-MM-DD_一句话总结核心战备状态'
2. 核心战备状态（红/黄/绿三级警报）
3. 各系统诊断（睡眠、神经、代谢系统）
4. 具体战术建议
5. 量化任务对冲建议"""

user_prompt = f"""
【当日核心数据】
日期: {data['date']}
体重: {data['weight']}kg (目标: <93.0kg)
HRV时序: {data['hrv_0000']}→{data['hrv_0400']}→{data['hrv_0800']}ms
深度睡眠: {data['deep_sleep_ratio']:.1%}
疲劳评分: {data['fatigue_score']}/10

【7日趋势分析】
{trend_analysis}

请生成健康战备报告。"""
```

3. **API调用执行**
```python
response = self.client.chat.completions.create(
    model=self.config.model,  # 如 'deepseek-chat', 'deepseek-reasoner'
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    stream=False,
    temperature=0.3,  # 低温度保证输出一致性
    max_tokens=1500   # 控制报告长度
)

ai_report = response.choices[0].message.content
```

4. **错误处理和回退机制**
```python
try:
    # API调用尝试
    report = self._call_deepseek_api(prompt)
    return {
        'success': True,
        'report_type': 'ai_analysis',
        'report_content': report
    }
except Exception as e:
    logger.error(f"API调用失败: {e}")
    # 回退到基于规则的基础报告
    return self._generate_basic_report(data)
```

### 配置管理系统

系统支持多级配置，优先级从高到低：

1. **命令行参数** (`--api-key`, `--model`, `--base-url`)
2. **环境变量** (`DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`)
3. **配置文件** (`models_config.json`)
4. **默认值** (hardcoded defaults)

**配置文件示例** (`models_config.json`):
```json
{
  "profiles": [
    {
      "name": "🚀 DeepSeek Chat (Standard)",
      "base_url": "https://api.deepseek.com",
      "model": "deepseek-chat",
      "api_key": "sk-xxxxxxxxxxxxxxxx"
    },
    {
      "name": "🧠 DeepSeek Reasoner (R1 - Pro)",
      "base_url": "https://api.deepseek.com",
      "model": "deepseek-reasoner",
      "api_key": "sk-xxxxxxxxxxxxxxxx"
    },
    {
      "name": "💻 LM Studio (Local)",
      "base_url": "http://localhost:1234/v1",
      "model": "local-model",
      "api_key": "not-needed"
    }
  ],
  "default_profile": "🚀 DeepSeek Chat (Standard)",
  "health_metrics": {
    "weight": {
      "name": "体重",
      "unit": "kg",
      "target": 93.0,
      "type": "max"
    },
    "deep_sleep": {
      "name": "深度睡眠占比",
      "unit": "%",
      "target": 0.15,
      "type": "min"
    },
    "hrv": {
      "name": "HRV_0800",
      "unit": "ms",
      "target": 60.0,
      "type": "min"
    }
  },
  "proxy_settings": {
    "enabled": false,
    "url": "http://127.0.0.1:7890"
  },
  "macro_settings": {
    "lookback_days": 120,
    "volatility_window": 20
  }
}
```

## 🚀 快速开始指南

### 环境准备

```bash
# 1. 克隆项目
git clone <repository-url>
cd MY-DOGE-HEALTH

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建配置文件
cp models_config.template models_config.json
# 编辑models_config.json，添加你的API密钥
```

### 数据库初始化

```bash
# 方法1：通过CLI初始化
python main.py --init

# 方法2：通过GUI初始化（首次运行会自动初始化）
python run_bio_monitor.py
```

### 启动系统

#### GUI模式（推荐）
```bash
python run_bio_monitor.py
```
**界面说明**：
- **左侧录入区**：每日生物特征数据录入
- **右侧情报区**：AI报告 + KPI仪表盘 + 趋势图表
- **顶部菜单**：数据库管理、设置、导出功能

#### CLI模式
```bash
# 交互式数据录入
python main.py --entry

# 生成今日健康报告
python main.py --report

# 查看数据库记录
python main.py --view

# 配置管理
python main.py --list-profiles
python main.py --validate-config
python main.py --show-config
```

### 数据录入流程

1. **每日数据采集**（建议早晨完成）
   - 记录前一晚的睡眠数据
   - 测量晨起体重
   - 评估主观疲劳度（1-10分）
   - 记录HRV值（如有设备）

2. **系统数据录入**
   ```bash
   # GUI方式：运行 run_bio_monitor.py，填写表单后点击"提交并生成报告"
   
   # CLI方式：
   python main.py --entry
   # 按提示输入各项数据
   ```

3. **报告查看与应用**
   - 查看AI生成的健康战备报告
   - 关注红/黄/绿警报状态
   - 执行对应的战术建议
   - 根据量化对冲建议调整当日工作强度

## 📊 数据模型与数据库设计

### 主数据库 Schema (`bio_data.db`)

```sql
CREATE TABLE biometric_logs (
    date DATE PRIMARY KEY,
    timestamp TEXT,               -- 报告生成时间 'HH:MM:SS'
    tags TEXT,                    -- 标签 'health,deepseek'
    analyst TEXT,                 -- 分析师 'deepseek-reasoner'
    total_sleep_min INTEGER,      -- 总睡眠分钟
    deep_sleep_min INTEGER,       -- 深度睡眠分钟
    deep_sleep_ratio REAL,        -- 深度睡眠占比（自动计算）
    hrv_0000 INTEGER,             -- 0点 HRV
    hrv_0400 INTEGER,             -- 4点 HRV（巅峰修复）
    hrv_0800 INTEGER,             -- 8点 HRV（苏醒状态）
    hrv_1200 INTEGER,             -- 12点 HRV（日间恢复）
    weight REAL,                  -- 体重（目标 < 93kg）
    fatigue_score INTEGER,        -- 主观疲劳度 1-10
    carb_limit_check BOOLEAN,     -- 睡前4小时禁碳水执行状态
    interventions TEXT,           -- 干预措施，逗号分隔
    title TEXT,                   -- 报告标题
    report_content TEXT           -- AI生成的完整报告
);

-- 索引优化
CREATE INDEX idx_date ON biometric_logs(date);
CREATE INDEX idx_weight ON biometric_logs(weight);
CREATE INDEX idx_deep_sleep_ratio ON biometric_logs(deep_sleep_ratio);
CREATE INDEX idx_analyst ON biometric_logs(analyst);
```

### 数据流架构

```
原始数据 → 数据验证 → 数据库存储 → AI分析 → 报告生成 → 可视化展示
   │          │          │          │          │          │
用户输入   范围检查   UPSERT操作  API调用   格式处理   图表渲染
   │          │          │          │          │          │
   └──────────┴──────────┴──────────┴──────────┴──────────┘
                    数据持久化和状态同步
```

## 🛡️ 自动对冲规则系统

### 规则引擎设计

系统内置智能规则引擎，根据生理数据自动调整建议：

#### 规则1：深度睡眠不足警报
- **触发条件**：`deep_sleep_min < 45` 且 `hrv_0800 < 50`
- **执行动作**：今日脑力任务难度下调30%
- **建议措施**：增加NSDR或冥想干预

#### 规则2：体重超标对冲
- **触发条件**：`weight > 93.0`
- **执行动作**：启动内务部紧急预案
- **具体措施**：冷水洗脸 + 哺乳动物潜水反射

#### 规则3：HRV异常高值检测
- **触发条件**：`hrv_0400 > 120`（异常生理修复尖峰）
- **执行动作**：减少高压演练，增加恢复时间
- **建议**：检查睡眠环境，避免过度刺激

### 熔断机制（紧急保护）

#### 红色警报（系统崩溃边缘）
- **触发条件**：`hrv_0800 < 40`
- **警报信息**：🔴 "系统处于崩溃边缘。立即停止开发，执行物理冷却。"
- **强制措施**：暂停所有开发工作，强制休息

#### 黄色警告（功能受损）
- **触发条件**：`40 <= hrv_0800 < 50`
- **警告信息**：🟡 "HRV值偏低，建议降低当日量化开发强度。"
- **建议措施**：降低工作强度50%，增加休息间隔

## 🔍 监控指标说明

### 核心健康指标

| 指标 | 正常范围 | 目标值 | 测量时间 | 生理意义 |
|------|---------|-------|---------|---------|
| **体重** | <93.0kg | 90.0kg | 早晨空腹 | 代谢状态和能量平衡 |
| **总睡眠** | 7-9小时 | 8小时 | 每日记录 | 生理恢复基础 |
| **深度睡眠占比** | >15% | >20% | 每日记录 | 生理修复质量 |
| **HRV_0000** | 50-100ms | >60ms | 凌晨0点 | 基础自主神经张力 |
| **HRV_0400** | 60-120ms | >80ms | 凌晨4点 | 生理修复尖峰 |
| **HRV_0800** | 50-100ms | >60ms | 早晨8点 | 日间功能状态 |
| **疲劳评分** | 1-10分 | <4分 | 主观评估 | 主观恢复感受 |

### 衍生计算指标

1. **HRV变化量**：`hrv_delta = hrv_0800 - hrv_0000`
   - 正值表示夜间恢复良好
   - 负值表示夜间恢复不足

2. **深度睡眠效率**：`deep_sleep_ratio = deep_sleep_min / total_sleep_min`
   - 反映睡眠质量核心指标
   - 与HRV恢复相关性最高

3. **综合健康评分**：基于多个指标的加权计算
   - 用于长期趋势追踪
   - 支持历史对比分析

## 🛠️ 开发与扩展

### 添加新的健康指标

1. **更新数据模型**：
```python
# 在src/bio/database.py中扩展Schema
ALTER TABLE biometric_logs ADD COLUMN new_metric REAL;
```

2. **更新界面组件**：
```python
# 在src/interface/bio_dashboard.py中添加输入控件
self.new_metric_input = QDoubleSpinBox()
layout.addWidget(QLabel("新指标:"), self.new_metric_input)
```

3. **更新AI提示词**：
```python
# 在src/bio/bio_strategist.py中更新上下文
context += f"新指标: {data['new_metric']}\n"
```

4. **更新配置系统**：
```json
// 在models_config.json中添加阈值
"health_metrics": {
  "new_metric": {
    "name": "新指标名称",
    "unit": "单位",
    "target": 目标值,
    "type": "min|max"
  }
}
```

### 集成新的AI模型

1. **添加Profile配置**：
```json
{
  "name": "🤖 New AI Provider",
  "base_url": "https://api.new-ai.com/v1",
  "model": "new-model",
  "api_key": "your-api-key"
}
```

2. **扩展客户端适配**（如果需要）：
```python
# 在BioStrategist中添加特定模型的提示词调整
if "new-model" in self.config.model:
    system_prompt = self._prepare_new_model_prompt(data)
```

### 数据导出与集成

1. **CSV导出**：通过数据库管理器界面导出完整数据
2. **API接口**：可扩展REST API供外部系统调用
3. **Webhook支持**：可添加数据变化时的webhook通知

## 🔧 故障排除

### 常见问题解决

| 问题现象 | 可能原因 | 解决方案 |
|---------|---------|---------|
| API调用失败 | 1. API密钥错误<br>2. 网络连接问题<br>3. 代理配置错误 | 1. `python main.py --validate-config`<br>2. 检查网络连通性<br>3. 确认代理设置正确 |
| 数据库错误 | 1. 文件权限问题<br>2. Schema不匹配<br>3. 磁盘空间不足 | 1. 检查data/目录权限<br>2. 重新初始化数据库<br>3. 清理磁盘空间 |
| GUI启动失败 | 1. PyQt6未安装<br>2. 显示驱动问题<br>3. 依赖冲突 | 1. `pip install PyQt6`<br>2. 检查显示设置<br>3. 重新安装依赖 |
| 报告生成缓慢 | 1. API响应延迟<br>2. 网络速度慢<br>3. 本地资源不足 | 1. 使用本地模型<br>2. 调整超时设置<br>3. 关闭其他占用程序 |

### 日志分析

系统日志记录在以下位置：
- **应用日志**：控制台输出 + 可配置的日志文件
- **错误追踪**：详细的异常堆栈信息
- **API调用日志**：请求/响应时间和状态码

查看日志：
```bash
# 实时监控日志
python main.py --verbose

# 查看API调用统计
grep "API调用" mbas.log | tail -20
```

## 📈 性能优化建议

### 数据库优化

1. **索引策略**：
   - 为常用查询字段建立索引
   - 定期分析查询性能
   - 考虑分区表处理历史数据

2. **数据清理**：
   ```sql
   -- 定期清理180天前的数据
   DELETE FROM biometric_logs 
   WHERE date < date('now', '-180 days');
   ```

### API调用优化

1. **批量处理**：
   ```python
   # 批量生成多日报告（待实现）
   def generate_batch_reports(self, date_range):
       for date in date_range:
           report = self.generate_daily_report(date)
           # 批量保存
   ```

2. **缓存机制**：
   ```python
   # 实现报告缓存（待实现）
   cache_key = f"report_{date}_{hash(data)}"
   if cache_key in report_cache:
       return report_cache[cache_key]
   ```

### 内存管理

1. **分页加载**：
   ```python
   # 大数据集分页显示
   LIMIT = 100
   OFFSET = page * LIMIT
   ```

2. **资源释放**：
   ```python
   # 及时释放matplotlib图形资源
   plt.close('all')
   ```

## 🔐 安全与隐私

### 数据保护措施

1. **本地存储**：所有健康数据存储在本地SQLite数据库
2. **可选API**：AI分析功能可完全禁用，纯本地运行
3. **数据加密**：支持导出时的数据加密（待实现）
4. **访问控制**：文件系统级权限管理

### API密钥安全

1. **环境变量优先**：建议使用环境变量存储敏感信息
   ```bash
   export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxx"
   python run_bio_monitor.py
   ```

2. **配置文件保护**：`models_config.json`已加入`.gitignore`
3. **密钥轮换**：支持定期更新API密钥而不影响历史数据

### 隐私合规

1. **数据所有权**：用户完全拥有自己的健康数据
2. **导出控制**：用户可随时导出或删除所有数据
3. **匿名分析**：支持导出匿名化数据用于统计分析

## 🚀 未来发展路线图

### 短期计划（v1.1-v1.3）

1. **移动端应用**：iOS/Android数据录入客户端
2. **自动化数据采集**：集成Apple Health/Google Fit
3. **高级分析仪表板**：更多统计图表和预测分析
4. **多用户支持**：家庭或团队健康管理

### 中期计划（v2.0）

1. **机器学习模型**：基于历史数据的个性化预测
2. **实时警报系统**：基于可穿戴设备的实时监控
3. **健康社交功能**：匿名健康数据对比和挑战
4. **专业医疗对接**：数据导出为医疗报告格式

### 长期愿景

1. **全面健康操作系统**：整合饮食、运动、睡眠全维度
2. **预防性健康管理**：基于遗传和生活方式的风险预测
3. **智能干预推荐**：基于AI的个性化健康改善方案
4. **开放平台**：第三方应用和设备的标准化接入

## 🤝 贡献指南

欢迎参与MY-DOGE项目开发！

### 开发环境设置

1. **Fork仓库**并克隆到本地
2. **创建虚拟环境**：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. **安装开发依赖**：
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # 开发工具
   ```

### 代码规范

1. **Python代码风格**：遵循PEP 8规范
2. **文档要求**：所有公共函数必须有docstring
3. **测试覆盖**：新功能需要包含单元测试
4. **提交信息**：使用约定式提交格式

### 提交流程

1. 创建功能分支：`git checkout -b feature/your-feature`
2. 编写代码并添加测试
3. 运行测试：`pytest tests/`
4. 提交更改：`git commit -m "feat: add new feature"`
5. 推送到分支：`git push origin feature/your-feature`
6. 创建Pull Request

## 📄 许可证

本项目采用 **Apache 2.0 许可证** - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与反馈

- **问题报告**：通过GitHub Issues提交bug或功能请求
- **使用问题**：查看本文档的故障排除部分
- **功能建议**：欢迎提出改进建议和使用场景

**免责声明**：本系统为个人健康管理工具，不替代专业医疗建议。如有健康问题，请咨询专业医疗人员。

---

*最后更新: 2025-12-24 | 系统版本: 1.0.0 | 文档版本: 2.0.0*  
*作者: wsman (wsman0325@gmail.com)*  
*项目状态: 🟢 积极维护中*
