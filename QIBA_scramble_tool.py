# the scramble tool

import wx
import random
import os


class MyWindow(wx.Frame):

    def  __init__(self, parent = None):
        wx.Frame.__init__(self, parent = None, title = "QIBA scramble tool", size = (900, 600))
        self.CenterOnScreen()
        self.CreateStatusBar()
        self.SetStatusText("Welcome to QIBA scramble tool!")
        self.SetupMenuBar()
        self.SetupMainUI()

    def SetupMenuBar(self):
        '''
        set up the menu bar
        '''
        self.menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        OnExit = fileMenu.Append(wx.ID_ANY, "&Quit\tCtrl+Q", "Quit")

        editMenu = wx.Menu()
        OnChangeSourceFolder = editMenu.Append(wx.ID_ANY, "Change the source folder...")
        OnChangeDestinationFolder = editMenu.Append(wx.ID_ANY, "Change the destination folder...")

        aboutMenu = wx.Menu()
        OnAboutApp = aboutMenu.Append(wx.ID_ANY, "About this application")

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
        sizerViewer = wx.BoxSizer(wx.HORIZONTAL)

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
        self.mainPanel.SetSizer(sizerPaths)

    def OnChangeSourceFolder(self, event):
        '''
        change the source folder
        '''
        dlg = wx.DirDialog(self, 'Change the source folder:', style = wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.SourceLocationTextControl.SetValue(dlg.GetPath())
            self.SetStatusText('Source folder refreshed.')
        else:
            self.SetStatusText('Source folder not refreshed.')

    def OnChangeDestinationFolder(self, event):
        '''
        change the destination folder
        '''
        dlg = wx.DirDialog(self, 'Change the destination folder:', style = wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.DestinationLocationTextControl.SetValue(dlg.GetPath())
            self.SetStatusText('Destination folder refreshed.')
        else:
            self.SetStatusText('Destination folder not refreshed.')

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


