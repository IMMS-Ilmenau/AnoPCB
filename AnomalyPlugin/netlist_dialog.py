"""Contains the NetlistDialog used by the RegexDialog"""
import pcbnew
import wx
import wx.aui
import wx.lib.mixins.listctrl as listmix


class NetlistDialog(wx.Dialog):
    """The dialog for presenting a netlist with all annotated nets."""

    class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin):
        def __init__(
            self,
            parent,
            ID=wx.ID_ANY,
            pos=wx.DefaultPosition,
            size=wx.DefaultSize,
            style=0,
        ):
            wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
            listmix.TextEditMixin.__init__(self)

    def __init__(self, parent, plugin):
        wx.Dialog.__init__(self, parent, size=(700, 900))
        self.plugin = plugin
        self.parent = parent

        self.possible_signals = parent.get_signals_list()

        self.control_elements()
        self.control_logic()
        self.layouting()

        self.reload_data()

    def reload_data(self):
        self.list_an.DeleteAllItems()
        self.list_un.DeleteAllItems()
        netdict = dict(pcbnew.GetBoard().GetNetsByNetcode())
        for net, signal in self.plugin.annotated_nets.items():
            num_nets_an = self.list_an.GetItemCount()
            if net in netdict:
                self.list_an.InsertItem(num_nets_an, netdict[net].GetNetname())
                self.list_an.SetItem(num_nets_an, 1, str(signal))
                self.list_an.SetItem(
                    num_nets_an, 2, self.possible_signals[int(signal) - 1]
                )
                if signal != 0:
                    del netdict[net]
        for net in netdict:
            num_nets_un = self.list_un.GetItemCount()
            self.list_un.InsertItem(num_nets_un, netdict[net].GetNetname())

    def control_elements(self):
        self.list_an = NetlistDialog.EditableListCtrl(self, -1, style=wx.LC_REPORT)
        self.list_un = NetlistDialog.EditableListCtrl(self, -1, style=wx.LC_REPORT)

    def control_logic(self):
        self.list_an.Bind(
            wx.EVT_LIST_BEGIN_LABEL_EDIT, self.change_an_signal_evt_handler
        )
        self.list_un.Bind(
            wx.EVT_LIST_BEGIN_LABEL_EDIT, self.change_un_signal_evt_handler
        )
        self.list_an.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.highlight_an_net)
        self.list_un.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.highlight_un_net)
        self.list_an.Bind(wx.EVT_CLOSE, self.remove_hightlighting_evt)
        self.list_un.Bind(wx.EVT_CLOSE, self.remove_hightlighting_evt)

    def layouting(self):
        self.table_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.list_an.InsertColumn(0, "Annotated Nets")
        self.list_an.InsertColumn(1, "Signal")
        self.list_an.InsertColumn(2, "Signalname")
        self.list_an.SetColumnWidth(0, 140)
        self.list_an.SetColumnWidth(1, 50)
        self.list_an.SetColumnWidth(2, 140)
        self.list_un.InsertColumn(0, "Other Nets")
        self.list_un.SetColumnWidth(0, 140)
        self.table_sizer.Add(self.list_an, 1, wx.EXPAND)
        self.table_sizer.Add(self.list_un, 1, wx.EXPAND)
        self.SetSizer(self.table_sizer)

    def change_an_signal_evt_handler(self, evt):
        self.change_signal(evt.GetIndex(), self.list_an)
        evt.Veto()
        self.reload_data()

    def change_un_signal_evt_handler(self, evt):
        self.change_signal(evt.GetIndex(), self.list_un)
        evt.Veto()
        self.reload_data()

    def change_signal(self, index, table):
        netname = table.GetItemText(index)
        netcode = pcbnew.GetBoard().GetNetcodeFromNetname(netname)

        if netname == "":
            return

        message_net = f"Net: {netname}"

        signal = self.plugin.get_annotated_net(netcode)
        signalname = (
            self.possible_signals[7]
            if signal is None
            else self.possible_signals[int(signal) - 1]
        )
        signal = self.possible_signals.index(signalname) + 1
        dialog = wx.SingleChoiceDialog(
            parent=self,
            message=message_net + "Signal: " + str(signalname),
            caption="Annotation",
            choices=self.possible_signals,
        )
        dialog.SetSelection(signal - 1)
        if dialog.ShowModal() == wx.ID_CANCEL:
            return
        value = str(dialog.GetSelection() + 1)
        if not value.isnumeric():
            wx.MessageBox(
                "Input signal must be a positive Integer!",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        elif not value in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            wx.MessageBox(
                "Signal not within accepted range! [1, 2, ..., 8]",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        else:
            self.plugin.set_annotated_net(netcode, value)

    def highlight_net(self, index, table):
        self.remove_hightlighting()
        netname = table.GetItemText(index)
        netcode = pcbnew.GetBoard().GetNetcodeFromNetname(netname)
        if netcode == None or netcode == 0:
            return
        comps = list(self.get_tracks()) + list(self.get_pads()) + list(self.get_zones())
        for comp in comps:
            if comp.GetNetCode() == netcode:
                print(f"Netcode {str(comp.GetNetCode())} set brightened")
                comp.SetBrightened()
        pcbnew.Refresh()

    def highlight_an_net(self, evt):
        self.highlight_net(evt.GetIndex(), self.list_an)
        evt.Allow()

    def highlight_un_net(self, evt):
        self.highlight_net(evt.GetIndex(), self.list_un)
        evt.Allow()

    def get_tracks(self):
        """Gets the current tracks from pcbnew.

        Returns:
            [pcbnew.Track]: The array of tracks.
        """
        board = pcbnew.GetBoard()
        return board.GetTracks()

    def get_pads(self):
        """Gets the current pads from pcbnew.

        Returns:
            [pcbnew.Pad]: The array of tracks.
        """
        board = pcbnew.GetBoard()
        return board.GetPads()

    def get_zones(self):
        """Gets the current zones from pcbnew.

        Returns:
            [pcbnew.Zone]: The array of zones.
        """
        board = pcbnew.GetBoard()
        return board.Zones()

    def remove_hightlighting_evt(self, evt):
        self.remove_hightlighting()

    def remove_hightlighting(self):
        """Dehighlights all brightened tracks and zones.

        Args:
            evt (wx.EVENT): Unused.
        """
        tracks = self.get_tracks()
        zones = self.get_zones()
        pads = self.get_pads()
        for track in tracks:
            track.ClearBrightened()
        for zone in zones:
            zone.ClearBrightened()
        for pad in pads:
            pad.ClearBrightened()
        pcbnew.Refresh()
        print("removed hightlighting")
