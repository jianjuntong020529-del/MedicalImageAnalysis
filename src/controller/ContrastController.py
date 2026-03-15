from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.service.ConstantService import ContrastService
from src.utils.globalVariables import getFileIsEmpty
from src.widgets.ContrastWidget import Contrast


class ContrastController(Contrast):
    def __init__(self,baseModelClass: BaseModel, viewModel: OrthoViewerModel, widget):
        super(ContrastController).__init__()
        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.widget = widget
        # 初始化对比度调整栏窗口
        self.init_widget()

        self.contrastService = ContrastService(self.baseModelClass, self.viewModel)

        self.window_level_slider.valueChanged.connect(self.levelSliderValueChange)
        self.window_width_slider.valueChanged.connect(self.widthSliderValueChange)


    def widthSliderValueChange(self):
        if getFileIsEmpty():
            print("未导入文件，不能修改窗位和窗宽数值")
            return
        self.contrastService.widthSliderValueChange()

    def levelSliderValueChange(self):
        if getFileIsEmpty():
            print("未导入文件，不能修改窗位和窗宽数值")
            return
        self.contrastService.levelSliderValueChange()



