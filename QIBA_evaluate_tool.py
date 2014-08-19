 #!/usr/bin/env python

import os.path
import wx
import wx.richtext as rt
import dicom
import pylab
import numpy
from scipy import stats
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.ticker as ticker

class MainWindow(wx.Frame):
    '''
    this is the main window of the QIBA evaluate tool
    '''
    applicationName = "QIBA evaluate tool"
    # the list of evaluated models
    testedModels = []
    path_Ktrans_ref = ''
    path_Ve_ref = ''
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
        menubar = wx.MenuBar()

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

        menubar.Bind(wx.EVT_MENU, self.OnExport, OnExport)
        # menubar.Bind(wx.EVT_MENU, self.OnClearModelList, OnClearModelList)
        menubar.Bind(wx.EVT_MENU, self.OnLoadReferenceKtrans, OnLoadKtransRef)
        menubar.Bind(wx.EVT_MENU, self.OnLoadReferenceVe, OnLoadVeRef)
        menubar.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        menubar.Bind(wx.EVT_MENU, self.OnAbout, OnAboutApp)

        menubar.Append(fileMenu, "&File")
        menubar.Append(editMenu, "&Edit")
        menubar.Append(aboutMenu, "&About")
        self.SetMenuBar(menubar)

    def SetupLeft(self):
        '''
        set up the left panel.
        show the directories and files list to load calculated DICOMs
        '''
        self.selectedFilePath = ''
        # setup the tree control widget for file viewing and selection
        self.fileBrowser = wx.GenericDirCtrl(self.leftPanel, -1, dir = os.path.dirname(__file__), style=wx.DIRCTRL_SHOW_FILTERS,
                                filter="DICOM files (*.dcm)|*.dcm")
        self.fileBrowser.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.GetFilePath)

        # setup the right click function
        self.popupMenu = wx.Menu()
        itemLoadCalK = self.popupMenu.Append(-1, 'Load as calculated Ktrans')
        self.leftPanel.Bind(wx.EVT_MENU, self.OnPopupItemSelected, itemLoadCalK)
        itemLoadCalV = self.popupMenu.Append(-1, 'Load as calculated Ve')
        self.leftPanel.Bind(wx.EVT_MENU, self.OnPopupItemSelected, itemLoadCalV)

        self.leftPanel.Bind(wx.EVT_CONTEXT_MENU, self.OnShowPopup)

        # setup 'evaluate' and 'export result' buttons
        buttonEvaluate = wx.Button(self.leftPanel, wx.ID_ANY, 'Evaluate')
        buttonExport = wx.Button(self.leftPanel, wx.ID_ANY, 'Export result')
        self.Bind(wx.EVT_BUTTON, self.OnEvaluate, buttonEvaluate)
        self.Bind(wx.EVT_BUTTON, self.OnExport, buttonExport)

        sizerButton = wx.BoxSizer(wx.HORIZONTAL)
        sizerButton.Add(buttonEvaluate, 1, wx.ALIGN_LEFT)
        sizerButton.Add(buttonExport, 1, wx.ALIGN_RIGHT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.fileBrowser, 1, wx.EXPAND)
        sizer.Add(sizerButton)
        self.leftPanel.SetSizer(sizer)

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
        self.pageResult = wx.Panel(self.noteBookRight)
        self.noteBookRight.AddPage(self.pageImagePreview, "Image Viewer")
        self.noteBookRight.AddPage(self.pageScatter, "Scatter Plots Viewer")
        self.noteBookRight.AddPage(self.pageHistogram, "Histograms Plots Viewer")
        self.noteBookRight.AddPage(self.pageBoxPlot, "Box Plots Viewer")
        self.noteBookRight.AddPage(self.pageResult, "Result Text Viewer")

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
        sizer.Add(self.verticalLine, 1, wx.EXPAND)
        sizer.Add(self.canvasHist_Ve, 35, wx.EXPAND)
        self.pageHistogram.SetSizer(sizer)

        # page box plots
        self.figureBoxPlot = Figure()
        self.canvasBoxPlot = FigureCanvas(self.pageBoxPlot,-1, self.figureBoxPlot)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasBoxPlot, 1, wx.EXPAND)
        self.pageBoxPlot.SetSizer(sizer)

        # page evaluation results
        # self.resultPage = rt.RichTextCtrl(self, style = wx.VSCROLL|wx.NO_BORDER)
        self.resultPage = wx.TextCtrl(self.pageResult, -1, style = wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_RICH)

        sizer = wx.BoxSizer()
        sizer.Add(self.resultPage, 1, wx.EXPAND)
        self.pageResult.SetSizer(sizer)

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
        dlg = wx.FileDialog(self, 'Load reference Ktrans...', '', '', "DICOM file(*.dcm)|*.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_Ktrans_ref = dlg.GetPath()
            self.SetStatusText('Reference Ktrans loaded.')

    def OnLoadReferenceVe(self, event):
        # Import the reference Ve
        dlg = wx.FileDialog(self, 'Load reference Ve...', '', '', "DICOM file(*.dcm)|*.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_Ve_ref = dlg.GetPath()
            self.SetStatusText('Reference Ve loaded.')

    def OnLoadCalculatedKtrans(self):
        # load the selected DICOM as calculated Ktrans
        if os.path.splitext(self.selectedFilePath)[1] == '.dcm':
            self.path_Ktrans_cal = self.selectedFilePath
            self.SetStatusText('Calculated Ktrans loaded.')
        else:
            self.SetStatusText('Invalid file chosen.')

    def OnLoadCalculatedVe(self):
        # load the selected DICOM as calculated Ve
        if os.path.splitext(self.selectedFilePath)[1] == '.dcm':
            self.path_Ve_cal = self.selectedFilePath
            self.SetStatusText('Calculated Ve loaded.')
        else:
            self.SetStatusText('Invalid file chosen.')

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
        self.SetStatusText('Evaluating...')

        # create new model object to evaluated on
        self.newModel = ModelEvaluated()

        # call the method to execute evaluation
        if self.path_Ktrans_ref == '':
            self.SetStatusText('Please load a proper DICOM file as reference Ktrans.')
            return 0
        elif self.path_Ve_ref == '':
            self.SetStatusText('Please load a proper DICOM file as reference Ve.')
            return 0
        elif self.path_Ktrans_cal == '':
            self.SetStatusText('Please load a proper DICOM file as calculated Ktrans.')
            return 0
        elif self.path_Ve_cal == '':
            self.SetStatusText('Please load a proper DICOM file as calculated Ve.')
            return 0
        else:
            self.newModel.Evaluate(self.path_Ktrans_ref, self.path_Ve_ref, self.path_Ktrans_cal, self.path_Ve_cal)

        # show the results in the main window
        #print self.newModel.GetEvaluationResultText()
        self.resultPage.SetValue(self.newModel.GetEvaluationResultText())

        # push the new tested model to the list
        self.testedModels.append(self.newModel)

        # draw the figures
        self.ShowImagePreview()
        self.DrawScatterPlot()
        self.DrawHistograms()
        self.DrawBoxPlot()
        self.SetStatusText('Evaluation finished.')



    def OnSave(self, event):
        # Save the statistic data for recording
        print 'save result function needed to be added.'
        pass

    def ShowImagePreview(self):
        # show calculated images and the error images
        subplotK_Cal = self.figureImagePreview.add_subplot(2,3,1)
        handler = subplotK_Cal.imshow(self.newModel.Ktrans_cal_rescaled, cmap = 'bone', interpolation='nearest')
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
        handler = subplotV_Cal.imshow(self.newModel.Ve_cal_rescaled, cmap = 'bone', interpolation='nearest')
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
        plotRaw = subPlotK.scatter(self.newModel.Ktrans_ref_inPatch, self.newModel.Ktrans_ref_inPatch, color = 'g', alpha = 0.25, label = 'reference value')
        plotUniformed = subPlotK.scatter(self.newModel.Ktrans_ref_inPatch, self.newModel.Ktrans_cal_inPatch, color = 'b', alpha = 0.25, label = 'calculated value')
        # plotRef = subPlotK.scatter(self.pixelsTempRefK, self.pixelsTempRefK, color = 'r', alpha = 0.25, label = 'uniformed calculated value')
        subPlotK.legend(loc = 'upper left')
        subPlotK.set_xlabel('Reference Ktrans')
        subPlotK.set_ylabel('Calculated Ktrans')
        subPlotK.set_title('Distribution plot of Ktrans')

        subPlotV = self.figureScatter.add_subplot(2, 1, 2)
        subPlotV.clear()
        plotRaw = subPlotV.scatter(self.newModel.Ve_ref_inPatch, self.newModel.Ve_ref_inPatch, color = 'g', alpha = 0.25, label = 'reference value')
        plotUniformed = subPlotV.scatter(self.newModel.Ve_ref_inPatch, self.newModel.Ve_cal_inPatch, color = 'b', alpha = 0.25, label = 'calculated value')
        # plotRef = subPlotV.scatter(self.pixelsTempRefV, self.pixelsTempRefV, color = 'r', alpha = 0.25, label = 'uniformed calculated value')
        subPlotV.legend(loc = 'upper left')
        subPlotV.set_xlabel('Reference Ve')
        subPlotV.set_ylabel('Calculated Ve')
        subPlotV.set_title('Distribution plot of Ve')

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
            temp.extend(self.newModel.Ktrans_cal_inPatch[i])
            referValueK.append(self.newModel.Ktrans_ref_inPatch[i][0][0])
        subPlotK.boxplot(temp)

        subPlotK.set_title('Box plot of calculated Ktrans')
        subPlotK.set_xlabel('Patches\' number, concatenated row by row')
        subPlotK.set_ylabel('Calculated values in patches')

        # subPlotK.set_yticks(referValueK, minor = True)
        # locator = MultipleLocator(base = 5)
        # subPlotK.xaxis.set_major_locator(locator)
        # subPlotK.set_xticks([5.5, 10.5, 15.5, 20.5, 25.5, 30.5], minor = True)
        # subPlotK.grid(True, which = 'minor')

        subPlotV = self.figureBoxPlot.add_subplot(2, 1, 2)
        subPlotV.clear()
        temp = []
        referValueV = []
        for j in range(self.newModel.nrOfColumns):
            for i in range(self.newModel.nrOfRows):
                temp.append(self.newModel.Ve_cal_inPatch[i][j])
            referValueV.append(zip(*self.newModel.Ve_ref_inPatch)[j][0][0])
        subPlotV.boxplot(temp)

        subPlotV.set_title('Box plot of calculated Ve')
        subPlotV.set_xlabel('Patches\' number, concatenated column by column')
        subPlotV.set_ylabel('Calculated values in patches')
        # subPlotV.set_yticks(referValueV, minor = True)
        # subPlotV.set_xticks([6.5, 12.5, 18.5, 24.5, 30.5], minor = True)
        # subPlotV.grid(True, which = 'minor')


        subPlotK.xaxis.set_major_formatter(ticker.NullFormatter())
        subPlotK.xaxis.set_minor_locator(ticker.FixedLocator([3, 8, 13, 18, 23, 28]))
        subPlotK.xaxis.set_minor_formatter(ticker.FixedFormatter(['Ktrans = ' + str(referValueK[0]), 'Ktrans = ' + str(referValueK[1]), 'Ktrans = ' + str(referValueK[2]), 'Ktrans = ' + str(referValueK[3]), 'Ktrans = ' + str(referValueK[4]), 'Ktrans = ' + str(referValueK[5])]))
        for i in range(self.newModel.nrOfRows):
            subPlotK.axvline(x = self.newModel.nrOfColumns * i + 0.5, color = 'green', linestyle = 'dashed')


        subPlotV.xaxis.set_major_formatter(ticker.NullFormatter())
        subPlotV.xaxis.set_minor_locator(ticker.FixedLocator([3.5, 9.5, 15.5, 21.5, 27.5]))
        subPlotV.xaxis.set_minor_formatter(ticker.FixedFormatter(['Ve = ' + str(referValueV[0]), 'Ve = ' + str(referValueV[1]), 'Ve = ' + str(referValueV[2]), 'Ve = ' + str(referValueV[3]), 'Ve = ' + str(referValueV[4])]))
        for i in range(self.newModel.nrOfColumns):
            subPlotV.axvline(x = self.newModel.nrOfRows * i + 0.5, color = 'green', linestyle = 'dashed')



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
                subPlot_K.hist(self.newModel.Ktrans_cal_inPatch[i][j], nrOfBins)
                minPatch_K = numpy.min(self.newModel.Ktrans_cal_inPatch[i][j])
                maxPatch_K = numpy.max(self.newModel.Ktrans_cal_inPatch[i][j])
                meanPatch_K = numpy.mean(self.newModel.Ktrans_cal_inPatch[i][j])
                subPlot_K.set_xticks([minPatch_K, maxPatch_K])
                subPlot_K.set_xticklabels([str(minPatch_K), str(maxPatch_K)])
                subPlot_K.axvline(meanPatch_K, color = 'r', linestyle = 'dashed', linewidth = 1) # draw a vertical line at the mean value
                subPlot_K.set_ylim([0, pixelCountInPatch])
                subPlot_K.text(meanPatch_K + 0.01 * meanPatch_K, 0.9 * pixelCountInPatch, str(meanPatch_K), size = 'x-small') # parameters: location_x, location_y, text, size
                if i == 0:
                    subPlot_K.set_xlabel('Ve = ' + str(self.newModel.Ve_ref_inPatch[i][j][0]))
                    subPlot_K.xaxis.set_label_position('top')
                if j == 0:
                    subPlot_K.set_ylabel('Ktrans = ' + str(self.newModel.Ktrans_ref_inPatch[i][j][0]))

                subPlot_V = self.figureHist_Ve.add_subplot(self.newModel.nrOfRows, self.newModel.nrOfColumns, i * self.newModel.nrOfColumns + j + 1 )
                # subPlot_V.clear()
                subPlot_V.hist(self.newModel.Ve_cal_inPatch[i][j], nrOfBins)
                minPatch_V = numpy.min(self.newModel.Ve_cal_inPatch[i][j])
                maxPatch_V = numpy.max(self.newModel.Ve_cal_inPatch[i][j])
                meanPatch_V = numpy.mean(self.newModel.Ve_cal_inPatch[i][j])
                subPlot_V.set_xticks([minPatch_V, maxPatch_V])
                subPlot_V.set_xticklabels([str(minPatch_V), str(maxPatch_V)])
                subPlot_V.axvline(meanPatch_V, color = 'r', linestyle = 'dashed', linewidth = 1) # draw a vertical line at the mean value
                subPlot_V.set_ylim([0, pixelCountInPatch])
                subPlot_V.text(meanPatch_V + 0.01 * meanPatch_V, 0.9 * pixelCountInPatch, str(meanPatch_V), size = 'x-small') # parameters: location_x, location_y, text, size
                if i == 0:
                    subPlot_V.set_xlabel('Ve = ' + str(self.newModel.Ve_ref_inPatch[i][j][0]))
                    subPlot_V.xaxis.set_label_position('top')
                if j == 0:
                    subPlot_V.set_ylabel('Ktrans = ' + str(self.newModel.Ktrans_ref_inPatch[i][j][0]))


        self.figureHist_Ve.tight_layout()
        self.figureHist_Ktrans.tight_layout()

        self.figureHist_Ktrans.subplots_adjust(top = 0.94, right = 0.95)
        self.figureHist_Ve.subplots_adjust(top = 0.94, right = 0.95)

        self.canvasHist_Ktrans.draw()
        self.canvasHist_Ve.draw()

    def Draw3DPlot(self):
        '''
        Not used now.
        plot 3D bars, so that a distribution view of the standard deviation can be referred to for different K,V combination
        '''
        subPlotK3D = self.figure3D.add_subplot(2, 1, 1, projection = '3d')
        subPlotK3D.clear()
        for i in range(self.calK.nrOfRows):
            xs = range(self.calK.nrOfColumns)
            ys = self.deviationK[i]
            subPlotK3D.bar(xs, ys, zs = i, zdir = 'x', alpha = 0.8)
        subPlotK3D.set_xlabel('Ktrans')
        subPlotK3D.set_ylabel('Ve')
        subPlotK3D.set_zlabel('Standard deviation of calculated data')
        subPlotK3D.set_title('Distribution of standard deviation of the calculated Ktrans')

        subPlotV3D = self.figure3D.add_subplot(2, 1, 2, projection = '3d')
        subPlotV3D.clear()
        for i in range(self.calV.nrOfRows):
            xs = range(self.calV.nrOfColumns)
            ys = self.deviationV[i]
            subPlotV3D.bar(xs, ys, zs = i, zdir = 'x', alpha = 0.8)
        subPlotV3D.set_xlabel('Ktrans')
        subPlotV3D.set_ylabel('Ve')
        subPlotV3D.set_zlabel('Standard deviation of calculated data')
        subPlotV3D.set_title('Distribution of standard deviation of the calculated Ve')

        self.canvas3D.draw()
        self.rightPanel.Layout()

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
        self.figureScatter.clear() # page 1
        self.canvasScatter.draw()
        self.figureBoxPlot.clear() # page 3
        self.canvasBoxPlot.draw()
        self.figureHist_Ktrans.clear() # page 2
        self.canvasHist_Ktrans.draw()
        self.figureHist_Ve.clear()
        self.canvasHist_Ve.draw()
        self.resultPage.SetValue('') # page 4

    def ClearPanel(self, panel):
        # clear a panel object(from wxPython)
        for child in panel.GetChildren():
            if child:
                child.Destroy()
            else:
                pass

    def OnExport(self, event):
        # export the evaluation result to pdf file.
        print "TODO: add export function"

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
        self.rescaleIntercept = 0
        self.rescaleSlope = 1
        self.METHOD = '' # for patch value decision

        # the raw image data as pixel flow
        self.Ktrans_ref_raw = []
        self.Ve_ref_raw = []
        self.Ktrans_cal_raw = []
        self.Ve_cal_raw = []

        # the error map between calculated and reference file
        self.Ktrans_error = []
        self.Ve_error = []
        self.Ktrans_error_normalized = []
        self.Ve_error_normalized = []

        # the rescaled image data
        self.Ktrans_ref_rescaled = []
        self.Ve_ref_rescaled = []
        self.Ktrans_cal_rescaled = []
        self.Ve_cal_rescaled = []

        # the rearranged image in patches
        self.Ktrans_ref_inPatch = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]
        self.Ve_ref_inPatch = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]
        self.Ktrans_cal_inPatch = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]
        self.Ve_cal_inPatch = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]

        # the mean value(or median value) matrix of a calculated image
        self.Ktrans_ref_patchValue = [[]for i in range(self.nrOfRows)]
        self.Ve_ref_patchValue = [[]for i in range(self.nrOfRows)]
        self.Ktrans_cal_patchValue = [[]for i in range(self.nrOfRows)]
        self.Ve_cal_patchValue = [[]for i in range(self.nrOfRows)]

        # planar fitting parameters
        self.Ktrans_fittingParameter = []
        self.Ve_fittingParameter = []

        # the result text
        self.resultText = ''

    def Evaluate(self, path_K_ref, path_V_ref, path_K_cal, path_V_cal):
        # do evaluation
        # pre-process for the imported DICOMs
        self.ImportDICOMs(path_K_ref, path_V_ref, path_K_cal, path_V_cal)
        self.RescaleImportedDICOMs()
        self.CalculateErrorForImportedDICOMs()
        self.RearrangeImportedDICOMs()
        self.EstimatePatchForImportedDICOMs('MEAN')

        # evaluation operations
        self.FittingPlanarForImportedDICOMs()
        self.CalculateCorrelation()

        # write the result to the result text
        self.TextResult()

    def TextResult(self):
        # write the results into text form
        tempResultKtrans = ''
        tempResultVe = ''

        tempResultKtrans += '********************************************\n' \
                            'The result for calculated Ktrans map: \n' \
                            '********************************************\n'
        tempResultKtrans += 'Planar fitting:\n'
        tempResultKtrans += 'Ktrans_cal = ' + str(self.a_Ktrans) + '  * Ktrans_ref + ' + str(self.b_Ktrans) + ' * Ve_ref + ' + str(self.c_Ktrans) + '\n\n'
        tempResultKtrans += 'Correlation:\n'
        for j in range(self.nrOfColumns):
            tempResultKtrans += 'The correlation between ' + str(j + 1) + 'th column of calculated Ktrans and reference Ktrans is: ' + str(self.Corre_KK[j]) + '\n'
        tempResultKtrans += '\n'
        for i in range(self.nrOfRows):
            tempResultKtrans += 'The correlation between ' + str(i + 1) + 'th row of calculated Ktrans and reference Ve is: ' + str(self.Corre_KV[i]) + '\n'
        tempResultKtrans += '\n'

        tempResultVe += '********************************************\n' \
                            'The result for calculated Ve map: \n' \
                            '********************************************\n'
        tempResultVe += 'Planar fitting:\n'
        tempResultVe += 'Ve_cal = ' + str(self.a_Ve) + ' * Ktrans_ref + ' + str(self.b_Ve) + ' * Ve_ref + ' + str(self.c_Ve) + '\n\n'
        tempResultVe += 'Correlation:\n'
        for i in range(self.nrOfRows):
            tempResultVe += 'The correlation between ' + str(i + 1) + 'th row of calculated Ktrans and reference Ve is: ' + str(self.Corre_VV[i]) + '\n'
        tempResultVe += '\n'
        for j in range(self.nrOfColumns):
            tempResultVe += 'The correlation between ' + str(j + 1) + 'th column of calculated Ve and reference Ktrans is: ' + str(self.Corre_VK[j]) + '\n'
        tempResultVe += '\n'


        self.resultText += tempResultKtrans
        self.resultText += tempResultVe

    def GetEvaluationResultText(self):
        # getter for the result text.
        return self.resultText

    def ImportDICOMs(self, path_K_ref, path_V_ref, path_K_cal, path_V_cal):
        # import the DICOM files for evaluation.
        self.Ktrans_ref_raw = self.ImportDICOM(path_K_ref)
        self.Ve_ref_raw = self.ImportDICOM(path_V_ref)
        self.Ktrans_cal_raw = self.ImportDICOM(path_K_cal)
        self.Ve_cal_raw = self.ImportDICOM(path_V_cal)

    def RescaleImportedDICOMs(self):
        # rescale the imported DICOM files
        self.Ktrans_ref_rescaled = self.Rescale(self.Ktrans_ref_raw)
        self.Ve_ref_rescaled = self.Rescale(self.Ve_ref_raw)
        self.Ktrans_cal_rescaled = self.Rescale(self.Ktrans_cal_raw)
        self.Ve_cal_rescaled = self.Rescale(self.Ve_cal_raw)

    def CalculateErrorForImportedDICOMs(self):
        # calculate the error between calculated and reference files
        self.Ktrans_error = self.CalculateError(self.Ktrans_ref_rescaled, self.Ktrans_cal_rescaled)
        self.Ve_error = self.CalculateError(self.Ve_ref_rescaled, self.Ve_cal_rescaled)

        self.Ktrans_error_normalized = self.CalculateNormalizedError(self.Ktrans_ref_rescaled, self.Ktrans_cal_rescaled)
        self.Ve_error_normalized = self.CalculateNormalizedError(self.Ve_ref_rescaled, self.Ve_cal_rescaled)

    def RearrangeImportedDICOMs(self):
        # rearrange the patched for each the imported DICOM
        self.Ktrans_ref_inPatch = self.Rearrange(self.Ktrans_ref_rescaled)
        self.Ve_ref_inPatch = self.Rearrange(self.Ve_ref_rescaled)
        self.Ktrans_cal_inPatch = self.Rearrange(self.Ktrans_cal_rescaled)
        self.Ve_cal_inPatch = self.Rearrange(self.Ve_cal_rescaled)

    def EstimatePatchForImportedDICOMs(self, patchValueMethod):
        # estimate the value to represent the patches for each imported DICOM
        self.Ktrans_ref_patchValue = self.EstimatePatch(self.Ktrans_ref_inPatch, patchValueMethod)
        self.Ve_ref_patchValue = self.EstimatePatch(self.Ve_ref_inPatch, patchValueMethod)
        self.Ktrans_cal_patchValue = self.EstimatePatch(self.Ktrans_cal_inPatch, patchValueMethod)
        self.Ve_cal_patchValue = self.EstimatePatch(self.Ve_cal_inPatch, patchValueMethod)

    def FittingPlanarForImportedDICOMs(self):
        # fit a planar for the calculated Ktrans and Ve maps
        self.a_Ktrans, self.b_Ktrans, self.c_Ktrans = self.FittingPlanar(self.Ktrans_cal_patchValue)
        self.a_Ve, self.b_Ve, self.c_Ve = self.FittingPlanar(self.Ve_cal_patchValue)

    def CalculateCorrelation(self):
        # calculate the correlation between the calculated parameters and the reference parameters
        # 'Corre_KV' stands for 'correlation coefficient between calculate Ktrans and reference Ve', etc.
        self.Corre_KK = []
        self.Corre_VV = []
        self.Corre_KV = []
        self.Corre_VK = []

        for i in range(self.nrOfColumns):
            self.Corre_KK.append(self.CalCorrMatrix(zip(*self.Ktrans_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
            self.Corre_VK.append(self.CalCorrMatrix(zip(*self.Ve_cal_patchValue)[i], zip(*self.Ktrans_ref_patchValue)[i])[0][1])
        for j in range(self.nrOfRows):
            self.Corre_VV.append(self.CalCorrMatrix(self.Ve_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])
            self.Corre_KV.append(self.CalCorrMatrix(self.Ktrans_cal_patchValue[j], self.Ve_ref_patchValue[j])[0][1])

    def ImportDICOM(self, path):
        # import a DICOM file(reference or calculated)
        # it should be able to deal with different data type like DICOM, binary and so on. right now it's possible for DICOM
        try:
            return  dicom.read_file(path)
        except:
            wx.MessageBox('Invalid file path!\n' + '(' + path +')', 'Cannot import file', wx.OK | wx.ICON_INFORMATION)

    def Rescale(self, ds):
        # rescale the DICOM file to remove the intercept and the slope. the 'pixel' in DICOM file means a row of pixels.
        try:
            self.rescaleIntercept = ds.RescaleIntercept
            self.rescaleSlope = ds.RescaleSlope
        except:
            pass
        pixelFlow = []
        for row in ds.pixel_array:
            temp = []
            for pixel in row:
                temp.append(pixel * self.rescaleSlope + self.rescaleIntercept)
            pixelFlow.append(temp)

        # remove the first and last row which do not contain valid data
        pixelFlow = pixelFlow[self.patchLen:-self.patchLen]

        return pixelFlow

    def CalculateError(self, cal, ref):
        # compare the calculated and reference files, and return the error
        errorCalRef = []

        for row_cal, row_ref in zip(cal, ref):
            temp = []
            for pixel_cal, pixel_ref in zip(row_cal, row_ref):
                temp.append(pixel_cal - pixel_ref)
            errorCalRef.append(temp)
        return errorCalRef

    def CalculateNormalizedError(self, cal, ref):
        # compare the calculated and reference files, and return the error
        errorNormalized = []
        delta = 0.0001 # to avoid dividing zero

        for row_cal, row_ref in zip(cal, ref):
            temp = []
            for pixel_cal, pixel_ref in zip(row_cal, row_ref):
                temp.append((pixel_cal - pixel_ref) / (pixel_ref + delta))
            errorNormalized.append(temp)
        return errorNormalized

    def Rearrange(self, pixelFlow):
        # rearrange the DICOM file so that the file can be accessed in patches and the top and bottom strips are removed as they are not used here.
        tempAll = []
        tempPatch = []
        tempRow = []
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                for k in range(self.patchLen):
                    tempPatch.extend(pixelFlow[i * self.patchLen + k][j * self.patchLen : (j + 1) * self.patchLen])
                tempRow.append(tempPatch)
                tempPatch = []
            tempAll.append(tempRow)
            tempRow = []
        return tempAll

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

    def FittingPlanar(self, calculatedPatchValue):
        # fitting the planar with 3D data, i.e. Ktrans_ref, Ve_ref, Ktrans_cal(Ve_cal). So that the parameter dependency could be seen
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
                xCurrent = self.Ktrans_ref_inPatch[i][j][0]
                yCurrent = self.Ve_ref_inPatch[i][j][0]
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

    def CalCorrMatrix(self, calculatedPatchValue, referencePatchValue):
        # calculate the correlation matrix of the calculated and reference DICOMs
        return numpy.corrcoef(calculatedPatchValue, referencePatchValue)

    def Score(self):
        # give a score for evaluation according to the weighting factors.
        pass

class WindowShowHistogram(wx.Frame, ModelEvaluated):
    '''
    the second window that shows up when the "process" button is pressed. In this window, the histogram of each patch will be shown,
    so that the user can see the distribution of the patches and decide which one(mean or median value) to choose to represent
    each patch.
    '''

    def __init__(self, parent, ModelEvaluated):
        # initialize the second window
        wx.Frame.__init__(self, parent, title = 'Mean value or median value...', size = wx.DisplaySize())
        self.leftPanel = wx.Panel(self)
        self.rightPanel = wx.Panel(self)

        # figure for histogram, Ktrans cal.
        self.figureHistogram_K = Figure()
        self.figureCanvas_K = FigureCanvas(self, -1, self.figureHistogram_K)

        # figure for histogram, Ktrans cal.
        self.figureHistogram_V = Figure()
        self.figureCanvas_V = FigureCanvas(self, -1, self.figureHistogram_V)

        # set sizer for the figures
        sizer = wx.BoxSizer()
        sizer.Add(self.figureCanvas_K, 1, border = 5, flag =wx.EXPAND)
        sizer.Add(self.figureCanvas_V, 1, border = 5, flag= wx.EXPAND)
        #sizer.Add(self.figureCanvas_V, 1, wx.EXPAND)
        self.leftPanel.SetSizer(sizer)

        # instruction text for choosing method
        #text = wx.StaticText(self.rightPanel, -1, 'You can choose one method, so that the corresponding value can represent the patch.' ) #, (100,10))

        # button configuration
        buttonMean = wx.Button(self.rightPanel, wx.ID_ANY, 'Mean value')
        buttonMedian = wx.Button(self.rightPanel, wx.ID_ANY, 'Median value')

        self.Bind(wx.EVT_BUTTON, self.OnClickMean, buttonMean)
        self.Bind(wx.EVT_BUTTON, self.OnClickMedian, buttonMedian)

        sizer = wx.GridSizer(cols = 1)
        #sizer.Add(text)
        sizer.Add(buttonMean)
        sizer.Add(buttonMedian)
        self.rightPanel.SetSizer(sizer)

        # set sizer for the
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.leftPanel, 8, wx.EXPAND)
        sizer.Add(self.rightPanel, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.K_ref = ModelEvaluated.Ktrans_ref_inPatch
        self.K_cal = ModelEvaluated.Ktrans_cal_inPatch
        self.V_ref = ModelEvaluated.Ve_ref_inPatch
        self.V_cal = ModelEvaluated.Ve_cal_inPatch

        self.nrOfRows = ModelEvaluated.nrOfRows
        self.nrOfColumns = ModelEvaluated.nrOfColumns

        self.PlotHistogram()

    def OnClickMean(self, event):
        # when click on 'mean' button
        ModelEvaluated.METHOD = 'MEAN'
        self.Close()

    def OnClickMedian(self, event):
        # when click on 'median' button
        ModelEvaluated.METHOD = 'MEDIAN'
        self.Close()

    def PlotHistogram(self):
        # plot the histogram to illustrate the value distribution of each patch, so that the user can choose the method accordingly.

        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                subPlot_K = self.figureHistogram_K.add_subplot(self.nrOfRows, self.nrOfColumns, i * self.nrOfColumns + (j * 1) )
                subPlot_K.clear()
                nrOfBins = 10
                subPlot_K.hist(self.K_cal[i][j], nrOfBins)

                subPlot_V = self.figureHistogram_V.add_subplot(self.nrOfRows, self.nrOfColumns, i * self.nrOfColumns + (j * 1) )
                subPlot_V.clear()
                nrOfBins = 10
                subPlot_V.hist(self.V_cal[i][j], nrOfBins)

                #subPlotK.step(patches, 'facecolor', 'g', 'alpha', 0.75)
                # subPlotK.set_title = 'Ktrans=' + str(self.K_ref[i][j][0]) + ', Ve=' + str(self.V_ref[i][j][0])
                #subPlotK.set_xlabel('Calculated value')
                #subPlotK.set_ylabel('Counting number')

        self.figureHistogram_K.tight_layout()
        self.figureHistogram_V.tight_layout()

class MySplashScreen(wx.SplashScreen):
    '''
    show the splash screen when the application is launched.
    '''
    def  __init__(self, parent=None):
        # This is a recipe to a the screen.
        # Modify the following variables as necessary.
        aBitmap = wx.Image(name = "splashImage.jpg").ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 3000 # milliseconds
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle, splashDuration, parent)



if __name__ == "__main__":
    # show the application's main window

    Application = wx.App()
    QIBASplashWindow = MySplashScreen()
    QIBASplashWindow.Show()

    window = MainWindow(None)
    window.Show()
    window.Maximize(True)
    Application.MainLoop()
