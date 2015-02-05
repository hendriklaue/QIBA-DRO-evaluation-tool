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
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from xlwt import Workbook


import QIBA_functions
import QIBA_model

class MainWindow(wx.Frame):
    '''
    this is the parent class of the main window of the application.
    '''

    def __init__(self, parent, applicationName):
        wx.Frame.__init__(self, parent, title = applicationName, size = (wx.SYS_SCREEN_X, wx.SYS_SCREEN_Y))
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.nrOfRow = 0
        self.nrOfColumn = 0
        self.patchLen = 10
        self.WARNINGTEXT = False
        self.supportedFileTypeList = ['.dcm', '.bin', '.raw', '.tif']
        self.READYTOEVALUATE = False

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
        OnManual = aboutMenu.Append(wx.ID_ANY, 'Open the manual...')
        aboutMenu.AppendSeparator()
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

        self.menubar.Bind(wx.EVT_MENU, self.OnExport, OnExport)
        self.menubar.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        self.menubar.Bind(wx.EVT_MENU, self.OnAbout, OnAboutApp)
        self.menubar.Bind(wx.EVT_MENU, self.OnManual, OnManual)

        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(aboutMenu, "&About")
        self.SetMenuBar(self.menubar)

    def OnManual(self, event):
        # open the manual file
        os.startfile(os.path.join(os.getcwd(), 'tools', 'Manual.pdf'))

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
        show the directories and files list to load calculated data
        '''

        sizerLeft = wx.BoxSizer(wx.VERTICAL)
        sizerButton = wx.BoxSizer(wx.HORIZONTAL)

        self.selectedFilePath = ''
        # setup the tree control widget for file viewing and selection
        self.fileBrowser = wx.GenericDirCtrl(self.leftPanel, -1, dir = os.path.join(os.getcwd(), 'calculated_data'), style=wx.DIRCTRL_SHOW_FILTERS,
                                             filter="Supported files (*.dcm *.bin *.raw *.tif)|*.dcm;*.bin;*.raw;*.tif")
        self.fileTree = self.fileBrowser.GetTreeCtrl()
        # setup tooltip
        self.fileTree.Bind(wx.EVT_MOTION, self.OnMouseMotion)

        # setup the right click function
        self.SetupRightClickMenu()

        sizerLeft.Add(self.fileBrowser, 1, wx.EXPAND)

        self.leftPanel.SetSizer(sizerLeft)

    def OnMouseMotion(self, event):
        '''
        show the tooltip on the tree control item
        '''
        pos = self.fileTree.ScreenToClient(wx.GetMousePosition())
        item_index, flag = self.fileTree.HitTest(pos)
        if flag == wx.TREE_HITTEST_ONITEMLABEL:
            if (str(os.path.splitext(self.fileTree.GetItemText(item_index))[1]) in self.supportedFileTypeList):
                self.fileTree.SetToolTipString('Left-click to select, then right click to import.')
        event.Skip()

    def SetupCalPath(self):
        '''
        setup the calculated data path part
        '''
        pass

    def SetupRefPath(self):
        '''
        setup the calculated data path part
        '''
        pass

    def SetupDimEdit(self):
        '''
        setup the calculated data path part
        '''
        pass


    def SetupRight(self):
        '''
        set up the right panel
        '''
        self.noteBookRight = wx.Notebook(self.rightPanel)  #, style=wx.SUNKEN_BORDER)
        self.pageStart = wx.Panel(self.noteBookRight)
        self.pageImagePreview = wx.Panel(self.noteBookRight)
        self.pageScatter = wx.Panel(self.noteBookRight)
        self.pageHistogram = wx.Panel(self.noteBookRight)
        #self.pageHistogram = scrolled.ScrolledPanel(self.noteBookRight)
        self.pageBoxPlot = wx.Panel(self.noteBookRight)
        self.pageStatistics = wx.Panel(self.noteBookRight)
        self.pageCovarianceCorrelation = wx.Panel(self.noteBookRight)
        self.pageModelFitting = wx.Panel(self.noteBookRight)
        self.pageT_Test = wx.Panel(self.noteBookRight)
        self.pageU_Test = wx.Panel(self.noteBookRight)
        self.pageChiq = wx.Panel(self.noteBookRight)

        self.noteBookRight.AddPage(self.pageStart, 'Start')
        self.noteBookRight.AddPage(self.pageImagePreview, "Image Viewer")
        self.noteBookRight.AddPage(self.pageScatter, "Scatter Plots Viewer")
        self.noteBookRight.AddPage(self.pageHistogram, "Histograms Plots Viewer")
        self.noteBookRight.AddPage(self.pageBoxPlot, "Box Plots Viewer")
        self.noteBookRight.AddPage(self.pageStatistics, "Statistics Viewer")
        self.noteBookRight.AddPage(self.pageCovarianceCorrelation, "Covariance And Correlation")
        self.noteBookRight.AddPage(self.pageModelFitting, "Model fitting")
        self.noteBookRight.AddPage(self.pageT_Test, "t-test results Viewer")
        self.noteBookRight.AddPage(self.pageU_Test, "U-test results Viewer")
        self.noteBookRight.AddPage(self.pageChiq, "Chi-Square test results Viewer")


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

        # page chi-square-test
        self.ChiqViewer = wx.html.HtmlWindow(self.pageChiq, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.ChiqViewer, 1, wx.EXPAND)
        self.pageChiq.SetSizer(sizer)



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

        try:
            self.ChiqViewer.SetPage('')
        except:
            pass

        try:
            self.ANOVAViewer.SetPage('')
        except:
            pass

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


        # setup the toolbar
        self.toolbar_maps = NavigationToolbar(self.canvasImagePreview)
        self.toolbar_maps.Hide()

        # right click
        self.figureImagePreview.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureImagePreview.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasImagePreview, self.rightDown_maps)
        self.popmenu_maps = wx.Menu()
        self.ID_POPUP_MAPS_PAN = wx.NewId()
        self.ID_POPUP_MAPS_ZOOM = wx.NewId()
        self.ID_POPUP_MAPS_SAVE = wx.NewId()

        OnMaps_pan = wx.MenuItem(self.popmenu_maps, self.ID_POPUP_MAPS_PAN, 'Pan')
        OnMaps_zoom = wx.MenuItem(self.popmenu_maps, self.ID_POPUP_MAPS_ZOOM, 'Zooom')
        OnMaps_save = wx.MenuItem(self.popmenu_maps, self.ID_POPUP_MAPS_SAVE, 'Save')
        self.popmenu_maps.AppendItem(OnMaps_pan)
        self.popmenu_maps.AppendItem(OnMaps_zoom)
        self.popmenu_maps.AppendItem(OnMaps_save)
        wx.EVT_MENU(self.popmenu_maps, self.ID_POPUP_MAPS_PAN, self.toolbar_maps.pan)
        wx.EVT_MENU(self.popmenu_maps, self.ID_POPUP_MAPS_ZOOM, self.toolbar_maps.zoom)
        wx.EVT_MENU(self.popmenu_maps, self.ID_POPUP_MAPS_SAVE, self.toolbar_maps.save_figure)

        # double click
        wx.EVT_LEFT_DCLICK(self.canvasImagePreview, self.toolbar_maps.home)

        self.figureImagePreview.tight_layout()
        self.canvasImagePreview.draw()

    def enter_axes(self, event):
        self.IN_AXES = True

    def leave_axes(self, event):
        self.IN_AXES = False

    def rightDown_maps(self, event):
        '''
        right down on figure
        '''
        if self.IN_AXES:
            self.pageImagePreview.PopupMenu(self.popmenu_maps, event.GetPosition())
        else:
            pass

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
                subPlot.scatter(refDataList[i][j], dataList[i][j], color = 'b', alpha = 1, label = 'calculated value')
                subPlot.scatter(refDataList[i][j], refDataList[i][j], color = 'g', alpha = 1, label = 'reference value')
                subPlot.legend(loc = 'upper left')
                subPlot.set_xlim(xLim[i])
                subPlot.set_ylim(yLim[i])
                subPlot.set_xlabel(xLabelList[i][j])
                subPlot.set_ylabel(yLabelList[i][j])
                subPlot.set_title(titleList[i][j])

        # setup the toolbar
        self.toolbar_scatters = NavigationToolbar(self.canvasScatter)
        self.toolbar_scatters.Hide()

        # right click
        self.figureScatter.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureScatter.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasScatter, self.rightDown_scatters)
        self.popmenu_scatters = wx.Menu()
        self.ID_POPUP_SCATTER_PAN = wx.NewId()
        self.ID_POPUP_SCATTER_ZOOM = wx.NewId()
        self.ID_POPUP_SCATTER_SAVE = wx.NewId()

        OnScatters_pan = wx.MenuItem(self.popmenu_scatters, self.ID_POPUP_SCATTER_PAN, 'Pan')
        OnScatters_zoom = wx.MenuItem(self.popmenu_scatters, self.ID_POPUP_SCATTER_ZOOM, 'Zooom')
        OnScatters_save = wx.MenuItem(self.popmenu_scatters, self.ID_POPUP_SCATTER_SAVE, 'Save')
        self.popmenu_scatters.AppendItem(OnScatters_pan)
        self.popmenu_scatters.AppendItem(OnScatters_zoom)
        self.popmenu_scatters.AppendItem(OnScatters_save)
        wx.EVT_MENU(self.popmenu_scatters, self.ID_POPUP_SCATTER_PAN, self.toolbar_scatters.pan)
        wx.EVT_MENU(self.popmenu_scatters, self.ID_POPUP_SCATTER_ZOOM, self.toolbar_scatters.zoom)
        wx.EVT_MENU(self.popmenu_scatters, self.ID_POPUP_SCATTER_SAVE, self.toolbar_scatters.save_figure)

        # double click
        wx.EVT_LEFT_DCLICK(self.canvasScatter, self.toolbar_scatters.home)

        self.figureScatter.tight_layout()
        self.canvasScatter.draw()

    def rightDown_scatters(self, event):
        '''
        right down on figure
        '''
        if self.IN_AXES:
            self.canvasScatter.PopupMenu(self.popmenu_scatters, event.GetPosition())
        else:
            pass

    def DrawHistograms(self):
        pass

    def DrawBoxPlot(self):
        pass


    def OnEvaluate(self, event):
        # start to evaluate

        # make sure there's calculated data loaded
        if not self.READYTOEVALUATE:
            wx.MessageBox('Please import proper calculated data!', 'Info', wx.OK | wx.ICON_INFORMATION)
            return

        # check the image dimension parameter validation
        if self.WARNINGTEXT:
            self.SetStatusText('Please input correct dimension of the image!')
            return

        # clear the interface if they were used before
        self.ClearInterface()

        # disable some widgets
        self.buttonEvaluate.Disable()

        # status bar
        self.SetStatusText('Evaluating, please wait...')
        #EvaluateProgressDialog.Update(5)

        # create new model object to evaluated on
        self.GenerateModel()

        # call the method to execute evaluation
        try:
            self.newModel.Evaluate()
        except RuntimeError:
            self.SetStatusText('RuntimeError occurs. Evaluation terminated.')
            return False
        except:
            self.SetStatusText('Error occurs. Evaluation terminated.')
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

    def GenerateModel(self):
        self.newModel = QIBA_model.Model_KV('', '', '', '', [self.nrOfRow, self.nrOfColumn])

    def ShowResults(self):
        pass

    def OnExportToPDF(self, event):
        # export the evaluation results to PDF

        self.buttonEvaluate.Disable()

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

        self.buttonEvaluate.Enable()



    def GetResultInHtml(self):
        # render the figures, tables into html, for exporting to pdf
        pass

    def OnQuit(self, event):
        # quit the application
        exit(0)

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

        self.patchLen = 10
        self.WARNINGTEXT = False

        # default files' paths
        self.path_ref_K = os.path.join(os.getcwd(), 'reference_data', 'Ktrans.dcm')
        self.path_ref_V = os.path.join(os.getcwd(), 'reference_data', 'Ve.dcm')
        self.path_cal_K = ''
        self.path_cal_V = ''

        # customize the main window
        self.LoadRef()
        self.SetupStartPage()
        self.SetupEditMenu()
        self.SetupRightClickMenu()
        self.SetupPage_Histogram()
        self.SetupPageANOVA()

    def ShowResults(self):
        # show the results in the main window
        self.statisticsViewer.SetPage(self.newModel.GetStatisticsInHTML())
        self.covCorrViewer.SetPage(self.newModel.GetCovarianceCorrelationInHTML())
        self.modelFittingViewer.SetPage(self.newModel.GetModelFittingInHTML())
        self.t_testViewer.SetPage(self.newModel.GetT_TestResultsInHTML())
        self.U_testViewer.SetPage(self.newModel.GetU_TestResultsInHTML())
        self.ANOVAViewer.SetPage(self.newModel.GetANOVAResultsInHTML())
        self.ChiqViewer.SetPage(self.newModel.ChiSquareTestResultInHTML)

        self.IN_AXES = False

        # draw the figures
        self.DrawMaps()
        self.DrawScatter()
        self.DrawHistograms()
        self.DrawBoxPlot()

    def SetupPageANOVA(self):
        '''
        setup page of ANOVA
        '''
        self.pageANOVA = wx.Panel(self.noteBookRight)
        self.noteBookRight.AddPage(self.pageANOVA, "ANOVA results Viewer")
        self.ANOVAViewer = wx.html.HtmlWindow(self.pageANOVA, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.ANOVAViewer, 1, wx.EXPAND)
        self.pageANOVA.SetSizer(sizer)
        self.rightPanel.Layout()

    def LoadRef(self):
        '''
        load the reference data, and get the image size
        '''
        self.ref_K, nrOfRow1, nrOfColumn1, fileType = QIBA_functions.ImportRawFile(self.path_ref_K, self.patchLen)
        self.ref_V, nrOfRow2, nrOfColumn2, fileType = QIBA_functions.ImportRawFile(self.path_ref_V, self.patchLen)
        if (nrOfRow1 == nrOfRow2) and (nrOfColumn1 == nrOfColumn2):
            self.nrOfRow = nrOfRow1 - 2
            self.nrOfColumn = nrOfColumn1
        else:
            self.SetStatusText('Please load suitable reference data!')

    def SetupStartPage(self):
        '''
        setup the start page
        '''
        # sizerRef_K_path = wx.BoxSizer(wx.HORIZONTAL)
        # sizerRef_V_path = wx.BoxSizer(wx.HORIZONTAL)
        sizerRef_K_image = wx.BoxSizer(wx.HORIZONTAL)
        sizerRef_V_image = wx.BoxSizer(wx.HORIZONTAL)
        sizerRef_K = wx.BoxSizer(wx.VERTICAL)
        sizerRef_V = wx.BoxSizer(wx.VERTICAL)
        sizerMiddle = wx.BoxSizer(wx.HORIZONTAL)

        panelRef_K = wx.Panel(self.pageStart, style = wx.SIMPLE_BORDER)
        panelRef_V = wx.Panel(self.pageStart, style = wx.SIMPLE_BORDER)

        # setup the reference data paths
        # sizerRef_K_path.Add(wx.StaticText(panelRef_K, -1, 'Reference Ktrans: '))
        # self.textCtrlRefPath_K = wx.TextCtrl(panelRef_K, -1, self.path_ref_K)
        # sizerRef_K_path.Add(self.textCtrlRefPath_K, 1, wx.EXPAND)
        #
        # buttonLoadRefK = wx.Button(panelRef_K, -1, 'Select reference Ktrans...')
        # buttonLoadRefK.Bind(wx.EVT_BUTTON, self.OnLoadRef_K)
        # sizerRef_K_path.Add(buttonLoadRefK, 0, wx.ALIGN_RIGHT)

        self.figureRefViewer_K = Figure()
        self.canvasRefViewer_K = FigureCanvas(panelRef_K, -1, self.figureRefViewer_K)
        sizerRef_K_image.Add(self.canvasRefViewer_K, 1, wx.EXPAND)

        sizerRef_K.Add(sizerRef_K_image, 1, wx.EXPAND)
        # sizerRef_K.Add(sizerRef_K_path, 0, wx.EXPAND)
        panelRef_K.SetSizer(sizerRef_K)

        # sizerRef_V_path.Add(wx.StaticText(panelRef_V, -1, 'Reference Ve: '))
        # self.textCtrlRefPath_V = wx.TextCtrl(panelRef_V, -1, self.path_ref_V, size = (400, -1))
        # sizerRef_V_path.Add(self.textCtrlRefPath_V, 1, wx.EXPAND)
        # buttonLoadRefV = wx.Button(panelRef_V, -1, 'Select reference Ve...')
        # buttonLoadRefV.Bind(wx.EVT_BUTTON, self.OnLoadRef_V)
        # sizerRef_V_path.Add(buttonLoadRefV)
        self.figureRefViewer_V = Figure()
        self.canvasRefViewer_V = FigureCanvas(panelRef_V, -1, self.figureRefViewer_V)
        sizerRef_V_image.Add(self.canvasRefViewer_V, 1, wx.EXPAND)

        sizerRef_V.Add(sizerRef_V_image, 1, wx.EXPAND)
        # sizerRef_V.Add(sizerRef_V_path, 0, wx.EXPAND)
        panelRef_V.SetSizer(sizerRef_V)

        # the upper part of the page
        self.ShowRef()
        sizerMiddle.Add(panelRef_K, 1, wx.EXPAND)
        sizerMiddle.Add(panelRef_V, 1, wx.EXPAND)

        # button to start evaluation
        self.buttonEvaluate = wx.Button(self.pageStart, wx.ID_ANY, 'Evaluate')
        self.Bind(wx.EVT_BUTTON, self.OnEvaluate, self.buttonEvaluate)
        self.buttonEvaluate.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0))
        self.buttonEvaluate.SetToolTip(wx.ToolTip('Press to evaluate after importing calculated data.'))

        # text area
        header = wx.StaticText(self.pageStart, -1, 'Welcome to QIBA Evaluate Tool(GKM)!')
        fontHeader = wx.Font(22, wx.DECORATIVE, style = wx.FONTSTYLE_NORMAL, weight = wx.FONTWEIGHT_NORMAL)
        # instruction1 = wx.StaticText(self.pageStart, -1, '- left-click to select and right-click to import the calculated file from the file tree on the left.')
        # instruction2 = wx.StaticText(self.pageStart, -1, '- change the reference data under if necessary.')
        # instruction3 = wx.StaticText(self.pageStart, -1, '- press the button "Evaluate" at the bottom to start evaluation.')
        # fontText = wx.Font(14, wx.DECORATIVE, style = wx.FONTSTYLE_NORMAL, weight = wx.FONTWEIGHT_NORMAL)
        header.SetFont(fontHeader)
        # instruction1.SetFont(fontText)
        # instruction2.SetFont(fontText)
        # instruction3.SetFont(fontText)
        sizerTop = wx.BoxSizer(wx.VERTICAL)
        sizerTop.AddStretchSpacer()
        sizerTop.Add(header, flag = wx.ALIGN_CENTER)
        sizerTop.AddStretchSpacer()
        # sizerTop.Add(instruction1)
        # sizerTop.Add(instruction2)
        # sizerTop.Add(instruction3)

        # the page sizer
        sizerPage = wx.BoxSizer(wx.VERTICAL)
        sizerPage.Add(sizerTop, 2, wx.EXPAND)
        sizerPage.Add(sizerMiddle, 19, wx.EXPAND)
        sizerPage.Add(self.buttonEvaluate, 1, wx.EXPAND)
        # self.buttonEvaluate.Disable()

        self.pageStart.SetSizer(sizerPage)
        self.pageStart.Fit()

    def ShowRef(self):
        '''
        show the reference images in the start page
        '''
        self.figureRefViewer_K.clear()
        subplot_Ref_K = self.figureRefViewer_K.add_subplot(1,1,1)
        handler = subplot_Ref_K.imshow(self.ref_K, cmap = 'bone', interpolation='nearest')
        divider = make_axes_locatable(subplot_Ref_K.get_figure().gca()) # for tight up the color bar
        cax = divider.append_axes("right", "5%", pad="3%")
        subplot_Ref_K.get_figure().colorbar(handler, cax = cax).set_label('Ktrans[1/min]') # show color bar and the label
        subplot_Ref_K.set_title('Reference Data Ktrans')
        self.figureRefViewer_K.tight_layout()
        self.canvasRefViewer_K.draw()

        self.figureRefViewer_V.clear()
        subplot_Ref_V = self.figureRefViewer_V.add_subplot(1,1,1)
        handler = subplot_Ref_V.imshow(self.ref_V, cmap = 'bone', interpolation='nearest')
        divider = make_axes_locatable(subplot_Ref_V.get_figure().gca()) # for tight up the color bar
        cax = divider.append_axes("right", "5%", pad="3%")
        subplot_Ref_V.get_figure().colorbar(handler, cax = cax).set_label('Ve[]') # show color bar and the label
        subplot_Ref_V.set_title('Reference Data Ve')
        self.figureRefViewer_V.tight_layout()
        self.canvasRefViewer_V.draw()

    def SetupEditMenu(self):
        # setup the edit menu in the menu bar
        editMenu = wx.Menu()

        # OnEditImageDimension = editMenu.Append(wx.ID_ANY, 'Edit the dimensions of the images...')
        # editMenu.AppendSeparator()
        OnLoadRef_K = editMenu.Append(wx.ID_ANY, 'Load reference Ktrans...')
        OnLoadRef_V = editMenu.Append(wx.ID_ANY, 'Load reference Ve...')
        # self.menubar.Bind(wx.EVT_MENU, self.OnEditImageDimension, OnEditImageDimension)
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
        wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_CAL_K, self.OnLoadCal_K)
        wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_CAL_V, self.OnLoadCal_V)

    def SetupPage_Histogram(self):
        # setup the histogram page
        self.figureHist_Ktrans = Figure()
        self.canvasHist_Ktrans = FigureCanvas(self.pageHistogram,-1, self.figureHist_Ktrans)

        self.figureHist_Ve = Figure()
        self.canvasHist_Ve = FigureCanvas(self.pageHistogram,-1, self.figureHist_Ve)

        self.verticalLineHist = wx.StaticLine(self.pageHistogram, -1, style=wx.LI_VERTICAL) # vertical line to separate the two subplots

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasHist_Ktrans, 35, wx.EXPAND)
        sizer.Add(self.verticalLineHist, 2, wx.EXPAND)
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
        self.newModel = QIBA_model.Model_KV(self.path_ref_K, self.path_ref_V, self.path_cal_K, self.path_cal_V, [self.nrOfRow, self.nrOfColumn])

    def OnRightClick(self, event):
        # the right click action on the file list
        if (str(os.path.splitext(self.fileBrowser.GetPath())[1]) in self.supportedFileTypeList):
            self.PopupMenu(self.popupMenu, event.GetPosition())
        else:
            self.SetStatusText('Invalid file or path chosen.')

    def OnLoadCal_K(self, event):
        # pass the file path for loading
        self.path_cal_K = self.fileBrowser.GetPath()
        self.SetStatusText('Calculated Ktrans loaded.')
        if self.path_cal_V:
            self.READYTOEVALUATE = True
            self.buttonEvaluate.Enable()

    def OnLoadCal_V(self, event):
        # pass the file path for loading
        self.path_cal_V = self.fileBrowser.GetPath()
        self.SetStatusText('Calculated Ve loaded.')
        if self.path_cal_K:
            self.READYTOEVALUATE = True
            self.buttonEvaluate.Enable()

    def OnLoadRef_K(self, event):
        # pass the file path for loading
        dlg = wx.FileDialog(self, 'Load reference Ktrans...', '', '', "Supported files (*.dcm *.bin *.raw *.tif)|*.dcm;*.bin;*.raw;*.tif", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_ref_K = dlg.GetPath()
            imageData, nrOfRow, nrOfColumn, fileType = QIBA_functions.ImportRawFile(self.path_ref_K, self.patchLen)
            if fileType == 'BINARY':
                self.OnImportBinaryDialog_K()
            elif imageData == False:
                self.SetStatusText('Please import a valid image!')
            else:
                self.ref_K = imageData
                self.nrOfRow = nrOfRow - 2
                self.nrOfColumn = nrOfColumn
            self.ShowRef()
            self.SetStatusText('Reference Ktrans loaded.')
        else:
            self.SetStatusText('Reference Ktrans was NOT loaded!')

    def OnLoadRef_V(self, event):
        # pass the file path for loading
        dlg = wx.FileDialog(self, 'Load reference Ve...', '', '', "Supported files (*.dcm *.bin *.raw *.tif)|*.dcm;*.bin;*.raw;*.tif", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_ref_V = dlg.GetPath()
            imageData, nrOfRow, nrOfColumn, fileType = QIBA_functions.ImportRawFile(self.path_ref_V, self.patchLen)
            if fileType == 'BINARY':
                self.OnImportBinaryDialog_V()
            elif imageData == False:
                self.SetStatusText('Please import a valid image!')
            else:
                self.ref_V = imageData
                self.nrOfRow = nrOfRow - 2
                self.nrOfColumn = nrOfColumn
            self.ShowRef()
            self.SetStatusText('Reference Ve loaded.')
        else:
            self.SetStatusText('Reference Ve was NOT loaded!')

    def OnImportBinaryDialog_K(self):
        # edit the dimension of the images for importing the binary images
        self.dlg = wx.Dialog(self, title = 'Please insert the size of the binary image...')

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
        self.buttonOK.Bind(wx.EVT_BUTTON, self.OnImportBinaryDialog_OK_K)
        self.sizer0.Add(self.sizer1, 1)
        self.sizer0.Add(self.sizer2, 1)
        self.sizer0.Add(self.buttonOK, 1)
        self.sizer0.Fit(self.dlg)
        self.dlg.SetSizer(self.sizer0)

        self.dlg.Center()
        self.WARNINGTEXT = False

        self.dlg.ShowModal()

    def OnImportBinaryDialog_OK_K(self, event):
        # when the OK is clicked in the dimension edit dialog

        if (QIBA_functions.IsPositiveInteger(self.textCtrl1.GetValue()) and QIBA_functions.IsPositiveInteger(self.textCtrl2.GetValue()) ):
            self.nrOfRow = int(self.textCtrl1.GetValue()) / self.patchLen
            self.nrOfColumn = int(self.textCtrl2.GetValue()) / self.patchLen
            self.dlg.Destroy()
            self.ref_K = QIBA_functions.ImportFile(self.path_ref_K, self.nrOfRow, self.nrOfColumn, self.patchLen)[0]
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

    def OnImportBinaryDialog_V(self):
        # edit the dimension of the images for importing the binary images
        self.dlg = wx.Dialog(self, title = 'Please insert the size of the binary image...')

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
        self.buttonOK.Bind(wx.EVT_BUTTON, self.OnImportBinaryDialog_OK_V)
        self.sizer0.Add(self.sizer1, 1)
        self.sizer0.Add(self.sizer2, 1)
        self.sizer0.Add(self.buttonOK, 1)
        self.sizer0.Fit(self.dlg)
        self.dlg.SetSizer(self.sizer0)

        self.dlg.Center()
        self.WARNINGTEXT = False

        self.dlg.ShowModal()

    def OnImportBinaryDialog_OK_V(self, event):
        # when the OK is clicked in the dimension edit dialog

        if (QIBA_functions.IsPositiveInteger(self.textCtrl1.GetValue()) and QIBA_functions.IsPositiveInteger(self.textCtrl2.GetValue()) ):
            self.nrOfRow = int(self.textCtrl1.GetValue()) / self.patchLen
            self.nrOfColumn = int(self.textCtrl2.GetValue()) / self.patchLen
            self.dlg.Destroy()
            self.ref_V = QIBA_functions.ImportFile(self.path_ref_V, self.nrOfRow, self.nrOfColumn, self.patchLen)[0]
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

        # setup the toolbar
        self.toolbar_hist_K = NavigationToolbar(self.canvasHist_Ktrans)
        self.toolbar_hist_K.Hide()
        self.toolbar_hist_V = NavigationToolbar(self.canvasHist_Ve)
        self.toolbar_hist_V.Hide()

        # right click
        self.figureHist_Ktrans.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureHist_Ktrans.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        self.figureHist_Ve.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureHist_Ve.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasHist_Ktrans, self.rightDown_hist_K)
        wx.EVT_RIGHT_DOWN(self.canvasHist_Ve, self.rightDown_hist_V)

        self.popmenu_hist_K = wx.Menu()
        self.ID_POPUP_HITS_PAN_K = wx.NewId()
        self.ID_POPUP_HITS_ZOOM_K = wx.NewId()
        self.ID_POPUP_HITS_SAVE_K = wx.NewId()

        OnHist_pan_K = wx.MenuItem(self.popmenu_hist_K, self.ID_POPUP_HITS_PAN_K, 'Pan')
        OnHist_zoom_K = wx.MenuItem(self.popmenu_hist_K, self.ID_POPUP_HITS_ZOOM_K, 'Zooom')
        OnHist_save_K = wx.MenuItem(self.popmenu_hist_K, self.ID_POPUP_HITS_SAVE_K, 'Save')
        self.popmenu_hist_K.AppendItem(OnHist_pan_K)
        self.popmenu_hist_K.AppendItem(OnHist_zoom_K)
        self.popmenu_hist_K.AppendItem(OnHist_save_K)
        wx.EVT_MENU(self.popmenu_hist_K, self.ID_POPUP_HITS_PAN_K, self.toolbar_hist_K.pan)
        wx.EVT_MENU(self.popmenu_hist_K, self.ID_POPUP_HITS_ZOOM_K, self.toolbar_hist_K.zoom)
        wx.EVT_MENU(self.popmenu_hist_K, self.ID_POPUP_HITS_SAVE_K, self.toolbar_hist_K.save_figure)

        self.popmenu_hist_V = wx.Menu()
        self.ID_POPUP_HITS_PAN_V = wx.NewId()
        self.ID_POPUP_HITS_ZOOM_V = wx.NewId()
        self.ID_POPUP_HITS_SAVE_V = wx.NewId()

        OnHist_pan = wx.MenuItem(self.popmenu_hist_V, self.ID_POPUP_HITS_PAN_V, 'Pan')
        OnHist_zoom = wx.MenuItem(self.popmenu_hist_V, self.ID_POPUP_HITS_ZOOM_V, 'Zooom')
        OnHist_save = wx.MenuItem(self.popmenu_hist_V, self.ID_POPUP_HITS_SAVE_V, 'Save')
        self.popmenu_hist_V.AppendItem(OnHist_pan)
        self.popmenu_hist_V.AppendItem(OnHist_zoom)
        self.popmenu_hist_V.AppendItem(OnHist_save)
        wx.EVT_MENU(self.popmenu_hist_V, self.ID_POPUP_HITS_PAN_V, self.toolbar_hist_V.pan)
        wx.EVT_MENU(self.popmenu_hist_V, self.ID_POPUP_HITS_ZOOM_V, self.toolbar_hist_V.zoom)
        wx.EVT_MENU(self.popmenu_hist_V, self.ID_POPUP_HITS_SAVE_V, self.toolbar_hist_V.save_figure)

        # double click
        wx.EVT_LEFT_DCLICK(self.canvasHist_Ktrans, self.toolbar_hist_K.home)
        wx.EVT_LEFT_DCLICK(self.canvasHist_Ve, self.toolbar_hist_V.home)


        self.figureHist_Ve.tight_layout()
        self.figureHist_Ktrans.tight_layout()

        self.figureHist_Ktrans.subplots_adjust(top = 0.94, right = 0.95)
        self.figureHist_Ve.subplots_adjust(top = 0.94, right = 0.95)

        self.canvasHist_Ktrans.draw()
        self.canvasHist_Ve.draw()

    def rightDown_hist_K(self, event):
        '''
        right down on figure
        '''
        if self.IN_AXES:
            self.canvasHist_Ktrans.PopupMenu(self.popmenu_hist_K, event.GetPosition())
        else:
            pass

    def rightDown_hist_V(self, event):
        '''
        right down on figure
        '''
        if self.IN_AXES:
            self.canvasHist_Ve.PopupMenu(self.popmenu_hist_V, event.GetPosition())
        else:
            pass

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
        subPlotK.boxplot(temp, notch = 1, sym = 'r+', whis=1.5)


        subPlotV = self.figureBoxPlot.add_subplot(2, 1, 2)
        subPlotV.clear()
        temp = []
        referValueV = []
        for j in range(self.newModel.nrOfColumns):
            for i in range(self.newModel.nrOfRows):
                temp.append(self.newModel.Ve_cal[i][j])
            referValueV.append(float('{0:.2f}'.format(zip(*self.newModel.Ve_ref)[j][0][0])))
        subPlotV.boxplot(temp, notch = 1, sym = 'r+', whis=1.5)

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

        # setup the toolbar
        self.toolbar_box = NavigationToolbar(self.canvasBoxPlot)
        self.toolbar_box.Hide()

        # right click
        self.figureBoxPlot.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureBoxPlot.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasBoxPlot, self.rightDown_box)
        self.popmenu_box = wx.Menu()
        self.ID_POPUP_BOX_PAN = wx.NewId()
        self.ID_POPUP_BOX_ZOOM = wx.NewId()
        self.ID_POPUP_BOX_SAVE = wx.NewId()

        OnBox_pan = wx.MenuItem(self.popmenu_box, self.ID_POPUP_BOX_PAN, 'Pan')
        OnBox_zoom = wx.MenuItem(self.popmenu_box, self.ID_POPUP_BOX_ZOOM, 'Zooom')
        OnBox_save = wx.MenuItem(self.popmenu_box, self.ID_POPUP_BOX_SAVE, 'Save')
        self.popmenu_box.AppendItem(OnBox_pan)
        self.popmenu_box.AppendItem(OnBox_zoom)
        self.popmenu_box.AppendItem(OnBox_save)
        wx.EVT_MENU(self.popmenu_box, self.ID_POPUP_BOX_PAN, self.toolbar_box.pan)
        wx.EVT_MENU(self.popmenu_box, self.ID_POPUP_BOX_ZOOM, self.toolbar_box.zoom)
        wx.EVT_MENU(self.popmenu_box, self.ID_POPUP_BOX_SAVE, self.toolbar_box.save_figure)

        # double click
        wx.EVT_LEFT_DCLICK(self.canvasBoxPlot, self.toolbar_box.home)


        self.figureBoxPlot.tight_layout()
        self.canvasBoxPlot.draw()
        self.rightPanel.Layout()

    def rightDown_box(self, event):
        '''
        right down on figure
        '''
        if self.IN_AXES:
            self.pageBoxPlot.PopupMenu(self.popmenu_box, event.GetPosition())
        else:
            pass

    def DrawMaps(self):
        # draw the maps of the preview and error
        self.PlotPreview([[self.newModel.Ktrans_cal_inRow, self.newModel.Ktrans_error, self.newModel.Ktrans_error_normalized],
                                  [self.newModel.Ve_cal_inRow, self.newModel.Ve_error, self.newModel.Ve_error_normalized]],

                                [['Calculated Ktrans', 'Error map of Ktrans', 'Normalized Error map of Ktrans'],
                                 ['Calculated Ve', 'Error map of Ve', 'Normalized Error map of Ve']],

                                [['bone', 'rainbow', 'rainbow'], ['bone', 'rainbow', 'rainbow']],

                                [['Ktrans[1/min]', 'Delta Ktrans[1/min.]', 'Normalized error[%]'], ['Ve[]', 'Delta Ve[]', 'Normalized error[%]']])

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

    def OnExport(self, event):
        '''
        export the files as .png, excel
        '''
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.SetStatusText('Exporting, please wait...')
            saveDir = dlg.GetPath()
            try:
                self.figureImagePreview.savefig(os.path.join(saveDir, 'maps.png'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return

            try:
                self.figureScatter.savefig(os.path.join(saveDir, 'scatters.png'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return

            try:
                self.figureHist_Ktrans.savefig(os.path.join(saveDir, 'hist_K.png'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return

            try:
                self.figureHist_Ve.savefig(os.path.join(saveDir, 'hist_V.png'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return

            try:
                self.figureBoxPlot.savefig(os.path.join(saveDir, 'boxplot.png'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return

            # export the table to excel
            book = Workbook()
            sheetMean = book.add_sheet('Mean')
            sheetStd = book.add_sheet('Standard deviation')
            sheetMedian = book.add_sheet('Median')
            sheet1Qtl = book.add_sheet('1st quartiel')
            sheet3Qtl = book.add_sheet('3rd quartiel')
            sheetMin = book.add_sheet('Minimum')
            sheetMax = book.add_sheet('Maximum')
            sheetCov = book.add_sheet('Covariance')
            sheetCor = book.add_sheet('Correlation')
            sheetFit = book.add_sheet('Model fitting')
            sheetT = book.add_sheet('T-test results')
            sheetU = book.add_sheet('U-test results')
            sheetChiq = book.add_sheet('Chi-square test results')
            sheetA = book.add_sheet('ANOVA results')


            QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetMean, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_mean, self.newModel.Ve_cal_patch_mean], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetStd, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_deviation, self.newModel.Ve_cal_patch_deviation], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetMedian, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_median, self.newModel.Ve_cal_patch_median], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_GKM_statistics(sheet1Qtl, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_1stQuartile, self.newModel.Ve_cal_patch_1stQuartile], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_GKM_statistics(sheet3Qtl, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_3rdQuartile, self.newModel.Ve_cal_patch_3rdQuartile], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetMin, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_min, self.newModel.Ve_cal_patch_min], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetMax, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_max, self.newModel.Ve_cal_patch_max], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)

            QIBA_functions.WriteToExcelSheet_GKM_co(sheetCor, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.corr_KK,self.newModel.corr_KV,self.newModel.corr_VK,self.newModel.corr_VV], 1, self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_GKM_co(sheetCov, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.cov_KK,self.newModel.cov_KV,self.newModel.cov_VK,self.newModel.cov_VV], 1, self.nrOfRow, self.nrOfColumn)

            QIBA_functions.WriteToExcelSheet_GKM_fit(sheetFit, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.a_lin_Ktrans, self.newModel.b_lin_Ktrans,self.newModel.a_log_Ktrans,self.newModel.b_log_Ktrans,self.newModel.a_lin_Ve, self.newModel.b_lin_Ve,self.newModel.a_log_Ve,self.newModel.b_log_Ve], 1, self.nrOfRow, self.nrOfColumn)

            QIBA_functions.WriteToExcelSheet_GKM_test(sheetT, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_ttest_t, self.newModel.Ktrans_cal_patch_ttest_p, self.newModel.Ve_cal_patch_ttest_t, self.newModel.Ve_cal_patch_ttest_p], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn, 'T-statistics')
            QIBA_functions.WriteToExcelSheet_GKM_test(sheetU, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_Utest_u, self.newModel.Ktrans_cal_patch_Utest_p, self.newModel.Ve_cal_patch_Utest_u, self.newModel.Ve_cal_patch_Utest_p], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn, 'U-value')

            QIBA_functions.WriteToExcelSheet_GKM_A(sheetA, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_ANOVA_f,self.newModel.Ktrans_cal_patch_ANOVA_p,self.newModel.Ve_cal_patch_ANOVA_f,self.newModel.Ve_cal_patch_ANOVA_p], 1, self.nrOfRow, self.nrOfColumn)

            QIBA_functions.WriteToExcelSheet_GKM_test(sheetChiq, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_Chisquare_c, self.newModel.Ktrans_cal_patch_Chisquare_p, self.newModel.Ve_cal_patch_Chisquare_c, self.newModel.Ve_cal_patch_Chisquare_p], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn, 'Chiq')

            try:
                book.save(os.path.join(saveDir, 'results.xls'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return

            self.SetStatusText('Files are exported.')
        else:
            pass



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

        self.patchLen = 10
        self.WARNINGTEXT = False

        # default files' paths
        self.path_ref_T1 = os.path.join(os.getcwd(), 'reference_data', 'T1.dcm')
        self.path_cal_T1 = ''


        # customize the main window
        self.LoadRef()
        self.SetupStartPage()
        self.SetupEditMenu()
        self.SetupRightClickMenu()
        self.SetupPage_Histogram()

    def ShowResults(self):
        # show the results in the main window
        self.statisticsViewer.SetPage(self.newModel.GetStatisticsInHTML())
        self.covCorrViewer.SetPage(self.newModel.GetCovarianceCorrelationInHTML())
        self.modelFittingViewer.SetPage(self.newModel.GetModelFittingInHTML())
        self.t_testViewer.SetPage(self.newModel.GetT_TestResultsInHTML())
        self.U_testViewer.SetPage(self.newModel.GetU_TestResultsInHTML())
        self.ChiqViewer.SetPage(self.newModel.ChiSquareTestResultInHTML)

        self.IN_AXES = False

        # draw the figures
        self.DrawMaps()
        self.DrawScatter()
        self.DrawHistograms()
        self.DrawBoxPlot()

    def LoadRef(self):
        '''
        load the reference data, and get the image size
        '''
        self.ref_T1, nrOfRow, nrOfColumn, fileType = QIBA_functions.ImportRawFile(self.path_ref_T1, self.patchLen)
        self.nrOfRow = nrOfRow - 1
        self.nrOfColumn = nrOfColumn

    def SetupStartPage(self):
        '''
        setup the start page
        '''
        # sizerRef_T1_path = wx.BoxSizer(wx.HORIZONTAL)
        sizerRef_T1_image = wx.BoxSizer(wx.HORIZONTAL)
        sizerRef_T1 = wx.BoxSizer(wx.VERTICAL)
        sizerMiddle = wx.BoxSizer(wx.HORIZONTAL)

        panelRef_T1 = wx.Panel(self.pageStart, style = wx.SIMPLE_BORDER)

        # setup the reference data paths
        # sizerRef_T1_path.Add(wx.StaticText(panelRef_T1, -1, 'Reference T1: '))
        # self.textCtrlRefPath_T1 = wx.TextCtrl(panelRef_T1, -1, self.path_ref_T1)
        # sizerRef_T1_path.Add(self.textCtrlRefPath_T1, 1, wx.EXPAND)
        # buttonLoadRefT1 = wx.Button(panelRef_T1, -1, 'Select reference T1...')
        # buttonLoadRefT1.Bind(wx.EVT_BUTTON, self.OnLoadRef_T1)
        # sizerRef_T1_path.Add(buttonLoadRefT1)

        self.figureRefViewer_T1 = Figure()
        self.canvasRefViewer_T1 = FigureCanvas(panelRef_T1, -1, self.figureRefViewer_T1)
        sizerRef_T1_image.Add(self.canvasRefViewer_T1, 1, wx.EXPAND)

        sizerRef_T1.Add(sizerRef_T1_image, 1, wx.EXPAND)
        # sizerRef_T1.Add(sizerRef_T1_path, 0, wx.EXPAND)
        panelRef_T1.SetSizer(sizerRef_T1)

        # the upper part of the page
        self.ShowRef()
        sizerMiddle.Add(panelRef_T1, 1, wx.EXPAND)

        # button to start evaluation
        self.buttonEvaluate = wx.Button(self.pageStart, wx.ID_ANY, 'Evaluate')
        self.Bind(wx.EVT_BUTTON, self.OnEvaluate, self.buttonEvaluate)
        self.buttonEvaluate.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0))
        self.buttonEvaluate.SetToolTip(wx.ToolTip('Press to evaluate after importing calculated data.'))

        # text area
        header = wx.StaticText(self.pageStart, -1, 'Welcome to QIBA Evaluate Tool(Flip Angle T1)!', style=wx.ALIGN_CENTER_HORIZONTAL)
        # instruction1 = wx.StaticText(self.pageStart, -1, '- left-click to select and right-click to import the calculated file from the file tree on the left.')
        # instruction2 = wx.StaticText(self.pageStart, -1, '- change the reference data under if necessary.')
        # instruction3 = wx.StaticText(self.pageStart, -1, '- press the button "Evaluate" at the bottom to start evaluation.')
        fontHeader = wx.Font(22, wx.DECORATIVE, style = wx.FONTSTYLE_NORMAL, weight = wx.FONTWEIGHT_NORMAL)
        fontText = wx.Font(14, wx.DECORATIVE, style = wx.FONTSTYLE_NORMAL, weight = wx.FONTWEIGHT_NORMAL)
        header.SetFont(fontHeader)
        # instruction1.SetFont(fontText)
        # instruction2.SetFont(fontText)
        # instruction3.SetFont(fontText)
        sizerTop = wx.BoxSizer(wx.VERTICAL)
        sizerTop.Add(header, flag = wx.CENTER)
        # sizerTop.Add(instruction1)
        # sizerTop.Add(instruction2)
        # sizerTop.Add(instruction3)

        # the page sizer
        sizerPage = wx.BoxSizer(wx.VERTICAL)
        sizerPage.Add(sizerTop, 2, wx.EXPAND)
        sizerPage.Add(sizerMiddle, 19, wx.EXPAND)
        sizerPage.Add(self.buttonEvaluate, 1, wx.EXPAND)
        # self.buttonEvaluate.Disable()

        self.pageStart.SetSizer(sizerPage)
        self.pageStart.Fit()

    def ShowRef(self):
        '''
        show the reference images in the start page
        '''
        self.figureRefViewer_T1.clear()
        subplot_Ref_T1 = self.figureRefViewer_T1.add_subplot(1,1,1)
        handler = subplot_Ref_T1.imshow(self.ref_T1, cmap = 'bone', interpolation='nearest')
        divider = make_axes_locatable(subplot_Ref_T1.get_figure().gca()) # for tight up the color bar
        cax = divider.append_axes("right", "5%", pad="3%")
        subplot_Ref_T1.get_figure().colorbar(handler, cax = cax).set_label('T1[ms]') # show color bar and the label
        subplot_Ref_T1.set_title('Reference Data T1')
        self.figureRefViewer_T1.tight_layout()
        self.canvasRefViewer_T1.draw()

    def SetupEditMenu(self):
        # setup the edit menu in the menu bar
        editMenu = wx.Menu()

        # OnEditImageDimension = editMenu.Append(wx.ID_ANY, 'Edit the dimensions of the images...')
        editMenu.AppendSeparator()
        OnLoadRef_T1 = editMenu.Append(wx.ID_ANY, 'Load reference T1...')
        # self.menubar.Bind(wx.EVT_MENU, self.OnEditImageDimension, OnEditImageDimension)
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
        sizer.Add(self.canvasHist_T1, 2, wx.EXPAND)
        self.pageHistogram.SetSizer(sizer)

    def ClearPage_Histogram(self):
        # clear the histogram page
        self.figureHist_T1.clear()
        self.canvasHist_T1.draw()

    def GenerateModel(self):
        # generate the model for evaluation
        self.newModel = QIBA_model.Model_T1(self.path_ref_T1, self.path_cal_T1, [self.nrOfRow, self.nrOfColumn])

    def OnRightClick(self, event):
        # the right click action on the file list
        if (str(os.path.splitext(self.fileBrowser.GetPath())[1]) in self.supportedFileTypeList):
            wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_CAL_T1, self.OnLoadCal_T1)
            self.PopupMenu(self.popupMenu, event.GetPosition())
        else:
            self.SetStatusText('Invalid file or path chosen.')

    def OnLoadCal_T1(self, event):
        # pass the file path for loading
        self.path_cal_T1 = self.fileBrowser.GetPath()
        self.SetStatusText('Calculated T1 loaded.')
        self.READYTOEVALUATE = True
        self.buttonEvaluate.Enable()

    def OnLoadRef_T1(self, event):
        # pass the file path for loading
        dlg = wx.FileDialog(self, 'Load reference T1...', '', '', "Supported files (*.dcm *.bin *.raw *.tif)|*.dcm;*.bin;*.raw;*.tif", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_ref_T1 = dlg.GetPath()
            imageData, nrOfRow, nrOfColumn, fileType = QIBA_functions.ImportRawFile(self.path_ref_T1, self.patchLen)
            if fileType == 'BINARY':
                self.OnImportBinaryDialog_T1()
            elif imageData == False:
                self.SetStatusText('Please import a valid image!')
            else:
                self.ref_T1 = imageData
                self.nrOfRow = nrOfRow - 1
                self.nrOfColumn = nrOfColumn
            self.ShowRef()
            self.SetStatusText('Reference T1 loaded.')
        else:
            self.SetStatusText('Reference T1 was NOT loaded!')

    def OnImportBinaryDialog_T1(self):
        # edit the dimension of the images for importing the binary images
        self.dlg = wx.Dialog(self, title = 'Please insert the size of the binary image...')

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
        self.buttonOK.Bind(wx.EVT_BUTTON, self.OnImportBinaryDialog_OK_T1)
        self.sizer0.Add(self.sizer1, 1)
        self.sizer0.Add(self.sizer2, 1)
        self.sizer0.Add(self.buttonOK, 1)
        self.sizer0.Fit(self.dlg)
        self.dlg.SetSizer(self.sizer0)

        self.dlg.Center()
        self.WARNINGTEXT = False

        self.dlg.ShowModal()

    def OnImportBinaryDialog_OK_T1(self, event):
        # when the OK is clicked in the dimension edit dialog

        if (QIBA_functions.IsPositiveInteger(self.textCtrl1.GetValue()) and QIBA_functions.IsPositiveInteger(self.textCtrl2.GetValue()) ):
            self.nrOfRow = int(self.textCtrl1.GetValue()) / self.patchLen
            self.nrOfColumn = int(self.textCtrl2.GetValue()) / self.patchLen
            self.dlg.Destroy()
            self.ref_T1 = QIBA_functions.ImportFile(self.path_ref_T1, self.nrOfRow, self.nrOfColumn, self.patchLen)[0]
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

    def DrawHistograms(self):
        # draw histograms of imported calculated maps, so that the user can have a look of the distribution of each patch.

        pixelCountInPatch = self.newModel.patchLen ** 2
        nrOfBins = 5

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
                self.pageHistogram.SetAutoLayout(1)


        # setup the toolbar
        self.toolbar_hist = NavigationToolbar(self.canvasHist_T1)
        self.toolbar_hist.Hide()

        # right click
        self.figureHist_T1.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureHist_T1.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasHist_T1, self.rightDown_hist)
        self.popmenu_hist = wx.Menu()
        self.ID_POPUP_HIST_PAN = wx.NewId()
        self.ID_POPUP_HIST_ZOOM = wx.NewId()
        self.ID_POPUP_HIST_SAVE = wx.NewId()

        OnHist_pan = wx.MenuItem(self.popmenu_hist, self.ID_POPUP_HIST_PAN, 'Pan')
        OnHist_zoom = wx.MenuItem(self.popmenu_hist, self.ID_POPUP_HIST_ZOOM, 'Zooom')
        OnHist_save = wx.MenuItem(self.popmenu_hist, self.ID_POPUP_HIST_SAVE, 'Save')
        self.popmenu_hist.AppendItem(OnHist_pan)
        self.popmenu_hist.AppendItem(OnHist_zoom)
        self.popmenu_hist.AppendItem(OnHist_save)
        wx.EVT_MENU(self.popmenu_hist, self.ID_POPUP_HIST_PAN, self.toolbar_hist.pan)
        wx.EVT_MENU(self.popmenu_hist, self.ID_POPUP_HIST_ZOOM, self.toolbar_hist.zoom)
        wx.EVT_MENU(self.popmenu_hist, self.ID_POPUP_HIST_SAVE, self.toolbar_hist.save_figure)

        # double click
        wx.EVT_LEFT_DCLICK(self.canvasHist_T1, self.toolbar_hist.home)

        self.figureHist_T1.tight_layout(pad=0.4, w_pad=0.1, h_pad=1.0)
        self.figureHist_T1.subplots_adjust(top = 0.94)
        self.canvasHist_T1.draw()


    def rightDown_hist(self, event):
        '''
        right down on figure
        '''
        if self.IN_AXES:
            self.pageHistogram.PopupMenu(self.popmenu_hist, event.GetPosition())
        else:
            pass

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
        subPlot_R1.boxplot(temp, notch = 1, sym = 'r+', whis=1.5)

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

        # setup the toolbar
        self.toolbar_box = NavigationToolbar(self.canvasBoxPlot)
        self.toolbar_box.Hide()

        # right click
        self.figureBoxPlot.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureBoxPlot.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasBoxPlot, self.rightDown_box)
        self.popmenu_box = wx.Menu()
        self.ID_POPUP_BOX_PAN = wx.NewId()
        self.ID_POPUP_BOX_ZOOM = wx.NewId()
        self.ID_POPUP_BOX_SAVE = wx.NewId()

        OnBox_pan = wx.MenuItem(self.popmenu_box, self.ID_POPUP_BOX_PAN, 'Pan')
        OnBox_zoom = wx.MenuItem(self.popmenu_box, self.ID_POPUP_BOX_ZOOM, 'Zooom')
        OnBox_save = wx.MenuItem(self.popmenu_box, self.ID_POPUP_BOX_SAVE, 'Save')
        self.popmenu_box.AppendItem(OnBox_pan)
        self.popmenu_box.AppendItem(OnBox_zoom)
        self.popmenu_box.AppendItem(OnBox_save)
        wx.EVT_MENU(self.popmenu_box, self.ID_POPUP_BOX_PAN, self.toolbar_box.pan)
        wx.EVT_MENU(self.popmenu_box, self.ID_POPUP_BOX_ZOOM, self.toolbar_box.zoom)
        wx.EVT_MENU(self.popmenu_box, self.ID_POPUP_BOX_SAVE, self.toolbar_box.save_figure)

        # double click
        wx.EVT_LEFT_DCLICK(self.canvasBoxPlot, self.toolbar_box.home)

        self.figureBoxPlot.tight_layout()
        self.canvasBoxPlot.draw()
        self.rightPanel.Layout()

    def rightDown_box(self, event):
        '''
        right down on figure
        '''
        if self.IN_AXES:
            self.pageBoxPlot.PopupMenu(self.popmenu_box, event.GetPosition())
        else:
            pass

    def DrawMaps(self):
        # draw the maps of the preview and error
        self.PlotPreview([[self.newModel.T1_cal_inRow], [self.newModel.T1_error], [self.newModel.T1_error_normalized],],

                                [['Calculated T1'], ['Error map of T1'], ['Normalized Error map of T1'],],

                                [['bone'], ['rainbow'], ['rainbow'], ],

                                [['T1[ms]'], ['Delta T1[ms]'], ['Normalized error[%]'],])

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

    def OnExport(self, event):
        '''
        export the files as .png, excel
        '''
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.SetStatusText('Exporting, please wait...')
            saveDir = dlg.GetPath()
            # export figures
            try:
                self.figureImagePreview.savefig(os.path.join(saveDir, 'maps.png'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return

            try:
                self.figureScatter.savefig(os.path.join(saveDir, 'scatters.png'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return

            try:
                self.figureHist_T1.savefig(os.path.join(saveDir, 'histogram.png'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return

            try:
                self.figureBoxPlot.savefig(os.path.join(saveDir, 'boxplot.png'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return

            # export to excel
            book = Workbook()
            sheetMean = book.add_sheet('Mean')
            sheetStd = book.add_sheet('Standard deviation')
            sheetMedian = book.add_sheet('Median')
            sheet1Qtl = book.add_sheet('1st quartiel')
            sheet3Qtl = book.add_sheet('3rd quartiel')
            sheetMin = book.add_sheet('Minimum')
            sheetMax = book.add_sheet('Maximum')
            sheetCov = book.add_sheet('Covariance')
            sheetCor = book.add_sheet('Correlation')
            sheetFit = book.add_sheet('Model fitting')
            sheetT = book.add_sheet('T-test results')
            sheetU = book.add_sheet('U-test results')
            sheetChiq = book.add_sheet('Chi-square-test results')
            # sheetA = book.add_sheet('ANOVA results')


            QIBA_functions.WriteToExcelSheet_T1_statistics(sheetMean, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_mean], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_T1_statistics(sheetStd, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_deviation], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_T1_statistics(sheetMedian, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_median], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_T1_statistics(sheet1Qtl, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_1stQuartile], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_T1_statistics(sheet3Qtl, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_3rdQuartile], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_T1_statistics(sheetMin, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_min], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_T1_statistics(sheetMax, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_max], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn)

            QIBA_functions.WriteToExcelSheet_T1_co(sheetCor, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.corr_T1T1], 1, self.nrOfRow, self.nrOfColumn)
            QIBA_functions.WriteToExcelSheet_T1_co(sheetCov, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.cov_T1T1], 1, self.nrOfRow, self.nrOfColumn)

            QIBA_functions.WriteToExcelSheet_T1_fit(sheetFit, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.a_lin_T1, self.newModel.b_lin_T1,self.newModel.a_log_T1,self.newModel.b_log_T1], 1, self.nrOfRow, self.nrOfColumn)

            QIBA_functions.WriteToExcelSheet_T1_test(sheetT, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_ttest_t, self.newModel.T1_cal_patch_ttest_p], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn, 'T-statistics')
            QIBA_functions.WriteToExcelSheet_T1_test(sheetU, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_Utest_u, self.newModel.T1_cal_patch_Utest_p], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn, 'U-value')
            QIBA_functions.WriteToExcelSheet_T1_test(sheetChiq, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_chisquare_c, self.newModel.T1_cal_patch_chisquare_p], int(self.nrOfRow/2), self.nrOfRow, self.nrOfColumn, 'Chiq')

            # QIBA_functions.WriteToExcelSheet_T1_A(sheetA, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_ANOVA_f,self.newModel.T1_cal_patch_ANOVA_p], 1, self.nrOfRow, self.nrOfColumn)
            try:
                book.save(os.path.join(saveDir, 'results.xls'))
            except:
                self.SetStatusText('Please close related files and try to export again.')
                return
            self.SetStatusText('Files are exported.')
        else:
            pass

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
    DEBUG = True
    if DEBUG:
        pass
    else:
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
        QIBASelectionDialog = MySelectionDialog(None, 'Please select which branch to enter:', 'Branch selection...', choices=['GKM', 'Flip Angle T1'])
        if QIBASelectionDialog.ShowModal() == wx.ID_OK:
            if QIBASelectionDialog.GetSelections() == 'GKM':
                window = MainWindow_KV("QIBA evaluate tool (GKM)")
            elif QIBASelectionDialog.GetSelections() == 'Flip Angle T1':
                window = MainWindow_T1("QIBA evaluate tool (Flip Angle T1)")
        else:
            exit(0)

    # show the application's main window
    window.Show()
    window.Maximize(True)
    Application.MainLoop()

