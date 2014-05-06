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
    DICOMSeries = {}
    refDICOMS = {}
    rescaleIntercept = 0
    rescaleSlope = 0
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
        OnImport = fileMenu.Append(wx.ID_ANY, "&Import...\tCtrl+I", "Import DICOM files, including reference files.")
        OnExport = fileMenu.Append(wx.ID_ANY, "&Export...\tCtrl+E", "Export the result as PDF/EXCEL file.")
        fileMenu.AppendSeparator()
        OnClearRef = fileMenu.Append(wx.ID_ANY, "&Clear the reference DICOMs", "Clear the DICOMs which were imported for parameter mapping.")
        fileMenu.AppendSeparator()
        OnExit = fileMenu.Append(wx.ID_ANY, "&Quit\tCtrl+Q", "Quit " + self.applicationName)

        aboutMenu = wx.Menu()
        OnThirdPartyLib = aboutMenu.Append(wx.ID_ANY, "Third party libraries...", "Third party libraries used in this application.")
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

        menubar.Bind(wx.EVT_MENU, self.OnImport, OnImport)
        menubar.Bind(wx.EVT_MENU, self.OnExport, OnExport)
        menubar.Bind(wx.EVT_MENU, self.OnClearRef, OnClearRef)
        menubar.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        menubar.Bind(wx.EVT_MENU, self.OnShowThirdParty, OnThirdPartyLib)
        menubar.Bind(wx.EVT_MENU, self.OnAbout, OnAboutApp)

        menubar.Append(fileMenu, "&File")
        menubar.Append(aboutMenu, "&About")
        self.SetMenuBar(menubar)

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

        # set sizer for the canvas
        sizer = wx.BoxSizer()
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.page1.SetSizer(sizer)

        # sizer for the right panel
        sizer = wx.BoxSizer()
        sizer.Add(self.noteBookRight, 1, wx.EXPAND)
        self.rightPanel.SetSizer(sizer)
        self.rightPanel.Layout()



    def SetupLayoutMain(self):
        self.leftPanel = wx.Panel(self, size = (200, 600))
        self.rightPanel = wx.Panel(self, size = (700, 600))

        self.SetupLayoutRight()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.leftPanel, 2, flag = wx.EXPAND)  # second argument being 0 to make sure that it wont expand
        sizer.Add(self.rightPanel, 7, flag = wx.EXPAND)  # second argument is for expansion proportion
        self.SetSizer(sizer)


    def OnImport(self, event):
        """import a selected file."""
        dlg = wx.FileDialog(self, 'Choose a file to add', '', '', "DICM file(*.dcm) | *.dcm", wx.OPEN | wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.DICOMSeries.clear()
            pathList = dlg.GetPaths()
            fileList = dlg.GetFilenames()
            filePathDict = {}
            for (path, file) in zip(pathList, fileList):
                filePathDict[file] = path

            # if the parameter map are not available, pop out dialog. TODO: very redundant, should be improved later.
            if not ('Ktrans.dcm' in fileList) | ('Ktrans.dcm' in self.refDICOMS) | ('Ve.dcm' in fileList) | ('Ve.dcm' in self.refDICOMS):
                dlg = wx.MessageDialog(self,  'No reference DICOM imported! \nPlease Import reference DICOM files.', 'Reference DICOM needed', wx.OK)
                dlg.ShowModal()
                return

            # load the reference DICOMS in advance if necessary, in order to have the rescale factors
            for ref in ['Ve.dcm', 'Ktrans.dcm']:
                if ref in fileList:
                    self.refDICOMS[ref] = ImportedDICOM(filePathDict[ref], ref)

            # load the rest DICOMs
            for (path, file) in zip(pathList, fileList):
                if file in ['Ve.dcm', 'Ktrans.dcm']:
                    continue
                self.DICOMSeries[file] = ImportedDICOM(path, file)

            # show the tree list of the imported DICOM files
            # TODO: bug here! Loading files multiple times cannot be dispalyed correctly.
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(ParameterTree(self.leftPanel), 1, flag = wx.EXPAND)
            self.leftPanel.SetSizer(sizer)
            self.leftPanel.Layout()

    def DrawPlot(self, testPixels, refPixles):
        # draw a plot on page 1 when an item is selected in the tree list
        self.scatterPlot = self.figure.add_subplot(1,1,1)
        self.scatterPlot.clear()
        self.scatterPlot.scatter(refPixles, testPixels)

        self.canvas.draw()
        self.rightPanel.Layout()

    def OnClearRef(self):
        self.refDICOMS.clear()
        self.SetStatusText("Reference DICOMs cleared.")

    def OnExport(self, event):
        print "TODO: add export function"

    def OnQuit(self, event):
        self.Close()

    def OnShowThirdParty(self):
        # could be added to the about dialog?
        pass

    def OnAbout(self, envent):
        description = """This is the description of this software."""

        licence = """This is the Licence of the software."""


        info = wx.AboutDialogInfo()

        # set icon here
        # info.SetIcon(wx.Icon('hunter.png', wx.BITMAP_TYPE_PNG))

        info.SetName('QIBA evaluate tool')
        info.SetVersion('1.0')
        info.SetDescription(description)
        # set copyright here
        # info.SetCopyright('(C) 2007 - 2011 Jan Bodnar')

        # set website
        # info.SetWebSite('http://www.zetcode.com')
        info.SetLicence(licence)

        # set developer
        # info.AddDeveloper('Jan Bodnar')
        # set document writer
        # info.AddDocWriter('Jan Bodnar')

        wx.AboutBox(info)

class ParameterTree(wx.TreeCtrl):
    ''' The customized TreeCtrl class, to index the display of the scatter plot accordingly
    '''
    def __init__(self, parent):
        wx.TreeCtrl.__init__(self, parent)
        self.root = self.AddRoot('Imported DICOM files')  # a name that could distinguish the imported DICOM
        treeListItems = []
        parameterList = []

        # try to abstract the parameter map from the DICOM, in order to show in the tree list
        if 'Ktrans.dcm' in MainWindow.refDICOMS:
                parameterList.append(['Ktrans', [str(p) for p in MainWindow.refDICOMS['Ktrans.dcm'].KtransMap]])
        if 'Ve.dcm' in MainWindow.refDICOMS:
                parameterList.append(['Ve', [str(p) for p in MainWindow.refDICOMS['Ve.dcm'].VeMap]])

        for key, DICOM in MainWindow.DICOMSeries.items():
            treeListItems.append([key, parameterList])

        # add nodes to the tree
        self.AddTreeNodes(self.root, treeListItems)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnActivated, self)

    def AddTreeNodes(self, parentItem, items):
        for item in items:
            if type(item) == str:
                self.AppendItem(parentItem, item)
            else:
                newParentItem = self.AppendItem(parentItem, item[0])
                print 'add item: ' + item[0]
                self.AddTreeNodes(newParentItem, item[1])

    def OnActivated(self, event):
        # get the item in order to display the plot
        print self.GetItemText(event.GetItem())

