"""Contains the ModelSelectionWindow used by the TrackGUI"""
import os
import base64
import wx
import wx.aui


class ModelSelectionWindow(wx.Frame):
    """This class implements the Model Selection window, used to select a machine
    learning model (h5/json-file). The model
    is sent with the specified compile parameters.
    For further reference check out the guide (ML-Guide.txt).
    """

    def __init__(self, parent, plugin):
        """Initializing method for the windw

        Args:
            parent (wx.Window): The parent Window.
            plugin (PrototypePlugin): The instance of the plugin.
        """
        self.plugin = plugin
        wx.Frame.__init__(self, parent=parent, title="Model Selection", size=(600, 200))

        self.optimizer = "adam"
        self.loss = "binary_crossentropy"
        self.metrics = "binary_crossentropy"

        self.control_elements()
        self.control_logic()
        self.layouting()

    def control_elements(self):
        """Loads all the GUI-Elements for the window"""
        self.send_button = wx.Button(parent=self, label="Select Model")

        self.optimizer_label = wx.StaticText(self, label="Optimizer")
        self.optimizer_text = wx.TextCtrl(self, value=self.optimizer)
        self.loss_label = wx.StaticText(self, label="Loss Function")
        self.loss_text = wx.TextCtrl(self, value=self.loss)
        self.metrics_label = wx.StaticText(self, label="Metrics (comma separated)")
        self.metrics_text = wx.TextCtrl(self, value=self.metrics)

    def control_logic(self):
        """Binds the Send Button to it's appropriate click-event: self.send_event"""
        self.send_button.Bind(wx.EVT_BUTTON, self.send_event)

    def layouting(self):
        """Layouts and aligns all the GUI-Elements in the model-selection window"""
        grid = wx.GridBagSizer(5, 5)
        grid.Add(
            self.optimizer_label,
            pos=(0, 0),
            flag=wx.TOP | wx.LEFT | wx.BOTTOM,
            border=10,
        )
        grid.Add(
            self.optimizer_text,
            pos=(0, 1),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=10,
        )
        grid.Add(
            self.loss_label, pos=(1, 0), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=10
        )
        grid.Add(
            self.loss_text, pos=(1, 1), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10
        )
        grid.Add(
            self.metrics_label, pos=(2, 0), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=10
        )
        grid.Add(
            self.metrics_text,
            pos=(2, 1),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=10,
        )
        grid.Add(
            self.send_button,
            pos=(3, 0),
            span=(1, 2),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5,
        )

        grid.AddGrowableCol(1)
        # haligner = wx.BoxSizer(wx.HORIZONTAL)
        valigner = wx.BoxSizer(wx.VERTICAL)
        valigner.Add((0, 0), 1)
        valigner.Add(grid, 0, wx.EXPAND)
        valigner.Add((0, 0), 2)
        self.SetSizer(valigner)
        # valigner.Add(self.porttxt, 1, wx.EXPAND)

    def load_model(self):
        """Opens the file explorer GUI to select the h5/json model
        returns the file contents, the model name and the filetype as string identifiers
        """
        dia = wx.FileDialog(
            self,
            "Select a model",
            wildcard="JSON Files, H5 Files (*.json;*.h5)|*.json;*.h5",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        model_str = ""
        model_name = ""
        model_kind = ""
        if dia.ShowModal() == wx.ID_OK:
            path = dia.GetPath()
            base = os.path.basename(path)
            model_name = os.path.splitext(base)[0]
            model_kind = os.path.splitext(base)[1][1:]
            if model_kind == "h5":
                with open(path, "rb") as f:
                    model_str = base64.b64encode(f.read()).decode("utf-8")
            else:
                with open(path, "r") as f:
                    model_str = f.read()
        dia.Close()
        return [model_str, model_name, model_kind]

    def send_event(self, event):
        """sends the models with all the necessary parameters to the active server"""
        # address = self.serverbox.GetValue()
        self.optimizer = self.optimizer_text.GetValue()
        self.loss = self.loss_text.GetValue()
        m_str = self.metrics_text.GetValue()
        self.metrics = [x.strip() for x in m_str.split(",")]
        self.metrics = [x for x in self.metrics if x]
        print(self.optimizer)
        print(self.loss)
        print(self.metrics)
        if not self.plugin.server_api.is_busy():
            model = self.load_model()
            if model[1] != "":
                dlg = None
                if model[2] == "h5":
                    dlg = wx.MessageDialog(
                        None,
                        'Selected H5 file, compile parameters will be ignored.\nSend model "'
                        + model[1]
                        + '" to server?',
                        "send_event",
                        wx.YES_NO | wx.ICON_QUESTION,
                    )
                else:
                    dlg = wx.MessageDialog(
                        None,
                        'Send model "'
                        + model[1]
                        + '" with compile parameters to server?',
                        "send_event",
                        wx.YES_NO | wx.ICON_QUESTION,
                    )
                result = dlg.ShowModal()
                print(model[1])
                print(model[2])
                if result == wx.ID_YES:
                    self.plugin.server_api.send_model(
                        model[0],
                        model[1],
                        model[2],
                        {
                            "optimizer": self.optimizer,
                            "loss": self.loss,
                            "metrics": self.metrics,
                            "loss_weights": None,
                            "sample_weight_mode": None,
                            "weighted_metrics": None,
                        },
                    )
                    self.Close()
        else:
            wx.MessageBox("Server not responding", "Warning", wx.OK | wx.ICON_WARNING)
