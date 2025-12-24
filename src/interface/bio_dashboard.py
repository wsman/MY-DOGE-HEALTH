import sys
import logging
from datetime import date, datetime
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QDateEdit, QSlider, QCheckBox,
    QGroupBox, QTextBrowser, QProgressBar, QSpinBox, QDoubleSpinBox,
    QMessageBox, QTabWidget, QSplitter, QFrame, QComboBox,
    QApplication, QDialog
)
from PyQt6.QtCore import Qt, QDate, pyqtSlot, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPalette, QColor
import re

# Matplotlib for charts
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np

# 导入项目模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bio.database import save_daily_log, get_recent_logs, initialize_db, get_intervention_stats
from src.bio.analytics import calculate_correlations, get_intervention_comparison_data, analyze_intervention_effectiveness
from src.bio.bio_strategist import BioStrategist, get_default_strategist
from src.health.config import get_default_config

logger = logging.getLogger(__name__)

class ReportGeneratorThread(QThread):
    """报告生成工作线程"""
    finished_signal = pyqtSignal(dict)  # 发送生成结果
    error_signal = pyqtSignal(str)      # 发送错误信息

    def __init__(self, strategist, data_dict, history_data):
        super().__init__()
        self.strategist = strategist
        self.data_dict = data_dict
        self.history_data = history_data

    def run(self):
        try:
            # 生成报告（耗时操作）
            report_result = self.strategist.generate_health_report(self.data_dict, self.history_data)
            self.finished_signal.emit(report_result)
        except Exception as e:
            logger.error(f"生成报告线程出错: {e}", exc_info=True)
            self.error_signal.emit(str(e))

class SleepInputWidget(QWidget):
    """睡眠输入组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QGridLayout()
        
        # 总睡眠时长（小时和分钟）
        layout.addWidget(QLabel("总睡眠时长:"), 0, 0)
        self.total_sleep_hours = QSpinBox()
        self.total_sleep_hours.setRange(0, 23)
        self.total_sleep_hours.setValue(7)
        self.total_sleep_hours.setSuffix(" 小时")
        layout.addWidget(self.total_sleep_hours, 0, 1)
        
        self.total_sleep_minutes = QSpinBox()
        self.total_sleep_minutes.setRange(0, 59)
        self.total_sleep_minutes.setValue(30)
        self.total_sleep_minutes.setSuffix(" 分钟")
        layout.addWidget(self.total_sleep_minutes, 0, 2)
        
        # 深度睡眠分钟
        layout.addWidget(QLabel("深度睡眠:"), 1, 0)
        self.deep_sleep_minutes = QSpinBox()
        self.deep_sleep_minutes.setRange(0, 1440)
        self.deep_sleep_minutes.setValue(90)
        self.deep_sleep_minutes.setSuffix(" 分钟")
        layout.addWidget(self.deep_sleep_minutes, 1, 1, 1, 2)
        
        # 计算总分钟标签
        self.total_min_label = QLabel("总分钟: 0")
        layout.addWidget(self.total_min_label, 2, 0, 1, 3)
        
        self.setLayout(layout)
        
        # 连接信号以更新总分钟
        self.total_sleep_hours.valueChanged.connect(self.update_total_minutes)
        self.total_sleep_minutes.valueChanged.connect(self.update_total_minutes)
    
    def update_total_minutes(self):
        """更新总分钟显示"""
        total_min = self.total_sleep_hours.value() * 60 + self.total_sleep_minutes.value()
        self.total_min_label.setText(f"总分钟: {total_min}")
    
    def get_total_sleep_min(self) -> int:
        """获取总睡眠分钟数"""
        return self.total_sleep_hours.value() * 60 + self.total_sleep_minutes.value()
    
    def get_deep_sleep_min(self) -> int:
        """获取深度睡眠分钟数"""
        return self.deep_sleep_minutes.value()
    
    def set_values(self, total_min: int, deep_min: int):
        """设置值"""
        hours = total_min // 60
        minutes = total_min % 60
        self.total_sleep_hours.setValue(hours)
        self.total_sleep_minutes.setValue(minutes)
        self.deep_sleep_minutes.setValue(deep_min)
        self.update_total_minutes()

class HRVInputWidget(QWidget):
    """HRV输入组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QGridLayout()
        
        # 0点 HRV
        layout.addWidget(QLabel("0点 HRV:"), 0, 0)
        self.hrv_0000 = QSpinBox()
        self.hrv_0000.setRange(0, 200)
        self.hrv_0000.setValue(65)
        self.hrv_0000.setSuffix(" ms")
        layout.addWidget(self.hrv_0000, 0, 1)
        
        # 2点 HRV
        layout.addWidget(QLabel("2点 HRV:"), 1, 0)
        self.hrv_0200 = QSpinBox()
        self.hrv_0200.setRange(0, 200)
        self.hrv_0200.setValue(70)
        self.hrv_0200.setSuffix(" ms")
        layout.addWidget(self.hrv_0200, 1, 1)
        
        # 4点 HRV
        layout.addWidget(QLabel("4点 HRV:"), 2, 0)
        self.hrv_0400 = QSpinBox()
        self.hrv_0400.setRange(0, 200)
        self.hrv_0400.setValue(85)
        self.hrv_0400.setSuffix(" ms")
        layout.addWidget(self.hrv_0400, 2, 1)
        
        # 6点 HRV
        layout.addWidget(QLabel("6点 HRV:"), 3, 0)
        self.hrv_0600 = QSpinBox()
        self.hrv_0600.setRange(0, 200)
        self.hrv_0600.setValue(75)
        self.hrv_0600.setSuffix(" ms")
        layout.addWidget(self.hrv_0600, 3, 1)
        
        # 8点 HRV
        layout.addWidget(QLabel("8点 HRV:"), 4, 0)
        self.hrv_0800 = QSpinBox()
        self.hrv_0800.setRange(0, 200)
        self.hrv_0800.setValue(70)
        self.hrv_0800.setSuffix(" ms")
        layout.addWidget(self.hrv_0800, 4, 1)
        
        self.setLayout(layout)
    
    def get_values(self) -> Dict[str, int]:
        """获取HRV值"""
        return {
            'hrv_0000': self.hrv_0000.value(),
            'hrv_0200': self.hrv_0200.value(),
            'hrv_0400': self.hrv_0400.value(),
            'hrv_0600': self.hrv_0600.value(),
            'hrv_0800': self.hrv_0800.value()
        }
    
    def set_values(self, hrv_0000: int, hrv_0200: int, hrv_0400: int, hrv_0600: int, hrv_0800: int):
        """设置HRV值"""
        self.hrv_0000.setValue(hrv_0000)
        self.hrv_0200.setValue(hrv_0200)
        self.hrv_0400.setValue(hrv_0400)
        self.hrv_0600.setValue(hrv_0600)
        self.hrv_0800.setValue(hrv_0800)

