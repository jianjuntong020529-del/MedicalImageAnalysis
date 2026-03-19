# -*- coding: utf-8 -*-
"""
口腔牙齿测量控制器

职责：
  1. 响应 Widget 的信号（加载文件、开始测量、导出PDF）
  2. 调用 ToothMeasurementEngine 执行计算
  3. 将结果回填到 Widget
  4. PDF 报告导出（使用 reportlab，若未安装则降级为 CSV）
"""

import os
import datetime
from PyQt5 import QtWidgets, QtCore

from src.widgets.ToothMeasurementWidget import ToothMeasurementWidget
from src.core.tooth_measurement import ToothMeasurementEngine, measure_from_nifti, ToothMetrics


class ToothMeasurementController(QtCore.QObject):
    """
    参数
    ----
    parent : QWidget，作为浮动窗口的父控件
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self._nii_path: str = ""
        self._results: dict = {}
        self._seg_data = None    # numpy 分割数据（用于三视图）
        self._spacing = (1, 1, 1)

        # 创建面板（独立浮动窗口，不设父级，避免被嵌入主窗口）
        self.widget = ToothMeasurementWidget()
        self.widget.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.WindowCloseButtonHint |
            QtCore.Qt.WindowMinMaxButtonsHint
        )
        self.widget.resize(1100, 700)

        # 连接信号
        self.widget.load_nii_requested.connect(self._on_load_nii)
        self.widget.measure_requested.connect(self._on_measure)
        self.widget.export_pdf_requested.connect(self._on_export_pdf)
        self.widget.tooth_selected.connect(self._on_tooth_selected)

    # ══════════════════════════════════════════════════════════════════════════
    # 公开方法
    # ══════════════════════════════════════════════════════════════════════════

    def show(self):
        """显示测量面板"""
        self.widget.show()
        self.widget.raise_()
        self.widget.activateWindow()

    def hide(self):
        self.widget.hide()

    def toggle(self):
        if self.widget.isVisible():
            self.hide()
        else:
            self.show()

    # ══════════════════════════════════════════════════════════════════════════
    # 信号处理
    # ══════════════════════════════════════════════════════════════════════════

    def _on_load_nii(self):
        """打开文件对话框，加载 NIfTI 分割文件"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.widget,
            "选择 NIfTI 分割文件",
            "",
            "NIfTI Files (*.nii *.nii.gz);;All Files (*)"
        )
        if not path:
            return
        if not os.path.exists(path):
            self._warn("文件不存在", f"找不到文件：{path}")
            return

        self._nii_path = path
        self._seg_data = None
        self.widget.clear()
        self.widget.set_file_path(path)
        self.widget.set_status("文件已加载，点击「开始测量」执行计算")

        # 加载后立即把分割数据传给三视图，不需要等测量完成
        try:
            import nibabel as nib
            import numpy as np
            img = nib.load(path)
            self._seg_data = np.asarray(img.get_fdata(), dtype=np.int32)
            self._spacing = tuple(float(s) for s in img.header.get_zooms()[:3])
            self.widget.triview_tab.set_data(None, self._seg_data, self._spacing)
        except ImportError:
            pass  # nibabel 未安装，三视图暂不显示
        except Exception as e:
            self.widget.set_status(f"三视图加载失败：{e}", "#f5a623")

    def _on_measure(self):
        """执行测量计算（在后台线程中运行，避免界面卡顿）"""
        if not self._nii_path:
            self._warn("未加载文件", "请先加载 NIfTI 分割文件")
            return

        self.widget.set_status("正在计算，请稍候...", "#5bc8f5")
        self.widget.btn_measure.setEnabled(False)
        QtWidgets.QApplication.processEvents()

        try:
            results, spacing = measure_from_nifti(self._nii_path)
            self._results = results
            self._spacing = spacing

            if not results:
                self._warn("测量结果为空", "未在分割文件中找到有效牙齿（label 1~32）")
                self.widget.set_status("未找到有效牙齿数据", "#f5a623")
                return

            self.widget.populate_results(results)

            # 如果 _seg_data 还没加载（nibabel 在 _on_load_nii 已加载），直接传给三视图
            if self._seg_data is not None:
                self.widget.triview_tab.set_data(None, self._seg_data, self._spacing)

        except ImportError:
            self._warn(
                "缺少依赖库",
                "需要安装 nibabel：\npip install nibabel\n\n安装后重启软件即可使用。"
            )
            self.widget.set_status("缺少 nibabel 库，请安装后重试", "#f5a623")
        except Exception as e:
            self._warn("测量失败", f"计算过程中发生错误：\n{str(e)}")
            self.widget.set_status(f"测量失败：{str(e)}", "#f5a623")
        finally:
            self.widget.btn_measure.setEnabled(True)

    def _on_export_pdf(self):
        """导出 PDF 报告（优先 reportlab，降级为 CSV）"""
        if not self._results:
            self._warn("无数据", "请先执行测量")
            return

        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.widget,
            "保存报告",
            f"牙齿测量报告_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "PDF 文件 (*.pdf);;CSV 文件 (*.csv)"
        )
        if not save_path:
            return

        try:
            if save_path.lower().endswith(".pdf"):
                self._export_pdf(save_path)
            else:
                self._export_csv(save_path)
            QtWidgets.QMessageBox.information(
                self.widget, "导出成功", f"报告已保存至：\n{save_path}"
            )
        except Exception as e:
            self._warn("导出失败", str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # PDF 导出
    # ══════════════════════════════════════════════════════════════════════════

    def _export_pdf(self, path: str):
        """使用 reportlab 生成 PDF 报告"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                SimpleDocTemplate, Table, TableStyle, Paragraph,
                Spacer, HRFlowable
            )
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            raise ImportError(
                "需要安装 reportlab：pip install reportlab\n"
                "或选择导出为 CSV 格式"
            )

        # 尝试注册中文字体（优先使用系统字体）
        font_name = self._register_chinese_font()

        doc = SimpleDocTemplate(
            path, pagesize=A4,
            leftMargin=20*mm, rightMargin=20*mm,
            topMargin=20*mm, bottomMargin=20*mm
        )

        styles = getSampleStyleSheet()
        # 自定义样式
        title_style = ParagraphStyle(
            'Title', fontName=font_name, fontSize=16,
            textColor=colors.HexColor('#1a73e8'), spaceAfter=6
        )
        sub_style = ParagraphStyle(
            'Sub', fontName=font_name, fontSize=10,
            textColor=colors.HexColor('#555555'), spaceAfter=4
        )
        warn_style = ParagraphStyle(
            'Warn', fontName=font_name, fontSize=10,
            textColor=colors.HexColor('#e65100'), spaceAfter=3
        )
        normal_style = ParagraphStyle(
            'Normal2', fontName=font_name, fontSize=10,
            textColor=colors.black, spaceAfter=3
        )

        story = []
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ── 标题 ──────────────────────────────────────────────────────────────
        story.append(Paragraph("全口牙齿 CBCT 分割测量分析报告", title_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1a73e8')))
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(f"报告生成时间：{now}", sub_style))
        story.append(Paragraph(f"分割文件：{os.path.basename(self._nii_path)}", sub_style))
        story.append(Paragraph("影像类型：CBCT  |  测量单位：长度(mm)、角度(°)、体积(mm³)", sub_style))
        story.append(Spacer(1, 6*mm))

        # ── 测量结果总表 ──────────────────────────────────────────────────────
        story.append(Paragraph("测量结果总表", ParagraphStyle(
            'H2', fontName=font_name, fontSize=12,
            textColor=colors.HexColor('#1a73e8'), spaceAfter=4
        )))

        headers = ["牙位", "牙体长\n(mm)", "牙冠长\n(mm)", "牙根长\n(mm)",
                   "近远中宽\n(mm)", "颊舌厚\n(mm)", "倾斜角\n(°)", "体积\n(mm³)", "状态"]
        table_data = [headers]

        for fdi in sorted(self._results.keys()):
            m = self._results[fdi]
            status = "⚠异常" if m.warnings else "✓正常"
            table_data.append([
                str(fdi),
                f"{m.total_length:.1f}",
                f"{m.crown_length:.1f}",
                f"{m.root_length:.1f}",
                f"{m.md_width:.1f}",
                f"{m.bl_thickness:.1f}",
                f"{m.angulation:.1f}",
                f"{m.volume:.0f}",
                status,
            ])

        col_widths = [15*mm, 18*mm, 18*mm, 18*mm, 20*mm, 18*mm, 16*mm, 18*mm, 15*mm]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0),  colors.HexColor('#1a73e8')),
            ('TEXTCOLOR',   (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',    (0, 0), (-1, -1), font_name),
            ('FONTSIZE',    (0, 0), (-1, -1), 9),
            ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('TOPPADDING',  (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 8*mm))

        # ── 异常诊断提示 ──────────────────────────────────────────────────────
        all_warnings = []
        for fdi in sorted(self._results.keys()):
            for w in self._results[fdi].warnings:
                all_warnings.append(f"FDI {fdi}：{w}")

        story.append(Paragraph("异常诊断提示", ParagraphStyle(
            'H2', fontName=font_name, fontSize=12,
            textColor=colors.HexColor('#e65100'), spaceAfter=4
        )))
        if all_warnings:
            for w in all_warnings:
                story.append(Paragraph(f"• {w}", warn_style))
        else:
            story.append(Paragraph("✓ 未发现明显异常", normal_style))

        story.append(Spacer(1, 6*mm))

        # ── 结论 ──────────────────────────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(
            "本报告基于全口牙齿三维分割结果自动生成，完成牙体长度、冠根比、"
            "近远中宽度、颊舌厚度、牙根倾斜角度及牙齿体积等测量，"
            "可辅助正畸、修复、种植临床诊断。本报告仅供参考，最终诊断请结合临床。",
            normal_style
        ))

        doc.build(story)

    def _register_chinese_font(self) -> str:
        """
        尝试注册系统中文字体，返回可用字体名称。
        优先 Windows 微软雅黑，其次 macOS/Linux 常见字体，
        最后降级为 Helvetica（不支持中文但不报错）。
        """
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            candidates = [
                ("msyh",    r"C:\Windows\Fonts\msyh.ttc"),       # 微软雅黑
                ("simhei",  r"C:\Windows\Fonts\simhei.ttf"),      # 黑体
                ("simsun",  r"C:\Windows\Fonts\simsun.ttc"),      # 宋体
                ("PingFang", "/System/Library/Fonts/PingFang.ttc"),# macOS
                ("NotoSansCJK", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            ]
            for name, fp in candidates:
                if os.path.exists(fp):
                    pdfmetrics.registerFont(TTFont(name, fp))
                    return name
        except Exception:
            pass
        return "Helvetica"

    # ══════════════════════════════════════════════════════════════════════════
    # CSV 降级导出
    # ══════════════════════════════════════════════════════════════════════════

    def _export_csv(self, path: str):
        """导出为 CSV 格式（不依赖 reportlab）"""
        import csv
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "牙位", "牙体长度(mm)", "牙冠长度(mm)", "牙根长度(mm)",
                "近远中宽(mm)", "颊舌厚(mm)", "倾斜角(°)", "体积(mm³)", "异常提示"
            ])
            for fdi in sorted(self._results.keys()):
                m = self._results[fdi]
                writer.writerow([
                    fdi,
                    f"{m.total_length:.2f}",
                    f"{m.crown_length:.2f}",
                    f"{m.root_length:.2f}",
                    f"{m.md_width:.2f}",
                    f"{m.bl_thickness:.2f}",
                    f"{m.angulation:.1f}",
                    f"{m.volume:.1f}",
                    "；".join(m.warnings) if m.warnings else "正常",
                ])

    # ══════════════════════════════════════════════════════════════════════════
    # 辅助
    # ══════════════════════════════════════════════════════════════════════════

    def _on_tooth_selected(self, fdi: int):
        """标签选中时同步三视图高亮"""
        self.widget.triview_tab.set_active_fdi(fdi)
        self.widget.threed_tab.highlight_fdi(fdi)

    def _warn(self, title: str, msg: str):
        QtWidgets.QMessageBox.warning(self.widget, title, msg)
