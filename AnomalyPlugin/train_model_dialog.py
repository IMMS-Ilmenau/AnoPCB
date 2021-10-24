"""Contains the TrainModelDialog used by the TrackGUI"""
import re
import time
import wx
import wx.aui
import pcbnew
import json
from AnomalyPlugin.training_results_dialog import ResultDialog


class TrainModelDialog(wx.Frame):
    """The dialog used to send datasets from the current PCB to the server and
     to train and evaluate the models on them. For further reference
     check out the guide (ML-Guide.txt).
    """

    def __init__(self, parent, plugin):
        """Initializes the GUI.

        Args:
            parent (wx.Window): The parent Window.
            plugin (MainPlugin): The instance of the plugin.
        """
        wx.Frame.__init__(self, parent, size=(637, 442))
        self.plugin = plugin
        self.datasets = self.get_data()
        self.active_model, self.input_shape = self.get_active_model()
        self.augment = False

        self.control_elements()
        self.update_data()
        self.control_logic()
        self.layouting()


    def control_elements(self):
        """Loads all the GUI-Elements for the train model dialog.
        """
        self.menu_bar = wx.MenuBar()
        self.menu = wx.Menu()
        self.import_slices_item = self.menu.Append(
            wx.ID_ANY,
            item="import slices",
            helpString="Import slices from a file and upload them.")

        self.train_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.val_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.test_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.duration_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.model_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.button_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.data_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.train_sizer = wx.BoxSizer(wx.VERTICAL)
        self.val_sizer = wx.BoxSizer(wx.VERTICAL)
        self.test_sizer = wx.BoxSizer(wx.VERTICAL)
        self.count_sizer_train = wx.GridBagSizer(1, 2)
        self.count_sizer_val = wx.GridBagSizer(1, 2)
        self.count_sizer_test = wx.GridBagSizer(1, 2)
        self.middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.input_sizer = wx.GridBagSizer(2, 2)
        self.text_sizer = wx.GridBagSizer(2, 1)
        self.button_sizer = wx.GridBagSizer(3, 2)

        self.train_data_ctrl = wx.ListCtrl(self.train_panel, -1, style=wx.LC_REPORT)
        self.val_data_ctrl = wx.ListCtrl(self.val_panel, -1, style=wx.LC_REPORT)
        self.test_data_ctrl = wx.ListCtrl(self.test_panel, -1, style=wx.LC_REPORT)
        self.count_text1 = wx.StaticText(self.train_panel, label="Batch Size:")
        self.count_text2 = wx.StaticText(self.val_panel, label="Batch Size:")
        self.count_text3 = wx.StaticText(self.test_panel, label="Batch Size:")
        self.count_ctrl_train = wx.TextCtrl(self.train_panel, value="0")
        self.count_ctrl_val = wx.TextCtrl(self.val_panel, value="0")
        self.count_ctrl_test = wx.TextCtrl(self.test_panel, value="0")
        self.duration_text1 = wx.StaticText(
            self.duration_panel,
            label="Maximum training time (min): ")
        self.duration_text2 = wx.StaticText(
            self.duration_panel,
            label="Maximum training (epochs): ")
        self.duration_ctrl1 = wx.TextCtrl(self.duration_panel, value="60")
        self.duration_ctrl2 = wx.TextCtrl(self.duration_panel, value="0")
        self.active_model_text = wx.StaticText(
            self.model_panel,
            label="Active model: " + str(self.active_model))
        self.model_input_text = wx.StaticText(
            self.model_panel,
            label="Model Input: " + self.input_shape)
        self.train_button = wx.Button(self.button_panel, 1, "Train Model")
        self.test_button = wx.Button(self.button_panel, 5, "Test Model")
        self.close_button = wx.Button(self.button_panel, 2, "Close")
        self.send_button = wx.Button(self.button_panel, 3, "Send slices")
        self.delete_button = wx.Button(self.button_panel, 4, "Delete slices")
        self.augment_button = wx.ToggleButton(self.button_panel, 6, "Augment OFF")


    def control_logic(self):
        """Binds the elements to their logic.
        """
        self.Bind(wx.EVT_BUTTON, self.on_train, id=1)
        self.Bind(wx.EVT_BUTTON, self.on_close, id=2)
        self.Bind(wx.EVT_BUTTON, self.on_send, id=3)
        self.Bind(wx.EVT_BUTTON, self.on_delete, id=4)
        self.Bind(wx.EVT_BUTTON, self.on_test, id=5)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_augment, id=6)
        self.Bind(wx.EVT_MENU, self.import_slices, self.import_slices_item)


    def layouting(self):
        """Layouts and aligns all the GUI-Elements in the configure model dialog.
        """
        self.menu_bar.Append(self.menu, "&Import")
        self.SetMenuBar(self.menu_bar)

        self.count_sizer_train.Add(
            self.count_text1,
            pos=(0, 0),
            flag=wx.TOP | wx.BOTTOM,
            border=5)
        self.count_sizer_train.Add(
            self.count_ctrl_train,
            pos=(0, 1),
            flag=wx.EXPAND | wx.RIGHT | wx.LEFT,
            border=5)
        self.count_sizer_train.AddGrowableCol(1)

        self.count_sizer_val.Add(
            self.count_text2, 
            pos=(0, 0),
            flag=wx.TOP | wx.BOTTOM,
            border=5)
        self.count_sizer_val.Add(
            self.count_ctrl_val,
            pos=(0, 1),
            flag=wx.EXPAND | wx.RIGHT | wx.LEFT,
            border=5)
        self.count_sizer_val.AddGrowableCol(1)

        self.count_sizer_test.Add(
            self.count_text3,
            pos=(0, 0),
            flag=wx.TOP | wx.BOTTOM,
            border=5)
        self.count_sizer_test.Add(
            self.count_ctrl_test,
            pos=(0, 1),
            flag=wx.EXPAND | wx.RIGHT | wx.LEFT,
            border=5)
        self.count_sizer_test.AddGrowableCol(1)

        self.train_sizer.Add(
            self.train_data_ctrl,
            0,
            flag=wx.ALL | wx.EXPAND,
            border=5)
        self.val_sizer.Add(
            self.val_data_ctrl,
            0,
            flag=wx.ALL | wx.EXPAND,
            border=5)
        self.test_sizer.Add(
            self.test_data_ctrl,
            0,
            flag=wx.ALL | wx.EXPAND,
            border=5)
        self.train_sizer.Add(
            self.count_sizer_train,
            0,
            flag=wx.BOTTOM | wx.LEFT | wx.EXPAND,
            border=5)
        self.val_sizer.Add(
            self.count_sizer_val,
            0,
            flag=wx.BOTTOM | wx.LEFT | wx.EXPAND,
            border=5)
        self.test_sizer.Add(
            self.count_sizer_test,
            0,
            flag=wx.BOTTOM | wx.LEFT | wx.EXPAND,
            border=5)

        self.train_panel.SetSizer(self.train_sizer)
        self.val_panel.SetSizer(self.val_sizer)
        self.test_panel.SetSizer(self.test_sizer)
        self.data_sizer.Add(self.train_panel)
        self.data_sizer.Add(self.val_panel)
        self.data_sizer.Add(self.test_panel)

        self.input_sizer.Add(
            self.duration_text1,
            pos=(0, 0),
            flag=wx.ALIGN_CENTRE_VERTICAL | wx.TOP | wx.LEFT,
            border=5)
        self.input_sizer.Add(
            self.duration_text2,
            pos=(1, 0),
            flag=wx.ALIGN_CENTRE_VERTICAL | wx.BOTTOM | wx.LEFT,
            border=5)
        self.input_sizer.Add(
            self.duration_ctrl1,
            pos=(0, 1),
            flag=wx.TOP | wx.RIGHT | wx.EXPAND,
            border=5)
        self.input_sizer.Add(
            self.duration_ctrl2,
            pos=(1, 1),
            flag=wx.BOTTOM | wx.RIGHT | wx.EXPAND,
            border=5)
        self.input_sizer.AddGrowableCol(1)
        self.duration_panel.SetSizer(self.input_sizer)

        self.text_sizer.Add(
            self.active_model_text,
            pos=(0, 0),
            flag=wx.TOP | wx.LEFT | wx.ALIGN_CENTRE_VERTICAL,
            border=5)
        self.text_sizer.Add(
            self.model_input_text,
            pos=(1, 0),
            flag=wx.BOTTOM | wx.LEFT | wx.ALIGN_CENTRE_VERTICAL,
            border=5)
        self.text_sizer.AddGrowableRow(0)
        self.text_sizer.AddGrowableRow(1)
        self.model_panel.SetSizer(self.text_sizer)

        self.button_sizer.Add(
            self.train_button,
            pos=(0, 0),
            flag=wx.EXPAND)
        self.button_sizer.Add(
            self.test_button,
            pos=(1, 0),
            flag=wx.EXPAND)
        self.button_sizer.Add(
            self.send_button,
            pos=(0, 1),
            flag=wx.EXPAND)
        self.button_sizer.Add(
            self.delete_button,
            pos=(1, 1),
            flag=wx.EXPAND)
        self.button_sizer.Add(
            self.close_button,
            pos=(1, 2),
            flag=wx.EXPAND)
        self.button_sizer.Add(
            self.augment_button,
            pos=(0, 2),
            flag=wx.EXPAND)
        self.button_sizer.AddGrowableCol(0)
        self.button_sizer.AddGrowableCol(1)
        self.button_sizer.AddGrowableCol(2)
        self.button_panel.SetSizer(self.button_sizer)

        self.middle_sizer.Add(
            self.duration_panel,
            1,
            flag=wx.EXPAND)
        self.middle_sizer.Add(
            self.model_panel,
            1,
            flag=wx.EXPAND)

        self.main_sizer.Add(self.data_sizer)
        self.main_sizer.Add(
            self.middle_sizer,
            flag=wx.EXPAND)
        self.main_sizer.Add(
            self.button_panel,
            flag=wx.EXPAND)
        self.SetSizer(self.main_sizer)
        self.Centre()


    def update_data(self):
        """Updates the available datasets.
        """
        self.train_data_ctrl.ClearAll()
        self.train_data_ctrl.InsertColumn(0, "Datasets for training")
        self.train_data_ctrl.SetColumnWidth(0, 200)
        [self.train_data_ctrl.InsertItem(0, item) for item in self.datasets]
        self.val_data_ctrl.ClearAll()
        self.val_data_ctrl.InsertColumn(0, "Datasets for validation")
        self.val_data_ctrl.SetColumnWidth(0, 200)
        [self.val_data_ctrl.InsertItem(0, item) for item in self.datasets]
        self.test_data_ctrl.ClearAll()
        self.test_data_ctrl.InsertColumn(0, "Datasets for testing")
        self.test_data_ctrl.SetColumnWidth(0, 200)
        [self.test_data_ctrl.InsertItem(0, item) for item in self.datasets]


    def get_data(self):
        """Queries the server for all available datasets.
        """
        if not self.plugin.server_api.is_busy():
            return self.plugin.server_api.get_datasets()["data"]
        else:
            wx.MessageBox(
                "Server not available.",
                'Error',
                wx.OK | wx.ICON_ERROR)
            self.Close()

    def import_slices(self, evt):
        with wx.FileDialog(
                self,
                "Import slices",
                wildcard="JSON file (*.json)|*.json",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = str(file_dialog.GetPath())
        
        with open(pathname, 'r') as json_file:
            data = json.load(json_file)

        send_slices = data['send_slices']
        slice_count = int(data['slice_count'])
        x_dim = int(data['x_dim'])
        y_dim = int(data['y_dim'])
        name = data['name']

        while self.plugin.server_api.is_busy():
            dia = wx.MessageDialog(
                parent=self,
                message="The server can't be reached, is not listening on the chosen port or busy. Wait 10 seconds?",
                caption="Server not responding",
                style=wx.OK | wx.CANCEL | wx.OK_DEFAULT)
            if dia.ShowModal() == wx.ID_OK:
                time.sleep(10)
            else:
                return

        resp = self.plugin.server_api.send_slices(
            send_slices,
            name,
            slice_count,
            x_dim,
            y_dim,
            self.augment)
        if resp == False:
            wx.MessageBox(
                "Sending Dataset to the server failed.",
                'Error',
                wx.OK | wx.ICON_ERROR)
        else:
            self.datasets = self.get_data()
            self.update_data()

    def on_train(self, evt):
        """Called by the "Train model" button. Trains and validates the currently
         active model on the selected datasets. Datasets for training and validation
         must be either the same or disjointed. The batchsizes determine how many slices
         from the selected datasets will be used.
         For further reference check out the guide (ML-Guide.txt).

        Args:
            evt (wx.EVENT): unused
        """
        index = self.train_data_ctrl.GetFirstSelected()
        train_datasets = []
        if index < 0:
            wx.MessageBox(
                "Must select a dataset from the datasets for training first.",
                'Error',
                wx.OK | wx.ICON_ERROR)
            return
        else:
            while index >= 0:
                train_datasets.append(self.train_data_ctrl.GetItemText(index))
                index = self.train_data_ctrl.GetNextSelected(index)

        index = self.val_data_ctrl.GetFirstSelected()
        val_datasets = []
        if index < 0:
            wx.MessageBox(
                "Must select a dataset from the datasets for validation first.",
                'Error',
                wx.OK | wx.ICON_ERROR)
            return
        else:
            while index >= 0:
                val_datasets.append(self.val_data_ctrl.GetItemText(index))
                index = self.val_data_ctrl.GetNextSelected(index)

        if val_datasets != train_datasets:
            for name in val_datasets:
                if name in train_datasets:
                    wx.MessageBox(
                        "Datasets for validation and training must be the same or disjoint.",
                        'Error',
                        wx.OK | wx.ICON_ERROR)
                    return

        train_batch_size = self.count_ctrl_train.GetValue()
        val_batch_size = self.count_ctrl_val.GetValue()
        if not (train_batch_size.isnumeric() and val_batch_size.isnumeric()):
            wx.MessageBox(
                "Batch size must be an integer.",
                'Error',
                wx.OK | wx.ICON_ERROR)
            return
        train_time_min = self.duration_ctrl1.GetValue()
        train_time_epochs = self.duration_ctrl2.GetValue()
        if not (train_time_min.isnumeric() and train_time_epochs.isnumeric()):
            wx.MessageBox(
                "Training time must be an integer.",
                'Error',
                wx.OK | wx.ICON_ERROR)
            return

        resp = self.plugin.server_api.new_train(
            (train_datasets, val_datasets),
            (int(train_batch_size), int(val_batch_size)),
            (int(train_time_min), int(train_time_epochs)))
        if not resp is False:
            dia = ResultDialog(self, resp)
            dia.Show()


    def on_test(self, evt):
        """Called by the "Test Model" button. Sends a list of dataset names and a batch-size
         to the server. The currently active model will be evaluated on "batch_size"
         samples taken from the selected datasets.

        Args:
            evt (wx.EVENT): unused
        """
        index = self.test_data_ctrl.GetFirstSelected()
        if index < 0:
            wx.MessageBox(
                "Must select a dataset from the datasets for testing first.",
                'Error',
                wx.OK | wx.ICON_ERROR)
        else:
            datasets = []
            while index >= 0:
                datasets.append(self.test_data_ctrl.GetItemText(index))
                index = self.test_data_ctrl.GetNextSelected(index)
            batch_size = self.count_ctrl_test.GetValue()
            if not batch_size.isnumeric():
                wx.MessageBox(
                    "Batch size must be an integer.",
                    'Error',
                    wx.OK | wx.ICON_ERROR)
            else:
                resp = self.plugin.server_api.test(datasets, int(batch_size))
                if not resp is False:
                    wx.MessageBox(f"Test loss: {resp['data']}")
                else:
                    wx.MessageBox(
                        "Error during testing.",
                        'Error',
                        wx.OK | wx.ICON_ERROR)


    def on_augment(self, evt):
        """Called by the "Augment ON/OFF" button. Sets the "augment" flag,
         that decides whether sent slices should be augmented.

        Args:
            evt (wx.EVENT): unused
        """
        if self.augment is False:
            self.augment = True
            self.augment_button.SetLabel("Augment ON")
        else:
            self.augment = False
            self.augment_button.SetLabel("Augment OFF")


    def on_send(self, evt):
        """Called by the "Send slices" button. Sends a dataset of slices
         taken from the current board to the server.

        Args:
            evt (wx.EVENT): unused
        """
        dia = wx.MessageDialog(
            parent=self,
            message="This may take 5 minutes or longer. Continue?",
            caption="Are you sure?",
            style=wx.OK | wx.CANCEL | wx.CANCEL_DEFAULT)
        if not dia.ShowModal() == wx.ID_OK:
            return

        slices = self.plugin.create_slices_mp()
        slices = slices[1]
        send_slices = [y.decode("utf-8") for x, y in slices] # x is metadata (e.g. position), y is slice in bytes
        slice_count = str(len(send_slices))
        x_dim = str(self.plugin.get_preference("slice_x"))
        y_dim = str(self.plugin.get_preference("slice_y"))
        board = pcbnew.GetBoard()
        filename = board.GetFileName()
        name = re.search(r'[^\/]*\.kicad_pcb', filename).group(0)[:-10]

        while self.plugin.server_api.is_busy():
            dia = wx.MessageDialog(
                parent=self,
                message="The server can't be reached, is not listening on the chosen port or busy. Wait 10 seconds?",
                caption="Server not responding",
                style=wx.OK | wx.CANCEL | wx.OK_DEFAULT)
            if dia.ShowModal() == wx.ID_OK:
                time.sleep(10)
            else:
                return

        resp = self.plugin.server_api.send_slices(
            send_slices,
            name,
            slice_count,
            x_dim,
            y_dim,
            self.augment)
        if resp == False:
            wx.MessageBox(
                "Sending Dataset to the server failed.",
                'Error',
                wx.OK | wx.ICON_ERROR)
        else:
            self.datasets = self.get_data()
            self.update_data()


    def on_delete(self, evt):
        """Instructs the server to delete the dataset selected in the train_data_ctrl list.

        Args:
            evt (wx.EVENT): unused
        """
        index = self.train_data_ctrl.GetFirstSelected()
        if index < 0:
            wx.MessageBox(
                "Must select a dataset from the datasets for training first.",
                'Error',
                wx.OK | wx.ICON_ERROR)
        else:
            name = self.train_data_ctrl.GetItemText(index)
            dia = wx.MessageDialog(
                parent=self,
                message=f"This will delete the {name} dataset for ever! Continue?",
                caption="WARNING!",
                style=wx.OK | wx.CANCEL | wx.OK_DEFAULT)
            if  not dia.ShowModal() == wx.ID_OK:
                return
            else:
                resp = self.plugin.server_api.delete_slices(name)
                if not resp:
                    wx.MessageBox(
                        "Couldnt delete dataset.",
                        'Error',
                        wx.OK | wx.ICON_ERROR)
                else:
                    self.datasets = self.get_data()
                    self.update_data()


    def on_close(self, evt):
        """ Called by the "Close" button.

        Args:
            evt (wx.EVENT): unused
        """
        self.Close()


    def get_active_model(self):
        """Queries the server for the currently active model.

        Returns:
            list: A list of names (strings).
        """
        if not self.plugin.server_api.is_busy():
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
            return (ac_model, inp_shape)
        else:
            wx.MessageBox(
                "Server not available.",
                'Error',
                wx.OK | wx.ICON_ERROR)
            self.Close()
            return ("", "")
