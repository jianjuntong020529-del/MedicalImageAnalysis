import vtk
from vtkmodules.vtkImagingCore import vtkImageShiftScale

from src.utils.globalVariables import getDirPath


class BaseModel:
    def __init__(self) -> None:
        # Reader
        self.imageReader = vtk.vtkDICOMImageReader()
        self.imageReader.SetDirectoryName(getDirPath())
        self.imageReader.Update()

        # Update the data information
        self.update_data_information()

        # Picker
        self.picker = vtk.vtkPicker()
        self.picker.SetTolerance(0.05)

    # update data information
    def update_data_information(self):
        print("update data information")
        # Calculate the scaler range of data
        self.scalerRange = self.imageReader.GetOutput().GetScalarRange()

        # Calculate the dimensions of data
        self.imageDimensions = self.imageReader.GetOutput().GetDimensions()

        # Calculate the bounds of data
        self.bounds = self.imageReader.GetOutput().GetBounds()

        # origin
        self.origin = self.imageReader.GetOutput().GetOrigin()

        # spcing
        self.spacing = self.imageReader.GetOutput().GetSpacing()

        # center
        self.center = self.imageReader.GetOutput().GetCenter()



