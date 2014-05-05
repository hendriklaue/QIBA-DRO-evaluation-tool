#!/usr/bin/env python

import os.path
import wx

import dicom
import pylab
import numpy
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure



class MainWindow(wx.Frame):
    ''' this is the main window of the QIBA evaluate tool
    '''
    applicationName = "QIBA evaluate tool"
    DICOMSeries = []
    VeList = [0.01, 0.05, 0.1, 0.2,0.5]
    KtransList = [0.01, 0.02, 0.05, 0.1, 0.2, 0.35]
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title = self.applicationName, size = (900, 600))
        self.SetMinSize((900, 600))
        self.CenterOnScreen()

        self.CreateStatusBar()
        self.SetStatusText("Welcome to " + self.applicationName + "!")

        self.SetupMenubar()
        self.SetupLayoutMain()

    def SetupMenubar(self):
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        OnImport = fileMenu.Append(wx.ID_ANY, "&Import...\tCtrl+I", "Import a new DICOM file.")
        OnExport = fileMenu.Append(wx.ID_ANY, "&Export...\tCtrl+E", "Export the result as PDF/EXCEL file.")
        fileMenu.AppendSeparator()
        OnExit = fileMenu.Append(wx.ID_ANY, "&Quit\tCtrl+Q", "Quit " + self.applicationName)

        aboutMenu = wx.Menu()
        OnThirdPartyLib = aboutMenu.Append(wx.ID_ANY, "Third party libraries...", "Third party libraries used in this application.")
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

        menubar.Bind(wx.EVT_MENU, self.OnImport, OnImport)
        menubar.Bind(wx.EVT_MENU, self.OnExport, OnExport)
        menubar.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        menubar.Bind(wx.EVT_MENU, self.OnShowThirdParty, OnThirdPartyLib)
        menubar.Bind(wx.EVT_MENU, self.OnShowAbout, OnAboutApp)

        menubar.Append(fileMenu, "&File")
        menubar.Append(aboutMenu, "&About")
        self.SetMenuBar(menubar)

    def SetupLayoutLeft(self):
        pass
        # Manage the tree list of the parameters on the left panel.
        # sizer for the left column
        #sizer = wx.BoxSizer(wx.VERTICAL)
        #self.parameterTree.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnSelChanged, id=1)
        #self.leftPanel.SetSizer(sizer)


    def SetupLayoutRight(self):
        # set up the right panel with notebook
        self.noteBookRight = wx.Notebook(self.rightPanel)  #, style=wx.SUNKEN_BORDER)
        self.page1 = wx.Panel(self.noteBookRight)
        self.page2 = wx.Panel(self.noteBookRight)
        self.noteBookRight.AddPage(self.page1, "Statistics Viewer")
        self.noteBookRight.AddPage(self.page2, "Result Review")

        # set a canvas on page 1
        self.figure = Figure()
        self.canvas = FigureCanvas(self.page1,-1, self.figure)

        # sizer for the right panel
        sizer = wx.BoxSizer()
        sizer.Add(self.noteBookRight, 1, wx.EXPAND)
        self.rightPanel.SetSizer(sizer)
        self.rightPanel.Layout()


    def DrawScatterPlot(self, pixels):
        # try to draw scatter plots on page 1
        # the display is fixed, just to show the possibility of showing the imported data
        # next step is to bind the treelist with display
        y = pixels[1]
        x = [[Ve]*100 for Ve in self.VeList]

        self.scatterPlot = self.figure.add_subplot(1,1,1)
        self.scatterPlot.clear()
        self.scatterPlot.scatter(x, y)

        self.canvas.draw()


    def SetupLayoutMain(self):
        self.leftPanel = wx.Panel(self, size = (200, 600))
        self.rightPanel = wx.Panel(self, size = (700, 600))

        self.SetupLayoutLeft()
        self.SetupLayoutRight()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.leftPanel, 0, flag = wx.EXPAND)  # second argument being 0 to make sure that it wont expand
        sizer.Add(self.rightPanel, 1, flag = wx.EXPAND)  # second argument is for expansion proportion
        self.SetSizer(sizer)


    def OnImport(self, event):
        """import a selected file."""
        dlg = wx.FileDialog(self, 'Choose a file to add', '', '', "DICM file(*.dcm) | *.dcm", wx.OPEN | wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            pathList = dlg.GetPaths()
            fileList = dlg.GetFilenames()
            for path in pathList:
                try:
                    path.endswith(".dcm")
                    self.DICOMSeries.append(ImportedDICOM(path))
                except ImportError:
                    print "File type not supported!"

            # show the tree list of the imported DICOM files
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(ParameterTree(self.leftPanel, fileList), 1, flag = wx.EXPAND)
            self.leftPanel.SetSizer(sizer)
            self.leftPanel.Layout()

            # show the scatter plot
            self.DrawScatterPlot(self.DICOMSeries[0].rearrangedPixels) # simply show the first DICOM
            self.rightPanel.Layout()


    def ShowPreview(self, filePath):
        # by now this function is not used.
        ds = dicom.read_file(filePath)
        pylab.imshow(ds.pixel_array, cmap=pylab.cm.bone)
        pylab.show()

        '''
        # test for tiff image file display and scrolled window
        self.newImage = wx.Image(filePath)
        w, h = self.newImage.GetSize()
        resizedImage = self.newImage.Scale(128, 128*h/w)  # restrict the width and set the height accordingly
        showImage = wx.StaticBitmap(self.scrollPreview, -1,wx.BitmapFromImage(resizedImage))
        textName = wx.StaticText(self.scrollPreview, -1, "lena", style=wx.ALIGN_CENTRE)
        self.scrollSizer.Add(showImage, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER, border = 25)
        self.scrollSizer.Add(textName, 1, wx.EXPAND)
        self.scrollPreview.SetSizerAndFit(self.scrollSizer)
        self.leftPanel.Layout()  # to refresh the scroll window
        '''


    def OnExport(self, event):
        print "TODO: add export function"

    def OnQuit(self, event):
        self.Close()

    def OnShowThirdParty(self):
        print "TODO: add third party libraries information here"

    def OnShowAbout(self):
        print "TODO: add application information here"

class ParameterTree(wx.TreeCtrl):
    ''' The customized TreeCtrl class, to index the display of the scatter plot accordingly
    '''
    DICOMs = []
    Ve = []
    Ktrans = []
    def __init__(self, parent, nodeNames):
        wx.TreeCtrl.__init__(self, parent)
        root = self.AddRoot('just a root name')  # a name that could distinguish the imported DICOM
        for i, node in enumerate(nodeNames):
            self.DICOMs.append(self.AppendItem(root, node))
            self.Ve.append(self.AppendItem(self.DICOMs[i], 'Ve'))
            self.Ktrans.append(self.AppendItem(self.DICOMs[i], 'Ktrans'))

            # the parameter should be able to be loaded from DICOM file.
            for p1 in MainWindow.VeList:
                self.AppendItem(self.Ve[i], str(p1))
            for p2 in MainWindow.KtransList:
                self.AppendItem(self.Ktrans[i], str(p2))

            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnActivated, self)
    def OnActivated(self, event):
        # get the item in order to display the plot
        print self.GetItemText(event.GetItem())