class MetabolicInputWidget(QWidget):
    """代谢输入组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QGridLayout()
        
        # 体重输入
        layout.addWidget(QLabel("体重 (kg):"), 0, 0)
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 200)
        self.weight_input.setValue(92.5)
        self.weight_input.setDecimals(1)
        self.weight_input.setSuffix(" kg")
        layout.addWidget(self.weight_input, 0, 1)
        
        # 疲劳度滑块
        layout.addWidget(QLabel("疲劳度 (1-10):"), 1, 0)
        self.fatigue_slider = QSlider(Qt.Orientation.Horizontal)
        self.fatigue_slider.setRange(1, 10)
        self.fatigue_slider.setValue(3)
        self.fatigue_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.fatigue_slider.setTickInterval(1)
        layout.addWidget(self.fatigue_slider, 1, 1)
        
        self.fatigue_label = QLabel("3")
        layout.addWidget(self.fatigue_label, 1, 2)
        
        # 禁碳水复选框
        self.carb_limit_check = QCheckBox("睡前4小时禁碳水")
        self.carb_limit_check.setChecked(True)
        layout.addWidget(self.carb_limit_check, 2, 0, 1, 2)
        
        self.setLayout(layout)
        
        # 连接信号
        self.fatigue_slider.valueChanged.connect(self.fatigue_label.setNum)
    
    def get_values(self) -> Dict[str, Any]:
        """获取代谢值"""
        return {
            'weight': self.weight_input.value(),
            'fatigue_score': self.fatigue_slider.value(),
            'carb_limit_check': self.carb_limit_check.isChecked()
        }
    
    def set_values(self, weight: float, fatigue: int, carb_limit: bool):
        """设置代谢值"""
        self.weight_input.setValue(weight)
        self.fatigue_slider.setValue(fatigue)
        self.carb_limit_check.setChecked(carb_limit)

class InterventionWidget(QWidget):
    """干预措施输入组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QGridLayout()
        
        # 干预措施复选框
        self.cold_water_check = QCheckBox("冷水洗脸")
        self.magnesium_check = QCheckBox("镁补充")
        self.nsdr_check = QCheckBox("NSDR")
        self.meditation_check = QCheckBox("冥想")
        
        layout.addWidget(self.cold_water_check, 0, 0)
        layout.addWidget(self.magnesium_check, 0, 1)
        layout.addWidget(self.nsdr_check, 1, 0)
        layout.addWidget(self.meditation_check, 1, 1)
        
        self.setLayout(layout)
    
    def get_values(self) -> str:
        """获取干预措施值，返回逗号分隔的字符串"""
        interventions = []
        if self.cold_water_check.isChecked():
            interventions.append("冷水洗脸")
        if self.magnesium_check.isChecked():
            interventions.append("镁补充")
        if self.nsdr_check.isChecked():
            interventions.append("NSDR")
        if self.meditation_check.isChecked():
            interventions.append("冥想")
        return ",".join(interventions)
    
    def set_values(self, interventions_str: str):
        """设置干预措施值"""
        interventions = interventions_str.split(',') if interventions_str else []
        self.cold_water_check.setChecked("冷水洗脸" in interventions)
        self.magnesium_check.setChecked("镁补充" in interventions)
        self.nsdr_check.setChecked("NSDR" in interventions)
        self.meditation_check.setChecked("冥想" in interventions)

