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
        self.x = []
        self.y = []

        self.SetMinSize((900, 600))
        self.CenterOnScreen()

        self.CreateStatusBar()
        self.SetStatusText("Welcome to " + self.applicationName + "!")

        self.SetupMenubar()
        self.SetupLayoutMain()

    def SetupMenubar(self):
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        OnImportRef = fileMenu.Append(wx.ID_ANY, "&Import Reference DICOM Files...\tCtrl+Shift+I", "Import reference DICOM files.")
        OnImport = fileMenu.Append(wx.ID_ANY, "&Import...\tCtrl+I", "Import DICOM files.")
        fileMenu.AppendSeparator()
        OnExport = fileMenu.Append(wx.ID_ANY, "&Export...\tCtrl+E", "Export the result as PDF/EXCEL file.")
        fileMenu.AppendSeparator()
        OnExit = fileMenu.Append(wx.ID_ANY, "&Quit\tCtrl+Q", "Quit " + self.applicationName)

        editMenu = wx.Menu()
        OnClearRef = editMenu.Append(wx.ID_ANY, "Clear the reference DICOM files.")
        OnClearDICOMs = editMenu.Append(wx.ID_ANY, "Clear the DICOM files evaluated on.")

        aboutMenu = wx.Menu()
        OnThirdPartyLib = aboutMenu.Append(wx.ID_ANY, "Third party libraries...", "Third party libraries used in this application.")
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

        menubar.Bind(wx.EVT_MENU, self.OnImportRef, OnImportRef)
        menubar.Bind(wx.EVT_MENU, self.OnImport, OnImport)
        menubar.Bind(wx.EVT_MENU, self.OnExport, OnExport)
        menubar.Bind(wx.EVT_MENU, self.OnClearRef, OnClearRef)
        menubar.Bind(wx.EVT_MENU, self.OnClearDICOMs, OnClearDICOMs)
        menubar.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        menubar.Bind(wx.EVT_MENU, self.OnShowThirdParty, OnThirdPartyLib)
        menubar.Bind(wx.EVT_MENU, self.OnAbout, OnAboutApp)

        menubar.Append(fileMenu, "&File")
        menubar.Append(editMenu, "&Edit")
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

    def OnImportRef(self, event):
        ''' Import the reference files for getting the parameter maps.
        '''
        dlg = wx.FileDialog(self, 'Choose a file to add', '', '', "DICOM file(*.dcm) | *.dcm", wx.OPEN | wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            pathList = dlg.GetPaths()
            fileList = dlg.GetFilenames()
            newFileCount = 0

            for (path, file) in zip(pathList, fileList):
                if os.path.isfile(path):
                    self.refDICOMS[file] = ImportedDICOM(path, file)
                    if not self.refDICOMS[file].ISREF:
                        self.refDICOMS[file].clear()
                        wx.MessageDialog(self, file + ' is an invalid reference file.', 'Invaid reference file', wx.OK).ShowModal()
                    else:
                        newFileCount = + 1
                else:
                    wx.MessageDialog(self, file + ' doesn\'t exist.', 'File doesn\'t exists', wx.OK).ShowModal()

            self.SetStatusText(''.join(key + ' ' for key in self.refDICOMS) + ' available.')
            self.ShowTreeList()

    def OnImport(self, event):
        """ Import DICOM files to evaluate on.
        """
        dlg = wx.FileDialog(self, 'Choose a file to add', '', '', "DICOM file(*.dcm) | *.dcm", wx.OPEN | wx.MULTIPLE)
        newFileCount = 0
        if dlg.ShowModal() == wx.ID_OK:
            pathList = dlg.GetPaths()
            fileList = dlg.GetFilenames()

            # if the parameter map are not available, pop out dialog.
            if self.refDICOMS == {}:
                wx.MessageDialog(self,  'No reference DICOM imported! \nPlease import reference DICOM files first.', 'Reference DICOM needed', wx.OK).ShowModal()
                return
            elif not 'Ktrans.dcm' in self.refDICOMS:
                wx.MessageDialog(self,  'Please also import reference DICOM file for Ktrans mapping.', 'Reference DICOM needed', wx.OK).ShowModal()
                return
            elif not 'Ve.dcm' in self.refDICOMS:
                wx.MessageDialog(self,  'Please also import reference DICOM file for Ve mapping.', 'Reference DICOM needed', wx.OK).ShowModal()
                return

            for (path, file) in zip(pathList, fileList):
                if os.path.isfile(path):
                    self.DICOMSeries[file] = ImportedDICOM(path, file)
                    if self.DICOMSeries[file].ISREF:
                        del self.DICOMSeries[file]
                        wx.MessageDialog(self, file + ' is a reference file.', 'Is a reference file', wx.OK).ShowModal()
                    else:
                        newFileCount = + 1
                else:
                    wx.MessageDialog(self, file + ' doesn\'t exist.', 'File doesn\'t exists', wx.OK).ShowModal()

            self.SetStatusText(str(newFileCount) + ' new DICOM file(s) imported.')
            self.ShowTreeList()

    def ShowTreeList(self):
        # show the tree list of the imported DICOM files
        self.CleanPanel(self.leftPanel)
        TreeSizer = wx.BoxSizer(wx.VERTICAL)
        TreeSizer.Add(ParameterTree(self.leftPanel), 1, flag = wx.EXPAND)
        self.leftPanel.SetSizer(TreeSizer)
        self.leftPanel.Layout()

    def DrawPlot(self):
        # draw scatter plot on page 1 when an item is selected in the tree list
        self.scatterPlot = self.figure.add_subplot(1,1,1)
        self.scatterPlot.clear()
        self.scatterPlot.scatter(self.x, self.y)

        self.canvas.draw()
        self.rightPanel.Layout()

    def OnClearRef(self, event):
        self.refDICOMS.clear()
        self.ShowTreeList()
        self.CleanPanel(self.rightPanel)
        self.SetupLayoutRight()
        self.SetStatusText("Reference DICOM files cleared.")

    def OnClearDICOMs(self, event):
        self.DICOMSeries.clear()
        self.ShowTreeList()
        self.CleanPanel(self.rightPanel)
        self.SetupLayoutRight()
        self.SetStatusText('DICOM files evaluated on cleared.')

    def CleanPanel(self, panel):
        for child in panel.GetChildren():
            if child:
                child.Destroy() # delete the old tree
            else:
                pass

    def OnExport(self, event):
        print "TODO: add export function"

    def OnQuit(self, event):
        self.Close()

    def OnShowThirdParty(self):
        # could be added to the about dialog?
        pass

    def OnAbout(self, event):
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
        treeListItems = []
        parameterList = []

        # try to abstract the parameter map from the DICOM, in order to show in the tree list
        if not ('Ktrans.dcm' in window.refDICOMS):
            wx.MessageDialog(self,  'Please Import reference DICOM for Ktrans mapping.', 'Ktrans mapping DICOM needed', wx.OK)
            return
        elif not ('Ve.dcm' in window.refDICOMS):
            wx.MessageDialog(self,  'Please Import reference DICOM for Ve mapping.', 'Ve mapping DICOM needed', wx.OK)
            return
        else:
            parameterList.append(['Ktrans', window.refDICOMS['Ktrans.dcm'].KtransMap])
            parameterList.append(['Ve', window.refDICOMS['Ve.dcm'].VeMap])

        if window.DICOMSeries == {}:
            return

        self.root = self.AddRoot('Imported DICOM files')  # a name that could distinguish the imported DICOM

        for key, DICOM in window.DICOMSeries.items():
            treeListItems.append([key, parameterList])

        # add nodes to the tree
        self.AddTreeNodes(self.root, treeListItems)
        self.ExpandAll()
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated, self)

    def AddTreeNodes(self, parentItem, items):
        for item in items:
            if type(item) == str:
                self.AppendItem(parentItem, item)
            else:
                newParentItem = self.AppendItem(parentItem, item[0])
                self.AddTreeNodes(newParentItem, item[1])

    def OnActivated(self, event):
        # get the item in order to display the plot
        try:
            fileName = self.GetItemText(self.GetItemParent(self.GetItemParent(event.GetItem())))
            parameterName = self.GetItemText(self.GetItemParent(event.GetItem()))
            parameter = self.GetItemText(event.GetItem())

            if parameterName == 'Ktrans':
                window.x = []
                window.y = []
                xTemp = [ [float(p)] * 100 for p in  window.refDICOMS['Ve.dcm'].VeMap]
                for patch in xTemp:
                    window.x.extend(patch)

                yTemp = window.DICOMSeries[fileName].OnQuery(parameterName, parameter)
                for patch in yTemp:
                    window.y.extend(patch)

            if parameterName == 'Ve':
                window.x = []
                window.y = []
                xTemp = [ [float(p)] * 100 for p in  window.refDICOMS['Ktrans.dcm'].KtransMap]
                for patch in xTemp:
                    window.x.extend(patch)

                yTemp = window.DICOMSeries[fileName].OnQuery(parameterName, parameter)
                for patch in yTemp:
                    window.y.extend(patch)
        except:
            return
        window.DrawPlot()

