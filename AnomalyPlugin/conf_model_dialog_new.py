"""Contains the ConfModelDialog used by the TrackGUI"""
import re
import wx
import wx.aui
from AnomalyPlugin.model_selection_window import ModelSelectionWindow


class ConfModelDialog(wx.Dialog):
    """The dialog opened when clicking the "model configuration" button.
     It allows the user to send new models to the server.
     It also queries the server for available models and gives
     the user the option to serve or delete them. For further reference
     check out the guide (ML-Guide.txt).
    """

    def __init__(self, parent, plugin):
        """Initializes the GUI.

        Args:
            parent (wx.Window): The parent Window.
            plugin (MainPlugin): The instance of the plugin.
        """
        wx.Dialog.__init__(self, parent, size=(510, 280), style=wx.DEFAULT_DIALOG_STYLE)
        self.plugin = plugin
        self.av_models, self.ac_model, self.ac_model_conf, self.inp_shape = self.get_models()

        self.control_elements()
        self.control_logic()
        self.layouting()


    def control_elements(self):
        """Loads all the GUI-Elements for the configure model dialog.
        """
        self.button_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.text_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)

        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.VERTICAL)
        self.model_sizer = wx.BoxSizer(wx.VERTICAL)
        self.text_sizer = wx.GridBagSizer(2, 1)

        self.model_ctrl = wx.ListCtrl(self, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.active_text = wx.StaticText(self.text_panel)
        self.active_shape = wx.StaticText(self.text_panel)
        self.update_models()
        self.send_button = wx.Button(self.button_panel, 1, "Send model")
        self.delete_button = wx.Button(self.button_panel, 2, "Delete model")
        self.serve_button = wx.Button(self.button_panel, 3, "Serve model")
        self.close_button = wx.Button(self.button_panel, 4, "Close")


    def control_logic(self):
        """Binds the elements to their logic.
        """
        self.Bind(wx.EVT_BUTTON, self.on_send, id=1)
        self.Bind(wx.EVT_BUTTON, self.on_delete, id=2)
        self.Bind(wx.EVT_BUTTON, self.on_serve, id=3)
        self.Bind(wx.EVT_BUTTON, self.on_close, id=4)


    def layouting(self):
        """Layouts and aligns all the GUI-Elements in the configure model dialog.
        """
        self.button_sizer.Add(
            self.send_button, 1, flag=wx.EXPAND)
        self.button_sizer.Add(
            self.delete_button, 1, flag=wx.EXPAND)
        self.button_sizer.Add(
            self.serve_button, 1, flag=wx.EXPAND)
        self.button_sizer.Add(
            self.close_button, 1, flag=wx.EXPAND)
        self.button_panel.SetSizer(self.button_sizer)

        self.text_sizer.Add(
            self.active_text, pos=(0, 0), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=0)
        self.text_sizer.Add(
            self.active_shape, pos=(1, 0), flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=0)
        self.text_panel.SetSizer(self.text_sizer)

        self.model_sizer.Add(
            self.model_ctrl, flag=wx.EXPAND | wx.TOP | wx.RIGHT, border=5)
        self.model_sizer.Add(
            self.text_panel, flag=wx.EXPAND | wx.BOTTOM | wx.TOP | wx.RIGHT, border=5)

        self.main_sizer.Add(
            self.button_panel, 2, flag=wx.EXPAND | wx.ALL, border=5)
        self.main_sizer.Add(
            self.model_sizer, 3, flag=wx.EXPAND)
        self.SetSizer(self.main_sizer)


    def on_send(self, evt):
        """Called by the "Send model" button. Opens the model selection window

        Args:
            evt (wx.EVENT): unused
        """
        model_window = ModelSelectionWindow(parent=self, plugin=self.plugin)
        model_window.Show(True)
        self.av_models, self.ac_model, self.ac_model_conf, self.inp_shape = self.get_models()
        self.update_models()


    def on_delete(self, evt):
        """Called by the "Delete model" button. Instructs the server to delete the model selected by the user.

        Args:
            evt (wx.EVENT): unused
        """
        index = self.model_ctrl.GetFirstSelected()
        if index < 0:
            wx.MessageBox("Must select a model first.", 'Error', wx.OK | wx.ICON_ERROR)
        else:
            name = self.model_ctrl.GetItemText(index)
            dia = wx.MessageDialog(
                parent=self,
                message=f"This will delete the {name} dataset for ever! Continue?",
                caption="WARNING!",
                style=wx.OK | wx.CANCEL | wx.OK_DEFAULT)
            if  not dia.ShowModal() == wx.ID_OK:
                return
            else:
                resp = self.plugin.server_api.delete_model(name)
                if not resp:
                    wx.MessageBox("Couldnt delete model.", 'Error', wx.OK | wx.ICON_ERROR)
                else:
                    self.av_models, self.ac_model, self.ac_model_conf, self.inp_shape = self.get_models()
                    self.update_models()


    def on_serve(self, evt):
        """Called by the "Serve model" button. Instructs the server to serve the model selected by the user.

        Args:
            evt (wx.EVENT): unused
        """
        index = self.model_ctrl.GetFirstSelected()
        if index < 0:
            wx.MessageBox("Must select a model first.", 'Error', wx.OK | wx.ICON_ERROR)
        else:
            name = self.model_ctrl.GetItemText(index)
            resp = self.plugin.server_api.serve(name)
            if not resp:
                wx.MessageBox("Couldnt serve model.", 'Error', wx.OK | wx.ICON_ERROR)
            else:
                self.av_models, self.ac_model, self.ac_model_conf, self.inp_shape = self.get_models()
                self.update_models()


    def on_close(self, evt):
        """ Called by the "Close" button.

        Args:
            evt (wx.EVENT): unused
        """
        self.Close()


    def update_models(self):
        """ Updates the displayed models.
        """
        self.model_ctrl.ClearAll()
        self.model_ctrl.InsertColumn(0, "Models")
        self.model_ctrl.SetColumnWidth(0, 300)
        [self.model_ctrl.InsertItem(0, item) for item in self.av_models]
        self.active_text.SetLabel("Active model: " + str(self.ac_model))
        self.active_shape.SetLabel("Input shape : " + self.inp_shape)


    def get_models(self):
        """Queries the server for available models.

        Returns:
            list: A list of names (strings).
        """
        if not self.plugin.server_api.is_busy():
            av_models = self.plugin.server_api.get_available_models()["data"]
            ac_model = self.plugin.server_api.get_active_model()["data"]
            ac_model_conf = ac_model[1]
            ac_model = ac_model[0]
            confstr = str(ac_model_conf)
            try:
                inp_shape = re.search(
                    r"\[.*\]",
                    re.search(r'"batch_input_shape": \[([\d\s,]|null)*\]', confstr).group(0)).group(0)
            except:
                inp_shape = ""
            return (av_models, ac_model, ac_model_conf, inp_shape)
        else:
            wx.MessageBox("Server not available.", 'Error', wx.OK | wx.ICON_ERROR)
            self.Close()
