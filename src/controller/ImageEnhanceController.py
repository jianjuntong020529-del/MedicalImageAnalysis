# -*- coding: utf-8 -*-
"""
图像增强控制器 — 连接 Widget 信号与 Service 管线，并刷新三个正交视图
"""
import os
from src.widgets.ImageEnhanceWidget import ImageEnhanceWidget
from src.service.ImageEnhanceService import ImageEnhanceService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ImageEnhanceController(ImageEnhanceWidget):

    def __init__(self, base_model, ortho_viewer_model, parent=None):
        super().__init__(parent)
        self._base_model   = base_model
        self._viewer_model = ortho_viewer_model
        self._service      = ImageEnhanceService(base_model)

        # 暴露 widget 属性，与其他 controller 保持一致
        self.widget_image_enhance = self

        self.apply_requested.connect(self._on_apply)
        self.reset_requested.connect(self._on_reset)
        self.export_requested.connect(self._on_export)

    # ── 槽函数 ────────────────────────────────────────────────────────────────

    def _on_apply(self, enabled: dict, params: dict):
        """更新 Service 参数 → 重建管线 → 刷新三个正交视图"""
        for k, v in enabled.items():
            self._service.set_enabled(k, v)
        for k, v in params.items():
            self._service.set_param(k, v)

        output = self._service.get_output()
        self._update_viewers(output)
        logger.info(f"Image enhance applied: enabled={enabled}, params={params}")

    def _on_reset(self):
        """恢复原始数据到视图"""
        output = self._base_model.imageReader.GetOutput()
        self._update_viewers(output)
        logger.info("Image enhance reset to original")

    def _on_export(self):
        """导出当前 XY 切片为 PNG"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import vtk

        viewer = self._viewer_model.AxialOrthoViewer.viewer
        if viewer is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, '导出切片', 'enhanced_slice.png',
            'PNG Image (*.png);;JPEG Image (*.jpg)'
        )
        if not path:
            return

        try:
            w2i = vtk.vtkWindowToImageFilter()
            w2i.SetInput(viewer.GetRenderWindow())
            w2i.Update()

            ext = os.path.splitext(path)[1].lower()
            if ext == '.jpg':
                writer = vtk.vtkJPEGWriter()
            else:
                writer = vtk.vtkPNGWriter()
            writer.SetFileName(path)
            writer.SetInputConnection(w2i.GetOutputPort())
            writer.Write()
            QMessageBox.information(self, '导出成功', f'切片已保存至：\n{path}')
            logger.info(f"Slice exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, '导出失败', str(e))
            logger.error(f"Export failed: {e}", exc_info=True)

    # ── 内部 ──────────────────────────────────────────────────────────────────

    def _update_viewers(self, image_data):
        """将增强后的 vtkImageData 推送到三个正交视图并刷新"""
        for ortho in (
            self._viewer_model.AxialOrthoViewer,
            self._viewer_model.SagittalOrthoViewer,
            self._viewer_model.CoronalOrthoViewer,
        ):
            try:
                ortho.viewer.SetInputData(image_data)
                ortho.viewer.UpdateDisplayExtent()
                ortho.viewer.Render()
            except Exception as e:
                logger.warning(f"Viewer update failed: {e}")
