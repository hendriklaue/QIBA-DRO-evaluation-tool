# the scramble tool

import wx
import os
import QIBA_functions
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.figure import Figure
from os.path import isfile, join
import shutil


class MyWindow(wx.Frame):

    def  __init__(self, parent = None):
        wx.Frame.__init__(self, parent = None, title = "QIBA scramble tool", size = (905, 600), style= wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX)
        self.fileTypeList = ['.dcm', '.bin', '.raw', '.tif']
        self.fileType = ""
        self.CenterOnScreen()
        self.CreateStatusBar()
        self.SetStatusText("Welcome to QIBA scramble tool!")
        self.SetupMenuBar()

        self.currentPage = -1
        self.pageNumber = 0
        self.nrOfRow = 0
        self.nrOfColumn = 0
        self.patchLen = 10
        self.imageList1 = []
        self.imageList2 = []
        self.imagePathListSource = []
        self.mapScrambleIndex = []
        self.SetupMainUI()

    def SetupMenuBar(self):
        '''
        set up the menu bar
        '''
        self.menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        OnExit = fileMenu.Append(wx.ID_ANY, "&Quit\tCtrl+Q", "Quit")

        editMenu = wx.Menu()
        OnEditImageDimension = editMenu.Append(wx.ID_ANY, "Change the image dimension...")
        editMenu.AppendSeparator()
        OnChangeSourceFolder = editMenu.Append(wx.ID_ANY, "Change the source folder...")
        OnChangeDestinationFolder = editMenu.Append(wx.ID_ANY, "Change the destination folder...")

        aboutMenu = wx.Menu()
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

        self.menubar.Bind(wx.EVT_MENU, self.OnEditImageDimension, OnEditImageDimension)
        self.menubar.Bind(wx.EVT_MENU, self.OnChangeSourceFolder, OnChangeSourceFolder)
        self.menubar.Bind(wx.EVT_MENU, self.OnChangeDestinationFolder, OnChangeDestinationFolder)
        self.menubar.Bind(wx.EVT_MENU, self.OnQuit, OnExit)
        self.menubar.Bind(wx.EVT_MENU, self.OnAbout, OnAboutApp)

        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(editMenu, "&Edit")
        self.menubar.Append(aboutMenu, "&About")
        self.SetMenuBar(self.menubar)

    def SetupMainUI(self):
        '''
        set up the main UI
        '''
        self.mainPanel = wx.Panel(self)
        sizerMain = wx.BoxSizer(wx.VERTICAL)
        sizerPaths = wx.FlexGridSizer(cols = 3, hgap = 6, vgap = 6 )
        sizerButtons = wx.FlexGridSizer(cols = 1, vgap = 20)
        sizerViewer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerSelector = wx.FlexGridSizer(rows = 1, vgap = 20)

        # sizer for paths
        SourceLocationText = wx.StaticText(self.mainPanel, -1, "Source folder:")
        self.SourceLocation = os.getcwd()
        self.SourceLocationTextControl = wx.TextCtrl(self.mainPanel, -1, self.SourceLocation, size = (650, -1))
        buttonBrowse1 = wx.Button(self.mainPanel, -1, "Browse...")
        buttonBrowse1.Bind(wx.EVT_BUTTON, self.OnChangeSourceFolder)

        DestinationLocationText = wx.StaticText(self.mainPanel, -1, "Destination folder:")
        self.DestinationLocation = os.getcwd()
        self.DestinationLocationTextControl = wx.TextCtrl(self.mainPanel, -1, self.DestinationLocation, size = (650, -1))
        buttonBrowse2 = wx.Button(self.mainPanel, -1, "Browse...")
        buttonBrowse2.Bind(wx.EVT_BUTTON, self.OnChangeDestinationFolder)

        sizerPaths.AddMany([SourceLocationText, self.SourceLocationTextControl, buttonBrowse1, DestinationLocationText, self.DestinationLocationTextControl, buttonBrowse2])
        # self.mainPanel.SetSizer(sizerPaths)

        # sizer for image previews
        buttonScramble = wx.Button(self.mainPanel, -1, "Scramble")
        buttonScramble.Bind(wx.EVT_BUTTON, self.OnScramble)
        buttonUnscramble = wx.Button(self.mainPanel, -1, "Unscramble")
        buttonUnscramble.Bind(wx.EVT_BUTTON, self.OnUnscramble)
        buttonSave = wx.Button(self.mainPanel, -1, "Save")
        buttonSave.Bind(wx.EVT_BUTTON, self.OnSave)
        sizerButtons.AddMany([buttonScramble, buttonUnscramble, buttonSave])
        # self.mainPanel.SetSizer(sizerButtons)

        self.figurePreviewerSource = Figure()
        self.figurePreviewerSource.set_figwidth(5)
        self.figurePreviewerSource.set_figheight(5)
        self.canvasPreviewerSource = FigureCanvas(self.mainPanel, -1, self.figurePreviewerSource)
        self.figurePreviewerDestination = Figure()
        self.figurePreviewerDestination.set_figwidth(5)
        self.figurePreviewerDestination.set_figheight(5)
        self.canvasPreviewerDestination = FigureCanvas(self.mainPanel, -1, self.figurePreviewerDestination)
        sizerViewer.AddMany([self.canvasPreviewerSource, sizerButtons, self.canvasPreviewerDestination])
        # self.mainPanel.SetSizer(sizerViewer)
        sizerViewer.Fit(self.mainPanel)

        # viewer selector
        self.buttonToHead = wx.Button(self.mainPanel, -1, "|<<")
        self.buttonToHead.Bind(wx.EVT_BUTTON, self.OnToHead)
        self.buttonToPrevious = wx.Button(self.mainPanel, -1, "Previous")
        self.buttonToPrevious.Bind(wx.EVT_BUTTON, self.OnToPrevious)
        self.buttonToNext = wx.Button(self.mainPanel, -1, "Next")
        self.buttonToNext.Bind(wx.EVT_BUTTON, self.OnToNext)
        self.buttonToEnd = wx.Button(self.mainPanel, -1, ">>|")
        self.buttonToEnd.Bind(wx.EVT_BUTTON, self.OnToEnd)

        self.currentPageText = wx.TextCtrl(self.mainPanel, -1, str(self.currentPage + 1), size = (25, -1))
        self.pageNumberText = wx.StaticText(self.mainPanel, -1, '/'+str(self.pageNumber), size = (30, -1))

        self.sizerSelector.AddMany([self.buttonToHead, self.buttonToPrevious, self.currentPageText, self.pageNumberText, self.buttonToNext, self.buttonToEnd])
        # self.mainPanel.SetSizer(sizerSelector)

        # main sizer
        sizerMain.AddMany([sizerPaths, sizerViewer, self.sizerSelector])
        sizerMain.Fit(self.mainPanel)
        self.mainPanel.SetSizer(sizerMain)

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

    def OnScramble(self, event):
        '''
        scramble the images under the selected folder
        '''
        try:
            self.imageList2, self.scrambleMap = QIBA_functions.ScrambleAndMap(self.imageList1, self.nrOfRow, self.nrOfColumn, self.patchLen)
        except:
            self.SetStatusText('Please make sure the image dimension fits!')
        self.ShowDestinationImage(self.imageList2[self.currentPage])
        self.SetStatusText('Images are scrambled.')

    def OnUnscramble(self, event):
        '''
        unscramble the images under the selected folder
        '''
        pass

    def OnSave(self, event):
        '''
        save the scrambled/unscrambled images
        '''

        for (index, sourceFilePath) in list(enumerate(self.imagePathListSource)):
            shutil.copy(sourceFilePath, self.DestinationLocation)

            fileName, fileExtension = os.path.splitext(sourceFilePath)
            dir, fileNameWithExtension = os.path.split(sourceFilePath)
            newFilePath = os.path.join(self.DestinationLocation, fileNameWithExtension)
            if fileExtension == '.dcm':
                ds =  QIBA_functions.dicom.read_file(newFilePath)
                for i, row in enumerate(self.imageList2[index]):
                    ds.pixel_array[i] = row
                ds.PixelData = ds.pixel_array.tostring()
                ds.save_as(newFilePath)
            elif fileExtension == '.tif':
                newImage = QIBA_functions.Image.fromarray(self.imageList2[index])
                newImage.save(newFilePath)
            elif fileExtension in ['.bin', '.raw']:
                pass
            else:
                self.SetStatusText('New images are not saved!')
                return
        self.SetStatusText('New Images are saved!')
        # save the map



    def OnToHead(self, event):
        '''
        jump to the head image
        '''
        self.currentPage = 0
        self.ShowSourceImage(self.imageList1[self.currentPage])
        if not( self.imageList2 == []):
            self.ShowDestinationImage(self.imageList2[self.currentPage])
        self.currentPageText.SetValue(str(self.currentPage + 1))
        self.buttonToNext.Enable()
        self.buttonToPrevious.Disable()

    def OnToPrevious(self, event):
        '''
        jump to the previous image
        '''

        self.currentPage = self.currentPage - 1
        self.ShowSourceImage(self.imageList1[self.currentPage])
        if not( self.imageList2 == []):
            self.ShowDestinationImage(self.imageList2[self.currentPage])

        self.currentPageText.SetValue(str(self.currentPage + 1))
        if self.currentPage - 1 == -1:
            self.buttonToPrevious.Disable()
        if not (self.currentPage  + 1 == self.pageNumber):
            self.buttonToNext.Enable()

    def OnToNext(self, event):
        '''
        jump to the next image
        '''
        self.currentPage = self.currentPage + 1
        self.ShowSourceImage(self.imageList1[self.currentPage])
        if not( self.imageList2 == []):
            self.ShowDestinationImage(self.imageList2[self.currentPage])

        self.currentPageText.SetValue(str(self.currentPage + 1))
        if self.currentPage + 1 == self.pageNumber:
            self.buttonToNext.Disable()
        if not (self.currentPage - 1 == -1):
            self.buttonToPrevious.Enable()

    def OnToEnd(self, event):
        '''
        jump to the end image
        '''
        self.currentPage = self.pageNumber -  1
        self.ShowSourceImage(self.imageList1[self.currentPage])
        if not( self.imageList2 == []):
            self.ShowDestinationImage(self.imageList2[self.currentPage])
        self.currentPageText.SetValue(str(self.currentPage + 1))
        self.buttonToNext.Disable()
        self.buttonToPrevious.Enable()

    def OnChangeSourceFolder(self, event):
        '''
        change the source folder
        '''
        dlg = wx.DirDialog(self, 'Change the source folder:', style = wx.DD_DEFAULT_STYLE |  wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.ClearPreview()

            path = dlg.GetPath()
            self.SourceLocationTextControl.SetValue(path)
            for f in os.listdir(path):
                if (isfile(join(path, f)) and (os.path.splitext(f)[1] in self.fileTypeList)):
                    self.fileType = os.path.splitext(f)[1]
                    filePath = join(path, f)
                    self.imagePathListSource.append(filePath)
                    rawFile, self.nrOfRow, self.nrOfColumn = QIBA_functions.ImportRawFile(filePath, self.patchLen)
                    self.imageList1.append(rawFile)
                else:
                    pass
            self.pageNumber = len(self.imageList1)
            if self.pageNumber:
                self.currentPage = 0
                self.ShowSourceImage(self.imageList1[self.currentPage])
                self.SetStatusText(str(len(self.imageList1)) + 'loaded.')
            else:
                self.pageNumber = 0
                self.currentPage = -1
                self.SetStatusText('Source folder contains no valid file!.')
            self.pageNumberText.SetLabel('/' + str(self.pageNumber))
            self.currentPageText.SetValue(str(self.currentPage + 1))
        else:
            self.SetStatusText('Source folder not refreshed.')

    def ClearPreview(self):
        '''
        clear the preview
        '''
        self.imageList2 = []
        self.imageList1 = []
        self.imagePathListSource = []
        self.figurePreviewerSource.clear()
        self.canvasPreviewerSource.draw()
        self.figurePreviewerDestination.clear()
        self.canvasPreviewerDestination.draw()
        self.currentPage = -1
        self.pageNumber = 0
        self.currentPageText.SetValue(str(self.currentPage + 1))
        self.pageNumberText.SetLabel('/' + str(self.pageNumber))

    def ShowSourceImage(self, image):
        '''
        show the image
        '''
        subplot = self.figurePreviewerSource.add_subplot(111)
        subplot.imshow(image, cmap = 'bone', interpolation='nearest')

        self.figurePreviewerSource.tight_layout()
        self.canvasPreviewerSource.draw()

    def ShowDestinationImage(self, image):
        '''
        show the image
        '''
        subplot = self.figurePreviewerDestination.add_subplot(111)
        subplot.imshow(image, cmap = 'bone', interpolation='nearest')

        self.figurePreviewerDestination.tight_layout()
        self.canvasPreviewerDestination.draw()

    def OnChangeDestinationFolder(self, event):
        '''
        change the destination folder
        '''
        dlg = wx.DirDialog(self, 'Change the destination folder:', style = wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.DestinationLocation = dlg.GetPath()
            self.DestinationLocationTextControl.SetValue(dlg.GetPath())
            self.SetStatusText('Destination folder selected.')
        else:
            self.SetStatusText('Destination folder not selected.')

    def OnAbout(self, event):
        pass

    def OnQuit(self, event):
        self.Close()

if __name__ == "__main__":
    # generate the application object
    Application = wx.App()

    window = MyWindow()

    # show the application's main window
    window.Show()
    # window.Maximize(True)
    Application.MainLoop()
