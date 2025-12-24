import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QMessageBox, QFileDialog, QHeaderView, QSplitter,
    QTextEdit, QGroupBox, QFormLayout, QLineEdit, QDateEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

# 导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bio.database import get_db_path as get_bio_db_path, get_all_logs, delete_log, save_daily_log
from src.health.database import get_db_path as get_health_db_path, get_biometric_data

class DatabaseManagerDialog(QDialog):
    """数据库管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("🗃️ 数据库管理 - bio_data.db & health_monitor.db")
        self.setGeometry(100, 100, 1200, 800)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("数据库管理界面")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 数据库路径显示
        db_info_group = QGroupBox("数据库文件路径")
        db_info_layout = QHBoxLayout()
        
        bio_db_path = get_bio_db_path()
        health_db_path = get_health_db_path()
        
        db_info_layout.addWidget(QLabel(f"bio_data.db: {bio_db_path}"))
        db_info_layout.addWidget(QLabel(f"health_monitor.db: {health_db_path}"))
        db_info_group.setLayout(db_info_layout)
        layout.addWidget(db_info_group)
        
        # 选项卡：两个数据库
        self.tab_widget = QTabWidget()
        
        # bio_data.db 选项卡
        bio_tab = self.create_bio_data_tab()
        self.tab_widget.addTab(bio_tab, "📊 bio_data.db (生物数据)")
        
        # health_monitor.db 选项卡
        health_tab = self.create_health_data_tab()
        self.tab_widget.addTab(health_tab, "📈 health_monitor.db (健康监测)")
        
        layout.addWidget(self.tab_widget)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 刷新数据")
        self.refresh_button.clicked.connect(self.load_data)
        button_layout.addWidget(self.refresh_button)
        
        self.export_button = QPushButton("📤 导出为CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_button)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_bio_data_tab(self):
        """创建bio_data.db管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 数据表
        self.bio_table = QTableWidget()
        self.bio_table.setAlternatingRowColors(True)
        self.bio_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ccc;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        layout.addWidget(self.bio_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.add_bio_button = QPushButton("➕ 添加记录")
        self.add_bio_button.clicked.connect(self.add_bio_record)
        button_layout.addWidget(self.add_bio_button)
        
        self.edit_bio_button = QPushButton("✏️ 编辑选中记录")
        self.edit_bio_button.clicked.connect(self.edit_bio_record)
        button_layout.addWidget(self.edit_bio_button)
        
        self.delete_bio_button = QPushButton("🗑️ 删除选中记录")
        self.delete_bio_button.clicked.connect(self.delete_bio_record)
        button_layout.addWidget(self.delete_bio_button)
        
        self.view_report_button = QPushButton("📄 查看报告")
        self.view_report_button.clicked.connect(self.view_report)
        button_layout.addWidget(self.view_report_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 统计信息
        self.bio_stats_label = QLabel("加载中...")
        self.bio_stats_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.bio_stats_label)
        
        tab.setLayout(layout)
        return tab
    
    def create_health_data_tab(self):
        """创建health_monitor.db管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 数据表
        self.health_table = QTableWidget()
        self.health_table.setAlternatingRowColors(True)
        self.health_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ccc;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        layout.addWidget(self.health_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.add_health_button = QPushButton("➕ 添加记录")
        self.add_health_button.clicked.connect(self.add_health_record)
        button_layout.addWidget(self.add_health_button)
        
        self.edit_health_button = QPushButton("✏️ 编辑选中记录")
        self.edit_health_button.clicked.connect(self.edit_health_record)
        button_layout.addWidget(self.edit_health_button)
        
        self.delete_health_button = QPushButton("🗑️ 删除选中记录")
        self.delete_health_button.clicked.connect(self.delete_health_record)
        button_layout.addWidget(self.delete_health_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 统计信息
        self.health_stats_label = QLabel("加载中...")
        self.health_stats_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.health_stats_label)
        
        tab.setLayout(layout)
        return tab
    
    def load_data(self):
        """加载两个数据库的数据"""
        self.load_bio_data()
        self.load_health_data()
    
    def load_bio_data(self):
        """加载bio_data.db数据"""
        try:
            # 获取所有记录
            records = get_all_logs()
            
            if not records:
                self.bio_table.setRowCount(0)
                self.bio_table.setColumnCount(1)
                self.bio_table.setHorizontalHeaderLabels(["信息"])
                self.bio_table.setItem(0, 0, QTableWidgetItem("数据库为空"))
                self.bio_stats_label.setText("数据库为空")
                return
            
            # 设置表格 - 只显示关键字段，按指定顺序
            display_columns = ['date', 'timestamp', 'tags', 'analyst',
                              'total_sleep_min', 'deep_sleep_min', 'deep_sleep_ratio',
                              'hrv_0000', 'hrv_0200', 'hrv_0400', 'hrv_0600', 'hrv_0800',
                              'weight', 'fatigue_score', 'carb_limit_check', 'title']
            
            # 检查哪些列实际存在
            available_columns = [col for col in display_columns if col in records[0]]
            # 添加报告内容列（如果存在）
            if 'report_content' in records[0]:
                available_columns.append('report_content')
            
            self.bio_table.setColumnCount(len(available_columns))
            self.bio_table.setHorizontalHeaderLabels(available_columns)
            self.bio_table.setRowCount(len(records))
            
            # 填充数据
            for row_idx, record in enumerate(records):
                for col_idx, col_name in enumerate(available_columns):
                    value = record.get(col_name, "")
                    
                    # 转换值为字符串
                    if value is None:
                        value_str = ""
                    elif isinstance(value, bool):
                        value_str = "是" if value else "否"
                    elif isinstance(value, float):
                        # 深度睡眠比例显示为百分比
                        if col_name == 'deep_sleep_ratio':
                            value_str = f"{value:.1%}"
                        else:
                            value_str = f"{value:.2f}"
                    elif col_name == 'total_sleep_min':
                        # 睡眠分钟转换为小时+分钟显示
                        hours = value // 60
                        minutes = value % 60
                        value_str = f"{hours}h{minutes}m"
                    elif col_name == 'deep_sleep_min':
                        value_str = f"{value}min"
                    elif col_name in ['hrv_0000', 'hrv_0200', 'hrv_0400', 'hrv_0600', 'hrv_0800']:
                        value_str = f"{value}ms"
                    elif col_name == 'weight':
                        value_str = f"{value}kg"
                    elif col_name == 'timestamp':
                        # 缩短时间戳显示
                        if value:
                            try:
                                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                value_str = dt.strftime('%Y-%m-%d %H:%M')
                            except:
                                value_str = str(value)
                        else:
                            value_str = ""
                    else:
                        value_str = str(value)
                    
                    item = QTableWidgetItem(value_str)
                    
                    # 根据列名设置对齐方式
                    if col_name in ['date', 'timestamp', 'tags', 'analyst', 'report_content']:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    
                    # 设置颜色标记
                    if col_name == 'weight' and isinstance(value, (int, float)):
                        if value > 93.0:
                            item.setBackground(QColor(255, 200, 200))  # 浅红色
                    elif col_name == 'deep_sleep_ratio' and isinstance(value, (int, float)):
                        if value < 0.15:
                            item.setBackground(QColor(255, 220, 180))  # 浅橙色
                    
                    self.bio_table.setItem(row_idx, col_idx, item)
            
            # 调整列宽
            header = self.bio_table.horizontalHeader()
            if header:
                header.setStretchLastSection(True)
            self.bio_table.resizeColumnsToContents()
            
            # 更新统计信息
            total_records = len(records)
            date_range = self.get_date_range(records)
            
            # 统计分析师分布
            analyst_counts = {}
            for record in records:
                analyst = record.get('analyst', 'unknown')
                analyst_counts[analyst] = analyst_counts.get(analyst, 0) + 1
            
            analyst_text = ""
            if analyst_counts:
                analyst_text = " | 分析师: " + ", ".join([f"{k}({v})" for k, v in analyst_counts.items()])
            
            self.bio_stats_label.setText(
                f"总记录数: {total_records} | 日期范围: {date_range['min']} 至 {date_range['max']}{analyst_text}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载bio_data.db数据失败:\n{str(e)}")
    
    def load_health_data(self):
        """加载health_monitor.db数据"""
        try:
            # 连接到数据库
            db_path = get_health_db_path()
            conn = sqlite3.connect(db_path)
            
            # 尝试查询，如果表不存在则创建
            try:
                query = "SELECT * FROM biometric_logs ORDER BY date DESC"
                df = pd.read_sql_query(query, conn)
            except sqlite3.OperationalError as e:
                if "no such table" in str(e).lower():
                    # 表不存在，调用初始化函数
                    conn.close()  # 关闭当前连接
                    
                    # 导入并调用初始化函数
                    from src.health.database import initialize_db
                    success = initialize_db()
                    if success:
                        # 重新连接并查询
                        conn = sqlite3.connect(db_path)
                        df = pd.read_sql_query(query, conn)
                    else:
                        raise Exception("数据库表初始化失败")
                else:
                    raise e
            
            conn.close()
            
            if df.empty:
                self.health_table.setRowCount(0)
                self.health_table.setColumnCount(1)
                self.health_table.setHorizontalHeaderLabels(["信息"])
                self.health_table.setItem(0, 0, QTableWidgetItem("数据库为空"))
                self.health_stats_label.setText("数据库为空")
                return
            
            # 设置表格
            columns = df.columns.tolist()
            self.health_table.setColumnCount(len(columns))
            self.health_table.setHorizontalHeaderLabels(columns)
            self.health_table.setRowCount(len(df))
            
            # 填充数据
            for row_idx in range(len(df)):
                for col_idx, col_name in enumerate(columns):
                    value = df.iloc[row_idx][col_name]
                    
                    # 转换值为字符串
                    if pd.isna(value):
                        value_str = ""
                    elif isinstance(value, bool):
                        value_str = "是" if value else "否"
                    elif isinstance(value, float):
                        value_str = f"{value:.2f}"
                    else:
                        value_str = str(value)
                    
                    item = QTableWidgetItem(value_str)
                    
                    # 根据列名设置对齐方式
                    if col_name in ['date', 'tags']:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    
                    self.health_table.setItem(row_idx, col_idx, item)
            
            # 调整列宽
            header = self.health_table.horizontalHeader()
            if header:
                header.setStretchLastSection(True)
            self.health_table.resizeColumnsToContents()
            
            # 更新统计信息
            total_records = len(df)
            if 'date' in df.columns and not df['date'].empty:
                min_date = df['date'].min()
                max_date = df['date'].max()
                date_range_text = f"{min_date} 至 {max_date}"
            else:
                date_range_text = "未知"
            
            self.health_stats_label.setText(
                f"总记录数: {total_records} | 日期范围: {date_range_text}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载health_monitor.db数据失败:\n{str(e)}")
    
    def get_date_range(self, records):
        """获取日期范围"""
        if not records:
            return {'min': '未知', 'max': '未知'}
        
        dates = [r['date'] for r in records if 'date' in r and r['date']]
        if dates:
            return {'min': min(dates), 'max': max(dates)}
        return {'min': '未知', 'max': '未知'}
    
    def add_bio_record(self):
        """添加bio_data.db记录"""
        dialog = BioRecordDialog(self)
        if dialog.exec():
            self.load_bio_data()
    
    def edit_bio_record(self):
        """编辑选中的bio_data.db记录"""
        selected = self.bio_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一条记录")
            return
        
        # 获取选中行的数据
        date_item = self.bio_table.item(selected, 0)  # date列是第一列
        if not date_item:
            QMessageBox.warning(self, "警告", "无法获取记录日期")
            return
        
        date_str = date_item.text()
        
        # 从数据库获取完整记录
        from src.bio.database import get_recent_logs
        records = get_recent_logs(days=365)  # 获取一年内的记录
        target_record = None
        for record in records:
            if str(record.get('date', '')) == date_str:
                target_record = record
                break
        
        if not target_record:
            QMessageBox.warning(self, "警告", f"未找到日期为 {date_str} 的记录")
            return
        
        # 打开编辑对话框
        dialog = BioRecordDialog(self, target_record)
        if dialog.exec():
            self.load_bio_data()
    
    def delete_bio_record(self):
        """删除选中的bio_data.db记录"""
        selected = self.bio_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一条记录")
            return
        
        # 获取选中行的日期
        date_item = self.bio_table.item(selected, 0)  # date列是第一列
        if not date_item:
            QMessageBox.warning(self, "警告", "无法获取记录日期")
            return
        
        date_str = date_item.text()
        
        # 确认删除
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除日期为 {date_str} 的记录吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from src.bio.database import delete_log
                if delete_log(date_str):
                    QMessageBox.information(self, "成功", "记录已删除")
                    self.load_bio_data()
                else:
                    QMessageBox.warning(self, "警告", "删除失败，记录可能不存在")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败:\n{str(e)}")
    
    def view_report(self):
        """查看选中记录的完整报告"""
        selected = self.bio_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一条记录")
            return
        
        # 获取报告内容
        report_col = -1
        for col in range(self.bio_table.columnCount()):
            header = self.bio_table.horizontalHeaderItem(col)
            if header and header.text() == 'report_content':
                report_col = col
                break
        
        if report_col < 0:
            QMessageBox.warning(self, "警告", "该记录没有报告内容")
            return
        
        report_item = self.bio_table.item(selected, report_col)
        if not report_item or not report_item.text().strip():
            QMessageBox.warning(self, "警告", "该记录的报告内容为空")
            return
        
        report_content = report_item.text()
        
        # 显示报告对话框
        dialog = ReportViewDialog(report_content, self)
        dialog.exec()
    
    def add_health_record(self):
        """添加health_monitor.db记录"""
        QMessageBox.information(self, "信息", "该功能正在开发中")
    
    def edit_health_record(self):
        """编辑选中的health_monitor.db记录"""
        QMessageBox.information(self, "信息", "该功能正在开发中")
    
    def delete_health_record(self):
        """删除选中的health_monitor.db记录"""
        selected = self.health_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一条记录")
            return
        
        # 获取选中行的日期
        date_item = self.health_table.item(selected, 0)  # date列
        if not date_item:
            QMessageBox.warning(self, "警告", "无法获取记录日期")
            return
        
        date_str = date_item.text()
        
        # 确认删除
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除日期为 {date_str} 的记录吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 连接到数据库并删除
                db_path = get_health_db_path()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM biometric_logs WHERE date = ?", (date_str,))
                conn.commit()
                deleted = cursor.rowcount > 0
                conn.close()
                
                if deleted:
                    QMessageBox.information(self, "成功", "记录已删除")
                    self.load_health_data()
                else:
                    QMessageBox.warning(self, "警告", "删除失败，记录可能不存在")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败:\n{str(e)}")
    
    def export_to_csv(self):
        """导出当前显示的数据库为CSV文件"""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # bio_data.db
            data_source = "bio"
            table = self.bio_table
        else:  # health_monitor.db
            data_source = "health"
            table = self.health_table
        
        if table.rowCount() == 0:
            QMessageBox.warning(self, "警告", "没有数据可导出")
            return
        
        # 选择保存路径
        default_name = f"{data_source}_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存CSV文件", default_name, "CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            # 收集表头和数据
            headers = []
            for col in range(table.columnCount()):
                header_item = table.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else f"列{col+1}")
            
            data = []
            for row in range(table.rowCount()):
                row_data = []
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # 创建DataFrame并保存
            df = pd.DataFrame(data, columns=headers)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            QMessageBox.information(self, "成功", f"数据已导出到:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

class BioRecordDialog(QDialog):
    """bio_data.db记录编辑对话框"""
    
    def __init__(self, parent=None, record=None):
        super().__init__(parent)
        self.record = record
        self.is_edit_mode = record is not None
        self.setup_ui()
        self.load_record_data()
    
    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("编辑生物数据记录" if self.is_edit_mode else "添加生物数据记录")
        self.setGeometry(200, 200, 600, 700)
        
        layout = QVBoxLayout()
        
        # 表单布局
        form_group = QGroupBox("记录详情")
        form_layout = QFormLayout()
        
        # 日期
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("日期 (YYYY-MM-DD):", self.date_edit)
        
        # 睡眠数据
        form_layout.addRow(QLabel("<b>睡眠指标</b>"))
        
        self.total_sleep_hours = QSpinBox()
        self.total_sleep_hours.setRange(0, 23)
        self.total_sleep_hours.setValue(7)
        self.total_sleep_hours.setSuffix(" 小时")
        
        self.total_sleep_minutes = QSpinBox()
        self.total_sleep_minutes.setRange(0, 59)
        self.total_sleep_minutes.setValue(30)
        self.total_sleep_minutes.setSuffix(" 分钟")
        
        sleep_layout = QHBoxLayout()
        sleep_layout.addWidget(self.total_sleep_hours)
        sleep_layout.addWidget(QLabel("小时"))
        sleep_layout.addWidget(self.total_sleep_minutes)
        sleep_layout.addWidget(QLabel("分钟"))
        form_layout.addRow("总睡眠时长:", sleep_layout)
        
        self.deep_sleep_minutes = QSpinBox()
        self.deep_sleep_minutes.setRange(0, 1440)
        self.deep_sleep_minutes.setValue(90)
        self.deep_sleep_minutes.setSuffix(" 分钟")
        form_layout.addRow("深度睡眠时长:", self.deep_sleep_minutes)
        
        # HRV数据
        form_layout.addRow(QLabel("<b>神经指标 (HRV)</b>"))
        
        self.hrv_0000 = QSpinBox()
        self.hrv_0000.setRange(0, 200)
        self.hrv_0000.setValue(65)
        self.hrv_0000.setSuffix(" ms")
        form_layout.addRow("0点 HRV:", self.hrv_0000)
        
        self.hrv_0200 = QSpinBox()
        self.hrv_0200.setRange(0, 200)
        self.hrv_0200.setValue(70)
        self.hrv_0200.setSuffix(" ms")
        form_layout.addRow("2点 HRV:", self.hrv_0200)
        
        self.hrv_0400 = QSpinBox()
        self.hrv_0400.setRange(0, 200)
        self.hrv_0400.setValue(85)
        self.hrv_0400.setSuffix(" ms")
        form_layout.addRow("4点 HRV:", self.hrv_0400)
        
        self.hrv_0600 = QSpinBox()
        self.hrv_0600.setRange(0, 200)
        self.hrv_0600.setValue(75)
        self.hrv_0600.setSuffix(" ms")
        form_layout.addRow("6点 HRV:", self.hrv_0600)
        
        self.hrv_0800 = QSpinBox()
        self.hrv_0800.setRange(0, 200)
        self.hrv_0800.setValue(70)
        self.hrv_0800.setSuffix(" ms")
        form_layout.addRow("8点 HRV:", self.hrv_0800)
        
        # 代谢数据
        form_layout.addRow(QLabel("<b>代谢指标</b>"))
        
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 200)
        self.weight_input.setValue(92.5)
        self.weight_input.setDecimals(1)
        self.weight_input.setSuffix(" kg")
        form_layout.addRow("体重:", self.weight_input)
        
        self.fatigue_score = QSpinBox()
        self.fatigue_score.setRange(1, 10)
        self.fatigue_score.setValue(3)
        form_layout.addRow("疲劳度 (1-10):", self.fatigue_score)
        
        self.carb_limit_check = QCheckBox("睡前4小时禁碳水")
        self.carb_limit_check.setChecked(True)
        form_layout.addRow("", self.carb_limit_check)
        
        # 报告内容
        form_layout.addRow(QLabel("<b>报告内容</b>"))
        
        self.report_content = QTextEdit()
        self.report_content.setPlaceholderText("可在此处编辑AI生成的健康战备报告...")
        self.report_content.setMinimumHeight(150)
        form_layout.addRow("报告内容:", self.report_content)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 保存")
        self.save_button.clicked.connect(self.save_record)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        if self.is_edit_mode:
            self.delete_button = QPushButton("🗑️ 删除")
            self.delete_button.clicked.connect(self.delete_record)
            button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_record_data(self):
        """加载现有记录数据"""
        if not self.record:
            return
        
        try:
            # 日期
            date_str = self.record.get('date', '')
            if date_str:
                date = QDate.fromString(date_str, "yyyy-MM-dd")
                if date.isValid():
                    self.date_edit.setDate(date)
            
            # 睡眠数据
            total_sleep_min = self.record.get('total_sleep_min', 450)
            hours = total_sleep_min // 60
            minutes = total_sleep_min % 60
            self.total_sleep_hours.setValue(hours)
            self.total_sleep_minutes.setValue(minutes)
            
            self.deep_sleep_minutes.setValue(self.record.get('deep_sleep_min', 60))
            
            # HRV数据
            self.hrv_0000.setValue(self.record.get('hrv_0000', 65))
            self.hrv_0200.setValue(self.record.get('hrv_0200', 70))
            self.hrv_0400.setValue(self.record.get('hrv_0400', 85))
            self.hrv_0600.setValue(self.record.get('hrv_0600', 75))
            self.hrv_0800.setValue(self.record.get('hrv_0800', 70))
            
            # 代谢数据
            self.weight_input.setValue(self.record.get('weight', 92.5))
            self.fatigue_score.setValue(self.record.get('fatigue_score', 3))
            
            carb_limit = self.record.get('carb_limit_check', True)
            if isinstance(carb_limit, str):
                carb_limit = carb_limit.lower() in ('true', '1', 'yes')
            self.carb_limit_check.setChecked(bool(carb_limit))
            
            # 报告内容
            report_content = self.record.get('report_content', '')
            self.report_content.setPlainText(report_content)
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载记录数据时出错:\n{str(e)}")
    
    def save_record(self):
        """保存记录"""
        try:
            # 收集数据
            date_str = self.date_edit.date().toString("yyyy-MM-dd")
            
            total_sleep_min = self.total_sleep_hours.value() * 60 + self.total_sleep_minutes.value()
            deep_sleep_min = self.deep_sleep_minutes.value()
            deep_sleep_ratio = deep_sleep_min / total_sleep_min if total_sleep_min > 0 else 0
            
            data_dict = {
                'date': date_str,
                'total_sleep_min': total_sleep_min,
                'deep_sleep_min': deep_sleep_min,
                'deep_sleep_ratio': deep_sleep_ratio,
                'hrv_0000': self.hrv_0000.value(),
                'hrv_0200': self.hrv_0200.value(),
                'hrv_0400': self.hrv_0400.value(),
                'hrv_0600': self.hrv_0600.value(),
                'hrv_0800': self.hrv_0800.value(),
                'weight': self.weight_input.value(),
                'fatigue_score': self.fatigue_score.value(),
                'carb_limit_check': self.carb_limit_check.isChecked(),
                'report_content': self.report_content.toPlainText()
            }
            
            # 验证数据
            if total_sleep_min <= 0:
                QMessageBox.warning(self, "警告", "总睡眠时长必须大于0")
                return
            
            if deep_sleep_min < 0 or deep_sleep_min > total_sleep_min:
                QMessageBox.warning(self, "警告", "深度睡眠时长无效")
                return
            
            if not (1 <= self.fatigue_score.value() <= 10):
                QMessageBox.warning(self, "警告", "疲劳度评分必须在1-10之间")
                return
            
            # 保存到数据库
            from src.bio.database import save_daily_log
            success = save_daily_log(data_dict)
            
            if success:
                QMessageBox.information(self, "成功", "记录已保存")
                self.accept()
            else:
                QMessageBox.warning(self, "警告", "保存失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存时发生错误:\n{str(e)}")
    
    def delete_record(self):
        """删除记录"""
        if not self.record:
            return
        
        date_str = self.record.get('date', '')
        if not date_str:
            QMessageBox.warning(self, "警告", "无法获取记录日期")
            return
        
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除日期为 {date_str} 的记录吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from src.bio.database import delete_log
            if delete_log(date_str):
                QMessageBox.information(self, "成功", "记录已删除")
                self.accept()
            else:
                QMessageBox.warning(self, "警告", "删除失败")

class ReportViewDialog(QDialog):
    """报告查看对话框"""
    
    def __init__(self, report_content, parent=None):
        super().__init__(parent)
        self.report_content = report_content
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("📄 健康战备报告")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # 报告内容
        self.report_text = QTextEdit()
        self.report_text.setPlainText(self.report_content)
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Consolas", 10))
        self.report_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.report_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.copy_button = QPushButton("📋 复制到剪贴板")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_button)
        
        self.save_button = QPushButton("💾 保存为文件")
        self.save_button.clicked.connect(self.save_to_file)
        button_layout.addWidget(self.save_button)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def copy_to_clipboard(self):
        """复制到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.report_content)
        QMessageBox.information(self, "成功", "报告已复制到剪贴板")
    
    def save_to_file(self):
        """保存为文件"""
        default_name = f"健康报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存报告", default_name, "Markdown文件 (*.md);;文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.report_content)
                QMessageBox.information(self, "成功", f"报告已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

# 用于导入
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    dialog = DatabaseManagerDialog()
    dialog.exec()
