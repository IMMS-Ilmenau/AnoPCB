"""Contains the ShowResultsDialog used by the TrackGUI"""
import wx
import wx.aui
from PIL import Image
import seaborn as sns
import matplotlib.pyplot as plt
from AnomalyPlugin.brighten import brighten
from ordered_enum import OrderedEnum


class ShowResultsDialog(wx.Frame):
    """A dialog presenting the results of the evaluation of the current PCB."""

    def __init__(self, parent, plugin, layers, slice_positions, results):
        """Initializes the GUI, Bitmaps and data in use for the results representation.

        Args:
            parent (wx.Window): The parent Window.
            plugin (MainPlugin): The plugin instance.
            layers (List): The layers to be shown.
            slice_positions (List): A list with the positions of the slices.
            results (List): The list with the results: the mean squared errors,
                 the vectors representing the slices and the date of the results.
        """

        self.cached_result_bitmaps = {}
        self.layer_base_bitmaps = []
        self.layer_base_bitmaps_orig = []
        # ([text for Choice GUI Element], [tuples for cached_result_bitmaps])
        self.configurations = ([], [])
        self.cluster_size = None
        self.threshold = None
        self.cluster_alg = None

        self.og_y_size = len(layers[0])
        self.og_x_size = len(layers[0][0])
        if self.og_x_size > self.og_y_size:
            x_size = 900
            self.im_size = (x_size, self.og_y_size * x_size // self.og_x_size)
            self.scale = x_size / self.og_x_size
        else:
            y_size = 750
            self.im_size = (self.og_x_size * y_size // self.og_y_size, y_size)
            self.scale = y_size / self.og_y_size
        self.square_radius = 3
        self.square_radius_scaled = round(self.square_radius * self.scale)

        self.plugin = plugin
        self.layers = brighten(layers)
        self.slice_positions = slice_positions
        self.results = results
        plt.close()
        sns.set(color_codes=True)
        p = sns.distplot(results[1])
        p.set_xlabel("mse")
        p.set_ylabel("count")
        plt.show()

        # I didn't find any good libraries to create distinct colour palettes.
        # There are standalone tools though! https://mokole.com/palette.html
        alpha = 45

        self.colour_pallete_8 = [
            wx.Brush(colour)
            for colour in [
                wx.Colour(0x19, 0x19, 0x70, alpha),
                wx.Colour(0x3C, 0xB3, 0x71, alpha),
                wx.Colour(0xFF, 0x45, 0x00, alpha),
                wx.Colour(0xFF, 0xD7, 0x00, alpha),
                wx.Colour(0x00, 0xFF, 0x00, alpha),
                wx.Colour(0x00, 0xBF, 0xFF, alpha),
                wx.Colour(0x00, 0x00, 0xFF, alpha),
                wx.Colour(0xFF, 0x14, 0x93, alpha),
            ]
        ]

        self.colour_pallete_20 = [
            wx.Brush(colour)
            for colour in [
                wx.Colour(0xDC, 0xDC, 0xDC, alpha),
                wx.Colour(0x2F, 0x4F, 0x4F, alpha),
                wx.Colour(0x2E, 0x8B, 0x57, alpha),
                wx.Colour(0x8B, 0x00, 0x00, alpha),
                wx.Colour(0x80, 0x80, 0x00, alpha),
                wx.Colour(0x80, 0x00, 0x80, alpha),
                wx.Colour(0xFF, 0x00, 0x00, alpha),
                wx.Colour(0xFF, 0x8C, 0x00, alpha),
                wx.Colour(0xFF, 0xD7, 0x00, alpha),
                wx.Colour(0x00, 0x00, 0xCD, alpha),
                wx.Colour(0x00, 0xFA, 0x9A, alpha),
                wx.Colour(0x41, 0x69, 0xE1, alpha),
                wx.Colour(0xE9, 0x96, 0x7A, alpha),
                wx.Colour(0x00, 0xFF, 0xFF, alpha),
                wx.Colour(0x00, 0xBF, 0xFF, alpha),
                wx.Colour(0xAD, 0xFF, 0x2F, alpha),
                wx.Colour(0xFF, 0x00, 0xFF, alpha),
                wx.Colour(0xF0, 0xE6, 0x8C, alpha),
                wx.Colour(0xDD, 0xA0, 0xDD, alpha),
                wx.Colour(0xFF, 0x14, 0x93, alpha),
            ]
        ]

        self.colour_pallete_40 = [
            wx.Brush(colour)
            for colour in [
                wx.Colour(0xA9, 0xA9, 0xA9, alpha),
                wx.Colour(0x2F, 0x4F, 0x4F, alpha),
                wx.Colour(0x55, 0x6B, 0x2F, alpha),
                wx.Colour(0xA0, 0x52, 0x2D, alpha),
                wx.Colour(0x8B, 0x00, 0x00, alpha),
                wx.Colour(0x80, 0x80, 0x00, alpha),
                wx.Colour(0x48, 0x3D, 0x8B, alpha),
                wx.Colour(0x00, 0x80, 0x00, alpha),
                wx.Colour(0x00, 0x8B, 0x8B, alpha),
                wx.Colour(0x46, 0x82, 0xB4, alpha),
                wx.Colour(0x9A, 0xCD, 0x32, alpha),
                wx.Colour(0x00, 0x00, 0x8B, alpha),
                wx.Colour(0xDA, 0xA5, 0x20, alpha),
                wx.Colour(0x8B, 0x00, 0x8B, alpha),
                wx.Colour(0x66, 0xCD, 0xAA, alpha),
                wx.Colour(0xFF, 0x45, 0x00, alpha),
                wx.Colour(0xFF, 0x8C, 0x00, alpha),
                wx.Colour(0xC7, 0x15, 0x85, alpha),
                wx.Colour(0x00, 0xFF, 0x00, alpha),
                wx.Colour(0x8A, 0x2B, 0xE2, alpha),
                wx.Colour(0x00, 0xFF, 0x7F, alpha),
                wx.Colour(0xDC, 0x14, 0x3C, alpha),
                wx.Colour(0x00, 0xFF, 0xFF, alpha),
                wx.Colour(0x00, 0xBF, 0xFF, alpha),
                wx.Colour(0xF4, 0xA4, 0x60, alpha),
                wx.Colour(0x93, 0x70, 0xDB, alpha),
                wx.Colour(0x00, 0x00, 0xFF, alpha),
                wx.Colour(0xAD, 0xFF, 0x2F, alpha),
                wx.Colour(0xFF, 0x00, 0xFF, alpha),
                wx.Colour(0x1E, 0x90, 0xFF, alpha),
                wx.Colour(0xDB, 0x70, 0x93, alpha),
                wx.Colour(0xF0, 0xE6, 0x8C, alpha),
                wx.Colour(0xFA, 0x80, 0x72, alpha),
                wx.Colour(0xFF, 0xFF, 0x54, alpha),
                wx.Colour(0xDD, 0xA0, 0xDD, alpha),
                wx.Colour(0xAF, 0xEE, 0xEE, alpha),
                wx.Colour(0xEE, 0x82, 0xEE, alpha),
                wx.Colour(0x98, 0xFB, 0x98, alpha),
                wx.Colour(0xFF, 0xE4, 0xC4, alpha),
                wx.Colour(0xFF, 0xC0, 0xCB, alpha),
            ]
        ]

        wx.Frame.__init__(self, parent)
        self.SetTitle("Results " + self.results[3])
        self.control_elements()
        self.control_logic()
        self.layouting()

        for layer in self.layers:
            image = wx.Image(
                self.im_size[0],
                self.im_size[1],
                Image.fromarray(layer, "L")
                .resize(self.im_size)
                .convert("RGB")
                .tobytes(),
            )
            image.InitAlpha()
            self.layer_base_bitmaps.append(wx.Bitmap(image))

        # also create bitmaps with the original size for high resolution screenshots
        for layer in self.layers:
            image = wx.Image(
                self.og_x_size,
                self.og_y_size,
                Image.fromarray(layer, "L")
                .resize((self.og_x_size, self.og_y_size))
                .convert("RGB")
                .tobytes(),
            )
            image.InitAlpha()
            self.layer_base_bitmaps_orig.append(wx.Bitmap(image))

        self.change_layer(0)
        self.Fit()

    def control_elements(self):
        """Loads all the GUI-Elements for the results dialog."""

        self.menu_bar = wx.MenuBar()
        self.file_menu = wx.Menu()
        self.save_screenshot_item = self.file_menu.Append(
            wx.ID_ANY,
            item="screenshot",
            helpString="save a high resolution screenshot of all layers",
        )
        self.save_screenshot_item_only_mask = self.file_menu.Append(
            wx.ID_ANY,
            item="screenshot (only mask)",
            helpString="save a high resolution screenshot (only mask) of all layers",
        )

        self.cluster_menu = wx.Menu()
        self.kmeans_item = self.cluster_menu.AppendRadioItem(
            wx.ID_ANY, item="KMeans", help="choose KMeans as the clustering algorithm"
        )
        self.dbscan_item = self.cluster_menu.AppendRadioItem(
            wx.ID_ANY, item="DBscan", help="choose DBscan as the clustering algorithm"
        )
        self.optics_item = self.cluster_menu.AppendRadioItem(
            wx.ID_ANY, item="Optics", help="choose Optics as the clustering algorithm"
        )

        self.layer_panel = wx.Panel(self, size=self.im_size, style=wx.BORDER_NONE)
        self.picture = wx.StaticBitmap(self.layer_panel)
        self.layer_panel.SetBackgroundColour(wx.WHITE)

        self.grid_panel = wx.Panel(self, style=wx.SUNKEN_BORDER)

        layer_list = ["Layer " + str(i + 1) for i in range(len(self.layers))]
        self.layer_box = wx.Choice(self.grid_panel, choices=layer_list)
        self.layer_box.SetSelection(0)
        self.configuration_box = wx.Choice(
            self.grid_panel, choices=self.configurations[0]
        )

        self.threshold_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)
        self.cluster_panel = wx.Panel(self.grid_panel, style=wx.SUNKEN_BORDER)

        self.threshold_spin_text = wx.StaticText(
            self.threshold_panel, label="threshold: "
        )
        self.threshold_spin = wx.SpinCtrlDouble(
            self.threshold_panel, initial=0.02, inc=0.0001, max=10
        )
        self.cluster_spin_text = wx.StaticText(
            self.cluster_panel, label="cluster size: "
        )
        self.cluster_spin = wx.SpinCtrl(self.cluster_panel, initial=8, max=40, min=1)

        self.view_button = wx.Button(self.grid_panel, label="View")
        self.close = wx.Button(self.grid_panel, label="Close")

    def control_logic(self):
        """Binds the elements to their logic."""
        self.Bind(
            wx.EVT_MENU,
            self.create_high_resolution_screenshot,
            self.save_screenshot_item,
        )
        self.Bind(
            wx.EVT_MENU,
            self.create_high_resolution_screenshot_only_mask,
            self.save_screenshot_item_only_mask,
        )
        self.Bind(wx.EVT_MENU, self.update_clustering_radio, self.kmeans_item)
        self.Bind(wx.EVT_MENU, self.update_clustering_radio, self.dbscan_item)
        self.Bind(wx.EVT_MENU, self.update_clustering_radio, self.optics_item)
        self.layer_box.Bind(wx.EVT_CHOICE, self.change_layer_event)
        self.configuration_box.Bind(wx.EVT_CHOICE, self.change_configuration_event)
        self.view_button.Bind(wx.EVT_BUTTON, self.view_results)
        self.close.Bind(wx.EVT_BUTTON, self.on_close)

    def layouting(self):
        """Layouts and aligns all the GUI-Elements in the results dialog."""
        self.menu_bar.Append(self.file_menu, "&File")
        self.menu_bar.Append(self.cluster_menu, "&Clustering")
        self.SetMenuBar(self.menu_bar)
        self.kmeans_item.Check()

        aligner = wx.BoxSizer(wx.VERTICAL)
        aligner.Add(self.picture, flag=wx.BOTTOM, border=2)

        threshold_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cluster_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)

        threshold_horizontal_sizer.Add(
            self.threshold_spin_text, 2, wx.ALIGN_CENTER_VERTICAL
        )
        threshold_horizontal_sizer.Add(self.threshold_spin, 5, wx.ALL | wx.EXPAND)
        cluster_horizontal_sizer.Add(
            self.cluster_spin_text, 2, wx.ALIGN_CENTER_VERTICAL
        )
        cluster_horizontal_sizer.Add(self.cluster_spin, 5, wx.ALL | wx.EXPAND)

        self.threshold_panel.SetSizer(threshold_horizontal_sizer)
        self.cluster_panel.SetSizer(cluster_horizontal_sizer)

        grid = wx.GridSizer(2, 5, 5)
        grid.Add(self.layer_box, 5, wx.EXPAND)
        grid.Add(self.configuration_box, 5, wx.EXPAND)
        grid.Add(self.threshold_panel, 5, wx.EXPAND)
        grid.Add(self.cluster_panel, 5, wx.EXPAND)
        grid.Add(self.view_button, 5, wx.EXPAND)
        grid.Add(self.close, 5, wx.EXPAND)

        self.grid_panel.SetSizer(grid)
        aligner.Add(self.grid_panel, 5, wx.ALL | wx.EXPAND)

        self.SetSizer(aligner)
        self.Centre()

    def on_close(self, event):
        """Called by the "Close" button."""
        self.Close()

    def change_layer_event(self, event):
        """Called when selecting a layer. Wrapper function for the GUI to change the layer."""
        item = event.GetSelection()
        self.change_layer(int(item))

    def change_configuration_event(self, event):
        """Wrapper function for the GUI to change the configuration (threshold and cluster size)."""
        item = event.GetSelection()
        self.change_configuration(item)

    def change_layer(self, i):
        """Changes the displayed layer to the selected layer.

        Args:
            i (int): The index of the layers to change to.
        """
        try:
            bitmap = self.cached_result_bitmaps[
                (self.cluster_size, self.threshold, self.cluster_alg)
            ][i]
        except:
            bitmap = self.layer_base_bitmaps[i]
        self.picture.SetFocus()
        self.picture.SetBitmap(bitmap)

    def change_configuration(self, index):
        """Changes the configuration to the new chosen one from the cache (theshold & cluster size).

        Args:
            index (int): The index of the configuration in the cache.
        """
        self.configuration_box.SetSelection(index)
        print("change configuration")
        self.threshold = self.configurations[1][index][1]
        self.cluster_size = self.configurations[1][index][0]
        self.change_layer(self.layer_box.GetSelection())

    class Cluster_Alg(OrderedEnum):
        KMEANS = 1
        DBSCAN = 2
        OPTICS = 3

    def run_clustering(self):
        return self.plugin.cluster_results(
            self.results[2],
            self.results[1],
            self.cluster_size,
            self.threshold,
            self.cluster_alg,
        )

    def view_results(self, event):
        """Creates a new configuration (theshold & cluster size)
        or switches to an already created one.
        """
        self.update_cluster_size()
        self.update_threshold()
        self.update_cluster_alg()

        try:
            self.cached_result_bitmaps[
                (self.cluster_size, self.threshold, self.cluster_alg)
            ]
        except:
            # generate new result bitmaps
            print("start generating bitmaps and clustering")
            # get colours for the clusters
            cluster = self.run_clustering()
            print("finished clustering")

            cluster_size = max(cluster) + 1
            if cluster_size <= 8:
                colour_scheme = self.colour_pallete_8
            elif cluster_size <= 20:
                colour_scheme = self.colour_pallete_20
            else:
                colour_scheme = self.colour_pallete_40

            new_layers_bitmaps = [
                wx.Bitmap(layer_base_bitmap)
                for layer_base_bitmap in self.layer_base_bitmaps
            ]
            for new_layer_bitmap in new_layers_bitmaps:
                print("start drawing a layer")
                memory_dc = wx.MemoryDC()  # <- not able to draw transparently
                memory_dc.SelectObject(new_layer_bitmap)
                grc = wx.GraphicsContext.Create(
                    memory_dc
                )  # <- able to draw transparently :D
                cluster_type_counter = 0
                for (x_pos, y_pos), mse in zip(self.slice_positions, self.results[1]):
                    # check the threshold
                    if mse < self.threshold:
                        continue
                    # pick the colour
                    grc.SetBrush(colour_scheme[min(39, cluster[cluster_type_counter])])
                    # correct coordinates
                    x_pos = int(x_pos * self.scale)
                    y_pos = int(y_pos * self.scale)
                    # check position
                    dx_pos = 0
                    dy_pos = 0
                    if x_pos > self.square_radius_scaled:
                        x_pos -= self.square_radius_scaled
                    else:
                        dx_pos = self.square_radius_scaled - x_pos
                        x_pos = 0
                    if y_pos > self.square_radius_scaled:
                        y_pos -= self.square_radius_scaled
                    else:
                        dy_pos = self.square_radius_scaled - y_pos
                        y_pos = 0
                    # draw on graphics
                    grc.DrawRectangle(
                        x_pos,
                        y_pos,
                        1 + 2 * self.square_radius_scaled - dx_pos,
                        1 + 2 * self.square_radius_scaled - dy_pos,
                    )
                    # our clustering only considers values passing the threshold
                    cluster_type_counter += 1
                grc.Flush()
                memory_dc.SelectObject(wx.NullBitmap)  # properly close DeviceController
            print("finished drawing, now caching")

            # Cache newly generated layers!
            key = (self.cluster_size, self.threshold, self.cluster_alg)
            self.cached_result_bitmaps[key] = new_layers_bitmaps
            if self.cluster_alg == ShowResultsDialog.Cluster_Alg.KMEANS:
                self.configurations[0].append(
                    f"KMeans: threshold={key[1]} & cluster size={cluster_size}"
                )
            elif self.cluster_alg == ShowResultsDialog.Cluster_Alg.DBSCAN:
                self.configurations[0].append(
                    f"DBscan: threshold={key[1]} & cluster size={cluster_size}"
                )
            else:  # OPTICS
                self.configurations[0].append(
                    f"Optics: threshold={key[1]} & cluster size={cluster_size}"
                )
            self.configurations[1].append(key)

            # update the configuration box
            self.update_configuration_box(key)

        # update displayed bitmap
        self.change_layer(self.layer_box.GetSelection())

        # update the configuration box
        self.configuration_box.SetSelection(
            self.configurations[1].index(
                (self.cluster_size, self.threshold, self.cluster_alg)
            )
        )

        print("finished view")

    def create_high_resolution_screenshot(self, event):
        """Creates a high resolution screenshot of all layers with the current configuration
        and saves it to a location of choice. Either saves in png or jpg.
        """
        if len(self.configurations[0]) == 0:
            dia = wx.MessageDialog(
                parent=self,
                message="Please first create a configuration",
                caption="missing configuration",
                style=wx.OK,
            )
            dia.ShowModal()
            return

        with wx.FileDialog(
            self,
            "Save screenshot",
            wildcard="PNG files (*.png)|*.png|JPG files (*.jpg)|*.jpg",
            style=wx.FD_SAVE,
        ) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = str(file_dialog.GetPath())

            # generate new result bitmaps
            print("start generating bitmaps and clustering")
            # get colours for the clusters
            cluster = self.run_clustering()
            print("finished clustering")
            cluster_size = max(cluster)
            if cluster_size <= 8:
                colour_scheme = self.colour_pallete_8
            elif cluster_size <= 20:
                colour_scheme = self.colour_pallete_20
            else:
                colour_scheme = self.colour_pallete_40

            new_layers_bitmaps = [
                wx.Bitmap(layer_base_bitmap_orig)
                for layer_base_bitmap_orig in self.layer_base_bitmaps_orig
            ]
            bitmap_sum = wx.Bitmap(
                self.og_x_size, self.og_y_size * len(new_layers_bitmaps)
            )
            dc_sum = wx.MemoryDC()
            dc_sum.SelectObject(bitmap_sum)

            for new_layer_bitmap, bitmap_sum_counter in zip(
                new_layers_bitmaps, range(len(new_layers_bitmaps))
            ):
                print("start drawing a layer")
                memory_dc = wx.MemoryDC()  # <- not able to draw transparently
                memory_dc.SelectObject(new_layer_bitmap)
                grc = wx.GraphicsContext.Create(
                    memory_dc
                )  # <- able to draw transparently :D
                cluster_type_counter = 0
                for (x_pos, y_pos), mse in zip(self.slice_positions, self.results[1]):
                    # check the threshold
                    if mse < self.threshold:
                        continue
                    # pick the colour
                    grc.SetBrush(colour_scheme[min(39, cluster[cluster_type_counter])])
                    # check position
                    dx_pos = 0
                    dy_pos = 0
                    if x_pos > self.square_radius:
                        x_pos -= self.square_radius
                    else:
                        dx_pos = self.square_radius - x_pos
                        x_pos = 0
                    if y_pos > self.square_radius:
                        y_pos -= self.square_radius
                    else:
                        dy_pos = self.square_radius - y_pos
                        y_pos = 0
                    # draw on graphics
                    grc.DrawRectangle(
                        x_pos,
                        y_pos,
                        1 + 2 * self.square_radius - dx_pos,
                        1 + 2 * self.square_radius - dy_pos,
                    )
                    # our clustering only considers values passing the threshold
                    cluster_type_counter += 1
                grc.Flush()
                dc_sum.Blit(
                    0,
                    self.og_y_size * bitmap_sum_counter,
                    self.og_x_size,
                    self.og_y_size,
                    memory_dc,
                    0,
                    0,
                )
                memory_dc.SelectObject(wx.NullBitmap)  # properly close DeviceController
            dc_sum.SelectObject(wx.NullBitmap)
            image = bitmap_sum.ConvertToImage()
            if pathname.split(".")[-1].lower() == "png":
                image.SaveFile(pathname, wx.BITMAP_TYPE_PNG)
            else:
                image.SaveFile(pathname, wx.BITMAP_TYPE_JPEG)

    def create_high_resolution_screenshot_only_mask(self, event):
        if len(self.configurations[0]) == 0:
            dia = wx.MessageDialog(
                parent=self,
                message="Please first create a configuration",
                caption="missing configuration",
                style=wx.OK,
            )
            dia.ShowModal()
            return

        with wx.FileDialog(
            self,
            "Save screenshot",
            wildcard="PNG files (*.png)|*.png",
            style=wx.FD_SAVE,
        ) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = str(file_dialog.GetPath())

            # generate new result bitmaps
            print("start generating bitmaps and clustering")
            # get colours for the clusters
            cluster = self.run_clustering()
            print("finished clustering")
            cluster_size = max(cluster)
            if cluster_size <= 8:
                colour_scheme = self.colour_pallete_8
            elif cluster_size <= 20:
                colour_scheme = self.colour_pallete_20
            else:
                colour_scheme = self.colour_pallete_40

            bitmap_sum = wx.Bitmap(self.og_x_size, self.og_y_size, depth=32)
            dc_sum = wx.MemoryDC()
            dc_sum.SelectObject(bitmap_sum)

            print("start drawing a layer")
            grc = wx.GraphicsContext.Create(dc_sum)  # <- able to draw transparently :D
            # grc.SetBrush(wx.Brush(wx.Colour(0xFF, 0xFF, 0xFF, 0x00)))
            # grc.DrawRectangle(0, 0, self.og_x_size, self.og_y_size)
            cluster_type_counter = 0
            for (x_pos, y_pos), mse in zip(self.slice_positions, self.results[1]):
                # check the threshold
                if mse < self.threshold:
                    continue
                # pick the colour
                grc.SetBrush(colour_scheme[min(39, cluster[cluster_type_counter])])
                # check position
                dx_pos = 0
                dy_pos = 0
                if x_pos > self.square_radius:
                    x_pos -= self.square_radius
                else:
                    dx_pos = self.square_radius - x_pos
                    x_pos = 0
                if y_pos > self.square_radius:
                    y_pos -= self.square_radius
                else:
                    dy_pos = self.square_radius - y_pos
                    y_pos = 0
                # draw on graphics
                grc.DrawRectangle(
                    x_pos,
                    y_pos,
                    1 + 2 * self.square_radius - dx_pos,
                    1 + 2 * self.square_radius - dy_pos,
                )
                # our clustering only considers values passing the threshold
                cluster_type_counter += 1
                grc.Flush()
            dc_sum.SelectObject(wx.NullBitmap)
            image = bitmap_sum.ConvertToImage()
            image.SaveFile(pathname, wx.BITMAP_TYPE_PNG)

    def update_clustering_radio(self, event):
        self.cluster_spin.Enable(self.kmeans_item.IsChecked())

    def update_configuration_box(self, key):
        """Changes the configuration box to a new chosen one (when recently switch e.g.).
         Also sort the elements in the box/wx.Choice.

        Args:
            key (Tuple): The key of the configuration in the cache.
        """
        # sort all configurations (only if there's more than one element due to zip()s behaviour)
        if len(self.configurations[0]) > 1:
            self.configurations = list(
                map(
                    list,
                    zip(
                        *list(
                            sorted(
                                list(zip(*self.configurations)),
                                key=lambda x: (x[1][2], x[1][1], x[1][0]),
                            )
                        )
                    ),
                )
            )
        # set the current item
        i = self.configurations[1].index(key)
        self.configuration_box.SetItems(self.configurations[0])
        self.configuration_box.SetSelection(i)

    def update_cluster_alg(self):
        self.cluster_alg = (
            ShowResultsDialog.Cluster_Alg.KMEANS
            if self.kmeans_item.IsChecked()
            else (
                ShowResultsDialog.Cluster_Alg.DBSCAN
                if self.dbscan_item.IsChecked()
                else ShowResultsDialog.Cluster_Alg.OPTICS
            )
        )

    def update_cluster_size(self):
        """Updates the cluster size."""
        self.update_cluster_alg()
        if self.cluster_alg == ShowResultsDialog.Cluster_Alg.KMEANS:
            self.cluster_size = self.cluster_spin.GetValue()
        else:
            self.cluster_size == None

    def update_threshold(self):
        """Updates the threshold."""
        self.threshold = self.threshold_spin.GetValue()