class ImportedDICOM:
    ''' This class manages the imported DICOM files.
    The parameters like the size of a patch, the arrange of patches in an image, should be able to be read from the images.
    The reference file will be loaded as common files, but used for abstracting parameters' purpose.
    '''
    def __init__(self, path, fileName):
        self.extraPatchNr = 2
        self.patchPxlNr = 10

        self.DICOMName = fileName
        self.KtransMap = []
        self.VeMap = []
        self.pixelArray = []
        self.rearrangedPixels = []

        ds = dicom.read_file(path)

        # rescale the pixel value
        try:
            MainWindow.rescaleIntercept = ds.RescaleIntercept
            MainWindow.rescaleSlope = ds.RescaleSlope
            print MainWindow.rescaleIntercept
        except:
            pass

        self.pixelArray.extend(self.Rescale(ds.pixel_array))

        # calculate the size of the patches
        self.nrOfRows = ds.Rows/self.patchPxlNr - self.extraPatchNr
        self.nrOfColumns = ds.Columns/self.patchPxlNr

        # rearrange the pixels
        self.rearrangedPixels.extend(self.RearrangePixels(self.pixelArray, self.nrOfRows, self.nrOfColumns))

        if fileName == 'Ktrans.dcm':
            self.AbstractKtrans()
        elif fileName == 'Ve.dcm':
            self.AbstractVe()
        else:
            pass

    def Rescale(self, intPixelArray):
        # rescale the pixel value from int to float
        temp = []
        floatPixelArray = []
        for row in intPixelArray:
            for pixel in row:
                temp.append(pixel * MainWindow.rescaleSlope + MainWindow.rescaleIntercept)
            floatPixelArray.append(temp)
            temp = []
        return floatPixelArray

    def RearrangePixels(self, pxlArr, nrOfRows, nrOfColumns):
        # rearrange the pixels so that they can be picked up in unit of patch, with index of [indexOfRow][indexOfColumn]
        patchTemp = [[[] for j in range(nrOfColumns)] for i in range(nrOfRows) ]
        patchCell = []
        for i in range(nrOfRows):
            for j in range(nrOfColumns):
                for k in range(self.patchPxlNr):
                    patchCell.extend(pxlArr[(i + 1) * self.patchPxlNr + k ][j : j + self.patchPxlNr])
                patchTemp[i][j] = patchCell
                patchCell = []
        return patchTemp

    def AbstractKtrans(self):
        self.KtransMap = []
        for i in range(self.nrOfRows):
            self.KtransMap.append(self.rearrangedPixels[i][1][1])

    def AbstractVe(self):
        self.VeMap = []
        for i in range(self.nrOfColumns):
            self.VeMap.append(self.rearrangedPixels[1][i][1])

if __name__ == "__main__":
    Application = wx.App()
    window = MainWindow(None)
    window.Show()
    Application.MainLoop()
