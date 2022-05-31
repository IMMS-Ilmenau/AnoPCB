"""Contains the PreferencesWindow used by the TrackGUI"""
import os
import wx
import wx.aui


class PreferencesWindow(wx.Frame):
    """This class implements the preferences window. Bound to the appropriate Plug-In Class,
    it can show and edit the preferences stored in a dictionary,
    that is maintained by the Anomaly-Plugin.
    """

    def __init__(self, parent, plugin):
        """Initializes the GUI.

        Args:
            parent (wx.Window): The parent Window.
            plugin (MainPlugin): The instance of the plugin.
        """
        self.plugin = plugin
        self.server_type_choice_texts = ["remote", "gpu", "cpu"]
        wx.Frame.__init__(self, parent=parent, title="Preferences", size=(700, 400))
        self.control_elements()
        self.control_logic()
        self.layouting()

    def control_elements(self):
        """Loads all the GUI-Elements for the preferences-window"""
        # alle GUI-Elemente
        prefs = self.load_prefs()

        self.menu_bar = wx.MenuBar()
        self.menu = wx.Menu()
        self.update_docker_item = self.menu.Append(
            wx.ID_ANY,
            item="update Docker",
            helpString="Remove and upgrade current docker configuration.",
        )

        self.menu_slices = wx.Menu()
        self.export_slices_item = self.menu_slices.Append(
            wx.ID_ANY,
            item="export slices",
            helpString="Exports slices for dataset usage.",
        )

        self.grid_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)

        self.server_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.port_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.filter_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.slice_x_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.slice_y_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.server_type_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)

        self.signal1_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.signal2_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.signal3_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.signal4_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.signal5_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.signal6_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.signal7_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.signal8_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)

        self.save_button = wx.Button(parent=self, label="Save")
        self.close_button = wx.Button(self.grid_panel, label="Close")
        self.serverlabel = wx.StaticText(self.server_panel, label=" Serveraddr.")
        self.portlabel = wx.StaticText(self.port_panel, label=" Port")
        self.serverbox = wx.TextCtrl(self.server_panel, value=str(prefs[0]))
        self.portbox = wx.TextCtrl(self.port_panel, value=str(prefs[1]))
        self.slice_x_label = wx.StaticText(self.slice_x_panel, label=" Slice X")
        self.slice_y_label = wx.StaticText(self.slice_y_panel, label=" Slice Y")
        self.slice_x_box = wx.TextCtrl(self.slice_x_panel, value=str(prefs[2]))
        self.slice_y_box = wx.TextCtrl(self.slice_y_panel, value=str(prefs[3]))
        self.server_type_label = wx.StaticText(
            self.server_type_panel, label=" Server Type"
        )
        self.server_type_choice = wx.Choice(
            self.server_type_panel, choices=self.server_type_choice_texts
        )
        self.save_filter_data_label = wx.StaticText(
            self.filter_panel, label="Save filter data locally?    "
        )
        self.save_filter_data_checkbox = wx.CheckBox(self.filter_panel)
        self.save_filter_data_checkbox.SetValue(prefs[5])
        self.empty_label = wx.StaticText(
            self, label=""
        )  # dont ask why its here, just accept that it is

        self.signal1_label = wx.StaticText(self.signal1_panel, label=" Signal 1:")
        self.signal1_box = wx.TextCtrl(self.signal1_panel, value=str(prefs[6]))
        self.signal2_label = wx.StaticText(self.signal2_panel, label=" Signal 2:")
        self.signal2_box = wx.TextCtrl(self.signal2_panel, value=str(prefs[7]))
        self.signal3_label = wx.StaticText(self.signal3_panel, label=" Signal 3:")
        self.signal3_box = wx.TextCtrl(self.signal3_panel, value=str(prefs[8]))
        self.signal4_label = wx.StaticText(self.signal4_panel, label=" Signal 4:")
        self.signal4_box = wx.TextCtrl(self.signal4_panel, value=str(prefs[9]))
        self.signal5_label = wx.StaticText(self.signal5_panel, label=" Signal 5:")
        self.signal5_box = wx.TextCtrl(self.signal5_panel, value=str(prefs[10]))
        self.signal6_label = wx.StaticText(self.signal6_panel, label=" Signal 6:")
        self.signal6_box = wx.TextCtrl(self.signal6_panel, value=str(prefs[11]))
        self.signal7_label = wx.StaticText(self.signal7_panel, label=" Signal 7:")
        self.signal7_box = wx.TextCtrl(self.signal7_panel, value=str(prefs[12]))
        self.signal8_label = wx.StaticText(self.signal8_panel, label=" Signal 8:")
        self.signal8_box = wx.TextCtrl(self.signal8_panel, value=str(prefs[13]))

        # TODO remove try/except later, when default values are always set, if values are missing
        try:
            self.server_type_choice.SetSelection(
                self.server_type_choice_texts.index(prefs[4])
            )
        except:
            self.server_type_choice.SetSelection(
                self.server_type_choice_texts.index("remote")
            )

    def control_logic(self):
        """Binds the Save Button to it's appropriate click-event: self.save_prefs"""
        self.save_button.Bind(wx.EVT_BUTTON, self.save_prefs)
        self.Bind(wx.EVT_MENU, self.remove_docker_container, self.update_docker_item)
        self.Bind(wx.EVT_MENU, self.export_slices, self.export_slices_item)
        self.close_button.Bind(wx.EVT_BUTTON, self.on_close)

    def layouting(self):
        """Layouts and aligns all the GUI-Elements in the preferences window"""

        self.menu_bar.Append(self.menu, "&Configuration")
        self.menu_bar.Append(self.menu_slices, "&Export")
        self.SetMenuBar(self.menu_bar)

        aligner = wx.BoxSizer(wx.VERTICAL)

        server_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        port_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        filter_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        slice_x_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        slice_y_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        server_type_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)

        signal1_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        signal2_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        signal3_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        signal4_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        signal5_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        signal6_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        signal7_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        signal8_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)

        server_horizontal_sizer.Add(self.serverlabel, 2, wx.ALIGN_CENTER_VERTICAL)
        server_horizontal_sizer.Add(self.serverbox, 5, wx.ALL | wx.EXPAND)
        port_horizontal_sizer.Add(self.portlabel, 2, wx.ALIGN_CENTER_VERTICAL)
        port_horizontal_sizer.Add(self.portbox, 5, wx.ALL | wx.EXPAND)
        filter_horizontal_sizer.Add(
            self.save_filter_data_label, 2, wx.ALIGN_CENTER_VERTICAL
        )
        filter_horizontal_sizer.Add(
            self.save_filter_data_checkbox, 5, wx.ALL | wx.EXPAND
        )
        slice_x_horizontal_sizer.Add(self.slice_x_label, 2, wx.ALIGN_CENTER_VERTICAL)
        slice_x_horizontal_sizer.Add(self.slice_x_box, 5, wx.ALL | wx.EXPAND)
        slice_y_horizontal_sizer.Add(self.slice_y_label, 2, wx.ALIGN_CENTER_VERTICAL)
        slice_y_horizontal_sizer.Add(self.slice_y_box, 5, wx.ALL | wx.EXPAND)
        server_type_horizontal_sizer.Add(
            self.server_type_label, 2, wx.ALIGN_CENTER_VERTICAL
        )
        server_type_horizontal_sizer.Add(self.server_type_choice, 5, wx.ALL | wx.EXPAND)

        signal1_horizontal_sizer.Add(self.signal1_label, 2, wx.ALIGN_CENTER_VERTICAL)
        signal1_horizontal_sizer.Add(self.signal1_box, 5, wx.ALL | wx.EXPAND)
        signal2_horizontal_sizer.Add(self.signal2_label, 2, wx.ALIGN_CENTER_VERTICAL)
        signal2_horizontal_sizer.Add(self.signal2_box, 5, wx.ALL | wx.EXPAND)
        signal3_horizontal_sizer.Add(self.signal3_label, 2, wx.ALIGN_CENTER_VERTICAL)
        signal3_horizontal_sizer.Add(self.signal3_box, 5, wx.ALL | wx.EXPAND)
        signal4_horizontal_sizer.Add(self.signal4_label, 2, wx.ALIGN_CENTER_VERTICAL)
        signal4_horizontal_sizer.Add(self.signal4_box, 5, wx.ALL | wx.EXPAND)
        signal5_horizontal_sizer.Add(self.signal5_label, 2, wx.ALIGN_CENTER_VERTICAL)
        signal5_horizontal_sizer.Add(self.signal5_box, 5, wx.ALL | wx.EXPAND)
        signal6_horizontal_sizer.Add(self.signal6_label, 2, wx.ALIGN_CENTER_VERTICAL)
        signal6_horizontal_sizer.Add(self.signal6_box, 5, wx.ALL | wx.EXPAND)
        signal7_horizontal_sizer.Add(self.signal7_label, 2, wx.ALIGN_CENTER_VERTICAL)
        signal7_horizontal_sizer.Add(self.signal7_box, 5, wx.ALL | wx.EXPAND)
        signal8_horizontal_sizer.Add(self.signal8_label, 2, wx.ALIGN_CENTER_VERTICAL)
        signal8_horizontal_sizer.Add(self.signal8_box, 5, wx.ALL | wx.EXPAND)

        self.server_panel.SetSizer(server_horizontal_sizer)
        self.port_panel.SetSizer(port_horizontal_sizer)
        self.filter_panel.SetSizer(filter_horizontal_sizer)
        self.slice_x_panel.SetSizer(slice_x_horizontal_sizer)
        self.slice_y_panel.SetSizer(slice_y_horizontal_sizer)
        self.server_type_panel.SetSizer(server_type_horizontal_sizer)

        self.signal1_panel.SetSizer(signal1_horizontal_sizer)
        self.signal2_panel.SetSizer(signal2_horizontal_sizer)
        self.signal3_panel.SetSizer(signal3_horizontal_sizer)
        self.signal4_panel.SetSizer(signal4_horizontal_sizer)
        self.signal5_panel.SetSizer(signal5_horizontal_sizer)
        self.signal6_panel.SetSizer(signal6_horizontal_sizer)
        self.signal7_panel.SetSizer(signal7_horizontal_sizer)
        self.signal8_panel.SetSizer(signal8_horizontal_sizer)

        grid = wx.GridSizer(2, 5, 5)
        grid.Add(self.server_panel, 5, wx.EXPAND)
        grid.Add(self.port_panel, 5, wx.EXPAND)
        grid.Add(self.slice_x_panel, 5, wx.EXPAND)
        grid.Add(self.slice_y_panel, 5, wx.EXPAND)
        grid.Add(self.server_type_panel, 5, wx.EXPAND)
        grid.Add(self.filter_panel, 5, wx.EXPAND)

        grid.Add(self.empty_label, 5, wx.EXPAND)
        grid.Add(self.empty_label, 5, wx.EXPAND)

        grid.Add(self.signal1_panel, 5, wx.EXPAND)
        grid.Add(self.signal2_panel, 5, wx.EXPAND)
        grid.Add(self.signal3_panel, 5, wx.EXPAND)
        grid.Add(self.signal4_panel, 5, wx.EXPAND)
        grid.Add(self.signal5_panel, 5, wx.EXPAND)
        grid.Add(self.signal6_panel, 5, wx.EXPAND)
        grid.Add(self.signal7_panel, 5, wx.EXPAND)
        grid.Add(self.signal8_panel, 5, wx.EXPAND)

        grid.Add(self.save_button, 5, wx.EXPAND)
        grid.Add(self.close_button, 5, wx.EXPAND)

        self.grid_panel.SetSizer(grid)
        aligner.Add(self.grid_panel, 5, wx.ALL | wx.EXPAND)

        self.SetSizer(aligner)
        self.Centre()

    def remove_docker_container(self, event):
        """Tries to stop the currently active docker server."""
        self.plugin.remove_docker_container()

    def export_slices(self, event):
        self.plugin.export_slices(self)

    def load_prefs(self):
        """Loads the preferences from the Main Plug-In,
        to be shown in the preference-windows edit labels
        """
        # self.plugin.set_preference()
        serveradd = self.plugin.get_preference("server_address")
        serverport = self.plugin.get_preference("server_port")
        slicex = self.plugin.get_preference("slice_x")
        slicey = self.plugin.get_preference("slice_y")
        server_type = self.plugin.get_preference("server_type")
        save_filter_data = self.plugin.get_preference("save_filter_data")

        signal1 = self.plugin.get_preference("signal1")
        signal2 = self.plugin.get_preference("signal2")
        signal3 = self.plugin.get_preference("signal3")
        signal4 = self.plugin.get_preference("signal4")
        signal5 = self.plugin.get_preference("signal5")
        signal6 = self.plugin.get_preference("signal6")
        signal7 = self.plugin.get_preference("signal7")
        signal8 = self.plugin.get_preference("signal8")
        # tuple #not anymore
        return [
            serveradd,
            serverport,
            slicex,
            slicey,
            server_type,
            save_filter_data,
            signal1,
            signal2,
            signal3,
            signal4,
            signal5,
            signal6,
            signal7,
            signal8,
        ]

    def save_prefs(self, event):
        """Saves the preferences (for instance Server address/port, slice dimensions, etc.)"""
        address = self.serverbox.GetValue()
        port = self.portbox.GetValue()
        x_dim = self.slice_x_box.GetValue()
        y_dim = self.slice_y_box.GetValue()
        server_type = self.server_type_choice_texts[
            self.server_type_choice.GetSelection()
        ]
        save_filter_data = self.save_filter_data_checkbox.GetValue()

        signal1 = self.signal1_box.GetValue()
        signal2 = self.signal2_box.GetValue()
        signal3 = self.signal3_box.GetValue()
        signal4 = self.signal4_box.GetValue()
        signal5 = self.signal5_box.GetValue()
        signal6 = self.signal6_box.GetValue()
        signal7 = self.signal7_box.GetValue()
        signal8 = self.signal8_box.GetValue()

        new_signals = [
            signal1,
            signal2,
            signal3,
            signal4,
            signal5,
            signal6,
            signal7,
            signal8,
        ]
        while "None" in new_signals:
            new_signals.remove("None")

        if len(new_signals) > len(list(dict.fromkeys(new_signals))):
            wx.MessageBox(
                "No double names allowed (except None)", "Error", wx.OK | wx.ICON_ERROR
            )
            return

        if signal1 in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:
            wx.MessageBox(
                "Signal 1 has a blocked value", "Error", wx.OK | wx.ICON_ERROR
            )
            signal1 = self.plugin.get_preference("signal1")
            self.signal1_box.SetValue(signal1)
            return

        if signal2 in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:
            wx.MessageBox(
                "Signal 2 has a blocked value", "Error", wx.OK | wx.ICON_ERROR
            )
            signal2 = self.plugin.get_preference("signal2")
            self.signal2_box.SetValue(signal2)
            return

        if signal3 in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:
            wx.MessageBox(
                "Signal 3 has a blocked value", "Error", wx.OK | wx.ICON_ERROR
            )
            signal3 = self.plugin.get_preference("signal3")
            self.signal3_box.SetValue(signal3)
            return

        if signal4 in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:
            wx.MessageBox(
                "Signal 4 has a blocked value", "Error", wx.OK | wx.ICON_ERROR
            )
            signal4 = self.plugin.get_preference("signal4")
            self.signal4_box.SetValue(signal4)
            return

        if signal5 in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:
            wx.MessageBox(
                "Signal 5 has a blocked value", "Error", wx.OK | wx.ICON_ERROR
            )
            signal5 = self.plugin.get_preference("signal5")
            self.signal5_box.SetValue(signal5)
            return

        if signal6 in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:
            wx.MessageBox(
                "Signal 6 has a blocked value", "Error", wx.OK | wx.ICON_ERROR
            )
            signal6 = self.plugin.get_preference("signal6")
            self.signal6_box.SetValue(str(signal6))
            return

        if signal7 in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:
            wx.MessageBox(
                "Signal 7 has a blocked value", "Error", wx.OK | wx.ICON_ERROR
            )
            signal7 = self.plugin.get_preference("signal7")
            self.signal7_box.SetValue(str(signal7))
            return

        if signal8 in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:
            wx.MessageBox(
                "Signal 8 has a blocked value", "Error", wx.OK | wx.ICON_ERROR
            )
            signal7 = self.plugin.get_preference("signal8")
            self.signal8_box.SetValue(str(signal8))
            return

        if server_type != "remote" and os.system("which docker") == 256:
            wx.MessageBox(
                "Docker not installed, install or use remote server instead!",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        if x_dim.isdigit() and y_dim.isdigit() and port.isdigit():
            if int(port) >= 2**16:
                wx.MessageBox(
                    "Invalid Port number. Port must be < 65536!",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
            elif int(x_dim) == 0 or int(y_dim) == 0:
                wx.MessageBox("X and Y may not be 0!", "Error", wx.OK | wx.ICON_ERROR)
            else:
                self.plugin.set_preference("server_address", address)
                self.plugin.set_preference("server_port", int(port))
                self.plugin.set_preference("slice_x", int(x_dim))
                self.plugin.set_preference("slice_y", int(y_dim))
                self.plugin.set_preference("server_type", server_type)
                self.plugin.set_preference("save_filter_data", save_filter_data)

                self.plugin.set_preference("signal1", signal1)
                self.plugin.set_preference("signal2", signal2)
                self.plugin.set_preference("signal3", signal3)
                self.plugin.set_preference("signal4", signal4)
                self.plugin.set_preference("signal5", signal5)
                self.plugin.set_preference("signal6", signal6)
                self.plugin.set_preference("signal7", signal7)
                self.plugin.set_preference("signal8", signal8)

                self.Close()
        else:
            wx.MessageBox(
                "Port, X and Y must be numeric values (nonnegative integers)!",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

    def on_close(self, event):
        """Called by the "Close" button."""
        self.Close()
