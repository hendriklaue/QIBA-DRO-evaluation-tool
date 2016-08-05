import wx

class ATEDialogBox(wx.Dialog):
    """This class defines a dialog box that allows the user to
    specify the allowable total error (ATE).  
    ATE is part of the formula for calculating the sigma metric.
    
    An alternate method of calculating ATE is using the equation
     
                                 2     2  0.5
    ATE = 1.65 * 0.5CV  + 0.25(CV  + CV  )
                      I          I     G
    where CV  is within-subject biological coefficient of variation and
            I
    CV  is between-subject biological coefficient of variation.
      G
      
    The option may be provided in a future update.
    """
    
    def __init__(self, parent, title, size, value_for_text_box):
        wx.Dialog.__init__(self, parent, -1, title, size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.THICK_FRAME|wx.RESIZE_BORDER|wx.TAB_TRAVERSAL)
        
        
        panel = wx.Panel(self)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        
        ate_box = wx.StaticBox(panel, label="Specify the value for Allowable Total Error")
        ate_box_sizer = wx.StaticBoxSizer(ate_box, orient=wx.VERTICAL)
        
        ate_value_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        #self.use_ate_value_radiobutton = wx.RadioButton(panel, label="Use ATE Value", style=wx.RB_GROUP)
        #self.use_eqn_radiobutton = wx.RadioButton(panel, label="Use 1.65 * 0.5CVi + 0.25(CVi**2 + CVg**2)**0.5")
        
        #ate_value_sizer.Add(self.use_ate_value_radiobutton)
        ate_label = wx.StaticText(panel, -1, "Allowable Total Error")
        self.ate_value_textbox = wx.TextCtrl(panel, value=str(value_for_text_box))
        ate_value_sizer.Add(ate_label,flag=wx.LEFT, border=5)
        ate_value_sizer.Add(self.ate_value_textbox, flag=wx.LEFT, border=5)
        
        #equation_label_1 = wx.StaticText(panel, -1, "\n     where CVi is the within-subject biological coefficient of variation,")
        #equation_label_2 = wx.StaticText(panel, -1, "     CVg is the between-subject biological coefficient of variation,")
        #equation_label_3 = wx.StaticText(panel, -1, "     and \"**\" means \"raised to the power\"") 
        ate_method_text = \
        """\nThe proper method of calculating ATE is a subject of research and likely
will vary with the application use case. One suggested starting point is the equation
ATE = 1.65 * 0.5CVi  + 0.25(CVi**2  + CVg**2)**0.5
where CVi is within-subject biological coefficient of variation,
CVg is between-subject biological coefficient of variation, and
** means raised to the power.

(Source: http://link.springer.com/article/10.1007%2Fs00769-009-0630-8#page-1)
"""
        ate_method_label = wx.StaticText(panel, -1, ate_method_text)
        
        
        ate_box_sizer.Add(ate_value_sizer)
        ate_box_sizer.Add(ate_method_label)
        #ate_box_sizer.Add(self.use_eqn_radiobutton)
        #ate_box_sizer.Add(equation_label_1)
        #ate_box_sizer.Add(equation_label_2)
        #ate_box_sizer.Add(equation_label_3)
        
        
        panel.SetSizer(ate_box_sizer)
        
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, label="OK")
        cancel_button = wx.Button(self, label="Cancel")
        button_sizer.Add(ok_button)
        button_sizer.Add(cancel_button, flag=wx.LEFT, border=5)
        
        v_sizer.Add(panel, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        v_sizer.Add(button_sizer, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)
        
        self.SetSizer(v_sizer)
        
        ok_button.Bind(wx.EVT_BUTTON, self.onClose)
        cancel_button.Bind(wx.EVT_BUTTON, self.onClose)
        
        self.SetFocus()
    
        #wx.Frame.__init__(self, parent, title="Allowable Total Error", size = (wx.SYS_SCREEN_X/10, wx.SYS_SCREEN_Y/10))
        #self.Bind(wx.EVT_CLOSE, self.onClose) #What to do when dialog box is closed
        
        #self.ok_button = wx.Button 
        
    def getActiveRadioButton(self):
        """Gets which radio button is active (Use ATE Value or
        Use Equation)
        
        Returns 0 if Use ATE Value is active or
        returns 1 if Use Equation is active.
        
        Returns -1 if neither is active (this shouldn't actually occur)
        
        Currently, this function is not used.  If a future update allows
        the user to specify ATE or use the equation, then this function
        will be needed
        """
        button_0_state = self.use_ate_value_radiobutton.GetValue()
        button_1_state = self.use_eqn_radiobutton.GetValue()
        
        if button_0_state:
            return 0
        elif button_1_state:
            return 1
            
        return -1
    
    def getATEValue(self):
        """Gets the value entered in the Use ATE Value box. Only returns
        this value if the Use ATE Value radio button is active. Otherwise,
        an empty string is returned.
        """

        #if self.getActiveRadioButton() == 0:
        return self.ate_value_textbox.GetValue()
        
    def onClose(self, event):
        self.button_clicked_name = event.GetEventObject().GetLabelText()
        #state = self.use_ate_value_radiobutton.GetValue()
        
        #if self.button_clicked_name == "OK": #for testing
        #    print(str(state)) #for testing
        #    print(button_clicked_name) #for testing
        #    s = self.getActiveRadioButton() #for testing
        #    ate_value = self.getATEValue() #for testing
        #    print(str(s)) #for testing
        #    print(self.getATEValue()) #for testing
        
        self.Close()
        #print("self.button_clicked_name:"+self.button_clicked_name)
        #self.Destroy()
        
    def destroy(self):
        self.Destroy()
        
#For testing the dialog box. Delete this when done.
#app = wx.App(redirect=False)
#dialog = ATEDialogBox(None, "Allowable Total Error", (500,300), "0.0")
#dialog.ShowModal()
#b = dialog.button_clicked_name
#a = dialog.getActiveRadioButton()
#v = dialog.getATEValue()
#print(str(a))
#print(b)
#print(str(v))
#dialog.destroy()

#app.MainLoop()