class ReportDisplayWidget(QTextBrowser):
    """报告显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        # 基础字体设置
        font = QFont("Consolas", 10)
        self.setFont(font)
        
        # 增强的CSS样式 (白底黑字)
        doc = self.document()
        if doc:
            doc.setDefaultStyleSheet("""
                body {
                    font-family: "Consolas", "Microsoft YaHei", monospace;
                    font-size: 11pt;
                    color: #000000;
                    background-color: #ffffff;
                    line-height: 1.6;
                }
                h1 {
                    font-size: 16pt;
                    font-weight: bold;
                    color: #2E7D32;
                    margin-top: 15px;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 5px;
                }
                h2 {
                    font-size: 14pt;
                    font-weight: bold;
                    color: #1565C0;
                    margin-top: 12px;
                    margin-bottom: 8px;
                }
                h3 {
                    font-size: 12pt;
                    font-weight: bold;
                    color: #EF6C00;
                    margin-top: 10px;
                    margin-bottom: 5px;
                }
                p {
                    margin-bottom: 8px;
                }
                ul {
                    margin-top: 0px;
                    margin-bottom: 10px;
                }
                li {
                    margin-bottom: 4px;
                }
                strong {
                    color: #000000;
                    font-weight: bold;
                }
                code {
                    background-color: #f5f5f5;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: "Consolas", monospace;
                    border: 1px solid #ddd;
                }
                hr {
                    border-top: 1px solid #ddd;
                    margin: 15px 0;
                }
                .warning { color: #D32F2F; font-weight: bold; }
                .success { color: #388E3C; font-weight: bold; }
            """)
        
        self.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 15px;
            }
        """)
    
    def display_report(self, report_content: str):
        """显示报告内容"""
        html_content = self._markdown_to_html(report_content)
        self.setHtml(html_content)
    
    def _markdown_to_html(self, markdown: str) -> str:
        """改进的Markdown转HTML解析器"""
        if not markdown:
            return ""
            
        lines = markdown.split('\n')
        html_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            
            # 处理空行
            if not line:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('<br>')
                continue
            
            # 处理标题 (支持 #, ##, ###)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                level = len(header_match.group(1))
                content = header_match.group(2)
                html_lines.append(f'<h{level}>{self._process_inline(content)}</h{level}>')
                continue
            
            # 处理分隔线
            if re.match(r'^[-*_]{3,}$', line):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('<hr>')
                continue
            
            # 处理列表项
            list_match = re.match(r'^[-*]\s+(.+)$', line)
            if list_match:
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                content = list_match.group(1)
                html_lines.append(f'<li>{self._process_inline(content)}</li>')
                continue
            
            # 结束列表
            if in_list:
                html_lines.append('</ul>')
                in_list = False
                
            # 处理普通段落
            html_lines.append(f'<p>{self._process_inline(line)}</p>')
        
        if in_list:
            html_lines.append('</ul>')
            
        return '\n'.join(html_lines)
    
    def _process_inline(self, text: str) -> str:
        """处理行内样式"""
        # 粗体 **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        
        # 代码 `text`
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        
        # 简单的Emoji替换增强显示（可选）
        text = text.replace('🔴', '<span class="warning">🔴</span>')
        text = text.replace('🟢', '<span class="success">🟢</span>')
        
        return text

class KPIDashboardWidget(QWidget):
    """KPI仪表盘组件（包含图表）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.metrics_config = {}
        self.history_data = []  # 存储最近7天的历史数据
        self.setup_ui()
        self.load_history_data()
    
    def set_metrics_config(self, metrics_config: Dict[str, Any]):
        """设置指标配置"""
        self.metrics_config = metrics_config
        self.update_ui_labels()
    
    def update_ui_labels(self):
        """更新界面标签"""
        if not self.metrics_config:
            return
            
        # 更新体重标题标签
        weight_cfg = self.metrics_config.get('weight')
        if weight_cfg:
            self.weight_title_label.setText(f"{weight_cfg.name} (目标 < {weight_cfg.target}{weight_cfg.unit})")
            
        # 更新睡眠标题标签
        sleep_cfg = self.metrics_config.get('deep_sleep')
        if sleep_cfg:
            target_pct = int(sleep_cfg.target * 100)
            self.sleep_title_label.setText(f"{sleep_cfg.name} (目标 > {target_pct}%)")
            
        # 更新HRV标题标签
        hrv_cfg = self.metrics_config.get('hrv')
        if hrv_cfg:
            self.hrv_title_label.setText(f"{hrv_cfg.name} (目标 > {int(hrv_cfg.target)}{hrv_cfg.unit})")
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # 添加边距防止文本被裁剪
        layout.setSpacing(10)  # 增加间距
        
        # ========== 上方：双图表水平布局 ==========
        charts_widget = QWidget()
        charts_layout = QHBoxLayout()
        charts_layout.setContentsMargins(0, 0, 0, 0)
        charts_layout.setSpacing(10)
        
        # 左侧：趋势折线图
        trend_group = QGroupBox("📈 趋势分析 (过去7天)")
        trend_layout = QVBoxLayout()
        trend_layout.setContentsMargins(5, 15, 5, 15)
        
        # 创建matplotlib图形（双轴折线图）- 固定高度
        self.figure = Figure(figsize=(6, 3), dpi=100)  # 调整尺寸以适应水平布局
        self.canvas = FigureCanvas(self.figure)
        
        # 设置图形样式和中文字体
        self.figure.patch.set_facecolor('#f5f5f5')
        
        # 设置matplotlib中文字体
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        
        # 创建两个子图（共享x轴）
        self.ax1 = self.figure.add_subplot(111)
        self.ax2 = self.ax1.twinx()  # 创建第二个y轴
        
        # 初始空图表
        self.ax1.set_xlabel('日期', fontsize=10)
        self.ax1.set_ylabel('HRV_0800 (ms)', color='tab:blue', fontsize=10)
        self.ax2.set_ylabel('深睡占比 (%)', color='tab:orange', fontsize=10)
        self.ax1.tick_params(axis='y', labelcolor='tab:blue', labelsize=8)
        self.ax2.tick_params(axis='y', labelcolor='tab:orange', labelsize=8)
        self.ax1.tick_params(axis='x', labelsize=8)
        self.ax1.grid(True, alpha=0.3)
        
        # 添加更多边距
        self.figure.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
        
        trend_layout.addWidget(self.canvas)
        trend_group.setLayout(trend_layout)
        charts_layout.addWidget(trend_group, 1)  # 1表示拉伸因子
        
        # 右侧：HRV昼夜节律柱状图
        hrv_bar_group = QGroupBox("📊 今日HRV昼夜节律")
        hrv_bar_layout = QVBoxLayout()
        hrv_bar_layout.setContentsMargins(5, 15, 5, 15)
        
        # 创建柱状图图形 - 固定高度
        self.bar_figure = Figure(figsize=(6, 3), dpi=100)
        self.bar_canvas = FigureCanvas(self.bar_figure)
        self.bar_ax = self.bar_figure.add_subplot(111)
        
        # 设置中文字体
        self.bar_figure.patch.set_facecolor('#f5f5f5')
        
        # 初始空柱状图
        times = ['0点', '4点', '8点', '12点']
        self.bar_ax.bar(times, [0, 0, 0, 0], color=['#4CAF50', '#2196F3', '#FF9800', '#9C27B0'])
        self.bar_ax.set_ylabel('HRV (ms)', fontsize=10)
        self.bar_ax.set_ylim(0, 120)
        self.bar_ax.tick_params(labelsize=8)
        self.bar_ax.grid(True, alpha=0.3, axis='y')
        
        # 添加更多边距
        self.bar_figure.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.2)
        
        hrv_bar_layout.addWidget(self.bar_canvas)
        hrv_bar_group.setLayout(hrv_bar_layout)
        charts_layout.addWidget(hrv_bar_group, 1)
        
        # 设置图表容器固定高度
        charts_widget.setLayout(charts_layout)
        charts_widget.setFixedHeight(320)  # 固定高度，包含图表和标题
        
        layout.addWidget(charts_widget)
        
        # ========== 下方：紧凑指标网格 (2x2) ==========
        metrics_widget = QWidget()
        metrics_layout = QGridLayout()
        metrics_layout.setContentsMargins(5, 5, 5, 5)
        metrics_layout.setSpacing(10)
        
        # 体重进度条 (0,0)
        weight_container = QVBoxLayout()
        self.weight_title_label = QLabel("⚖️ 体重目标 (目标 < 93.0kg)")
        self.weight_title_label.setFont(QFont("Microsoft YaHei", 10))
        weight_container.addWidget(self.weight_title_label)
        
        self.weight_progress = QProgressBar()
        self.weight_progress.setRange(0, 100)
        self.weight_progress.setValue(50)
        self.weight_progress.setFormat("当前: %v kg")
        self.weight_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
                height: 20px;  /* 紧凑高度 */
                font-size: 10pt;
                padding: 1px;
                margin: 2px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        weight_container.addWidget(self.weight_progress)
        metrics_layout.addLayout(weight_container, 0, 0)
        
        # 深度睡眠进度条 (0,1)
        sleep_container = QVBoxLayout()
        self.sleep_title_label = QLabel("😴 深度睡眠占比 (目标 > 15%)")
        self.sleep_title_label.setFont(QFont("Microsoft YaHei", 10))
        sleep_container.addWidget(self.sleep_title_label)
        
        self.sleep_progress = QProgressBar()
        self.sleep_progress.setRange(0, 100)
        self.sleep_progress.setValue(15)
        self.sleep_progress.setFormat("当前: %v%")
        self.sleep_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
                height: 20px;  /* 紧凑高度 */
                font-size: 10pt;
                padding: 1px;
                margin: 2px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 5px;
            }
        """)
        sleep_container.addWidget(self.sleep_progress)
        metrics_layout.addLayout(sleep_container, 0, 1)
        
        # HRV状态标签 (1,0)
        hrv_container = QVBoxLayout()
        self.hrv_title_label = QLabel("🧠 HRV状态 (目标 > 60ms)")
        self.hrv_title_label.setFont(QFont("Microsoft YaHei", 10))
        hrv_container.addWidget(self.hrv_title_label)
        
        self.hrv_label = QLabel("HRV 8点: -- ms")
        self.hrv_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.hrv_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))  # 12pt字体
        hrv_container.addWidget(self.hrv_label)
        metrics_layout.addLayout(hrv_container, 1, 0)
        
        # 规则触发状态 (1,1)
        rules_container = QVBoxLayout()
        rules_title_label = QLabel("🚨 规则状态")
        rules_title_label.setFont(QFont("Microsoft YaHei", 10))
        rules_container.addWidget(rules_title_label)
        
        self.rules_label = QLabel("无规则触发")
        self.rules_label.setWordWrap(True)
        self.rules_label.setFont(QFont("Microsoft YaHei", 10))
        self.rules_label.setStyleSheet("color: #FF9800; font-weight: bold; padding: 5px;")
        rules_container.addWidget(self.rules_label)
        metrics_layout.addLayout(rules_container, 1, 1)
        
        # 设置网格列拉伸，使两列等宽
        metrics_layout.setColumnStretch(0, 1)
        metrics_layout.setColumnStretch(1, 1)
        metrics_layout.setRowStretch(0, 1)
        metrics_layout.setRowStretch(1, 1)
        
        metrics_widget.setLayout(metrics_layout)
        layout.addWidget(metrics_widget)
        
        self.setLayout(layout)
    
    def load_history_data(self):
        """从数据库加载最近7天的历史数据"""
        try:
            from src.bio.database import get_recent_logs
            self.history_data = get_recent_logs(days=7)
            # 确保数据按日期升序排列（最旧到最新）
            self.history_data.sort(key=lambda x: x.get('date', ''))
            self.update_charts()
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            self.history_data = []
    
    def update_charts(self):
        """更新所有图表"""
        self.update_trend_chart()
        # 柱状图需要今日数据，将在update_kpis中更新
    
    def update_trend_chart(self):
        """更新趋势图表（HRV_0800和深睡占比）"""
        if not self.history_data:
            # 没有数据，显示空图表
            self.ax1.clear()
            self.ax2.clear()
            self.ax1.set_xlabel('日期')
            self.ax1.set_ylabel('HRV_0800 (ms)', color='tab:blue')
            self.ax2.set_ylabel('深睡占比 (%)', color='tab:orange')
            self.ax1.text(0.5, 0.5, '暂无历史数据', horizontalalignment='center',
                         verticalalignment='center', transform=self.ax1.transAxes)
            self.ax1.grid(True, alpha=0.3)
            self.canvas.draw()
            return
        
        # 提取数据
        dates = []
        hrv_values = []
        deep_sleep_ratios = []
        
        for record in self.history_data:
            date_str = record.get('date', '')
            if date_str:
                dates.append(date_str)
                hrv_values.append(record.get('hrv_0800', 0))
                deep_sleep_ratios.append(record.get('deep_sleep_ratio', 0) * 100)  # 转换为百分比
        
        if len(dates) < 2:
            # 数据不足，显示提示
            self.ax1.clear()
            self.ax2.clear()
            self.ax1.set_xlabel('日期')
            self.ax1.set_ylabel('HRV_0800 (ms)', color='tab:blue')
            self.ax2.set_ylabel('深睡占比 (%)', color='tab:orange')
            self.ax1.text(0.5, 0.5, '数据不足，需要至少2天数据', horizontalalignment='center',
                         verticalalignment='center', transform=self.ax1.transAxes)
            self.ax1.grid(True, alpha=0.3)
            self.canvas.draw()
            return
        
        # 清除旧图表
        self.ax1.clear()
        self.ax2.clear()
        
        # 绘制HRV折线（左轴）
        color1 = 'tab:blue'
        self.ax1.set_xlabel('日期')
        self.ax1.set_ylabel('HRV_0800 (ms)', color=color1)
        line1 = self.ax1.plot(dates, hrv_values, color=color1, marker='o', linewidth=2, label='HRV_0800')[0]
        self.ax1.tick_params(axis='y', labelcolor=color1)
        
        # 绘制深睡占比折线（右轴）
        color2 = 'tab:orange'
        self.ax2.set_ylabel('深睡占比 (%)', color=color2)
        line2 = self.ax2.plot(dates, deep_sleep_ratios, color=color2, marker='s', linewidth=2, label='深睡占比')[0]
        self.ax2.tick_params(axis='y', labelcolor=color2)
        
        # 设置x轴标签旋转，避免重叠
        self.ax1.set_xticks(range(len(dates)))
        self.ax1.set_xticklabels(dates, rotation=45, ha='right')
        
        # 添加网格
        self.ax1.grid(True, alpha=0.3)
        
        # 添加图例（组合两个轴的图例）
        lines = [line1, line2]
        labels = [str(line.get_label()) for line in lines]  # 确保标签为字符串
        self.ax1.legend(lines, labels, loc='upper left')
        
        # 自动调整布局
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_hrv_bar_chart(self, hrv_0000: int, hrv_0200: int, hrv_0400: int, hrv_0600: int, hrv_0800: int):
        """更新今日HRV柱状图"""
        # 清除旧图表
        self.bar_ax.clear()
        
        times = ['0点', '2点', '4点', '6点', '8点']
        values = [hrv_0000, hrv_0200, hrv_0400, hrv_0600, hrv_0800]
        colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#E91E63']
        
        # 绘制柱状图
        bars = self.bar_ax.bar(times, values, color=colors)
        
        # 在每个柱子上添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            self.bar_ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                            f'{value} ms', ha='center', va='bottom', fontsize=9)
        
        # 设置y轴范围（留一些空间）
        max_val = max(values) if values else 100
        self.bar_ax.set_ylim(0, max(max_val * 1.2, 100))
        
        self.bar_ax.set_ylabel('HRV (ms)')
        self.bar_ax.set_title('今日HRV昼夜节律', fontsize=12, fontweight='bold')
        self.bar_ax.grid(True, alpha=0.3, axis='y')
        
        # 自动调整布局
        self.bar_figure.tight_layout()
        self.bar_canvas.draw()
    
    def update_kpis(self, weight: float, deep_sleep_ratio: float, hrv_0800: int, rules_triggered: list,
                    hrv_0000: int = 0, hrv_0200: int = 0, hrv_0400: int = 0, hrv_0600: int = 0, hrv_1200: int = 0):
        """更新KPI显示和图表"""
        # 获取阈值（优先使用配置，否则使用默认）
        weight_target = 93.0
        if self.metrics_config.get('weight'):
            weight_target = self.metrics_config['weight'].target
            
        sleep_target = 0.15
        if self.metrics_config.get('deep_sleep'):
            sleep_target = self.metrics_config['deep_sleep'].target
            
        hrv_target = 60
        if self.metrics_config.get('hrv'):
            hrv_target = int(self.metrics_config['hrv'].target)
            
        # 体重进度
        weight_percent = min(100, int((weight / weight_target) * 100))
        self.weight_progress.setValue(weight_percent)
        self.weight_progress.setFormat(f"当前: {weight} kg (目标: {weight_target}kg)")
        
        # 设置颜色（绿色表示达标，红色表示超标）
        if weight <= weight_target:
            self.weight_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 5px;
                    text-align: center;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 5px;
                }
            """)
        else:
            self.weight_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 5px;
                    text-align: center;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #F44336;
                    border-radius: 5px;
                }
            """)
        
        # 深度睡眠占比进度
        # 乘以一个系数使得目标值对应进度条的大约一半或合理位置
        # 这里为了简化，假设 3 * target = 100% (例如 15% * 3 = 45%进度)
        scale_factor = 100 / (sleep_target * 3)
        sleep_percent = min(100, int(deep_sleep_ratio * 100 * 3))
        self.sleep_progress.setValue(sleep_percent)
        self.sleep_progress.setFormat(f"当前: {deep_sleep_ratio:.1%}")
        
        # 设置颜色（蓝色表示达标，橙色表示不足）
        if deep_sleep_ratio >= sleep_target:
            self.sleep_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 5px;
                    text-align: center;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #2196F3;
                    border-radius: 5px;
                }
            """)
        else:
            self.sleep_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 5px;
                    text-align: center;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #FF9800;
                    border-radius: 5px;
                }
            """)
        
        # HRV状态
        self.hrv_label.setText(f"HRV 8点: {hrv_0800} ms")
        if hrv_0800 >= hrv_target:
            self.hrv_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        elif hrv_0800 >= (hrv_target - 10):
            self.hrv_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.hrv_label.setStyleSheet("color: #F44336; font-weight: bold;")
        
        # 规则触发状态
        if rules_triggered:
            rules_text = "🚨 规则触发:\n" + "\n".join(rules_triggered)
            self.rules_label.setText(rules_text)
            self.rules_label.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            self.rules_label.setText("✅ 无规则触发")
            self.rules_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # 更新HRV柱状图
        self.update_hrv_bar_chart(hrv_0000, hrv_0200, hrv_0400, hrv_0600, hrv_0800)
        
        # 重新加载历史数据以更新趋势图
        self.load_history_data()

