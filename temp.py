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
    # the list of models to evaluate on
    testedModels = []

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title = self.applicationName, size = wx.DisplaySize()) #size = (900, 600)

        #self.SetMinSize((900, 600))
        self.CenterOnScreen()

        self.CreateStatusBar()
        self.SetStatusText("Welcome to " + self.applicationName + "!")

        self.SetupMenubar()

        self.SetupLayoutMain()

        self.InitModel()

    def InitModel(self):
        # paths tp import files
        self.path_Ktrans_ref = ''
        self.path_Ve_ref = ''
        self.path_Ktrans_cal = ''
        self.path_Ve_cal = ''

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
        self.page4 = wx.Panel(self.noteBookRight)
        self.noteBookRight.AddPage(self.page1, "Scatter plots Viewer")
        self.noteBookRight.AddPage(self.page2, "Standard Deviation 3D plots")
        self.noteBookRight.AddPage(self.page3, "Box plots")
        self.noteBookRight.AddPage(self.page4, "Result Review")

        # page 1
        # buttons
        button1 = wx.Button(self.page1, wx.ID_ANY, 'reference Ktrans')
        button2 = wx.Button(self.page1, wx.ID_ANY, 'reference Ve')
        button3 = wx.Button(self.page1, wx.ID_ANY, 'calculated trans')
        button4 = wx.Button(self.page1, wx.ID_ANY, 'calculated Ve')
        buttonOK = wx.Button(self.page1, wx.ID_ANY, 'Evaluate')
        buttonSave = wx.Button(self.page1, wx.ID_ANY, 'Save')

        self.Bind(wx.EVT_BUTTON, self.OnImportRefK, button1)
        self.Bind(wx.EVT_BUTTON, self.OnImportRefV, button2)
        self.Bind(wx.EVT_BUTTON, self.OnImportCalK, button3)
        self.Bind(wx.EVT_BUTTON, self.OnImportCalV, button4)
        self.Bind(wx.EVT_BUTTON, self.OnEvaluate, buttonOK)
        self.Bind(wx.EVT_BUTTON, self.OnSave, buttonSave)

        sizerButton = wx.GridSizer(cols=1)
        sizerButton.Add(button1)
        sizerButton.Add(button2)
        sizerButton.Add(button3)
        sizerButton.Add(button4)
        sizerButton.Add(buttonOK)
        sizerButton.Add(buttonSave)

        # set a canvas on page 1
        self.figureScatter = Figure()
        self.canvasScatter = FigureCanvas(self.page1,-1, self.figureScatter)

        # set sizer for the canvas
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasScatter, 1, wx.EXPAND)
        sizer.Add(sizerButton)
        self.page1.SetSizer(sizer)

        # page 2
        self.figure3D = Figure()
        self.canvas3D = FigureCanvas(self.page2,-1, self.figure3D)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvas3D, 1, wx.EXPAND)
        self.page2.SetSizer(sizer)

        # page 3, box plots
        # set a canvas on page 3
        self.figureBoxPlot = Figure()
        self.canvasBoxPlot = FigureCanvas(self.page3,-1, self.figureBoxPlot)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasBoxPlot, 1, wx.EXPAND)
        self.page3.SetSizer(sizer)

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
        Import the reference Ktrans
        '''
        dlg = wx.FileDialog(self, 'Choose a DICOM file to add', '', '', "DICOM file(*.dcm) | *.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_Ktrans_ref += (dlg.GetPath())

    def OnImportRefV(self, event):
        '''
        Import the reference Ve
        '''
        dlg = wx.FileDialog(self, 'Choose a DICOM file to add', '', '', "DICOM file(*.dcm) | *.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_Ve_ref += (dlg.GetPath())

    def OnImportCalK(self, event):
        '''
        Import the calculated Ktrans
        '''
        dlg = wx.FileDialog(self, 'Choose a DICOM file to add', '', '', "DICOM file(*.dcm) | *.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_Ktrans_cal += (dlg.GetPath())

    def OnImportCalV(self, event):
        '''
        Import the calculated Ve
        '''
        dlg = wx.FileDialog(self, 'Choose a DICOM file to add', '', '', "DICOM file(*.dcm) | *.dcm", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_Ve_cal += (dlg.GetPath())

    def OnEvaluate(self, event):
        '''
        process the imported DICOM,and display
        '''
        self.SetStatusText('Start to evaluate...')

        # create new model object
        self.newModel = ModelTested()

        # pass the paths and import the files
        self.newModel.Ktrans_ref_raw = self.newModel.ImportDICOM(self.path_Ktrans_ref)
        self.newModel.Ve_ref_raw = self.newModel.ImportDICOM(self.path_Ve_ref)
        self.newModel.Ktrans_cal_raw = self.newModel.ImportDICOM(self.path_Ktrans_cal)
        self.newModel.Ve_cal_raw = self.newModel.ImportDICOM(self.path_Ve_cal)

        # rescale the data if possible
        self.newModel.Ktrans_ref_rescaled = self.newModel.Rescale(self.newModel.Ktrans_ref_raw)
        self.newModel.Ve_ref_rescaled = self.newModel.Rescale(self.newModel.Ve_ref_raw)
        self.newModel.Ktrans_cal_rescaled = self.newModel.Rescale(self.newModel.Ktrans_cal_raw)
        self.newModel.Ve_cal_rescaled = self.newModel.Rescale(self.newModel.Ve_cal_raw)

        # rearrange the data
        self.newModel.Ktrans_ref_inPatch = self.newModel.Rearrange(self.newModel.Ktrans_ref_rescaled)
        self.newModel.Ve_ref_inPatch = self.newModel.Rearrange(self.newModel.Ve_ref_rescaled)
        self.newModel.Ktrans_cal_inPatch = self.newModel.Rearrange(self.newModel.Ktrans_cal_rescaled)
        self.newModel.Ve_cal_inPatch = self.newModel.Rearrange(self.newModel.Ve_cal_rescaled)

        # abstract the mean value for each patch
        self.newModel.Ktrans_ref_patchValue = self.newModel.EstimatePatch(self.newModel.Ktrans_ref_inPatch)
        self.newModel.Ve_ref_patchValue = self.newModel.EstimatePatch(self.newModel.Ve_ref_inPatch)
        self.newModel.Ktrans_cal_patchValue = self.newModel.EstimatePatch(self.newModel.Ktrans_cal_inPatch)
        self.newModel.Ve_cal_patchValue = self.newModel.EstimatePatch(self.newModel.Ve_cal_inPatch)

        # execute the planar fitting
        self.newModel.Ktrans_fittingParameter = self.newModel.FittingPlanar(self.newModel.Ktrans_cal_patchValue)
        self.newModel.Ve_fittingParameter = self.newModel.FittingPlanar(self.newModel.Ve_cal_patchValue)

        print 'the planar fitting result is:'
        print 'for the Ktrans map, Ktrans_cal = ' + str(self.newModel.Ktrans_fittingParameter[0]) + '* Ktrans_ref + ' + str(self.newModel.Ktrans_fittingParameter[1]) + '* Ve_ref' + str(self.newModel.Ktrans_fittingParameter[2])
        print 'for the Ve map, Ve_cal = ' + str(self.newModel.Ve_fittingParameter[0]) + '* Ktrans_ref + ' + str(self.newModel.Ve_fittingParameter[1]) + '* Ve_ref' + str(self.newModel.Ve_fittingParameter[2])


# ****************************
        self.deviationK = [[]*i for i in range(self.calK.nrOfRows)] # the std deviation of each patch, one list contains the values of a row
        self.deviationV = [[]*i for i in range(self.calV.nrOfRows)]
        self.meanValueOfPatchK = [[]*i for i in range(self.calK.nrOfRows)] # the mean value of the each patch, one list contains the values of a row
        self.meanValueOfPatchV = [[]*i for i in range(self.calV.nrOfRows)]
        self.medianValueOfPatchK = [[]*i for i in range(self.calK.nrOfRows)] # the median value of the each patch, one list contains the values of a row
        self.medianValueOfPatchV = [[]*i for i in range(self.calV.nrOfRows)]
        self.uniformedPatchK = [[[] for j in range(self.calK.nrOfColumns)] for i in range(self.calK.nrOfRows) ]
        self.uniformedPatchV = [[[] for j in range(self.calV.nrOfColumns)] for i in range(self.calV.nrOfRows) ]
        self.pixelsTempRefK = []
        self.pixelsTempCalK = []
        self.pixelsTempRefV = []
        self.pixelsTempCalV = []

        for i in range(self.calK.nrOfRows):
            for j in range(self.calK.nrOfColumns):
                # collect all the pixels to calculate the std error
                self.pixelsTempRefK.extend(self.refK.rearrangedPixels[i][j])
                self.pixelsTempCalK.extend(self.calK.rearrangedPixels[i][j])
                self.pixelsTempRefV.extend(self.refV.rearrangedPixels[i][j])
                self.pixelsTempCalV.extend(self.calV.rearrangedPixels[i][j])

        # linear regression, to remove the factor and offset in different models
        slopeK, interceptK, r_valueK, p_valueK, slope_std_errorK = stats.linregress(numpy.array(self.pixelsTempRefK), numpy.array(self.pixelsTempCalK))
        slopeV, interceptV, r_valueV, p_valueV, slope_std_errorV = stats.linregress(numpy.array(self.pixelsTempRefV), numpy.array(self.pixelsTempCalV))

        #uniform the data first, then calculate the standard deviation of each patch
        for i in range(self.calK.nrOfRows):
            for j in range(self.calK.nrOfColumns):
                for pixel in range(100):
                    self.uniformedPatchK[i][j].append((self.calK.rearrangedPixels[i][j][pixel] - numpy.asscalar(interceptK)) / numpy.asscalar(slopeK) )
                    self.uniformedPatchV[i][j].append((self.calV.rearrangedPixels[i][j][pixel] - numpy.asscalar(interceptV)) / numpy.asscalar(slopeV) )

                # student t test to decide the patch has normal distribution or not
                # skip this step firstly, and assume that each has normal distribution
                self.deviationK[i].append(numpy.std(self.uniformedPatchK[i][j]))
                self.deviationV[i].append(numpy.std(self.uniformedPatchV[i][j]))
                self.meanValueOfPatchK[i].append(numpy.mean(self.uniformedPatchK[i][j]))
                self.meanValueOfPatchV[i].append(numpy.mean(self.uniformedPatchV[i][j]))
                self.medianValueOfPatchK[i].append(numpy.median(self.uniformedPatchK[i][j]))
                self.medianValueOfPatchV[i].append(numpy.median(self.uniformedPatchV[i][j]))



        # uniform the calculated data, to remove artificial slope and intercept
        self.pixelsTempCalK_Uniformed = (self.pixelsTempCalK - interceptK) / slopeK
        self.pixelsTempCalK_Uniformed = self.pixelsTempCalK_Uniformed.tolist()
        self.pixelsTempCalV_Uniformed = (self.pixelsTempCalV - interceptV) / slopeV
        self.pixelsTempCalV_Uniformed = self.pixelsTempCalV_Uniformed.tolist()

        # calculate std error with uniformed data
        # maybe make more sense if the errors are calculated for each patch
        stdErrorK_Uniformed = numpy.sqrt(numpy.sum((numpy.array(self.pixelsTempRefK) - numpy.array(self.pixelsTempCalK_Uniformed)) ** 2) / len(self.pixelsTempRefK))
        stdErrorV_Uniformed = numpy.sqrt(numpy.sum((numpy.array(self.pixelsTempRefV) - numpy.array(self.pixelsTempCalV_Uniformed)) ** 2) / len(self.pixelsTempRefV))

        # the std error after rescale? Also could add 3D bar chart, so that the performance according to the (K, V) combination could be viewed
        print '******** EVALUATION RESULT *********'
        print 'the goodness of fit of Calculated Ktrans: ' + str(r_valueK) # this can be taken as a main factor for evaluating the performance of a model
        print 'the goodness of fit of Calculated Ve: ' + str(r_valueV)
        print 'std error of uniformed calculated Ktrans:' + str(stdErrorK_Uniformed)
        print 'std error of uniformed calculated Ve:' + str(stdErrorV_Uniformed)
        print 'estimate the artificial slope of calculated Ktrans: ' + str(slopeK)
        print 'estimate the artificial intercept of calculated Ktrans: ' + str(interceptK)
        print 'estimate the artificial slope of calculated Ve: ' + str(slopeV)
        print 'estimate the artificial intercept calculated Ve: ' + str(interceptV)
        print 'patch deviation of uniformed calculated Ktrans: ' + str(self.deviationK)
        print 'patch deviation of uniformed calculated Ve: ' + str(self.deviationV)

        # draw the figures
        self.DrawScatterPlot()
        self.Draw3DPlot()
        self.DrawBoxPlot()
        self.SetStatusText('Evaluation finished.')

        self.InitModel()

    def OnSave(self, event):
        # Save the statistic data for recording
        pass

    def DrawScatterPlot(self):
        '''
        the scatter plots show the distribution of the calculated values
        '''
        subPlotK = self.figureScatter.add_subplot(2, 1, 1)
        subPlotK.clear()
        plotRaw = subPlotK.scatter(self.pixelsTempRefK, self.pixelsTempCalK, color = 'g', alpha = 0.25, label = 'reference value')
        plotUniformed = subPlotK.scatter(self.pixelsTempRefK, self.pixelsTempCalK_Uniformed, color = 'b', alpha = 0.25, label = 'calculated value')
        plotRef = subPlotK.scatter(self.pixelsTempRefK, self.pixelsTempRefK, color = 'r', alpha = 0.25, label = 'uniformed calculated value')
        subPlotK.legend(loc = 'upper left')
        subPlotK.set_xlabel('Reference Ktrans')
        subPlotK.set_ylabel('Calculated Ktrans')
        subPlotK.set_title('Distribution plot of Ktrans')

        subPlotV = self.figureScatter.add_subplot(2, 1, 2)
        subPlotV.clear()
        plotRaw = subPlotV.scatter(self.pixelsTempRefV, self.pixelsTempCalV, color = 'g', alpha = 0.25, label = 'reference value')
        plotUniformed = subPlotV.scatter(self.pixelsTempRefV, self.pixelsTempCalV_Uniformed, color = 'b', alpha = 0.25, label = 'calculated value')
        plotRef = subPlotV.scatter(self.pixelsTempRefV, self.pixelsTempRefV, color = 'r', alpha = 0.25, label = 'uniformed calculated value')
        subPlotV.legend(loc = 'upper left')
        subPlotV.set_xlabel('Reference Ve')
        subPlotV.set_ylabel('Calculated Ve')
        subPlotV.set_title('Distribution plot of Ve')

        self.canvasScatter.draw()
        self.rightPanel.Layout()

    def DrawBoxPlot(self):
        '''
        draw box plots
        '''

        subPlotK = self.figureBoxPlot.add_subplot(2, 1, 1)
        subPlotK.clear()
        temp = []
        referValueK = []
        for i in range(self.calK.nrOfRows):
            temp.extend(self.uniformedPatchK[i])
            referValueK.append(self.refK.rearrangedPixels[i][0][0])
        subPlotK.boxplot(temp)

        subPlotK.set_title('Box plot of calculated Ktrans')
        subPlotK.set_xlabel('Patches\' number, concatenated row by row')
        subPlotK.set_ylabel('Calculated values in patches')
        subPlotK.set_yticks(referValueK, minor = True)
        subPlotK.grid(True, which = 'minor')


        subPlotV = self.figureBoxPlot.add_subplot(2, 1, 2)
        subPlotV.clear()
        temp = []
        referValueV = []
        for j in range(self.calV.nrOfColumns):
            referValueV.append(self.refV.rearrangedPixels[0][j][0])
            for i in range(self.calV.nrOfRows):
                temp.append(self.uniformedPatchV[i][j])
        subPlotV.boxplot(temp)

        subPlotV.set_title('Box plot of calculated Ve')
        subPlotV.set_xlabel('Patches\' number, concatenated column by column')
        subPlotV.set_ylabel('Calculated values in patches')
        subPlotV.set_yticks(referValueV, minor = True)
        subPlotV.grid(True, which = 'minor')

        self.canvasBoxPlot.draw()
        self.rightPanel.Layout()


    def Draw3DPlot(self):
        '''
        plot 3D bar s, so that a distribution view of the standard deviation can be referred to for different K,V combination
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
        earrange the pixels so that they can be picked up in unit of patch, with index of [indexOfRow][indexOfColumn]
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

