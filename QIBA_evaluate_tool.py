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

import csv
import os.path
import decimal
from sys import argv, exit
#import getopt #Replaced by argparse to handle command-line options
import argparse
import wx
import wx.html
import numpy
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.ticker as ticker
import matplotlib.pyplot as pyplt
import time
import subprocess
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
import wx.lib.scrolledpanel as scrolled
from xlwt import Workbook
import sys
import traceback #For debugging. Delete.
from PIL import Image
import scipy.stats

import QIBA_functions
import QIBA_model
import QIBA_functions_for_table
from ATEDialogBox import ATEDialogBox
from QIBA_table import QIBA_table
from QIBA_table_model_KV import QIBA_table_model_KV
from QIBA_table_model_T1 import QIBA_table_model_T1
import VerboseModeStatDescriptions as StatDescriptions

class MainWindow(wx.Frame):
    '''
    this is the parent class of the main window of the application.
    '''

    def __init__(self, parent, applicationName, calFiles, refFiles, desDir, verbose_mode=False):
        wx.Frame.__init__(self, parent, title = applicationName, size = (wx.SYS_SCREEN_X, wx.SYS_SCREEN_Y))
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.path_cal_T1 = ''
        self.path_cal_K = ''
        self.path_cal_V = ''
        self.path_qiba_table_T1 = ''
        self.path_qiba_table_K = ''
        self.path_qiba_table_V = ''
        self.nrOfRow = 0
        self.nrOfColumn = 0
        self.patchLen = 10
        self.WARNINGTEXT = False
        self.supportedFileTypeList = ['.dcm', '.bin', '.raw', '.tif', '.img']
        self.supportedTextFileTypeList = ['.csv', '.cdata', '.txt'] #Valid filetypes for reading text file tables

        self.verbose_mode = verbose_mode

        self.CenterOnScreen()

        self.CreateStatusBar()
        self.SetStatusText("Welcome to " + applicationName + "!")

        # Allowable total error
        self.allowable_total_error_set = False
        self.allowable_total_error = "0.0"

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
        OnExit = fileMenu.Append(wx.ID_EXIT, "&Quit\tCtrl+Q", "Quit")

        # self.SetupEditMenu()

        aboutMenu = wx.Menu()
        OnManual = aboutMenu.Append(wx.ID_ANY, 'Open the manual...')
        aboutMenu.AppendSeparator()
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

        #self.menubar.Bind(wx.EVT_MENU, self.OnExport, OnExport)
        #self.menubar.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        #self.menubar.Bind(wx.EVT_MENU, self.OnAbout, OnAboutApp)
        #self.menubar.Bind(wx.EVT_MENU, self.OnManual, OnManual)
        self.Bind(wx.EVT_MENU, self.OnExport, OnExport)
        self.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        self.Bind(wx.EVT_MENU, self.OnAbout, OnAboutApp)
        self.Bind(wx.EVT_MENU, self.OnManual, OnManual)
    
        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(aboutMenu, "&About")
        self.SetMenuBar(self.menubar)

    def OnExport(self, event):
        pass

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

    def SetupRightClickMenuForTextFiles(self):
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
                                             filter="Supported files (*.dcm *.bin *.raw *.tif *.img *.csv *.cdata *.txt)|*.dcm;*.bin;*.raw;*.tif;*.img;*.csv;*.cdata;*.txt")
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

    def CreateDefaultMask(self, number_of_rows, number_of_columns, patch_length):
        """Creates a default mask to use when evaluating. By default,
        all pixels will be evaluated. 
        The mask should have the dimensions (nrOfRows x nrOfColumns)
        A mask value of 255 means that the pixel should be evaluated.
        A mask value of 0 means that the pixel should not be evaluated.
        Proportional weighting (if determined to be useful should be easy
        to implement.
        
        The default mask should be 60 rows x 50 columns
        
        The function loadMaskFile handles loading a user-specified mask.
        Store this mask in the variable self.mask.
        The mask should be a list of numeric values.
        """
        mask = []
        
        for i in range(number_of_rows * 10):
            #row = [255 for j in range(number_of_columns * patch_length)]
            row = [255 for j in range(number_of_columns*10)]
            mask.append(row)
        return mask
        
    def loadMaskFile(self, mask_path):
        """Loads a mask to use when evaluating.
        The mask should have the dimensions (nrOfRows x nrOfColumns)
        A mask value of 255 means that the pixel should be evaluated.
        A mask value of 0 means that the pixel should not be evaluated.
        Proportional weighting (if determined to be useful) should be easy
        to implement.
        
        The function CreateDefaultMask handles creating a default mask.
        The mask is stored in the variable self.mask and should be a list of
        numeric values.
        """

        temp_original_mask = list(self.mask) # Store the current mask until the new, loaded mask is validated

        if mask_path.endswith(".cdata") or mask_path.endswith(".csv") or mask_path.endswith(".txt"):
            file_contents = []
            with open(mask_path, "rb") as mask_file:
                try:
                    dialect = csv.Sniffer().sniff(mask_file.read(), delimiters=",\t") #Determine delimiter used in file (commas, tabs, etc.)
                    mask_file.seek(0)
                    delimiter = dialect.delimiter
                    csv_reader = csv.reader(mask_file, delimiter=delimiter)
                    for row in csv_reader:
                        file_contents.append(row)
                except csv.Error:
                    print("There was an error reading " + mask_path)
                    #ex_type, ex, tb = sys.exc_info() #For debugging
                    #traceback.print_tb(tb) #For debugging
                    return
            parsed_mask, valid_mask = self.parseMaskFile(file_contents, "table", self.nrOfRow, self.nrOfColumn, self.patchLen, delimiter)
            
            if valid_mask:
                return parsed_mask
            else:
                return self.mask # Keep the existing mask
            
        else: # Handle mask if it is an image
            #raw_mask_image = QIBA_functions.ImportFile(mask_path, self.nrOfRow, self.nrOfColumn, self.patchLen, "L") #L mode is 8-bit B/W
            #print(raw_mask_image)
            #Use function QIBA_functions.ImportFile(path, nrOfRows, nrOfColumns, patchLen, mode)
            try:
                raw_mask_image = Image.open(mask_path)
                raw_mask_array = numpy.array(raw_mask_image)
                parsed_mask, valid_mask = self.parseMaskFile(raw_mask_array, "image", self.nrOfRow, self.nrOfColumn, self.patchLen, "\t")

                if valid_mask:
                    return parsed_mask
                else:
                    return self.mask # Keep the existing mask
            except IOError:
                print("There was a problem reading the mask file at "+mask_path+".")
                print("No mask will be used.")
                return self.mask # Keep the existing mask
        #return self.mask # In case none of the above return statements are reached
            
    def parseMaskFile(self, file_contents, data_type, number_of_rows, number_of_columns, patch_length, delimiter):
        mask_contents = []
        valid_mask = True
        correct_x_dim_len = number_of_rows * patch_length
        correct_y_dim_len = number_of_columns * patch_length
        
        if data_type == "table":
            try:
                for line in file_contents:
                    line_int = [int(n) for n in line]
                    mask_contents.append(line_int)
            except ValueError:
                print("Error: The mask file contains non-numeric data") 
                valid_mask = False
        
            rows_in_mask = len(mask_contents)
            if rows_in_mask != correct_x_dim_len:
                print("Error: The mask should have "+str(correct_x_dim_len)+" rows. It has "+str(rows_in_mask)+" row(s).")
                valid_mask = False
            for i in range(rows_in_mask):
                i_plus_1 = i + 1
                row = mask_contents[i]
                elements_in_row = len(row)
                if elements_in_row != correct_y_dim_len:
                    print("Error: Mask row "+str(i_plus_1)+" has "+str(elements_in_row)+" element(s). It should have "+str(correct_y_dim_len)+" element(s).")
                    valid_mask = False
            
            #file_contents = file_contents.split("\n")
                
            #for line in file_contents:
                #line_list = list(line.split(delimiter))
                #mask_contents.append(line_list)
                
        elif data_type == "image":
            mask_contents = []
            mask_x_dim_len = len(file_contents)
            mask_y_dim_len = len(file_contents[0])
            if mask_x_dim_len != correct_x_dim_len or mask_y_dim_len != correct_y_dim_len:
                print("Error: The mask dimensions must be "+str(correct_x_dim_len)+ "x"+str(correct_y_dim_len)+". The supplied mask is "+str(mask_x_dim_len)+"x"+str(mask_y_dim_len)+".")
                valid_mask = False

            if valid_mask:
                for i in range(mask_x_dim_len):
                    #mask_contents[i] = list(file_contents[i])
                    mask_contents.append(list(file_contents[i]))


        return mask_contents, valid_mask
    
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
        self.pageImagePreview  = wx.Panel(self.noteBookRight)
        ###self.pageImagePreview = scrolled.ScrolledPanel(self.noteBookRight)
        self.pageScatter = wx.Panel(self.noteBookRight)
        # self.pageHistogram = wx.Panel(self.noteBookRight)
        self.pageHistogram = scrolled.ScrolledPanel(self.noteBookRight)
        # self.pageBoxPlot = wx.Panel(self.noteBookRight)
        self.pageBoxPlot = scrolled.ScrolledPanel(self.noteBookRight)
        self.pageStatistics = wx.Panel(self.noteBookRight)
        self.pageNaN = wx.Panel(self.noteBookRight)
        self.pageCovarianceCorrelation = wx.Panel(self.noteBookRight)
        self.pageModelFitting = wx.Panel(self.noteBookRight)
        self.pageRMSD = wx.Panel(self.noteBookRight) 
        self.pageCCC = wx.Panel(self.noteBookRight)
        self.pageTDI = wx.Panel(self.noteBookRight)
        self.pageLOA = wx.Panel(self.noteBookRight)
        self.pageSigmaMetric = wx.Panel(self.noteBookRight)
        self.pageT_Test = wx.Panel(self.noteBookRight)
        self.pageU_Test = wx.Panel(self.noteBookRight)
        self.pageChiq = wx.Panel(self.noteBookRight)

        self.noteBookRight.AddPage(self.pageStart, 'Start')
        self.noteBookRight.AddPage(self.pageImagePreview, "Image Viewer")
        self.noteBookRight.AddPage(self.pageScatter, "Scatter Plots Viewer")
        self.noteBookRight.AddPage(self.pageHistogram, "Histograms Plots Viewer")
        self.noteBookRight.AddPage(self.pageBoxPlot, "Box Plots Viewer")
        self.noteBookRight.AddPage(self.pageNaN, "NaN Viewer")
        self.noteBookRight.AddPage(self.pageStatistics, "Statistics Viewer")
        self.noteBookRight.AddPage(self.pageCovarianceCorrelation, "Covariance And Correlation")
        self.noteBookRight.AddPage(self.pageRMSD, "Root Mean Square Deviation")
        self.noteBookRight.AddPage(self.pageCCC, "Concordance Correlation Coefficient")
        self.noteBookRight.AddPage(self.pageTDI, "Total Deviation Index")
        self.noteBookRight.AddPage(self.pageLOA, "Bland-Altman Limits of Agreement")
        self.noteBookRight.AddPage(self.pageSigmaMetric, "Sigma Metric")
        self.noteBookRight.AddPage(self.pageModelFitting, "Model fitting")
        self.noteBookRight.AddPage(self.pageT_Test, "t-test results Viewer")
        self.noteBookRight.AddPage(self.pageU_Test, "U-test results Viewer")
        self.noteBookRight.AddPage(self.pageChiq, "Chi-Square test results Viewer")

        # show the calculated images and error images
        self.figureImagePreview = Figure()
        self.canvasImagePreview = FigureCanvas(self.pageImagePreview, -1, self.figureImagePreview)

        #Changed: The sizer for the image preview window is now an instance variable.
        #Original 3 lines
        #sizer = wx.BoxSizer(wx.HORIZONTAL)
        #sizer.Add(self.canvasImagePreview, 1, wx.EXPAND)
        #self.pageImagePreview.SetSizer(sizer)
        
        #New 6 lines
        self.imagePreviewSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tableViewer = wx.html.HtmlWindow(self.pageImagePreview, -1, style=wx.html.HW_SCROLLBAR_AUTO | wx.ALWAYS_SHOW_SB)
        self.imagePreviewSizer.Add(self.tableViewer, 1, wx.EXPAND)  # adds table to sizer
        self.imagePreviewSizer.Show(self.tableViewer, show=False)
        self.imagePreviewSizer.Add(self.canvasImagePreview, 1, wx.EXPAND) #adds image preview to sizer
        self.pageImagePreview.SetSizer(self.imagePreviewSizer)

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

        # Bland-Altman plot page
        self.SetupPage_BlandAltmanPlot()
        
        # page box plots
        self.SetupPage_BoxPlot()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasBoxPlot, 1, wx.EXPAND)
        self.pageBoxPlot.SetSizer(sizer)

        # page statistics
        self.statisticsViewer = wx.html.HtmlWindow(self.pageStatistics, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.statisticsViewer, 1, wx.EXPAND)
        self.pageStatistics.SetSizer(sizer)

        # page Nan
        self.NaNViewer = wx.html.HtmlWindow(self.pageNaN, -1)
        sizer = wx.BoxSizer()
        sizer.Add(self.NaNViewer, 1, wx.EXPAND)
        self.pageNaN.SetSizer(sizer)

        # page covariance and correlation
        self.covCorrViewer = wx.html.HtmlWindow(self.pageCovarianceCorrelation, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.covCorrViewer, 1, wx.EXPAND)
        self.pageCovarianceCorrelation.SetSizer(sizer)

        # RMSD Page
        self.rmsdViewer = wx.html.HtmlWindow(self.pageRMSD, -1)
        
        sizer = wx.BoxSizer()
        sizer.Add(self.rmsdViewer, 1, wx.EXPAND)
        self.pageRMSD.SetSizer(sizer)

        # page ccc
        self.cccViewer = wx.html.HtmlWindow(self.pageCCC, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.cccViewer, 1, wx.EXPAND)
        self.pageCCC.SetSizer(sizer)

        # TDI Page
        self.tdiViewer = wx.html.HtmlWindow(self.pageTDI, -1)
        
        sizer = wx.BoxSizer()
        sizer.Add(self.tdiViewer, 1, wx.EXPAND)
        self.pageTDI.SetSizer(sizer)
        
        # Bland-Altman LOA Page
        #self.loaViewer = wx.html.HtmlWindow(self.pageLOA, -1)
        
        #sizer = wx.BoxSizer()
        #sizer.Add(self.loaViewer, 1, wx.EXPAND)
        #self.pageLOA.SetSizer(sizer)
        
        # Sigma Metric Page
        self.sigmaMetricViewer = wx.html.HtmlWindow(self.pageSigmaMetric, -1)
        
        sizer = wx.BoxSizer()
        sizer.Add(self.sigmaMetricViewer, 1, wx.EXPAND)
        self.pageSigmaMetric.SetSizer(sizer)
        
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
        sizer.Add(self.noteBookRight, 1, wx.EXPAND) #originally 1
        self.rightPanel.SetSizer(sizer)
        self.rightPanel.Layout()

    def SetupPage_BoxPlot(self):
        pass

    def OnSwitchViewing(self, event):
        # switch the viewing in scatter plot page
        if self.type_of_data_loaded == "image":
            self.SetStatusText("Rearranging the scatter plot...")
            self.SCATTER_SWITCH = not self.SCATTER_SWITCH
            self.buttonSwitch.Disable()
            self.DrawScatter()
            self.buttonSwitch.Enable()
            self.SetStatusText("Rearranging the scatter plot finished.")
        else:
            print "Warning: no implementation for switch viewing for table data. Should be impemented or the button "+\
            "should be disabled/removed for table data. "

    def changeTabTitle(self, old_title, new_title):
        """Changes the title of a wxPython Notebook tab. wxPython lacks
        a way to do this with one statement, so this is the alternate.
        """
        for tab_id in range(self.noteBookRight.GetPageCount()):
            if self.noteBookRight.GetPageText(tab_id) == old_title:
                self.noteBookRight.SetPageText(tab_id, new_title)
                return

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
        self.NaNViewer.SetPage('')
        self.covCorrViewer.SetPage('')
        self.modelFittingViewer.SetPage('')
        self.t_testViewer.SetPage('')
        self.U_testViewer.SetPage('')
        self.rmsdViewer.SetPage('')
        self.cccViewer.SetPage('')
        self.tdiViewer.SetPage('')
        
        self.ClearPage_BlandAltmanPlot()
        
        #self.loaViewer.SetPage('')
        self.sigmaMetricViewer.SetPage('')

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

    def DrawTable(self):
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
        OnMaps_zoom = wx.MenuItem(self.popmenu_maps, self.ID_POPUP_MAPS_ZOOM, 'Zoom')
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
        OnScatters_zoom = wx.MenuItem(self.popmenu_scatters, self.ID_POPUP_SCATTER_ZOOM, 'Zoom')
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
        # The data can be (Ktrans,Ve) image data or table data.
        # Or, the data can be T1/R1 image data or table data.
        self.type_of_data_loaded = ""

        try:
            if (self.path_cal_K and self.path_cal_V) or self.path_cal_T1:
                self.type_of_data_loaded = "image"
            elif (self.path_qiba_table_K and self.path_qiba_table_V) or self.path_qiba_table_T1:
                self.type_of_data_loaded = "table"
        except:
            wx.MessageBox('Please import proper calculated data!', 'Info', wx.OK | wx.ICON_INFORMATION)
            return

        # check the image dimension parameter validation
        if self.WARNINGTEXT:
            self.SetStatusText('Please input correct dimension of the image!')
            return

        # clear the interface if they were used before
        self.ClearInterface()

        # disable some widgets
        #self.buttonEvaluate.Disable()

        # Make sure allowable total error is set
        while not self.allowable_total_error_set:
            self.setAllowableTotalError()
            

        # status bar
        self.SetStatusText('Evaluating, please wait...')
        #EvaluateProgressDialog.Update(5)

        #If a table is loaded, parse it and create a KV or T1 model with the nominal and calculated data
        if self.type_of_data_loaded == "image":
            # create new model object to evaluated on
            self.GenerateModel()
        elif self.type_of_data_loaded == "table":
            self.GenerateTableModel()

        # call the method to execute evaluation
        try:
            if self.type_of_data_loaded == "image":
                self.newModel.evaluate()
            elif self.type_of_data_loaded == "table":
                self.newModel.evaluate()
        #except RuntimeError:
        #original - restore
        #    self.SetStatusText('RuntimeError occurs. Evaluation terminated.')
        #    return False
        except RuntimeError as e:
            print(e)
            ex_type, ex, tb = sys.exc_info()  # For debugging
            traceback.print_tb(tb)  # For debugging
            self.SetStatusText('Runtime error occurs. Evaluation terminated.')
            return False
        except Exception as e: #For debugging. Originally just "except".
            print(e) #For debugging
            ex_type, ex, tb = sys.exc_info() #For debugging
            traceback.print_tb(tb) #For debugging
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
        # self.buttonEvaluate.Enable()
        
    def setAllowableTotalErrorMenu(self, event):
        """Display the Allowable Total Error dialog box, which allows
        the user to specify the value for Allowable Total Error.
        This value is needed to calculate the sigma metric.
        
        This function is called when "Set Allowable Total Error" command
        is selected in the Edit menu.
        """
        ate_dialog_box = ATEDialogBox(None, "Allowable Total Error", (500,300), self.allowable_total_error)
        ate_dialog_box.ShowModal()
        
        button_clicked_name = ate_dialog_box.button_clicked_name
        if button_clicked_name == "OK":
            
            self.allowable_total_error = ate_dialog_box.getATEValue()
                
            #Convert the entry in the dialog's text box to a float
            try:
                self.allowable_total_error = float(self.allowable_total_error)
                self.allowable_total_error_set = True
            except ValueError:
                self.allowable_total_error_set = False
                self.SetStatusText("Please enter a number for allowable total error")
                error_message = "Please enter a number for allowable total error"
                wx.MessageBox(error_message, "Allowable Total Error", wx.OK|wx.ICON_ERROR)
                    
        else:
            ate_dialog_box.destroy()
            return
        
        ate_dialog_box.destroy()
    
    def setAllowableTotalError(self):
        """Display the Allowable Total Error dialog box, which allows
        the user to specify the value for Allowable Total Error.
        This value is needed to calculate the sigma metric.
        
        This function is called if the user clicks the Evaluate
        button without choosing the Set Allowable Total Error menu command
        """
        #valid_ate_entered = False
        ate_dialog_box = ATEDialogBox(None, "Allowable Total Error", (500,300), self.allowable_total_error)
        ate_dialog_box.ShowModal()
        
        button_clicked_name = ate_dialog_box.button_clicked_name
        
        while not self.allowable_total_error_set:
            if button_clicked_name == "OK":
                
                self.allowable_total_error = ate_dialog_box.getATEValue()
                
                #Convert the entry in the dialog's text box to a float
                try:
                    self.allowable_total_error = float(self.allowable_total_error)
                    self.allowable_total_error_set = True
                except ValueError:
                    self.allowable_total_error_set = False
                    self.SetStatusText("Please enter a number for allowable total error")
                    error_message = "Please enter a number for allowable total error"
                    wx.MessageBox(error_message, "Allowable Total Error", wx.OK|wx.ICON_ERROR)
                    self.setAllowableTotalError()

            elif button_clicked_name == "Cancel":
                ate_dialog_box.destroy()
                return
            
        ate_dialog_box.destroy()

    def setVerboseMode(self, event):
        """Enable/disable Verbose Mode.
        If Verbose Mode is enabled, then explanations of the
        CCC, RMSD, TDI, BA-LOA, and sigma metric will be included in the output reports."""
        self.verbose_mode = not self.verbose_mode


    def evaluateCmdLine(self):
        """Do evaluation. Use this function when running from command line."""
        # make sure there's calculated data loaded
        # The data can be (Ktrans,Ve) image data or table data.
        # Or, the data can be T1/R1 image data or table data.
        self.type_of_data_loaded = ""
        try:
            if (self.path_cal_K and self.path_cal_V) or self.path_cal_T1:
                self.type_of_data_loaded = "image"
            elif (self.path_qiba_table_K and self.path_qiba_table_V) or self.path_qiba_table_T1:
                self.type_of_data_loaded = "table"
        except:
            print("Please import proper calculated data!")
            return
        #If a table is loaded, parse it and create a KV or T1 model with the nominal and calculated data
        if self.type_of_data_loaded == "image":
            # create new model object to evaluated on
            self.GenerateModel()
        elif self.type_of_data_loaded == "table":
            self.GenerateTableModel()
        
        # call the method to execute evaluation
        try:
            if self.type_of_data_loaded == "image":
                self.newModel.evaluate()
            elif self.type_of_data_loaded == "table":
                self.newModel.evaluate()
        except RuntimeError:
            print("RuntimeError occurred. Evaluation terminated.")
            return False
        except Exception as e: #For debugging. Originally just "except".
            print(e) #For debugging
            ex_type, ex, tb = sys.exc_info() #For debugging
            traceback.print_tb(tb) #For debugging
            return False
        
    def GenerateModel(self):
        self.newModel = QIBA_model.Model_KV('', '', '', '', [self.nrOfRow, self.nrOfColumn])

    def GenerateTableModel(self):
        """Generates the QIBA model if table-based data is supplied."""
        self.newModel = QIBA_table_model_KV.QIBA_table_model_KV("", "")
        
    def ShowResults(self):
        pass

    def OnExport(self, event):
        '''
        export selection
        '''
        save_folder = ""

        exportDialog = MySelectionDialog(None, "Export as:", "Export as...", choices=["PDF", "Excel file"])
        if self.type_of_data_loaded == "table":
            save_folder = self.saveResultsTable()

        if exportDialog.ShowModal() == wx.ID_OK:
            if exportDialog.GetSelections() == "PDF":
                self.OnExportToPDF(save_folder)
            elif exportDialog.GetSelections() == "Excel file":
                self.OnExportToFolder(save_folder)



        #if self.type_of_data_loaded == "image":
        #    exportDialog = MySelectionDialog(None, 'Export as:', 'Export as...', choices=['PDF', 'Excel file'])
        #    if exportDialog.ShowModal() == wx.ID_OK:
        #        if exportDialog.GetSelections() == 'PDF':
        #            self.OnExportToPDF('')
        #        elif exportDialog.GetSelections() == 'Excel file':
        #            self.OnExportToFolder('')
        #    else:
        #        pass
        #elif self.type_of_data_loaded == "table":
        #    save_folder = self.saveResultsTable()

    def OnExportToFolder(self, desDir):
        pass

    def OnExportToPDF(self, desDir):
        # export the evaluation results to PDF

        #self.buttonEvaluate.Disable()

        # show in status bar when export finishes
        try:
            self.SetStatusText('Exporting results...')
        except:
            pass

        # save file path dialog
        savePath = os.getcwd()
        #desDir_folder_only = os.path.dirname(desDir)
        #desFile = os.path.basename(fullDesPath)
        #os.chdir(desDir) # Sets the working directory to the destination directory
        if desDir == '':
            dlg = wx.FileDialog(self, 'Export the results as PDF file...', '', '', "PDF file(*.pdf)|*.pdf", wx.SAVE | wx.OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                savePath = dlg.GetPath()
            else:
                return
        else:
            savePath = os.path.join(desDir, 'results.pdf')

        # save to temp html file
        temp_html = open(os.path.join(os.getcwd(), 'temp', 'temp.html'), 'w+')
        #temp_html_folder = os.path.join(desDir, "temp")
        #if not os.path.exists(temp_html_folder):
        #    os.makedirs(temp_html_folder)
        #temp_html = open(os.path.join(desDir, "temp", "temp.html"), "w+")
        temp_html.write(self.GetResultInHtml())
        temp_html.close()

        # due to the Python wrapper of wkhtmltopdf "python_wkhtmltopdf" pre-requires xvfb is not available for Windows, here use commandline to call the tool
        cmd=[os.path.join(os.getcwd(), 'tools', 'wkhtmltopdf', 'bin', 'wkhtmltopdf'), os.path.join(os.getcwd(), 'temp', 'temp.html'), savePath]
        #cmd=[os.path.join(desDir, 'tools', 'wkhtmltopdf', 'bin', 'wkhtmltopdf'), os.path.join(desDir, 'temp', 'temp.html'), savePath]
        process = subprocess.Popen(cmd) #, stdout=subprocess.PIPE)
        process.wait()

        # remove the temp file
        folderPath = os.path.join(os.getcwd(), 'temp')
        #folderPath = os.path.join(desDir, 'temp')
        for theFile in os.listdir(folderPath):
            os.remove(os.path.join(folderPath, theFile))

        # show in status bar when export finishes
        try:
            self.SetStatusText('Results exported as PDF file.')
        except:
            pass

        #self.buttonEvaluate.Enable()

    def OnExportToPDFCmdLine(self, desDir):
        # export the results to PDF
        # used when program is run in command-line mode
        
        if not os.path.isdir(desDir):
            desDir_folder_only = os.path.dirname(desDir)
        else:
            desDir_folder_only = desDir
            
        savePath = desDir_folder_only
        if desDir == '':
            dlg = wx.FileDialog(self, 'Export the results as PDF file...', '', '', "PDF file(*.pdf)|*.pdf", wx.SAVE | wx.OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                savePath = dlg.GetPath()
            else:
                return
        else:
            savePath = os.path.join(desDir_folder_only, 'results.pdf')
            
        # save to temp html file
        if not os.path.exists(os.path.join(desDir_folder_only, "temp")):
            os.makedirs(os.path.join(desDir_folder_only, "temp"))
            
        temp_html = open(os.path.join(desDir_folder_only, 'temp', 'temp.html'), 'w+')
        #temp_html_folder = os.path.join(desDir, "temp")
        #if not os.path.exists(temp_html_folder):
        #    os.makedirs(temp_html_folder)
        #temp_html = open(os.path.join(desDir, "temp", "temp.html"), "w+")
        temp_html.write(self.GetResultInHtml())
        temp_html.close()
        
        # due to the Python wrapper of wkhtmltopdf "python_wkhtmltopdf" pre-requires xvfb is not available for Windows, here use commandline to call the tool
        cmd=[os.path.join(os.getcwd(), 'tools', 'wkhtmltopdf', 'bin', 'wkhtmltopdf'), os.path.join(desDir_folder_only, 'temp', 'temp.html'), savePath]
        process = subprocess.Popen(cmd) #, stdout=subprocess.PIPE)
        process.wait()
        
        # remove the temp file
        folderPath = os.path.join(desDir_folder_only, 'temp')
        for theFile in os.listdir(folderPath):
            os.remove(os.path.join(folderPath, theFile))

        # show in status bar when export finishes
        try:
            print('Results exported as PDF file.')
        except:
            pass

    #Original
    #def OnExportToPDF(self, desDir):
        # export the evaluation results to PDF

        #self.buttonEvaluate.Disable()

        # show in status bar when export finishes
    #    try:
    #        self.SetStatusText('Exporting results...')
    #    except:
    #        pass

        # save file path dialog
    #    savePath = os.getcwd()
    #    print("working directory:"+desDir) #for debugging
    #    if desDir == '':
    #        dlg = wx.FileDialog(self, 'Export the results as PDF file...', '', '', "PDF file(*.pdf)|*.pdf", wx.SAVE | wx.OVERWRITE_PROMPT)
    #        if dlg.ShowModal() == wx.ID_OK:
    #            savePath = dlg.GetPath()
    #        else:
    #            return
    #    else:
    #        savePath = os.path.join(desDir, 'results.pdf')

        # save to temp html file
    #    temp_html = open(os.path.join(os.getcwd(), 'temp', 'temp.html'), 'w+')
    #    temp_html.write(self.GetResultInHtml())
    #    temp_html.close()

        # due to the Python wrapper of wkhtmltopdf "python_wkhtmltopdf" pre-requires xvfb is not available for Windows, here use commandline to call the tool
    #    cmd=[os.path.join(os.getcwd(), 'tools', 'wkhtmltopdf', 'bin', 'wkhtmltopdf'), os.path.join(os.getcwd(), 'temp', 'temp.html'), savePath]
    #    process = subprocess.Popen(cmd) #, stdout=subprocess.PIPE)
    #    process.wait()

        # remove the temp file
    #    folderPath = os.path.join(os.getcwd(), 'temp')
    #    for theFile in os.listdir(folderPath):
    #        os.remove(os.path.join(folderPath, theFile))

        # show in status bar when export finishes
    #    try:
    #        self.SetStatusText('Results exported as PDF file.')
    #    except:
    #        pass

        #self.buttonEvaluate.Enable()


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
    def __init__(self, appName, calFiles, refFiles, desDir, verbose_mode):
        # instance of the main window
        MainWindow.__init__(self, None, appName, calFiles, refFiles, desDir, verbose_mode)

        self.patchLen = 10
        self.WARNINGTEXT = False

        # default files' paths
        if refFiles:
            self.path_ref_K, self.path_ref_V = refFiles.split(',')
        else:
            self.path_ref_K = os.path.join(os.getcwd(), 'reference_data', 'Ktrans.tif')
            self.path_ref_V = os.path.join(os.getcwd(), 'reference_data', 'Ve.tif')

        if calFiles:
            self.path_cal_K, self.path_cal_V = calFiles.split(',')
            self.SetStatusText(self.path_cal_V)
        else:
            self.path_cal_K = ''
            self.path_cal_V = ''

        self.path_qiba_table_K = ""
        self.path_qiba_table_V = ""
        
        # customize the main window
        self.LoadRef()
        self.SetupStartPage()
        self.SetupEditMenu()
        self.SetupRightClickMenu()
        self.SetupRightClickMenuForTextFiles()
        self.SetupPageANOVA()
        self.mask = self.CreateDefaultMask(self.nrOfRow, self.nrOfColumn, self.patchLen)

        # temporary -- for debugging
        #self.mask = self.loadMaskFile("V:/QIBA/QIBA Project Round 5/Text File Tables for QDET Non-Image Mode/Test_Mask.cdata") #for debugging

    def SetupPage_BoxPlot(self):
        self.figureBoxPlot = Figure()
        self.canvasBoxPlot = FigureCanvas(self.pageBoxPlot,-1, self.figureBoxPlot)

    def ShowResults(self):
        # show the results in the main window
        self.NaNViewer.SetPage(self.newModel.NaNPercentageInHTML)
        self.statisticsViewer.SetPage(self.newModel.GetStatisticsInHTML())
        self.covCorrViewer.SetPage(self.newModel.GetCovarianceCorrelationInHTML())
        self.rmsdViewer.SetPage(self.newModel.RMSDResultInHTML)
        self.cccViewer.SetPage(self.newModel.CCCResultInHTML)
        self.tdiViewer.SetPage(self.newModel.TDIResultInHTML)
        #self.loaViewer.SetPage(self.newModel.LOAResultInHTML)
        self.sigmaMetricViewer.SetPage(self.newModel.sigmaMetricResultInHTML)
        self.modelFittingViewer.SetPage(self.newModel.GetModelFittingInHTML())
        self.t_testViewer.SetPage(self.newModel.GetT_TestResultsInHTML())
        self.U_testViewer.SetPage(self.newModel.GetU_TestResultsInHTML())
        self.ANOVAViewer.SetPage(self.newModel.GetANOVAResultsInHTML())
        self.ChiqViewer.SetPage(self.newModel.Chiq_testResultInHTML)

        self.IN_AXES = False

        # draw the figures
        if self.type_of_data_loaded == "image":
            self.DrawMaps()
            self.DrawScatter()
            self.DrawHistograms()
            self.DrawBoxPlot()
            self.DrawBlandAltmanPlot()
        elif self.type_of_data_loaded == "table":
            self.DrawTable()
            self.DrawScatterFromTable()
            self.DrawHistogramsFromTable()
            self.DrawBoxPlotFromTable()
            self.DrawBlandAltmanPlotFromTable()

    def saveResultsTable(self, save_path=None):
        """Saves the results table as a text file.
        This function is called automatically when the table model is evaluated.
        Call this function with the save_path when QIBA Evaluate Tool is used in 
        command-line mode.
        save_path should include the folders and file name."""
        def addToTable(table, data_label_list, data_to_add_list):
            for j in range(len(data_to_add_list)):
                data_label = data_label_list[j]
                data_to_add = data_to_add_list[j]
                for k in range(len(data_to_add)):
                    if k == len(data_to_add)-1:
                        table += str(data_to_add[k]) + "\n"
                    elif k > 0:
                        table += str(data_to_add[k]) + "\t"
                    else:
                        table += data_label + " = \t" + str(data_to_add[k]) + "\t"
            return table
            
        #default_directory = os.path.expanduser("~") # User's home folder
        default_directory = os.path.dirname(self.path_qiba_table_K)
        
        # Remove ktrans and file extension from source ktrans table file name.
        # Build the default results table file name from this.
        ktrans_table_file = os.path.basename(self.path_qiba_table_K)
        ktrans_table_file = ktrans_table_file.lower()
        ktrans_table_file = self.removeSubstring(ktrans_table_file, "_ktrans")
        ktrans_table_file = self.removeSubstring(ktrans_table_file, "ktrans")
        ktrans_table_file = self.removeSubstring(ktrans_table_file, "_k")
        ktrans_table_file = self.removeSubstring(ktrans_table_file, "k")  
        ktrans_table_file = ktrans_table_file[0:ktrans_table_file.rfind(".")]
        
        if save_path is None:
            save_file_dialog = wx.FileDialog(self, "Save Results Table", default_directory, ktrans_table_file+"_Results_Table.txt", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if save_file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            save_path = save_file_dialog.GetPath()
        
        results_table = ""
        label_list = ["Mean", "Median", "Std. Dev.", "1st Quartile", "3rd Quartile", "Min.", "Max.", "RMSD", "CCC", "TDI", "Sigma metric"]

        if self.type_of_data_loaded == "image":
            ktrans_headers_list = self.newModel.headersHorizontal
            for h in range(len(ktrans_headers_list)):
                ktrans_headers_list[h] = ktrans_headers_list[h].replace("R1 = ", "")
        elif self.type_of_data_loaded == "table":
            ktrans_headers_list = self.newModel.headers_Ktrans
        else:
            ktrans_headers_list = []

        for i in range(len(ktrans_headers_list)):
            if i == len(ktrans_headers_list)-1:
                results_table += str(ktrans_headers_list) + "\n"
            elif i > 0:
                results_table += str(ktrans_headers_list) + "\t"
            else:
                results_table += "Ref ktrans = \t"+ str(ktrans_headers_list) + "\t"
        
        Ktrans_data_list = [self.newModel.Ktrans_cal_patch_mean, self.newModel.Ktrans_cal_patch_median, self.newModel.Ktrans_cal_patch_deviation, 
        self.newModel.Ktrans_cal_patch_1stQuartile, self.newModel.Ktrans_cal_patch_3rdQuartile, self.newModel.Ktrans_cal_patch_min,
        self.newModel.Ktrans_cal_patch_max, self.newModel.Ktrans_rmsd, self.newModel.Ktrans_ccc, self.newModel.Ktrans_tdi, self.newModel.Ktrans_sigma_metric]

        if self.type_of_data_loaded == "table":
            results_table = addToTable(results_table, label_list, Ktrans_data_list)
        results_table += "All Regions Combined\nRMSD = \t"+str(self.newModel.Ktrans_rmsd_all_regions)+"\n"
        results_table += "Mean = \t"+str(self.newModel.Ktrans_cal_aggregate_mean)+"\n"
        results_table += "CCC = \t"+str(self.newModel.Ktrans_ccc_all_regions)+"\n"
        results_table += "TDI (Nonparametric) = \t"+str(self.newModel.Ktrans_tdi_all_regions)+"\n"
        results_table += "TDI (Parametric) = \t" + str(self.newModel.Ktrans_tdi_all_regions_method_2) + "\n"
        results_table += "Sigma metric = \t"+str(self.newModel.Ktrans_sigma_metric_all_regions)+"\n"
        results_table += "Mean bias = \t"+str(self.ktrans_mean_percent_bias)+"\n"
        results_table += "Variability (wSD) = \t" + str(self.newModel.Ktrans_cal_aggregate_deviation) + "\n"
        results_table += "Bland-Altman Lower Limit = \t" + str(self.ktrans_lower_sd_line_value) + "\n"
        results_table += "Bland-Altman Upper Limit = \t" + str(self.ktrans_upper_sd_line_value) + "\n"
        results_table += "Bland-Altman Repeatability Coefficient = \t" + str(self.ktrans_repeatability_coefficient) + "\n"
        results_table += "\n"

        if self.type_of_data_loaded == "image":
            ve_headers_list = self.newModel.headersHorizontal
            for h in range(len(ve_headers_list)):
                ve_headers_list[h] = ve_headers_list[h].replace("R1 = ", "")
        elif self.type_of_data_loaded == "table":
            ve_headers_list = self.newModel.headers_Ktrans
        else:
            ve_headers_list = []

        for i in range(len(ve_headers_list)):
            if i == len(ve_headers_list)-1:
                results_table += str(ve_headers_list) + "\n"
            elif i > 0:
                results_table += str(ve_headers_list) + "\t"
            else:
                results_table += "Ref ve = \t"+ str(ve_headers_list) + "\t"
                
        Ve_data_list = [self.newModel.Ve_cal_patch_mean, self.newModel.Ve_cal_patch_median, self.newModel.Ve_cal_patch_deviation, 
        self.newModel.Ve_cal_patch_1stQuartile, self.newModel.Ve_cal_patch_3rdQuartile, self.newModel.Ve_cal_patch_min,
        self.newModel.Ve_cal_patch_max, self.newModel.Ve_rmsd, self.newModel.Ve_ccc, self.newModel.Ve_tdi, self.newModel.Ve_sigma_metric]

        if self.type_of_data_loaded == "table":
            results_table = addToTable(results_table, label_list, Ve_data_list)
        results_table += "All Regions Combined\nRMSD = \t"+str(self.newModel.Ve_rmsd_all_regions)+"\n"
        results_table += "Mean = \t" + str(self.newModel.Ve_cal_aggregate_mean) + "\n"
        results_table += "CCC = \t"+str(self.newModel.Ve_ccc_all_regions)+"\n"
        results_table += "TDI (Nonparametric) = \t"+str(self.newModel.Ve_tdi_all_regions)+"\n"
        results_table += "TDI (Parametric) = \t" + str(self.newModel.Ve_tdi_all_regions_method_2) + "\n"
        results_table += "Sigma metric = \t"+str(self.newModel.Ve_sigma_metric_all_regions) + "\n"
        results_table += "Mean bias = \t"+str(self.ve_mean_percent_bias) + "\n"
        results_table += "Variability (wSD) = \t" + str(self.newModel.Ve_cal_aggregate_deviation) + "\n"
        results_table += "Bland-Altman Lower Limit = \t" + str(self.ve_lower_sd_line_value) + "\n"
        results_table += "Bland-Altman Upper Limit = \t" + str(self.ve_upper_sd_line_value) + "\n"
        results_table += "Bland-Altman Repeatability Coefficient = \t" + str(self.ve_repeatability_coefficient) + "\n"
        results_table += "\n"
        
        # If user entered .csv as the file extension, replace tabs in the
        # results_table with commas
        save_file_name = os.path.basename(save_path)
        if save_file_name.endswith(".csv") or save_file_name.endswith(".CSV") or save_file_name.endswith(".Csv"):
            results_table = results_table.replace("\t", ",")
        
        with open(save_path, "w") as output_file:
            try:
                output_file.write(results_table)
                self.SetStatusText(save_path + " saved successfully")
                return os.path.dirname(save_path)
            except IOError:
                self.SetStatusText("Error saving results table")
                wx.MessageBox("There was an error saving the results table", "Error Saving Results Table", wx.OK | wx.ICON_ERROR)
    
    def removeSubstring(self, string, substring):
        index = 0
        length = len(substring)
        while string.find(substring) != -1:
            index = string.find(substring)
            string = string[0:index] + string[index+length:]
        return string
    
                
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
        self.buttonEvaluate.Disable() #was commented-out

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
        editMenu.AppendSeparator()
        set_allowable_total_error = editMenu.Append(wx.ID_ANY, "Set Allowable Total Error...")
        editMenu.AppendSeparator()
        onVerboseMode = editMenu.AppendCheckItem(wx.ID_ANY, "Include Stat. Descriptions in Reports")

        # self.menubar.Bind(wx.EVT_MENU, self.OnEditImageDimension, OnEditImageDimension) #This function doesn't exist anymore
        self.Bind(wx.EVT_MENU, self.OnLoadRef_K, OnLoadRef_K)
        self.Bind(wx.EVT_MENU, self.OnLoadRef_V, OnLoadRef_V)
        self.Bind(wx.EVT_MENU, self.setAllowableTotalErrorMenu, set_allowable_total_error)
        self.Bind(wx.EVT_MENU, self.setVerboseMode, onVerboseMode)
        
        self.menubar.Insert(1, editMenu, "&Edit")
        self.SetMenuBar(self.menubar)
        
    def SetupRightClickMenu(self):
        # setup the popup menu on right click
        wx.EVT_RIGHT_DOWN(self.fileBrowser.GetTreeCtrl(), self.OnRightClick)
        self.popupMenu = wx.Menu()
        self.ID_POPUP_LOAD_CAL_K = wx.NewId()
        self.ID_POPUP_LOAD_CAL_V = wx.NewId()
        self.ID_POPUP_LOAD_MASK_KV = wx.NewId()

        OnLoadCal_K = wx.MenuItem(self.popupMenu, self.ID_POPUP_LOAD_CAL_K, 'Load as calculated Ktrans')
        OnLoadCal_V = wx.MenuItem(self.popupMenu, self.ID_POPUP_LOAD_CAL_V, 'Load as calculated Ve')
        OnLoadMask_KV = wx.MenuItem(self.popupMenu, self.ID_POPUP_LOAD_MASK_KV, 'Load as Mask')
        self.popupMenu.AppendItem(OnLoadCal_K)
        self.popupMenu.AppendItem(OnLoadCal_V)
        self.popupMenu.AppendItem(OnLoadMask_KV)
        wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_CAL_K, self.OnLoadCal_K)
        wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_CAL_V, self.OnLoadCal_V)
        wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_MASK_KV, self.OnLoadMask_KV)

    def SetupRightClickMenuForTextFiles(self):
        # setup the popup menu for right clicking on text files (.csv, .cdata, .txt)
        #print("SetupRightClickMenuForTestFiles (KV)") #for testing
        wx.EVT_RIGHT_DOWN(self.fileBrowser.GetTreeCtrl(), self.OnRightClick)
        self.popupMenuTextFiles = wx.Menu()
        self.ID_POPUP_LOAD_TEXT_FILE_K = wx.NewId()
        self.ID_POPUP_LOAD_TEXT_FILE_V = wx.NewId()
        self.ID_POPUP_LOAD_MASK_KV_TEXT = wx.NewId()
        
        OnLoadTextFile_K = wx.MenuItem(self.popupMenuTextFiles, self.ID_POPUP_LOAD_TEXT_FILE_K, "Load as Ktrans parameter text file")
        OnLoadTextFile_V = wx.MenuItem(self.popupMenuTextFiles, self.ID_POPUP_LOAD_TEXT_FILE_V, "Load as Ve parameter text file")
        OnLoadMask_KV = wx.MenuItem(self.popupMenuTextFiles, self.ID_POPUP_LOAD_MASK_KV_TEXT, "Load as Mask")
        self.popupMenuTextFiles.AppendItem(OnLoadTextFile_K)
        self.popupMenuTextFiles.AppendItem(OnLoadTextFile_V)
        self.popupMenuTextFiles.AppendItem(OnLoadMask_KV)
        wx.EVT_MENU(self.popupMenuTextFiles, self.ID_POPUP_LOAD_TEXT_FILE_K, self.OnLoadTextFile_K)
        wx.EVT_MENU(self.popupMenuTextFiles, self.ID_POPUP_LOAD_TEXT_FILE_V, self.OnLoadTextFile_V)
        wx.EVT_MENU(self.popupMenuTextFiles, self.ID_POPUP_LOAD_MASK_KV_TEXT, self.OnLoadMask_KV)
        
    def SetupPage_Histogram(self):
        # setup the histogram page
        self.figureHist_Ktrans = Figure()
        self.canvasHist_Ktrans = FigureCanvas(self.pageHistogram,-1, self.figureHist_Ktrans)

        self.figureHist_Ve = Figure()
        self.canvasHist_Ve = FigureCanvas(self.pageHistogram,-1, self.figureHist_Ve)

        self.verticalLineHist = wx.StaticLine(self.pageHistogram, -1, style=wx.LI_VERTICAL) # vertical line to separate the two subplots

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasHist_Ktrans, 35, wx.EXPAND)
        sizer.Add(self.verticalLineHist, 1, wx.EXPAND)
        sizer.Add(self.canvasHist_Ve, 35, wx.EXPAND)
        self.pageHistogram.SetSizer(sizer)

    def SetupPage_BlandAltmanPlot(self):
        #Set up the Bland Altman Limits of Agreement page
        self.figureLOA_Ktrans = Figure()
        self.canvasLOA_Ktrans = FigureCanvas(self.pageLOA, -1, self.figureLOA_Ktrans)
        
        self.figureLOA_Ve = Figure()
        self.canvasLOA_Ve = FigureCanvas(self.pageLOA, -1, self.figureLOA_Ve)

        self.figureLOA_description = Figure()
        self.canvasLOA_description = FigureCanvas(self.pageLOA, -1, self.figureLOA_description)

        self.horizontalLineLOA = wx.StaticLine(self.pageLOA, -1, style=wx.LI_HORIZONTAL) # horizontal line to separate the two subplots
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        if self.verbose_mode:
            proportions = [35,1,35,1]
        else:
            proportions = [46,2,46,6]

        sizer.Add(self.canvasLOA_Ktrans, proportions[0], wx.EXPAND)
        sizer.Add(self.horizontalLineLOA, proportions[1], wx.EXPAND)
        sizer.Add(self.canvasLOA_Ve, proportions[2], wx.EXPAND)
        sizer.Add(self.canvasLOA_description, proportions[3], wx.EXPAND)

        #sizer.Add(self.canvasLOA_Ktrans, 35, wx.EXPAND)
        #sizer.Add(self.horizontalLineLOA, 1, wx.EXPAND)
        #sizer.Add(self.canvasLOA_Ve, 35, wx.EXPAND)
        #if self.verbose_mode:
        #    proportion = 15
        #else:
        #    proportion = 1
        #sizer.Add(self.canvasLOA_description, proportion, wx.EXPAND)

        self.pageLOA.SetSizer(sizer)
        
    def ClearPage_Histogram(self):
        # clear the histogram page
        self.figureHist_Ktrans.clear()
        self.canvasHist_Ktrans.draw()
        self.figureHist_Ve.clear()
        self.canvasHist_Ve.draw()
        
    def ClearPage_BlandAltmanPlot(self):
        # clear the Bland Altman plot page
        self.figureLOA_Ktrans.clear()
        self.canvasLOA_Ktrans.draw()
        self.figureLOA_Ve.clear()
        self.canvasLOA_Ve.draw()
        self.figureLOA_description.clear()
        self.canvasLOA_description.draw()

    def GenerateModel(self):
        # generate the model for evaluation
        self.newModel = QIBA_model.Model_KV(self.path_ref_K, self.path_ref_V, self.path_cal_K, self.path_cal_V, [self.nrOfRow, self.nrOfColumn], self.allowable_total_error, self.mask, self.verbose_mode)

    def GenerateTableModel(self):
        """Generates the QIBA model if table-based data is supplied."""
        self.newModel = QIBA_table_model_KV(self.data_table_K_contents, self.data_table_V_contents, self.allowable_total_error, self.verbose_mode)
        
    def OnRightClick(self, event):
        # the right click action on the file list
        if (str(os.path.splitext(self.fileBrowser.GetPath())[1]) in self.supportedFileTypeList):
            self.PopupMenu(self.popupMenu, event.GetPosition())
        elif (str(os.path.splitext(self.fileBrowser.GetPath())[1]) in self.supportedTextFileTypeList):
            self.PopupMenu(self.popupMenuTextFiles, event.GetPosition())
        else:
            self.SetStatusText('Invalid file or path chosen.')

    def OnLoadCal_K(self, event):
        # pass the file path for loading
        self.path_cal_K = self.fileBrowser.GetPath()
        self.SetStatusText('Calculated Ktrans loaded.')
        if self.path_cal_V:
            self.buttonEvaluate.Enable()
            self.changeTabTitle("Table Viewer", "Image Viewer")
        else:
            self.buttonEvaluate.Disable()
        self.data_table_K = None
        self.path_qiba_table_K = None
        self.data_table_V = None
        self.path_qiba_table_V = None

    def OnLoadCal_V(self, event):
        # pass the file path for loading
        self.path_cal_V = self.fileBrowser.GetPath()
        self.SetStatusText('Calculated Ve loaded.')
        if self.path_cal_K:
            self.buttonEvaluate.Enable()
            self.changeTabTitle("Table Viewer", "Image Viewer")
        else:
            self.buttonEvaluate.Disable()
        self.data_table_K = None
        self.path_qiba_table_K = None
        self.data_table_V = None
        self.path_qiba_table_V = None

    def OnLoadMask_KV(self, event):
        # pass the mask file path for loading
        path = self.fileBrowser.GetPath()
        self.mask = self.loadMaskFile(path)
        self.SetStatusText('Mask Loaded.')

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
        
    def OnLoadTextFile_K(self, event):
        self.data_table_K = QIBA_table(self.fileBrowser.GetPath())
        self.data_table_K_contents = self.data_table_K.table_contents
        self.path_qiba_table_K = self.fileBrowser.GetPath()
        #result_image_type = self.data_table.getResultImageType() #Ktrans, Ve, or T1
        valid_table, error_message = self.data_table_K.validateTable()
        if not valid_table:
            self.SetStatusText("Error reading Ktrans table")
            wx.MessageBox(error_message, "Error Reading Ktrans Table", wx.OK | wx.ICON_ERROR)
            return
        self.SetStatusText("Ktrans table file loaded successfully.")
        if self.path_qiba_table_V:
            self.buttonEvaluate.Enable()
            self.changeTabTitle("Image Viewer", "Table Viewer")
        else:
            self.buttonEvaluate.Disable()
        self.path_cal_K = None
        self.path_cal_V = None
        
    def OnLoadTextFile_V(self, event):
        self.data_table_V = QIBA_table(self.fileBrowser.GetPath())
        self.data_table_V_contents = self.data_table_V.table_contents
        self.path_qiba_table_V = self.fileBrowser.GetPath()
        #result_image_type = self.data_table.getResultImageType() #Ktrans, Ve, or T1
        valid_table, error_message = self.data_table_V.validateTable()
        if not valid_table:
            self.SetStatusText("Error reading Ve table")
            wx.MessageBox(error_message, "Error Reading Ve Table", wx.OK | wx.ICON_ERROR)
            return
        self.SetStatusText("Ve table file loaded successfully.")
        if self.path_qiba_table_K:
            self.buttonEvaluate.Enable()
            self.changeTabTitle("Image Viewer", "Table Viewer")
        else:
            self.buttonEvaluate.Disable()
        self.path_cal_K = None
        self.path_cal_V = None
    
    def loadTextFileCmdLine_K(self, text_file_path):
        """Loads the ktrans table file specified by text_file_path.
        Use this function when the program is run from the command line
        """
        self.data_table_K = QIBA_table(text_file_path)
        self.data_table_K_contents = self.data_table_K.table_contents
        self.path_qiba_table_K = text_file_path
        valid_table, error_message = self.data_table_K.validateTable()
        if not valid_table:
            print("Error reading Ktrans table at\n"+text_file_path)
            print(error_message)
            return False
        print(text_file_path+" loaded successfully.")
        self.path_cal_K = None
        self.path_cal_V = None
        return True
        
    def loadTextFileCmdLine_V(self, text_file_path):
        """Loads the ve table file specified by text_file_path.
        Use this function when the program is run from the command line
        """
        self.data_table_V = QIBA_table(text_file_path)
        self.data_table_V_contents = self.data_table_V.table_contents
        self.path_qiba_table_V = text_file_path
        valid_table, error_message = self.data_table_V.validateTable()
        if not valid_table:
            print("Error reading Ve table at\n"+text_file_path)
            print(error_message)
            return False
        print(text_file_path+" loaded successfully.")
        self.path_cal_K = None
        self.path_cal_V = None
        return True
            
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
                processedData_Ktrans = QIBA_functions.DealNaN(self.newModel.Ktrans_cal[i][j])[0]
                processedData_Ktrans = QIBA_functions.DropNaN(processedData_Ktrans)
                if len(processedData_Ktrans )==0:
                    subPlot_K.plot([])
                    subPlot_K.xaxis.set_ticks([])
                    subPlot_K.yaxis.set_ticks([])
                else:
                    subPlot_K.hist(processedData_Ktrans, nrOfBins)
                    minPatch_K = numpy.min(processedData_Ktrans)
                    maxPatch_K = numpy.max(processedData_Ktrans)
                    meanPatch_K = numpy.mean(processedData_Ktrans)

                    minPatch_K = QIBA_functions.formatFloatTo2DigitsString(minPatch_K)
                    maxPatch_K = QIBA_functions.formatFloatTo2DigitsString(maxPatch_K)
                    meanPatch_K = QIBA_functions.formatFloatTo2DigitsString(meanPatch_K)
                    minPatch_K = minPatch_K.replace(":", "")
                    maxPatch_K = maxPatch_K.replace(":", "")

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
                processedData_Ve = QIBA_functions.DealNaN(self.newModel.Ve_cal[i][j])[0]
                processedData_Ve = QIBA_functions.DropNaN(processedData_Ve)
                if len(processedData_Ve)==0:
                    subPlot_V.plot([])
                    subPlot_V.xaxis.set_ticks([])
                    subPlot_V.yaxis.set_ticks([])
                else:
                    subPlot_V.hist(processedData_Ve, nrOfBins)
                    minPatch_V = numpy.min(processedData_Ve)
                    maxPatch_V = numpy.max(processedData_Ve)
                    meanPatch_V = numpy.mean(processedData_Ve)
                    minPatch_V = QIBA_functions.formatFloatTo2DigitsString(minPatch_V)
                    maxPatch_V = QIBA_functions.formatFloatTo2DigitsString(maxPatch_V)
                    meanPatch_V = QIBA_functions.formatFloatTo2DigitsString(meanPatch_V)
                    minPatch_V = minPatch_V.replace(":", "")
                    maxPatch_V = maxPatch_V.replace(":", "")

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
        OnHist_zoom_K = wx.MenuItem(self.popmenu_hist_K, self.ID_POPUP_HITS_ZOOM_K, 'Zoom')
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
        OnHist_zoom = wx.MenuItem(self.popmenu_hist_V, self.ID_POPUP_HITS_ZOOM_V, 'Zoom')
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

    def DrawHistogramsFromTable(self):
        """Draw histograms of imported calculated Ktrans and Ve table data, so that the user can have a look of the distribution of each patch."""
        ref_cal_Ktrans_groups = self.newModel.ref_cal_Ktrans_groups
        ref_cal_Ve_groups = self.newModel.ref_cal_Ve_groups
        
        nrOfBins = 10

        self.figureHist_Ktrans.suptitle('The histogram of the calculated Ktrans') #, fontsize = 18)
        self.figureHist_Ve.suptitle('The histogram of the calculated Ve') # , fontsize = 18)
        
        #1. Ktrans histogram: Extract data from Ktrans group list
        for i in range(len(ref_cal_Ktrans_groups)):
            unique_Ktrans_ref_group = ref_cal_Ktrans_groups[i]
            ref_Ktrans_data_list = list() #The list of reference values (raw data), extracted from ref_cal_group_list
            cal_Ktrans_data_list = list() #The list of calculated values (raw data), extracted from ref_cal_group_list
            ktrans_instances_counted_list = list()
            for t in range(len(unique_Ktrans_ref_group)):
                tpl = unique_Ktrans_ref_group[t]
                ref_Ktrans_data_list.append(tpl[0])
                cal_Ktrans_data_list.append(tpl[1])
                ktrans_instances_counted_list.append(tpl[3])
            
            #Draw one histogram for each reference Ktrans
            subPlot_K = self.figureHist_Ktrans.add_subplot(len(ref_cal_Ktrans_groups), 1, i)
            if sum(ktrans_instances_counted_list) == 0:
                subPlot_K.plot([])
                subPlot_K.xaxis.set_ticks([])
                subPlot_K.yaxis.set_ticks([])
            else:
                #Calculate weighted average of cal_Ktrans_data
                weighted_cal_Ktrans_data_list = list()
                for m in range(len(cal_Ktrans_data_list)):
                    cal_K = cal_Ktrans_data_list[m]
                    weight = ktrans_instances_counted_list[m]
                    for n in range(weight):
                        weighted_cal_Ktrans_data_list.append(cal_K)

                weighted_meanPatch_K = numpy.mean(weighted_cal_Ktrans_data_list)

                #Create the histogram
                subPlot_K.hist(weighted_cal_Ktrans_data_list, nrOfBins)
                weighted_minPatch_K = numpy.min(weighted_cal_Ktrans_data_list)
                weighted_maxPatch_K = numpy.max(weighted_cal_Ktrans_data_list)
                #meanPatch_K = numpy.mean(weighted_cal_Ktrans_data_list)
                weighted_minPatch_K = QIBA_functions_for_table.formatFloatTo2DigitsString(weighted_minPatch_K)
                weighted_maxPatch_K = QIBA_functions_for_table.formatFloatTo2DigitsString(weighted_maxPatch_K)
                weighted_meanPatch_K = QIBA_functions_for_table.formatFloatTo4DigitsString(weighted_meanPatch_K)
                
                subPlot_K.set_xticks([float(weighted_minPatch_K), float(weighted_maxPatch_K)])
                subPlot_K.set_xticklabels([weighted_minPatch_K, weighted_maxPatch_K], size="small")
                subPlot_K.axvline(float(weighted_meanPatch_K), color="r", linestyle="dashed", linewidth=1) #Draw a vertical line at the mean value
                subPlot_K.set_ylim([0,sum(ktrans_instances_counted_list)])
                subPlot_K.text(float(weighted_meanPatch_K) + 0.01 * float(weighted_meanPatch_K), 0.9 * sum(ktrans_instances_counted_list), weighted_meanPatch_K, size = 'x-small') # parameters: location_x, location_y, text, size

        #2. Ve histogram: Extract data from Ve group list
        for i in range(len(ref_cal_Ve_groups)):
            unique_Ve_ref_group = ref_cal_Ve_groups[i]
            ref_Ve_data_list = list() #The list of reference values (raw data), extracted from ref_cal_group_list
            cal_Ve_data_list = list() #The list of calculated values (raw data), extracted from ref_cal_group_list
            ve_instances_counted_list = list()
            for t in range(len(unique_Ve_ref_group)):
                tpl = unique_Ve_ref_group[t]
                ref_Ve_data_list.append(tpl[0])
                cal_Ve_data_list.append(tpl[1])
                ve_instances_counted_list.append(tpl[3])
            
            #Draw one histogram for each reference Ktrans
            subPlot_V = self.figureHist_Ve.add_subplot(len(ref_cal_Ve_groups), 1, i)
            if sum(ve_instances_counted_list) == 0:
                subPlot_V.plot([])
                subPlot_V.xaxis.set_ticks([])
                subPlot_V.yaxis.set_ticks([])
            else:
                #Calculate weighted average of cal_Ve_data
                weighted_cal_Ve_data_list = list()
                for m in range(len(cal_Ve_data_list)):
                    cal_V = cal_Ve_data_list[m]
                    weight = ve_instances_counted_list[m]
                    for n in range(weight):
                        weighted_cal_Ve_data_list.append(cal_V)

                weighted_meanPatch_V = numpy.mean(weighted_cal_Ve_data_list)

                #Create the histogram
                subPlot_V.hist(weighted_cal_Ve_data_list, nrOfBins)
                weighted_minPatch_V = numpy.min(weighted_cal_Ve_data_list)
                weighted_maxPatch_V = numpy.max(weighted_cal_Ve_data_list)
                #meanPatch_V = numpy.mean(weighted_cal_Ve_data_list)
                weighted_minPatch_V = QIBA_functions_for_table.formatFloatTo2DigitsString(weighted_minPatch_V)
                weighted_maxPatch_V = QIBA_functions_for_table.formatFloatTo2DigitsString(weighted_maxPatch_V)
                weighted_meanPatch_V = QIBA_functions_for_table.formatFloatTo4DigitsString(weighted_meanPatch_V)
                
                subPlot_V.set_xticks([float(weighted_minPatch_V), float(weighted_maxPatch_V)])
                subPlot_V.set_xticklabels([weighted_minPatch_V, weighted_maxPatch_V], size="small")
                subPlot_V.axvline(float(weighted_meanPatch_V), color="r", linestyle="dashed", linewidth=1) #Draw a vertical line at the mean value
                subPlot_V.set_ylim([0,sum(ve_instances_counted_list)])
                subPlot_V.text(float(weighted_meanPatch_V) + 0.01 * float(weighted_meanPatch_V), 0.9 * sum(ve_instances_counted_list), weighted_meanPatch_V, size = 'x-small') # parameters: location_x, location_y, text, size
         
        #3. Setup toolbars, menus, etc.
        #toolbars
        self.toolbar_hist_K = NavigationToolbar(self.canvasHist_Ktrans)
        self.toolbar_hist_K.Hide()
        self.toolbar_hist_V = NavigationToolbar(self.canvasHist_Ve)
        self.toolbar_hist_V.Hide()
        
        #right-click popup menu
        self.figureHist_Ktrans.canvas.mpl_connect("axes_enter_event", self.enter_axes)
        self.figureHist_Ktrans.canvas.mpl_connect("axes_leave_event", self.leave_axes)
        self.figureHist_Ve.canvas.mpl_connect("axes_enter_event", self.enter_axes)
        self.figureHist_Ve.canvas.mpl_connect("axes_leave_event", self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasHist_Ktrans, self.rightDown_hist_K)
        wx.EVT_RIGHT_DOWN(self.canvasHist_Ve, self.rightDown_hist_V)
        
        self.popmenu_hist_K = wx.Menu()
        self.ID_POPUP_HITS_PAN_K = wx.NewId()
        self.ID_POPUP_HITS_ZOOM_K = wx.NewId()
        self.ID_POPUP_HITS_SAVE_K = wx.NewId()
        
        OnHist_pan_K = wx.MenuItem(self.popmenu_hist_K, self.ID_POPUP_HITS_PAN_K, "Pan")
        OnHist_zoom_K = wx.MenuItem(self.popmenu_hist_K, self.ID_POPUP_HITS_ZOOM_K, "Zoom")
        OnHist_save_K = wx.MenuItem(self.popmenu_hist_K, self.ID_POPUP_HITS_SAVE_K, "Save")
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
        
        OnHist_pan_V = wx.MenuItem(self.popmenu_hist_V, self.ID_POPUP_HITS_PAN_V, "Pan")
        OnHist_zoom_V = wx.MenuItem(self.popmenu_hist_V, self.ID_POPUP_HITS_ZOOM_V, "Zoom")
        OnHist_save_V = wx.MenuItem(self.popmenu_hist_V, self.ID_POPUP_HITS_SAVE_V, "Save")
        self.popmenu_hist_V.AppendItem(OnHist_pan_V)
        self.popmenu_hist_V.AppendItem(OnHist_zoom_V)
        self.popmenu_hist_V.AppendItem(OnHist_save_V)
        wx.EVT_MENU(self.popmenu_hist_V, self.ID_POPUP_HITS_PAN_V, self.toolbar_hist_V.pan)
        wx.EVT_MENU(self.popmenu_hist_V, self.ID_POPUP_HITS_ZOOM_V, self.toolbar_hist_V.zoom)
        wx.EVT_MENU(self.popmenu_hist_V, self.ID_POPUP_HITS_SAVE_V, self.toolbar_hist_V.save_figure)
        
        #double-click
        wx.EVT_LEFT_DCLICK(self.canvasHist_Ktrans, self.toolbar_hist_K.home)
        wx.EVT_LEFT_DCLICK(self.canvasHist_Ve, self.toolbar_hist_V.home)
        
        #4. Draw the histograms        
        self.figureHist_Ktrans.tight_layout()
        self.figureHist_Ve.tight_layout()
        self.figureHist_Ktrans.subplots_adjust(top=0.94, right=0.95)
        self.figureHist_Ve.subplots_adjust(top=0.94, right=0.95)
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

    def rightDown_LOA_K(self, event):
        '''
        right-click on Ktrans LOA plot
        '''
        if self.IN_AXES:
            self.canvasLOA_Ktrans.PopupMenu(self.popmenu_LOA_K, event.GetPosition())
        else:
            pass
            
    def rightDown_LOA_V(self, event):
        '''
        right-click on Ve LOA plot
        '''
        if self.IN_AXES:
            self.canvasLOA_Ve.PopupMenu(self.popmenu_LOA_V, event.GetPosition())
        else:
            pass

    def DrawBlandAltmanPlot(self):
        #pyplt refers to matplotlib.pyplot
        ktrans_refData_nbp = numpy.asarray(self.newModel.Ktrans_ref_no_bad_pixels)
        ktrans_calData_nbp = numpy.asarray(self.newModel.Ktrans_cal_no_bad_pixels)
        ktrans_mask_nbp = self.newModel.Ktrans_mask_no_bad_pixels
        ve_refData_nbp = numpy.asarray(self.newModel.Ve_ref_no_bad_pixels)
        ve_calData_nbp = numpy.asarray(self.newModel.Ve_cal_no_bad_pixels)
        ve_mask_nbp = self.newModel.Ve_mask_no_bad_pixels
        
        ktrans_ref_total_pixels_counted = 0
        ktrans_cal_total_pixels_counted = 0
        ve_ref_total_pixels_counted = 0
        ve_cal_total_pixels_counted = 0
        i_dimension = len(ktrans_calData_nbp)
        j_dimension = len(ktrans_calData_nbp[0])
        
        ktrans_means_list = []
        ve_means_list = []
        ktrans_diffs_list = []
        ve_diffs_list = []
        ktrans_percent_bias_list = []
        ve_percent_bias_list = []
        
        for i in range(i_dimension):
            for j in range(j_dimension):
                ktrans_refData_nbp_10x10 = ktrans_refData_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)
                ktrans_calData_nbp_10x10 = ktrans_calData_nbp[i][j] #The 10x10 pixel patch or raw pixel data
                ktrans_mask_nbp_10x10 = ktrans_mask_nbp[i][j]
                ve_refData_nbp_10x10 = ve_refData_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)
                ve_calData_nbp_10x10 = ve_calData_nbp[i][j] #The 10x10 pixel patch or raw pixel data
                ve_mask_nbp_10x10 = ve_mask_nbp[i][j]

                ktrans_refData_nbp_10x10 = QIBA_functions.applyMask(ktrans_refData_nbp_10x10, ktrans_mask_nbp_10x10)
                ktrans_calData_nbp_10x10 = QIBA_functions.applyMask(ktrans_calData_nbp_10x10, ktrans_mask_nbp_10x10)
                ve_refData_nbp_10x10 = QIBA_functions.applyMask(ve_refData_nbp_10x10, ve_mask_nbp_10x10)
                ve_calData_nbp_10x10 = QIBA_functions.applyMask(ve_calData_nbp_10x10, ve_mask_nbp_10x10)

                ktrans_ref_pixels_counted_10x10 = len(ktrans_refData_nbp_10x10)
                ktrans_cal_pixels_counted_10x10 = len(ktrans_calData_nbp_10x10)
                ktrans_ref_total_pixels_counted += ktrans_ref_pixels_counted_10x10
                ktrans_cal_total_pixels_counted += ktrans_cal_pixels_counted_10x10
                ve_ref_pixels_counted_10x10 = len(ve_refData_nbp_10x10)
                ve_cal_pixels_counted_10x10 = len(ve_calData_nbp_10x10)
                ve_ref_total_pixels_counted += ve_ref_pixels_counted_10x10
                ve_cal_total_pixels_counted += ve_cal_pixels_counted_10x10
                
                if ktrans_cal_pixels_counted_10x10 > 0:
                    ref_mean = numpy.mean(ktrans_refData_nbp_10x10)
                    cal_mean = numpy.mean(ktrans_calData_nbp_10x10)
                    mean = numpy.mean([ref_mean, cal_mean])
                    difference = cal_mean - ref_mean
                    bias = ((cal_mean-ref_mean)/ref_mean) * 100.0
                    ktrans_means_list.append(mean)
                    ktrans_diffs_list.append(difference)
                    ktrans_percent_bias_list.append(bias)

                    
                if ve_cal_pixels_counted_10x10 > 0:
                    ref_mean = numpy.mean(ve_refData_nbp_10x10)
                    cal_mean = numpy.mean(ve_calData_nbp_10x10)
                    mean = numpy.mean([ref_mean, cal_mean])
                    difference = cal_mean - ref_mean
                    bias = ((cal_mean - ref_mean) / ref_mean) * 100.0
                    ve_means_list.append(mean)
                    ve_diffs_list.append(difference)
                    ve_percent_bias_list.append(bias)

        self.ktrans_mean_difference = numpy.mean(ktrans_diffs_list)  # The mean of the differences
        self.ktrans_sd_difference = numpy.std(ktrans_diffs_list)  # The standard deviation of the differences
        self.ktrans_mean_percent_bias = numpy.mean(ktrans_percent_bias_list)
        self.ve_mean_difference = numpy.mean(ve_diffs_list)
        self.ve_sd_difference = numpy.std(ve_diffs_list)
        self.ve_mean_percent_bias = numpy.mean(ve_percent_bias_list)

        # Setup the toolbars
        self.toolbar_LOA_K = NavigationToolbar(self.canvasLOA_Ktrans)
        self.toolbar_LOA_K.Hide()
        self.toolbar_LOA_V = NavigationToolbar(self.canvasLOA_Ve)
        self.toolbar_LOA_V.Hide()
        
        # Setup right-clicking
        self.figureLOA_Ktrans.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureLOA_Ktrans.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        self.figureLOA_Ve.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureLOA_Ve.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasLOA_Ktrans, self.rightDown_LOA_K)
        wx.EVT_RIGHT_DOWN(self.canvasLOA_Ve, self.rightDown_LOA_V)

        # Setup the pop-up menus that appear when user right-clicks
        self.popmenu_LOA_K = wx.Menu()
        self.ID_POPUP_LOA_PAN_K = wx.NewId()
        self.ID_POPUP_LOA_ZOOM_K = wx.NewId()
        self.ID_POPUP_LOA_SAVE_K = wx.NewId()
        OnLOA_pan_K = wx.MenuItem(self.popmenu_LOA_K, self.ID_POPUP_LOA_PAN_K, "Pan")
        OnLOA_zoom_K = wx.MenuItem(self.popmenu_LOA_K, self.ID_POPUP_LOA_ZOOM_K, "Zoom")
        OnLOA_save_K = wx.MenuItem(self.popmenu_LOA_K, self.ID_POPUP_LOA_SAVE_K, "Save")
        self.popmenu_LOA_K.AppendItem(OnLOA_pan_K)
        self.popmenu_LOA_K.AppendItem(OnLOA_zoom_K)
        self.popmenu_LOA_K.AppendItem(OnLOA_save_K)
        wx.EVT_MENU(self.popmenu_LOA_K, self.ID_POPUP_LOA_PAN_K, self.toolbar_LOA_K.pan)
        wx.EVT_MENU(self.popmenu_LOA_K, self.ID_POPUP_LOA_ZOOM_K, self.toolbar_LOA_K.zoom)
        wx.EVT_MENU(self.popmenu_LOA_K, self.ID_POPUP_LOA_SAVE_K, self.toolbar_LOA_K.save_figure)
        
        self.popmenu_LOA_V = wx.Menu()
        self.ID_POPUP_LOA_PAN_V = wx.NewId()
        self.ID_POPUP_LOA_ZOOM_V = wx.NewId()
        self.ID_POPUP_LOA_SAVE_V = wx.NewId()
        OnLOA_pan_V = wx.MenuItem(self.popmenu_LOA_V, self.ID_POPUP_LOA_PAN_V, "Pan")
        OnLOA_zoom_V = wx.MenuItem(self.popmenu_LOA_V, self.ID_POPUP_LOA_ZOOM_V, "Zoom")
        OnLOA_save_V = wx.MenuItem(self.popmenu_LOA_V, self.ID_POPUP_LOA_SAVE_V, "Save")
        self.popmenu_LOA_V.AppendItem(OnLOA_pan_V)
        self.popmenu_LOA_V.AppendItem(OnLOA_zoom_V)
        self.popmenu_LOA_V.AppendItem(OnLOA_save_V)
        wx.EVT_MENU(self.popmenu_LOA_V, self.ID_POPUP_LOA_PAN_V, self.toolbar_LOA_V.pan)
        wx.EVT_MENU(self.popmenu_LOA_V, self.ID_POPUP_LOA_ZOOM_V, self.toolbar_LOA_V.zoom)
        wx.EVT_MENU(self.popmenu_LOA_V, self.ID_POPUP_LOA_SAVE_V, self.toolbar_LOA_V.save_figure)
        
        # Draw the Bland-Altman plot for Ktrans
        font = {'fontname':'Arial', 'fontsize':12, 'weight':'bold'}
        ktrans_subplot = self.figureLOA_Ktrans.add_subplot(111)
        ktrans_subplot.scatter(ktrans_means_list, ktrans_diffs_list, s=50, marker=".") #s= size, c= color
        #  Should outliers be excluded when calculating mean_line and sd_lines?
        ktrans_mean_line = ktrans_subplot.axhline(self.ktrans_mean_difference, color="red", linestyle="--")
        #self.ktrans_upper_sd_line_value = ktrans_mean_difference + (1.96*ktrans_sd_difference)
        #self.ktrans_lower_sd_line_value = ktrans_mean_difference - (1.96*ktrans_sd_difference)
        #self.ktrans_repeatability_coefficient = 1.96 * ktrans_sd_difference
        t_statistic = scipy.stats.t.ppf(0.95, len(ktrans_diffs_list) - 1)
        self.ktrans_upper_sd_line_value = self.ktrans_mean_difference + (t_statistic*self.ktrans_sd_difference)
        self.ktrans_lower_sd_line_value = self.ktrans_mean_difference - (t_statistic*self.ktrans_sd_difference)
        self.ktrans_repeatability_coefficient = t_statistic * self.ktrans_sd_difference
        ktrans_upper_sd_line = ktrans_subplot.axhline(self.ktrans_upper_sd_line_value, color="gray", linestyle="--")
        ktrans_lower_sd_line = ktrans_subplot.axhline(self.ktrans_lower_sd_line_value, color="gray", linestyle="--")
        ktrans_subplot.set_xlabel("Mean of Reference and Calculated Ktrans", fontdict=font)
        ktrans_subplot.set_ylabel("Difference of Reference and Calculated Ktrans", fontdict=font)
        ktrans_subplot.legend( (ktrans_mean_line, ktrans_upper_sd_line), ("Mean Difference ("+str(self.ktrans_mean_difference)+")", \
        "95% Confidence Interval ("+str(self.ktrans_lower_sd_line_value)+", "+str(self.ktrans_upper_sd_line_value)+")"), loc="lower center", ncol=2, prop={'size':10})
        
        """
        #     Adjust scales of x- and y-axes. Avoid including outliers in determining the scale.
        ktrans_means_list_no_outliers, ktrans_means_limits = self.removeOutliers(ktrans_means_list)
        ktrans_diffs_list_no_outliers, ktrans_diffs_limits = self.removeOutliers(ktrans_diffs_list)
        print("ktrans_means_limits:") #for testing
        print(ktrans_means_limits) #for testing
        print("ktrans_diffs_limits:") #for testing
        print(ktrans_diffs_limits) #for testing
        x_min = min(ktrans_means_list_no_outliers) * 0.70
        x_max = max(ktrans_means_list_no_outliers) * 1.30
        #y_min = (ktrans_mean_difference - (1.96*ktrans_sd_difference)) * 1.30
        #y_max = (ktrans_mean_difference + (1.96*ktrans_sd_difference)) * 1.30
        y_min = min(ktrans_diffs_list_no_outliers) * 0.70
        y_max = max(ktrans_diffs_list_no_outliers) * 1.30
        print("x_min="+str(x_min)+", x_max="+str(x_max)+", y_min="+str(y_min)+", y_max="+str(y_max))
        ktrans_subplot.set_xlim(left=x_min, right=x_max, emit=True)
        ktrans_subplot.set_ylim(top=y_max, bottom=y_min, emit=True)
        # left off: plot outlier points - go through means and diffs lists at same time. identify x-y coordinates outside of x_min/x_max, y_min/y_max range 
        for i in range(0, len(ktrans_means_list)):
            if ktrans_means_list[i] > ktrans_means_limits[0] and ktrans_diffs_list[i] > ktrans_diffs_limits[0]: #mean is high outlier, diff is high outlier
                print("Values for drawing arrow in top-right corner: x_max="+str(x_max)+", y_max="+str(y_max))
                ktrans_subplot.arrow(x_max*0.99, y_max*0.99, x_max, y_max, width=(x_max*y_max*0.1), edgecolor="black", facecolor="black")
            elif ktrans_means_list[i] < ktrans_means_limits[1] and ktrans_diffs_list[i] < ktrans_diffs_limits[1]: #mean is low outlier, diff is low outlier
                ktrans_subplot.arrow(x_min*1.01, y_min*1.01, x_min, y_min, width=(x_max*y_max*0.1), edgecolor="black", facecolor="black")
            elif ktrans_means_list[i] > ktrans_means_limits[0] and ktrans_diffs_list[i] < ktrans_diffs_limits[1]: #mean is high outlier, diff is low outlier
                ktrans_subplot.arrow(x_max*0.99, y_min*1.01, x_max, y_min, width=(x_max*y_max*0.1), edgecolor="black", facecolor="black")
            elif ktrans_means_list[i] < ktrans_means_limits[1] and ktrans_diffs_list[i] > ktrans_diffs_limits[0]: #mean is low outlier, diff is high outlier
                ktrans_subplot.arrow(x_min*1.01, y_max*0.99, x_min, y_max, width=(x_max*y_max*0.1), edgecolor="black", facecolor="black")
            elif ktrans_means_list[i] > ktrans_means_limits[0]: #mean is high outlier, diff is not outlier
                ktrans_subplot.arrow(x_max*0.99, ktrans_diffs_list[i], x_max, ktrans_diffs_list[i], width=(x_max*y_max*0.1), edgecolor="black", facecolor="black")
            elif ktrans_means_list[i] < ktrans_means_limits[1]: #mean is low outlier, diff is not outlier
                ktrans_subplot.arrow(x_min*1.01, ktrans_diffs_list[i], x_min, ktrans_diffs_list[i], width=(x_max*y_max*0.1), edgecolor="black", facecolor="black")
            elif ktrans_diffs_list[i] > ktrans_diffs_limits[0]: #mean is not outlier, diff is high outlier
                ktrans_subplot.arrow(ktrans_means_list[i], y_max*0.99, ktrans_means_list[i], y_max, width=(x_max*y_max*0.1), edgecolor="black", facecolor="black")
            elif ktrans_diffs_list[i] < ktrans_diffs_limits[0]: #mean is not outlier, diff is low outlier
                ktrans_subplot.arrow(ktrans_means_list[i], y_min*1.01, ktrans_means_list[i], y_min, width=(x_max*y_max*0.1), edgecolor="black", facecolor="black")
        """
        
        self.figureLOA_Ktrans.tight_layout()
        #self.figureLOA_Ktrans.subplots_adjust(top=0.94, right=0.95)
        self.canvasLOA_Ktrans.draw()

        # Draw the Bland-Altman plot for Ve
        ve_subplot = self.figureLOA_Ve.add_subplot(111)
        ve_subplot.scatter(ve_means_list, ve_diffs_list, s=50, marker=".")
        ve_mean_line = ve_subplot.axhline(self.ve_mean_difference, color="red", linestyle="--")
        t_statistic = scipy.stats.t.ppf(0.95, len(ve_diffs_list) - 1)
        #self.ve_upper_sd_line_value = ve_mean_difference + (1.96*ve_sd_difference)
        #self.ve_lower_sd_line_value = ve_mean_difference - (1.96*ve_sd_difference)
        #self.ve_repeatability_coefficient = 1.96 * ve_sd_difference
        self.ve_upper_sd_line_value = self.ve_mean_difference + (t_statistic*self.ve_sd_difference)
        self.ve_lower_sd_line_value = self.ve_mean_difference - (t_statistic*self.ve_sd_difference)
        self.ve_repeatability_coefficient = t_statistic * self.ve_sd_difference
        ve_upper_sd_line = ve_subplot.axhline(self.ve_upper_sd_line_value, color="gray", linestyle="--")
        ve_lower_sd_line = ve_subplot.axhline(self.ve_lower_sd_line_value, color="gray", linestyle="--")
        ve_subplot.set_xlabel("Mean of Reference and Calculated Ve", fontdict=font)
        ve_subplot.set_ylabel("Difference of Reference and Calculated Ve", fontdict=font)
        #ve_subplot.legend( (ve_mean_line, ve_upper_sd_line), ("Mean Difference", "95% Confidence Interval"), loc="lower center", bbox_to_anchor=(0.5,-0.1), ncol=2, prop={'size':10})
        ve_subplot.legend( (ve_mean_line, ve_upper_sd_line), ("Mean Difference ("+str(self.ve_mean_difference)+")", \
        "95% Confidence Interval ("+str(self.ve_lower_sd_line_value)+", "+str(self.ve_upper_sd_line_value)+")"), loc="lower center", ncol=2, prop={'size':10})
        self.figureLOA_Ve.tight_layout()
        self.canvasLOA_Ve.draw()

        if self.verbose_mode:
            #description_subplot = self.figureLOA_description.add_subplot(111)
            self.figureLOA_description.text(0.2, 0.5, StatDescriptions.loa_text)
            #self.figureLOA_description.tight_layout()
            self.canvasLOA_description.draw()

        
    def DrawBlandAltmanPlotFromTable(self):
        ref_cal_Ktrans_groups = self.newModel.ref_cal_Ktrans_groups
        ref_cal_Ve_groups = self.newModel.ref_cal_Ve_groups
        
        #Get calculated Ktrans values
        unique_ref_Ktrans_values_list = [] #A list of each reference Ktrans value (i.e. [0.01, 0.02, 0.05, 0.1, 0.2, 0.35])
        all_ref_Ktrans_values_list = []
        all_cal_Ktrans_values_list = []
        
        for i in range(len(ref_cal_Ktrans_groups)):
            unique_Ktrans_ref_group = ref_cal_Ktrans_groups[i]
            #temp_temp = list()
            #ref_Ktrans_per_group_list = list() #The list of reference values (raw data), extracted from ref_cal_Ktrans_groups
            #cal_Ktrans_per_group_list = list() #The list of calculated values (raw data), extracted from ref_cal_Ktrans_groups
            ktrans_instances_counted_list = []
            
            for t in range(len(unique_Ktrans_ref_group)):
                tpl = unique_Ktrans_ref_group[t]
                #ref_Ktrans_per_group_list.append(tpl[0])
                #cal_Ktrans_per_group_list.append(tpl[1])
                ktrans_instances_counted_list.append(tpl[3])
                if t == 0:
                    unique_ref_Ktrans_values_list.append(tpl[0])
                all_ref_Ktrans_values_list.append(tpl[0])
                all_cal_Ktrans_values_list.append(tpl[1])
            #all_ref_Ktrans_values_list.append(ref_Ktrans_per_group_list)
            #all_cal_Ktrans_values_list.append(cal_Ktrans_per_group_list)
        
        #Calculate Ktrans mean and Ktrans diff
        ktrans_means_list = []
        ktrans_diffs_list = []
        ktrans_percent_bias_list = []
        
        for i in range(len(all_cal_Ktrans_values_list)):
            #ktrans_means_list.append(numpy.mean(all_cal_Ktrans_values_list[i]))
            mean_of_ktrans_ref_and_cal = numpy.mean([all_cal_Ktrans_values_list[i], all_ref_Ktrans_values_list[i]])
            ktrans_means_list.append(mean_of_ktrans_ref_and_cal)
            ktrans_diffs_list.append(all_cal_Ktrans_values_list[i] - all_ref_Ktrans_values_list[i])
            bias = ((all_cal_Ktrans_values_list[i]-all_ref_Ktrans_values_list[i])/all_ref_Ktrans_values_list[i])*100.0
            ktrans_percent_bias_list.append(bias)
        
        self.ktrans_mean_difference = numpy.mean(ktrans_diffs_list) #The mean of the differences
        self.ktrans_sd_difference = numpy.std(ktrans_diffs_list) #The standard deviation of the differences
        self.ktrans_mean_percent_bias = numpy.mean(ktrans_percent_bias_list)
        
        #Get calculated Ve values
        unique_ref_Ve_values_list = []
        all_ref_Ve_values_list = []
        all_cal_Ve_values_list = []
        
        for i in range(len(ref_cal_Ve_groups)):
            unique_Ve_ref_group = ref_cal_Ve_groups[i]
            ve_instances_counted_list = []
            
            for t in range(len(unique_Ve_ref_group)):
                tpl = unique_Ve_ref_group[t]
                ve_instances_counted_list.append(tpl[3])
                if t == 0 :
                    unique_ref_Ve_values_list.append(tpl[0])
                all_ref_Ve_values_list.append(tpl[0])
                all_cal_Ve_values_list.append(tpl[1])
                
        #Calculate Ve mean and Ve diff
        ve_means_list = []
        ve_diffs_list = []
        ve_percent_bias_list = []
        
        for i in range(len(all_cal_Ve_values_list)):
            #ve_means_list.append(numpy.mean(all_cal_Ve_values_list[i]))
            mean_of_ve_ref_and_cal = numpy.mean([all_cal_Ve_values_list[i], all_ref_Ve_values_list[i]])
            ve_means_list.append(mean_of_ve_ref_and_cal)
            ve_diffs_list.append(all_cal_Ve_values_list[i] - all_ref_Ve_values_list[i])
            bias = ((all_cal_Ve_values_list[i] - all_ref_Ve_values_list[i])/all_ref_Ve_values_list[i])*100.0
            ve_percent_bias_list.append(bias)
        
        self.ve_mean_difference = numpy.mean(ve_diffs_list) #The mean of the differences
        self.ve_sd_difference = numpy.std(ve_diffs_list) #The standard deviation of the differences
        self.ve_mean_percent_bias = numpy.mean(ve_percent_bias_list)
        
        # Setup the toolbars
        self.toolbar_LOA_K = NavigationToolbar(self.canvasLOA_Ktrans)
        self.toolbar_LOA_K.Hide()
        self.toolbar_LOA_V = NavigationToolbar(self.canvasLOA_Ve)
        self.toolbar_LOA_V.Hide()
        
        # Setup right-clicking
        self.figureLOA_Ktrans.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureLOA_Ktrans.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        self.figureLOA_Ve.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureLOA_Ve.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasLOA_Ktrans, self.rightDown_LOA_K)
        wx.EVT_RIGHT_DOWN(self.canvasLOA_Ve, self.rightDown_LOA_V)
        
        # Setup the pop-up menus that appear when user right-clicks
        self.popmenu_LOA_K = wx.Menu()
        self.ID_POPUP_LOA_PAN_K = wx.NewId()
        self.ID_POPUP_LOA_ZOOM_K = wx.NewId()
        self.ID_POPUP_LOA_SAVE_K = wx.NewId()
        OnLOA_pan_K = wx.MenuItem(self.popmenu_LOA_K, self.ID_POPUP_LOA_PAN_K, "Pan")
        OnLOA_zoom_K = wx.MenuItem(self.popmenu_LOA_K, self.ID_POPUP_LOA_ZOOM_K, "Zoom")
        OnLOA_save_K = wx.MenuItem(self.popmenu_LOA_K, self.ID_POPUP_LOA_SAVE_K, "Save")
        self.popmenu_LOA_K.AppendItem(OnLOA_pan_K)
        self.popmenu_LOA_K.AppendItem(OnLOA_zoom_K)
        self.popmenu_LOA_K.AppendItem(OnLOA_save_K)
        wx.EVT_MENU(self.popmenu_LOA_K, self.ID_POPUP_LOA_PAN_K, self.toolbar_LOA_K.pan)
        wx.EVT_MENU(self.popmenu_LOA_K, self.ID_POPUP_LOA_ZOOM_K, self.toolbar_LOA_K.zoom)
        wx.EVT_MENU(self.popmenu_LOA_K, self.ID_POPUP_LOA_SAVE_K, self.toolbar_LOA_K.save_figure)
        
        self.popmenu_LOA_V = wx.Menu()
        self.ID_POPUP_LOA_PAN_V = wx.NewId()
        self.ID_POPUP_LOA_ZOOM_V = wx.NewId()
        self.ID_POPUP_LOA_SAVE_V = wx.NewId()
        OnLOA_pan_V = wx.MenuItem(self.popmenu_LOA_V, self.ID_POPUP_LOA_PAN_V, "Pan")
        OnLOA_zoom_V = wx.MenuItem(self.popmenu_LOA_V, self.ID_POPUP_LOA_ZOOM_V, "Zoom")
        OnLOA_save_V = wx.MenuItem(self.popmenu_LOA_V, self.ID_POPUP_LOA_SAVE_V, "Save")
        self.popmenu_LOA_V.AppendItem(OnLOA_pan_V)
        self.popmenu_LOA_V.AppendItem(OnLOA_zoom_V)
        self.popmenu_LOA_V.AppendItem(OnLOA_save_V)
        wx.EVT_MENU(self.popmenu_LOA_V, self.ID_POPUP_LOA_PAN_V, self.toolbar_LOA_V.pan)
        wx.EVT_MENU(self.popmenu_LOA_V, self.ID_POPUP_LOA_ZOOM_V, self.toolbar_LOA_V.zoom)
        wx.EVT_MENU(self.popmenu_LOA_V, self.ID_POPUP_LOA_SAVE_V, self.toolbar_LOA_V.save_figure)

        # Draw the Bland-Altman plot for Ktrans
        font = {'fontname':'Arial', 'fontsize':12, 'weight':'bold'}
        ktrans_subplot = self.figureLOA_Ktrans.add_subplot(111)
        ktrans_subplot.scatter(ktrans_means_list, ktrans_diffs_list, s=50, marker=".") #s= size, c= color
        #  Should outliers be excluded when calculating mean_line and sd_lines?
        ktrans_mean_line = ktrans_subplot.axhline(self.ktrans_mean_difference, color="red", linestyle="--")
        #self.ktrans_upper_sd_line_value = ktrans_mean_difference + (1.96*ktrans_sd_difference)
        #self.ktrans_lower_sd_line_value = ktrans_mean_difference - (1.96*ktrans_sd_difference)
        #self.ktrans_repeatability_coefficient = 1.96 * ktrans_sd_difference
        t_statistic = scipy.stats.t.ppf(0.95, len(ktrans_diffs_list) - 1)
        self.ktrans_upper_sd_line_value = self.ktrans_mean_difference + (t_statistic*self.ktrans_sd_difference)
        self.ktrans_lower_sd_line_value = self.ktrans_mean_difference - (t_statistic*self.ktrans_sd_difference)
        self.ktrans_repeatability_coefficient = t_statistic * self.ktrans_sd_difference
        ktrans_upper_sd_line = ktrans_subplot.axhline(self.ktrans_upper_sd_line_value, color="gray", linestyle="--")
        ktrans_lower_sd_line = ktrans_subplot.axhline(self.ktrans_lower_sd_line_value, color="gray", linestyle="--")
        ktrans_subplot.set_xlabel("Mean of Reference and Calculated Ktrans", fontdict=font)
        ktrans_subplot.set_ylabel("Difference of Reference and Calculated Ktrans", fontdict=font)
        ktrans_subplot.legend( (ktrans_mean_line, ktrans_upper_sd_line), ("Mean Difference ("+str(self.ktrans_mean_difference)+")", \
        "95% Confidence Interval ("+str(self.ktrans_lower_sd_line_value)+", "+str(self.ktrans_upper_sd_line_value)+")"), loc="lower center", ncol=2, prop={'size':10})
        self.figureLOA_Ktrans.tight_layout()
        #self.figureLOA_Ktrans.subplots_adjust(top=0.94, right=0.95)
        self.canvasLOA_Ktrans.draw()
        
        # Draw the Bland-Altman plot for Ve
        ve_subplot = self.figureLOA_Ve.add_subplot(111)
        ve_subplot.scatter(ve_means_list, ve_diffs_list, s=50, marker=".")
        ve_mean_line = ve_subplot.axhline(self.ve_mean_difference, color="red", linestyle="--")
        #self.ve_upper_sd_line_value = ve_mean_difference + (1.96*ve_sd_difference)
        #self.ve_lower_sd_line_value = ve_mean_difference - (1.96*ve_sd_difference)
        #self.ve_repeatability_coefficient = 1.96 * ve_sd_difference
        t_statistic = scipy.stats.t.ppf(0.95, len(ve_diffs_list) - 1)
        self.ve_upper_sd_line_value = self.ve_mean_difference + (t_statistic * self.ve_sd_difference)
        self.ve_lower_sd_line_value = self.ve_mean_difference - (t_statistic * self.ve_sd_difference)
        self.ve_repeatability_coefficient = t_statistic * self.ve_sd_difference
        ve_upper_sd_line = ve_subplot.axhline(self.ve_upper_sd_line_value, color="gray", linestyle="--")
        ve_lower_sd_line = ve_subplot.axhline(self.ve_lower_sd_line_value, color="gray", linestyle="--")
        ve_subplot.set_xlabel("Mean of Reference and Calculated Ve", fontdict=font)
        ve_subplot.set_ylabel("Difference of Reference and Calculated Ve", fontdict=font)
        #ve_subplot.legend( (ve_mean_line, ve_upper_sd_line), ("Mean Difference", "95% Confidence Interval"), loc="lower center", bbox_to_anchor=(0.5,-0.1), ncol=2, prop={'size':10})
        ve_subplot.legend( (ve_mean_line, ve_upper_sd_line), ("Mean Difference ("+str(self.ve_mean_difference)+")", \
        "95% Confidence Interval ("+str(self.ve_lower_sd_line_value)+", "+str(self.ve_upper_sd_line_value)+")"), loc="lower center", ncol=2, prop={'size':10})
        self.figureLOA_Ve.tight_layout()
        self.canvasLOA_Ve.draw()

        if self.verbose_mode:
            #description_subplot = self.figureLOA_description.add_subplot(111)
            self.figureLOA_description.text(0.2, 0.5, StatDescriptions.loa_text)
            #self.figureLOA_description.tight_layout()
            self.canvasLOA_description.draw()
        
    def removeOutliers(self, original_list_outliers):
        """Remove outliers from the original_outliers list.
        Used to calculate scale for x- and y-axes for Bland-Altman plot.
        An outlier is defined as any point 1.5 IQRs above 3rd quartile or 1.5 IQRs below 1st quartile.
        
        Currently, this function is not used
        """
        percentile_25 = numpy.percentile(original_list_outliers, 25)
        percentile_75 = numpy.percentile(original_list_outliers, 75)
        iqr = percentile_75 - percentile_25
        upper_limit = percentile_75 + (1.5*iqr)
        lower_limit = percentile_25 - (1.5*iqr)
        list_no_outliers = [p for p in original_list_outliers if p < upper_limit and p > lower_limit]
        return list_no_outliers, [upper_limit, lower_limit]
    
    def DrawBoxPlot(self):
        '''
        draw box plots of each patch
        '''

        subPlotK = self.figureBoxPlot.add_subplot(2, 1, 1)
        subPlotK.clear()
        temp = []
        referValueK = []
        for i in range(self.newModel.nrOfRows):
            temp_temp = []
            for element in self.newModel.Ktrans_cal[i]:
                temp_temp.append(QIBA_functions.DealNaN(element)[0])
            temp.extend(temp_temp)

            #referValueK.append(float('{0:.2f}'.format(self.newModel.Ktrans_ref[i][0][0]))) #original line - Converts 0.1 to ERR
            
            #This works so far...
            k_string = str(self.newModel.Ktrans_ref[i][0][0]) #Convert numpy float64 to string
            k_float = float(k_string) #Convert string to built-in float type
            k_float_rounded = round(k_float, 2) #Round to at most 2 decimal places
            referValueK.append(k_float_rounded)
            
        subPlotK.boxplot(temp, notch = 1, sym = 'r+', whis=1.5)


        subPlotV = self.figureBoxPlot.add_subplot(2, 1, 2)
        subPlotV.clear()
        temp = []
        referValueV = []
        for j in range(self.newModel.nrOfColumns):
            for i in range(self.newModel.nrOfRows):
                # temp.append(self.newModel.Ve_cal[i][j])
                temp.append(QIBA_functions.DealNaN(self.newModel.Ve_cal[i][j])[0])
            
            #referValueV.append(float('{0:.2f}'.format(zip(*self.newModel.Ve_ref)[j][0][0]))) #original line - converts a valid float to ERR
            
            #This works so far...
            v_string = str(zip(*self.newModel.Ve_ref)[j][0][0]) #Convert numpy float64 to string
            v_float = float(v_string) #Convert string to built-in float type
            v_float_rounded = round(v_float, 2) #Round to at most 2 decimal places
            referValueV.append(v_float_rounded)
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
        OnBox_zoom = wx.MenuItem(self.popmenu_box, self.ID_POPUP_BOX_ZOOM, 'Zoom')
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

    def DrawBoxPlotFromTable(self):
        """Draw box plots from each Ktrans or Ve group"""
        ### To do: Add weighting to box plots
        
        #Setup Ktrans plot
        ref_cal_Ktrans_groups = self.newModel.ref_cal_Ktrans_groups
        subPlotK = self.figureBoxPlot.add_subplot(2, 1, 1)
        subPlotK.clear()
    
        #Get calculated Ktrans values
        unique_ref_Ktrans_values_list = list() #A list of each reference Ktrans value (i.e. [0.01, 0.02, 0.05, 0.1, 0.2, 0.35])
        all_cal_Ktrans_values_list = list()
        
        for i in range(len(ref_cal_Ktrans_groups)):
            unique_Ktrans_ref_group = ref_cal_Ktrans_groups[i]
            #temp_temp = list()
            ref_Ktrans_per_group_list = list() #The list of reference values (raw data), extracted from ref_cal_Ktrans_groups
            cal_Ktrans_per_group_list = list() #The list of calculated values (raw data), extracted from ref_cal_Ktrans_groups
            ktrans_instances_counted_list = list()
            
            for t in range(len(unique_Ktrans_ref_group)):
                tpl = unique_Ktrans_ref_group[t]
                ref_Ktrans_per_group_list.append(tpl[0])
                cal_Ktrans_per_group_list.append(tpl[1])
                ktrans_instances_counted_list.append(tpl[3])
                if t == 0:
                    unique_ref_Ktrans_values_list.append(tpl[0])
            all_cal_Ktrans_values_list.append(cal_Ktrans_per_group_list)
                
        #Setup Ve plot
        ref_cal_Ve_groups = self.newModel.ref_cal_Ve_groups
        subPlotV = self.figureBoxPlot.add_subplot(2, 1, 2)
        subPlotV.clear()
        
        #Get calculated Ve values
        unique_ref_Ve_values_list = list() #A list of each reference Ve value
        all_cal_Ve_values_list = list()
        
        for i in range(len(ref_cal_Ve_groups)):
            unique_Ve_ref_group = ref_cal_Ve_groups[i]
            ref_Ve_per_group_list = list() #The list of reference values (raw data), extracted from ref_cal_Ve_groups
            cal_Ve_per_group_list = list() #The list of calculated values (raw data), extracted from ref_cal_Ve_groups
            ve_instances_counted_list = list()
            
            for t in range(len(unique_Ve_ref_group)):
                tpl = unique_Ve_ref_group[t]
                ref_Ve_per_group_list.append(tpl[0])
                cal_Ve_per_group_list.append(tpl[1])
                ve_instances_counted_list.append(tpl[3])
                if t == 0:
                    unique_ref_Ve_values_list.append(tpl[0])
            all_cal_Ve_values_list.append(cal_Ve_per_group_list)
            
        #Draw Ktrans box plot
        subPlotK.boxplot(all_cal_Ktrans_values_list, notch = False, sym = 'r+', whis=1.5)
        
        # decorate Ktrans plot
        subPlotK.set_title("Box plot of calculated Ktrans")
        #subPlotK.set_xlabel('In each column, each box plot denotes Ve = ' + str(referValueV) + ' respectively')
        subPlotK.set_ylabel("Calculated values")

        subPlotK.xaxis.set_major_formatter(ticker.NullFormatter())
        subPlotK.set_xticklabels(unique_ref_Ktrans_values_list)
        subPlotK.xaxis.set_minor_formatter(ticker.IndexFormatter(unique_ref_Ktrans_values_list))
        for i in range(len(ref_cal_Ktrans_groups)):
            subPlotK.axvline(x = i + 0.5, color = 'green', linestyle = 'dashed')

        self.figureBoxPlot.tight_layout()
        self.canvasBoxPlot.draw()
        self.rightPanel.Layout()

        #Draw Ve box plot
        subPlotV.boxplot(all_cal_Ve_values_list, notch = False, sym = "r+", whis=1.5)
        
        # decorate Ve plot
        subPlotV.set_title("Box plot of calculated Ve")
        subPlotV.set_ylabel("Calculated values")
        
        subPlotV.xaxis.set_major_formatter(ticker.NullFormatter())
        subPlotV.set_xticklabels(unique_ref_Ve_values_list)
        subPlotV.xaxis.set_minor_formatter(ticker.IndexFormatter(unique_ref_Ve_values_list))
        for i in range(len(ref_cal_Ve_groups)):
            subPlotV.axvline(x = i + 0.5, color = "green", linestyle = "dashed")
        
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
        OnBox_zoom = wx.MenuItem(self.popmenu_box, self.ID_POPUP_BOX_ZOOM, 'Zoom')
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
        #if self.type_of_data_loaded == "image":
        #    if not isinstance(self.figureImagePreview, Figure):
        #        self.figureImagePreview = Figure()
        #self.figureImagePreview = Figure()
        
        ##self.figureImagePreview = Figure()
        ##self.canvasImagePreview = FigureCanvas(self.pageImagePreview, -1, self.figureImagePreview)
        ##sizer = wx.BoxSizer(wx.HORIZONTAL)
        ##sizer.Add(self.canvasImagePreview, 1, wx.EXPAND)
        ##self.pageImagePreview.SetSizer(sizer, deleteOld=True)

        #New 8/29/16
        self.imagePreviewSizer.Show(self.canvasImagePreview, show=True)
        self.imagePreviewSizer.Show(self.tableViewer, show=False)
        self.tableViewer.SetPage("")
        self.pageImagePreview.Layout() #Resizes the tab's contents and ensures that its contents are displayed correctly. Required since tab is changed after it is initally drawn.
        #End new 8/29/16

        self.PlotPreview([[self.newModel.Ktrans_cal_inRow, self.newModel.Ktrans_error, self.newModel.Ktrans_error_normalized], \
            [self.newModel.Ve_cal_inRow, self.newModel.Ve_error, self.newModel.Ve_error_normalized]], \

            [['Calculated Ktrans', 'Error map of Ktrans', 'Normalized Error map of Ktrans'], \
            ['Calculated Ve', 'Error map of Ve', 'Normalized Error map of Ve']], \
            [['bone', 'rainbow', 'rainbow'], ['bone', 'rainbow', 'rainbow']], \
            [['Ktrans[1/min]', 'Delta Ktrans[1/min.]', 'Normalized error[%]'], ['Ve[]', 'Delta Ve[]', 'Normalized error[%]']])
        
    def DrawTable(self):
        """Draws the table in the Table Viewer tab. Used when table data is loaded."""
        
        #Make HTML versions of the Ktrans and Ve table data
        Ktrans_table_in_html = QIBA_functions_for_table.putRawDataTableInHtml(self.data_table_K)
        Ve_table_in_html = QIBA_functions_for_table.putRawDataTableInHtml(self.data_table_V)
        
        #Now defined in SetupRight
        #self.imagePreviewViewer = wx.html.HtmlWindow(self.pageImagePreview, -1, style=wx.html.HW_SCROLLBAR_AUTO | wx.ALWAYS_SHOW_SB)
        
        #Changed: The sizer for the image preview window is now an instance variable.
        #(original) sizer = wx.BoxSizer(wx.VERTICAL)
        #(original) sizer.Add(self.imagePreviewViewer, 1, wx.EXPAND)
        #(original) self.pageImagePreview.SetSizer(sizer, deleteOld=True)
        #(original) self.pageImagePreview.SetAutoLayout(1)
        #self.pageImagePreview.SetupScrolling()

        self.imagePreviewSizer.Show(self.canvasImagePreview, show=False)
        self.imagePreviewSizer.Show(self.tableViewer, show=True)
        self.figureImagePreview.clf() # Clears the Image Preview window
        self.pageImagePreview.Layout() #Resizes the tab's contents and ensures that its contents are displayed correctly. Required since tab is changed after it is initally drawn.
        #self.pageImagePreview.SetupScrolling()
        htmlText = """
        <!DOCTYPE html>
        <html>
        <body>
        """
        htmlText += "<small>Click anywhere in the table to activate scrolling.</small>"
        htmlText += "<h2>The original Ktrans data table</h2>"
        htmlText += Ktrans_table_in_html
        htmlText += "<h2>The original Ve data table</h2>"
        htmlText += Ve_table_in_html
        
        htmlText += """
        </body>
        </html>
        """
        self.tableViewer.SetPage(htmlText)
        #self.imagePreviewViewer.Bind(wx.EVT_ACTIVATE, self.ActivateTest)
        #self.buttonSwitch.Bind(wx.EVT_BUTTON, self.OnSwitchViewing)
        #wx.EVT_ACTIVATE(self.pageImagePreview, self.ActivateTest())
        
        
    def DrawScatter(self):
        # draw the scatters
        if self.SCATTER_SWITCH:
            minLim_x_K = numpy.nanmin(self.newModel.Ktrans_ref_inRow)
            maxLim_x_K = numpy.nanmax(self.newModel.Ktrans_ref_inRow)
            minLim_y_K = numpy.nanmin( [numpy.min(self.newModel.Ktrans_ref_inRow), numpy.min(self.newModel.Ktrans_cal_inRow)])
            maxLim_y_K = numpy.nanmax( [numpy.max(self.newModel.Ktrans_ref_inRow), numpy.max(self.newModel.Ktrans_cal_inRow)])

            minLim_x_V = numpy.nanmin(self.newModel.Ve_ref_inRow)
            maxLim_x_V = numpy.nanmax(self.newModel.Ve_ref_inRow)
            minLim_y_V = numpy.nanmin( [numpy.min(self.newModel.Ve_ref_inRow), numpy.min(self.newModel.Ve_cal_inRow)])
            maxLim_y_V = numpy.nanmax( [numpy.max(self.newModel.Ve_ref_inRow), numpy.max(self.newModel.Ve_cal_inRow)])
        else:
            minLim_x_K = numpy.nanmin(self.newModel.Ktrans_ref_patchValue)
            maxLim_x_K = numpy.nanmax(self.newModel.Ktrans_ref_patchValue)
            minLim_y_K = numpy.nanmin( [numpy.min(self.newModel.Ktrans_ref_patchValue), numpy.min(self.newModel.Ktrans_cal_patchValue)])
            maxLim_y_K = numpy.nanmax( [numpy.max(self.newModel.Ktrans_ref_patchValue), numpy.max(self.newModel.Ktrans_cal_patchValue)])

            minLim_x_V = numpy.nanmin(self.newModel.Ve_ref_patchValue)
            maxLim_x_V = numpy.nanmax(self.newModel.Ve_ref_patchValue)
            minLim_y_V = numpy.nanmin( [numpy.min(self.newModel.Ve_ref_patchValue), numpy.min(self.newModel.Ve_cal_patchValue)])
            maxLim_y_V = numpy.nanmax( [numpy.max(self.newModel.Ve_ref_patchValue), numpy.max(self.newModel.Ve_cal_patchValue)])
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
                            
    def DrawScatterFromTable(self):
        """Creates the scatter plot when table data is loaded"""
        
        # Lists of reference (nominal) Ktrans and Ve values
        # (parameter8 or index 7 using 0-based indexing)
        ref_Ktrans_list = self.newModel.getValuesFromTable(self.data_table_K_contents, 7, datatype="float")
        ref_Ve_list = self.newModel.getValuesFromTable(self.data_table_V_contents, 7, datatype="float")
        
        # Lists of calculated Ktrans and Ve values
        # (parameter9 or index 8 using 0-based indexing)
        cal_Ktrans_list = self.newModel.getValuesFromTable(self.data_table_K_contents, 8, datatype="float")
        cal_Ve_list = self.newModel.getValuesFromTable(self.data_table_V_contents, 8, datatype="float")
        
        minLim_x_K = numpy.nanmin(ref_Ktrans_list)
        maxLim_x_K = numpy.nanmax(ref_Ktrans_list)
        minLim_y_K = numpy.nanmin( [numpy.min(ref_Ktrans_list), numpy.min(cal_Ktrans_list)])
        maxLim_y_K = numpy.nanmax( [numpy.max(ref_Ktrans_list), numpy.max(cal_Ktrans_list)])

        minLim_x_V = numpy.nanmin(ref_Ve_list)
        maxLim_x_V = numpy.nanmax(ref_Ve_list)
        minLim_y_V = numpy.nanmin( [numpy.min(ref_Ve_list), numpy.min(cal_Ve_list)])
        maxLim_y_V = numpy.nanmax( [numpy.max(ref_Ve_list), numpy.max(cal_Ve_list)])
        
        spacing_x_K = (maxLim_x_K - minLim_x_K) * 0.05
        spacing_y_K = (maxLim_y_K - minLim_y_K) * 0.05
        spacing_x_V = (maxLim_x_V - minLim_x_V) * 0.05
        spacing_y_V = (maxLim_y_V - minLim_y_V) * 0.05
        
        self.PlotScatter([[cal_Ktrans_list], [cal_Ve_list]], \
            [[ref_Ktrans_list], [ref_Ve_list]], \
            [['Reference Ktrans'], ['Reference Ve']], \
            [['Calculated Ktrans'], ['Calculated Ve']], \
            [['Distribution plot of Ktrans'], ['Distribution plot of Ve']], \
            [[minLim_x_K - spacing_x_K, maxLim_x_K + spacing_x_K], [minLim_x_V - spacing_x_V, maxLim_x_V + spacing_x_V]], \
            [[minLim_y_K - spacing_y_K, maxLim_y_K + 2*spacing_y_K], [minLim_y_V - spacing_y_V, maxLim_y_V + 2*spacing_y_V]])

    def OnExportToFolder(self, desDir):
        '''
        export the files as .png, excel
        '''
        #saveDir = os.getcwd()
        saveDir = desDir
        if not (desDir == ''):
            saveDir = desDir
        elif desDir == '':
            dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
            if dlg.ShowModal() == wx.ID_OK:
                saveDir = dlg.GetPath()
            else:
                return
        self.SetStatusText('Exporting, please wait...')
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

        try:
            self.figureLOA_Ktrans.savefig(os.path.join(saveDir, 'limits_of_agreement_K.png'))
        except:
            self.SetStatusText('Please close related LOA Ktrans files and try to export again.')
            return
        
        try:
            self.figureLOA_Ve.savefig(os.path.join(saveDir, 'limits_of_agreement_V.png'))
        except:
            self.SetStatusText('Please close related LOA Ve files and try to export again.')
            
        # export the table to excel
        book = Workbook()
        sheetNaN = book.add_sheet('NaN percentage')
        sheetMean = book.add_sheet('Mean')
        sheetStd = book.add_sheet('Standard deviation')
        sheetMedian = book.add_sheet('Median')
        sheet1Qtl = book.add_sheet('1st quartiel')
        sheet3Qtl = book.add_sheet('3rd quartiel')
        sheetMin = book.add_sheet('Minimum')
        sheetMax = book.add_sheet('Maximum')
        sheetCov = book.add_sheet('Covariance')
        sheetCor = book.add_sheet('Correlation')
        sheetRMSD = book.add_sheet('RMSD')
        sheetCCC = book.add_sheet('CCC')
        sheetTDI = book.add_sheet('TDI')
        #sheetLOA = book.add_sheet('LOA')
        sheetSigmaMetric = book.add_sheet('Sigma Metric')
        sheetFit = book.add_sheet('Model fitting')
        sheetT = book.add_sheet('T-test results')
        sheetU = book.add_sheet('U-test results')
        sheetChiq = book.add_sheet('Chi-square test results')
        sheetA = book.add_sheet('ANOVA results')

        QIBA_functions.WriteToExcelSheet_GKM_percentage(sheetNaN, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_NaN_percentage, self.newModel.Ve_NaN_percentage], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetMean, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_mean, self.newModel.Ve_cal_patch_mean], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetStd, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_deviation, self.newModel.Ve_cal_patch_deviation], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetMedian, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_median, self.newModel.Ve_cal_patch_median], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheet1Qtl, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_1stQuartile, self.newModel.Ve_cal_patch_1stQuartile], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheet3Qtl, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_3rdQuartile, self.newModel.Ve_cal_patch_3rdQuartile], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetMin, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_min, self.newModel.Ve_cal_patch_min], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetMax, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_max, self.newModel.Ve_cal_patch_max], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)

        QIBA_functions.WriteToExcelSheet_GKM_co(sheetCor, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.corr_KK,self.newModel.corr_KV,self.newModel.corr_VK,self.newModel.corr_VV], 1, self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_co(sheetCov, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.cov_KK,self.newModel.cov_KV,self.newModel.cov_VK,self.newModel.cov_VV], 1, self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetRMSD, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_rmsd, self.newModel.Ve_rmsd], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetCCC, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_ccc, self.newModel.Ve_ccc], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetTDI, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_tdi, self.newModel.Ve_tdi], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        #QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetLOA, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_loa, self.newModel.Ve_loa], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_GKM_statistics(sheetSigmaMetric, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_sigma_metric, self.newModel.Ve_sigma_metric], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)

        QIBA_functions.WriteToExcelSheet_GKM_fit(sheetFit, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.a_lin_Ktrans, self.newModel.b_lin_Ktrans, self.newModel.r_squared_lin_K, self.newModel.a_log_Ktrans,self.newModel.b_log_Ktrans,self.newModel.a_lin_Ve, self.newModel.b_lin_Ve, self.newModel.r_squared_lin_V, self.newModel.a_log_Ve,self.newModel.b_log_Ve], 1, self.nrOfRow, self.nrOfColumn)

        QIBA_functions.WriteToExcelSheet_GKM_test(sheetT, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_ttest_t, self.newModel.Ktrans_cal_patch_ttest_p, self.newModel.Ve_cal_patch_ttest_t, self.newModel.Ve_cal_patch_ttest_p], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn, 'T-statistics')
        QIBA_functions.WriteToExcelSheet_GKM_test(sheetU, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_Utest_u, self.newModel.Ktrans_cal_patch_Utest_p, self.newModel.Ve_cal_patch_Utest_u, self.newModel.Ve_cal_patch_Utest_p], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn, 'U-value')

        QIBA_functions.WriteToExcelSheet_GKM_A(sheetA, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_ANOVA_f,self.newModel.Ktrans_cal_patch_ANOVA_p,self.newModel.Ve_cal_patch_ANOVA_f,self.newModel.Ve_cal_patch_ANOVA_p], 1, self.nrOfRow, self.nrOfColumn)

        QIBA_functions.WriteToExcelSheet_GKM_test(sheetChiq, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.Ktrans_cal_patch_Chisquare_c, self.newModel.Ktrans_cal_patch_Chisquare_p, self.newModel.Ve_cal_patch_Chisquare_c, self.newModel.Ve_cal_patch_Chisquare_p], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn, 'Chiq')

        try:
            book.save(os.path.join(saveDir, 'results.xls'))
        except:
            self.SetStatusText('Please close related files and try to export again.')
            return

        self.SetStatusText('Files are exported.')



    def GetResultInHtml(self):
        # render the figures, tables into html, for exporting to pdf
        htmlContent = ''
        self.figureImagePreview.savefig(os.path.join(os.getcwd(), 'temp', 'figureImages.png'))
        self.figureScatter.savefig(os.path.join(os.getcwd(), 'temp', 'figureScatters.png'))
        self.figureHist_Ktrans.savefig(os.path.join(os.getcwd(), 'temp', 'figureHist_K.png'))
        self.figureHist_Ve.savefig(os.path.join(os.getcwd(), 'temp', 'figureHist_V.png'))
        self.figureBoxPlot.savefig(os.path.join(os.getcwd(), 'temp', 'figureBoxPlots.png'))
        self.figureLOA_Ktrans.savefig(os.path.join(os.getcwd(), 'temp', 'figureLOA_K.png'))
        self.figureLOA_Ve.savefig(os.path.join(os.getcwd(), 'temp', 'figureLOA_V.png'))

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

        htmlContent += self.newModel.NaNPercentageInHTML

        htmlContent += self.newModel.StatisticsInHTML

        htmlContent += self.newModel.covCorrResultsInHtml

        htmlContent += self.newModel.RMSDResultInHTML

        htmlContent += self.newModel.CCCResultInHTML
        
        htmlContent += self.newModel.TDIResultInHTML

        htmlContent += self.newModel.packInHtml('''
        <h2 align="center">The Bland-Altman Limits of Agreement plots of calculated Ktrans and Ve</h2>
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureLOA_K.png') + '''" style="width:100%" align="left">''' + '''
        <p><h4>The repeatability coefficient is '''+str(self.ktrans_repeatability_coefficient)+'''</h4></p>
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureLOA_V.png') + '''" style="width:100%" align="right">''' + '''
        <p><h4>The repeatability coefficient is '''+str(self.ve_repeatability_coefficient)+'''</h4></p>
        </p></p>''')

        if self.verbose_mode:
            htmlContent += "<p><h5>" + StatDescriptions.loa_text + "</h5></p>"

        htmlContent += self.newModel.sigmaMetricResultInHTML

        htmlContent += self.newModel.ModelFittingInHtml

        htmlContent += self.newModel.T_testResultInHTML

        htmlContent += self.newModel.U_testResultInHTML

        htmlContent += self.newModel.Chiq_testResultInHTML

        htmlContent += self.newModel.ANOVAResultInHTML

        return htmlContent

class MainWindow_T1(MainWindow):
    '''
    this is the Ktrans-Ve branch's interface.
    '''
    def __init__(self, appName, calFiles, refFiles, desDir, verbose_mode):
        MainWindow.__init__(self, None, appName, calFiles, refFiles, desDir, verbose_mode)

        self.patchLen = 10
        self.WARNINGTEXT = False

        # default files' paths
        if refFiles:
            self.path_ref_T1 = refFiles
        else:
            self.path_ref_T1 = os.path.join(os.getcwd(), 'reference_data', 'T1.tif')

        if calFiles:
            self.path_cal_T1 = calFiles
        else:
            self.path_cal_T1 = ''

        self.T1_R1_flag = "T1" # By default, assume T1 image data is loaded

        self.path_qiba_table_T1 = ""
        
        # customize the main window
        self.LoadRef()
        self.SetupStartPage()
        self.SetupEditMenu()
        self.SetupRightClickMenu()
        self.SetupRightClickMenuForTextFiles()
        self.mask = self.CreateDefaultMask(self.nrOfRow, self.nrOfColumn, self.patchLen)

    def SetupPage_BoxPlot(self):
        self.figureBoxPlot = Figure()
        w, h = self.figureBoxPlot.get_size_inches()
        self.figureBoxPlot.set_size_inches([w*3, h])
        self.canvasBoxPlot = FigureCanvas(self.pageBoxPlot,-1, self.figureBoxPlot)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasBoxPlot, 1, wx.EXPAND)
        self.pageBoxPlot.SetSizer(sizer)
        self.pageBoxPlot.SetAutoLayout(1)
        self.pageBoxPlot.SetupScrolling()

    def ShowResults(self):
        # show the results in the main window
        self.NaNViewer.SetPage(self.newModel.NaNPercentageInHTML)
        self.statisticsViewer.SetPage(self.newModel.GetStatisticsInHTML())
        self.covCorrViewer.SetPage(self.newModel.GetCovarianceCorrelationInHTML())
        self.modelFittingViewer.SetPage(self.newModel.GetModelFittingInHTML())
        self.rmsdViewer.SetPage(self.newModel.RMSDResultInHTML)
        self.cccViewer.SetPage(self.newModel.CCCResultInHTML)
        self.tdiViewer.SetPage(self.newModel.TDIResultInHTML)
        #self.loaViewer.SetPage(self.newModel.LOAResultInHTML)
        self.sigmaMetricViewer.SetPage(self.newModel.sigmaMetricResultInHTML)
        self.t_testViewer.SetPage(self.newModel.GetT_TestResultsInHTML())
        self.U_testViewer.SetPage(self.newModel.GetU_TestResultsInHTML())
        self.ChiqViewer.SetPage(self.newModel.ChiSquareTestResultInHTML)

        self.IN_AXES = False

        if self.type_of_data_loaded == "image":
            self.DrawMaps()
            self.DrawScatter()
            self.DrawHistograms()
            self.DrawBoxPlot()
            self.DrawBlandAltmanPlot()
        elif self.type_of_data_loaded == "table":
            self.DrawTable()
            self.DrawScatterFromTable()
            self.DrawHistogramsFromTable()
            self.DrawBoxPlotFromTable()
            self.DrawBlandAltmanPlotFromTable()
    
    def saveResultsTable(self, save_path=None):
        """Saves the results table as a text file.
        This function is called automatically when the table model is evaluated.
        Call this function with the save_path when QIBA Evaluate Tool is used in 
        command-line mode.
        save_path should include the folders and file name."""
        def addToTable(table, data_label_list, data_to_add_list):
            for j in range(len(data_to_add_list)):
                data_label = data_label_list[j]
                data_to_add = data_to_add_list[j]
                for k in range(len(data_to_add)):
                    if k == len(data_to_add)-1:
                        table += str(data_to_add[k]) + "\n"
                    elif k > 0:
                        table += str(data_to_add[k]) + "\t"
                    else:
                        table += data_label + " = \t" + str(data_to_add[k]) + "\t"
            return table

        #default_directory = os.path.expanduser("~") # User's home folder
        default_directory = os.path.dirname(self.path_qiba_table_T1)
        
        # Remove ktrans and file extension from source ktrans table file name.
        # Build the default results table file name from this.
        t1_table_file = os.path.basename(self.path_qiba_table_T1)
        #t1_table_file = t1_table_file.lower()
        #t1_table_file = self.removeSubstring(t1_table_file, "_t1")
        #t1_table_file = self.removeSubstring(t1_table_file, "t1")
        #t1_table_file = self.removeSubstring(t1_table_file, "_t")
        t1_table_file = t1_table_file[0:t1_table_file.rfind(".")]
        
        if save_path is None:
            save_file_dialog = wx.FileDialog(self, "Save Results Table", default_directory, t1_table_file+"_Results_Table.txt", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        
            if save_file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            
            save_path = save_file_dialog.GetPath()
        
        results_table = ""
        label_list = ["Mean", "Median", "Std. Dev.", "1st Quartile", "3rd Quartile", "Min.", "Max.", "RMSD", "CCC", "TDI", "Sigma metric"]

        if self.type_of_data_loaded == "image":
            headers_list = self.newModel.headersHorizontal
            for h in range(len(headers_list)):
                headers_list[h] = headers_list[h].replace("R1 = ", "")
                headers_list[h] = str(1/float(headers_list[h])) #Convert R1 to T1
        elif self.type_of_data_loaded == "table":
            headers_list = self.newModel.headers_T1
        else:
            headers_list = []

        for i in range(len(headers_list)):
            if i == len(headers_list)-1:
                results_table += str(headers_list[i]) + "\n"
            elif i > 0:
                results_table += str(headers_list[i]) + "\t"
            else:
                results_table += "Ref T1 = \t" + str(headers_list[i]) + "\t"
        #for i in range(len(self.newModel.headers_T1)):
        #    if i == len(self.newModel.headers_T1)-1:
        #        results_table += str(self.newModel.headers_T1[i]) + "\n"
        #    elif i > 0:
        #        results_table += str(self.newModel.headers_T1[i]) + "\t"
        #    else:
        #        results_table += "Ref T1 = \t"+ str(self.newModel.headers_T1[i]) + "\t"

        T1_data_list = [self.newModel.T1_cal_patch_mean, self.newModel.T1_cal_patch_median, self.newModel.T1_cal_patch_deviation, 
        self.newModel.T1_cal_patch_1stQuartile, self.newModel.T1_cal_patch_3rdQuartile, self.newModel.T1_cal_patch_min,
        self.newModel.T1_cal_patch_max, self.newModel.T1_rmsd, self.newModel.T1_ccc, self.newModel.T1_tdi, self.newModel.T1_sigma_metric]

        if self.type_of_data_loaded == "table":
            results_table = addToTable(results_table, label_list, T1_data_list)

        results_table += "All Regions Combined\nRMSD = \t"+str(self.newModel.T1_rmsd_all_regions)+"\n"
        results_table += "Mean = \t"+str(self.newModel.T1_cal_aggregate_mean)+"\n"
        results_table += "CCC = \t"+str(self.newModel.T1_ccc_all_regions)+"\n"
        results_table += "TDI (Nonparametric) = \t"+str(self.newModel.T1_tdi_all_regions)+"\n"
        results_table += "TDI (Parametric) = \t"+str(self.newModel.T1_tdi_all_regions_method_2)+"\n"
        results_table += "Sigma metric = \t"+str(self.newModel.T1_sigma_metric_all_regions)+"\n"
        results_table += "Mean bias = \t"+str(self.t1_mean_percent_bias)+"\n"
        results_table += "Variability (wSD) = \t"+str(self.newModel.T1_cal_aggregate_deviation)+"\n"
        results_table += "Bland-Altman Lower Limit = \t"+str(self.t1_lower_sd_line_value)+"\n"
        results_table += "Bland-Altman Upper Limit = \t"+str(self.t1_upper_sd_line_value)+"\n"
        results_table += "Bland-Altman Repeatability Coefficient = \t"+str(self.t1_repeatability_coefficient)+"\n"
        
        # If user entered .csv as the file extension, replace tabs in the
        # results_table with commas
        save_file_name = os.path.basename(save_path)
        if save_file_name.endswith(".csv") or save_file_name.endswith(".CSV") or save_file_name.endswith(".Csv"):
            results_table = results_table.replace("\t", ",")
        
        with open(save_path, "w") as output_file:
            try:
                output_file.write(results_table)
                self.SetStatusText(save_path + " saved successfully")
                return os.path.dirname(save_path)
            except IOError:
                self.SetStatusText("Error saving results table")
                wx.MessageBox("There was an error saving the results table", "Error Saving Results Table", wx.OK | wx.ICON_ERROR)
    
    def removeSubstring(self, string, substring):
        index = 0
        length = len(substring)
        while string.find(substring) != -1:
            index = string.find(substring)
            string = string[0:index] + string[index+length:]
        return string
            
    def LoadRef(self):
        '''
        load the reference data, and get the image size
        '''
        self.ref_T1, nrOfRow, nrOfColumn, fileType = QIBA_functions.ImportRawFile(self.path_ref_T1, self.patchLen)
        self.nrOfRow = nrOfRow - 1
        self.nrOfColumn = nrOfColumn

        # If GUI mode is used, the reference data will always be T1.
        # If batch mode is used, the reference data can be either T1 or R1.  If it's provided as R1, then convert it to T1.
        ref_filename = os.path.basename(self.path_ref_T1)
        if "R1" in ref_filename:
            self.ref_T1 = self.convertRefR1ToT1(self.ref_T1, self.nrOfRow, self.nrOfColumn)

    def convertRefR1ToT1(self, R1_values, nrOfRows, nrOfColumns):
        """Converts the reference R1 map to T1.

        The toolkit expects the calculated maps to be T1 maps and not R1 maps.
        Called when a reference R1 map is loaded from batch mode.

        Arguments:
        R1_values -- The original R1 map data
        nrOfRows, nrOfColumns -- The dimensions of the 10x10 patch grid

        Returns:
        The T1 map
        """

        T1_values = R1_values
        # print("nrOfRows="+str(nrOfRows)+", nrOfColumns="+str(nrOfColumns)+", k_dimension="+str(k_dimension)) #for testing
        # print("Original R1 map:") #for testing
        # print(R1_cal[0][0]) #for testing

        for i in range(nrOfRows):
            for j in range(nrOfColumns):
                R1 = R1_values[i][j]
                try:
                    T1 = 1 / R1
                    T1_values[i][j] = T1
                except ValueError:
                    pass
        # print("T1 map:") #for testing
        # print(T1_cal) #for testing
        return T1_values

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
        self.buttonEvaluate.Disable()
        
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
        editMenu.AppendSeparator()
        set_allowable_total_error = editMenu.Append(wx.ID_ANY, "Set Allowable Total Error...")
        editMenu.AppendSeparator()
        onVerboseMode = editMenu.AppendCheckItem(wx.ID_ANY, "Include Stat. Descriptions in Reports")
        
        # self.menubar.Bind(wx.EVT_MENU, self.OnEditImageDimension, OnEditImageDimension)
        self.Bind(wx.EVT_MENU, self.OnLoadRef_T1, OnLoadRef_T1)
        self.Bind(wx.EVT_MENU, self.setAllowableTotalErrorMenu, set_allowable_total_error)
        self.Bind(wx.EVT_MENU, self.setVerboseMode, onVerboseMode)

        self.menubar.Insert(1,editMenu, "&Edit")
        self.SetMenuBar(self.menubar)

    def SetupRightClickMenu(self):
        # setup the popup menu on right click
        wx.EVT_RIGHT_DOWN(self.fileBrowser.GetTreeCtrl(), self.OnRightClick)
        self.popupMenu = wx.Menu()
        self.ID_POPUP_LOAD_CAL_T1 = wx.NewId()
        self.ID_POPUP_LOAD_CAL_R1 = wx.NewId()
        self.ID_POPUP_LOAD_MASK_T1R1 = wx.NewId()

        OnLoadCal_T1 = wx.MenuItem(self.popupMenu, self.ID_POPUP_LOAD_CAL_T1, 'Load as calculated T1')
        OnLoadCal_R1 = wx.MenuItem(self.popupMenu, self.ID_POPUP_LOAD_CAL_R1, 'Load as calculated R1')
        OnLoadMask_T1R1 = wx.MenuItem(self.popupMenu, self.ID_POPUP_LOAD_MASK_T1R1, 'Load as Mask')
        self.popupMenu.AppendItem(OnLoadCal_T1)
        self.popupMenu.AppendItem(OnLoadCal_R1)
        self.popupMenu.AppendItem(OnLoadMask_T1R1)

    def SetupRightClickMenuForTextFiles(self):
        # setup the popup menu for right clicking on text files (.csv, .cdata, .txt)
        # Separate options to load T1 and R1 are not needed since the table file will contain
        # both nominal and calculated data.  There is no need to convert calculated R1 data to T1.
        wx.EVT_RIGHT_DOWN(self.fileBrowser.GetTreeCtrl(), self.OnRightClick)
        self.popupMenuTextFiles = wx.Menu()
        self.ID_POPUP_LOAD_TEXT_FILE_T1 = wx.NewId()
        self.ID_POPUP_LOAD_MASK_T1R1_TEXT = wx.NewId()
        
        OnLoadTextFile_T1 = wx.MenuItem(self.popupMenuTextFiles, self.ID_POPUP_LOAD_TEXT_FILE_T1, "Load as T1/R1 parameter text file")
        OnLoadMask_T1R1 = wx.MenuItem(self.popupMenuTextFiles, self.ID_POPUP_LOAD_MASK_T1R1, "Load as Mask")
        self.popupMenuTextFiles.AppendItem(OnLoadTextFile_T1)
        self.popupMenuTextFiles.AppendItem(OnLoadMask_T1R1)
        wx.EVT_MENU(self.popupMenuTextFiles, self.ID_POPUP_LOAD_TEXT_FILE_T1, self.OnLoadTextFile_T1)
        wx.EVT_MENU(self.popupMenuTextFiles, self.ID_POPUP_LOAD_MASK_T1R1_TEXT, self.OnLoadMask_T1R1)
        
    def SetupPage_Histogram(self):
        # setup the histogram page

        self.figureHist_T1 = Figure()
        w, h = self.figureHist_T1.get_size_inches()
        self.figureHist_T1.set_size_inches([w*3, h])
        self.canvasHist_T1 = FigureCanvas(self.pageHistogram, -1, self.figureHist_T1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasHist_T1, 1, wx.EXPAND)
        self.pageHistogram.SetSizer(sizer)
        self.pageHistogram.SetAutoLayout(1)
        self.pageHistogram.SetupScrolling()

    def SetupPage_BlandAltmanPlot(self):
        # setup the Bland-Altman plot page
        self.figureLOA_T1 = Figure()
        w,h = self.figureLOA_T1.get_size_inches()
        self.figureLOA_T1.set_size_inches([w*3, h])
        self.canvasLOA_T1 = FigureCanvas(self.pageLOA, -1, self.figureLOA_T1)

        self.figureLOA_description = Figure()
        #self.figureLOA_description.set_size_inches([w*3, h*0.05])
        self.canvasLOA_description = FigureCanvas(self.pageLOA, -1, self.figureLOA_description)

        if self.verbose_mode:
            proportions = [90,10]
        else:
            proportions = [99,1]

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasLOA_T1, proportions[0], wx.EXPAND)
        sizer.Add(self.canvasLOA_description, proportions[1], wx.EXPAND)
        self.pageLOA.SetSizer(sizer)
        self.pageLOA.SetAutoLayout(1)
        #self.pageLOA.SetupScrolling()
        
    def ClearPage_Histogram(self):
        # clear the histogram page
        self.figureHist_T1.clear()
        self.canvasHist_T1.draw()

    def ClearPage_BlandAltmanPlot(self):
        # clear the Bland-Altman plot page
        self.figureLOA_T1.clear()
        self.canvasLOA_T1.draw()
        self.figureLOA_description.clear()
        self.canvasLOA_description.draw()
        
    def GenerateModel(self):
        # generate the model for evaluation
        self.newModel = QIBA_model.Model_T1(self.path_ref_T1, self.path_cal_T1, [self.nrOfRow, self.nrOfColumn], self.T1_R1_flag, self.allowable_total_error, self.mask, self.verbose_mode)

    def GenerateTableModel(self):
        """Generates the QIBA model if table-based data is supplied."""
        self.newModel = QIBA_table_model_T1(self.data_table_T1_contents, self.allowable_total_error, self.verbose_mode)
        
    def OnRightClick(self, event):
        # the right click action on the file list
        if (str(os.path.splitext(self.fileBrowser.GetPath())[1]) in self.supportedFileTypeList):
            wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_CAL_T1, self.OnLoadCal_T1)
            wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_CAL_R1, self.OnLoadCal_R1)
            wx.EVT_MENU(self.popupMenu, self.ID_POPUP_LOAD_MASK_T1R1, self.OnLoadMask_T1R1)
            self.PopupMenu(self.popupMenu, event.GetPosition())
        elif (str(os.path.splitext(self.fileBrowser.GetPath())[1]) in self.supportedTextFileTypeList):
            self.PopupMenu(self.popupMenuTextFiles, event.GetPosition())
        else:
            self.SetStatusText('Invalid file or path chosen.')

    def OnLoadCal_T1(self, event):
        # pass the file path for loading
        self.path_cal_T1 = self.fileBrowser.GetPath()
        self.SetStatusText('Calculated T1 loaded.')
        self.changeTabTitle("Table Viewer", "Image Viewer")
        self.buttonEvaluate.Enable()
        self.T1_R1_flag = "T1"
        self.path_qiba_table_T1 = None

    def OnLoadCal_R1(self, event):
        # pass the file path for loading
        self.path_cal_T1 = self.fileBrowser.GetPath()
        self.SetStatusText('Calculated R1 loaded.')
        self.changeTabTitle("Table Viewer", "Image Viewer")
        self.buttonEvaluate.Enable()
        self.T1_R1_flag = "R1"
        self.path_qiba_table_T1 = None

    def OnLoadMask_T1R1(self, event):
        # pass the mask file path for loading
        path = self.fileBrowser.GetPath()
        self.mask = self.loadMaskFile(path)
        self.SetStatusText('Mask Loaded.')
        
    def OnLoadRef_T1(self, event):
        # pass the file path for loading
        dlg = wx.FileDialog(self, 'Load reference T1...', '', '', "Supported files (*.dcm *.bin *.raw *.tif)|*.dcm;*.bin;*.raw;*.tif", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.path_ref_T1 = dlg.GetPath()
            imageData, nrOfRow, nrOfColumn, fileType = QIBA_functions.ImportRawFile(self.path_ref_T1, self.patchLen)
            if fileType == 'BINARY':
                self.OnImportBinaryDialog_T1()
            #elif imageData == False:
            elif fileType == "":
                self.SetStatusText('Please import a valid image!')
            else:
                self.ref_T1 = imageData
                self.nrOfRow = nrOfRow - 1
                self.nrOfColumn = nrOfColumn
            self.ShowRef()
            self.SetStatusText('Reference T1 loaded.')
        else:
            self.SetStatusText('Reference T1 was NOT loaded!')

    def OnLoadTextFile_T1(self, event):
        self.data_table_T1 = QIBA_table(self.fileBrowser.GetPath())
        self.data_table_T1_contents = self.data_table_T1.table_contents
        self.path_qiba_table_T1 = self.fileBrowser.GetPath()
        
        #Determine from the filename if the table contains T1 or R1 data
        table_filename = os.path.basename(self.path_qiba_table_T1)
        if "T1" in table_filename:
            self.T1_R1_flag = "T1"
        elif "R1" in table_filename:
            self.T1_R1_flag = "R1"
        #result_image_type = self.data_table.getResultImageType() #Ktrans, Ve, or T1
        valid_table, error_message = self.data_table_T1.validateTable()
        if not valid_table:
            self.SetStatusText("Error reading T1/R1 table")
            wx.MessageBox(error_message, "Error Reading T1/R1 Table", wx.OK | wx.ICON_ERROR)
            return
        self.SetStatusText("T1/R1 table file loaded successfully.")
        self.changeTabTitle("Image Viewer", "Table Viewer")
        self.buttonEvaluate.Enable()
        self.path_cal_T1 = None
    
    def loadTextFileCmdLine_T1(self, text_file_path):
        """Loads the T1 table file specified by text_file_path.
        Use this function when the program is run from the command line
        """
        self.data_table_T1 = QIBA_table(text_file_path)
        self.data_table_T1_contents = self.data_table_T1.table_contents
        self.path_qiba_table_T1 = text_file_path
        
        # Determine from the filename if the table contains T1 or R1 data
        table_filename = os.path.basename(self.path_qiba_table_T1)
        if "T1" in table_filename:
            self.T1_R1_flag = "T1"
        elif "R1" in table_filename:
            self.T1_R1_flag = "R1"
        valid_table, error_message = self.data_table_T1.validateTable()
        if not valid_table:
            print("Error reading T1/R1 table at\n"+text_file_path)
            print(error_message)
            return False
        print(text_file_path+" loaded successfully.")
        self.path_cal_T1 = None
        return True
    
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
        nrOfBins = 10

        self.figureHist_T1.suptitle('The histogram of the calculated T1',) # fontsize = 18)

        for i in range(self.newModel.nrOfRows):
            for j in range(self.newModel.nrOfColumns):
                subPlot_T1 = self.figureHist_T1.add_subplot(self.newModel.nrOfRows, self.newModel.nrOfColumns, i * self.newModel.nrOfColumns + j + 1)
                # subPlot_K.clear()

                #processedData_T1 = [n for n in self.newModel.T1_cal[i][j] if n is not numpy.nan] #Remove NaNs. Matplotlib's histogram seems to fail if there are NaNs
                processedData_T1 = QIBA_functions.DealNaN(self.newModel.T1_cal[i][j])[0] # Original
                subPlot_T1.hist(processedData_T1, nrOfBins) # normed=True if want the bars to be normalized
                minPatch_T1 = numpy.min(processedData_T1)
                maxPatch_T1 = numpy.max(processedData_T1)
                meanPatch_T1 = numpy.mean(processedData_T1)
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
        self.pageHistogram.Layout()
        self.pageHistogram.SetupScrolling()


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
        OnHist_zoom = wx.MenuItem(self.popmenu_hist, self.ID_POPUP_HIST_ZOOM, 'Zoom')
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
        
    def DrawHistogramsFromTable(self):
        """Draw histograms of imported calculated T1 table data, so that the user can have a look of the distribution of each patch."""
        ref_cal_T1_groups = self.newModel.ref_cal_T1_groups
        
        nrOfBins = 10

        if self.T1_R1_flag == "R1":
            self.figureHist_T1.suptitle('The histogram of the calculated R1') #, fontsize = 18)
        else:
            self.figureHist_T1.suptitle('The histogram of the calculated T1') #, fontsize = 18)
        
        w, h = self.figureHist_T1.get_size_inches()
        self.figureHist_T1.set_size_inches([w*0.75,h*3])
        self.canvasHist_T1 = FigureCanvas(self.pageHistogram, -1, self.figureHist_T1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvasHist_T1, 1, wx.EXPAND)
        self.pageHistogram.SetSizer(sizer)
        self.pageHistogram.SetAutoLayout(1)
        self.pageHistogram.SetupScrolling()
        
        #1. T1 histogram: Extract data from T1 group list
        for i in range(len(ref_cal_T1_groups)):
            unique_T1_ref_group = ref_cal_T1_groups[i]
            ref_T1_data_list = list() #The list of reference values (raw data), extracted from ref_cal_group_list
            cal_T1_data_list = list() #The list of calculated values (raw data), extracted from ref_cal_group_list
            t1_instances_counted_list = list()
            for t in range(len(unique_T1_ref_group)):
                tpl = unique_T1_ref_group[t]
                ref_T1_data_list.append(tpl[0])
                cal_T1_data_list.append(tpl[1])
                t1_instances_counted_list.append(tpl[3])
            
            #Draw one histogram for each reference T1
            subPlot_T1 = self.figureHist_T1.add_subplot(len(ref_cal_T1_groups), 1, i)
            if sum(t1_instances_counted_list) == 0:
                subPlot_T1.plot([])
                subPlot_T1.xaxis.set_ticks([])
                subPlot_T1.yaxis.set_ticks([])
            else:
                #Calculate weighted average of cal_T1_data
                weighted_cal_T1_data_list = list()
                for m in range(len(cal_T1_data_list)):
                    cal_T1 = cal_T1_data_list[m]
                    weight = t1_instances_counted_list[m]
                    for n in range(weight):
                        weighted_cal_T1_data_list.append(cal_T1)

                weighted_meanPatch_T1 = numpy.mean(weighted_cal_T1_data_list)

                #Create the histogram
                subPlot_T1.hist(weighted_cal_T1_data_list, nrOfBins)
                weighted_minPatch_T1 = numpy.min(weighted_cal_T1_data_list)
                weighted_maxPatch_T1 = numpy.max(weighted_cal_T1_data_list)
                #meanPatch_T1 = numpy.mean(weighted_cal_T1_data_list)
                weighted_minPatch_T1 = QIBA_functions_for_table.formatFloatTo2DigitsString(weighted_minPatch_T1)
                weighted_maxPatch_T1 = QIBA_functions_for_table.formatFloatTo2DigitsString(weighted_maxPatch_T1)
                weighted_meanPatch_T1 = QIBA_functions_for_table.formatFloatTo4DigitsString(weighted_meanPatch_T1)
                
                subPlot_T1.set_xticks([float(weighted_minPatch_T1), float(weighted_maxPatch_T1)])
                subPlot_T1.set_xticklabels([weighted_minPatch_T1, weighted_maxPatch_T1], size="small")
                subPlot_T1.axvline(float(weighted_meanPatch_T1), color="r", linestyle="dashed", linewidth=1) #Draw a vertical line at the mean value
                subPlot_T1.set_ylim([0,sum(t1_instances_counted_list)])
                subPlot_T1.text(float(weighted_meanPatch_T1) + 0.01 * float(weighted_meanPatch_T1), 0.9 * sum(t1_instances_counted_list), weighted_meanPatch_T1, size = 'x-small') # parameters: location_x, location_y, text, size
                 
        #3. Setup toolbars, menus, etc.
        #toolbars
        self.toolbar_hist_T1 = NavigationToolbar(self.canvasHist_T1)
        self.toolbar_hist_T1.Hide()
        
        #right-click popup menu
        self.figureHist_T1.canvas.mpl_connect("axes_enter_event", self.enter_axes)
        self.figureHist_T1.canvas.mpl_connect("axes_leave_event", self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasHist_T1, self.rightDown_hist)
        
        self.popmenu_hist_T1 = wx.Menu()
        self.ID_POPUP_HITS_PAN_T1 = wx.NewId()
        self.ID_POPUP_HITS_ZOOM_T1 = wx.NewId()
        self.ID_POPUP_HITS_SAVE_T1 = wx.NewId()
        
        OnHist_pan_T1 = wx.MenuItem(self.popmenu_hist_T1, self.ID_POPUP_HITS_PAN_T1, "Pan")
        OnHist_zoom_T1 = wx.MenuItem(self.popmenu_hist_T1, self.ID_POPUP_HITS_ZOOM_T1, "Zoom")
        OnHist_save_T1 = wx.MenuItem(self.popmenu_hist_T1, self.ID_POPUP_HITS_SAVE_T1, "Save")
        self.popmenu_hist_T1.AppendItem(OnHist_pan_T1)
        self.popmenu_hist_T1.AppendItem(OnHist_zoom_T1)
        self.popmenu_hist_T1.AppendItem(OnHist_save_T1)
        wx.EVT_MENU(self.popmenu_hist_T1, self.ID_POPUP_HITS_PAN_T1, self.toolbar_hist_T1.pan)
        wx.EVT_MENU(self.popmenu_hist_T1, self.ID_POPUP_HITS_ZOOM_T1, self.toolbar_hist_T1.zoom)
        wx.EVT_MENU(self.popmenu_hist_T1, self.ID_POPUP_HITS_SAVE_T1, self.toolbar_hist_T1.save_figure)
        
        #double-click
        wx.EVT_LEFT_DCLICK(self.canvasHist_T1, self.toolbar_hist_T1.home)
        
        #4. Draw the histograms
        #self.pageHistogram.Layout()
        
        self.figureHist_T1.tight_layout()
        self.figureHist_T1.subplots_adjust(top=0.94, right=0.95)
        self.canvasHist_T1.draw()

    def DrawBlandAltmanPlot(self): #T1
        #pyplt refers to matplotlib.pyplot
        t1_refData_nbp = numpy.asarray(self.newModel.T1_ref_no_bad_pixels)
        t1_calData_nbp = numpy.asarray(self.newModel.T1_cal_no_bad_pixels)
        t1_mask_nbp = self.newModel.T1_mask_no_bad_pixels

        t1_ref_total_pixels_counted = 0
        t1_cal_total_pixels_counted = 0
        i_dimension = len(t1_calData_nbp)
        j_dimension = len(t1_calData_nbp[0])
        
        t1_means_list = []
        t1_diffs_list = []
        t1_percent_bias_list = []

        #t_statistic = QIBA_functions.T_Test_Aggregate_Data(t1_calData_nbp, t1_refData_nbp, i_dimension, j_dimension, t1_mask_nbp)

        #print("i_dimension="+str(i_dimension)+", j_dimension="+str(j_dimension)) #for testing
        for i in range(i_dimension):
            for j in range(j_dimension):
                t1_refData_nbp_10x10 = t1_refData_nbp[i][j] #The 10x10 pixel patch of raw pixel data (no bad pixels)
                t1_calData_nbp_10x10 = t1_calData_nbp[i][j] #The 10x10 pixel patch or raw pixel data
                mask_nbp_10x10 = t1_mask_nbp[i][j]

                t1_refData_nbp_10x10 = QIBA_functions.applyMask(t1_refData_nbp_10x10, mask_nbp_10x10)
                t1_calData_nbp_10x10 = QIBA_functions.applyMask(t1_calData_nbp_10x10, mask_nbp_10x10)

                t1_ref_pixels_counted_10x10 = len(t1_refData_nbp_10x10)
                t1_cal_pixels_counted_10x10 = len(t1_calData_nbp_10x10)
                t1_ref_total_pixels_counted += t1_ref_pixels_counted_10x10
                t1_cal_total_pixels_counted += t1_cal_pixels_counted_10x10
                
                if t1_cal_pixels_counted_10x10 > 0:
                    ref_mean = numpy.mean(t1_refData_nbp_10x10)
                    cal_mean = numpy.mean(t1_calData_nbp_10x10)
                    mean = numpy.mean([ref_mean, cal_mean])
                    difference = cal_mean - ref_mean
                    bias = ((cal_mean - ref_mean) / ref_mean) * 100.0
                    #print("i="+str(i)+", j="+str(j)+": mean="+str(mean)+", difference="+str(difference)) #for testing
                    t1_means_list.append(mean)
                    t1_diffs_list.append(difference)
                    t1_percent_bias_list.append(bias)
        self.t1_mean_difference = numpy.mean(t1_diffs_list) #The mean of the differences
        self.t1_sd_difference = numpy.std(t1_diffs_list) #The standard deviation of the differences
        self.t1_mean_percent_bias = numpy.mean(t1_percent_bias_list)

        # Setup the toolbars
        self.toolbar_LOA_T1 = NavigationToolbar(self.canvasLOA_T1)
        self.toolbar_LOA_T1.Hide()
        
        # Setup right-clicking
        self.figureLOA_T1.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureLOA_T1.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasLOA_T1, self.rightDown_LOA)
        
        # Setup the pop-up menus that appear when user right-clicks
        self.popmenu_LOA_T1 = wx.Menu()
        self.ID_POPUP_LOA_PAN_T1 = wx.NewId()
        self.ID_POPUP_LOA_ZOOM_T1 = wx.NewId()
        self.ID_POPUP_LOA_SAVE_T1 = wx.NewId()
        OnLOA_pan_T1 = wx.MenuItem(self.popmenu_LOA_T1, self.ID_POPUP_LOA_PAN_T1, "Pan")
        OnLOA_zoom_T1 = wx.MenuItem(self.popmenu_LOA_T1, self.ID_POPUP_LOA_ZOOM_T1, "Zoom")
        OnLOA_save_T1 = wx.MenuItem(self.popmenu_LOA_T1, self.ID_POPUP_LOA_SAVE_T1, "Save")
        self.popmenu_LOA_T1.AppendItem(OnLOA_pan_T1)
        self.popmenu_LOA_T1.AppendItem(OnLOA_zoom_T1)
        self.popmenu_LOA_T1.AppendItem(OnLOA_save_T1)
        wx.EVT_MENU(self.popmenu_LOA_T1, self.ID_POPUP_LOA_PAN_T1, self.toolbar_LOA_T1.pan)
        wx.EVT_MENU(self.popmenu_LOA_T1, self.ID_POPUP_LOA_ZOOM_T1, self.toolbar_LOA_T1.zoom)
        wx.EVT_MENU(self.popmenu_LOA_T1, self.ID_POPUP_LOA_SAVE_T1, self.toolbar_LOA_T1.save_figure)
        
        # Draw the Bland-Altman plot for T1
        font = {'fontname':'Arial', 'fontsize':12, 'weight':'bold'}
        t1_subplot = self.figureLOA_T1.add_subplot(111)
        t1_subplot.scatter(t1_means_list, t1_diffs_list, s=50, marker=".") #s= size, c= color
        t1_mean_line = t1_subplot.axhline(self.t1_mean_difference, color="red", linestyle="--")
        #self.t1_upper_sd_line_value = t1_mean_difference + (1.96*t1_sd_difference)
        #self.t1_lower_sd_line_value = t1_mean_difference - (1.96*t1_sd_difference)
        #self.t1_repeatability_coefficient = 1.96 * t1_sd_difference
        t_statistic = scipy.stats.t.ppf(0.95, len(t1_diffs_list) - 1)
        self.t1_upper_sd_line_value = self.t1_mean_difference + (t_statistic*self.t1_sd_difference)
        self.t1_lower_sd_line_value = self.t1_mean_difference - (t_statistic*self.t1_sd_difference)
        self.t1_repeatability_coefficient = t_statistic * self.t1_sd_difference
        t1_upper_sd_line = t1_subplot.axhline(self.t1_upper_sd_line_value, color="gray", linestyle="--")
        t1_lower_sd_line = t1_subplot.axhline(self.t1_lower_sd_line_value, color="gray", linestyle="--")
        t1_subplot.set_xlabel("Mean of Reference and Calculated T1", fontdict=font)
        t1_subplot.set_ylabel("Difference of Reference and Calculated T1", fontdict=font)
        t1_subplot.legend( (t1_mean_line, t1_upper_sd_line), ("Mean Difference ("+str(self.t1_mean_difference)+")", \
        "95% Confidence Interval ("+str(self.t1_lower_sd_line_value)+", "+str(self.t1_upper_sd_line_value)+")"), loc="lower center", ncol=2, prop={'size':10})
        self.figureLOA_T1.tight_layout()
        #self.figureLOA_T1.subplots_adjust(top=0.94, right=0.95)
        #####self.canvasLOA_T1.draw()

        if self.verbose_mode:
            #description_subplot = self.figureLOA_description.add_subplot(111)
            self.figureLOA_description.text(0.2, 0.5, StatDescriptions.loa_text) #original: 0.2, 0.5
            #self.figureLOA_description.tight_layout()
            self.canvasLOA_description.draw()
        #print(t1_means_list)
    
    def DrawBlandAltmanPlotFromTable(self):
        ref_cal_T1_groups = self.newModel.ref_cal_T1_groups
        
        #Get calculated T1 values
        unique_ref_T1_values_list = [] #A list of each reference T1 value (i.e. [0.01, 0.02, 0.05, 0.1, 0.2, 0.35])
        all_ref_T1_values_list = []
        all_cal_T1_values_list = []

        #t_statistic = QIBA_functions_for_table.T_Test_Aggregate_Data(ref_cal_T1_groups)

        for i in range(len(ref_cal_T1_groups)):
            unique_T1_ref_group = ref_cal_T1_groups[i]
            #temp_temp = list()
            #ref_T1_per_group_list = list() #The list of reference values (raw data), extracted from ref_cal_T1_groups
            #cal_T1_per_group_list = list() #The list of calculated values (raw data), extracted from ref_cal_T1_groups
            t1_instances_counted_list = list()
            
            for t in range(len(unique_T1_ref_group)):
                tpl = unique_T1_ref_group[t]
                #ref_Ktrans_per_group_list.append(tpl[0])
                #cal_Ktrans_per_group_list.append(tpl[1])
                t1_instances_counted_list.append(tpl[3])
                if t == 0:
                    unique_ref_T1_values_list.append(tpl[0])
                all_ref_T1_values_list.append(tpl[0])
                all_cal_T1_values_list.append(tpl[1])
            #all_ref_T1_values_list.append(ref_T1_per_group_list)
            #all_cal_T1_values_list.append(cal_T1_per_group_list)
        
        #Calculate T1 mean and Ktrans diff
        t1_means_list = []
        t1_diffs_list = []
        t1_percent_bias_list = []
        
        for i in range(len(all_cal_T1_values_list)):
            #t1_means_list.append(numpy.mean(all_cal_T1_values_list[i]))
            mean_of_t1_ref_and_cal = numpy.mean([all_cal_T1_values_list[i], all_ref_T1_values_list[i]])
            t1_means_list.append(mean_of_t1_ref_and_cal)
            t1_diffs_list.append(all_cal_T1_values_list[i] - all_ref_T1_values_list[i])
            bias = ((all_cal_T1_values_list[i]-all_ref_T1_values_list[i])/all_ref_T1_values_list[i]) * 100.0
            t1_percent_bias_list.append(bias)
        
        self.t1_mean_difference = numpy.mean(t1_diffs_list) #The mean of the differences
        self.t1_sd_difference = numpy.std(t1_diffs_list) #The standard deviation of the differences
        self.t1_mean_percent_bias = numpy.mean(t1_percent_bias_list)
        
        # Setup the toolbars
        self.toolbar_LOA_T1 = NavigationToolbar(self.canvasLOA_T1)
        self.toolbar_LOA_T1.Hide()
        
        # Setup right-clicking
        self.figureLOA_T1.canvas.mpl_connect('axes_enter_event', self.enter_axes)
        self.figureLOA_T1.canvas.mpl_connect('axes_leave_event', self.leave_axes)
        wx.EVT_RIGHT_DOWN(self.canvasLOA_T1, self.rightDown_LOA)
        
        # Setup the pop-up menus that appear when user right-clicks
        self.popmenu_LOA_T1 = wx.Menu()
        self.ID_POPUP_LOA_PAN_T1 = wx.NewId()
        self.ID_POPUP_LOA_ZOOM_T1 = wx.NewId()
        self.ID_POPUP_LOA_SAVE_T1 = wx.NewId()
        OnLOA_pan_T1 = wx.MenuItem(self.popmenu_LOA_T1, self.ID_POPUP_LOA_PAN_T1, "Pan")
        OnLOA_zoom_T1 = wx.MenuItem(self.popmenu_LOA_T1, self.ID_POPUP_LOA_ZOOM_T1, "Zoom")
        OnLOA_save_T1 = wx.MenuItem(self.popmenu_LOA_T1, self.ID_POPUP_LOA_SAVE_T1, "Save")
        self.popmenu_LOA_T1.AppendItem(OnLOA_pan_T1)
        self.popmenu_LOA_T1.AppendItem(OnLOA_zoom_T1)
        self.popmenu_LOA_T1.AppendItem(OnLOA_save_T1)
        wx.EVT_MENU(self.popmenu_LOA_T1, self.ID_POPUP_LOA_PAN_T1, self.toolbar_LOA_T1.pan)
        wx.EVT_MENU(self.popmenu_LOA_T1, self.ID_POPUP_LOA_ZOOM_T1, self.toolbar_LOA_T1.zoom)
        wx.EVT_MENU(self.popmenu_LOA_T1, self.ID_POPUP_LOA_SAVE_T1, self.toolbar_LOA_T1.save_figure)
        
        # Draw the Bland-Altman plot for T1
        font = {'fontname':'Arial', 'fontsize':12, 'weight':'bold'}
        t1_subplot = self.figureLOA_T1.add_subplot(111)
        t1_subplot.scatter(t1_means_list, t1_diffs_list, s=50, marker=".") #s= size, c= color
        #  Should outliers be excluded when calculating mean_line and sd_lines?
        t1_mean_line = t1_subplot.axhline(self.t1_mean_difference, color="red", linestyle="--")

        t_statistic = scipy.stats.t.ppf(0.95, len(t1_diffs_list)-1)
        #t_statistic = self.newModel.T1_cal_patch_ttest_t
        #t_statistic = QIBA_functions.T_Test_Aggregate_Data(all_ref_T1_values_list, all_cal_T1_values_list)
        #self.t1_upper_sd_line_value = t1_mean_difference + (1.96*t1_sd_difference)
        #self.t1_lower_sd_line_value = t1_mean_difference - (1.96*t1_sd_difference)
        #self.t1_repeatability_coefficient = 1.96 * t1_sd_difference
        self.t1_upper_sd_line_value = self.t1_mean_difference + (t_statistic*self.t1_sd_difference) #Need to calculate an aggregate t_statistic. "t_statistic" currently is a list of 1 t_stat for each row.
        self.t1_lower_sd_line_value = self.t1_mean_difference - (t_statistic*self.t1_sd_difference)
        self.t1_repeatability_coefficient = t_statistic * self.t1_sd_difference

        t1_upper_sd_line = t1_subplot.axhline(self.t1_upper_sd_line_value, color="gray", linestyle="--")
        t1_lower_sd_line = t1_subplot.axhline(self.t1_lower_sd_line_value, color="gray", linestyle="--")
        
        if self.T1_R1_flag == "T1":
            t1_subplot.set_xlabel("Mean of Reference and Calculated T1", fontdict=font)
            t1_subplot.set_ylabel("Difference of Reference and Calculated T1", fontdict=font)
        elif self.T1_R1_flag == "R1":
            t1_subplot.set_xlabel("Mean of Reference and Calculated R1", fontdict=font)
            t1_subplot.set_ylabel("Difference of Reference and Calculated R1", fontdict=font)
        else:
            t1_subplot.set_xlabel("Mean of Reference and Calculated Values", fontdict=font)
            t1_subplot.set_ylabel("Difference of Reference and Calculated Values", fontdict=font)
            
        t1_subplot.legend( (t1_mean_line, t1_upper_sd_line), ("Mean Difference ("+str(self.t1_mean_difference)+")", \
        "95% Confidence Interval ("+str(self.t1_lower_sd_line_value)+", "+str(self.t1_upper_sd_line_value)+")"), loc="lower center", ncol=2, prop={'size':10})
        self.figureLOA_T1.tight_layout()
        #self.figureLOA_T1.subplots_adjust(top=0.94, right=0.95)
        self.canvasLOA_T1.draw()

    def rightDown_hist(self, event):
        '''
        right down on figure
        '''
        if self.IN_AXES:
            self.canvasHist_T1.PopupMenu(self.popmenu_hist, event.GetPosition())
        else:
            pass

    def rightDown_LOA(self, event):
        '''
        right-click on Ktrans LOA plot
        '''
        if self.IN_AXES:
            self.canvasLOA_T1.PopupMenu(self.popmenu_LOA_T1, event.GetPosition())
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
            temp_temp = []
            for element in zip(*self.newModel.R1_cal)[j]:
                temp_temp.append(QIBA_functions.DealNaN(element)[0])
            temp.extend(temp_temp)
            # referValue_R1.append(QIBA_functions.formatFloatTo2DigitsString(self.newModel.T1_ref[j][0][0]))
        subPlot_R1.boxplot(temp, notch = 1, sym = 'r+', whis=1.5)

        # decorate R1 plot
        subPlot_R1.set_title('Box plot of R1 from calculated T1')
        subPlot_R1.set_xlabel('The result shows the R1 patches from calculated T1, concatenated in columns')
        subPlot_R1.set_ylabel('Calculated values in patches')

        subPlot_R1.xaxis.set_major_formatter(ticker.NullFormatter())
        # subPlot_R1.xaxis.set_minor_locator(ticker.FixedLocator([8, 23, 38, 53, 68, 83]))
        subPlot_R1.xaxis.set_minor_locator(ticker.FixedLocator([4, 11, 18, 25, 32, 39, 46, 53, 60, 67, 74, 81, 88, 95, 102]))
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
        OnBox_zoom = wx.MenuItem(self.popmenu_box, self.ID_POPUP_BOX_ZOOM, 'Zoom')
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
        
    def DrawBoxPlotFromTable(self):
        """Draw box plots from each Ktrans or Ve group"""
        ### To do: Add weighting to box plots
        
        #Setup T1 plot
        ref_cal_T1_groups = self.newModel.ref_cal_T1_groups
        subPlotT1 = self.figureBoxPlot.add_subplot(2, 1, 1)
        subPlotT1.clear()
    
        #Get calculated T1 values
        unique_ref_T1_values_list = list() #A list of each reference T1 value (i.e. [0.01, 0.02, 0.05, 0.1, 0.2, 0.35])
        all_cal_T1_values_list = list()
        
        for i in range(len(ref_cal_T1_groups)):
            unique_T1_ref_group = ref_cal_T1_groups[i]
            #temp_temp = list()
            ref_T1_per_group_list = list() #The list of reference values (raw data), extracted from ref_cal_T1_groups
            cal_T1_per_group_list = list() #The list of calculated values (raw data), extracted from ref_cal_T1_groups
            t1_instances_counted_list = list()
            
            for t in range(len(unique_T1_ref_group)):
                tpl = unique_T1_ref_group[t]
                ref_T1_per_group_list.append(tpl[0])
                cal_T1_per_group_list.append(tpl[1])
                t1_instances_counted_list.append(tpl[3])
                if t == 0:
                    unique_ref_T1_values_list.append(tpl[0])
            all_cal_T1_values_list.append(cal_T1_per_group_list)
                
        #Draw T1 box plot
        subPlotT1.boxplot(all_cal_T1_values_list, notch = False, sym = 'r+', whis=1.5)
        
        # decorate T1 plot
        if self.T1_R1_flag == "T1":
            subPlotT1.set_title("Box plot of calculated T1")
        elif self.T1_R1_flag == "R1":
            subPlotT1.set_title("Box plot of calculated R1")
        else:
            subPlotT1.set_title("Box plot of calculated values")
        #subPlotT1.set_xlabel('In each column, each box plot denotes Ve = ' + str(referValueV) + ' respectively')
        subPlotT1.set_ylabel("Calculated values")

        subPlotT1.xaxis.set_major_formatter(ticker.NullFormatter())
        subPlotT1.set_xticklabels(unique_ref_T1_values_list)
        subPlotT1.xaxis.set_minor_formatter(ticker.IndexFormatter(unique_ref_T1_values_list))
        for i in range(len(ref_cal_T1_groups)):
            subPlotT1.axvline(x = i + 0.5, color = 'green', linestyle = 'dashed')

        #self.figureBoxPlot.tight_layout()
        #self.canvasBoxPlot.draw()
        #self.rightPanel.Layout()
        
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
        OnBox_zoom = wx.MenuItem(self.popmenu_box, self.ID_POPUP_BOX_ZOOM, 'Zoom')
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
            self.canvasBoxPlot.PopupMenu(self.popmenu_box, event.GetPosition())
        else:
            pass

    def DrawMaps(self):
        # draw the maps of the preview and error

        #Original
        #self.figureImagePreview = Figure()
        #self.canvasImagePreview = FigureCanvas(self.pageImagePreview, -1, self.figureImagePreview)
        #sizer = wx.BoxSizer(wx.HORIZONTAL)
        #sizer.Add(self.canvasImagePreview, 1, wx.EXPAND)
        #self.pageImagePreview.SetSizer(sizer, deleteOld=True)

        self.imagePreviewSizer.Show(self.canvasImagePreview, show=True)
        self.imagePreviewSizer.Show(self.tableViewer, show=False)
        self.tableViewer.SetPage("")
        self.pageImagePreview.Layout()  # Resizes the tab's contents and ensures that its contents are displayed correctly. Required since tab is changed after it is initally drawn.

        self.PlotPreview([[self.newModel.T1_cal_inRow], [self.newModel.T1_error], [self.newModel.T1_error_normalized],],

                                [['Calculated T1'], ['Error map of T1'], ['Normalized Error map of T1'],],

                                [['bone'], ['rainbow'], ['rainbow'], ],

                                [['T1[ms]'], ['Delta T1[ms]'], ['Normalized error[%]'],])

    def DrawTable(self):
        """Draws the table in the Table Viewer tab. Used when table data is loaded."""
        #Make HTML versions of the Ktrans and Ve table data
        T1_table_in_html = QIBA_functions_for_table.putRawDataTableInHtml(self.data_table_T1)
        
        #self.imagePreviewViewer = wx.html.HtmlWindow(self.pageImagePreview, -1, style=wx.html.HW_SCROLLBAR_AUTO | wx.ALWAYS_SHOW_SB)
        
        #sizer = wx.BoxSizer(wx.VERTICAL)
        #sizer.Add(self.imagePreviewViewer, 1, wx.EXPAND)
        #self.pageImagePreview.SetSizer(sizer, deleteOld=True)
        #self.pageImagePreview.SetAutoLayout(1)
        ##self.pageImagePreview.SetupScrolling()
        #self.pageImagePreview.Layout() #Resizes the tab's contents and ensures that its contents are displayed correctly. Required since tab is changed after it is initally drawn.
        ##self.pageImagePreview.SetupScrolling()

        self.imagePreviewSizer.Show(self.canvasImagePreview, show=False)
        self.imagePreviewSizer.Show(self.tableViewer, show=True)
        self.figureImagePreview.clf()  # Clears the Image Preview window
        self.pageImagePreview.Layout()  # Resizes the tab's contents and ensures that its contents are displayed correctly. Required since tab is changed after it is initally drawn.

        htmlText = """
        <!DOCTYPE html>
        <html>
        <body>
        """
        htmlText += "<small>Click anywhere in the table to activate scrolling.</small>"
        htmlText += "<h2>The original T1 data table</h2>"
        htmlText += T1_table_in_html

        htmlText += """
        </body>
        </html>
        """
        self.tableViewer.SetPage(htmlText)
        #self.imagePreviewViewer.Bind(wx.EVT_ACTIVATE, self.ActivateTest)
        #self.buttonSwitch.Bind(wx.EVT_BUTTON, self.OnSwitchViewing)
        #wx.EVT_ACTIVATE(self.pageImagePreview, self.ActivateTest())
        
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

    def DrawScatterFromTable(self):
        """Creates the scatter plot when table data is loaded"""
        
        # List of reference (nominal) T1 values
        # (parameter8 or index 7 using 0-based indexing)
        ref_T1_list = self.newModel.getValuesFromTable(self.data_table_T1_contents, 7, datatype="float")
        
        # List of calculated T1 values
        # (parameter9 or index 8 using 0-based indexing)
        cal_T1_list = self.newModel.getValuesFromTable(self.data_table_T1_contents, 8, datatype="float")
        
        minLim_x_T1 = numpy.nanmin(ref_T1_list)
        maxLim_x_T1 = numpy.nanmax(ref_T1_list)
        minLim_y_T1 = numpy.nanmin( [numpy.min(ref_T1_list), numpy.min(cal_T1_list)])
        maxLim_y_T1 = numpy.nanmax( [numpy.max(ref_T1_list), numpy.max(cal_T1_list)])
        
        spacing_x_T1 = (maxLim_x_T1 - minLim_x_T1) * 0.05
        spacing_y_T1 = (maxLim_y_T1 - minLim_y_T1) * 0.05
        
        self.PlotScatter([[cal_T1_list]], [[ref_T1_list]], \
            [['Reference T1']], [['Calculated T1']], \
            [['Distribution plot of T1']], \
            [[minLim_x_T1 - spacing_x_T1, maxLim_x_T1 + spacing_x_T1]], \
            [[minLim_y_T1 - spacing_y_T1, maxLim_y_T1 + 2*spacing_y_T1]])

    def OnExportToFolder(self, desDir):
        '''
        export the files as .png, excel
        '''
        saveDir = os.getcwd()
        if not (desDir == ''):
            saveDir = desDir
        elif desDir == '':
            dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
            if dlg.ShowModal() == wx.ID_OK:
                saveDir = dlg.GetPath()
            else:
                return
        self.SetStatusText('Exporting, please wait...')
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
            
        try:
            self.figureLOA_T1.savefig(os.path.join(saveDir, 'limits_of_agreement.png'))
        except:
            self.SetStatusText('Please close related LOA files and try to export again.')

        # export to excel
        book = Workbook()
        sheetNaN = book.add_sheet('NaN percentage')
        sheetMean = book.add_sheet('Mean')
        sheetStd = book.add_sheet('Standard deviation')
        sheetMedian = book.add_sheet('Median')
        sheet1Qtl = book.add_sheet('1st quartiel')
        sheet3Qtl = book.add_sheet('3rd quartiel')
        sheetMin = book.add_sheet('Minimum')
        sheetMax = book.add_sheet('Maximum')
        sheetCov = book.add_sheet('Covariance')
        sheetCor = book.add_sheet('Correlation')
        sheetRMSD = book.add_sheet('RMSD')
        sheetCCC = book.add_sheet('CCC')
        sheetTDI = book.add_sheet('TDI')
        #sheetLOA = book.add_sheet('LOA')
        sheetSigmaMetric = book.add_sheet('Sigma Metric')
        sheetFit = book.add_sheet('Model fitting')
        sheetT = book.add_sheet('T-test results')
        sheetU = book.add_sheet('U-test results')
        sheetChiq = book.add_sheet('Chi-square-test results')

        QIBA_functions.WriteToExcelSheet_T1_percentage(sheetNaN, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_NaN_percentage], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_statistics(sheetMean, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_mean], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_statistics(sheetStd, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_deviation], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_statistics(sheetMedian, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_median], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_statistics(sheet1Qtl, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_1stQuartile], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_statistics(sheet3Qtl, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_3rdQuartile], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_statistics(sheetMin, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_min], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_statistics(sheetMax, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_max], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)

        QIBA_functions.WriteToExcelSheet_T1_co(sheetCor, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.corr_T1T1], 1, self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_co(sheetCov, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.cov_T1T1], 1, self.nrOfRow, self.nrOfColumn)

        QIBA_functions.WriteToExcelSheet_T1_statistics(sheetRMSD, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_rmsd], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_statistics(sheetCCC, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_ccc], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_statistics(sheetTDI, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_tdi], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        #QIBA_functions.WriteToExcelSheet_T1_statistics(sheetLOA, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_loa], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_statistics(sheetSigmaMetric, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_sigma_metric], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn)

        QIBA_functions.WriteToExcelSheet_T1_fit(sheetFit, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.a_lin_T1, self.newModel.b_lin_T1, self.newModel.r_squared_lin_T1, self.newModel.a_log_T1,self.newModel.b_log_T1], 1, self.nrOfRow, self.nrOfColumn)
        QIBA_functions.WriteToExcelSheet_T1_test(sheetT, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_ttest_t, self.newModel.T1_cal_patch_ttest_p], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn, 'T-statistics')
        QIBA_functions.WriteToExcelSheet_T1_test(sheetU, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_Utest_u, self.newModel.T1_cal_patch_Utest_p], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn, 'U-value')

        QIBA_functions.WriteToExcelSheet_T1_test(sheetChiq, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_chisquare_c, self.newModel.T1_cal_patch_chisquare_p], int(self.nrOfColumn/2), self.nrOfRow, self.nrOfColumn, 'Chiq')

        # QIBA_functions.WriteToExcelSheet_T1_A(sheetA, self.newModel.headersHorizontal, self.newModel.headersVertical, [self.newModel.T1_cal_patch_ANOVA_f,self.newModel.T1_cal_patch_ANOVA_p], 1, self.nrOfRow, self.nrOfColumn)
        try:
            book.save(os.path.join(saveDir, 'results.xls'))
        except:
            self.SetStatusText('Please close related files and try to export again.')
            return
        self.SetStatusText('Files are exported.')

    def GetResultInHtml(self):
        # render the figures, tables into html, for exporting to pdf
        htmlContent = ''
        self.figureImagePreview.savefig(os.path.join(os.getcwd(), 'temp', 'figureImages.png'))
        self.figureScatter.savefig(os.path.join(os.getcwd(), 'temp', 'figureScatters.png'))
        self.figureHist_T1.savefig(os.path.join(os.getcwd(), 'temp', 'figureHist_T1.png'))
        self.figureBoxPlot.savefig(os.path.join(os.getcwd(), 'temp', 'figureBoxPlots.png'))
        self.figureLOA_T1.savefig(os.path.join(os.getcwd(), 'temp', 'figureLOA_T1.png'))

        htmlContent += self.newModel.packInHtml('<h1 align="center">QIBA DRO Evaluation Tool Results Report<br>(T1)</h1>')

        htmlContent += self.newModel.packInHtml('''
        <h2 align="center">The image view of calculated T1''' +\
        '''<img src="''' + os.path.join(os.getcwd(), 'temp', 'figureImages.png') + '''" style="width:100%"> <br>'''+\
        '''<p><font face="verdana">* The first row shows the calculated T1 in black and white. You can have a general impression of the value distribution according to the changing of the parameters. Generally the brighter the pixel is, the higher the calculated value is.<br>
        <br>The Second row shows the error map between calculated and reference data. Each pixel is the result of corresponding pixel in calculated data being subtracted with that in the reference data. Generally the more the color approaches to the red direction, the larger the error is.<br>
        <br>The third row shows the normalized error. This is out of the consideration that the error could be related with the original value itself. Therefore normalized error may give a more uniformed standard of the error level. Each pixel's value comes from the division of the error by the reference pixel value. Similarly as the error map, the more the color approaches to the red direction, the larger the normalized error is.
        </p>''' )

        htmlContent += self.newModel.packInHtml( '''
        <h2 align="center">The scatter plots of calculated T1</h2>
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureScatters.png') + '''" style="width:100%"> <br>'''+\
        '''<p><font face="verdana">* For the reference data, the pixel values in rows contains different values(details please refer to the file description). Therefore in the scatter plot it shows that all green dots of a row (or column) overlap to each other. For the calculated data, as they share the same parameter, the blue dots align to the same x-axis. But they may scatter vertically, showing there's variance of the value in a row (or column).<br>
        <br>From these plots you can see the trend of the values, which offer some information of which model (e.g. linear or logarithmic) the calculated parameter may fit. For example, with the artificial calculated data which were generated from the reference data by adding Gaussian noise, scaling by two and adding 0.5, it can be easily read from the plots that the calculated data follow the linear model, and have scaling factor and extra bias value.
        </p>''' )

        htmlContent += self.newModel.packInHtml('''
        <h2 align="center">The histograms of calculated T1</h2>
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureHist_T1.png') + '''" style="width:100%" align="right"> <br>'''+\
        '''<p><font face="verdana">* All histograms have the uniformed y-axis limits, so that the comparison among different patched is easier.  The minimum and maximum values of a patch are denoted on the x-axis for reference.
        </p>''')

        htmlContent += self.newModel.packInHtml('''
        <h2 align="center">The box plots of calculated T1</h2>
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureBoxPlots.png') + '''" style="width:100%"> <br>'''+\
        '''<p><font face="verdana">* The vertical dash lines are used to separate the rows (or columns), as each box plot is responsible for one patch. From these plots you could see (roughly) the statistics of each patch, like the mean value, the 1st and 3rd quartile, the minimum and maximum value. The more precise value of those statistics could be found in the tab "Result in HTML viewer".
        </p>''')

        htmlContent += self.newModel.NaNPercentageInHTML

        htmlContent += self.newModel.StatisticsInHTML

        htmlContent += self.newModel.covCorrResultsInHtml

        htmlContent += self.newModel.RMSDResultInHTML

        htmlContent += self.newModel.CCCResultInHTML
        
        htmlContent += self.newModel.TDIResultInHTML

        htmlContent += self.newModel.packInHtml('''
        <h2 align="center">The Bland-Altman Limits of Agreement plot of calculated T1</h2>
        <img src="''' + os.path.join(os.getcwd(), 'temp', 'figureLOA_T1.png') + '''" style="width:100%" align="left">''' + '''
        <p><h4>The repeatability coefficient is '''+str(self.t1_repeatability_coefficient)+'''</h4></p>
        </p></p>''')

        if self.verbose_mode:
            htmlContent += "<p><h5>" + StatDescriptions.loa_text + "</h5></p>"

        htmlContent += self.newModel.sigmaMetricResultInHTML

        htmlContent += self.newModel.ModelFittingInHtml

        htmlContent += self.newModel.T_testResultInHTML

        htmlContent += self.newModel.U_testResultInHTML

        htmlContent += self.newModel.ChiSquareTestResultInHTML

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

def ProcessWithoutGUI(mode, calFiles, refFiles, desDir, allowable_total_error_params, mask_path, verbose_mode):
    '''
    evaluate without GUI, for purpose of batch processing
    
    allowable_total_error_params : [allowable_total_error_set, allowable_total_error_eqn, allowable_total_error]
    '''
    #self.type_of_data_loaded = ""
    patchLen = 10
    
    desDir = desDir[0]
    desFile = os.path.basename(desDir)
    desDir = os.path.dirname(desDir)

    #os.chdir(desDir) #Change working directory to the destination directory
    
    allowable_total_error_set = allowable_total_error_params[0] # True or False
    allowable_total_error = allowable_total_error_params[1] # float or numpy.nan
    
    if mode == 'GKM':
        window = MainWindow_KV("QIBA evaluate tool (GKM)", calFiles, refFiles, desDir, verbose_mode=False)
        window.allowable_total_error_set = allowable_total_error_set
        window.allowable_total_error = allowable_total_error
        
        if mask_path is not None:
            # Load the mask file (image or table) if provided in the
            # parameters.  The contents of the mask file will be validated.
            # If the mask is not valid, then the default mask will be returned.
            # (The default mask is created when the MainWindow_KV object is created).
            window.mask = window.loadMaskFile(mask_path)
        
        print 'files loaded...'
        window.Show()
        window.Maximize(True)
        window.Hide()
        print 'start to evaluate...'
        window.OnEvaluate(None)
        print 'evaluation finished.'
        print 'exporting result...'
        window.OnExportToFolder(desDir)
        window.OnExportToPDFCmdLine(desDir)
        print 'results exported.'


    elif mode == "T1":
        window = MainWindow_T1("QIBA evaluate tool (T1)", calFiles, refFiles, desDir, verbose_mode)
        window.allowable_total_error_set = allowable_total_error_set
        window.allowable_total_error = allowable_total_error

        file_name = os.path.basename(calFiles)
        file_name_lc = file_name.lower()
        if "r1" in file_name_lc and "t1" in file_name_lc:
            print("\nAction Required: Cannot determine if the image file \"" + file_name + "\" contains R1 or T1 data.")
            print("Please enter 1 if the file contains R1 data, 2 if the file contains T1 data,")
            print("or 3 to exit.")
            r1_t1_user_input = getR1T1FromUser()
            print(file_name + " will be loaded as " + r1_t1_user_input +" data.")
            window.T1_R1_flag = r1_t1_user_input

        elif "r1" in file_name_lc:
            window.T1_R1_flag = "R1"
        elif "t1" in file_name_lc:
            window.T1_R1_flag = "T1"
        else:
            print("\nAction Required: Cannot determine if the image file \"" + file_name + "\" contains R1 or T1 data.")
            print("Please enter 1 if the file contains R1 data, 2 if the file contains T1 data,")
            print("or 3 to exit.")
            r1_t1_user_input = getR1T1FromUser()
            print(file_name + " will be loaded as " + r1_t1_user_input + " data.")
            window.T1_R1_flag = r1_t1_user_input


        if mask_path is not None:
            # Load the mask file (image or table) if provided in the
            # parameters.  The contents of the mask file will be validated.
            # If the mask is not valid, then the default mask will be returned.
            # (The default mask is created when the MainWindow_T1 object is created).
            window.mask = window.loadMaskFile(mask_path)
        
        window.Show()
        window.Maximize(True)
        window.Hide()
        window.OnEvaluate(None)
        window.OnExportToFolder(desDir)
        window.OnExportToPDFCmdLine(desDir)

    # Save the results table for both GKM and T1 modes
    window.saveResultsTable(save_path=desDir+os.path.sep+desFile)

def getR1T1FromUser():
    """In command line mode (T1 branch), QDET uses the file name to determine if the loaded calculated image
    contains R1 or T1 data. If "R1" and "T1" are both in the file name or if the file name doesn't contain "R1" or "T1",
    then get this from the user."""
    valid_entry = False
    number_of_times = 0
    accepted_exit_list = ["3", "quit", "exit", "bye", "goodbye", "end", "leave"]
    while not valid_entry:
        if number_of_times >=1 :
            r1_t1_user_input = raw_input("Please enter 1 for R1, 2 for T1, or 3 to exit.\n>")
        else:
            r1_t1_user_input = raw_input("\n>")
        r1_t1_user_input_lc = r1_t1_user_input.lower()
        r1_t1_user_input_lc.strip() #Remove trailing spaces and other blank characters

        if r1_t1_user_input == "1" or r1_t1_user_input_lc == "r1":
            return "R1"
        elif r1_t1_user_input == "2" or r1_t1_user_input_lc == "t1":
            return "T1"
        elif r1_t1_user_input_lc in accepted_exit_list:
            sys.exit("QDET exited by user")
        number_of_times = number_of_times + 1

def processGKMTablesWithoutGUI(ktransTableFile, veTableFile, desFile, allowable_total_error_params, verbose_mode):
    # allowable_total_error_params : [allowable_total_error_set, allowable_total_error_eqn, allowable_total_error]
    
    allowable_total_error_set = allowable_total_error_params[0] # True or False
    allowable_total_error = allowable_total_error_params[1] # float or numpy.nan
    
    window = MainWindow_KV("QIBA Evaluate tool (GKM)", [], [], desFile, verbose_mode=verbose_mode)
    window.allowable_total_error_set = allowable_total_error_set
    window.allowable_total_error = allowable_total_error
            
    ktrans_table_loaded = window.loadTextFileCmdLine_K(ktransTableFile)
    ve_table_loaded = window.loadTextFileCmdLine_V(veTableFile)
    if ktrans_table_loaded and ve_table_loaded:
        print("Evaluating ktrans table "+ktransTableFile)
        print(" and ve table "+veTableFile+"...")
    window.evaluateCmdLine()
    window.saveResultsTable(save_path=desFile)
    
def processT1TablesWithoutGUI(t1TableFile, desFile, allowable_total_error_params, verbose_mode):
    # allowable_total_error_params : [allowable_total_error_set, allowable_total_error_eqn, allowable_total_error]
    
    allowable_total_error_set = allowable_total_error_params[0] # True or False
    allowable_total_error = allowable_total_error_params[1] # float or numpy.nan
    
    window = MainWindow_T1("QIBA Evaluate Tool (T1)", [], [], desFile, verbose_mode=verbose_mode)
    window.allowable_total_error_set = allowable_total_error_set
    window.allowable_total_error = allowable_total_error
        
    t1_table_loaded = window.loadTextFileCmdLine_T1(t1TableFile)
    if t1_table_loaded:
        print("Evaluating T1 table "+t1TableFile)
    window.evaluateCmdLine()
    window.saveResultsTable(save_path=desFile)
    

def checkCmdLineArguments(args):
    valid_arguments = True
    error_message = ""
    # Some argument combinations are not valid. Exit if an invalid combination is found.
    if args.mode == "GKM" and args.t1file is not None:
        error_message += "QIBA Evaluate Tool error: GKM mode cannot be used to evaluate T1 mapping files\n"
        valid_arguments = False
    elif args.mode == "T1" and (args.ktransfile is not None or args.vefile is not None):
        error_message += "QIBA Evaluate Tool error: T1 mode cannot be used to evaluate Ktrans and Ve files\n"
        valid_arguments = False
    if args.ktransfile is not None and args.vefile is None:
        error_message += "QIBA Evaluate Tool error: If ktrans file(s) is/are provided, then ve file(s) must also be provided\n"
        valid_arguments = False
    elif args.vefile is not None and args.ktransfile is None:
        error_message += "QIBA Evaluate Tool error: If ve file(s) is/are provided, then ktrans file(s) must also be provided\n"
        valid_arguments = False
    elif args.cfile is not None and args.rfile is None:
        error_message += "QIBA Evaluate Tool error: If calculated image file(s) is/are provided, then reference image file(s) must also be provided\n"
        valid_arguments = False
    elif args.rfile is not None and args.cfile is None:
        error_message += "QIBA Evaluate Tool error: If reference image file(s) is/are provided, then calculated image file(s) must also be provided\n"
        valid_arguments = False
    
    #elif len(args.ktransfile) != len(args.vefile) and len(args.ktransfile) != len(args.destination):
    #    error_message += "QIBA Evaluate Tool error: The number of ktrans files, number of ve files, and number of destination files must all be the same\n"
    #    valid_arguments = False
    
    # Check allowable total error.
    # Allowable total error must be numeric.
    try:
        ate_float = float(args.ate[0])
    except ValueError:
        error_message += "QIBA Evaluate Tool error: Allowable total error must be numeric."
        valid_arguments = False
        
    if not valid_arguments:
        print(error_message)
        
    if args.mask is not None:
        if not os.path.exists(args.mask):
            error_message += "QIBA Evaluate Tool error: The file specified by the --mask parameter does not exist\n"
            valid_arguments = False
        if args.ktransfile is not None or args.vefile is not None or args.t1file is not None:
            if valid_arguments:
                print("Note: The --mask parameter is not needed if tables are provided. It will not be used in the analysis.")
            else:
                print("Note: The --mask parameter is not needed if tables are provided.")
        
    return valid_arguments
    
def checkIfFilesExist(list_of_files):
    """Check if the reference and calculated Ktrans/Ve/T1 files exist.
    If they don't then show an error message and exit"""
    not_found_files = ""
    for f in list_of_files:
        if not os.path.exists(f):
            not_found_files = not_found_files + f + "\n"

    if not_found_files != "":
        print("QIBA Evaluate Tool error: The following input file(s) could not be found:")
        print(not_found_files)
        sys.exit(1)

def main(argv):
    # generate the application object
    if len(argv) == 0:
        Application = wx.App() #For GUI mode, direct all output to a wxpython window
    else:
        Application = wx.App(redirect=False) #For command-line mode, direct all output to the terminal/console window

    ISCOMMAND = False

    # show the splash window
    DEBUG = True
    if DEBUG:
        pass
    else:
        QIBASplashWindow = MySplashScreen()
        QIBASplashWindow.Show()
        time.sleep(2)

    # deal with command line
    calFiles = []
    refFiles = []
    desDir = ''
    
    # New command-line argument handler
    if len(argv) == 0: # No command-line arguments provided. Run from GUI
        QIBASelectionDialog = MySelectionDialog(None, 'Please select which branch to enter:', 'Branch selection...', choices=['GKM', 'Flip Angle T1'])
        if QIBASelectionDialog.ShowModal() == wx.ID_OK:
            if QIBASelectionDialog.GetSelections() == 'GKM':
                window = MainWindow_KV("QIBA evaluate tool (GKM)", calFiles, refFiles, desDir, verbose_mode=False)
                window.Show()
                window.Maximize(True)
            elif QIBASelectionDialog.GetSelections() == 'Flip Angle T1':
                window = MainWindow_T1("QIBA evaluate tool (Flip Angle T1)", calFiles, refFiles, desDir, verbose_mode=False)
                window.Show()
                window.Maximize(True)
    else:
        parser = argparse.ArgumentParser("QIBA Evaluation Tool Command Line Mode")
        #parser.add_argument("-b", "--batch", action="store_true")
        parser.add_argument("-m", "--mode", choices=["GKM", "T1"], required=True)
        parser.add_argument("-c", "--cfile", nargs="+") # Ktrans and Ve images with calculated data, or T1 image with calculated data
        parser.add_argument("-r", "--rfile", nargs="+") # Ktrans and Ve image with reference data, or T1 image with calculated data
        parser.add_argument("-k", "--ktransfile", nargs="+")
        parser.add_argument("-v", "--vefile", nargs="+")
        parser.add_argument("-t", "--t1file", nargs="+")
        parser.add_argument("-d", "--destination", nargs="+", required=True)
        parser.add_argument("-a", "-e", "--ate", "--allowable_total_error", "--allowabletotalerror", nargs=1, required=True)
        parser.add_argument("--mask", nargs="?") # The path of the optional mask file. Used for image mode only (Ignore if supplied in table mode). Can be a text file or an image file.
        parser.add_argument("--verbose", action="store_true")
        # Valid parameters:
        # -----------------
        # If images are loaded:
        # 1 cfile and 1 rfile
        # 1 destination -- the destination is the output table (.cdata or .txt) file
        #
        # If tables are loaded:
        # (At least 1 ktransfile and at least 1 vefile) or (At least 1 t1file)
        # One destination for each set of input files
        # 0 or 1 mask file(s)


        args = parser.parse_args()
        
        # Some argument combinations are not valid. Exit if an invalid combination is found.
        # (Note: the argparse parser will detect if mode is GKM/T1 or if destination is set
        valid_arguments = checkCmdLineArguments(args)
        
        mode = args.mode # (GKM or T1)
        desDir = args.destination

        # Non-image based mode takes precedence over image based mode.
        # If image-based parameters (cfile & rfile) and non-image based parameters (ktransfile, vefile, t1file) are both set,
        # then display a warning message that the image-based options will be ignored
        if args.ktransfile is not None and args.cfile is not None:
            print("QIBA Evaluate Tool warning: Image files will be ignored because tables were provided.")
        
        if args.ktransfile is not None:
            #do Ktrans/Ve text file handling here
            ktransFiles = args.ktransfile
            veFiles = args.vefile
            dataType = "table"
        elif args.t1file is not None:
            #do T1 text file handling here
            t1Files = args.t1file
            dataType = "table"
        else:
            calFiles = args.cfile
            refFiles = args.rfile
            checkIfFilesExist(calFiles+refFiles)
            if mode == "GKM":
                calFiles = calFiles[0]+","+calFiles[1] # Convert the list of calFiles into a comma-separated string -- the program expects a comma-separated string
                refFiles = refFiles[0]+","+refFiles[1] # Convert the list of refFiles into a comma-separated string -- the program expects a comma-separated string
                #checkIfFilesExist([calFiles[0], calFiles[1], refFiles[0], refFiles[1]])
            elif mode == "T1":
                calFiles = calFiles[0] # Convert the one item list to a string
                refFiles = refFiles[0] # Convert the one item list to a string
                #checkIfFilesExist([calFiles, refFiles])
            dataType = "image"
        
        if len(sys.argv) > 1 and valid_arguments:
            # Set Allowable Total Error - The input from the command line
            # has already been validated
            allowable_total_error = float(args.ate[0])
            allowable_total_error_set = True
        
            allowable_total_error_params = [allowable_total_error_set, allowable_total_error]

            verbose_mode = args.verbose

            try:
                if dataType == "image":
                    mask_path = args.mask
                    ProcessWithoutGUI(mode, calFiles, refFiles, desDir, allowable_total_error_params, mask_path, verbose_mode)
                elif dataType == "table" and mode == "GKM":
                    for i in range(len(ktransFiles)):
                        processGKMTablesWithoutGUI(ktransFiles[i], veFiles[i], desDir[i], allowable_total_error_params, verbose_mode)
                elif dataType == "table" and mode == "T1":
                    for i in range(len(t1Files)):
                        processT1TablesWithoutGUI(t1Files[i], desDir[i], allowable_total_error_params, verbose_mode)
                exit(0)

            except Exception as e: #For debugging. Originally just "except".
                print(e) #For debugging
                ex_type, ex, tb = sys.exc_info() #For debugging
                traceback.print_tb(tb) #For debugging
            #except:
            #    print("An error occurred during processing")

            
            
        #else: #GUI modepass
            # initialize the main window
            #try:
            #    if mode == "GKM":
            #        # window = MainWindow_KV("QIBA evaluate tool (GKM)", calFiles, refFiles, desDir)
            #        window = MainWindow_KV("QIBA evaluate tool (GKM)", calFiles, refFiles, desDir)
            #        window.Show()
            #        window.Maximize(True)
            #    elif mode == "T1":
            #        window = MainWindow_T1("QIBA evaluate tool (Flip Angle T1)", calFiles, refFiles, desDir)
            #        window.Show()
            #        window.Maximize(True)
            #except:
            #    pass
    """        
    try:
        opts, args = getopt.getopt(argv, "hb:m:c:r:d:", ["batch", "mode=", "cfile=", "rfile=", "destination="])
        if not opts: # open GUI
            QIBASelectionDialog = MySelectionDialog(None, 'Please select which branch to enter:', 'Branch selection...', choices=['GKM', 'Flip Angle T1'])
            if QIBASelectionDialog.ShowModal() == wx.ID_OK:
                if QIBASelectionDialog.GetSelections() == 'GKM':
                    window = MainWindow_KV("QIBA evaluate tool (GKM)", calFiles, refFiles, desDir)
                    window.Show()
                    window.Maximize(True)
                elif QIBASelectionDialog.GetSelections() == 'Flip Angle T1':
                    window = MainWindow_T1("QIBA evaluate tool (Flip Angle T1)", calFiles, refFiles, desDir)
                    window.Show()
                    window.Maximize(True)
        else:
            for opt, arg in opts:
                if opt == '-m':
                    mode = arg
                elif opt == "-c":
                    calFiles = arg
                elif opt == "-r":
                    refFiles = arg
                elif opt == "-d":
                    desDir = arg
                elif opt == '-b':
                    ISCOMMAND = True
            if ISCOMMAND:
                try:
                    ProcessWithoutGUI(mode, calFiles, refFiles, desDir)
                    return
                except:
                    print "Error occurs. Evaluation terminated."
                    return

            # initialize the main window
            try:
                if mode == "GKM":
                    # window = MainWindow_KV("QIBA evaluate tool (GKM)", calFiles, refFiles, desDir)
                    window = MainWindow_KV("QIBA evaluate tool (GKM)", calFiles, refFiles, desDir)
                    window.Show()
                    window.Maximize(True)
                elif mode == "T1":
                    window = MainWindow_T1("QIBA evaluate tool (Flip Angle T1)", calFiles, refFiles, desDir)
                    window.Show()
                    window.Maximize(True)
            except:
                pass
    except getopt.GetoptError:
        pass
    """
    
    # main loop
    Application.MainLoop()

if __name__ == "__main__":

    main(argv[1:])

