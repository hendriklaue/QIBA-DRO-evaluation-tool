 #!/usr/bin/env python

import os.path
import wx
import dicom
import pylab
import numpy
from scipy import stats
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import axes3d


class MainWindow(wx.Frame):
    '''
    this is the main window of the QIBA evaluate tool
    '''
    applicationName = "QIBA evaluate tool"

    # lists to contain the DICOM files
    refK = []
    refV = []
    calK = []
    calV = []


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
        '''
        set up the menubar
        '''
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        OnExport = fileMenu.Append(wx.ID_ANY, "&Export the results...\tCtrl+E", "Export the result as PDF/EXCEL file.")
        fileMenu.AppendSeparator()
        OnExit = fileMenu.Append(wx.ID_ANY, "&Quit\tCtrl+Q", "Quit " + self.applicationName)

        editMenu = wx.Menu()
        OnClearRef = editMenu.Append(wx.ID_ANY, "Clear Reference DICOM Files.")
        OnClearDICOMs = editMenu.Append(wx.ID_ANY, "Clear Calculated DICOM Files.")

        aboutMenu = wx.Menu()
        OnThirdPartyLib = aboutMenu.Append(wx.ID_ANY, "Third party libraries...", "Third party libraries used in this application.")
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

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

    def SetupLeft(self):
        '''
        set up the left panel. Empty right now.
        '''
        pass

    def SetupRight(self):
        '''
        set up the right panel
        '''
        self.noteBookRight = wx.Notebook(self.rightPanel)  #, style=wx.SUNKEN_BORDER)
        self.page1 = wx.Panel(self.noteBookRight)
        self.page2 = wx.Panel(self.noteBookRight)
        self.page3 = wx.Panel(self.noteBookRight)
        self.noteBookRight.AddPage(self.page1, "Statistics Viewer")
        self.noteBookRight.AddPage(self.page2, "Dispersion distribution")
        self.noteBookRight.AddPage(self.page3, "Result Review")

        # page 1
        # buttons
        button1 = wx.Button(self.page1, wx.ID_ANY, 'reference Ktrans')
        button2 = wx.Button(self.page1, wx.ID_ANY, 'reference Ve')
        button3 = wx.Button(self.page1, wx.ID_ANY, 'calculated trans')
        button4 = wx.Button(self.page1, wx.ID_ANY, 'calculated Ve')
        buttonOK = wx.Button(self.page1, wx.ID_ANY, 'Evaluate')

        self.Bind(wx.EVT_BUTTON, self.OnImportRefK, button1)
        self.Bind(wx.EVT_BUTTON, self.OnImportRefV, button2)
        self.Bind(wx.EVT_BUTTON, self.OnImportCalK, button3)
        self.Bind(wx.EVT_BUTTON, self.OnImportCalV, button4)
        self.Bind(wx.EVT_BUTTON, self.OnEvaluate, buttonOK)

        sizerButton = wx.GridSizer(cols=1)
        sizerButton.Add(button1)
        sizerButton.Add(button2)
        sizerButton.Add(button3)
        sizerButton.Add(button4)
        sizerButton.Add(buttonOK)

        # set a canvas on page 1
        self.figure = Figure()
        self.canvas = FigureCanvas(self.page1,-1, self.figure)

        # set sizer for the canvas
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(sizerButton)
        self.page1.SetSizer(sizer)

        # page 2
        self.figure3D = Figure()
        self.canvas3D = FigureCanvas(self.page2,-1, self.figure3D)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvas3D, 1, wx.EXPAND)
        self.page2.SetSizer(sizer)

        # sizer for the right panel
        sizer = wx.BoxSizer()
        sizer.Add(self.noteBookRight, 1, wx.EXPAND)
        self.rightPanel.SetSizer(sizer)
        self.rightPanel.Layout()

    def SetupLayoutMain(self):
        '''
        set up the main window
        '''
        self.leftPanel = wx.Panel(self, size = (200, 600))
        self.rightPanel = wx.Panel(self, size = (700, 600))

        self.SetupLeft()
        self.SetupRight()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.leftPanel, 2, flag = wx.EXPAND)  # second argument being 0 to make sure that it wont expand
        sizer.Add(self.rightPanel, 7, flag = wx.EXPAND)  # second argument is for expansion proportion
        self.SetSizer(sizer)

    def OnImportRefK(self, event):
        '''
<<<<<<< HEAD
        Import the reference Ktrans
        '''
        dlg = wx.FileDialog(self, 'Choose a DICOM file to add', '', '', "DICOM file(*.dcm) | *.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.refK = ImportedDICOM(dlg.GetPath())

    def OnImportRefV(self, event):
        '''
        Import the reference Ve
        '''
        dlg = wx.FileDialog(self, 'Choose a DICOM file to add', '', '', "DICOM file(*.dcm) | *.dcm", wx.OPEN)
=======
        dlg = wx.FileDialog(self, 'Choose a file to add', '', '', "DICOM file (*.dcm)|*.dcm", wx.OPEN | wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            pathList = dlg.GetPaths()
            fileList = dlg.GetFilenames()
            newFileCount = 0

            for (path, file) in zip(pathList, fileList):
                if os.path.isfile(path):
                    self.refDICOMS[file] = ImportedDICOM(path, file)
                    if not self.refDICOMS[file].ISREF: # this is a error proven so that normal DICOM file cannot be loaded as reference. However the standard deserves reconsideration
                        del self.refDICOMS[file]
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
        dlg = wx.FileDialog(self, 'Choose a file to add', '', '', "DICOM file (*.dcm)|*.dcm", wx.OPEN | wx.MULTIPLE)
        newFileCount = 0
>>>>>>> 6d998c85bf02c278bb3a8580b953bad8d9840d76
        if dlg.ShowModal() == wx.ID_OK:
            self.refV = ImportedDICOM(dlg.GetPath())

    def OnImportCalK(self, event):
        '''
        Import the calculated Ktrans
        '''
        dlg = wx.FileDialog(self, 'Choose a DICOM file to add', '', '', "DICOM file(*.dcm) | *.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.calK = ImportedDICOM(dlg.GetPath())

    def OnImportCalV(self, event):
        '''
        Import the calculated Ve
        '''
        dlg = wx.FileDialog(self, 'Choose a DICOM file to add', '', '', "DICOM file(*.dcm) | *.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.calV = ImportedDICOM(dlg.GetPath())

    def OnEvaluate(self, event):
        '''
        process the imported DICOM,and display
        '''
        self.SetStatusText('Start to evaluate...')
        self.dispersionOfDICOMK = []
        self.dispersionOfDICOMV = []
        self.dispersionK = [[]*i for i in range(self.calK.nrOfRows)]
        self.dispersionV = [[]*i for i in range(self.calV.nrOfRows)]
        self.pixelsTempRefK = []
        self.pixelsTempCalK = []
        self.pixelsTempRefV = []
        self.pixelsTempCalV = []

        for i in range(self.calK.nrOfRows):
            for j in range(self.calK.nrOfColumns):
                # simply attach the dispersion of patches from left to right, from up to down
                self.dispersionOfDICOMK.append(numpy.std(self.calK.rearrangedPixels[i][j]))
                self.dispersionOfDICOMV.append(numpy.std(self.calV.rearrangedPixels[i][j]))

                # collect all the pixels to calculate the std error
                self.pixelsTempRefK.extend(self.refK.rearrangedPixels[i][j])
                self.pixelsTempCalK.extend(self.calK.rearrangedPixels[i][j])
                self.pixelsTempRefV.extend(self.refV.rearrangedPixels[i][j])
                self.pixelsTempCalV.extend(self.calV.rearrangedPixels[i][j])


        # linear regression
        slopeK, interceptK, r_valueK, p_valueK, slope_std_errorK = stats.linregress(numpy.array(self.pixelsTempRefK), numpy.array(self.pixelsTempCalK))
        slopeV, interceptV, r_valueV, p_valueV, slope_std_errorV = stats.linregress(numpy.array(self.pixelsTempRefV), numpy.array(self.pixelsTempCalV))

        # uniform the calculated data, to remove artificial slope and intercept
        self.pixelsTempCalK_Uniformed = (self.pixelsTempCalK - interceptK) / slopeK
        self.pixelsTempCalK_Uniformed = self.pixelsTempCalK_Uniformed.tolist()
        self.pixelsTempCalV_Uniformed = (self.pixelsTempCalV - interceptV) / slopeV
        self.pixelsTempCalV_Uniformed = self.pixelsTempCalV_Uniformed.tolist()

        # calculate std error with uniformed data
        stdErrorK_Uniformed = numpy.sqrt(numpy.sum((numpy.array(self.pixelsTempRefK) - numpy.array(self.pixelsTempCalK_Uniformed)) ** 2) / len(self.pixelsTempRefK))
        stdErrorV_Uniformed = numpy.sqrt(numpy.sum((numpy.array(self.pixelsTempRefV) - numpy.array(self.pixelsTempCalV_Uniformed)) ** 2) / len(self.pixelsTempRefV))

        # calculate the dispersion after uniforming
        tempK = []
        tempV = []
        for i in range(self.calK.nrOfRows):
            for j in range(self.calK.nrOfColumns):
                for pixel in range(100):
                    tempK.append((self.calK.rearrangedPixels[i][j][pixel] - numpy.asscalar(interceptK)) / numpy.asscalar(slopeK) )
                    tempV.append((self.calV.rearrangedPixels[i][j][pixel] - numpy.asscalar(interceptV)) / numpy.asscalar(slopeV) )
                self.dispersionK[i].append(numpy.std(tempK))
                self.dispersionV[i].append(numpy.std(tempV))
                tempK = []
                tempV = []

        # the std error after rescale? Also could add 3D bar chart, so that the performance according to the (K, V) combination could be viewed
        print '******** EVALUATION RESULT *********'
        print 'std error of uniformed calculated Ktrans:' + str(stdErrorK_Uniformed)
        print 'std error of uniformed calculated Ve:' + str(stdErrorV_Uniformed)
        print 'estimate the artificial slope of calculated Ktrans: ' + str(slopeK)
        print 'estimate the artificial intercept of calculated Ktrans: ' + str(interceptK)
        print 'estimate the artificial slope of calculated Ve: ' + str(slopeV)
        print 'estimate the artificial intercept calculated Ve: ' + str(interceptV)
        print 'patch dispersion of uniformed calculated Ktrans: ' + str(self.dispersionK)
        print 'patch dispersion of uniformed calculated Ve: ' + str(self.dispersionV)

        # draw the figures
        self.DrawPlot()
        self.DrawPlot3D()
        self.SetStatusText('Evaluation finished.')

    def DrawPlot(self):
        '''
        the scatter plots show the distribution of the calculated values
        '''
        subPlotK = self.figure.add_subplot(2, 1, 1)
        subPlotK.clear()
        plotRaw = subPlotK.scatter(self.pixelsTempRefK, self.pixelsTempCalK, color = 'g', alpha = 0.25)
        plotUniformed = subPlotK.scatter(self.pixelsTempRefK, self.pixelsTempCalK_Uniformed, color = 'b', alpha = 0.25)
        plotRef = subPlotK.scatter(self.pixelsTempRefK, self.pixelsTempRefK, color = 'r', alpha = 0.25)
        subPlotK.legend([plotRef, plotRaw,  plotUniformed], ['reference value', 'calculated value', 'uniformed calculated value'])
        subPlotK.set_xlabel('Reference Ktrans')
        subPlotK.set_ylabel('Calculated Ktrans')
        subPlotK.set_title('Distribution plot of Ktrans')

        subPlotV = self.figure.add_subplot(2, 1, 2)
        subPlotV.clear()
        plotRaw = subPlotV.scatter(self.pixelsTempRefV, self.pixelsTempCalV, color = 'g', alpha = 0.25)
        plotUniformed = subPlotV.scatter(self.pixelsTempRefV, self.pixelsTempCalV_Uniformed, color = 'b', alpha = 0.25)
        plotRef = subPlotV.scatter(self.pixelsTempRefV, self.pixelsTempRefV, color = 'r', alpha = 0.25)
        subPlotV.legend([plotRef, plotRaw,  plotUniformed], ['reference value', 'calculated value', 'uniformed calculated value'])
        subPlotV.set_xlabel('Reference Ve')
        subPlotV.set_ylabel('Calculated Ve')
        subPlotV.set_title('Distribution plot of Ve')

        self.canvas.draw()
        self.rightPanel.Layout()

    def DrawPlot3D(self):
        '''
        plot 3D bar s, so that a distribution view of the dispersion can be referred to for different K,V combination
        '''
        subPlotK3D = self.figure3D.add_subplot(2, 1, 1, projection = '3d')
        subPlotK3D.clear()
        for i in range(self.calK.nrOfRows):
            xs = range(self.calK.nrOfColumns)
            ys = self.dispersionK[i]
            subPlotK3D.bar(xs, ys, zs = i, zdir = 'x', alpha = 0.8)
        subPlotK3D.set_xlabel('Ktrans')
        subPlotK3D.set_ylabel('Ve')
        subPlotK3D.set_zlabel('Dispersion of calculated data')
        subPlotK3D.set_title('Distribution of dispersion of the calculated Ktrans')

        subPlotV3D = self.figure3D.add_subplot(2, 1, 2, projection = '3d')
        subPlotV3D.clear()
        for i in range(self.calV.nrOfRows):
            xs = range(self.calV.nrOfColumns)
            ys = self.dispersionV[i]
            subPlotV3D.bar(xs, ys, zs = i, zdir = 'x', alpha = 0.8)
        subPlotV3D.set_xlabel('Ktrans')
        subPlotV3D.set_ylabel('Ve')
        subPlotV3D.set_zlabel('Dispersion of calculated data')
        subPlotV3D.set_title('Distribution of dispersion of the calculated Ve')

        self.canvas3D.draw()
        self.rightPanel.Layout()

    def OnClearRef(self, event):
        self.refK = []
        self.refV = []
        self.CleanPanel(self.rightPanel)
        self.SetupLayoutRight()
        self.SetStatusText("Reference DICOM files cleared.")

    def OnClearDICOMs(self, event):
        self.calK = []
        self.calV = []
        self.CleanPanel(self.rightPanel)
        self.SetupLayoutRight()
        self.SetStatusText('Calculated DICOM files cleared.')

    def CleanPanel(self, panel):
        for child in panel.GetChildren():
            if child:
                child.Destroy()
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
    '''
    The customized TreeCtrl class, to index the display of the scatter plot accordingly. Not used now.
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
        # get the parameter entry from the treelist, in order to display the specific plot
        try:
            fileName = self.GetItemText(self.GetItemParent(self.GetItemParent(event.GetItem())))
            parameterName = self.GetItemText(self.GetItemParent(event.GetItem()))
            parameter = self.GetItemText(event.GetItem())
            window.x = [[], []]
            window.y = [[], []]
            yAverageTemp = []

            if parameterName == 'Ktrans':
                xTemp = [ [float(p)] * 100 for p in  window.refDICOMS['Ve.dcm'].VeMap]
                for patch in xTemp:
                    window.x[0].extend(patch)
                window.x[1] = [float(p) for p in  window.refDICOMS['Ve.dcm'].VeMap]

                yTemp = window.DICOMSeries[fileName].OnQuery(parameterName, parameter)
                for patch in yTemp:
                    yAverageTemp.append(numpy.mean(patch))
                    window.y[0].extend(patch)

            if parameterName == 'Ve':
                xTemp = [ [float(p)] * 100 for p in  window.refDICOMS['Ktrans.dcm'].KtransMap]
                for patch in xTemp:
                    window.x[0].extend(patch)
                window.x[1] = [float(p) for p in  window.refDICOMS['Ktrans.dcm'].KtransMap]

                yTemp = window.DICOMSeries[fileName].OnQuery(parameterName, parameter)
                for patch in yTemp:
                    yAverageTemp.append(numpy.mean(patch))
                    window.y[0].extend(patch)
            window.y[1] = yAverageTemp
        except:
            return

        window.DrawPlot()

class ImportedDICOM:
    '''
    Manages the imported DICOM files.
    '''
    def __init__(self, path):
        self.extraPatchNr = 2
        self.patchPxlNr = 10

        self.KtransMap = []
        self.VeMap = []
        self.parameterMaps = {}
        self.pixelArray = []
        self.rearrangedPixels = []

        ds = dicom.read_file(path)

        # rescale the pixel value
        try:
            self.rescaleIntercept = ds.RescaleIntercept
            self.rescaleSlope = ds.RescaleSlope
        except:
            self.rescaleIntercept = 0
            self.rescaleSlope = 1
            pass

        self.pixelArray.extend(self.Rescale(ds.pixel_array))

        # calculate the size of the patches
        self.nrOfRows = ds.Rows/self.patchPxlNr - self.extraPatchNr
        self.nrOfColumns = ds.Columns/self.patchPxlNr

        # rearrange the pixels
        self.rearrangedPixels.extend(self.RearrangePixels(self.pixelArray, self.nrOfRows, self.nrOfColumns))


    def Rescale(self, intPixelArray):
        '''
        rescale the pixel value from int to float
        '''
        temp = []
        floatPixelArray = []
        for row in intPixelArray:
            for pixel in row:
                temp.append(pixel * self.rescaleSlope + self.rescaleIntercept)
            floatPixelArray.append(temp)
            temp = []
        return floatPixelArray

    def RearrangePixels(self, pxlArr, nrOfRows, nrOfColumns):
        '''
        rearrange the pixels so that they can be picked up in unit of patch, with index of [indexOfRow][indexOfColumn]
        '''
        patchAll = [[[] for j in range(nrOfColumns)] for i in range(nrOfRows) ]
        patchTemp = []
        for i in range(nrOfRows):
            for j in range(nrOfColumns):
                for k in range(self.patchPxlNr):
                    patchTemp.extend(pxlArr[(i+1) * self.patchPxlNr + k ][j * self.patchPxlNr : (j + 1) * self.patchPxlNr])
                patchAll[i][j].extend(patchTemp)
                patchTemp = []
        return patchAll

    def AbstractKtrans(self):
        '''
        get the Ktrans parameters
        '''
        for i in range(self.nrOfRows):
            self.KtransMap.append('%.2f' %self.rearrangedPixels[i][1][1])

    def AbstractVe(self):
        '''
        get the Ve parameters
        '''
        for i in range(self.nrOfColumns):
            self.VeMap.append('%.2f' %self.rearrangedPixels[1][i][1])


if __name__ == "__main__":
    Application = wx.App()
    window = MainWindow(None)
    window.Show()
    Application.MainLoop()
