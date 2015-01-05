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
from sys import argv, exit
import wx
import wx.html
import numpy
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.ticker as ticker
import time
import subprocess

import QIBA_functions
import QIBA_model

class MainWindow(wx.Frame):
    '''
    this is the parent class of the main window of the application.
    '''

    def __init__(self, parent, applicationName):
        wx.Frame.__init__(self, parent, title = applicationName, size = (wx.SYS_SCREEN_X, wx.SYS_SCREEN_Y))

        self.nrOfRow = 0
        self.nrOfColumn = 0
        self.WARNINGTEXT = False

        self.CenterOnScreen()

        self.CreateStatusBar()
        self.SetStatusText("Welcome to " + applicationName + "!")


        # scatter plot switch
        self.SCATTER_SWITCH = True

        self.SetupMenubar()

        self.SetupLayoutMain()

    def SetupEditMenu(self):
        pass

    def OnRightClick(self, event):
        pass

    def SetupMenubar(self):
        '''
        set up the menu bar
        '''
        self.menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        OnExport = fileMenu.Append(wx.ID_ANY, "&Export the results...\tCtrl+E", "Export the result as PDF/EXCEL file.")
        fileMenu.AppendSeparator()
        OnExit = fileMenu.Append(wx.ID_ANY, "&Quit\tCtrl+Q", "Quit")

        # self.SetupEditMenu()

        aboutMenu = wx.Menu()
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

        self.menubar.Bind(wx.EVT_MENU, self.OnExport, OnExport)
        self.menubar.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        self.menubar.Bind(wx.EVT_MENU, self.OnAbout, OnAboutApp)

        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(aboutMenu, "&About")
        self.SetMenuBar(self.menubar)

    def OnEditImageDimension(self, event):
        # edit the dimension of the images
        self.dlg = wx.Dialog(self, title = 'Edit the dimension of the image...')

        self.sizer0 = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.text1 = wx.StaticText(self.dlg, label="number of the rows:")
        self.textCtrl1 = wx.TextCtrl(self.dlg, -1, str(self.nrOfRow))
        self.sizer1.Add(self.text1, 0)
        self.sizer1.Add(self.textCtrl1, 1)

        self.text2 = wx.StaticText(self.dlg, label="number of the columns:")
        self.textCtrl2 = wx.TextCtrl(self.dlg, -1, str(self.nrOfColumn))
        self.sizer2.Add(self.text2, 0)
        self.sizer2.Add(self.textCtrl2, 1)

        self.buttonOK = wx.Button(self.dlg, label = 'Ok')
        self.buttonOK.Bind(wx.EVT_BUTTON, self.OnEditDimension_OK)
        self.sizer0.Add(self.sizer1, 1)
        self.sizer0.Add(self.sizer2, 1)
        self.sizer0.Add(self.buttonOK, 1)
        self.sizer0.Fit(self.dlg)
        self.dlg.SetSizer(self.sizer0)

        self.dlg.Center()
        self.WARNINGTEXT = False

        self.dlg.ShowModal()

    def OnEditDimension_OK(self, event):
        # when the OK is clicked in the dimension edit dialog

        if (QIBA_functions.IsPositiveInteger(self.textCtrl1.GetValue()) and QIBA_functions.IsPositiveInteger(self.textCtrl2.GetValue()) ):
            self.SetStatusText('Image dimension is set successfully!')
            self.nrOfRow = int(self.textCtrl1.GetValue())
            self.nrOfColumn = int(self.textCtrl2.GetValue())
            self.dlg.Destroy()
        else:
            self.SetStatusText('Image dimension is not set correctly!')
            if self.WARNINGTEXT == False:
                self.textWarning = wx.StaticText(self.dlg, label="Please input a proper integer!")
                self.sizer0.Insert(2, self.textWarning)
                self.sizer0.Fit(self.dlg)
                self.dlg.SetSizer(self.sizer0)
                self.WARNINGTEXT = True
                self.dlg.Update()
            return


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

    def SetupRightClickMenu(self):
        pass

    def SetupPage_Histogram(self):
        pass

    def ClearPage_Histogram(self):
        pass

    def SetupLeft(self):
        '''
        set up the left panel.
        show the directories and files list to load calculated DICOMs
        '''
        self.selectedFilePath = ''
        # setup the tree control widget for file viewing and selection

        self.fileBrowser = wx.GenericDirCtrl(self.leftPanel, -1, dir = os.path.join(os.getcwd(), 'calculated_data'), style=wx.DIRCTRL_SHOW_FILTERS,
                                             # filter="DICOM files (*.dcm)|*.dcm|Binary files (*.bin *.raw )|*.bin;*.raw|TIFF (*.tif)|*.tif")
                                             filter="Supported files (*.dcm *.bin *.raw *.tif)|*.dcm;*.bin;*.raw;*.tif")

        # self.Bind(wx.EVT_TREE_SEL_CHANGED, self.GetFilePath)

        # setup the right click function
        self.SetupRightClickMenu()

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
        self.canvasScatter = FigureCanvas(self.pageScatter, -1, self.figureScatter)
        self.buttonSwitch = wx.Button(self.pageScatter, -1, label = 'Switch viewing', size = (90, 30))
        self.buttonSwitch.Bind(wx.EVT_BUTTON, self.OnSwitchViewing)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvasScatter, 1, wx.EXPAND)
        sizer.Add(self.buttonSwitch, 0, wx.EXPAND)
        self.pageScatter.SetSizer(sizer)

        # page histogram
        self.SetupPage_Histogram()

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

    def OnSwitchViewing(self, event):
        # switch the viewing in scatter plot page
        self.SetStatusText("Rearranging the scatter plot...")
        self.SCATTER_SWITCH = not self.SCATTER_SWITCH
        self.buttonSwitch.Disable()
        self.DrawScatter()
        self.buttonSwitch.Enable()
        self.SetStatusText("Rearranging the scatter plot finished.")

    def ClearInterface(self):
        # clear the plots in the interface, so that when the evaluated models are cleared, the interface will also be cleaned.
        self.figureImagePreview.clear()
        self.canvasImagePreview.draw()

        self.figureScatter.clear()
        self.canvasScatter.draw()

        self.ClearPage_Histogram()

        self.figureBoxPlot.clear()
        self.canvasBoxPlot.draw()

        self.statisticsViewer.SetPage('')
        self.covCorrViewer.SetPage('')
        self.modelFittingViewer.SetPage('')
        self.t_testViewer.SetPage('')
        self.U_testViewer.SetPage('')
        self.ANOVAViewer.SetPage('')

    def DrawMaps(self):
        pass

    def DrawScatter(self):
        pass

    def PlotPreview(self, dataList, titleList, colorMapList, unitList):
        # show calculated images and the error images
        nrOfSubFigRows = len(dataList)
        nrOfSubFigColumns = len(dataList[0])
        # subplot = [[] for i in range(nrOfSubFigRows)]

        for i in range(nrOfSubFigRows):
            for j in range(nrOfSubFigColumns):
                subplot = self.figureImagePreview.add_subplot(nrOfSubFigRows, nrOfSubFigColumns, i * nrOfSubFigColumns + j + 1)
                handler = subplot.imshow(dataList[i][j], cmap = colorMapList[i][j], interpolation='nearest')
                divider = make_axes_locatable(subplot.get_figure().gca()) # for tight up the color bar
                cax = divider.append_axes("right", "5%", pad="3%")
                subplot.get_figure().colorbar(handler, cax = cax).set_label(unitList[i][j]) # show color bar and the label
                subplot.set_title(titleList[i][j])

        self.figureImagePreview.tight_layout()
        self.canvasImagePreview.draw()

    def PlotScatter(self, dataList, refDataList, xLabelList, yLabelList, titleList, xLim, yLim):
        '''
        the scatter plots to show the distribution of the calculated values
        '''
        nrOfSubFigRows = len(dataList)
        nrOfSubFigColumns = len(dataList[0])
        self.figureScatter.clear()

        for i in range(nrOfSubFigRows):
            for j in range(nrOfSubFigColumns):
                subPlot = self.figureScatter.add_subplot(nrOfSubFigRows, nrOfSubFigColumns, i * nrOfSubFigColumns + j + 1)
                subPlot.scatter(refDataList[i][j], dataList[i][j], color = 'b', alpha = 0.25, label = 'calculated value')
                subPlot.scatter(refDataList[i][j], refDataList[i][j], color = 'g', alpha = 0.25, label = 'reference value')
                subPlot.legend(loc = 'upper left')
                subPlot.set_xlim(xLim[i])
                subPlot.set_ylim(yLim[i])
                subPlot.set_xlabel(xLabelList[i][j])
                subPlot.set_ylabel(yLabelList[i][j])
                subPlot.set_title(titleList[i][j])

        self.figureScatter.tight_layout()
        self.canvasScatter.draw()

    def DrawHistograms(self):
        pass

    def DrawBoxPlot(self):
        pass


    def OnEvaluate(self, event):
        # start to evaluate

        # check the image dimension parameter validation
        if self.WARNINGTEXT:
            self.SetStatusText('Please input correct dimension of the image!')
            return

        # clear the interface if they were used before
        self.ClearInterface()

        # disable some widgets
        self.buttonEvaluate.Disable()
        self.buttonExport.Disable()

        # status bar
        self.SetStatusText('Evaluating...')
        #EvaluateProgressDialog.Update(5)

        # create new model object to evaluated on
        self.GenerateModel()
        #EvaluateProgressDialog.Update(10)

        # call the method to execute evaluation
        try:
            self.newModel.Evaluate()
        except RuntimeError:
            self.SetStatusText('RuntimeError occurs. Evaluation terminated.')
            return False

        #EvaluateProgressDialog.Update(20)

        # show the results in the main window
        self.ShowResults()

        # status bar
        self.SetStatusText('Evaluation finished.')
        #EvaluateProgressDialog.Update(100)
        #EvaluateProgressDialog.Destroy()

        # enable some widgets
        self.buttonEvaluate.Enable()
        self.buttonExport.Enable()

    def GenerateModel(self):
        pass

    def ShowResults(self):
        # show the results in the main window
        self.statisticsViewer.SetPage(self.newModel.GetStatisticsInHTML())
        self.covCorrViewer.SetPage(self.newModel.GetCovarianceCorrelationInHTML())
        self.modelFittingViewer.SetPage(self.newModel.GetModelFittingInHTML())
        self.t_testViewer.SetPage(self.newModel.GetT_TestResultsInHTML())
        self.U_testViewer.SetPage(self.newModel.GetU_TestResultsInHTML())
        self.ANOVAViewer.SetPage(self.newModel.GetANOVAResultsInHTML())
        #EvaluateProgressDialog.Update(25)

        #EvaluateProgressDialog.Update(30)

        # draw the figures
        self.DrawMaps()
        #EvaluateProgressDialog.Update(35)
        self.DrawScatter()
        #EvaluateProgressDialog.Update(50)
        self.DrawHistograms()
        #EvaluateProgressDialog.Update(90)
        self.DrawBoxPlot()
        #EvaluateProgressDialog.Update(95)

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
        folderPath = os.path.join(os.getcwd(), 'temp')
        for theFile in os.listdir(folderPath):
            os.remove(os.path.join(folderPath, theFile))

        # show in status bar when export finishes
        self.SetStatusText('Results exported as PDF file.')

        # enable some widgets
        self.buttonEvaluate.Enable()
        self.buttonExport.Enable()

    def GetResultInHtml(self):
        # render the figures, tables into html, for exporting to pdf
        pass

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