class ImportedDICOM:
    ''' This class manages the imported DICOM files.
    The parameters like the size of a patch, the arrange of patches in an image, should be able to be read from the images.
    '''
    def __init__(self, path):
        self.extraPatchNr = 2
        self.patchPxlNr = 10

        self.nrOfRows = 0
        self.nrOfColumns = 0
        self.rearrangedPixels = []

        self.AddNew(path)

    def AddNew(self, path):
        ds = dicom.read_file(path)

        self.nrOfRows = ds.Rows/self.patchPxlNr - self.extraPatchNr
        self.nrOfColumns = ds.Columns/self.patchPxlNr

        self.rearrangedPixels.extend(self.RearrangePixels(ds.pixel_array, self.nrOfRows, self.nrOfColumns))

    def RearrangePixels(self, pxlArr, rows, columns):
        patchTemp = [[[] for j in range(columns)] for i in range(rows) ]
        patchCell = []
        for i in range(rows):
            for j in range(columns):
                for k in range(self.patchPxlNr):
                    patchCell.extend(pxlArr[(i + 1) * self.patchPxlNr + k ][j : j + self.patchPxlNr])
                # patchTemp.extend(patchCell)
                patchTemp[i][j] = patchCell
                patchCell = []
        return patchTemp



if __name__ == "__main__":
    Application = wx.App()
    window = MainWindow(None)
    window.Show()
    Application.MainLoop()

# TODO also add remove file function