## *****************************************************************
class ModelTested:
    ''' the class for a tested model. It includes the necessary data and methods for evaluating one model.
    '''
    def __init__(self):
        # initializes the class

        # parameters of the image size
        self.nrOfRows = 6
        self.nrOfColumns = 5
        self.patchLen = 10
        self.rescaleIntercept = 0
        self.rescaleSlope = 1

        # the raw image data as pixel flow
        self.Ktrans_ref_raw = []
        self.Ve_ref_raw = []
        self.Ktrans_cal_raw = []
        self.Ve_cal_raw = []

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
        self.Ktrans_ref_patchValue = [[]for i in self.nrOfRows]
        self.Ve_ref_patchValue = [[]for i in self.nrOfRows]
        self.Ktrans_cal_patchValue = [[]for i in self.nrOfRows]
        self.Ve_cal_patchValue = [[]for i in self.nrOfRows]

        # planar fitting parameters
        self.Ktrans_fittingParameter = []
        self.Ve_fittingParameter = []

    def ImportDICOM(self, path):
        # import reference and calculated DICOM files
        # it should be able to deal with different data type like DICOM, binary and so on. right now it's possible for DICOM
        try:
            ds = dicom.read_file(path)
            return ds
        except:
            dlg = wx.MessageBox('Invalid file path!', 'Cannot import file', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()


    def Rescale(self, ds):
        # rescale the DICOM file to remove the intercept and the slope. the 'pixel' in DICOM file means a row of pixels.

        try:
            self.rescaleIntercept = ds.rescaleIntercept
            self.rescaleSlope = ds.rescaleSlope
        except:
            pass

        pixelFlow = []
        for row in ds.pixel_array[1:len(originalPixels)-1]:
            temp = []
            for pixel in row:
                temp.append(pixel * self.rescaleSlope - self.rescaleIntercept)
            pixelFlow.extend(temp)
        return pixelFlow

    def Rearrange(self, pixelFlow):
        # rearrange the DICOM file so that the file can be accessed in patches and the top and bottom strips are removed as they are not meaningful here.
        tempAll = [[[] for j in range(self.nrOfColumns)] for i in range(self.nrOfRows) ]
        tempPatch = []
        for i in range(self.nrOfRows):
            for j in range(self.nrOfColumns):
                for k in range(self.patchLen):
                    tempPatch.append(pixelFlow[i * self.patchLen + k][j * self.patchLen : (j + 1) * self.patchLen])
                tempAll[i][j].extend(tempPatch)
                tempPatch = []
        return tempAll

    def EstimatePatch(self, dataInPatch):
        # estimate the value that can represent a patch. It can be mean or median value, and the deviation could also be provided for further evaluation.
        # some statistics test like normal distribution test should be applied to decide which value to take
        # as the first step each patch is believed as normally distributed. Therefore the mean value is taken.
        temp = [[]for i in range(self.nrOfRows) ]
        for i in range(self.nrOfRows):
            for j in range (self.nrOfColumns):
                temp[i].append(numpy.mean(dataInPatch[i][j]))
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
                xCurrent = self.Ktrans_ref_patchValue[i][j]
                yCurrent = self.Ve_ref_patchValue[i][j]
                zCurrent = calculatedPatchValue[i][j]
                x.append(xCurrent)
                y.append(yCurrent)
                z.append(zCurrent)
                xx.append(xCurrent**2)
                yy.append(yCurrent**2)
                xy.append(xCurrent * yCurrent)
                xz.append(xCurrent * zCurrent)
                yz.append(yCurrent * zCurrent)
        [a, b, c] = numpy.squeeze(numpy.array(numpy.inv([[numpy.sum(xx), numpy.sum(xy), numpy.sum(x)], [numpy.sum(xy), numpy.sum(yy), numpy.sum(y)], [numpy.sum(x), numpy.sum(y), self.nrOfRows * self.nrOfColumns]]) * numpy.array([[numpy.sum(xz)], [numpy.sum(yz)], [numpy.sum(z)]])))
        return a, b, c

    def Score(self):
        # give a score for evaluation according to the weighting factors.
        pass