class BioDashboard(QMainWindow):
    """生物信息监测主界面"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化组件
        self.strategist = get_default_strategist()
        self.current_report = None
        
        self.setup_ui()
        self.setup_connections()
        
        # 尝试加载今日数据（如果存在）
        self.load_today_data()
    
    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("MY-DOGE BIO-MONITOR - 内务部健康监测系统")
        self.setGeometry(100, 100, 1400, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局（左右分割）
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧录入区
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧情报区
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)
    
    def create_left_panel(self) -> QWidget:
        """创建左侧录入区"""
        panel = QWidget()
        panel.setMaximumWidth(500)
        layout = QVBoxLayout()
        
        # 日期选择器
        date_group = QGroupBox("记录日期")
        date_layout = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(QLabel("日期:"))
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # 睡眠输入组
        sleep_group = QGroupBox("睡眠指标")
        sleep_layout = QVBoxLayout()
        self.sleep_input = SleepInputWidget()
        sleep_layout.addWidget(self.sleep_input)
        sleep_group.setLayout(sleep_layout)
        layout.addWidget(sleep_group)
        
        # HRV输入组
        hrv_group = QGroupBox("神经指标 (HRV)")
        hrv_layout = QVBoxLayout()
        self.hrv_input = HRVInputWidget()
        hrv_layout.addWidget(self.hrv_input)
        hrv_group.setLayout(hrv_layout)
        layout.addWidget(hrv_group)
        
        # 代谢输入组
        metabolic_group = QGroupBox("代谢指标")
        metabolic_layout = QVBoxLayout()
        self.metabolic_input = MetabolicInputWidget()
        metabolic_layout.addWidget(self.metabolic_input)
        metabolic_group.setLayout(metabolic_layout)
        layout.addWidget(metabolic_group)
        
        # 干预措施组
        intervention_group = QGroupBox("干预措施追踪")
        intervention_layout = QVBoxLayout()
        self.intervention_widget = InterventionWidget()
        intervention_layout.addWidget(self.intervention_widget)
        intervention_group.setLayout(intervention_layout)
        layout.addWidget(intervention_group)
        
        # 数据库管理按钮
        db_group = QGroupBox("数据库管理")
        db_layout = QVBoxLayout()
        self.db_manage_button = QPushButton("🗃️ 打开数据库管理界面")
        self.db_manage_button.clicked.connect(self.open_database_management)
        db_layout.addWidget(self.db_manage_button)
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # 提交按钮
        self.submit_button = QPushButton("🚀 提交并生成健康战备报告")
        self.submit_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        layout.addWidget(self.submit_button)
        
        # 状态提示
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧情报区"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 选项卡：报告、KPI和效能归因
        self.tab_widget = QTabWidget()
        
        # 报告选项卡
        report_tab = QWidget()
        report_layout = QVBoxLayout()
        self.report_display = ReportDisplayWidget()
        report_layout.addWidget(self.report_display)
        report_tab.setLayout(report_layout)
        self.tab_widget.addTab(report_tab, "📄 健康战备报告")
        
        # KPI仪表盘选项卡
        kpi_tab = QWidget()
        kpi_layout = QVBoxLayout()
        self.kpi_dashboard = KPIDashboardWidget()
        # 设置指标配置
        if self.strategist and self.strategist.config:
            self.kpi_dashboard.set_metrics_config(self.strategist.config.health_metrics)
            
        kpi_layout.addWidget(self.kpi_dashboard)
        kpi_tab.setLayout(kpi_layout)
        self.tab_widget.addTab(kpi_tab, "📈 KPI仪表盘")
        
        # 效能归因选项卡
        efficacy_tab = QWidget()
        efficacy_layout = QVBoxLayout()
        self.efficacy_widget = EfficacyAnalysisWidget()
        efficacy_layout.addWidget(self.efficacy_widget)
        efficacy_tab.setLayout(efficacy_layout)
        self.tab_widget.addTab(efficacy_tab, "🧪 效能归因")
        
        layout.addWidget(self.tab_widget)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 刷新历史数据")
        button_layout.addWidget(self.refresh_button)
        
        self.clear_button = QPushButton("🗑️ 清除显示")
        button_layout.addWidget(self.clear_button)
        
        self.settings_button = QPushButton("⚙️ 目标设置")
        button_layout.addWidget(self.settings_button)
        
        layout.addLayout(button_layout)
        
        panel.setLayout(layout)
        return panel
    
    def setup_connections(self):
        """设置信号槽连接"""
        self.submit_button.clicked.connect(self.submit_data)
        self.refresh_button.clicked.connect(self.load_today_data)
        self.clear_button.clicked.connect(self.clear_display)
        self.settings_button.clicked.connect(self.open_settings)
    
    def load_today_data(self):
        """加载今日数据，若无则预填充最新历史数据"""
        today_str = QDate.currentDate().toString("yyyy-MM-dd")
        
        # 1. 尝试获取今日数据
        # 使用 get_recent_logs 获取最近一条记录
        recent = get_recent_logs(days=1)  # 获取最新的1条记录
        
        target_data = {}
        is_today_data = False
        
        if recent and recent[0].get('date') == today_str:
            # A. 命中今日数据 -> 完整加载
            target_data = recent[0]
            is_today_data = True
            self.status_label.setText(f"✅ 已加载今日数据 ({today_str})")
            self.status_label.setStyleSheet("color: #4CAF50;")
        else:
            # B. 未命中 -> 寻找最近一次的历史记录 (用于预填充)
            if recent:
                latest_record = recent[0]  # 最近一条记录，可能是昨天或更早
                target_data = {
                    'weight': latest_record.get('weight', 92.5),
                    'fatigue_score': latest_record.get('fatigue_score', 3),
                    'carb_limit_check': latest_record.get('carb_limit_check', True),
                    'interventions': latest_record.get('interventions', ''),
                    # 睡眠和HRV通常波动大，不预填充或设为默认，防止误录
                    'total_sleep_min': 480,
                    'deep_sleep_min': 72,
                    'hrv_0000': 60,
                    'hrv_0400': 60,
                    'hrv_0800': 60,
                    'hrv_1200': 60
                }
                # 提取日期并格式化为 MM-dd
                record_date = latest_record.get('date', '')
                if record_date:
                    # 假设日期格式为 yyyy-MM-dd
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(record_date, "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%m-%d")
                    except:
                        formatted_date = record_date
                else:
                    formatted_date = "未知日期"
                self.status_label.setText(f"ℹ️ 已预填昨日({formatted_date})的体重与疲劳度，请录入今日睡眠/HRV")
                self.status_label.setStyleSheet("color: #FF9800;")
            else:
                # C. 纯新用户 -> 默认值
                self.status_label.setText("🌱 欢迎使用，请录入第一条数据")
                return

        # 2. 将数据填充到左侧输入框 (UI Update)
        # 睡眠
        total_sleep = target_data.get('total_sleep_min', 480)
        deep_sleep = target_data.get('deep_sleep_min', 72)
        self.sleep_input.set_values(total_sleep, deep_sleep)
        
        # HRV
        self.hrv_input.set_values(
            target_data.get('hrv_0000', 60),
            target_data.get('hrv_0200', 60),
            target_data.get('hrv_0400', 60),
            target_data.get('hrv_0600', 60),
            target_data.get('hrv_0800', 60)
        )
        
        # 代谢
        self.metabolic_input.set_values(
            target_data.get('weight', 92.5),
            target_data.get('fatigue_score', 3),
            bool(target_data.get('carb_limit_check', True))
        )
        
        # 干预措施
        self.intervention_widget.set_values(target_data.get('interventions', ''))
        
        # 设置日期
        if is_today_data:
            record_date = QDate.fromString(target_data['date'], "yyyy-MM-dd")
            self.date_edit.setDate(record_date)
        else:
            self.date_edit.setDate(QDate.currentDate())
        
        # 3. [关键修复] 立即同步更新右侧 KPI 仪表盘
        # 计算深睡占比
        if total_sleep > 0:
            deep_ratio = deep_sleep / total_sleep
        else:
            deep_ratio = 0
            
        # 简单的规则预判 (仅用于UI颜色显示，不生成文字报告)
        rules = []
        if deep_ratio < 0.15: rules.append("深睡不足")
        
        self.kpi_dashboard.update_kpis(
            weight=target_data.get('weight', 92.5),
            deep_sleep_ratio=deep_ratio,
            hrv_0800=target_data.get('hrv_0800', 60),
            rules_triggered=rules, # 简单传递，避免空值
            hrv_0000=target_data.get('hrv_0000', 60),
            hrv_0200=target_data.get('hrv_0200', 60),
            hrv_0400=target_data.get('hrv_0400', 60),
            hrv_0600=target_data.get('hrv_0600', 60),
            hrv_1200=target_data.get('hrv_1200', 60)
        )
        
        # 4. 如果是今日数据且有报告，尝试加载报告内容
        if is_today_data and target_data.get('report_content'):
            self.report_display.display_report(target_data['report_content'])
    
    @pyqtSlot()
    def submit_data(self):
        """提交数据并生成报告"""
        try:
            # 收集数据
            data_dict = self.collect_input_data()
            
            # 验证数据
            if not self.validate_input_data(data_dict):
                return
            
            # 保存到数据库
            self.status_label.setText("正在保存数据到数据库...")
            self.status_label.setStyleSheet("color: #2196F3;")
            
            success = save_daily_log(data_dict)
            if not success:
                QMessageBox.critical(self, "错误", "保存数据到数据库失败！")
                self.status_label.setText("保存失败")
                self.status_label.setStyleSheet("color: #F44336;")
                return
            
            # 获取历史数据用于分析
            history_data = get_recent_logs(days=7)
            
            # 禁用提交按钮，防止重复点击
            self.submit_button.setEnabled(False)
            self.submit_button.setText("正在分析数据中...")
            self.status_label.setText("正在调用AI生成健康战备报告，请稍候...")
            
            # 启动工作线程
            self.report_thread = ReportGeneratorThread(self.strategist, data_dict, history_data)
            self.report_thread.finished_signal.connect(self.on_report_finished)
            self.report_thread.error_signal.connect(self.on_report_error)
            self.report_thread.start()
            
        except Exception as e:
            logger.error(f"提交数据时发生错误: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"提交数据时发生错误:\n{str(e)}")
            self.status_label.setText("提交失败")
            self.status_label.setStyleSheet("color: #F44336;")
            self.submit_button.setEnabled(True)
            self.submit_button.setText("🚀 提交并生成健康战备报告")

    @pyqtSlot(dict)
    def on_report_finished(self, report_result):
        """报告生成完成的回调"""
        # 恢复按钮状态
        self.submit_button.setEnabled(True)
        self.submit_button.setText("🚀 提交并生成健康战备报告")
        
        if not report_result.get('success'):
            QMessageBox.warning(self, "警告", f"生成报告失败: {report_result.get('error')}")
            self.status_label.setText("报告生成失败")
            self.status_label.setStyleSheet("color: #F44336;")
            return
        
        # 收集数据（重新收集以确保一致性，或者从线程传递）
        data_dict = self.collect_input_data()
        
        # 保存报告到数据库（更新report_content字段和title字段）
        data_dict['report_content'] = report_result['report_content']
        data_dict['title'] = report_result['report_title']
        save_daily_log(data_dict)  # 更新记录
        
        # 显示报告
        self.current_report = report_result
        self.report_display.display_report(report_result['report_content'])
        
        # 更新KPI仪表盘
        self.kpi_dashboard.update_kpis(
            weight=data_dict['weight'],
            deep_sleep_ratio=data_dict.get('deep_sleep_ratio', 0),
            hrv_0800=data_dict['hrv_0800'],
            rules_triggered=report_result['metadata'].get('rules_triggered', []),
            hrv_0000=data_dict['hrv_0000'],
            hrv_0200=data_dict.get('hrv_0200', 0),
            hrv_0400=data_dict['hrv_0400'],
            hrv_0600=data_dict.get('hrv_0600', 0),
            hrv_1200=data_dict.get('hrv_1200', 0)
        )
        
        # 无需启用保存按钮，报告已自动保存
        
        # 切换到报告选项卡
        self.tab_widget.setCurrentIndex(0)
        
        self.status_label.setText(f"报告生成成功！日期: {data_dict['date']}")
        self.status_label.setStyleSheet("color: #4CAF50;")
        
        QMessageBox.information(self, "成功", "数据提交成功，健康战备报告已生成！")

    @pyqtSlot(str)
    def on_report_error(self, error_msg):
        """报告生成出错的回调"""
        self.submit_button.setEnabled(True)
        self.submit_button.setText("🚀 提交并生成健康战备报告")
        
        QMessageBox.critical(self, "错误", f"生成报告时发生错误:\n{error_msg}")
        self.status_label.setText("生成出错")
        self.status_label.setStyleSheet("color: #F44336;")
    
    def collect_input_data(self) -> Dict[str, Any]:
        """收集输入数据"""
        # 日期
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        
        # 睡眠数据
        total_sleep_min = self.sleep_input.get_total_sleep_min()
        deep_sleep_min = self.sleep_input.get_deep_sleep_min()
        deep_sleep_ratio = deep_sleep_min / total_sleep_min if total_sleep_min > 0 else 0
        
        # HRV数据
        hrv_values = self.hrv_input.get_values()
        
        # 代谢数据
        metabolic_values = self.metabolic_input.get_values()
        
        # 干预措施
        interventions = self.intervention_widget.get_values()
        
        # 组合数据
        data_dict = {
            'date': date_str,
            'total_sleep_min': total_sleep_min,
            'deep_sleep_min': deep_sleep_min,
            'deep_sleep_ratio': deep_sleep_ratio,
            **hrv_values,
            **metabolic_values,
            'interventions': interventions,
            'report_content': ''  # 初始为空，生成报告后会更新
        }
        
        return data_dict
    
    def validate_input_data(self, data_dict: Dict[str, Any]) -> bool:
        """验证输入数据"""
        errors = []
        
        # 检查总睡眠时长
        if data_dict['total_sleep_min'] <= 0:
            errors.append("总睡眠时长必须大于0")
        elif data_dict['total_sleep_min'] > 1440:
            errors.append("总睡眠时长不能超过1440分钟（24小时）")
        
        # 检查深度睡眠时长
        if data_dict['deep_sleep_min'] < 0:
            errors.append("深度睡眠时长不能为负数")
        elif data_dict['deep_sleep_min'] > data_dict['total_sleep_min']:
            errors.append("深度睡眠时长不能超过总睡眠时长")
        
        # 检查疲劳度评分
        if not (1 <= data_dict['fatigue_score'] <= 10):
            errors.append("疲劳度评分必须在1-10之间")
        
        if errors:
            QMessageBox.warning(self, "数据验证失败", "\n".join(errors))
            return False
        
        return True
    
    @pyqtSlot()
    def save_report(self):
        """保存报告到文件"""
        if not self.current_report:
            QMessageBox.warning(self, "警告", "没有可保存的报告！")
            return
        
        try:
            # 创建reports目录
            import os
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # 生成文件名：report_by_[model]_[date]_[time].md
            date_str = self.current_report['date']
            
            # 获取模型名称
            model_name = "unknown"
            if self.strategist and self.strategist.config and self.strategist.config.model:
                model_name = self.strategist.config.model
            
            # 清理模型名称（移除特殊字符）
            safe_model_name = re.sub(r'[^\w\-]', '_', model_name)
            
            # 当前时间
            time_str = datetime.now().strftime('%H-%M-%S')
            
            filename = f"report_by_{safe_model_name}_{date_str}_{time_str}.md"
            filepath = os.path.join(reports_dir, filename)
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.current_report['report_content'])
            
            QMessageBox.information(self, "成功", f"报告已保存到:\n{filepath}")
            
        except Exception as e:
            logger.error(f"保存报告时发生错误: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"保存报告时发生错误:\n{str(e)}")
    
    @pyqtSlot()
    def clear_display(self):
        """清除显示"""
        self.report_display.clear()
        self.status_label.setText("显示已清除")
        self.status_label.setStyleSheet("color: #666;")
    
    @pyqtSlot()
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self.strategist.config, self)
        if dialog.exec():
            # 设置已保存，更新KPI仪表盘显示
            if self.kpi_dashboard and self.strategist.config:
                self.kpi_dashboard.set_metrics_config(self.strategist.config.health_metrics)
            self.status_label.setText("目标设置已更新")
            self.status_label.setStyleSheet("color: #4CAF50;")
    
    @pyqtSlot()
    def open_database_management(self):
        """打开数据库管理界面"""
        from src.interface.database_manager import DatabaseManagerDialog
        dialog = DatabaseManagerDialog(self)
        dialog.exec()

class EfficacyAnalysisWidget(QWidget):
    """效能归因分析组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_analysis_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 标题和刷新按钮
        header_layout = QHBoxLayout()
        title = QLabel("🧪 干预措施效能归因分析")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        self.refresh_button = QPushButton("🔄 刷新分析")
        self.refresh_button.clicked.connect(self.load_analysis_data)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # 分析结果标签
        self.summary_label = QLabel("正在加载分析数据...")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #87ceeb;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """)
        layout.addWidget(self.summary_label)
        
        # 图表区域
        self.chart_group = QGroupBox("📊 干预措施对比分析")
        chart_layout = QVBoxLayout()
        
        # 创建matplotlib图形（两个子图：HRV和深睡）
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        # 设置中文字体
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        matplotlib.rcParams['axes.unicode_minus'] = False
        
        # 创建两个子图
        self.ax1 = self.figure.add_subplot(211)  # HRV图表
        self.ax2 = self.figure.add_subplot(212)  # 深睡图表
        
        # 初始空图表
        self.ax1.set_title('HRV_0800对比 (ms)', fontsize=12, fontweight='bold')
        self.ax1.set_ylabel('HRV (ms)')
        self.ax1.grid(True, alpha=0.3)
        
        self.ax2.set_title('深睡占比对比 (%)', fontsize=12, fontweight='bold')
        self.ax2.set_ylabel('深睡占比 (%)')
        self.ax2.grid(True, alpha=0.3)
        
        self.figure.tight_layout(pad=3.0)
        
        chart_layout.addWidget(self.canvas)
        self.chart_group.setLayout(chart_layout)
        layout.addWidget(self.chart_group)
        
        # 详细数据表格
        data_group = QGroupBox("📋 详细影响分数")
        data_layout = QVBoxLayout()
        
        self.data_text = QTextBrowser()
        self.data_text.setMaximumHeight(150)
        self.data_text.setStyleSheet("""
            QTextBrowser {
                font-family: "Consolas", "Microsoft YaHei";
                font-size: 10pt;
            }
        """)
        data_layout.addWidget(self.data_text)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # 分析报告
        report_group = QGroupBox("📄 分析报告")
        report_layout = QVBoxLayout()
        
        self.report_text = QTextBrowser()
        self.report_text.setMaximumHeight(200)
        self.report_text.setStyleSheet("""
            QTextBrowser {
                font-family: "Microsoft YaHei";
                font-size: 10pt;
                line-height: 1.4;
            }
        """)
        report_layout.addWidget(self.report_text)
        
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)
        
        # 底部说明
        footer_label = QLabel("💡 说明：分析基于历史数据，比较有干预措施与无干预措施时的平均指标差异。")
        footer_label.setWordWrap(True)
        footer_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(footer_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_analysis_data(self):
        """加载分析数据并更新图表"""
        try:
            # 获取干预统计数据
            df = get_intervention_stats()
            if df is None or df.empty:
                self.summary_label.setText("❌ 无法获取干预统计数据，请确保数据库中有记录。")
                self.summary_label.setStyleSheet("color: #F44336;")
                return
            
            # 计算相关性
            from src.bio.analytics import calculate_correlations, get_intervention_comparison_data, analyze_intervention_effectiveness
            
            correlation_result = calculate_correlations(df)
            comparison_data = get_intervention_comparison_data(df, top_n=3)
            report_text = analyze_intervention_effectiveness(df)
            
            # 更新摘要标签
            summary = f"📊 分析完成：共分析 {correlation_result.get('total_samples', 0)} 条记录，"
            summary += f"发现 {len(correlation_result.get('impact_scores', {}))} 个有效干预措施。"
            summary += f"\n💡 {correlation_result.get('summary', '')}"
            
            self.summary_label.setText(summary)
            self.summary_label.setStyleSheet("""
                QLabel {
                    background-color: #f0fff0;
                    border: 1px solid #90ee90;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 5px;
                    color: #006400;
                }
            """)
            
            # 更新图表
            self.update_charts(comparison_data)
            
            # 更新详细数据
            self.update_data_text(correlation_result)
            
            # 更新分析报告
            self.report_text.setPlainText(report_text)
            
        except Exception as e:
            logger.error(f"加载分析数据失败: {e}")
            self.summary_label.setText(f"❌ 分析数据加载失败: {str(e)}")
            self.summary_label.setStyleSheet("color: #F44336;")
    
    def update_charts(self, comparison_data: Dict[str, Any]):
        """更新对比图表"""
        # 清除旧图表
        self.ax1.clear()
        self.ax2.clear()
        
        categories = comparison_data.get('categories', [])
        hrv_data = comparison_data.get('hrv_data', [])
        sleep_data = comparison_data.get('sleep_data', [])
        hrv_labels = comparison_data.get('hrv_labels', [])
        sleep_labels = comparison_data.get('sleep_labels', [])
        
        if not categories or len(categories) < 2:
            # 没有足够数据
            self.ax1.text(0.5, 0.5, '数据不足，无法生成对比图表', 
                         horizontalalignment='center', verticalalignment='center',
                         transform=self.ax1.transAxes, fontsize=12)
            self.ax2.text(0.5, 0.5, '数据不足，无法生成对比图表',
                         horizontalalignment='center', verticalalignment='center',
                         transform=self.ax2.transAxes, fontsize=12)
            self.canvas.draw()
            return
        
        # 设置颜色：基线用蓝色，正面影响用绿色，负面影响用红色
        colors = []
        for i, cat in enumerate(categories):
            if i == 0:  # 基线
                colors.append('#2196F3')  # 蓝色
            else:
                # 检查是正面还是负面影响
                hrv_value = hrv_data[i]
                sleep_value = sleep_data[i]
                baseline_hrv = hrv_data[0]
                baseline_sleep = sleep_data[0]
                
                if hrv_value >= baseline_hrv and sleep_value >= baseline_sleep:
                    colors.append('#4CAF50')  # 绿色
                elif hrv_value <= baseline_hrv and sleep_value <= baseline_sleep:
                    colors.append('#F44336')  # 红色
                else:
                    colors.append('#FF9800')  # 橙色
        
        # 绘制HRV图表
        x_positions = range(len(categories))
        bars1 = self.ax1.bar(x_positions, hrv_data, color=colors, alpha=0.8)
        self.ax1.set_title('HRV_0800对比 (ms)', fontsize=12, fontweight='bold')
        self.ax1.set_ylabel('HRV (ms)')
        self.ax1.set_xticks(x_positions)
        self.ax1.set_xticklabels(categories, rotation=15, ha='right')
        self.ax1.grid(True, alpha=0.3, axis='y')
        
        # 在柱子上添加标签
        for bar, label in zip(bars1, hrv_labels):
            height = bar.get_height()
            self.ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                         label, ha='center', va='bottom', fontsize=9, rotation=0)
        
        # 绘制深睡图表
        bars2 = self.ax2.bar(x_positions, sleep_data, color=colors, alpha=0.8)
        self.ax2.set_title('深睡占比对比 (%)', fontsize=12, fontweight='bold')
        self.ax2.set_ylabel('深睡占比 (%)')
        self.ax2.set_xticks(x_positions)
        self.ax2.set_xticklabels(categories, rotation=15, ha='right')
        self.ax2.grid(True, alpha=0.3, axis='y')
        
        # 在柱子上添加标签
        for bar, label in zip(bars2, sleep_labels):
            height = bar.get_height()
            self.ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                         label, ha='center', va='bottom', fontsize=9, rotation=0)
        
        # 自动调整布局
        self.figure.tight_layout(pad=3.0)
        self.canvas.draw()
    
    def update_data_text(self, correlation_result: Dict[str, Any]):
        """更新详细数据文本"""
        impact_scores = correlation_result.get('impact_scores', {})
        baseline = correlation_result.get('baseline', {})
        
        if not impact_scores:
            self.data_text.setPlainText("暂无有效干预措施数据。")
            return
        
        # 构建表格文本
        text_lines = []
        text_lines.append(f"{'干预措施':<15} {'样本数':<8} {'HRV变化':<12} {'深睡变化':<12}")
        text_lines.append("-" * 50)
        
        # 按综合影响排序
        sorted_items = sorted(
            impact_scores.items(),
            key=lambda x: abs(x[1].get('sleep_pct', 0)) * 0.7 + abs(x[1].get('hrv_pct', 0)) * 0.3,
            reverse=True
        )
        
        for name, data in sorted_items:
            hrv_sign = "+" if data.get('hrv_pct', 0) > 0 else ""
            sleep_sign = "+" if data.get('sleep_pct', 0) > 0 else ""
            
            text_lines.append(
                f"{name:<15} {data.get('samples', 0):<8} "
                f"{hrv_sign}{data.get('hrv_pct', 0):>5.1f}% ({data.get('hrv_impact', 0):>+5.1f}ms) "
                f"{sleep_sign}{data.get('sleep_pct', 0):>5.1f}% ({data.get('sleep_impact', 0):>+5.3f})"
            )
        
        text_lines.append("")
        text_lines.append(f"基线数据: HRV={baseline.get('hrv_0800_mean', 0):.1f}ms, "
                         f"深睡占比={baseline.get('deep_sleep_ratio_mean', 0)*100:.1f}% "
                         f"(n={baseline.get('samples', 0)})")
        
        self.data_text.setPlainText("\n".join(text_lines))

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
        self.load_current_values()
    
    def setup_ui(self):
        self.setWindowTitle("⚙️ 健康指标目标设置")
        self.setGeometry(200, 200, 400, 300)
        
        layout = QVBoxLayout()
        
        # 体重目标设置
        weight_group = QGroupBox("体重目标")
        weight_layout = QGridLayout()
        weight_layout.addWidget(QLabel("目标体重上限 (kg):"), 0, 0)
        self.weight_spinbox = QDoubleSpinBox()
        self.weight_spinbox.setRange(50, 150)
        self.weight_spinbox.setDecimals(1)
        self.weight_spinbox.setSuffix(" kg")
        weight_layout.addWidget(self.weight_spinbox, 0, 1)
        weight_group.setLayout(weight_layout)
        layout.addWidget(weight_group)
        
        # 深度睡眠目标设置
        sleep_group = QGroupBox("深度睡眠目标")
        sleep_layout = QGridLayout()
        sleep_layout.addWidget(QLabel("目标占比 (%):"), 0, 0)
        self.sleep_spinbox = QDoubleSpinBox()
        self.sleep_spinbox.setRange(5, 50)
        self.sleep_spinbox.setDecimals(1)
        self.sleep_spinbox.setSuffix(" %")
        sleep_layout.addWidget(self.sleep_spinbox, 0, 1)
        sleep_group.setLayout(sleep_layout)
        layout.addWidget(sleep_group)
        
        # HRV目标设置
        hrv_group = QGroupBox("HRV目标 (8点基准)")
        hrv_layout = QGridLayout()
        hrv_layout.addWidget(QLabel("目标值 (ms):"), 0, 0)
        self.hrv_spinbox = QSpinBox()
        self.hrv_spinbox.setRange(30, 150)
        self.hrv_spinbox.setSuffix(" ms")
        hrv_layout.addWidget(self.hrv_spinbox, 0, 1)
        hrv_group.setLayout(hrv_layout)
        layout.addWidget(hrv_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("💾 保存")
        self.cancel_button = QPushButton("取消")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)
    
    def load_current_values(self):
        """加载当前配置值"""
        metrics = self.config.health_metrics
        
        if 'weight' in metrics:
            self.weight_spinbox.setValue(metrics['weight'].target)
        else:
            self.weight_spinbox.setValue(93.0)
        
        if 'deep_sleep' in metrics:
            # 配置文件中存储的是小数（0.15），但UI显示百分比（15%）
            self.sleep_spinbox.setValue(metrics['deep_sleep'].target * 100)
        else:
            self.sleep_spinbox.setValue(15.0)
        
        if 'hrv' in metrics:
            self.hrv_spinbox.setValue(int(metrics['hrv'].target))
        else:
            self.hrv_spinbox.setValue(60)
    
    def save_settings(self):
        """保存设置"""
        try:
            # 更新配置
            weight_target = self.weight_spinbox.value()
            sleep_target = self.sleep_spinbox.value() / 100.0  # 转换为小数
            hrv_target = self.hrv_spinbox.value()
            
            # 更新内存配置
            self.config.update_metric_target('weight', weight_target)
            self.config.update_metric_target('deep_sleep', sleep_target)
            self.config.update_metric_target('hrv', float(hrv_target))
            
            # 保存到文件
            if self.config.save_config():
                QMessageBox.information(self, "成功", "配置已保存！")
                self.accept()
            else:
                QMessageBox.warning(self, "警告", "保存配置文件失败，请检查文件权限。")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置时发生错误:\n{str(e)}")

# 应用程序入口
def main():
    """主函数"""
    # 初始化数据库
    initialize_db()
    
    # 创建并显示窗口
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = BioDashboard()
    window.show()
    
    # 启动事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    main()
