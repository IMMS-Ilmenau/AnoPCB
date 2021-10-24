"""Contains the Api for the ML-Server used by the plugin. Can also be used as a standalone.
The first call should always be "is_busy" to check wether the server is available."""

import json
from typing import List, Tuple
import requests
from requests.exceptions import ConnectionError


class ServerAPI:
    """
    The Api for the ML-Server used by the plugin. Can also be used as a standalone.
    The first call should always be "is_busy" to check wether the server is available.
    """

    def __init__(self, ip_adr: str, port: int):
        """Initializes the server connection details.

        Args:
            ip_adr (str): The IP-Adress.
            port (int): The port.
        """
        self.ip_adr = ip_adr
        self.port = port
        self.adress = f"http://{self.ip_adr}:{self.port}"
        self.model_name = None
        self.session = self.get_session()
        if self.session:
            self.session = self.session['data']


    def update_adress(self, ip_adr: str, port: int):
        """Updates the adress the api is connecting to.

        Arguments:
            ip_adr (int): IP
            port (int): Port
        """
        address = f"http://{ip_adr}:{port}"
        if self.adress==address:
            return
        
        try:
            self.remove_session()
        except:
            pass
        self.ip_adr = ip_adr
        self.port = port
        self.adress = address
        self.model_name = None
        self.session = self.get_session()
        if self.session:
            self.session = self.session['data']

    def check_session_local(self):
        if self.session:
            return True
        self.session = self.get_session()
        if self.session:
            self.session = self.session['data']
        return self.session
    
    def check_session_online(self):
        """After 30 minutes without session activity, the session is removed on the server. Tied to a server is a reserved model.
        A model may be reserved and used by multiple users at the same time. But model training is only possible, when the model is not reserved by any session.
        Vice-versa a model cannot be reserved if model training is in progress. Any api call with a session updates the timeout timestamp, so further api calls can be called without worry.
        If the session of a client is removed, the client will automatically get a new session and try to reserve the previously selected model.
        This function does so and has to be called prior to api calls using a session. Though this is entirely covered in the api and does not need to be considered outside this code-file.
        """
        if not self.model_name:
            return True
        if not self.get_active_model_straight()['data'][0]: # <- model_name or None
            # session lost the model
            # try to gain the model again
            return self.serve(self.model_name)
        return True

        

    def send_model(self, model: str, name: str, kind: str, comp: dict) -> bool:
        """Sends the model to the server. Since the model must be compiled first it requires
         a dictionary with compile parameters (does not accept kwargs),
         see https://www.tensorflow.org/api_docs/python/tf/keras/Model#compile
         for further reference. If the model was saved as a h5 file, comp can be an empty
         dictionary.

        Arguments:
            model (string): The models config as a json string.
            name (string): The models name.
            kind (string): The models kind (h5 or json)
            comp (dictionary): A dictionary with compile parameters.

        Returns:
            success: True if successfull, else False.
        """

        payload = {
            "type" : 0,
            "name" : "send_model",
            "model": name,
            "kind" : kind,
            "data" : model,
            "comp" : comp
        }
        try:
            res = requests.put(self.adress, data=json.dumps(payload))
            return res.status_code == 204
        except ConnectionError as error:
            print("Error: ", error.args)
            return False


    def send_slices(self, data: List[str], name: str, count: str, x_dim: str, y_dim: str, augment: bool) -> bool:
        """Sends a set of slices to the server.

        Args:
            data (List): list of slices
            name (str): the name of the board the slices were taken from
            count (str): the amount of slices
            x_dim (str): their length in the x-dimension
            y_dim (str): their length in the y-dimension
            augment (bool): whether the data should be augmented

        Returns:
            bool: True if successfull, else False.
        """
        payload = {
            "type" : 8,
            "name" : "send_slices",
            "board": name,
            "count": count,
            "x_dim": x_dim,
            "y_dim": y_dim,
            "aug"  : augment,
            "data" : data
        }
        try:
            res = requests.put(self.adress, data=json.dumps(payload))
            return res.status_code == 204
        except ConnectionError as error:
            print("Error: ", error.args)
            return False

    
    def delete_slices(self, name: str) -> bool:
        """Deletes dataset of slices with name "name".

        Args:
            name (str): name of dataset

        Returns:
            bool: True if successfull, else False.
        """
        payload = {
            "type" : 9,
            "name" : "delete_slices",
            "board": name
        }
        try:
            res = requests.put(self.adress, data=json.dumps(payload))
            return res.status_code == 204
        except ConnectionError as error:
            print("Error: ", error.args)
            return False


    def delete_model(self, name: str) -> bool:
        """Deletes the model with name "name".

        Arguments:
            name (string): The models name.

        Returns:
            success: True if successfull, else False.
        """

        payload = {
            "type" : 7,
            "name" : "delete_model",
            "model": name,
        }
        try:
            res = requests.put(self.adress, data=json.dumps(payload))
            return res.status_code == 204
        except ConnectionError as error:
            print("Error: ", error.args)
            return False


    def is_busy(self) -> bool:
        """The only request with a timeout (of 1 second) to test wether the server is available.

        Returns:
            success: True if the server is busy, else False.
        """
        payload = {
            "type" : 6,
            "name" : "busy"
        }
        try:
            requests.get(self.adress, data=json.dumps(payload), timeout=1)
            return False
        except requests.exceptions.Timeout as error:
            return True
        except ConnectionError as error:
            print("Error: ", error.args)
            return True


    def get_available_models(self):
        """Gets the available models from the server.

        Returns:
            models: List of models if successfull, else False.
        """
        payload = {
            "type" : 1,
            "name" : "models"
        }
        try:
            res = requests.get(self.adress, data=json.dumps(payload))
            if res.status_code == 200:
                return res.json()
            else:
                return False
        except ConnectionError as error:
            print("Error: ", error.args)
            return False


    def get_active_model(self):
        """Gets the currently active model from the server.

        Returns:
            model: Name of the currently active model if successfull, else False.
        """
        if not self.check_session_local():
            print("Error: no session")
            return False
        self.check_session_online() # only call it, whether it succeeds or not
        payload = {
            "type" : 5,
            "name" : "active",
            "session" : self.session
        }
        try:
            res = requests.get(self.adress, data=json.dumps(payload))
            if res.status_code == 200:
                return res.json()
            else:
                return False
        except ConnectionError as error:
            print("Error: ", error.args)
            return False

    def get_active_model_straight(self):
        """Gets the currently active model from the server, without considering session removals!

        Returns:
            model: Name of the currently active model if successfull, else False.
        """
        if not self.check_session_local():
            print("Error: no session")
            return False
        payload = {
            "type" : 5,
            "name" : "active",
            "session" : self.session
        }
        try:
            res = requests.get(self.adress, data=json.dumps(payload))
            if res.status_code == 200:
                return res.json()
            else:
                return False
        except ConnectionError as error:
            print("Error: ", error.args)
            return False

    def get_datasets(self):
        """Gets the available datasets from the server.

        Returns:
            datasets: list of datasets if successfull, else False.
        """
        payload = {
            "type" : 10,
            "name" : "get_data"
        }
        try:
            res = requests.get(self.adress, data=json.dumps(payload))
            if res.status_code == 200:
                return res.json()
            else:
                return False
        except ConnectionError as error:
            print("Error: ", error.args)
            return False


    def train(self, slices: List[str], shape: Tuple[int, int], fit: dict):
        """(DEPRECATED) Queries the currently active model with slices of shape "shape" for training.
         Requires a (possibly empty) dictionary containing the following optional arguments for
         tensorflows fit function: batch_size, epochs, shuffle. For further reference see
         https://www.tensorflow.org/api_docs/python/tf/keras/Model#fit.

        Arguments:
            slices (list): list of slices
            shape (tuple): shape[0] = x-size, shape[1] = y-size of slice
            fit (dictionary): A dictionary with fit parameters.

        Returns:
            metrics: training summary if successfull, else False
        """
        if not self.check_session_local():
            print("Error: no session")
            return False
        if not self.check_session_online():
            print("Error: Old model couldn't be served again, please manually serve a model again")
            return False
        payload = {
            "type" : 2,
            "name" : "train",
            "data" : slices,
            "shape": shape,
            "fit"  : fit
        }
        try:
            res = requests.post(self.adress, data=json.dumps(payload))
            if res.status_code == 200:
                return res.json()
            else:
                return False
        except ConnectionError as error:
            print("Error: ", error.args)
            return False


    def new_train(self, datasets: Tuple[List[str], List[str]], batch_size: Tuple[int, int], train_time: Tuple[int, int]):
        """Queries the server to train and validate the currently active
         model on selected datasets until the model overfits or the
         maximum training time is reached.

        Args:
            datasets (Tuple[List[str], List[str]]): Lists of dataset-names for training and validation
            batch_size (Tuple[int, int]): the total amount of samples selected from the respective datasets
            train_time (Tuple[int, int]): maximum train time in minutes and epochs

        Returns:
            metrics: training summary if successfull, else False
        """
        if not self.check_session_local():
            print("Error: no session")
            return False
        if not self.check_session_online():
            print("Error: Old model couldn't be served again, please manually serve a model again")
            return False
        payload = {
            "type" : 2,
            "name" : "train",
            "datasets"  : datasets,
            "batch_size": batch_size,
            "train_time": train_time,
            "session" : self.session
        }
        try:
            res = requests.post(self.adress, data=json.dumps(payload))
            if res.status_code == 200:
                return res.json()
            else:
                return False
        except ConnectionError as error:
            print("Error: ", error.args)
            return False


    def test(self, datasets: List[str], batch_size: int):
        """Queries the server tp evaluate the currently active model on the
         selected datasets.

        Args:
            datasets (List[str]): list of dataset-names
            batch_size (int): the total amount of samples selected from the datasets

        Returns:
            metrics: evaluation summary if successfull, else False
        """
        if not self.check_session_local():
            print("Error: no session")
            return False
        if not self.check_session_online():
            print("Error: Old model couldn't be served again, please manually serve a model again")
            return False
        payload = {
            "type" : 11,
            "name" : "test",
            "datasets"  : datasets,
            "batch_size": batch_size,
            "session" : self.session
        }
        try:
            res = requests.post(self.adress, data=json.dumps(payload))
            if res.status_code == 200:
                return res.json()
            else:
                return False
        except ConnectionError as error:
            print("Error: ", error.args)
            return False


    def evaluate(self, slices: List[str], shape: Tuple[int, int]):
        """Queries the currently active model with slices of shape "shape" for evaluation.
         Slices is a list of string decoded byte representations of slices.

        Arguments:
            slices (list): list of slices
            shape (tuple): shape[0] = x-size, shape[1] = y-size of slice

        Returns:
            metrics: list [loss, mse, encoded vector]
        """
        if not self.check_session_local():
            print("Error: no session")
            return False
        if not self.check_session_online():
            print("Error: Old model couldn't be served again, please manually serve a model again")
            return False
        payload = {
            "type" : 3,
            "name" : "evaluate",
            "data" : slices,
            "shape": shape,
            "session" : self.session
        }
        try:
            res = requests.post(self.adress, data=json.dumps(payload))
            if res.status_code == 200:
                return res.json()
            else:
                return False
        except ConnectionError as error:
            print("Error: ", error.args)
            return False


    def serve(self, model_name: str) -> bool:
        """Instructs the server to serve the model with name "model_name"
         for training and evaluation.

        Arguments:
            model_name (string): The name of the model to be served.

        Returns:
            success: True if successfull else False.
        """
        if not self.check_session_local():
            print("Error: no session")
            return False
        payload = {
            "type" : 4,
            "name" : "serve",
            "model": model_name,
            "session" : self.session
        }
        try:
            res = requests.post(self.adress, data=json.dumps(payload))
            if res.status_code == 204:
                self.model_name = model_name
            return res.status_code == 204
        except ConnectionError as error:
            print("Error: ", error.args)
            return False

    def get_session(self):
        payload = {
            "type" : 12,
            "name" : "get_session"
        }
        try:
            res = requests.post(self.adress, data=json.dumps(payload))
            if res.status_code == 200:
                return res.json()
            else:
                return False
        except ConnectionError as error:
            print("Error: ", error.args)
            return False

    def remove_session(self):
        if not self.session:
            return True
        payload = {
            "type" : 13,
            "name" : "remove_session",
            "session" : self.session
        }
        try:
            res = requests.put(self.adress, data=json.dumps(payload))
            return res.status_code == 204
        except ConnectionError as error:
            print("Error: ", error.args)
            return False
    