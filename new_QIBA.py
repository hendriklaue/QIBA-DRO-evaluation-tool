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
from sys import exit
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

    def __init__(self, parent, BRANCH):
        wx.Frame.__init__(self, parent, title = self.applicationName, size = (wx.SYS_SCREEN_X, wx.SYS_SCREEN_Y))

        # default file paths
        self.path_Ktrans_ref = os.path.join(os.getcwd(), 'reference_data', 'Ktrans.dcm')
        self.path_Ve_ref = os.path.join(os.getcwd(), 'reference_data', 'Ve.dcm')
        self.path_Ktrans_cal = ''
        self.path_Ve_cal = ''
        self.path_T1_ref = os.path.join(os.getcwd(), 'reference_data', 'T1.dcm')
        self.path_T1_cal = ''

        # decide the interface according to the BRANCH
        if BRANCH == 'Ktrans-Ve':
            self.EditMenuItemList = ['Load new reference Ktrans...', 'Load new reference Ve...']
            self.PopupMenuItemList = ['Load as cal. Ktrans', 'Load as cal. Ve']
            self.applicationName = "QIBA evaluate tool (Ktrans-Ve)"
        elif BRANCH == 'T1':
            self.EditMenuItemList = ['Load new reference T1...']
            self.PopupMenuItemList = ['Load as cal. T1']
            self.applicationName = "QIBA evaluate tool (T1)"

        self.CenterOnScreen()

        self.CreateStatusBar()
        self.SetStatusText("Welcome to " + self.applicationName + "!")

        self.SetupMenubar(BRANCH)

        self.SetupLayoutMain(BRANCH)

    def SetupMenubar(self, BRANCH):
        '''
        set up the menu bar
        '''
        self.menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        OnExport = fileMenu.Append(wx.ID_ANY, "&Export the results...\tCtrl+E", "Export the result as PDF/EXCEL file.")
        fileMenu.AppendSeparator()
        OnExit = fileMenu.Append(wx.ID_ANY, "&Quit\tCtrl+Q", "Quit " + self.applicationName)

        editMenu = wx.Menu()
        if BRANCH == 'Ktrans-Ve':
            OnLoadKtransRef = editMenu.Append(wx.ID_ANY, "Load reference Ktrans...")
            OnLoadVeRef = editMenu.Append(wx.ID_ANY, "Load reference Ve...")
            self.menubar.Bind(wx.EVT_MENU, self.OnLoadReferenceKtrans, OnLoadKtransRef)
            self.menubar.Bind(wx.EVT_MENU, self.OnLoadReferenceVe, OnLoadVeRef)
        elif BRANCH == 'T1':
            OnLoadT1Ref = editMenu.Append(wx.ID_ANY, "Load reference T1...")
            self.menubar.Bind(wx.EVT_MENU, self.OnLoadReferenceT1, OnLoadT1Ref)

        aboutMenu = wx.Menu()
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

        self.menubar.Bind(wx.EVT_MENU, self.OnExport, OnExport)
        self.menubar.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        self.menubar.Bind(wx.EVT_MENU, self.OnAbout, OnAboutApp)

        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(editMenu, "&Edit")
        self.menubar.Append(aboutMenu, "&About")
        self.SetMenuBar(self.menubar)

    def SetupLayoutMain(self, BRANCH):
        '''
        set up the main window
        '''
        self.leftPanel = wx.Panel(self)
        self.rightPanel = wx.Panel(self)

        self.SetupLeft(BRANCH)
        self.SetupRight(BRANCH)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.leftPanel, 2, flag = wx.EXPAND)  # second argument being 0 to make sure that it wont expand
        sizer.Add(self.rightPanel, 7, flag = wx.EXPAND)
        self.SetSizer(sizer)

    def SetupLeft(self, BRANCH):
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
        if BRANCH == 'Ktrans-Ve':
            itemLoadCalK = self.popupMenu.Append(-1, 'Load as calculated Ktrans')
            self.leftPanel.Bind(wx.EVT_MENU, self.OnPopupItemSelected, itemLoadCalK)
            itemLoadCalV = self.popupMenu.Append(-1, 'Load as calculated Ve')
            self.leftPanel.Bind(wx.EVT_MENU, self.OnPopupItemSelected, itemLoadCalV)
        else:
            itemLoadT1 = self.popupMenu.Append(-1, 'Load as calculated T1')
            self.leftPanel.Bind(wx.EVT_MENU, self.OnPopupItemSelected, itemLoadT1)

        # right click action to popup menu
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
        else:
            self.OnLoadCalculatedT1()

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

    def OnLoadReferenceT1(self, event):
        # Import the reference T1
        dlg = wx.FileDialog(self, 'Load reference T1...', '', '', "DICOM files (*.dcm)|*.dcm|Binary files (*.bin *.raw )|*.bin;*.raw", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_T1_ref = dlg.GetPath()
            self.SetStatusText('Reference T1 loaded.')
        else:
            self.SetStatusText('Reference T1 was NOT loaded!')

    def OnLoadCalculatedT1(self):
        # load the selected file as calculated Ktrans
        if os.path.splitext(self.selectedFilePath)[1] == '.dcm' or '.bin' or '.raw':
            self.path_T1_cal = self.selectedFilePath
            self.SetStatusText('Calculated T1 loaded.')
        else:
            self.SetStatusText('Invalid file or path chosen.')

        # enable the evaluate button when the paths are valid
        if self.path_T1_cal:
            self.buttonEvaluate.Enable()

    def OnLoadCalculatedKtrans(self):
        # load the selected file as calculated Ktrans
        if os.path.splitext(self.selectedFilePath)[1] == '.dcm' or '.bin' or '.raw':
            self.path_Ktrans_cal = self.selectedFilePath
            self.SetStatusText('Calculated Ktrans loaded.')
        else:
            self.SetStatusText('Invalid file or path chosen.')

        # enable the evaluate button when the paths are valid
        if self.path_Ktrans_cal and self.path_Ve_cal:
            self.buttonEvaluate.Enable()

    def OnLoadCalculatedVe(self):
        # load the selected file as calculated Ve
        if os.path.splitext(self.selectedFilePath)[1] == '.dcm' or '.bin' or '.raw':
            self.path_Ve_cal = self.selectedFilePath
            self.SetStatusText('Calculated Ve loaded.')
        else:
            self.SetStatusText('Invalid file or path chosen.')

        # enable the evaluate button when the paths are valid
        if self.path_Ktrans_cal and self.path_Ve_cal:
            self.buttonEvaluate.Enable()

    def GetFilePath(self, event):
        # copy the selected file's path for loading it
        if self.fileBrowser.GetFilePath():
            self.selectedFilePath = self.fileBrowser.GetFilePath()

    def SetupRight(self, BRANCH):
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

    def OnEvaluate(self, event):
        # start to evaluate
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
        folderPath = os.path.join(os.getcwd(), 'temp')
        for theFile in os.listdir(folderPath):
            os.remove(os.path.join(folderPath, theFile))

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


class MainWindow_KV(MainWindow):
    '''
    this is the Ktrans-Ve branch's interface.
    '''
    def __init__(self, wx,Frame):
        MainWindow.__init__(self, wx.Frame, 'Ktrans-Ve')

        # default reference files
        self.path_Ktrans_ref = os.path.join(os.getcwd(), 'reference_data', 'Ktrans.dcm')
        self.path_Ve_ref = os.path.join(os.getcwd(), 'reference_data', 'Ve.dcm')
        self.path_Ktrans_cal = ''
        self.path_Ve_cal = ''

class MainWindow_T1(MainWindow):
    '''
    this is the Ktrans-Ve branch's interface.
    '''
    def __init__(self, wx,Frame):
        MainWindow.__init__(self, wx.Frame, 'T1')


        # default reference files
        self.path_T1_ref = os.path.join(os.getcwd(), 'reference_data', 'T1.dcm')
        self.path_T1_cal = ''

class MainWindow_KV(wx.Frame):
    '''
    this is the main window of the QIBA evaluate tool
    '''
    applicationName = "QIBA evaluate tool(Ktrans-Ve)"

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
            self.SetStatusText('Invalid file or path chosen.')

        # enable the evaluate button when the paths are valid
        if self.path_Ktrans_cal and self.path_Ve_cal:
            self.buttonEvaluate.Enable()

    def OnLoadCalculatedVe(self):
        # load the selected DICOM as calculated Ve
        if os.path.splitext(self.selectedFilePath)[1] == '.dcm' or '.bin' or '.raw':
            self.path_Ve_cal = self.selectedFilePath
            self.SetStatusText('Calculated Ve loaded.')
        else:
            self.SetStatusText('Invalid file or path chosen.')

        # enable the evaluate button when the paths are valid
        if self.path_Ktrans_cal and self.path_Ve_cal:
            self.buttonEvaluate.Enable()

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
        self.newModel = QIBA_model.Model_KV()
        #EvaluateProgressDialog.Update(10)

        # # make sure the import path is valid
        # if not self.newModel.ImportFile(self.path_Ktrans_ref):
        #     self.SetStatusText('Please load a proper file as reference Ktrans.')
        #     return False
        #
        # if not self.newModel.ImportFile(self.path_Ve_ref):
        #     self.SetStatusText('Please load a proper file as reference Ve.')
        #     return False
        #
        # if not self.newModel.ImportFile(self.path_Ktrans_cal):
        #     self.SetStatusText('Please load a proper file as calculated Ktrans.')
        #     return False
        #
        # if not self.newModel.ImportFile(self.path_Ve_cal):
        #     self.SetStatusText('Please load a proper file as calculated ve.')
        #     return False
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

                minPatch_K = QIBA_functions.formatFloatTo2DigitsString(minPatch_K)
                maxPatch_K = QIBA_functions.formatFloatTo2DigitsString(maxPatch_K)
                meanPatch_K = QIBA_functions.formatFloatTo2DigitsString(meanPatch_K)

                subPlot_K.set_xticks([float(minPatch_K), float(maxPatch_K)])

                subPlot_K.set_xticklabels([minPatch_K, maxPatch_K])
                subPlot_K.axvline(float(meanPatch_K), color = 'r', linestyle = 'dashed', linewidth = 1) # draw a vertical line at the mean value
                subPlot_K.set_ylim([0, pixelCountInPatch])
                subPlot_K.text(float(meanPatch_K) + 0.01 * float(meanPatch_K), 0.9 * pixelCountInPatch, meanPatch_K, size = 'x-small') # parameters: location_x, location_y, text, size
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
                minPatch_V = QIBA_functions.formatFloatTo2DigitsString(minPatch_V)
                maxPatch_V = QIBA_functions.formatFloatTo2DigitsString(maxPatch_V)
                meanPatch_V = QIBA_functions.formatFloatTo2DigitsString(meanPatch_V)

                subPlot_V.set_xticks([float(minPatch_V), float(maxPatch_V)])
                subPlot_V.set_xticklabels([minPatch_V, maxPatch_V])
                subPlot_V.axvline(float(meanPatch_V), color = 'r', linestyle = 'dashed', linewidth = 1) # draw a vertical line at the mean value
                subPlot_V.set_ylim([0, pixelCountInPatch])
                subPlot_V.text(float(meanPatch_V) + 0.01 * float(meanPatch_V), 0.9 * pixelCountInPatch, meanPatch_V, size = 'x-small') # parameters: location_x, location_y, text, size
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
        folderPath = os.path.join(os.getcwd(), 'temp')
        for theFile in os.listdir(folderPath):
            os.remove(os.path.join(folderPath, theFile))

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

class MainWindow_T1(wx.Frame):

    applicationName = "QIBA evaluate tool"
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title = self.applicationName, size = (wx.SYS_SCREEN_X, wx.SYS_SCREEN_Y))

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
        self.showUpCheckBox = wx.CheckBox(self, -1, 'Do not show this dialog any more when start.')
        self.buttons = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)

        sizer.Add(self.branchChoices, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.showUpCheckBox, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.buttons, 1, wx.ALL | wx.EXPAND, 5)
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

    # the branch selection dialog
    QIBASelectionDialog = MySelectionDialog(None, 'Please select which branch to enter:', 'Branch selection...', choices=['Ktrans-Ve', 'T1'])

    if QIBASelectionDialog.ShowModal() == wx.ID_OK:
        if QIBASelectionDialog.GetSelections() == 'Ktrans-Ve':
            window = MainWindow_KV(None)
        else:
            window = MainWindow_T1(None)
    else:
        exit(0) # quit the application

    # show the application's main window
    window.Show()
    window.Maximize(True)
    Application.MainLoop()

