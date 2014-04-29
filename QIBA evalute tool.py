#!/usr/bin/env python

import os.path
import wx

import dicom
import pylab

import random
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure



class MainWindow(wx.Frame):
    applicationName = "QIBA evaluate tool"
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
        # add the scroll bar to the left panel
        self.scrollPreview = wx.ScrolledWindow(self.leftPanel, -1)  #, style = wx.ALWAYS_SHOW_SB)
        #self.scrollSizer = wx.FlexGridSizer(cols = 1, vgap = 10)
        self.scrollPreview.SetScrollbars(1,1,1,1)

        # sizer for the left column
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.scrollPreview, 1, flag = wx.EXPAND)
        self.leftPanel.SetSizer(sizer)

    def SetupLayoutRight(self):
        noteBookRight = wx.Notebook(self.rightPanel)  #, style=wx.SUNKEN_BORDER)
        page1 = wx.Panel(noteBookRight)
        page2 = wx.Panel(noteBookRight)
        noteBookRight.AddPage(page1, "Statistics Viewer")
        noteBookRight.AddPage(page2, "Result Review")

        # try to draw scatter plots on page 1
        # the repetition of the code is just for demonstration purpose
        # could also have other forms to show the plots
        x = [random.random() for i in range(25)]
        y = [random.random() for i in range(25)]
        self.figure = Figure()
        self.canvas = FigureCanvas(page1,-1, self.figure)

        self.scatterPlot1 = self.figure.add_subplot(2,2,1)
        self.scatterPlot1.clear()
        self.scatterPlot1.scatter(x, y)

        self.scatterPlot2 = self.figure.add_subplot(2,2,2)
        self.scatterPlot2.clear()
        self.scatterPlot2.scatter(x, y)

        self.scatterPlot3 = self.figure.add_subplot(2,2,3)
        self.scatterPlot3.clear()
        self.scatterPlot3.scatter(x, y)

        self.scatterPlot4 = self.figure.add_subplot(2,2,4)
        self.scatterPlot4.clear()
        self.scatterPlot4.scatter(x, y)

        self.canvas.draw()


        # sizer for the right column
        sizer = wx.BoxSizer()
        sizer.Add(noteBookRight, 1, wx.EXPAND)
        self.rightPanel.SetSizer(sizer)

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
            # fileList = dlg.GetFilename()
            for path in pathList:
                try:
                    path.endswith(".dcm")
                    CaseOne = ImportedDICOM()
                    CaseOne.addNew(path)
                    print ImportedDICOM.fileNames
                    # self.ImportImage(path)
                except ImportError:
                    print "file type not supported!"


    def ImportImage(self, filePath):
        ds = dicom.read_file(filePath)
        #read header data
        print ds

        # show DICOM image with matplotlib
        pylab.imshow(ds.pixel_array, cmap=pylab.cm.bone)
        pylab.show()

        return
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


    def OnExport(self, event):
        print "TODO: add export function"

    def OnQuit(self, event):
        self.Close()

    def OnShowThirdParty(self):
        print "TODO: add third party libraries information here"

    def OnShowAbout(self):
        print "TODO: add application information here"

    def plot(self, event):
        self.testScatter.plot()


class ImportedDICOM():
    ''' The class that manage the imported DICOM files
    '''
    fileNames = []

    def addNew(self, path):
        head, tail = os.path.split(path)
        self.fileNames.append(tail)


if __name__ == "__main__":
    Application = wx.App()
    window = MainWindow(None)
    window.Show()
    Application.MainLoop()

# TODO also add remove file function
