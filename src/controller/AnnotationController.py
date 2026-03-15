from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.service.AnnotationService import AnnotationService
from src.widgets.AnnotationWidget import Annotation


class AnnotationController(Annotation):
    def __init__(self, baseModelClass:BaseModel, viewModel:OrthoViewerModel, widget):
        super(AnnotationController).__init__()

        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.widget = widget

        self.annotationService = AnnotationService(self.baseModelClass, self.viewModel)

        self.init_widget()

        self.pushButton_clear.clicked.connect(self.label_clear)
        self.pushButton_undo.clicked.connect(self.label_undo)
        self.pushButton_redo.clicked.connect(self.label_redo)


    def label_clear(self):
        self.annotationService.label_clear()

    def label_undo(self):
        self.annotationService.label_undo()


    def label_redo(self):
        self.annotationService.label_redo()
