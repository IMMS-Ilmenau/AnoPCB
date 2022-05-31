"""Contains the RegexDialog used by the TrackGUI"""
import pcbnew
import wx
import wx.aui
from AnomalyPlugin.netlist_dialog import NetlistDialog


class RegexDialog(wx.Frame):
    """The dialog for annotating the board via RegExes."""

    def __init__(self, parent, plugin):
        """Initializes the GUI.

        Args:
            idnr (int): The id of the Dialog.
            parent (wx.Window): The parent Window.
            plugin (MainPlugin): The instance of the plugin.
        """

        self.plugin = plugin
        wx.Frame.__init__(self, parent=parent, title="RegEx", size=(600, 400))

        self.control_elements()
        self.control_logic()
        self.layouting()

        dat = self.plugin.get_user_regex_tuples()
        possible_signals = self.get_signals_list()
        for i in dat:
            num_items = self.regex_list.GetItemCount()
            self.regex_list.InsertItem(num_items, i[0])
            self.regex_list.SetItem(num_items, 1, possible_signals[int(i[1]) - 1])

    def control_elements(self):
        """Loads all the GUI-Elements for the regex dialog."""

        self.grid_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)

        self.component_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.signal_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)

        self.add_button = wx.Button(self.grid_panel, label="Add")
        self.remove_button = wx.Button(self.grid_panel, label="Remove")
        self.clear_button = wx.Button(self.grid_panel, label="Clear")
        self.close_button = wx.Button(self.grid_panel, label="Close")
        self.annotate_button = wx.Button(self.grid_panel, label="Annotate")
        self.netlist_button = wx.Button(self.grid_panel, label="Netlist")
        self.regex_list = wx.ListCtrl(self, -1, style=wx.LC_REPORT)
        self.component_label = wx.StaticText(self.component_panel, label=" Component")
        self.signal_label = wx.StaticText(self.signal_panel, label=" Signal")
        self.component_box = wx.TextCtrl(self.component_panel, value="")
        self.signal_box = wx.TextCtrl(self.signal_panel, value="")
        self.text = wx.TextCtrl(self, style=wx.TE_READONLY)

    def control_logic(self):
        """Binds the elements to their logic."""
        self.add_button.Bind(wx.EVT_BUTTON, self.on_add)
        self.remove_button.Bind(wx.EVT_BUTTON, self.on_remove)
        self.clear_button.Bind(wx.EVT_BUTTON, self.on_clear)
        self.close_button.Bind(wx.EVT_BUTTON, self.on_close)
        self.annotate_button.Bind(wx.EVT_BUTTON, self.on_annotate)
        self.netlist_button.Bind(wx.EVT_BUTTON, self.on_netlist)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_lc_selected, id=-1)

    def layouting(self):
        """Layouts and aligns all the GUI-Elements in the regex dialog."""
        aligner = wx.BoxSizer(wx.VERTICAL)

        self.regex_list.InsertColumn(0, "Component")
        self.regex_list.InsertColumn(1, "Signal")
        self.regex_list.SetColumnWidth(0, 300)
        self.regex_list.SetColumnWidth(1, 300)

        aligner.Add(self.regex_list, 5, wx.ALL | wx.EXPAND)
        aligner.Add(self.text, 1, wx.ALL | wx.EXPAND)

        component_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        signal_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)

        component_horizontal_sizer.Add(
            self.component_label, 2, wx.ALIGN_CENTER_VERTICAL
        )
        component_horizontal_sizer.Add(self.component_box, 5, wx.ALL | wx.EXPAND)
        signal_horizontal_sizer.Add(self.signal_label, 2, wx.ALIGN_CENTER_VERTICAL)
        signal_horizontal_sizer.Add(self.signal_box, 5, wx.ALL | wx.EXPAND)

        self.component_panel.SetSizer(component_horizontal_sizer)
        self.signal_panel.SetSizer(signal_horizontal_sizer)

        grid = wx.GridSizer(2, 5, 5)
        grid.Add(self.component_panel, 5, wx.EXPAND)
        grid.Add(self.signal_panel, 5, wx.EXPAND)
        grid.Add(self.add_button, 5, wx.EXPAND)
        grid.Add(self.remove_button, 5, wx.EXPAND)
        grid.Add(self.annotate_button, 5, wx.EXPAND)
        grid.Add(self.netlist_button, 5, wx.EXPAND)
        grid.Add(self.clear_button, 5, wx.EXPAND)
        grid.Add(self.close_button, 5, wx.EXPAND)

        self.grid_panel.SetSizer(grid)
        aligner.Add(self.grid_panel, 4, wx.ALL | wx.EXPAND)

        self.SetSizer(aligner)
        self.Centre()

    def get_signals_list(self):
        """Loads the preferences for the Signals 1-8 and returns a list containing them."""
        signal1 = self.plugin.get_preference("signal1")
        signal2 = self.plugin.get_preference("signal2")
        signal3 = self.plugin.get_preference("signal3")
        signal4 = self.plugin.get_preference("signal4")
        signal5 = self.plugin.get_preference("signal5")
        signal6 = self.plugin.get_preference("signal6")
        signal7 = self.plugin.get_preference("signal7")
        signal8 = self.plugin.get_preference("signal8")

        possible_signals = [
            signal1,
            signal2,
            signal3,
            signal4,
            signal5,
            signal6,
            signal7,
            signal8,
        ]

        return possible_signals

    def on_netlist(self, evt):
        """Called when the netlist button is pressed.

        Args:
            evt (wx.EVENT): Unused.
        """
        dia = NetlistDialog(self, self.plugin)
        dia.Show(True)

    def on_lc_selected(self, event):
        """Shows the currently selected Component.

        Args:
            evt (wx.EVENT): Unused.
        """

        possible_signals = self.get_signals_list()
        self.text.Clear()
        item0 = self.regex_list.GetItem(self.regex_list.GetFocusedItem(), 0).GetText()
        item1 = self.regex_list.GetItem(self.regex_list.GetFocusedItem(), 1).GetText()
        if item1 in possible_signals:
            item1 = str(possible_signals.index(item1) + 1)
        self.text.AppendText(item0 + " -> " + item1)

    def on_add(self, event):
        """Called by the 'Add' button. Adds the entered RegEx - Signal pair.

        Args:
            evt (wx.EVENT): Unused.
        """
        num_items = self.regex_list.GetItemCount()
        if not self.signal_box.GetValue():
            return
        signal = self.signal_box.GetValue()

        if not self.component_box.GetValue():
            return
        component = self.component_box.GetValue()

        possible_signals = self.get_signals_list()

        if signal in possible_signals:
            signal = str(possible_signals.index(signal) + 1)

        if not signal in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            dlg = wx.MessageDialog(
                self,
                "No possible value selected! (1, 2, 3, 4, 5, 6, 7, 8) or ("
                + ", ".join(str(i) for i in possible_signals)
                + ")",
                "Error",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        if self.plugin.user_regex_contains_component(component):
            dlg = wx.MessageDialog(
                self,
                "There is already a regex containing " + str(component) + "!",
                "Error",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        self.regex_list.InsertItem(num_items, component)
        self.regex_list.SetItem(num_items, 1, possible_signals[int(signal) - 1])
        self.plugin.set_user_regex(component, signal)  # change in dict
        netcontains = False
        board = pcbnew.GetBoard()
        netcodearray = list(board.GetNetsByNetcode())
        for netcode in netcodearray:
            netname = board.FindNet(netcode).GetNetname()
            if component in netname:
                netcontains = True
        if not netcontains:
            dlg = wx.MessageDialog(
                self,
                "The Board has no Component that Contains: \n" + self.component,
                "Warning",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()

        self.component_box.Clear()
        self.signal_box.Clear()

    def on_remove(self, event):
        """Called by the 'remove' button. Removes the currently selected Regex - signal pair.

        Args:
            evt (wx.EVENT): Unused.
        """
        index = self.regex_list.GetFocusedItem()
        # change in dict
        self.plugin.delete_user_regex(self.regex_list.GetItem(index, 0).GetText())
        self.regex_list.DeleteItem(index)
        self.text.Clear()

    def on_close(self, event):
        """Called by the 'close' button. Closes the dialog.

        Args:
            evt (wx.EVENT): Unused.
        """
        self.Close()

    def on_clear(self, event):
        """Called by the 'clear' button. Deletes all entries.

        Args:
            evt (wx.EVENT): Unused.
        """
        self.regex_list.DeleteAllItems()
        self.plugin.clear_user_regex()  # change in dict
        self.text.Clear()

    def get_tracks(self):
        """Gets all tracks from the Pcbnew Api."""
        board = pcbnew.GetBoard()
        return board.GetTracks()

    def on_annotate(self, event):
        """Called by the 'annotate' button. Applies all RegExes.

        Args:
            evt (wx.EVENT): Unused.
        """

        dat = self.plugin.get_user_regex_tuples()
        board = pcbnew.GetBoard()
        netcodearray = list(pcbnew.GetBoard().GetNetsByNetcode())
        for (name, signal) in dat:
            for netcode in netcodearray:
                if name in board.FindNet(netcode).GetNetname():
                    self.plugin.set_annotated_net(netcode, signal)
        print("annotated succesfully")
