"""The core of the plugin."""
import sys
if __package__ is None or __package__ == "":
    sys.path.append("..")
import pcbnew
import wx
import wx.aui
import os
import datetime
import time
import json
import docker
import atexit
from threading import Thread
from skimage import io as skio
from skimage import draw
import sklearn.cluster
import numpy as np
import re
from AnomalyPlugin.wrappers import Track, Pad, Via, Net
from AnomalyPlugin.track_gui import TrackGUI
from AnomalyPlugin.show_results_dialog import ShowResultsDialog
from AnomalyPlugin.generate_slices_mp import createSlicesMP
from AnomalyPlugin.server_api import ServerAPI
#from .wrappers import Track, Pad, Via, Net
#from . import TrackGUI
#from .alternative_generate_slices import createSlicesAlt
#from .generate_slices_mp import createSlicesMP
#from .generate_slices_default import createSlices


class MainPlugin(pcbnew.ActionPlugin):
    """
    This plugin handles core functionality for AnoPCB
     like handling data and a local server."""

    def defaults(self):
        """Sets default values, setup plugin metadata."""
        self.name = "AnoPCB"
        self.category = "prototype"
        self.description = "annotation and serilization of nets, create slices"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.split(__file__)[0], "Icons/rsz_anopcb.png")
        # our dict containing information about our annotated data
        # key: NetCode (Integer); value: Signal (Integer)
        self.annotated_nets = {}
        self.backup_nets = True
        # dict containing user preferences
        # key: Preference Name (String); value: Wert (???)
        self.preferences = {}
        self.backup_prefs = True
        # dict containing user regexes
        # key: RegEx (String); value: Signal (Integer)

        self.user_regexes = {}
        self.backup_regex = True
        # only initialize once
        self.initialized = False

        # dict containing singals
        # key: Signal (String); value: Number (Integer)
        self.signals = {}
        self.backup_signals = True


    def get_preference(self, name):
        """Used to get a current preference setting.

        Args:
            name (str): The preference name, whose current setting is asked for.

        Returns:
            str, int: The setting of the preference name, which was passed as an argument.
        """
        return self.preferences.get(name)


    def set_preference(self, name, value):
        """Used to set a current preference setting.

        Args:
            name (str): The preference name to set a setting for.
            value (int, str): The setting value to set.
        """
        self.preferences[name] = value
        # is_remote = self.get_preference("server_type")=="remote" 
        is_remote = True if self.get_preference("server_type") == "remote" else False
        if name == "server_address" and is_remote:
            self.server_api.update_adress(value, self.get_preference("server_port"))
        if name == "server_port" and is_remote:
            self.server_api.update_adress(self.get_preference("server_address"), value)
        if name == "server_type" and is_remote:
            self.server_api.update_adress(
                self.get_preference("server_address"),
                self.get_preference("server_port"))

        return


    def user_regex_contains(self, name) -> bool:
        """Checks whether a specific regex exists.

        Args:
            name (str): The regex to check for.

        Returns:
            bool: Whether the regex exists.
        """
        if name in self.user_regexes:
            return True
        return False

    def user_regex_contains_component(self, name) -> bool:
        """Checks whether a regex for a component exists.

        Args:
            name (str): The regex to check for.

        Returns:
            bool: Whether the regex exists.
        """
        return name in self.user_regexes.keys()

    def get_user_regex(self, name):
        """Used to get the annotated signal of a regex.

        Args:
            name (str): The regex, whose signal is asked for.

        Returns:
            str: The signal of the regex, which was passed as an argument.
        """
        return self.user_regexes.get(name)


    def set_user_regex(self, name, signal):
        """Used to set the annotated signal for a regex.

        Args:
            name (str): The regex to be set.
            signal (str): The signal of the regex to be set.
        """
        self.user_regexes[name] = signal
        return


    def delete_user_regex(self, name):
        """Deletes a regex associated with a signal.

        Args:
            name (str): The regex text of the regex to be removed.
        """
        del self.user_regexes[name]
        return


    def clear_user_regex(self):
        """Deletes all regex associated with a signal.
        """
        self.user_regexes.clear()
        return


    def get_user_regex_tuples(self):
        """
        Gets all all regex associated with a signal in
         form of an array with tuples instead of a dict.

        Returns:
            tuple: The new created tuple containing the regex and signals.
        """
        dat = []
        for compx in self.user_regexes:
            dat.append((compx, self.user_regexes[compx]))
        return dat


    def get_annotated_net(self, netcode):
        """Used to get the specifically annotated signal of a net.

        Args:
            netcode (str): The netcode, whose signal is asked for.

        Returns:
            str: The signal of the netcode, which was passed as an argument.
        """
        return self.annotated_nets.get(netcode)


    def set_annotated_net(self, netcode, signal):
        """Used to set the specifically annotated signal of a net.

        Args:
            netcode (str): The netcode, whose signal is to be set.
            signal (str): The signal to be set.
        """
        self.annotated_nets[netcode] = signal
        return


    def scheduled_save(self):
        """
        Make sure to save all to be serialized data, when the user saves the kicad project.
        Also make backup data to prevent accidental loss of data.
        """
        while True:
            last_modified = os.path.getmtime(self.project_file_path)
            if self.project_last_modified != last_modified:
                # project was saved -> update last_modified and save anopcb's data
                self.project_last_modified = last_modified
                # save preferences and annotations, create backups (just in case)
                try:
                    with open(self.anopcb_nets_path, 'w') as anopcb_json:
                        json.dump(self.annotated_nets, anopcb_json)
                    if self.backup_nets:
                        with open(self.anopcb_nets_backup_path, 'w') as anopcb_json:
                            json.dump(self.annotated_nets, anopcb_json)
                    print("Saved annotations.")

                    with open(self.anopcb_pref_path, 'w') as anopcb_json:
                        json.dump(self.preferences, anopcb_json)
                    if self.backup_prefs:
                        with open(self.anopcb_pref_backup_path, 'w') as anopcb_json:
                            json.dump(self.preferences, anopcb_json)
                    print("Saved preferences.")

                    # saves regex
                    with open(self.anopcb_regex_path, 'w') as anopcb_json:
                        json.dump(self.user_regexes, anopcb_json)
                    if self.backup_regex:
                        with open(self.anopcb_regex_backup_path, 'w') as anopcb_json:
                            json.dump(self.user_regexes, anopcb_json)
                    print("Saved regular expressions.")

                except IOError as error:
                    print("Error while saving: ", error.args)
            time.sleep(0.3)


    def scheduled_stop_server(self):
        """Make sure to stop the locally started docker server once kicad is closed.
        """
        try:
            self.anopcb_server_container.stop()
        except Exception:
            pass

    def scheduled_session_removal(self):
        """Make sure to remove session from server before closing application.
        If this does not get through, the server will remove the session after 30 minutes of inactivity.
        """
        try:
            self.server_api.remove_session()
        except Exception:
            pass


    def initiliaze(self):
        """
        Initiliazes stuff after pcbnew finished initiliazing itself,
         by doing it when the user interacts with the plugin the first time.
         Also it's only called once at most. It loads seriliazed data and makes
         sure data is saved when the user saves the project.
        """
        if not self.initialized:
            self.initialized = True

            # paths of relevant files
            self.project_file_path = pcbnew.GetBoard().GetFileName()
            if self.project_file_path == '':
                wx.MessageBox(
                    "No Project opened, the plugin wont work!",
                    'Error',
                    wx.OK | wx.ICON_ERROR)
                return
            self.project_dir_path = os.path.split(self.project_file_path)[0] #(dirname, filename)[0]
            self.anopcb_nets_path = os.path.join(
                self.project_dir_path, 'anopcb_kicad_pcb.json')
            self.anopcb_nets_backup_path = os.path.join(
                self.project_dir_path, 'anopcb_kicad_pcb_backup.json')
            self.anopcb_pref_path = os.path.join(
                self.project_dir_path, 'anopcb_kicad_pref.json')
            self.anopcb_pref_backup_path = os.path.join(
                self.project_dir_path, 'anopcb_kicad_pref_backup.json')
            self.anopcb_regex_path = os.path.join(
                self.project_dir_path, 'anopcb_kicad_regex.json')
            self.anopcb_regex_backup_path = os.path.join(
                self.project_dir_path, 'anopcb_kicad_regex_backup.json')
            self.anopcb_filter_layers_path = os.path.join(
                self.project_dir_path, 'anopcb_filter_layers.json')
            self.anopcb_filter_slices_path = os.path.join(
                self.project_dir_path, 'anopcb_filter_slices.json')
            self.anopcb_filter_results_path = os.path.join(
                self.project_dir_path, 'anopcb_filter_results.json')

            # if anopcb already saved annotation data, we will want to load it
            # if we cant load it the backup wont be overriden with the new (empty) dictionary
            if os.path.isfile(self.anopcb_nets_path):
                with open(self.anopcb_nets_path, "r") as anopcb_json:
                    try:
                        self.annotated_nets = json.load(anopcb_json)
                    except json.decoder.JSONDecodeError as error:
                        print("Error while loading annotations: ", error.args)
                        self.annotated_nets = {}
                        self.backup_nets = False
                new_d = {int(key) : int(value) for key, value in self.annotated_nets.items()}
                self.annotated_nets = new_d
            else:
                self.backup_nets = False
                print("Error: Did not find config file 'anopcb_kicad_pcb.json'.")

            if os.path.isfile(self.anopcb_pref_path):
                with open(self.anopcb_pref_path, "r") as anopcb_json:
                    try:
                        preferences = json.load(anopcb_json)
                        self.preferences = preferences
                    except json.decoder.JSONDecodeError as error:
                        print("Error while loading preferences: ", error.args)
                        self.backup_prefs = False
            else:
                self.backup_prefs = False
                print("Error: Did not find config file 'anopcb_kicad_pref.json'.")

            # default preferences
            if self.preferences.get("server_address") is None:
                self.preferences["server_address"] = "localhost"
            if self.preferences.get("server_port") is None:
                self.preferences["server_port"] = 8420
            if self.preferences.get("slice_x") is None:
                self.preferences["slice_x"] = 28
            if self.preferences.get("slice_y") is None:
                self.preferences["slice_y"] = 4
            if self.preferences.get("server_type") is None:
                self.preferences["server_type"] = "remote"
            if self.preferences.get("save_filter_data") is None:
                self.preferences["save_filter_data"] = False

            if self.preferences.get("signal1") is None:
                self.preferences["signal1"] = "digital stable"
            if self.preferences.get("signal2") is None:
                self.preferences["signal2"] = "digital switching"
            if self.preferences.get("signal3") is None:
                self.preferences["signal3"] = "analog"
            if self.preferences.get("signal4") is None:
                self.preferences["signal4"] = "analog sensitive"
            if self.preferences.get("signal5") is None:
                self.preferences["signal5"] = "supply"
            if self.preferences.get("signal6") is None:
                self.preferences["signal6"] = "None"
            if self.preferences.get("signal7") is None:
                self.preferences["signal7"] = "None"
            if self.preferences.get("signal8") is None:
                self.preferences["signal8"] = "unknown"

            

            if os.path.isfile(self.anopcb_regex_path):
                with open(self.anopcb_regex_path, "r") as anopcb_json:
                    try:
                        user_regexes = json.load(anopcb_json)
                        self.user_regexes = user_regexes
                    except json.decoder.JSONDecodeError as error:
                        print("Error while loading regexes: ", error.args)
                        self.backup_regex = False
            else:
                self.backup_regex = False
                print("Error: Did not find config file 'anopcb_kicad_regex.json'.")

            # keep track of the last modified time, to be able to check, if the project was saved
            self.project_last_modified = os.path.getmtime(self.project_file_path)
            # start a periodic thread, to save our annotation data, when the project is saved
            timer = Thread(target=self.scheduled_save)
            timer.setDaemon(True)
            timer.start()

            # the server api
            self.server_api = ServerAPI(
                self.get_preference("server_address"),
                self.get_preference("server_port"))
            
            atexit.register(self.scheduled_session_removal)


    def maybe_start_anopcb_server(self):
        """
        Checks whether a local server is wished for by the user.
         Proceeds to start one, by using docker.
         When no docker server image is located on disk it also downloads it from the internet.
         It can start a server using the cpu or the gpu, decided by the user.
         Make sure to have docker installed, running and working!
         Also it makes sure to stop the server when closing kicad.
         Sets up the API connection details of the plugin.
         Only one server runs at max.

        Returns:
            bool: Whether a server was actually started.
        """
        server_started_here = False

        # check whether to even use a local server and make sure it's note remote
        docker_tag = self.get_preference("server_type")

        if docker_tag == "remote":
            return False

        if os.system("which docker") == 256:
            wx.MessageBox(
                "Docker not installed, install or use remote server instead!",
                'Error',
                wx.OK | wx.ICON_ERROR)
            return False

        # setting up the docker anopcb server
        docker_client = docker.from_env()

        # look for a eventually running server and stop it
        try:
            if self.anopcb_server_container.name == f"anopcb-server-{docker_tag}":
                self.server_api.update_adress("localhost", 23923)
                return server_started_here
            self.anopcb_server_container.stop()
        except:
            pass

        # add ${ANOPCB_SERVER_SOURCE} to path! (path to the folder containing the source)
        # create/run the server container, may take a while to download
        try:
            self.anopcb_server_container = list(filter(
                lambda container: container.name == f"anopcb-server-{docker_tag}",
                docker_client.containers.list(all=True)))[0]

            self.anopcb_server_container.restart()
            server_started_here = True
        except:
            dlg = wx.MessageDialog(
                None,
                "This might download a docker image from the internet and it would take some time. Continue?",
                'Continue?',
                wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            if result == wx.ID_NO:
                return False

            mount_volumes = {"anopcb-models": {"bind": "/anopcb-server/models", "mode": "rw"}}
            try:
                mount_volumes.update({f"{os.environ['ANOPCB_SERVER_SOURCE']}/AnomalyServer.py": {"bind": "/anopcb-server/AnomalyServer.py", "mode": "rw"}})
            except:
                pass


            self.anopcb_server_container = docker_client.containers.run(
                f"julian20delta/anopcb-server:{docker_tag}",
                ports={23923: 23923},
                detach=True,
                volumes=mount_volumes,
                name=f"anopcb-server-{docker_tag}")
            server_started_here = True
        self.server_api.update_adress("localhost", 23923)

        # register clean up function to stop the server later
        atexit.register(self.scheduled_stop_server)

        return server_started_here


    def remove_docker_container(self):
        """Tries to stop the currently active docker server."""
        docker_client = docker.from_env()
        try:
            self.anopcb_server_container.stop()
        except:
            pass
        try:
            container = list(filter(
                lambda container: container.name == f"anopcb-server-cpu",
                docker_client.containers.list(all=True)))[0]
            container.remove()
        except:
            pass
        try:
            container = list(filter(
                lambda container: container.name == f"anopcb-server-gpu",
                docker_client.containers.list(all=True)))[0]
            container.remove()
        except:
            pass
        self.anopcb_server_container = None

        dlg = wx.MessageDialog(
            None,
            "This might download a docker image from the internet and it would take some time. Continue?",
            'Continue?',
            wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_NO:
            return
        docker_tag = self.get_preference("server_type")
        if docker_tag == "remote":
            docker_tag = ""
        else:
            docker_tag = ":"+docker_tag
        try:
            docker_client.images.pull(f"julian20delta/anopcb-server{docker_tag}")
        except:
            pass

    def export_slices(self, gui):
        dia = wx.MessageDialog(
            parent=gui,
            message="This may take 5 minutes or longer. Continue?",
            caption="Are you sure?",
            style=wx.OK | wx.CANCEL | wx.CANCEL_DEFAULT)
        if not dia.ShowModal() == wx.ID_OK:
            return
        
        board = pcbnew.GetBoard()
        filename = board.GetFileName()
        name = re.search(r'[^\/]*\.kicad_pcb', filename).group(0)[:-10]

        with wx.FileDialog(
                gui,
                "Export slices",
                wildcard="JSON file (*.json)|*.json",
                defaultFile="slices_"+name+".json",
                style=wx.FD_SAVE) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = str(file_dialog.GetPath())

        slices = self.create_slices_mp()
        slices = slices[1]
        send_slices = [y.decode("utf-8") for x, y in slices] # x is metadata (e.g. position), y is slice in bytes
        slice_count = str(len(send_slices))
        x_dim = str(self.get_preference("slice_x"))
        y_dim = str(self.get_preference("slice_y"))

        data = dict()
        data['send_slices'] = send_slices
        data['slice_count'] = slice_count
        data['x_dim'] = x_dim
        data['y_dim'] = y_dim
        data['name'] = name

        with open(pathname, 'w') as json_file:
            json.dump(data, json_file)
        
        dia = wx.MessageDialog(
                parent=gui,
                message="Done saving slices.",
                caption="Notice",
                style=wx.OK)
        dia.ShowModal()


    def is_annotated(self, netid):
        """(BROKEN) Checks whether a net has a specifically annotated signal.

        Args:
            netid (int): The netcode, whose annotation state is asked for.

        Returns:
            bool: Whether an annotation exists.
        """
        try:
            return self.annotated_nets[str(netid)] == 1
        except KeyError:
            self.annotated_nets[str(netid)] = 0
            return False


    def analyze(self):
        """Calls the method that creates a list of slices from the PCB.
         Each slice has the following format: ["xpos_ypos_direction", array_as_bytes].
         The x- and y-positions are not the positions from pcbnew but the positions in the
         rasterized array. The direction is either 0 or 1 where 0 stands for "in x-direction"
         and 1 for "in y-direction". The bytes representing the array have to be reconstructed
         using numpys frombuffer() method. Note that the arrays original shape is not encoded in
         each slice and has to be inferred from the "slice_x" and "slice_y" preferences used while
         creating the slices. For further reference see the reconstructor.py file.
         Example slice: ['1204_1721_0', '\x00\x00\x00\x01\x01\x01']
        """
        print("maybe starting server here")
        if self.maybe_start_anopcb_server():
            # wait for the server to boot
            time.sleep(6)

        if self.server_api.is_busy():
            dia = wx.MessageDialog(
                parent=self.gui,
                message="The server can't be reached, is not listening on the chosen port or busy.",
                caption="Server not responding",
                style=wx.OK)
            dia.ShowModal()
            return
        if self.server_api.get_active_model()["data"][0] is None:
            dia = wx.MessageDialog(
                parent=self.gui,
                message="No machine learning model is active, choose one under 'model configuration'!",
                caption="No active model.",
                style=wx.OK)
            dia.ShowModal()
            return
        if self.get_preference("slice_y") > pcbnew.GetBoard().GetCopperLayerCount():
            dia = wx.MessageDialog(
                parent=self.gui,
                message=f"Reduce Slice Y. The board only has {pcbnew.GetBoard().GetCopperLayerCount()} layers. ",
                caption="Bad Slice Y",
                style=wx.OK)
            dia.ShowModal()
            return
        slices = self.create_slices_mp()
        layers = slices[0]
        slices = slices[1]
        send_slices = [y.decode("utf-8") for x, y in slices]

        # Dump slices here
        if self.get_preference("save_filter_data"):
            print("dumping slices")
            with open(self.anopcb_filter_slices_path, "w") as f:
                save_slices = [(x, y.decode("utf-8")) for x, y in slices]
                json.dump(save_slices, f)
                del save_slices

        def get_slice_position(slice_meta):
            splitted = slice_meta.split("_")
            return (int(splitted[0]), int(splitted[1]))
        slice_positions = [get_slice_position(slice[0]) for slice in slices]
        del slices

        # dump layers for debugging results dialog
        if self.get_preference("save_filter_data"):
            print("dumping layers")
            layers_to_json = layers.tolist()
            with open(self.anopcb_filter_layers_path, "w") as layers_json:
                json.dump(layers_to_json, layers_json)
                del layers_to_json

        while self.server_api.is_busy():
            dia = wx.MessageDialog(
                parent=self.gui,
                message="The server can't be reached, is not listening on the chosen port or busy. Wait 10 seconds?",
                caption="Server not responding",
                style=wx.OK | wx.CANCEL | wx.OK_DEFAULT)
            if dia.ShowModal() == wx.ID_OK:
                time.sleep(10)
            else:
                return

        print("sending slices to server and wait")
        resp = self.server_api.evaluate(
            send_slices,
            (self.get_preference("slice_x"), self.get_preference("slice_y")))
        if resp is not False:
            resp = resp["data"]
        else:
            print("An Error occured. Check server log for more information.")
            return

        del send_slices

        # add date to results
        results_date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        resp.append(results_date)
        # dumping results
        if self.get_preference("save_filter_data"):
            print("dumping results")
            with open(self.anopcb_filter_results_path, "w") as f:
                json.dump(resp, f)

        ShowResultsDialog(self.gui, self, layers, slice_positions, resp).Show()


    def create_slices_mp(self):
        """ Calls the "createSlicesMP" method.

        Returns:
            list: A list of slices as byte object.
             Contain no information about the slice dimensions (reshape in plugin).
        """
        return createSlicesMP(self)


    def cluster_results(self, latent_vectors, mse_list, cluster_size, threshold, cluster_alg):
        """Clusters the latent vectors with K-Means.

        Args:
            latent_vectors (List): The slices compressed by the autoencoder in the server.
            mse_list (List): The mean squared errors of the slices.
            cluster_size (int): The amount of cluster to create.
            threshold (int): The minimum error amount to be considered.

        Returns:
            (List): The cluster indices of all slices in order.
             Only slices passing the threshold considered!
        """
        latent_vectors = [latent_vector for latent_vector, mse in zip(latent_vectors, mse_list) if mse >= threshold]
        if cluster_alg == ShowResultsDialog.Cluster_Alg.KMEANS:
            return sklearn.cluster.KMeans(
                n_clusters=cluster_size,
                max_iter=550).fit_predict(np.array(latent_vectors))
        elif cluster_alg == ShowResultsDialog.Cluster_Alg.DBSCAN:
            clustering = [i + 1 for i in sklearn.cluster.DBSCAN(n_jobs=-1).fit_predict(latent_vectors)] # clustering returns indices starting from -1
            return clustering
        elif cluster_alg == ShowResultsDialog.Cluster_Alg.OPTICS:
            clustering = [i + 1 for i in sklearn.cluster.OPTICS(max_eps=400, n_jobs=-1).fit_predict(latent_vectors)] # clustering returns indices starting from -1
            return clustering



    def Run(self):
        """
        Starts when clicking the plugin in pcbnews menu.
         Creates the gui and calls the initialize method.
        """
        pcbnew_frame = list(filter(
            lambda w: w.GetTitle().startswith('Pcbnew'),
            wx.GetTopLevelWindows()))[0]
        pcbnew_manager = wx.aui.AuiManager.GetManager(pcbnew_frame)
        pane = wx.aui.AuiPaneInfo()                     \
                 .Caption(u"AnoPCB")                  \
                 .Float()                               \
                 .FloatingPosition(wx.Point(346, 268))  \
                 .FloatingSize(wx.Size(300, 300))       \
                 .MinSize(wx.Size(44, 36))            \
                 .Layer(0).Center()
        self.gui = TrackGUI(pcbnew_frame, self)
        pcbnew_manager.AddPane(self.gui, pane)
        pcbnew_manager.Update()
        self.gui.resize()

        # initialize here, as the Board is not yet available from default at bootup
        self.initiliaze()