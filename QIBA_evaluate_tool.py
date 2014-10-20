 #!/usr/bin/env python
# License file for the QIBA DRO Evaluation Tool (QDET)

# Copyright (c) 2014-2015 Fraunhofer MEVIS, member of the Fraunhofer Soviety 
# and the Radiological Society of North America (RSNA)

# Except for portions outlined below, pydicom is released under an MIT license:

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os.path
import wx
import wx.html
import dicom
import numpy
from scipy import stats, optimize
from math import log10
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.ticker as ticker
import time
import subprocess
import struct

class MainWindow(wx.Frame):
    '''
    this is the main window of the QIBA evaluate tool
    '''
    applicationName = "QIBA evaluate tool"

    # the list of evaluated models
    testedModels = []

    # path_Ktrans_ref = os.path.join(os.path.dirname(sys.argv[0]), 'reference_data', 'Ktrans.dcm')
    # path_Ve_ref = os.path.join(os.path.dirname(sys.argv[0]), 'reference_data', 'Ve.dcm')
    path_Ktrans_ref = os.path.join(os.getcwd(), 'reference_data', 'Ktrans.dcm')
    path_Ve_ref = os.path.join(os.getcwd(), 'reference_data', 'Ve.dcm')
    path_Ktrans_cal = ''
    path_Ve_cal = ''

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title = self.applicationName, size = (wx.SYS_SCREEN_X, wx.SYS_SCREEN_Y))

        self.CenterOnScreen()

        self.CreateStatusBar()
        self.SetStatusText("Welcome to " + self.applicationName + "!")

        self.SetupMenubar()

        self.SetupLayoutMain()


    def SetupMenubar(self):
        '''
        set up the menu bar
        '''
        self.menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        OnExport = fileMenu.Append(wx.ID_ANY, "&Export the results...\tCtrl+E", "Export the result as PDF/EXCEL file.")
        fileMenu.AppendSeparator()
        OnExit = fileMenu.Append(wx.ID_ANY, "&Quit\tCtrl+Q", "Quit " + self.applicationName)

        editMenu = wx.Menu()
        # OnClearModelList = editMenu.Append(wx.ID_ANY, "Clear evaluated model list")
        OnLoadKtransRef = editMenu.Append(wx.ID_ANY, "Load Ktrans reference parameter map...")
        OnLoadVeRef = editMenu.Append(wx.ID_ANY, "Load Ve reference parameter map...")

        aboutMenu = wx.Menu()
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

        self.menubar.Bind(wx.EVT_MENU, self.OnExport, OnExport)
        # menubar.Bind(wx.EVT_MENU, self.OnClearModelList, OnClearModelList)
        self.menubar.Bind(wx.EVT_MENU, self.OnLoadReferenceKtrans, OnLoadKtransRef)
        self.menubar.Bind(wx.EVT_MENU, self.OnLoadReferenceVe, OnLoadVeRef)
        self.menubar.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        self.menubar.Bind(wx.EVT_MENU, self.OnAbout, OnAboutApp)

        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(editMenu, "&Edit")
        self.menubar.Append(aboutMenu, "&About")
        self.SetMenuBar(self.menubar)

    def SetupLeft(self):
        '''
        set up the left panel.
        show the directories and files list to load calculated DICOMs
        '''
        self.selectedFilePath = ''
        # setup the tree control widget for file viewing and selection

        self.fileBrowser = wx.GenericDirCtrl(self.leftPanel, -1, dir = os.path.join(os.getcwd(), 'calculated_data'), style=wx.DIRCTRL_SHOW_FILTERS,
                                             filter="DICOM files (*.dcm)|*.dcm|Binary files (*.bin *.raw )|*.bin;*.raw")

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.GetFilePath)

        # setup the right click function
        self.popupMenu = wx.Menu()
        itemLoadCalK = self.popupMenu.Append(-1, 'Load as calculated Ktrans')
        self.leftPanel.Bind(wx.EVT_MENU, self.OnPopupItemSelected, itemLoadCalK)
        itemLoadCalV = self.popupMenu.Append(-1, 'Load as calculated Ve')
        self.leftPanel.Bind(wx.EVT_MENU, self.OnPopupItemSelected, itemLoadCalV)

        self.leftPanel.Bind(wx.EVT_CONTEXT_MENU, self.OnShowPopup)

        # setup 'evaluate' and 'export result' buttons
        self.buttonEvaluate = wx.Button(self.leftPanel, wx.ID_ANY, 'Evaluate')
        self.buttonExport = wx.Button(self.leftPanel, wx.ID_ANY, 'Export result')
        self.Bind(wx.EVT_BUTTON, self.OnEvaluate, self.buttonEvaluate)
        self.Bind(wx.EVT_BUTTON, self.OnExport, self.buttonExport)

        sizerButton = wx.BoxSizer(wx.HORIZONTAL)
        sizerButton.Add(self.buttonEvaluate, 1, wx.ALIGN_LEFT)
        sizerButton.Add(self.buttonExport, 1, wx.ALIGN_RIGHT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.fileBrowser, 1, wx.EXPAND)
        sizer.Add(sizerButton)
        self.leftPanel.SetSizer(sizer)

        # disable the export/evaluate button in start up
        self.buttonExport.Disable()
        self.buttonEvaluate.Disable()

    def OnShowPopup(self, event):
        # show the popup menu
        position = event.GetPosition()
        position = self.leftPanel.ScreenToClient(position)
        self.leftPanel.PopupMenu(self.popupMenu, position)

    def OnPopupItemSelected(self, event):
        # do something when item of the popup menu is selected
        item = self.popupMenu.FindItemById(event.GetId())
        if item.GetText() == 'Load as calculated Ktrans':
            self.OnLoadCalculatedKtrans()
        elif item.GetText() == 'Load as calculated Ve':
            self.OnLoadCalculatedVe()

    def GetFilePath(self, event):
        # copy the selected file's path for loading it
        if self.fileBrowser.GetFilePath():
            self.selectedFilePath = self.fileBrowser.GetFilePath()

    def SetupRight(self):
        '''
        set up the right panel
        '''
        self.noteBookRight = wx.Notebook(self.rightPanel)  #, style=wx.SUNKEN_BORDER)
        self.pageImagePreview = wx.Panel(self.noteBookRight)
        self.pageScatter = wx.Panel(self.noteBookRight)
        self.pageHistogram = wx.Panel(self.noteBookRight)
        self.pageBoxPlot = wx.Panel(self.noteBookRight)
        self.pageStatistics = wx.Panel(self.noteBookRight)
        self.pageCovarianceCorrelation = wx.Panel(self.noteBookRight)
        self.pageModelFitting = wx.Panel(self.noteBookRight)
        self.pageT_Test = wx.Panel(self.noteBookRight)
        self.pageU_Test = wx.Panel(self.noteBookRight)
        self.pageANOVA = wx.Panel(self.noteBookRight)
        self.noteBookRight.AddPage(self.pageImagePreview, "Image Viewer")
        self.noteBookRight.AddPage(self.pageScatter, "Scatter Plots Viewer")
        self.noteBookRight.AddPage(self.pageHistogram, "Histograms Plots Viewer")
        self.noteBookRight.AddPage(self.pageBoxPlot, "Box Plots Viewer")
        self.noteBookRight.AddPage(self.pageStatistics, "Statistics Viewer")
        self.noteBookRight.AddPage(self.pageCovarianceCorrelation, "Covariance And Correlation")
        self.noteBookRight.AddPage(self.pageModelFitting, "Model fitting")
        self.noteBookRight.AddPage(self.pageT_Test, "t-test results Viewer")
        self.noteBookRight.AddPage(self.pageU_Test, "U-test results Viewer")
        self.noteBookRight.AddPage(self.pageANOVA, "ANOVA results Viewer")

        # show the calculated images and error images
        self.figureImagePreview = Figure()
        self.canvasImagePreview = FigureCanvas(self.pageImagePreview, -1, self.figureImagePreview)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasImagePreview, 1, wx.EXPAND)
        self.pageImagePreview.SetSizer(sizer)

        # page scatter
        self.figureScatter = Figure()
        self.canvasScatter = FigureCanvas(self.pageScatter,-1, self.figureScatter)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasScatter, 1, wx.EXPAND)
        self.pageScatter.SetSizer(sizer)

        # page Histogram
        self.figureHist_Ktrans = Figure()
        self.canvasHist_Ktrans = FigureCanvas(self.pageHistogram,-1, self.figureHist_Ktrans)

        self.figureHist_Ve = Figure()
        self.canvasHist_Ve = FigureCanvas(self.pageHistogram,-1, self.figureHist_Ve)

        self.verticalLine = wx.StaticLine(self.pageHistogram, -1, style=wx.LI_VERTICAL) # vertical line to separate the two subplots

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasHist_Ktrans, 35, wx.EXPAND)
        sizer.Add(self.verticalLine, 2, wx.EXPAND)
        sizer.Add(self.canvasHist_Ve, 35, wx.EXPAND)
        self.pageHistogram.SetSizer(sizer)

        # page box plots
        self.figureBoxPlot = Figure()
        self.canvasBoxPlot = FigureCanvas(self.pageBoxPlot,-1, self.figureBoxPlot)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasBoxPlot, 1, wx.EXPAND)
        self.pageBoxPlot.SetSizer(sizer)

        # page statistics
        self.statisticsViewer = wx.html.HtmlWindow(self.pageStatistics, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.statisticsViewer, 1, wx.EXPAND)
        self.pageStatistics.SetSizer(sizer)

        # page covariance and correlation
        self.covCorrViewer = wx.html.HtmlWindow(self.pageCovarianceCorrelation, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.covCorrViewer, 1, wx.EXPAND)
        self.pageCovarianceCorrelation.SetSizer(sizer)

        # page model fitting
        self.modelFittingViewer = wx.html.HtmlWindow(self.pageModelFitting, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.modelFittingViewer, 1, wx.EXPAND)
        self.pageModelFitting.SetSizer(sizer)

        # page t-test
        self.t_testViewer = wx.html.HtmlWindow(self.pageT_Test, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.t_testViewer, 1, wx.EXPAND)
        self.pageT_Test.SetSizer(sizer)

        # page U-test
        self.U_testViewer = wx.html.HtmlWindow(self.pageU_Test, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.U_testViewer, 1, wx.EXPAND)
        self.pageU_Test.SetSizer(sizer)

        # page ANOVA
        self.ANOVAViewer = wx.html.HtmlWindow(self.pageANOVA, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.ANOVAViewer, 1, wx.EXPAND)
        self.pageANOVA.SetSizer(sizer)

        # sizer for the right panel
        sizer = wx.BoxSizer()
        sizer.Add(self.noteBookRight, 1, wx.EXPAND)
        self.rightPanel.SetSizer(sizer)
        self.rightPanel.Layout()

    def SetupLayoutMain(self):
        '''
        set up the main window
        '''
        self.leftPanel = wx.Panel(self)
        self.rightPanel = wx.Panel(self)

        self.SetupLeft()
        self.SetupRight()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.leftPanel, 2, flag = wx.EXPAND)  # second argument being 0 to make sure that it wont expand
        sizer.Add(self.rightPanel, 7, flag = wx.EXPAND)
        self.SetSizer(sizer)

    def OnLoadReferenceKtrans(self, event):
        # Import the reference Ktrans
        dlg = wx.FileDialog(self, 'Load reference Ktrans...', '', '', "DICOM files (*.dcm)|*.dcm|Binary files (*.bin *.raw )|*.bin;*.raw", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_Ktrans_ref = dlg.GetPath()
            self.SetStatusText('Reference Ktrans loaded.')
        else:
            self.SetStatusText('Reference Ktrans was NOT loaded!')

    def OnLoadReferenceVe(self, event):
        # Import the reference Ve
        dlg = wx.FileDialog(self, 'Load reference Ve...', '', '', "DICOM files (*.dcm)|*.dcm|Binary files (*.bin *.raw )|*.bin;*.raw", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_Ve_ref = dlg.GetPath()
            self.SetStatusText('Reference Ve loaded.')
        else:
            self.SetStatusText('Reference Ve was NOT loaded!')

    def OnLoadCalculatedKtrans(self):
        # load the selected DICOM as calculated Ktrans
        if os.path.splitext(self.selectedFilePath)[1] == '.dcm' or '.bin' or '.raw':
            self.path_Ktrans_cal = self.selectedFilePath
            self.SetStatusText('Calculated Ktrans loaded.')
        else:
            self.SetStatusText('Invalid file chosen.')

        # enable the evaluate button when the paths are valid
        if self.path_Ktrans_cal and self.path_Ve_cal:
            self.buttonEvaluate.Enable()

    def OnLoadCalculatedVe(self):
        # load the selected DICOM as calculated Ve
        if os.path.splitext(self.selectedFilePath)[1] == '.dcm' or '.bin' or '.raw':
            self.path_Ve_cal = self.selectedFilePath
            self.SetStatusText('Calculated Ve loaded.')
        else:
            self.SetStatusText('Invalid file chosen.')

        # enable the evaluate button when the paths are valid
        if self.path_Ktrans_cal and self.path_Ve_cal:
            self.buttonEvaluate.Enable()
    def OnImportCalK(self, event):
        '''
        Import the calculated Ktrans
        '''
        dlg = wx.FileDialog(self, 'Load calculated Ktrans...', '', '', "DICOM file(*.dcm)|*.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_Ktrans_cal = dlg.GetPath()

    def OnImportCalV(self, event):
        '''
        Import the calculated Ve
        '''
        dlg = wx.FileDialog(self, 'Load calculated Ve...', '', '', "DICOM file(*.dcm)|*.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_Ve_cal = dlg.GetPath()

    def OnEvaluate(self, event):
        '''
        process the imported DICOM,and display
        '''

        # initialize one progress bar
       # max = 100
        #EvaluateProgressDialog = wx.ProgressDialog('Evaluating...', 'The progress of evaluation:', maximum = max)

        # clear the interface if they were used before
        self.ClearInterface()

        # disable some widgets
        self.buttonEvaluate.Disable()
        self.buttonExport.Disable()

        # status bar
        self.SetStatusText('Evaluating...')
        #EvaluateProgressDialog.Update(5)

        # create new model object to evaluated on
        self.newModel = ModelEvaluated()
        #EvaluateProgressDialog.Update(10)

        # make sure the import path is valid
        if not self.newModel.ImportFile(self.path_Ktrans_ref):
            self.SetStatusText('Please load a proper file as reference Ktrans.')
            return False

        if not self.newModel.ImportFile(self.path_Ve_ref):
            self.SetStatusText('Please load a proper file as reference Ve.')
            return False

        if not self.newModel.ImportFile(self.path_Ktrans_cal):
            self.SetStatusText('Please load a proper file as calculated Ktrans.')
            return False

        if not self.newModel.ImportFile(self.path_Ve_cal):
            self.SetStatusText('Please load a proper file as calculated ve.')
            return False
        #EvaluateProgressDialog.Update(15)

        # call the method to execute evaluation
        self.newModel.Evaluate(self.path_Ktrans_ref, self.path_Ve_ref, self.path_Ktrans_cal, self.path_Ve_cal)
        #EvaluateProgressDialog.Update(20)

        # show the results in the main window
        self.statisticsViewer.SetPage(self.newModel.GetStatisticsInHTML())
        self.covCorrViewer.SetPage(self.newModel.GetCovarianceCorrelationInHTML())
        self.modelFittingViewer.SetPage(self.newModel.GetModelFittingInHTML())
        self.t_testViewer.SetPage(self.newModel.GetT_TestResultsInHTML())
        self.U_testViewer.SetPage(self.newModel.GetU_TestResultsInHTML())
        self.ANOVAViewer.SetPage(self.newModel.GetANOVAResultsInHTML())
        #EvaluateProgressDialog.Update(25)

        # push the new tested model to the list
        self.testedModels.append(self.newModel)
        #EvaluateProgressDialog.Update(30)

        # draw the figures
        self.ShowImagePreview()
        #EvaluateProgressDialog.Update(35)
        self.DrawScatterPlot()
        #EvaluateProgressDialog.Update(50)
        self.DrawHistograms()
        #EvaluateProgressDialog.Update(90)
        self.DrawBoxPlot()
        #EvaluateProgressDialog.Update(95)

        # status bar
        self.SetStatusText('Evaluation finished.')
        #EvaluateProgressDialog.Update(100)
        #EvaluateProgressDialog.Destroy()

        # enable some widgets
        self.buttonEvaluate.Enable()
        self.buttonExport.Enable()

    def ShowImagePreview(self):
        # show calculated images and the error images
        subplotK_Cal = self.figureImagePreview.add_subplot(2,3,1)
        handler = subplotK_Cal.imshow(self.newModel.Ktrans_cal_inRow, cmap = 'bone', interpolation='nearest')
        divider = make_axes_locatable(subplotK_Cal.get_figure().gca()) # for tight up the color bar
        cax = divider.append_axes("right", "5%", pad="3%")
        subplotK_Cal.get_figure().colorbar(handler, cax = cax).set_label('Ktrans[1/min]') # show color bar and the label
        subplotK_Cal.set_title('Calculated Ktrans')

        subplotK_Err = self.figureImagePreview.add_subplot(2,3,2)
        handler = subplotK_Err.imshow(self.newModel.Ktrans_error, cmap = 'rainbow', interpolation='nearest')
        divider = make_axes_locatable(subplotK_Err.get_figure().gca())
        cax = divider.append_axes("right", "5%", pad="3%")
        subplotK_Err.get_figure().colorbar(handler, cax = cax).set_label('Delta Ktrans[1/min.]')
        subplotK_Err.set_title('Error map of Ktrans')

        subplotK_Err_Normalized = self.figureImagePreview.add_subplot(2,3,3)
        handler = subplotK_Err_Normalized.imshow(self.newModel.Ktrans_error_normalized, cmap = 'rainbow', interpolation='nearest')
        divider = make_axes_locatable(subplotK_Cal.get_figure().gca()) # for tight up the color bar
        cax = divider.append_axes("right", "5%", pad="3%")
        subplotK_Err_Normalized.get_figure().colorbar(handler, cax = cax).set_label('Normalized error[1]')
        subplotK_Err_Normalized.set_title('Normalized error map of Ktrans')

        subplotV_Cal = self.figureImagePreview.add_subplot(2,3,4)
        handler = subplotV_Cal.imshow(self.newModel.Ve_cal_inRow, cmap = 'bone', interpolation='nearest')
        divider = make_axes_locatable(subplotK_Cal.get_figure().gca()) # for tight up the color bar
        cax = divider.append_axes("right", "5%", pad="3%")
        subplotV_Cal.get_figure().colorbar(handler, cax = cax).set_label('ve[]')
        subplotV_Cal.set_title('Preview of Calculated Ve')

        subplotV_Err = self.figureImagePreview.add_subplot(2,3,5)
        handler = subplotV_Err.imshow(self.newModel.Ve_error, cmap = 'rainbow', interpolation='nearest')
        divider = make_axes_locatable(subplotK_Cal.get_figure().gca()) # for tight up the color bar
        cax = divider.append_axes("right", "5%", pad="3%")
        subplotV_Err.get_figure().colorbar(handler, cax = cax).set_label('Delta ve[]')
        subplotV_Err.set_title('Error map of Ve')

        subplotV_Err_Normalized = self.figureImagePreview.add_subplot(2,3,6)
        handler = subplotV_Err_Normalized.imshow(self.newModel.Ve_error_normalized, cmap = 'rainbow', interpolation='nearest')
        divider = make_axes_locatable(subplotK_Cal.get_figure().gca()) # for tight up the color bar
        cax = divider.append_axes("right", "5%", pad="3%")
        subplotV_Err_Normalized.get_figure().colorbar(handler, cax = cax).set_label('Normalized error[1]')
        subplotV_Err_Normalized.set_title('Normalized error map of Ve')

        self.figureImagePreview.tight_layout()
        self.canvasImagePreview.draw()

    def DrawScatterPlot(self):
        '''
        the scatter plots to show the distribution of the calculated values
        '''
        subPlotK = self.figureScatter.add_subplot(2, 1, 1)
        subPlotK.clear()
        plotRaw = subPlotK.scatter(self.newModel.Ktrans_ref, self.newModel.Ktrans_ref, color = 'g', alpha = 0.25, label = 'reference value')
        plotUniformed = subPlotK.scatter(self.newModel.Ktrans_ref, self.newModel.Ktrans_cal, color = 'b', alpha = 0.25, label = 'calculated value')
        # plotRef = subPlotK.scatter(self.pixelsTempRefK, self.pixelsTempRefK, color = 'r', alpha = 0.25, label = 'uniformed calculated value')
        subPlotK.legend(loc = 'upper left')
        subPlotK.set_xlabel('Reference Ktrans')
        subPlotK.set_ylabel('Calculated Ktrans')
        subPlotK.set_title('Distribution plot of Ktrans')

        subPlotV = self.figureScatter.add_subplot(2, 1, 2)
        subPlotV.clear()
        plotRaw = subPlotV.scatter(self.newModel.Ve_ref, self.newModel.Ve_ref, color = 'g', alpha = 0.25, label = 'reference value')
        plotUniformed = subPlotV.scatter(self.newModel.Ve_ref, self.newModel.Ve_cal, color = 'b', alpha = 0.25, label = 'calculated value')
        # plotRef = subPlotV.scatter(self.pixelsTempRefV, self.pixelsTempRefV, color = 'r', alpha = 0.25, label = 'uniformed calculated value')
        subPlotV.legend(loc = 'upper left')
        subPlotV.set_xlabel('Reference Ve')
        subPlotV.set_ylabel('Calculated Ve')
        subPlotV.set_title('Distribution plot of Ve')

        self.figureScatter.tight_layout()
        self.canvasScatter.draw()
        self.rightPanel.Layout()

    def DrawBoxPlot(self):
        '''
        draw box plots of each patch
        '''

        subPlotK = self.figureBoxPlot.add_subplot(2, 1, 1)
        subPlotK.clear()
        temp = []
        referValueK = []
        for i in range(self.newModel.nrOfRows):
            temp.extend(self.newModel.Ktrans_cal[i])
            referValueK.append(float('{0:.2f}'.format(self.newModel.Ktrans_ref[i][0][0])))
        subPlotK.boxplot(temp)

        subPlotV = self.figureBoxPlot.add_subplot(2, 1, 2)
        subPlotV.clear()
        temp = []
        referValueV = []
        for j in range(self.newModel.nrOfColumns):
            for i in range(self.newModel.nrOfRows):
                temp.append(self.newModel.Ve_cal[i][j])
            referValueV.append(float('{0:.2f}'.format(zip(*self.newModel.Ve_ref)[j][0][0])))
        subPlotV.boxplot(temp)

        # decorate Ktrans plot
        subPlotK.set_title('Box plot of calculated Ktrans')
        subPlotK.set_xlabel('In each column, each box plot denotes Ve = ' + str(referValueV) + ' respectively')
        subPlotK.set_ylabel('Calculated values in patches')

        subPlotK.xaxis.set_major_formatter(ticker.NullFormatter())
        subPlotK.xaxis.set_minor_locator(ticker.FixedLocator([3, 8, 13, 18, 23, 28]))
        subPlotK.xaxis.set_minor_formatter(ticker.FixedFormatter(['Ktrans = ' + str(referValueK[0]), 'Ktrans = ' + str(referValueK[1]), 'Ktrans = ' + str(referValueK[2]), 'Ktrans = ' + str(referValueK[3]), 'Ktrans = ' + str(referValueK[4]), 'Ktrans = ' + str(referValueK[5])]))
        for i in range(self.newModel.nrOfRows):
            subPlotK.axvline(x = self.newModel.nrOfColumns * i + 0.5, color = 'green', linestyle = 'dashed')

        # decorate Ve plot
        subPlotV.set_title('Box plot of calculated Ve')
        subPlotV.set_xlabel('In each column, each box plot denotes Ktrans = ' + str(referValueK) + ' respectively')
        subPlotV.set_ylabel('Calculated values in patches')

        subPlotV.xaxis.set_major_formatter(ticker.NullFormatter())
        subPlotV.xaxis.set_minor_locator(ticker.FixedLocator([3.5, 9.5, 15.5, 21.5, 27.5]))
        subPlotV.xaxis.set_minor_formatter(ticker.FixedFormatter(['Ve = ' + str(referValueV[0]), 'Ve = ' + str(referValueV[1]), 'Ve = ' + str(referValueV[2]), 'Ve = ' + str(referValueV[3]), 'Ve = ' + str(referValueV[4])]))
        for i in range(self.newModel.nrOfColumns):
            subPlotV.axvline(x = self.newModel.nrOfRows * i + 0.5, color = 'green', linestyle = 'dashed')


        self.figureBoxPlot.tight_layout()
        self.canvasBoxPlot.draw()
        self.rightPanel.Layout()

    def DrawHistograms(self):
        # draw histograms of imported calculated Ktrans and Ve maps, so that the user can have a look of the distribution of each patch.

        self.figureHist_Ktrans.suptitle('The histogram of the calculated Ktrans',) # fontsize = 18)
        self.figureHist_Ve.suptitle('The histogram of the calculated Ve') # , fontsize = 18)

        pixelCountInPatch = self.newModel.patchLen ** 2
        nrOfBins = 10

        for i in range(self.newModel.nrOfRows):
            for j in range(self.newModel.nrOfColumns):
                subPlot_K = self.figureHist_Ktrans.add_subplot(self.newModel.nrOfRows, self.newModel.nrOfColumns, i * self.newModel.nrOfColumns + j + 1)
                # subPlot_K.clear()
                subPlot_K.hist(self.newModel.Ktrans_cal[i][j], nrOfBins)
                minPatch_K = numpy.min(self.newModel.Ktrans_cal[i][j])
                maxPatch_K = numpy.max(self.newModel.Ktrans_cal[i][j])
                meanPatch_K = numpy.mean(self.newModel.Ktrans_cal[i][j])
                subPlot_K.set_xticks([minPatch_K, maxPatch_K])
                subPlot_K.set_xticklabels([str(minPatch_K), str(maxPatch_K)])
                subPlot_K.axvline(meanPatch_K, color = 'r', linestyle = 'dashed', linewidth = 1) # draw a vertical line at the mean value
                subPlot_K.set_ylim([0, pixelCountInPatch])
                subPlot_K.text(meanPatch_K + 0.01 * meanPatch_K, 0.9 * pixelCountInPatch, str(meanPatch_K), size = 'x-small') # parameters: location_x, location_y, text, size
                if i == 0:
                    subPlot_K.set_xlabel('Ve = ' + str(self.newModel.Ve_ref[i][j][0]))
                    subPlot_K.xaxis.set_label_position('top')
                if j == 0:
                    subPlot_K.set_ylabel('Ktrans = ' + str(self.newModel.Ktrans_ref[i][j][0]))

                subPlot_V = self.figureHist_Ve.add_subplot(self.newModel.nrOfRows, self.newModel.nrOfColumns, i * self.newModel.nrOfColumns + j + 1 )
                # subPlot_V.clear()
                subPlot_V.hist(self.newModel.Ve_cal[i][j], nrOfBins)
                minPatch_V = numpy.min(self.newModel.Ve_cal[i][j])
                maxPatch_V = numpy.max(self.newModel.Ve_cal[i][j])
                meanPatch_V = numpy.mean(self.newModel.Ve_cal[i][j])
                subPlot_V.set_xticks([minPatch_V, maxPatch_V])
                subPlot_V.set_xticklabels([str(minPatch_V), str(maxPatch_V)])
                subPlot_V.axvline(meanPatch_V, color = 'r', linestyle = 'dashed', linewidth = 1) # draw a vertical line at the mean value
                subPlot_V.set_ylim([0, pixelCountInPatch])
                subPlot_V.text(meanPatch_V + 0.01 * meanPatch_V, 0.9 * pixelCountInPatch, str(meanPatch_V), size = 'x-small') # parameters: location_x, location_y, text, size
                if i == 0:
                    subPlot_V.set_xlabel('Ve = ' + str(self.newModel.Ve_ref[i][j][0]))
                    subPlot_V.xaxis.set_label_position('top')
                if j == 0:
                    subPlot_V.set_ylabel('Ktrans = ' + str(self.newModel.Ktrans_ref[i][j][0]))


        self.figureHist_Ve.tight_layout()
        self.figureHist_Ktrans.tight_layout()

        self.figureHist_Ktrans.subplots_adjust(top = 0.94, right = 0.95)
        self.figureHist_Ve.subplots_adjust(top = 0.94, right = 0.95)

        self.canvasHist_Ktrans.draw()
        self.canvasHist_Ve.draw()

    def GetResultInHtml(self):
        # render the figures, tables into html, for exporting to pdf
        htmlContent = ''
        self.figureImagePreview.savefig(os.path.join(os.getcwd(), 'temp', 'figureImages.png'))
        self.figureScatter.savefig(os.path.join(os.getcwd(), 'temp', 'figureScatters.png'))
        self.figureHist_Ktrans.savefig(os.path.join(os.getcwd(), 'temp', 'figureHist_K.png'))
        self.figureHist_Ve.savefig(os.path.join(os.getcwd(), 'temp', 'figureHist_V.png'))
        self.figureBoxPlot.savefig(os.path.join(os.getcwd(), 'temp', 'figureBoxPlots.png'))

        htmlContent += self.newModel.packInHtml('<h1 align="center">QIBA DRO Evaluation Tool Results Report</h1>')

        htmlContent += self.newModel.packInHtml('''
        <h2 align="center">The image view of calculated Ktrans and Ve</h2>''' +\
        '''<img src="''' + os.path.join(os.getcwd(), 'temp', 'figureImages.png') + '''" style="width:100%"> <br>'''+\
        '''<p><font face="verdana">* The first column shows the calculated Ktrans and Ve in black and white. You can have a general impression of the value distribution according to the changing of the parameters. Generally the brighter the pixel is, the higher the calculated value is.<br>
        <br>The Second column shows the error map between calculated and reference data. Each pixel is the result of corresponding pixel in calculated data being subtracted with that in the reference data. Generally the more the color approaches to the red direction, the larger the error is.<br>
        <br>The third column shows the normalized error. This is out of the consideration that the error could be related with the original value itself. Therefore normalized error may give a more uniformed standard of the error level. Each pixel's value comes from the division of the error by the reference pixel value. Similarly as the error map, the more the color approaches to the red direction, the larger the normalized error is.
        </p>''' )

        htmlContent += self.newModel.packInHtml( '''
        <h2 align="center">The scatter plots of calculated Ktrans and Ve</h2>
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureScatters.png') + '''" style="width:100%"> <br>'''+\
        '''<p><font face="verdana">* For the reference data, the pixel values in one row (for Ktrans) or column (for Ve) share the same constant value. Therefore in the scatter plot it shows that all green dots of a row (or column) overlap to each other. For the calculated data, as they share the same parameter, the blue dots align to the same x-axis. But they may scatter vertically, showing there's variance of the value in a row (or column).<br>
        <br>From these plots you can see the trend of the values, which offer some information of which model (e.g. linear or logarithmic) the calculated parameter may fit. For example, with the artificial calculated data which were generated from the reference data by adding Gaussian noise, scaling by two and adding 0.5, it can be easily read from the plots that the calculated data follow the linear model, and have scaling factor and extra bias value.
        </p>''' )

        htmlContent += self.newModel.packInHtml('''
        <h2 align="center">The histograms of calculated Ktrans and Ve</h2>
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureHist_K.png') + '''" style="width:50%" align="left">''' + '''
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureHist_V.png') + '''" style="width:50%" align="right"> <br>'''+\
        '''<p><font face="verdana">* All histograms have the uniformed y-axis limits, so that the comparison among different patched is easier.  The minimum and maximum values of a patch are denoted on the x-axis for reference.
        </p>''')

        htmlContent += self.newModel.packInHtml('''
        <h2 align="center">The box plots of calculated Ktrans and Ve</h2>
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureBoxPlots.png') + '''" style="width:100%"> <br>'''+\
        '''<p><font face="verdana">* The vertical dash lines are used to separate the rows (or columns), as each box plot is responsible for one patch. From these plots you could see (roughly) the statistics of each patch, like the mean value, the 1st and 3rd quartile, the minimum and maximum value. The more precise value of those statistics could be found in the tab "Result in HTML viewer".
        </p>''')

        htmlContent += self.newModel.StatisticsInHTML

        htmlContent += self.newModel.ModelFittingInHtml

        htmlContent += self.newModel.T_testResultInHTML

        htmlContent += self.newModel.U_testResultInHTML

        htmlContent += self.newModel.ANOVAResultInHTML

        return htmlContent

    def OnClearModelList(self, event):
        # not used now
        # clear the list which holds all the models that have been evaluated.
        if self.testedModels == []:
            self.SetStatusText('Evaluated model list is empty.')
        else:
            self.testedModels = []
            self.SetStatusText('Evaluated model list is cleared.')

        # clean the interface plots
        self.ClearInterface()

    def ClearInterface(self):
        # clear the plots in the interface, so that when the evaluated models are cleared, the interface will also be cleaned.
        self.figureImagePreview.clear()
        self.canvasImagePreview.draw()

        self.figureScatter.clear()
        self.canvasScatter.draw()

        self.figureBoxPlot.clear()
        self.canvasBoxPlot.draw()

        self.figureHist_Ktrans.clear()
        self.canvasHist_Ktrans.draw()
        self.figureHist_Ve.clear()
        self.canvasHist_Ve.draw()

        self.statisticsViewer.SetPage('')
        self.covCorrViewer.SetPage('')
        self.modelFittingViewer.SetPage('')
        self.t_testViewer.SetPage('')
        self.U_testViewer.SetPage('')
        self.ANOVAViewer.SetPage('')

    def ClearPanel(self, panel):
        # clear a panel object(from wxPython)
        for child in panel.GetChildren():
            if child:
                child.Destroy()
            else:
                pass

    def OnExport(self, event):
        # export the evaluation results to PDF

        # disable some widgets
        self.buttonEvaluate.Disable()
        self.buttonExport.Disable()

        # show in status bar when export finishes
        self.SetStatusText('Exporting results...')

        # save file path dialog
        savePath = ''
        dlg = wx.FileDialog(self, 'Export the results as PDF file...', '', '', "PDF file(*.pdf)|*.pdf", wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            savePath = dlg.GetPath()
        else:
            return False

        # save to temp html file
        resultToSaveInHtml = self.GetResultInHtml()
        temp_html = open(os.path.join(os.getcwd(), 'temp', 'temp.html'), 'w+')
        temp_html.write(resultToSaveInHtml)
        temp_html.close()

        # due to the Python wrapper of wkhtmltopdf "python_wkhtmltopdf" pre-requires xvfb is not available for Windows, here use commandline to call the tool
        cmd=[os.path.join(os.getcwd(), 'tools', 'wkhtmltopdf', 'bin', 'wkhtmltopdf'), os.path.join(os.getcwd(), 'temp', 'temp.html'), savePath]
        process = subprocess.Popen(cmd) #, stdout=subprocess.PIPE)
        process.wait()

        # remove the temp file
        # os.remove(os.path.join(os.getcwd(), 'temp', 'temp.html'))
        os.remove(os.path.join(os.getcwd(), 'temp', 'figureImages.png'))
        os.remove(os.path.join(os.getcwd(), 'temp', 'figureScatters.png'))
        os.remove(os.path.join(os.getcwd(), 'temp', 'figureHist_K.png'))
        os.remove(os.path.join(os.getcwd(), 'temp', 'figureHist_V.png'))
        os.remove(os.path.join(os.getcwd(), 'temp', 'figureBoxPlots.png'))

        # show in status bar when export finishes
        self.SetStatusText('Results exported as PDF file.')

        # enable some widgets
        self.buttonEvaluate.Enable()
        self.buttonExport.Enable()

    def OnQuit(self, event):
        # quit the application
        self.Close()

    def OnAbout(self, event):
        # show the information about this application and the related.
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

class ModelEvaluated:
    '''
    the class for a evaluated model. It includes the necessary data and methods for evaluating the result from one calculation model.
    '''
    def __init__(self):
        # initializes the class

        # parameters of the image size
        self.nrOfRows = 6
        self.nrOfColumns = 5
        self.patchLen = 10
        self.METHOD = '' # for patch value decision

        # the raw image data as pixel flow
        self.Ktrans_ref = []
        self.Ve_ref = []
        self.Ktrans_cal = []
        self.Ve_cal = []

        # the image data in row, for showing the preview of the images
        self.Ktrans_ref_inRow = [[]for i in range(self.nrOfRows * self.patchLen)]
        self.Ve_ref_inRow = [[]for i in range(self.nrOfRows * self.patchLen)]
        self.Ktrans_cal_inRow = [[]for i in range(self.nrOfRows * self.patchLen)]
        self.Ve_cal_inRow = [[]for i in range(self.nrOfRows * self.patchLen)]

        # the error map between calculated and reference file
        self.Ktrans_error = []
        self.Ve_error = []
        self.Ktrans_error_normalized = []
        self.Ve_error_normalized = []

        # the mean value(or median value) matrix of a calculated image
        self.Ktrans_ref_patchValue = [[]for i in range(self.nrOfRows)]
        self.Ve_ref_patchValue = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patchValue = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patchValue = [[]for i in range(self.nrOfRows)]

        # the mean value
        self.Ktrans_ref_patch_mean = [[]for i in range(self.nrOfRows)]
        self.Ve_ref_patch_mean = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patch_mean = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_mean = [[]for i in range(self.nrOfRows)]

        # the median value
        self.Ktrans_ref_patch_median = [[]for i in range(self.nrOfRows)]
        self.Ve_ref_patch_median = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patch_median = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_median = [[]for i in range(self.nrOfRows)]

        # the deviation
        self.Ktrans_cal_patch_deviation = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_deviation = [[]for i in range(self.nrOfRows)]

        # the first quartile
        self.Ktrans_cal_patch_1stQuartile = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_1stQuartile = [[]for i in range(self.nrOfRows)]

        # the third quartile
        self.Ktrans_cal_patch_3rdQuartile = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_3rdQuartile = [[]for i in range(self.nrOfRows)]

        # the min. value
        self.Ktrans_cal_patch_min = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_min = [[]for i in range(self.nrOfRows)]

        # the max. value
        self.Ktrans_cal_patch_max = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_max = [[]for i in range(self.nrOfRows)]

         # the student-t test
        self.Ktrans_cal_patch_ttest_t = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_ttest_t = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patch_ttest_p = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_ttest_p = [[]for i in range(self.nrOfRows)]

        # the U test
        self.Ktrans_cal_patch_Utest_u = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_Utest_u = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patch_Utest_p = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patch_Utest_p = [[]for i in range(self.nrOfRows)]

        # ANOVA
        self.Ktrans_cal_patch_ANOVA_f = []
        self.Ktrans_cal_patch_ANOVA_p = []
        self.Ve_cal_patch_ANOVA_f = []
        self.Ve_cal_patch_ANOVA_p = []

        # covarinace
        self.cov_KK = []
        self.cov_VK = []
        self.cov_KV = []
        self.cov_VV = []

        # covarinace
        self.corr_KK = []
        self.corr_VK = []
        self.corr_KV = []
        self.corr_VV = []

        # planar fitting parameters
        self.Ktrans_fittingParameter = []
        self.Ve_fittingParameter = []

        # the result text
        self.resultText = ''

        # the result in HTML
        self.resultInHTML = ''

    def Evaluate(self, path_K_ref, path_V_ref, path_K_cal, path_V_cal):
        # evaluation
        # pre-process for the imported files
        self.ImportFiles(path_K_ref, path_V_ref, path_K_cal, path_V_cal)

        self.CalculateErrorForModel()
        self.EstimatePatchForModel('MEAN')

        # evaluation operations
        self.FittingLinearModelForModel()
        self.FittingLogarithmicModelForModel()
        self.CalculateCorrelationForModel()
        self.CalculateCovarianceForModel()
        self.CalculateMeanForModel()
        self.CalculateMedianForModel()
        self.CalculateSTDDeviationForModel()
        self.Calculate1stAnd3rdQuartileForModel()
        self.CalculateMinAndMaxForModel()
        self.T_TestForModel()
        self.U_TestForModel()
        self.ANOVAForModel()

        # write HTML result
        self.htmlCovCorrResults()
        self.htmlModelFitting()
        self.htmlT_TestResults()
        self.htmlU_TestResults()
        self.htmlStatistics()
        self.htmlANOVAResults()

    def htmlStatistics(self):
        # write the statistics to html form

        statisticsNames = ['Mean', 'Median', 'std. Derivative', '1st Quartile', '3rd Quartile', 'min.', 'max.']
        statisticsData = [[self.Ktrans_cal_patch_mean, self.Ktrans_cal_patch_median, self.Ktrans_cal_patch_deviation, self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_3rdQuartile, self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_max],
                          [self.Ve_cal_patch_mean, self.Ve_cal_patch_median, self.Ve_cal_patch_deviation, self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_3rdQuartile, self.Ve_cal_patch_min, self.Ve_cal_patch_max]]



        # Ktrans statistics tables
        KtransStatisticsTable = \
                        '<h2>The statistics analysis of each patch in calculated Ktrans:</h2>'

        KtransStatisticsTable += self.EditTable('the mean and standard deviation value', ['mean', 'std. deviation'], [self.Ktrans_cal_patch_mean, self.Ktrans_cal_patch_deviation])

        KtransStatisticsTable += self.EditTable('the median, 1st and 3rd quartile, min. and max. values', ['min.', '1st quartile', 'median', '3rd quartile', 'max.'], [self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_median, self.Ktrans_cal_patch_3rdQuartile, self.Ktrans_cal_patch_max])




        # Ve statistics table
        VeStatisticsTable = \
                        '<h2>The statistics analysis of each patch in calculated Ve:</h2>'

        VeStatisticsTable += self.EditTable('the mean and standard deviation value', ['mean', 'std. deviation'], [self.Ve_cal_patch_mean, self.Ve_cal_patch_deviation])

        VeStatisticsTable += self.EditTable('the median, 1st and 3rd quartile, min. and max. values', ['min.', '1st quartile', 'median', '3rd quartile', 'max.'], [self.Ve_cal_patch_min, self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_median, self.Ve_cal_patch_3rdQuartile, self.Ve_cal_patch_max])

        # put the text into html structure
        self.StatisticsInHTML = self.packInHtml(KtransStatisticsTable + '<br>' + VeStatisticsTable)

    def htmlModelFitting(self):
        # write the model fitting results to html

        # Ktrans planar fitting
        KtransLinearFitting = '<h2>The linear model fitting for calculated Ktrans:</h2>' \
                            '<p>Ktrans_cal = ' + self.formatFloatTo4DigitsString(self.a_lin_Ktrans) + '  * Ktrans_ref + ' + self.formatFloatTo4DigitsString(self.b_lin_Ktrans) + ' * Ve_ref + ' + self.formatFloatTo4DigitsString(self.c_lin_Ktrans) + '</p>'

        # Ktrans logarithmic fitting
        KtransLogarithmicFitting = '<h2>The logarithmic model fitting for calculated Ktrans:</h2>' \
                                        '<table border="1" cellspacing="10">'

        for j in range(self.nrOfColumns):
            KtransLogarithmicFitting += '<tr>'
            KtransLogarithmicFitting += '<th>Ref. Ve = '
            KtransLogarithmicFitting += str('{:3.2f}'.format(zip(*self.Ve_ref_patchValue)[j][0]))
            KtransLogarithmicFitting += '</th>'

            KtransLogarithmicFitting += '<td align="right">Ktrans_cal = '
            KtransLogarithmicFitting += self.formatFloatTo4DigitsString(self.a_log_Ktrans[j])
            KtransLogarithmicFitting += ' + '
            KtransLogarithmicFitting += self.formatFloatTo4DigitsString(self.corr_KK[j])
            KtransLogarithmicFitting += ' * log10(Ktrans_ref)'
            KtransLogarithmicFitting += '</td>'
            KtransLogarithmicFitting += '</tr>'

        KtransLogarithmicFitting += '</table>'


        # Ve planar fitting
        VeLinearFitting = \
                        '<h2>The linear model fitting for calculated Ve:</h2>' \
                            '<p>Ve_cal = ' + self.formatFloatTo4DigitsString(self.a_lin_Ve) + '  * Ktrans_ref + ' + self.formatFloatTo4DigitsString(self.b_lin_Ve) + ' * Ve_ref + ' + self.formatFloatTo4DigitsString(self.c_lin_Ve) + '</p>'

        # Ve logarithmic fitting
        VeLogarithmicFitting = '<h2>The logarithmic model fitting for calculated Ve:</h2>'\
                        '<table border="1" cellspacing="10">'

        for i in range(self.nrOfRows):
            VeLogarithmicFitting += '<tr>'
            VeLogarithmicFitting += '<th>Ref. Ktrans = '
            VeLogarithmicFitting += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            VeLogarithmicFitting += '</th>'

            VeLogarithmicFitting += '<td align="right">Ve_cal = '
            VeLogarithmicFitting += self.formatFloatTo4DigitsString(self.a_log_Ve[i])
            VeLogarithmicFitting += ' + '
            VeLogarithmicFitting += self.formatFloatTo4DigitsString(self.corr_KV[i])
            VeLogarithmicFitting += ' * log10(Ve_ref)'
            VeLogarithmicFitting += '</td>'
            VeLogarithmicFitting += '</tr>'
        VeLogarithmicFitting += '</table>'


        self.ModelFittingInHtml = self.packInHtml(KtransLinearFitting + '<br>' + KtransLogarithmicFitting + '<br>' + VeLinearFitting + '<br>' + VeLogarithmicFitting)


    def htmlCovCorrResults(self):
        # write the correlation and covariance results into html

        # relation between cal. K and ref. K
        KK_Table = '<h2>The correlation and covariance of each column in calculated Ktrans map with reference Ktrans map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            KK_Table += '<th>Ref. Ve = '
            KK_Table += str('{:3.2f}'.format(zip(*self.Ve_ref_patchValue)[j][0]))
            KK_Table += '</th>'
        KK_Table += '</tr>'

        KK_Table += '<tr>'
        for j in range(self.nrOfColumns):
            KK_Table += '<td align="right">cov.: '
            KK_Table += self.formatFloatTo4DigitsString(self.cov_KK[j])
            KK_Table += '<br>corr.: '
            KK_Table += self.formatFloatTo4DigitsString(self.corr_KK[j])
            KK_Table += '</td>'
        KK_Table += '</tr>'
        KK_Table += '</table>'

        # relation between cal. K and ref. V
        KV_Table = '<h2>The correlation and covariance of each row in calculated Ktrans map with reference Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            KV_Table += '<th>Ref. Ktrans = '
            KV_Table += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            KV_Table += '</th>'
        KV_Table += '</tr>'

        KV_Table += '<tr>'
        for i in range(self.nrOfRows):
            KV_Table += '<td align="right">cov.: '
            KV_Table += self.formatFloatTo4DigitsString(self.cov_KV[i])
            KV_Table += '<br>corr.: '
            KV_Table += self.formatFloatTo4DigitsString(self.corr_KV[i])
            KV_Table += '</td>'
        KV_Table += '</tr>'
        KV_Table += '</table>'

        # relation between cal. V and ref. K
        VK_Table = '<h2>The correlation and covariance of each column in calculated Ve map with reference Ktrans map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            VK_Table += '<th>Ref. Ve = '
            VK_Table += str('{:3.2f}'.format(zip(*self.Ve_ref_patchValue)[j][0]))
            VK_Table += '</th>'
        VK_Table += '</tr>'

        VK_Table += '<tr>'
        for j in range(self.nrOfColumns):
            VK_Table += '<td align="right">cov.: '
            VK_Table += self.formatFloatTo4DigitsString(self.cov_VK[j])
            VK_Table += '<br>corr.: '
            VK_Table += self.formatFloatTo4DigitsString(self.corr_VK[j])
            VK_Table += '</td>'
        VK_Table += '</tr>'
        VK_Table += '</table>'

        # relation between cal. V and ref. V
        VV_Table = '<h2>The correlation and covariance of each row in calculated Ve map with reference Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            VV_Table += '<th>Ref. Ktrans = '
            VV_Table += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            VV_Table += '</th>'
        VV_Table += '</tr>'

        VV_Table += '<tr>'
        for i in range(self.nrOfRows):
            VV_Table += '<td align="right">cov.: '
            VV_Table += self.formatFloatTo4DigitsString(self.cov_VV[i])
            VV_Table += '<br>corr.: '
            VV_Table += self.formatFloatTo4DigitsString(self.corr_VV[i])
            VV_Table += '</td>'
        VV_Table += '</tr>'
        VV_Table += '</table>'

        self.covCorrResultsInHtml = self.packInHtml(KK_Table + '<br>' + KV_Table + '<br>' + VK_Table + '<br>' + VV_Table)

    def htmlT_TestResults(self):
        # write the t-test results into HTML form

        statisticsNames = [ 't-test: t-statistic', 't-test: p-value']
        statisticsData = [[self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p],
                          [ self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p]]

        # Ktrans statistics tables
        KtransT_TestTable = \
                        '<h2>The t-test result of each patch in calculated Ktrans map:</h2>'

        KtransT_TestTable += self.EditTable('', ['t-statistic', 'p-value'], [self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p])

        # Ktrans statistics tables
        VeT_TestTable = \
                        '<h2>The t-test result of each patch in calculated Ve map:</h2>'

        VeT_TestTable += self.EditTable('', ['t-statistic', 'p-value'], [self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p])


        # put the text into html structure
        self.T_testResultInHTML = self.packInHtml(KtransT_TestTable + '<br>' + VeT_TestTable)

    def htmlU_TestResults(self):
        # write the U-test results into HTML form

        # Ktrans statistics tables
        KtransU_TestTable = \
                        '<h2>The Mann-Whitney U test result of each patch in calculated Ktrans map:</h2>'

        KtransU_TestTable += self.EditTable('', ['U-value', 'p-value'], [self.Ktrans_cal_patch_Utest_u, self.Ktrans_cal_patch_Utest_p])

        # Ktrans statistics tables
        VeU_TestTable = \
                        '<h2>The Mann-Whitney test result of each patch in calculated Ve map:</h2>'

        VeU_TestTable += self.EditTable('', ['U-value', 'p-value'], [self.Ve_cal_patch_Utest_u, self.Ve_cal_patch_Utest_p])


        # put the text into html structure
        self.U_testResultInHTML = self.packInHtml(KtransU_TestTable + '<br>' + VeU_TestTable)

    def htmlANOVAResults(self):
        # write the ANOVA results into HTML form

        statisticsNames = [ 'ANOVA: f-value', 'ANOVA: p-value']
        statisticsData = [[self.Ktrans_cal_patch_ANOVA_f, self.Ktrans_cal_patch_ANOVA_p],
                          [ self.Ve_cal_patch_ANOVA_f, self.Ve_cal_patch_ANOVA_p]]

        # Ktrans ANOVA tables
        KtransANOVATable = \
                        '<h2>The ANOVA result of each row in calculated Ktrans map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for i in range(self.nrOfRows):
            KtransANOVATable += '<th>Ktrans = '
            KtransANOVATable += str('{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]))
            KtransANOVATable += '</th>'
        KtransANOVATable += '</tr>'

        KtransANOVATable += '<tr>'
        for i in range(self.nrOfRows):
            KtransANOVATable += '<td align="right">f-value: '
            KtransANOVATable += self.formatFloatTo4DigitsString(self.Ktrans_cal_patch_ANOVA_f[i])
            KtransANOVATable += '<br>p-value: '
            KtransANOVATable += self.formatFloatTo4DigitsString(self.Ktrans_cal_patch_ANOVA_p[i])
            KtransANOVATable += '</td>'
        KtransANOVATable += '</tr>'
        KtransANOVATable += '</table>'

        # Ve ANOVA tables
        VeANOVATable = \
                        '<h2>The ANOVA result of each column in calculated Ve map:</h2>'\
                        '<table border="1" cellspacing="10">'\
                            '<tr>'
        for j in range(self.nrOfColumns):
            VeANOVATable += '<th>Ve = '
            VeANOVATable += str('{:3.2f}'.format(zip(*self.Ve_ref_patchValue)[j][0]))
            VeANOVATable += '</th>'
        VeANOVATable += '</tr>'

        VeANOVATable += '<tr>'
        for j in range(self.nrOfColumns):
            VeANOVATable += '<td align="right">f-value: '
            VeANOVATable += self.formatFloatTo4DigitsString(self.Ve_cal_patch_ANOVA_f[j])
            VeANOVATable += '<br>p-value: '
            VeANOVATable += self.formatFloatTo4DigitsString(self.Ve_cal_patch_ANOVA_p[j])
            VeANOVATable += '</td>'
        VeANOVATable += '</tr>'
        VeANOVATable += '</table>'

        # put the text into html structure
        self.ANOVAResultInHTML = self.packInHtml(KtransANOVATable + '<br>' + VeANOVATable)

    def packInHtml(self, content):
        # pack the content into html, so that the exported pdf can start a new page.
        htmlText = ''
        htmlText += '''
        <!DOCTYPE html>
        <html>
        <body>
        '''
        htmlText += content

        htmlText += '''
        </body>
        </html>
        '''
        return htmlText

    def EditTable(self, caption, entryName, entryData):
        # edit a table of certain scale in html. return the table part html
        # for the first line
        tableText = '<h3>' + caption + '</h3>'
        tableText += '<table border="1" cellspacing="10">'
        # tableText += '<caption>' + caption + '</caption>'
        tableText += '<tr>'
        tableText +=     '<th></th>'
        for Ve in self.Ve_ref_patchValue[0]:
            tableText += '<th>Ve = ' + '{:3.2f}'.format(Ve) + '</th>'
        tableText += '</tr>'

        # for the column headers and the table cells.
        for i in range(self.nrOfRows):
            tableText += '<tr>'
            tableText +=    '<th>Ktrans = ' + '{:3.2f}'.format(self.Ktrans_ref_patchValue[i][0]) + '</th>'
            for j in range(self.nrOfColumns):
                tableText += '<td align="right">'
                for name, data in zip(entryName, entryData):
                    tableText += name + ' = ' + self.formatFloatTo4DigitsString(data[i][j]) + '<br>'
                tableText = tableText[:-4]
                tableText += '</td>'
            tableText += '</tr>'

        tableText += '</table>'
        tableText += '<br>'

        return tableText

    def GetStatisticsInHTML(self):
        # getter for the result in HTML.
        return self.StatisticsInHTML

    def GetCovarianceCorrelationInHTML(self):
        # getter for the result in HTML.
        return self.covCorrResultsInHtml

    def GetModelFittingInHTML(self):
        # getter for the result in HTML
        return self.ModelFittingInHtml

    def GetT_TestResultsInHTML(self):
        # getter for the result in HTML.
        return self.T_testResultInHTML

    def GetU_TestResultsInHTML(self):
        # getter for the result in HTML.
        return self.U_testResultInHTML

    def GetANOVAResultsInHTML(self):
        # getter for the result in HTML.
        return self.ANOVAResultInHTML

    def ImportFiles(self, path_K_ref, path_V_ref, path_K_cal, path_V_cal):
        # import the DICOM files for evaluation.
        self.Ktrans_ref_inRow, self.Ktrans_ref = self.ImportFile(path_K_ref)
        self.Ve_ref_inRow, self.Ve_ref = self.ImportFile(path_V_ref)
        self.Ktrans_cal_inRow, self.Ktrans_cal = self.ImportFile(path_K_cal)
        self.Ve_cal_inRow, self.Ve_cal = self.ImportFile(path_V_cal)

    def CalculateErrorForModel(self):
        # calculate the error between calculated and reference files
        self.Ktrans_error = self.CalculateError(self.Ktrans_cal_inRow, self.Ktrans_ref_inRow)
        self.Ve_error = self.CalculateError(self.Ve_cal_inRow, self.Ve_ref_inRow)

        self.Ktrans_error_normalized = self.CalculateNormalizedError(self.Ktrans_cal_inRow, self.Ktrans_ref_inRow)
        self.Ve_error_normalized = self.CalculateNormalizedError(self.Ve_cal_inRow, self.Ve_ref_inRow)

    def EstimatePatchForModel(self, patchValueMethod):
        # estimate the value to represent the patches for each imported DICOM
        self.Ktrans_ref_patchValue = self.EstimatePatch(self.Ktrans_ref, patchValueMethod)
        self.Ve_ref_patchValue = self.EstimatePatch(self.Ve_ref, patchValueMethod)
        self.Ktrans_cal_patchValue = self.EstimatePatch(self.Ktrans_cal, patchValueMethod)
        self.Ve_cal_patchValue = self.EstimatePatch(self.Ve_cal, patchValueMethod)

    def FittingLinearModelForModel(self):
        # fit a planar for the calculated Ktrans and Ve maps
        self.a_lin_Ktrans, self.b_lin_Ktrans, self.c_lin_Ktrans = self.FittingLinearModel(self.Ktrans_cal_patchValue)
        self.a_lin_Ve, self.b_lin_Ve, self.c_lin_Ve = self.FittingLinearModel(self.Ve_cal_patchValue)

    def FittingLogarithmicModelForModel(self):
        # fitting logarithmic model
        self.a_log_Ktrans,self.b_log_Ktrans = self.FittingLogarithmicModel_K(self.Ktrans_cal_patchValue, self.Ktrans_ref_patchValue) # , self.c_log_Ktrans
        self.a_log_Ve,self.b_log_Ve = self.FittingLogarithmicModel_V(self.Ve_cal_patchValue, self.Ve_ref_patchValue) # , self.c_log_Ve

    def CalculateCorrelationForModel(self):
        # calculate the correlation between the calculated parameters and the reference parameters
        # 'Corre_KV' stands for 'correlation coefficient between calculate Ktrans and reference Ve', etc.

        for i in range(self.nrOfColumns):
            self.corr_KK.append(self.CalCorrMatrix(zip(*self.Ktrans_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
            self.corr_VK.append(self.CalCorrMatrix(zip(*self.Ve_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
        for j in range(self.nrOfRows):
            self.corr_VV.append(self.CalCorrMatrix(self.Ve_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
            self.corr_KV.append(self.CalCorrMatrix(self.Ktrans_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])

    def CalculateCovarianceForModel(self):
        # calculate the covariance between the calculated parameters and the reference parameters
        # e.g. 'cov_KV' stands for 'correlation coefficient between calculate Ktrans and reference Ve', etc.

        for i in range(self.nrOfColumns):
            self.cov_KK.append(self.CalCovMatrix(zip(*self.Ktrans_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
            self.cov_VK.append(self.CalCovMatrix(zip(*self.Ve_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
        for j in range(self.nrOfRows):
            self.cov_VV.append(self.CalCovMatrix(self.Ve_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
            self.cov_KV.append(self.CalCovMatrix(self.Ktrans_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])

    def CalculateMeanForModel(self):
        # call the mean calculation function
        self.Ktrans_cal_patch_mean = self.CalculateMean(self.Ktrans_cal)
        self.Ve_cal_patch_mean = self.CalculateMean(self.Ve_cal)

    def CalculateMedianForModel(self):
        # call the median calculation function
        self.Ktrans_cal_patch_median = self.CalculateMedian(self.Ktrans_cal)
        self.Ve_cal_patch_median = self.CalculateMedian(self.Ve_cal)

    def CalculateSTDDeviationForModel(self):
        # call the std deviation calculation function
        self.Ktrans_cal_patch_deviation = self.CalculateSTDDeviation(self.Ktrans_cal)
        self.Ve_cal_patch_deviation = self.CalculateSTDDeviation(self.Ve_cal)

    def Calculate1stAnd3rdQuartileForModel(self):
        # call the 1st and 3rd quartile calculation function
        self.Ktrans_cal_patch_1stQuartile, self.Ktrans_cal_patch_3rdQuartile = self.Calculate1stAnd3rdQuartile(self.Ktrans_cal)
        self.Ve_cal_patch_1stQuartile, self.Ve_cal_patch_3rdQuartile = self.Calculate1stAnd3rdQuartile(self.Ve_cal)

    def CalculateMinAndMaxForModel(self):
        self.Ktrans_cal_patch_min, self.Ktrans_cal_patch_max = self.CalculateMinAndMax(self.Ktrans_cal)
        self.Ve_cal_patch_min, self.Ve_cal_patch_max = self.CalculateMinAndMax(self.Ve_cal)

    def T_TestForModel(self):
        # call the Ttest function
        self.Ktrans_cal_patch_ttest_t, self.Ktrans_cal_patch_ttest_p = self.T_Test_1samp(self.Ktrans_cal, self.Ktrans_ref_patchValue)
        self.Ve_cal_patch_ttest_t, self.Ve_cal_patch_ttest_p = self.T_Test_1samp(self.Ve_cal, self.Ve_ref_patchValue)

    def U_TestForModel(self):
        # call the U test function
        self.Ktrans_cal_patch_Utest_u, self.Ktrans_cal_patch_Utest_p = self.U_Test(self.Ktrans_cal, self.Ktrans_ref)
        self.Ve_cal_patch_Utest_u, self.Ve_cal_patch_Utest_p = self.U_Test(self.Ve_cal, self.Ve_ref)

    def ANOVAForModel(self):
        # call the ANOVA function
        self.Ktrans_cal_patch_ANOVA_f, self.Ktrans_cal_patch_ANOVA_p = self.ANOVA_oneway_K(self.Ktrans_cal)
        self.Ve_cal_patch_ANOVA_f, self.Ve_cal_patch_ANOVA_p = self.ANOVA_oneway_V(self.Ve_cal)

############## ############## the unit functions ############## ##############
    def formatFloatTo4DigitsString(self, input):
        # format the input value into a string with 2 digits
        if abs(input) < 0.0001:
            return  str('{:5.4e}'.format(float(input)))
        else:
            return  str('{:5.4f}'.format(float(input)))

    def ImportFile(self, path):
        # import a file. and pre-process the data so that handy to use later

        fileName, self.fileExtensionRef = os.path.splitext(path)
        if self.fileExtensionRef == '.dcm':
            try:
                ds =  dicom.read_file(path)
                rescaled = self.RescaleDICOM(ds)
                rearranged = self.RearrangeDICOM(rescaled)
                return rescaled, rearranged
            except:
                wx.MessageBox('Invalid file path!\n' + '(' + path +')', 'Cannot import file', wx.OK | wx.ICON_INFORMATION)
                return False

        elif self.fileExtensionRef == '.bin' or '.raw':
            binaryData = []
            rawData = open(path, 'rb').read()
            fileLength = os.stat(path).st_size
            dataLength = fileLength / ((self.nrOfRows + 2) * self.nrOfColumns * self.patchLen * self.patchLen)
            if dataLength == 4:
                dataType = 'f'
            elif dataLength == 8:
                dataType = 'd'
            for i in range(fileLength / dataLength):
                data = rawData[i * dataLength : (i + 1) * dataLength]
                binaryData.append(struct.unpack(dataType, data)[0])
            sectioned, rearranged = self.RearrangeBIN(binaryData)
            return sectioned, rearranged

    def RescaleDICOM(self, ds):
        # rescale the DICOM file to remove the intercept and the slope. the 'pixel' in DICOM file means a row of pixels.
        try:
            self.rescaleIntercept = ds.RescaleIntercept
            self.rescaleSlope = ds.RescaleSlope
        except:
            self.rescaleIntercept = 0
            self.rescaleSlope = 1
        pixelFlow = []
        for row in ds.pixel_array:
            temp = []
            for pixel in row:
                temp.append(pixel * self.rescaleSlope + self.rescaleIntercept)
            pixelFlow.append(temp)

        # remove the first and last row which do not contain valid data
        pixelFlow = pixelFlow[self.patchLen:-self.patchLen]
        return pixelFlow

    def RearrangeDICOM(self, pixelFlow):
        # rearrange the DICOM file so that the file can be accessed in patches and the top and bottom strips are removed as they are not used here.
        tempAll = []
        tempRow = []
        tempPatch = []
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                for k in range(self.patchLen):
                    tempPatch.extend(pixelFlow[i * self.patchLen + k][j * self.patchLen : (j + 1) * self.patchLen])
                tempRow.append(tempPatch)
                tempPatch = []
            tempAll.append(tempRow)
            tempRow = []
        return tempAll

    def RearrangeBIN(self, pixelFlow):
        # rearrange the binary data so that the data are arranged in the order of patched

        # firstly section the binary data into DICOM fashioned order
        sectioned = [[]for i in range((self.nrOfRows + 2) * self.patchLen)]

        for i in range ((self.nrOfRows+2) * self.patchLen):
            sectioned[i].extend(pixelFlow[self.nrOfColumns * self.patchLen * i : self.nrOfColumns * self.patchLen * (i + 1)] )
        # remove the head and the tail strips which are not used in this evaluation
        sectioned = sectioned[self.patchLen : -self.patchLen]
        tempAll = []
        tempRow = []
        tempPatch = []
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                for k in range(self.patchLen):
                    tempPatch.extend(sectioned[i * self.patchLen + k][j * self.patchLen : (j + 1) * self.patchLen])
                tempRow.append(tempPatch)
                tempPatch = []
            tempAll.append(tempRow)
            tempRow = []
        return sectioned, tempAll

    def CalculateError(self, cal, ref):
        # compare the calculated and reference files, and return the error
        errorAll = []
        errorRow = []

        for row_cal, row_ref in zip(cal, ref):
            for pixel_cal, pixel_ref in zip(row_cal, row_ref):
                errorRow.append(pixel_cal - pixel_ref)
            errorAll.append(errorRow)
            errorRow = []
        return errorAll

    def CalculateNormalizedError(self, cal, ref):
        # compare the calculated and reference files, and return the normalized error
        delta = 0.0001 # to avoid dividing zero
        errorAllNormalized = []
        errorRow = []
        for row_cal, row_ref in zip(cal, ref):
            for pixel_cal, pixel_ref in zip(row_cal, row_ref):
                errorRow.append((pixel_cal - pixel_ref) / (pixel_ref + delta))
            errorAllNormalized.append(errorRow)
            errorRow = []
        return errorAllNormalized

    def EstimatePatch(self, dataInPatch, patchValueMethod):
        # estimate the value that can represent a patch. It can be mean or median value, and the deviation could also be provided for further evaluation.
        # some statistics test like normality test could be applied to decide which value to take. But considering there are many patches, how to synchronise is also a question.
        # currently the solution is, to open one new window when the 'process' button is pressed, on which the histograms of the patches will be shown. Whether to choose mean value
        # or median value to represent a patch is up to the user.
        temp = [[]for i in range(self.nrOfRows) ]
        if patchValueMethod == 'MEAN':
            for i in range(self.nrOfRows):
                for j in range (self.nrOfColumns):
                    temp[i].append(numpy.mean(dataInPatch[i][j]))
        if patchValueMethod == 'MEDIAN':
            for i in range(self.nrOfRows):
                for j in range (self.nrOfColumns):
                    temp[i].append(numpy.median(dataInPatch[i][j]))
        return temp

    def FittingLinearModel(self, calculatedPatchValue):
        # fitting the linear model, i.e. Ktrans_ref, Ve_ref, Ktrans_cal(Ve_cal). So that the parameter dependency could be seen
        # the fitting algorithm relies on the paper 'least squares fitting of data', David Eberly, Geometric tools, LLC
        # assume x, y, z denote Ktrans_ref, Ve_ref and Ktrans_cal(Ve_cal) respectively.
        x = []
        y = []
        z = []
        xx = []
        yy = []
        xy = []
        xz = []
        yz = []

        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                xCurrent = self.Ktrans_ref[i][j][0]
                yCurrent = self.Ve_ref[i][j][0]
                zCurrent = calculatedPatchValue[i][j]
                x.append(xCurrent)
                y.append(yCurrent)
                z.append(zCurrent)
                xx.append(xCurrent**2)
                yy.append(yCurrent**2)
                xy.append(xCurrent * yCurrent)
                xz.append(xCurrent * zCurrent)
                yz.append(yCurrent * zCurrent)
        left = numpy.matrix([[numpy.sum(xx), numpy.sum(xy), numpy.sum(x)], [numpy.sum(xy), numpy.sum(yy), numpy.sum(y)], [numpy.sum(x), numpy.sum(y), self.nrOfRows * self.nrOfColumns]])
        right = numpy.matrix([[numpy.sum(xz)], [numpy.sum(yz)], [numpy.sum(z)]])

        [a, b ,c] = numpy.squeeze(numpy.array( numpy.linalg.inv(left) * right ))
        return a, b, c

    def func_for_log_calculation(self,x, a, b):
        # assistant function for calculating logarithmic model fitting
        return a + b * numpy.log10(x)

    def FittingLogarithmicModel_K(self, calculated, reference):
        # fit the calculated Ktrans with reference data in logarithmic model
        temp_a = []
        temp_b = []

        for j in range(self.nrOfColumns):
            popt, pcov = optimize.curve_fit(self.func_for_log_calculation, zip(*reference)[j], zip(*calculated)[j])
            temp_a.append(popt[0])
            temp_b.append(popt[1])

        return temp_a, temp_b

    def FittingLogarithmicModel_V(self, calculated, reference):
        # fit the calculated Ve with reference data in logarithmic model
        temp_a = []
        temp_b = []

        for i in range(self.nrOfRows):
            popt, pcov = optimize.curve_fit(self.func_for_log_calculation, reference[i], calculated[i])
            temp_a.append(popt[0])
            temp_b.append(popt[1])

        return temp_a, temp_b

    def CalCorrMatrix(self, calculatedPatchValue, referencePatchValue):
        # calculate the correlation matrix of the calculated and reference DICOMs
        return numpy.corrcoef(calculatedPatchValue, referencePatchValue)

    def CalCovMatrix(self, calculatedPatchValue, referencePatchValue):
        # calculate the covariance matrix of the calculated and reference DICOMs
        return  numpy.cov(calculatedPatchValue, referencePatchValue)

    def CalculateMean(self, inPatch):
        # calculate the mean value of each patch
        temp = [[]for i in range(self.nrOfRows) ]
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                temp[i].append(numpy.mean(inPatch[i][j]))
        return temp

    def CalculateMedian(self, inPatch):
        # calculate the median value of each patch
        temp = [[]for i in range(self.nrOfRows) ]
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                temp[i].append(numpy.median(inPatch[i][j]))
        return temp

    def CalculateSTDDeviation(self, inPatch):
        # calculate the std deviation of each patch
        temp = [[]for i in range(self.nrOfRows) ]
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                temp[i].append(numpy.std(inPatch[i][j]))
        return temp

    def Calculate1stAnd3rdQuartile(self, inPatch):
        # calculate the 1st and 3rd quartile of each patch
        temp1stQuartile = [[]for i in range(self.nrOfRows) ]
        temp3rdQuartile = [[]for i in range(self.nrOfRows) ]
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                temp1stQuartile[i].append(stats.mstats.mquantiles(inPatch[i][j],prob = 0.25))
                temp3rdQuartile[i].append(stats.mstats.mquantiles(inPatch[i][j],prob = 0.75))
        return temp1stQuartile, temp3rdQuartile

    def CalculateMinAndMax(self, inPatch):
        # calculated the min. and max value of each patch
        tempMin = [[]for i in range(self.nrOfRows) ]
        tempMax = [[]for i in range(self.nrOfRows) ]
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                tempMin[i].append(numpy.min(inPatch[i][j]))
                tempMax[i].append(numpy.max(inPatch[i][j]))
        return tempMin, tempMax

    def T_Test_1samp(self, dataToBeTested, expectedMean):
        # do 1 sample t-test
        temp_t = [[]for i in range(self.nrOfRows) ]
        temp_p = [[]for i in range(self.nrOfRows) ]
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                temp_t[i].append(stats.ttest_1samp(dataToBeTested[i][j], expectedMean[i][j])[0])
                temp_p[i].append(stats.ttest_1samp(dataToBeTested[i][j], expectedMean[i][j])[1])
        return temp_t, temp_p

    def U_Test(self, dataToBeTested, referenceData):
        # do Mann-Whitney U test
        temp_u = [[]for i in range(self.nrOfRows) ]
        temp_p = [[]for i in range(self.nrOfRows) ]
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                temp_u[i].append(stats.mannwhitneyu(dataToBeTested[i][j], referenceData[i][j])[0])
                temp_p[i].append(stats.mannwhitneyu(dataToBeTested[i][j], referenceData[i][j])[1])
        return temp_u, temp_p

    def ANOVA_oneway_K(self, inPatch_K):
        # do ANOVA for each row of calculated Ktrans, to see if there is significant difference with regarding to Ve
        tempf = []
        tempp = []
        for i in range(self.nrOfRows):
            tempf.append(stats.f_oneway(inPatch_K[i][0], inPatch_K[i][1], inPatch_K[i][2], inPatch_K[i][3], inPatch_K[i][4])[0])
            tempp.append(stats.f_oneway(inPatch_K[i][0], inPatch_K[i][1], inPatch_K[i][2], inPatch_K[i][3], inPatch_K[i][4])[1])
        return tempf, tempp

    def ANOVA_oneway_V(self, inPatch_V):
        # do ANOVA for each column of calculated Ve, to see if there is significant difference with regarding to Ktrans
        tempf = []
        tempp = []
        for j in range(self.nrOfColumns):
            tempf.append(stats.f_oneway(zip(*inPatch_V)[j][0], zip(*inPatch_V)[j][1], zip(*inPatch_V)[j][2], zip(*inPatch_V)[j][3], zip(*inPatch_V)[j][4], zip(*inPatch_V)[j][5])[0])
            tempp.append(stats.f_oneway(zip(*inPatch_V)[j][0], zip(*inPatch_V)[j][1], zip(*inPatch_V)[j][2], zip(*inPatch_V)[j][3], zip(*inPatch_V)[j][4], zip(*inPatch_V)[j][5])[1])

        return tempf, tempp

    def Score(self):
        # give a score for evaluation according to the weighting factors.
        pass

class MySplashScreen(wx.SplashScreen):
    '''
    show the splash screen when the application is launched.
    '''
    def  __init__(self, parent=None):
        # This is a recipe to a the screen.
        # Modify the following variables as necessary.

        # aBitmap = wx.Image(name = os.path.join(os.path.dirname(sys.argv[0]), 'splashImage_small.jpg')).ConvertToBitmap()
        aBitmap = wx.Image(name = os.path.join(os.getcwd(), 'splashImage_small.jpg')).ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 2000 # milliseconds
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle, splashDuration, parent)



if __name__ == "__main__":
    # show the application's main window

    Application = wx.App()
    QIBASplashWindow = MySplashScreen()
    QIBASplashWindow.Show()

    time.sleep(2)
    window = MainWindow(None)
    window.Show()
    window.Maximize(True)
    Application.MainLoop()