class MainWindow_KV(MainWindow):
    '''
    this is the Ktrans-Ve branch's interface.
    '''
    def __init__(self, appName):
        # instance of the main window
        MainWindow.__init__(self, None, appName)

        self.nrOfRow = 6
        self.nrOfColumn = 5
        self.WARNINGTEXT = False

        # default files' paths
        self.path_ref_K = os.path.join(os.getcwd(), 'reference_data', 'Ktrans.dcm')
        self.path_ref_V = os.path.join(os.getcwd(), 'reference_data', 'Ve.dcm')
        self.path_cal_K = ''
        self.path_cal_V = ''

        # customize the main window
        self.SetupEditMenu()
        self.SetupRightClickMenu()
        self.SetupPage_Histogram()

    def SetupEditMenu(self):
        # setup the edit menu in the menu bar
        editMenu = wx.Menu()

        OnEditImageDimension = editMenu.Append(wx.ID_ANY, 'Eidt the dimension of the images...')
        editMenu.AppendSeparator()
        OnLoadRef_K = editMenu.Append(wx.ID_ANY, 'Load reference Ktrans...')
        OnLoadRef_V = editMenu.Append(wx.ID_ANY, 'Load reference Ve...')
        self.menubar.Bind(wx.EVT_MENU, self.OnEditImageDimension, OnEditImageDimension)
        self.menubar.Bind(wx.EVT_MENU, self.OnLoadRef_K, OnLoadRef_K)
        self.menubar.Bind(wx.EVT_MENU, self.OnLoadRef_V, OnLoadRef_V)
        self.menubar.Insert(1,editMenu, "&Edit")
        self.SetMenuBar(self.menubar)

    def SetupRightClickMenu(self):
        # setup the popup menu on right click
        wx.EVT_RIGHT_DOWN(self.fileBrowser.GetTreeCtrl(), self.OnRightClick)
        self.popupMenu = wx.Menu()
        self.ID_POPUP_LOAD_CAL_K = wx.NewId()
        self.ID_POPUP_LOAD_CAL_V = wx.NewId()

        OnLoadCal_K = wx.MenuItem(self.popupMenu, self.ID_POPUP_LOAD_CAL_K, 'Load as calculated Ktrans')
        OnLoadCal_V = wx.MenuItem(self.popupMenu, self.ID_POPUP_LOAD_CAL_V, 'Load as calculated Ve')
        self.popupMenu.AppendItem(OnLoadCal_K)
        self.popupMenu.AppendItem(OnLoadCal_V)

    def SetupPage_Histogram(self):
        # setup the histogram page
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

    def ClearPage_Histogram(self):
        # clear the histogram page
        self.figureHist_Ktrans.clear()
        self.canvasHist_Ktrans.draw()
        self.figureHist_Ve.clear()
        self.canvasHist_Ve.draw()

    def GenerateModel(self):
        # generate the model for evaluation
        try:
            self.newModel = QIBA_model.Model_KV(self.path_ref_K, self.path_ref_V, self.path_cal_K, self.path_cal_V, [self.nrOfRow, self.nrOfColumn])
        except:
            self.SetStatusText('Error occours. New evaluation object wasn\'t generated successfully.')

    def OnRightClick(self, event):
        # the right click action on the file list
        if (str(os.path.splitext(self.fileBrowser.GetPath())[1]) in ['.dcm', '.bin', '.raw', '.tif']):
            wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_CAL_K, self.OnLoadCal_K)
            wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_CAL_V, self.OnLoadCal_V)
            self.PopupMenu(self.popupMenu, event.GetPosition())
        else:
            self.SetStatusText('Invalid file or path chosen.')

    def OnLoadCal_K(self, event):
        # pass the file path for loading
        self.path_cal_K = self.fileBrowser.GetPath()
        self.SetStatusText('Calculated Ktrans loaded.')
        if self.path_cal_V:
            self.buttonEvaluate.Enable()

    def OnLoadCal_V(self, event):
        # pass the file path for loading
        self.path_cal_V = self.fileBrowser.GetPath()
        self.SetStatusText('Calculated Ve loaded.')
        if self.path_cal_K:
            self.buttonEvaluate.Enable()

    def OnLoadRef_K(self, event):
        # pass the file path for loading
        dlg = wx.FileDialog(self, 'Load reference Ktrans...', '', '', "Supported files (*.dcm *.bin *.raw *.tif)|*.dcm;*.bin;*.raw;*.tif", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_ref_K = dlg.GetPath()
            self.SetStatusText('Reference Ktrans loaded.')
        else:
            self.SetStatusText('Reference Ktrans was NOT loaded!')

    def OnLoadRef_V(self, event):
        # pass the file path for loading
        dlg = wx.FileDialog(self, 'Load reference Ktrans...', '', '', "Supported files (*.dcm *.bin *.raw *.tif)|*.dcm;*.bin;*.raw;*.tif", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_ref_V = dlg.GetPath()
            self.SetStatusText('Reference Ve loaded.')
        else:
            self.SetStatusText('Reference Ve was NOT loaded!')

    def DrawHistograms(self):
        # draw histograms of imported calculated Ktrans and Ve maps, so that the user can have a look of the distribution of each patch.

        pixelCountInPatch = self.newModel.patchLen ** 2
        nrOfBins = 10

        self.figureHist_Ktrans.suptitle('The histogram of the calculated Ktrans',) # fontsize = 18)
        self.figureHist_Ve.suptitle('The histogram of the calculated Ve') # , fontsize = 18)

        for i in range(self.newModel.nrOfRows):
            for j in range(self.newModel.nrOfColumns):
                subPlot_K = self.figureHist_Ktrans.add_subplot(self.newModel.nrOfRows, self.newModel.nrOfColumns, i * self.newModel.nrOfColumns + j + 1)
                # subPlot_K.clear()
                subPlot_K.hist(self.newModel.Ktrans_cal[i][j], nrOfBins)
                minPatch_K = numpy.min(self.newModel.Ktrans_cal[i][j])
                maxPatch_K = numpy.max(self.newModel.Ktrans_cal[i][j])
                meanPatch_K = numpy.mean(self.newModel.Ktrans_cal[i][j])

                minPatch_K = QIBA_functions.formatFloatTo2DigitsString(minPatch_K)
                maxPatch_K = QIBA_functions.formatFloatTo2DigitsString(maxPatch_K)
                meanPatch_K = QIBA_functions.formatFloatTo2DigitsString(meanPatch_K)

                subPlot_K.set_xticks([float(minPatch_K), float(maxPatch_K)])

                subPlot_K.set_xticklabels([minPatch_K, maxPatch_K])
                subPlot_K.axvline(float(meanPatch_K), color = 'r', linestyle = 'dashed', linewidth = 1) # draw a vertical line at the mean value
                subPlot_K.set_ylim([0, pixelCountInPatch])
                subPlot_K.text(float(meanPatch_K) + 0.01 * float(meanPatch_K), 0.9 * pixelCountInPatch, meanPatch_K, size = 'x-small') # parameters: location_x, location_y, text, size
                if i == 0:
                    subPlot_K.set_xlabel(self.newModel.headersHorizontal[j])
                    subPlot_K.xaxis.set_label_position('top')
                if j == 0:
                    subPlot_K.set_ylabel(self.newModel.headersVertical[i])

                subPlot_V = self.figureHist_Ve.add_subplot(self.newModel.nrOfRows, self.newModel.nrOfColumns, i * self.newModel.nrOfColumns + j + 1 )
                # subPlot_V.clear()
                subPlot_V.hist(self.newModel.Ve_cal[i][j], nrOfBins)
                minPatch_V = numpy.min(self.newModel.Ve_cal[i][j])
                maxPatch_V = numpy.max(self.newModel.Ve_cal[i][j])
                meanPatch_V = numpy.mean(self.newModel.Ve_cal[i][j])
                minPatch_V = QIBA_functions.formatFloatTo2DigitsString(minPatch_V)
                maxPatch_V = QIBA_functions.formatFloatTo2DigitsString(maxPatch_V)
                meanPatch_V = QIBA_functions.formatFloatTo2DigitsString(meanPatch_V)

                subPlot_V.set_xticks([float(minPatch_V), float(maxPatch_V)])
                subPlot_V.set_xticklabels([minPatch_V, maxPatch_V])
                subPlot_V.axvline(float(meanPatch_V), color = 'r', linestyle = 'dashed', linewidth = 1) # draw a vertical line at the mean value
                subPlot_V.set_ylim([0, pixelCountInPatch])
                subPlot_V.text(float(meanPatch_V) + 0.01 * float(meanPatch_V), 0.9 * pixelCountInPatch, meanPatch_V, size = 'x-small') # parameters: location_x, location_y, text, size
                if i == 0:
                    subPlot_V.set_xlabel(self.newModel.headersHorizontal[j])
                    subPlot_V.xaxis.set_label_position('top')
                if j == 0:
                    subPlot_V.set_ylabel(self.newModel.headersVertical[i])


        self.figureHist_Ve.tight_layout()
        self.figureHist_Ktrans.tight_layout()

        self.figureHist_Ktrans.subplots_adjust(top = 0.94, right = 0.95)
        self.figureHist_Ve.subplots_adjust(top = 0.94, right = 0.95)

        self.canvasHist_Ktrans.draw()
        self.canvasHist_Ve.draw()

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

    def DrawMaps(self):
        # draw the maps of the preview and error
        self.PlotPreview([[self.newModel.Ktrans_cal_inRow, self.newModel.Ktrans_error, self.newModel.Ktrans_error_normalized],
                                  [self.newModel.Ve_cal_inRow, self.newModel.Ve_error, self.newModel.Ve_error_normalized]],

                                [['Calculated Ktrans', 'Error map of Ktrans', 'Normalized Error map of Ktrans'],
                                 ['Calculated Ve', 'Error map of Ve', 'Normalized Error map of Ve']],

                                [['bone', 'rainbow', 'rainbow'], ['bone', 'rainbow', 'rainbow']],

                                [['Ktrans[1/min]', 'Delta Ktrans[1/min.]', 'Normalized error[1]'], ['Ve[]', 'Delta Ve[]', 'Normalized error[1]']])

    def DrawScatter(self):
        # draw the scatters
        if self.SCATTER_SWITCH:
            minLim_x_K = numpy.min(self.newModel.Ktrans_ref_inRow)
            maxLim_x_K = numpy.max(self.newModel.Ktrans_ref_inRow)
            minLim_y_K = numpy.min( [numpy.min(self.newModel.Ktrans_ref_inRow), numpy.min(self.newModel.Ktrans_cal_inRow)])
            maxLim_y_K = numpy.max( [numpy.max(self.newModel.Ktrans_ref_inRow), numpy.max(self.newModel.Ktrans_cal_inRow)])

            minLim_x_V = numpy.min(self.newModel.Ve_ref_inRow)
            maxLim_x_V = numpy.max(self.newModel.Ve_ref_inRow)
            minLim_y_V = numpy.min( [numpy.min(self.newModel.Ve_ref_inRow), numpy.min(self.newModel.Ve_cal_inRow)])
            maxLim_y_V = numpy.max( [numpy.max(self.newModel.Ve_ref_inRow), numpy.max(self.newModel.Ve_cal_inRow)])
        else:
            minLim_x_K = numpy.min(self.newModel.Ktrans_ref_patchValue)
            maxLim_x_K = numpy.max(self.newModel.Ktrans_ref_patchValue)
            minLim_y_K = numpy.min( [numpy.min(self.newModel.Ktrans_ref_patchValue), numpy.min(self.newModel.Ktrans_cal_patchValue)])
            maxLim_y_K = numpy.max( [numpy.max(self.newModel.Ktrans_ref_patchValue), numpy.max(self.newModel.Ktrans_cal_patchValue)])

            minLim_x_V = numpy.min(self.newModel.Ve_ref_patchValue)
            maxLim_x_V = numpy.max(self.newModel.Ve_ref_patchValue)
            minLim_y_V = numpy.min( [numpy.min(self.newModel.Ve_ref_patchValue), numpy.min(self.newModel.Ve_cal_patchValue)])
            maxLim_y_V = numpy.max( [numpy.max(self.newModel.Ve_ref_patchValue), numpy.max(self.newModel.Ve_cal_patchValue)])
        spacing_x_K = (maxLim_x_K - minLim_x_K) * 0.05
        spacing_y_K = (maxLim_y_K - minLim_y_K) * 0.05

        spacing_x_V = (maxLim_x_V - minLim_x_V) * 0.05
        spacing_y_V = (maxLim_y_V - minLim_y_V) * 0.05
        self.PlotScatter([[self.newModel.Ktrans_cal], [self.newModel.Ve_cal]],

                            [[self.newModel.Ktrans_ref], [self.newModel.Ve_ref]],

                            [['Reference Ktrans'], ['Reference Ve']],

                            [['Calculated Ktrans'], ['Calculated Ve']],

                            [['Distribution plot of Ktrans'], ['Distribution plot of Ve']],

                            [[minLim_x_K - spacing_x_K, maxLim_x_K + spacing_x_K], [minLim_x_V - spacing_x_V, maxLim_x_V + spacing_x_V]],

                            [[minLim_y_K - spacing_y_K, maxLim_y_K + 2*spacing_y_K], [minLim_y_V - spacing_y_V, maxLim_y_V + 2*spacing_y_V]])

    def GetResultInHtml(self):
        # render the figures, tables into html, for exporting to pdf
        htmlContent = ''
        self.figureImagePreview.savefig(os.path.join(os.getcwd(), 'temp', 'figureImages.png'))
        self.figureScatter.savefig(os.path.join(os.getcwd(), 'temp', 'figureScatters.png'))
        self.figureHist_Ktrans.savefig(os.path.join(os.getcwd(), 'temp', 'figureHist_K.png'))
        self.figureHist_Ve.savefig(os.path.join(os.getcwd(), 'temp', 'figureHist_V.png'))
        self.figureBoxPlot.savefig(os.path.join(os.getcwd(), 'temp', 'figureBoxPlots.png'))

        htmlContent += self.newModel.packInHtml('<h1 align="center">QIBA DRO Evaluation Tool Results Report<br>(Ktrans-Ve)</h1>')

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

class MainWindow_T1(MainWindow):
    '''
    this is the Ktrans-Ve branch's interface.
    '''
    def __init__(self, appName):
        MainWindow.__init__(self, None, appName)

        self.nrOfRow = 6
        self.nrOfColumn = 15
        self.WARNINGTEXT = False

        # default files' paths
        self.path_ref_T1 = os.path.join(os.getcwd(), 'reference_data', 'T1.dcm')
        self.path_cal_T1 = ''


        # customize the main window
        self.SetupEditMenu()
        self.SetupRightClickMenu()
        self.SetupPage_Histogram()

    def SetupEditMenu(self):
        # setup the edit menu in the menu bar
        editMenu = wx.Menu()

        OnEditImageDimension = editMenu.Append(wx.ID_ANY, 'Edit the dimension of the images...')
        editMenu.AppendSeparator()
        OnLoadRef_T1 = editMenu.Append(wx.ID_ANY, 'Load reference T1...')
        self.menubar.Bind(wx.EVT_MENU, self.OnEditImageDimension, OnEditImageDimension)
        self.menubar.Bind(wx.EVT_MENU, self.OnLoadRef_T1, OnLoadRef_T1)
        self.menubar.Insert(1,editMenu, "&Edit")
        self.SetMenuBar(self.menubar)

    def SetupRightClickMenu(self):
        # setup the popup menu on right click
        wx.EVT_RIGHT_DOWN(self.fileBrowser.GetTreeCtrl(), self.OnRightClick)
        self.popupMenu = wx.Menu()
        self.ID_POPUP_LOAD_CAL_T1 = wx.NewId()

        OnLoadCal_T1 = wx.MenuItem(self.popupMenu, self.ID_POPUP_LOAD_CAL_T1, 'Load as calculated T1')
        self.popupMenu.AppendItem(OnLoadCal_T1)

    def SetupPage_Histogram(self):
        # setup the histogram page

        self.figureHist_T1 = Figure()
        self.canvasHist_T1 = FigureCanvas(self.pageHistogram,-1, self.figureHist_T1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasHist_T1, 1, wx.EXPAND)
        self.pageHistogram.SetSizer(sizer)


    def ClearPage_Histogram(self):
        # clear the histogram page
        self.figureHist_T1.clear()
        self.canvasHist_T1.draw()

    def GenerateModel(self):
        # generate the model for evaluation
        try:
            self.newModel = QIBA_model.Model_T1(self.path_ref_T1, self.path_cal_T1, [self.nrOfRow, self.nrOfColumn])
        except:
            self.SetStatusText('Error occours. New evaluation object wasn\'t generated successfully.')

    def OnRightClick(self, event):
        # the right click action on the file list
        if (str(os.path.splitext(self.fileBrowser.GetPath())[1]) in ['.dcm', '.bin', '.raw', '.tif']):
            wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_CAL_T1, self.OnLoadCal_T1)
            self.PopupMenu(self.popupMenu, event.GetPosition())
        else:
            self.SetStatusText('Invalid file or path chosen.')

    def OnLoadCal_T1(self, event):
        # pass the file path for loading
        self.path_cal_T1 = self.fileBrowser.GetPath()
        self.SetStatusText('Calculated T1 loaded.')
        self.buttonEvaluate.Enable()

    def OnLoadRef_T1(self, event):
        # pass the file path for loading
        dlg = wx.FileDialog(self, 'Load reference T1...', '', '', "Supported files (*.dcm *.bin *.raw *.tif)|*.dcm;*.bin;*.raw;*.tif", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_ref_T1 = dlg.GetPath()
            self.SetStatusText('Reference T1 loaded.')
        else:
            self.SetStatusText('Reference T1 was NOT loaded!')


    def DrawHistograms(self):
        # draw histograms of imported calculated Ktrans and Ve maps, so that the user can have a look of the distribution of each patch.

        pixelCountInPatch = self.newModel.patchLen ** 2
        nrOfBins = 10

        self.figureHist_T1.suptitle('The histogram of the calculated T1',) # fontsize = 18)

        for i in range(self.newModel.nrOfRows):
            for j in range(self.newModel.nrOfColumns):
                subPlot_T1 = self.figureHist_T1.add_subplot(self.newModel.nrOfRows, self.newModel.nrOfColumns, i * self.newModel.nrOfColumns + j + 1)
                # subPlot_K.clear()
                subPlot_T1.hist(self.newModel.T1_cal[i][j], nrOfBins) # normed=True if want the bars to be normalized
                minPatch_T1 = numpy.min(self.newModel.T1_cal[i][j])
                maxPatch_T1 = numpy.max(self.newModel.T1_cal[i][j])
                meanPatch_T1 = numpy.mean(self.newModel.T1_cal[i][j])

                minPatch_T1 = QIBA_functions.formatFloatTo2DigitsString(minPatch_T1)
                maxPatch_T1 = QIBA_functions.formatFloatTo2DigitsString(maxPatch_T1)
                meanPatch_T1 = QIBA_functions.formatFloatTo2DigitsString(meanPatch_T1)

                subPlot_T1.set_xticks([float(minPatch_T1), float(maxPatch_T1)])

                subPlot_T1.set_xticklabels([minPatch_T1, maxPatch_T1])
                subPlot_T1.axvline(float(meanPatch_T1), color = 'r', linestyle = 'dashed', linewidth = 1) # draw a vertical line at the mean value
                subPlot_T1.set_ylim([0, pixelCountInPatch])
                subPlot_T1.text(float(meanPatch_T1), 0.9 * pixelCountInPatch, meanPatch_T1, size = 'x-small') # parameters: location_x, location_y, text, size
                if i == 0:
                    subPlot_T1.set_xlabel(self.newModel.headersHorizontal[j])
                    subPlot_T1.xaxis.set_label_position('top')
                if j == 0:
                    subPlot_T1.set_ylabel(self.newModel.headersVertical[i])

        self.figureHist_T1.tight_layout(pad=0.4, w_pad=0.1, h_pad=1.0)
        self.figureHist_T1.subplots_adjust(top = 0.94)
        self.canvasHist_T1.draw()


    def DrawBoxPlot(self):
        '''
        draw box plots of each patch
        '''

        subPlot_R1 = self.figureBoxPlot.add_subplot(1, 1, 1)
        subPlot_R1.clear()
        temp = []
        # referValue_R1 = []
        for j in range(self.newModel.nrOfColumns):
            temp.extend(zip(*self.newModel.R1_cal)[j])
            # referValue_R1.append(QIBA_functions.formatFloatTo2DigitsString(self.newModel.T1_ref[j][0][0]))
        subPlot_R1.boxplot(temp)

        # decorate R1 plot
        subPlot_R1.set_title('Box plot of R1 from calculated T1')
        subPlot_R1.set_xlabel('The result shows the R1 patches from calculated T1, concatenated in columns')
        subPlot_R1.set_ylabel('Calculated values in patches')

        subPlot_R1.xaxis.set_major_formatter(ticker.NullFormatter())
        # subPlot_R1.xaxis.set_minor_locator(ticker.FixedLocator([8, 23, 38, 53, 68, 83]))
        subPlot_R1.xaxis.set_minor_locator(ticker.FixedLocator([4, 10, 16, 22, 28, 34, 40, 46, 52, 58, 64, 70, 76, 82, 88]))
        subPlot_R1.xaxis.set_minor_formatter(ticker.FixedFormatter(self.newModel.headersHorizontal))
        for j in range(self.newModel.nrOfColumns):
            subPlot_R1.axvline(x = self.newModel.nrOfRows * j + 0.5, color = 'green', linestyle = 'dashed')

        self.figureBoxPlot.tight_layout()
        self.canvasBoxPlot.draw()
        self.rightPanel.Layout()

    def DrawMaps(self):
        # draw the maps of the preview and error
        self.PlotPreview([[self.newModel.T1_cal_inRow], [self.newModel.T1_error], [self.newModel.T1_error_normalized],],

                                [['Calculated T1'], ['Error map of T1'], ['Normalized Error map of T1'],],

                                [['bone'], ['rainbow'], ['rainbow'], ],

                                [['T1[ms]'], ['Delta T1[ms]'], ['Normalized error[1]'],])

    def DrawScatter(self):
        # draw the scatters
        if self.SCATTER_SWITCH:
            minLim_x = numpy.min(self.newModel.T1_ref_inRow)
            maxLim_x = numpy.max(self.newModel.T1_ref_inRow)
            minLim_y = numpy.min([numpy.min(self.newModel.T1_ref_inRow), numpy.min(self.newModel.T1_cal_inRow)])
            maxLim_y = numpy.max([numpy.max(self.newModel.T1_ref_inRow), numpy.max(self.newModel.T1_cal_inRow)])
        else:
            minLim_x = numpy.min(self.newModel.T1_ref_patchValue)
            maxLim_x = numpy.max(self.newModel.T1_ref_patchValue)
            minLim_y = numpy.min([numpy.min(self.newModel.T1_ref_patchValue), numpy.min(self.newModel.T1_cal_patchValue)])
            maxLim_y = numpy.max([numpy.max(self.newModel.T1_ref_patchValue), numpy.max(self.newModel.T1_cal_patchValue)])

        spacing_x = (maxLim_x - minLim_x) * 0.05
        spacing_y = (maxLim_y - minLim_y) * 0.05
        self.PlotScatter([[self.newModel.T1_cal],],

                            [[self.newModel.T1_ref],],

                            [['Reference T1'],],

                            [['Calculated T1'],],

                            [['Distribution plot of T1'],],

                            [[minLim_x - spacing_x, maxLim_x + spacing_x],],

                            [[minLim_y - spacing_y, maxLim_y + spacing_y],])

    def GetResultInHtml(self):
        # render the figures, tables into html, for exporting to pdf
        htmlContent = ''
        self.figureImagePreview.savefig(os.path.join(os.getcwd(), 'temp', 'figureImages.png'))
        self.figureScatter.savefig(os.path.join(os.getcwd(), 'temp', 'figureScatters.png'))
        self.figureHist_T1.savefig(os.path.join(os.getcwd(), 'temp', 'figureHist_T1.png'))
        self.figureBoxPlot.savefig(os.path.join(os.getcwd(), 'temp', 'figureBoxPlots.png'))

        htmlContent += self.newModel.packInHtml('<h1 align="center">QIBA DRO Evaluation Tool Results Report<br>(T1)</h1>')

        htmlContent += self.newModel.packInHtml('''
        <h2 align="center">The image view of calculated T1''' +\
        '''<img src="''' + os.path.join(os.getcwd(), 'temp', 'figureImages.png') + '''" style="width:100%"> <br>'''+\
        '''<p><font face="verdana">* The first column shows the calculated T1 in black and white. You can have a general impression of the value distribution according to the changing of the parameters. Generally the brighter the pixel is, the higher the calculated value is.<br>
        <br>The Second column shows the error map between calculated and reference data. Each pixel is the result of corresponding pixel in calculated data being subtracted with that in the reference data. Generally the more the color approaches to the red direction, the larger the error is.<br>
        <br>The third column shows the normalized error. This is out of the consideration that the error could be related with the original value itself. Therefore normalized error may give a more uniformed standard of the error level. Each pixel's value comes from the division of the error by the reference pixel value. Similarly as the error map, the more the color approaches to the red direction, the larger the normalized error is.
        </p>''' )

        htmlContent += self.newModel.packInHtml( '''
        <h2 align="center">The scatter plots of calculated T1</h2>
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureScatters.png') + '''" style="width:100%"> <br>'''+\
        '''<p><font face="verdana">* For the reference data, the pixel values in rows contains different values(details please refer to the file description). Therefore in the scatter plot it shows that all green dots of a row (or column) overlap to each other. For the calculated data, as they share the same parameter, the blue dots align to the same x-axis. But they may scatter vertically, showing there's variance of the value in a row (or column).<br>
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

class MySelectionDialog(wx.Dialog):
    '''
    let the users to choose which branch of the software are they entering.
    '''
    def __init__(self, parent, message, caption, choices=[]):
        wx.Dialog.__init__(self, parent, -1)
        self.Center()
        self.SetTitle(caption)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.branchChoices = wx.RadioBox(self, -1, label = message, choices = choices, style=wx.RA_SPECIFY_ROWS)
        # self.showUpCheckBox = wx.CheckBox(self, -1, 'Do not show this dialog any more when start.')
        self.buttons = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)

        sizer.Add(self.branchChoices, 1, wx.ALL | wx.EXPAND, 5)
        # sizer.Add(self.showUpCheckBox, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.buttons, 1, wx.ALL | wx.EXPAND, 5)

        sizer.Fit(self)
        self.SetSizer(sizer)

    def GetSelections(self):
        return self.branchChoices.GetStringSelection()

    def GetIsToShowDialog(self):
        return not self.showUpCheckBox.IsChecked()

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
    # generate the application object
    Application = wx.App()

    # show the splash window
    QIBASplashWindow = MySplashScreen()
    QIBASplashWindow.Show()
    time.sleep(2)

    if len(argv) == 2:
        if argv[1] == 'KV':
            window = MainWindow_KV("QIBA evaluate tool (Ktrans-Ve)")
        elif argv[1] == 'T1':
            window = MainWindow_T1("QIBA evaluate tool (T1)")
        else:
            exit(0)
    else:
        QIBASelectionDialog = MySelectionDialog(None, 'Please select which branch to enter:', 'Branch selection...', choices=['Ktrans-Ve', 'T1'])
        if QIBASelectionDialog.ShowModal() == wx.ID_OK:
            if QIBASelectionDialog.GetSelections() == 'Ktrans-Ve':
                window = MainWindow_KV("QIBA evaluate tool (Ktrans-Ve)")
            elif QIBASelectionDialog.GetSelections() == 'T1':
                window = MainWindow_T1("QIBA evaluate tool (T1)")
        else:
            exit(0)

    # show the application's main window
    window.Show()
    window.Maximize(True)
    Application.MainLoop()

