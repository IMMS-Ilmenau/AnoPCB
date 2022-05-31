"""Contains the Main GUI."""
import os
import time
import json
import numpy as np
import pcbnew
import wx
from AnomalyPlugin.conf_model_dialog_new import ConfModelDialog
from AnomalyPlugin.show_results_dialog import ShowResultsDialog
from AnomalyPlugin.preferences_window import PreferencesWindow
from AnomalyPlugin.regex_dialog import RegexDialog
from AnomalyPlugin.train_model_dialog import TrainModelDialog


class TrackGUI(wx.Panel):
    """Main class of the wx GUI used by the plugin."""

    def __init__(self, parent, plugin):
        """Initializes the GUI elements.

        Args:
            parent (wx.Window): The parent window.
            plugin (MainPlugin): The instance of the plugin.
        """
        self.icon_width_height = 30
        self.plugin = plugin
        wx.Panel.__init__(self, parent)

        self.control_elements()
        self.control_logic()
        self.Show(True)

    def on_size_change(self, evt):
        """Changes the orientation of the GUI panel.

        Args:
            evt (wx.EVENT): Unused.
        """
        size = evt.GetSize()
        if size.x > size.y and self.aligner.GetOrientation() == wx.VERTICAL:
            self.aligner.SetOrientation(wx.HORIZONTAL)
            self.aligner.Layout()
        elif size.y > size.x and self.aligner.GetOrientation() == wx.HORIZONTAL:
            self.aligner.SetOrientation(wx.VERTICAL)
            self.aligner.Layout()
        evt.Skip()

    def resize(self):
        """Resizes all elements to fit the GUI by using the parent window."""
        self.aligner.Fit(self.Parent)  # r esize everything to fit

    def get_bitmap_icon(self, path):
        """Converts an image to a bitmap and scales its size to fit the toolbar.

        Args:
            path (str): The path to the image to be used.

        Returns:
            wx.Bitmap: The created bitmap with proper size.
        """
        image = wx.Image(path, wx.BITMAP_TYPE_PNG)
        image = image.Scale(
            self.icon_width_height, self.icon_width_height, wx.IMAGE_QUALITY_HIGH
        )
        return wx.Bitmap(image)

    def control_elements(self):
        """Sets up the layout and design of the GUI."""
        path_button_annotate = os.path.join(
            os.path.split(__file__)[0], "Icons/logo_annotate.png"
        )
        path_button_show_left = os.path.join(
            os.path.split(__file__)[0], "Icons/logo_show_unannotated.png"
        )
        path_button_create_slices = os.path.join(
            os.path.split(__file__)[0], "Icons/logo_analyze.png"
        )
        path_button_preferences = os.path.join(
            os.path.split(__file__)[0], "Icons/logo_settings.png"
        )
        path_button_regular_expressions = os.path.join(
            os.path.split(__file__)[0], "Icons/logo_RegEx.png"
        )
        path_button_model_configuration = os.path.join(
            os.path.split(__file__)[0], "Icons/IconConf.png"
        )
        path_button_filter = os.path.join(
            os.path.split(__file__)[0], "Icons/IconFilter.png"
        )
        path_button_train = os.path.join(
            os.path.split(__file__)[0], "Icons/logo_train.png"
        )

        self.button_annotate = wx.BitmapButton(
            self, 0, self.get_bitmap_icon(path_button_annotate)
        )
        self.button_show_left = wx.BitmapButton(
            self, 1, self.get_bitmap_icon(path_button_show_left)
        )
        self.button_create_slices = wx.BitmapButton(
            self, 2, self.get_bitmap_icon(path_button_create_slices)
        )
        self.button_preferences = wx.BitmapButton(
            self, 3, self.get_bitmap_icon(path_button_preferences)
        )
        self.button_regular_expressions = wx.BitmapButton(
            self, 4, self.get_bitmap_icon(path_button_regular_expressions)
        )
        self.button_model_configuration = wx.BitmapButton(
            self, 5, self.get_bitmap_icon(path_button_model_configuration)
        )
        self.button_filter = wx.BitmapButton(
            self, 6, self.get_bitmap_icon(path_button_filter)
        )
        self.button_train = wx.BitmapButton(
            self, 7, self.get_bitmap_icon(path_button_train)
        )

        self.button_annotate.SetToolTip(wx.ToolTip("annotate"))
        self.button_show_left.SetToolTip(wx.ToolTip("show unannotated tracks"))
        self.button_create_slices.SetToolTip(wx.ToolTip("analyze board"))
        self.button_preferences.SetToolTip(wx.ToolTip("preferences"))
        self.button_regular_expressions.SetToolTip(wx.ToolTip("regular expressions"))
        self.button_model_configuration.SetToolTip(wx.ToolTip("model configuration"))
        self.button_filter.SetToolTip(wx.ToolTip("show last results"))
        self.button_train.SetToolTip(wx.ToolTip("train model"))

        aligner = wx.BoxSizer(wx.VERTICAL)
        aligner.Add(self.button_annotate, 0, wx.SHAPED)
        aligner.Add(self.button_show_left, 0, wx.SHAPED)
        aligner.Add(self.button_create_slices, 0, wx.SHAPED)
        aligner.Add(self.button_preferences, 0, wx.SHAPED)
        aligner.Add(self.button_regular_expressions, 0, wx.SHAPED)
        aligner.Add(self.button_model_configuration, 0, wx.SHAPED)
        aligner.Add(self.button_filter, 0, wx.SHAPED)
        aligner.Add(self.button_train, 0, wx.SHAPED)

        self.SetSizer(aligner)
        self.aligner = aligner

    def control_logic(self):
        """Sets up the logic and functionality of the GUI."""
        # Triggert die Funktionen fuer die entsprechenden Buttons
        self.button_annotate.Bind(wx.EVT_BUTTON, self.annotate_selected)
        self.button_show_left.Bind(wx.EVT_BUTTON, self.show_unannotated)
        self.button_create_slices.Bind(wx.EVT_BUTTON, self.create_slices)
        self.button_preferences.Bind(wx.EVT_BUTTON, self.preferences)
        self.button_regular_expressions.Bind(wx.EVT_BUTTON, self.do_regex)
        self.button_model_configuration.Bind(wx.EVT_BUTTON, self.configure_model)
        self.button_filter.Bind(wx.EVT_BUTTON, self.filter_model)
        self.button_train.Bind(wx.EVT_BUTTON, self.train_model)
        self.Bind(wx.EVT_SIZE, self.on_size_change)

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

    def train_model(self, evt):
        """Opens the model training dialog.

        Args:
            evt (wx.EVENT): Unused.
        """
        if self.plugin.maybe_start_anopcb_server():
            # wait for the server to boot
            time.sleep(3)

        dia = TrainModelDialog(self, self.plugin)
        dia.Show()

    def filter_model(self, evt):
        # TODO add doc string, if it's actually used in form of a button?
        """Tries to load and display results from last analysis.

        Args:
            evt (wx.EVENT): Unused.
        """
        if not (
            os.path.isfile(self.plugin.anopcb_filter_slices_path)
            and os.path.isfile(self.plugin.anopcb_filter_results_path)
            and os.path.isfile(self.plugin.anopcb_filter_layers_path)
        ):
            dia = wx.MessageDialog(
                parent=self,
                message="You are missing files to show the filter results. Enable the option to save the data and run analyze!",
                caption="cannot show the filter results",
                style=wx.OK,
            )
            dia.ShowModal()
            return

        with open(self.plugin.anopcb_filter_slices_path) as slices_json:
            slices = json.load(slices_json)
        with open(self.plugin.anopcb_filter_results_path) as results_json:
            results = json.load(results_json)
        with open(self.plugin.anopcb_filter_layers_path) as layers_json:
            layers = json.load(layers_json)
        layers = np.asarray(layers, dtype=np.int8)

        def get_slice_position(slice_meta):
            splitted = slice_meta.split("_")
            return (int(splitted[0]), int(splitted[1]))

        slice_positions = [get_slice_position(slice[0]) for slice in slices]

        # open a results dialog
        dialog = ShowResultsDialog(self, self.plugin, layers, slice_positions, results)
        dialog.Show()

    def configure_model(self, evt):
        """Called by the "model configuration" button. Opens the corresponding dialog."""
        if self.plugin.maybe_start_anopcb_server():
            # wait for the server to boot
            time.sleep(3)

        dia = ConfModelDialog(self, self.plugin)
        dia.Show()

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

    def hightlight_annotated(self, evt):
        """Annotates all selected tracks and zones with signal 1.

        Args:
            evt (wx.EVENT): Unused.
        """
        tracks = self.get_tracks()
        zones = self.get_zones()
        for track in tracks:
            if self.plugin.is_annotated(track.GetNetCode()):
                track.SetBrightened()
            else:
                track.ClearBrightened()
        for zone in zones:
            if self.plugin.is_annotated(zone.GetNetCode()):
                zone.SetBrightened()
            else:
                zone.ClearBrightened()
        pcbnew.Refresh()

    def remove_hightlighting(self, evt):
        """Dehighlights all brightened tracks and zones.

        Args:
            evt (wx.EVENT): Unused.
        """
        tracks = self.get_tracks()
        zones = self.get_zones()
        for track in tracks:
            track.ClearBrightened()
        for zone in zones:
            zone.ClearBrightened()
        pcbnew.Refresh()

    def annotate_selected(self, evt):
        """Opens the dialog to annotate multiple selected components with signal information.

        Arguments:
            evt (wx.EVENT): Unused but necessary.
        """
        try:
            comps = list(
                filter(
                    lambda x: x.IsSelected(),
                    list(self.get_tracks()) + list(self.get_pads()),
                )
            )
            # check if there's atleast one element
            next(iter(comps))
        except StopIteration:
            wx.MessageBox(
                "Must select a component first!", "Error", wx.OK | wx.ICON_ERROR
            )
            return

        # build the string from hand to add \n
        temp_nets = list(dict.fromkeys(map(lambda x: str(x.GetNetname()), comps)))
        message_nets = "Nets: ["
        for net_i in zip(range(1, len(temp_nets) + 1), temp_nets):
            message_nets = message_nets + f"'{net_i[1]}'"
            if net_i[0] != len(temp_nets):
                message_nets = message_nets + ", "
            if net_i[0] / 4 == int(net_i[0] / 4) and net_i[0] != len(temp_nets):
                message_nets = message_nets + "\n"
        message_nets = message_nets + "]\n"

        possible_signals = self.get_signals_list()
        signals = set()
        for signal in list(
            map(lambda x: self.plugin.get_annotated_net(x.GetNetCode()), comps)
        ):
            signal = (
                possible_signals[7]
                if signal is None
                else possible_signals[int(signal) - 1]
            )  # we don't expect written signals with value 0
            signals.update({signal})

        # Erzeugung des Eingabefensters:
        signal = (
            8
            if len(signals) != 1
            else (possible_signals.index(next(iter(signals))) + 1)
        )
        signals = list(signals)
        signals.sort()

        dialog = wx.SingleChoiceDialog(
            parent=self,
            message=message_nets + "Signals: " + str(signals),
            caption="Annotation",
            choices=possible_signals,
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
            for netcode in list(map(lambda x: x.GetNetCode(), comps)):
                self.plugin.set_annotated_net(netcode, value)

    def preferences(self, evt):
        """Opens the Preferences window."""
        pref_window = PreferencesWindow(parent=self, plugin=self.plugin)
        pref_window.Show(True)

    def create_slices(self, evt):
        """Starts the PCB Analysis.

        Arguments:
            evt (wx.EVENT): Unused but necessary.
        """
        dia = wx.MessageDialog(
            parent=self,
            message="This may take 10 minutes or longer. Continue?",
            caption="Are you sure?",
            style=wx.OK | wx.CANCEL | wx.CANCEL_DEFAULT,
        )
        if dia.ShowModal() == wx.ID_OK:
            self.plugin.analyze()

    def do_regex(self, evt):
        """Opens the regex GUI.

        Args:
            evt (wx.EVENT): Unused.
        """
        dia = RegexDialog(parent=self, plugin=self.plugin)
        dia.Show(True)

    def show_unannotated(self, evt):
        """Marks all tracks and vias, which have no annotation yet.

        Args:
            evt (wx.EVENT): Unused but necessary.
        """
        comps = list(self.get_tracks()) + list(self.get_pads())
        show = True
        for comp in comps:
            if comp.IsBrightened():
                show = False
                break

        def is_zero_lambda(comp):
            code = self.plugin.get_annotated_net(comp.GetNetCode())
            return (code == None or int(code) == 0) and comp.GetNetname() != ""

        if show:
            unannotated_comps = list(filter(is_zero_lambda, comps))
            for comp in unannotated_comps:
                comp.SetBrightened()
        else:
            for comp in comps:
                comp.ClearBrightened()
        pcbnew.Refresh()