class ImportedDICOM:
    ''' This class manages the imported DICOM files.
    The parameters like the size of a patch, the arrange of patches in an image, should be able to be read from the images.
    The reference file will be loaded as commonly, but used mainly for abstracting parameters' purpose.
    '''
    def __init__(self, path, fileName):
        self.extraPatchNr = 2
        self.patchPxlNr = 10

        self.DICOMName = fileName
        self.KtransMap = []
        self.VeMap = []
        self.parameterMaps = {}
        self.pixelArray = []
        self.rearrangedPixels = []

        ds = dicom.read_file(path)

        # rescale the pixel value
        try:
            window.rescaleIntercept = ds.RescaleIntercept
            window.rescaleSlope = ds.RescaleSlope
            self.ISREF = True
        except:
            self.ISREF = False

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
                temp.append(pixel * window.rescaleSlope + window.rescaleIntercept)
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
                    patchCell.extend(pxlArr[i * self.patchPxlNr + k ][j * self.patchPxlNr : (j + 1) * self.patchPxlNr])
                patchTemp[i][j].extend(patchCell)
                patchCell = []
        return patchTemp

    def OnQuery(self, parameterName, parameter):
        if parameterName == 'Ktrans':
            return self.rearrangedPixels[window.refDICOMS['Ktrans.dcm'].KtransMap.index(parameter)]
        if parameterName == 'Ve':
            temp = []
            for i in range(len(window.refDICOMS['Ktrans.dcm'].KtransMap)):
                temp.append(self.rearrangedPixels[i][window.refDICOMS['Ve.dcm'].VeMap.index(parameter)])
            return temp


    def AbstractKtrans(self):
        for i in range(self.nrOfRows):
            self.KtransMap.append('%.2f' %self.rearrangedPixels[i][1][1])


    def AbstractVe(self):
        for i in range(self.nrOfColumns):
            self.VeMap.append('%.2f' %self.rearrangedPixels[1][i][1])


if __name__ == "__main__":
    Application = wx.App()
    window = MainWindow(None)
    window.Show()
    Application.MainLoop()
