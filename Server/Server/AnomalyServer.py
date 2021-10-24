"""The module containing the ML-Server. Can be run to start
 the server, expects a port as argument."""
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import base64
from tensorflow import keras
from threading import Thread
import os
import tensorflow as tf
from sys import argv
import numpy as np
from numba import njit, prange
from numba.typed import List
from threading import Lock
from threading import Thread
import random
import shutil


SAVED_MODEL_FORMAT = "h5"
IP = "0.0.0.0"
NR_CHANNELS = 8
SAMPLES_PER_BATCH = 5000
PATIENCE_MAX = 5


@njit(parallel=True)
def reshape_array(restored, new_shape, shape):
    """Reshapes the 2D array restored into a 3D array.
     each entry in the original array is turned into a one-hot vector.

    Args:
        restored (2D byte-Array): The original array
        new_shape (Tuple[int, int, int]): The shape of the output array
        shape (Tuple[int, int]): The shape of the original array

    Returns:
        3D byte-Array: The one-hot representation of the original array
    """
    reshaped = np.zeros((len(restored), new_shape[0], new_shape[1], new_shape[2]), np.uint8)
    for i in prange(len(restored)):
        for j in range(shape[0]):
            for k in range(shape[1]):
                v = restored[i][j][k]
                reshaped[i][j][k][v-1] = 1 if v != 0 else 0
    return reshaped


class AnomalyHandler(BaseHTTPRequestHandler):
    """The http-Handler handling the requests to the server. Expects requests according to the REST
     interface specified in the "REST definition.txt" and sends responses accordingly.
    """
    def save_model(self, model_name, data, kind, comp):
        """Compiles and saves the model with the configuration specified in "data"
         under the name "model_name" using compile parameters in "comp".

        Args:
            model_name (string): name to save the model under
            data (string): configuration of the model
            comp (dictionary): dictionary with compile parameters

        Returns:
            boolean: True if successfull, else False
        """
        try:
            if os.path.split(os.getcwd())[1] == "Server" or os.path.split(os.getcwd())[1] == "anopcb-server":
                os.chdir("models")
            if os.path.split(os.getcwd())[1] == "datasets":
                os.chdir("../models")
            if kind == "json":
                model = tf.keras.models.model_from_json(data)
                model.compile(
                    optimizer=comp.get("optimizer"),
                    loss=[comp.get("loss"), None, None],
                    metrics=comp.get("metrics"),
                    loss_weights=[1.0, 0.0, 0.0]
                    )
                model.save(f"{model_name}.{SAVED_MODEL_FORMAT}", save_format='h5')
                return True
            elif kind == "h5":
                data = base64.b64decode(data)
                with open(f"{model_name}.{SAVED_MODEL_FORMAT}", "wb") as f:
                    f.write(data)
                return True
            else:
                return False
        except KeyError as e:
            print("Encountered Error: ", e.args)
            return False
        except TypeError as e:
            print("Encountered Error: ", e.args)
            return False
        except IOError as e:
            print("Encountered Error: ", e.args)
            return False
        except ValueError as e:
            print("Encountered Error: ", e.args)
            return False


    def add_to_dict(self, key, value, d, res):
        """adds the hashed Data to an Dictionary to remove Duples

        Args:
            key (int): hashed Data - eventuell unnötig, wenn man einfach in der funktion selbst hashed, stattdessen hash(value)
            value (str): Single Value of the Data 
            d (dict): Dictionary 
            res (list): final List without duplicates

        Returns:
            boolean: always True because it works in the reference of res
        """
        if not (key in d):
            d.update({key:[value]})
            res.append(value)
        elif value in d.get(key):
            return True
        else:
            d.get(key).append(value)
            res.append(value)
        return True
    
    def flip_data(self, data, shape):
        """Flips the dataset in x, y and x and y direction. 

        Args:
            data (List): a list of slices
            shape (set): shape[0] = x_dim, shape[1] = y_dim

        Returns:
            list: list with all Flipped slices
        """
        restored = np.array([np.frombuffer(a.encode(), np.uint8).reshape(shape) for a in data])
        #restored_0 = np.flip(restored, 0) <- doesn't work, returns nonsense
        restored_y = np.flip(restored, 1) #y-direction
        restored_x = np.flip(restored, 2) #x-direction
        restored_xy = np.flip(restored_y, 2) #x-y-direction
        res = []
        

        for i in restored_xy:
            b = i.flatten().tobytes()
            b_decoded = b.decode("utf-8", 'strict') # strict throws an error, if it fails. I wanna make sure, that'll be corect
            res.append(b_decoded)
        for i in restored_y:
            b = i.flatten().tobytes()
            b_decoded=b.decode("utf-8", 'strict')
            res.append(b_decoded)
        for i in restored_x:
            b = i.flatten().tobytes()
            b_decoded = b.decode("utf-8", 'strict')
            res.append(b_decoded)

        return res


    def augment_data(self, data, shape):
        """augments the Data (removes Dubles and flips the slices)

        Args:
            data (List): a list of slices
            shape (set): shape[0] = x_dim, shape[1] = y_dim

        Returns:
            list: List of augmented Data
        """
        d = dict()
        res = []
        for i in data:
            self.add_to_dict(hash(i), i, d, res)
        
        res = self.flip_data(res, shape)
        return res


    def save_data(self, data, name, count, x_dim, y_dim, augment):
        """Saves the dataset. The saved datasets name is as follows:
         "name_count_xdim_ydim.json"

        Args:
            data (List): a list of slices
            name (str): name of the board
            count (str): number of slices
            x_dim (str): length of slice in x-dimension
            y_dim (str): length of slice in y-dimension
            augment (bool): whether the data should be augmented

        Returns:
            boolean: True if successfull, else False
        """
        try:
            if os.path.split(os.getcwd())[1] == "Server" or os.path.split(os.getcwd())[1] == "anopcb-server":
                os.chdir("datasets")
            if os.path.split(os.getcwd())[1] == "models":
                os.chdir("../datasets")
            if augment:
                data = self.augment_data(data, (int(x_dim), int(y_dim)))
                count = str(len(data))
                print("Data Augmentation successful")

                with open(f"{name}_{count}_{x_dim}_{y_dim}_a.json", "w") as f:
                    json.dump(data, f)
            else:
                with open(f"{name}_{count}_{x_dim}_{y_dim}.json", "w") as f:
                    json.dump(data, f)
            return True
        except IOError as e:
            print("Encountered Error: ", e.args)
            return False


    def delete_data(self, name):
        """Deletes the dataset with name "name".

        Args:
            name (str): name of a dataset

        Returns:
            boolean: True if successfull, else False
        """
        try:
            if os.path.split(os.getcwd())[1] == "Server" or os.path.split(os.getcwd())[1] == "anopcb-server":
                os.chdir("datasets")
            if os.path.split(os.getcwd())[1] == "models":
                os.chdir("../datasets")    
            os.remove(f"{name}.json")
            return True
        except IOError as e:
            print("Encountered Error: ", e.args)
            return False


    def delete_model(self, name):
        """Deletes the model with name "name", except when it is currently active.

        Args:
            name (str): name of a model

        Returns:
            boolean: True if successfull, else False
        """
        try:
            with self.server.session_lock:
                if os.path.split(os.getcwd())[1] == "Server" or os.path.split(os.getcwd())[1] == "anopcb-server":
                    os.chdir("models")
                if os.path.split(os.getcwd())[1] == "datasets":
                    os.chdir("../models")
                if name in list(map(lambda x: x[0][0], self.server.sessions.values())):
                    return False
                else:
                    os.remove(f"{name}.{SAVED_MODEL_FORMAT}")
                    return True
        except IOError as e:
            print("Encountered Error: ", e.args)
            return False

    def get_session(self):
        tmp = self.server.session_counter
        self.server.session_counter += 1
        self.server.sessions[tmp] = [[None, None], int(time.time()), False]
        return tmp

    def remove_session(self, session):
        with self.server.session_lock:
            try:
                self.server.sessions.pop(session)
            except Exception:
                pass
            return True

    def get_data(self):
        """Gets the names of all available datasets.

        Returns:
            List: names of datasets
        """
        if os.path.split(os.getcwd())[1] == "Server" or os.path.split(os.getcwd())[1] == "anopcb-server":
            os.chdir("datasets")
        if os.path.split(os.getcwd())[1] == "models":
            os.chdir("../datasets")
        datasets = os.listdir()
        datasets = [os.path.splitext(x)[0] for x in datasets]
        return datasets


    def get_model(self, name):
        """Loads the model with name "name"

        Args:
            name (string): name of model

        Returns:
            model: tensorflow model
        """        
        if os.path.split(os.getcwd())[1] == "Server" or os.path.split(os.getcwd())[1] == "anopcb-server":
            os.chdir("models")
        if os.path.split(os.getcwd())[1] == "datasets":
            os.chdir("../models")
        model = tf.keras.models.load_model(f"{name}.{SAVED_MODEL_FORMAT}")
        return model


    def get_available_models(self):
        """Gets the currently available models.

        Returns:
            list: names of available models
        """        
        if os.path.split(os.getcwd())[1] == "Server" or os.path.split(os.getcwd())[1] == "anopcb-server":
            os.chdir("models")
        if os.path.split(os.getcwd())[1] == "datasets":
            os.chdir("../models")
        files = [os.path.splitext(x)[0] for x in os.listdir() if os.path.splitext(x)[1] == f".{SAVED_MODEL_FORMAT}"]
        return files


    def set_active_model(self, model_name, session):
        """Sets the currently active model.

        Args:
            model_name (string): name of the model

        Returns:
            boolean: True if successfull, else False
        """        
        self.update_session_time(session)
        try:
            model = self.get_model(model_name)
        except ValueError as e:
            print("Encountered Error: ", e.args)
            return False
        except ImportError as e:
            print("Encountered Error: ", e.args)
            return False
        except IOError as e:
            print("Encountered Error: ", e.args)
            return False
        with self.server.session_lock:
            if list(filter(lambda x: x[0][0]==model_name and x[2], self.server.sessions.values())) != []:
                return False
            try:
                mod_ses = self.server.sessions[session]
            except:
                mod_ses = [None, int(time.time()), False]
            mod_ses[0] = [model_name, model]
            self.server.sessions[session] = mod_ses
            return True


    def get_active_model(self, session):
        """Gets the currently active model.

        Returns:
            tuple: name and config of active model
        """     
        self.update_session_time(session)
        with self.server.session_lock:   
            conf = self.server.sessions[session][0][1] if session in self.server.sessions.keys() else None
            if conf != None:
                conf = conf.to_json()
            name = self.server.sessions[session][0][0] if session in self.server.sessions.keys() else None
            return (name, conf)


    def load_data(self, datasets, batch_size):
        """Loads a batch of size batch_size with random samples from datasets.

        Args:
            datasets (list): List of dataset names
            batch_size (int): batch size

        Returns:
            Result: data as numpy array if successful, else False
        """
        if os.path.split(os.getcwd())[1] == "Server" or os.path.split(os.getcwd())[1] == "anopcb-server":
            os.chdir("datasets")
        if os.path.split(os.getcwd())[1] == "models":
            os.chdir("../datasets")

        shapes = set()
        for name in datasets:
            split = name.split("_")
            shapes.add((int(split[2]), int(split[3])))
        if len(shapes) != 1:
            return False
        shape = shapes.pop()

        slices = []
        for name in datasets:
            with open(f"{name}.json", "r") as f:
                slices += json.load(f)
        restored = np.array([np.frombuffer(a.encode(), np.uint8).reshape(shape) for a in slices])
        new_shape = (shape[0], shape[1], NR_CHANNELS)
        if not (batch_size < 1 or batch_size > len(slices)):
            indices = np.random.choice(len(restored), batch_size, replace=False)
            restored = restored[indices]
        return reshape_array(restored, new_shape, shape)


    def reconstruct(self, data, shape):
        """Converts "data". which is a string representation of the slice data and converts
         it back to a numpy array.

        Args:
            data (list): list of slices
            shape (tuple): shape[0] = x-size, shape[1] = y-size of slice

        Returns:
            array: correctly formatted input array for the ML model
        """
        restored = np.array([np.frombuffer(a.encode(), np.uint8).reshape(shape) for a in data])
        new_shape = (shape[0], shape[1], NR_CHANNELS)
        return reshape_array(restored, new_shape, shape)


    def test(self, datasets, batch_size, session):
        """Evaluates the model on batch of size batch_size of random samples
         from datasets.

        Args:
            datasets (list): List of dataset names
            batch_size (int): batch size

        Returns:
            Loss: Loss as Integer if successful, else False
        """
        self.update_session_time(session)
        with self.server.session_lock:
            active_model_name = self.server.sessions[session][0][0] if session in self.server.sessions.keys() else None
            active_model = self.server.sessions[session][0][1] if session in self.server.sessions.keys() else None

            if list(filter(lambda x: x[0][0]==active_model_name and x[2], self.server.sessions.values())) != []:
                return False
            
            if active_model is None:
                print("No active ML-Model!")
                return False
            data = self.load_data(datasets, batch_size)
            if data is False:
                return False
            try:
                loss = active_model.evaluate(data, data)[0]
                return float(loss)
            except ValueError as e:
                print("Encountered Error: ", e.args)
                return False
            except Exception as e:
                print("Encountered Error: ", e.args)
                return False


    def evaluate(self, data, shape, session):
        """Evaluates "data" with shape "shape" on the currently active model.

        Args:
            data (list): list of slices
            shape (tuple): shape[0] = x-size, shape[1] = y-size of slice

        Returns:
            metrics: list [loss, mse, encoded vector]
        """
        self.update_session_time(session)
        with self.server.session_lock:
            active_model_name = self.server.sessions[session][0][0] if session in self.server.sessions.keys() else None
            active_model = self.server.sessions[session][0][1] if session in self.server.sessions.keys() else None

            if list(filter(lambda x: x[0][0]==active_model_name and x[2], self.server.sessions.values())) != []:
                return False
            
            if active_model is None:
                print("No active ML-Model!")
                return False
            if active_model.input.shape[1:3] != shape:
                print(f"Shape {shape} of slices does not match model input {active_model.input.shape}!")
                return False
            try:
                inp = self.reconstruct(data, shape)
                predicts = active_model.predict(inp)
                # loss not needed in current implementation
                return ["dummy", predicts[2].tolist(), predicts[1].tolist()]
            except ValueError as e:
                print("Encountered Error: ", e.args)
                return False
            except Exception as e:
                print("Encountered Error: ", e.args)
                return False


    def update_session_time(self, session):
        try:
            self.server.session[session][1] = int(time.time())
        except Exception:
            pass

    def new_train(self, datasets, batch_size, train_time, session):
        """Trains and validates the model on datasets. If datasets for training and validation
         are the same, they will be split. If the batch size for training is chosen
         larger than the size of the datasets, no data will be used for validation (bad).
         The model will train for train_time[1] epochs. One epoch means training
         on SAMPLES_PER_BATCH (5000 per default) samples, then validating. If the validation loss rises for 5 epochs in
         succession, the training is stopped (overfitting). Otherwise the training will be stopped
         after train_time[0] minutes or train_time[1] epochs.

        Args:
            datasets (Tuple[List, List]): Tuple of lists of dataset names. One for training, one for validation.
            batch_size (Tuple[int, int]): Tuple of batch sizes. One for training, one for validation.
            train_time (Tuple[int, int]): Tuple of train times. One in minutes, one in epochs.

        Returns:
            metrics: List of Tuples[loss, validation loss] if successful, else False
        """
        self.update_session_time(session)
        with self.server.session_lock:
            active_model_name = self.server.sessions[session][0][0] if session in self.server.sessions.keys() else None
            active_model = self.server.sessions[session][0][1] if session in self.server.sessions.keys() else None
            
            if list(filter(lambda x: x[0][0]==active_model_name and x[2], self.server.sessions.values())) != []:
                return False
            self.server.sessions[session][2] = True
            try:
                if active_model is None:
                    print("No active ML-Model!")
                    return False
                try:
                    train_datasets = datasets[0]
                    val_datasets = datasets[1]
                    train_batch_size = batch_size[0]
                    val_batch_size = batch_size[1]
                    train_min = train_time[0] if train_time[0] > 0 else 1000000
                    train_ep = train_time[1] if train_time[1] > 0 else 1000000000

                    if train_datasets == val_datasets:
                        data = self.load_data(train_datasets, 0)
                        if data is False:
                            return False
                        ind = np.random.choice(len(data), len(data), replace=False)
                        b1 = train_batch_size if train_batch_size > 0 and train_batch_size < len(data) else len(data)
                        b2 = b1 + val_batch_size if b1 + val_batch_size < len(data) else len(data)
                        ind1 = ind[0:b1]
                        ind2 = ind[b1:b2]
                        train_data = data[ind1]
                        val_data = data[ind2]
                    else:
                        train_data = self.load_data(train_datasets, train_batch_size)
                        val_data = self.load_data(val_datasets, val_batch_size)
                        if train_data is False or val_data is False:
                            return False

                    patience = 0
                    lastloss = float("inf")
                    noval = len(val_data) == 0
                    start = time.time()
                    metrics = []
                    for epi in range(train_ep):
                        print(f"Epoch {epi} of {train_ep}.")
                        sample = train_data[np.random.choice(len(train_data), SAMPLES_PER_BATCH, replace=False)]
                        if noval:
                            hs = active_model.fit(
                                x=sample,
                                y=sample).history
                            loss = hs["loss"][-1]
                            metrics.append((str(loss), "0"))
                        else:
                            val_sample = val_data[np.random.choice(len(val_data), SAMPLES_PER_BATCH, replace=False)]
                            hs = active_model.fit(
                                x=sample,
                                y=sample).history
                            loss = hs["loss"][-1]
                            val_loss = active_model.evaluate(
                                x=val_sample,
                                y=val_sample)[0]
                            metrics.append((str(loss), str(val_loss)))
                            if val_loss > lastloss:
                                patience += 1
                            else:
                                patience = 0
                            if patience == PATIENCE_MAX:
                                break
                            lastloss = val_loss
                        now = time.time()
                        if now - start > train_min*60:
                            break
                    if os.path.split(os.getcwd())[1] == "Server" or os.path.split(os.getcwd())[1] == "anopcb-server":
                        os.chdir("models")
                    return metrics
                except ValueError as e:
                    print("Encountered ValueError: ", e.args)
                    return False
                except IOError as e:
                    print("Encountered IOError: ", e.args)
                    return False
                except Exception as e:
                    print("Encountered Error: ", e.args)
                    return False
            finally:
                self.server.sessions[session][2] = False


    def train(self, data, shape, fit):
        """(DEPRECATED) Trains the currently active model on "data" with shape "shape" using
         parameters in "fit".

        Args:
            data (list): list of slices
            shape (tuple): shape[0] = x-size, shape[1] = y-size of slice
            fit (dictionary): A dictionary with fit parameters.

        Returns:
            metrics: training summary if successfull, else False
        """
        if self.server.active_model is None:
            print("No active ML-Model!")
            return False    
        try:
            inp = self.reconstruct(data, shape)
            metrics = self.server.active_model.fit(
                x=inp, 
                y=inp, 
                batch_size=fit.get("batch_size"), 
                epochs=fit.get("epochs") if fit.get("epochs") is not None else 1, 
                shuffle=fit.get("shuffle") if fit.get("shuffle") is not None else True
            )
            if os.path.split(os.getcwd())[1] == "Server" or os.path.split(os.getcwd())[1] == "anopcb-server":
                os.chdir("models")
            if os.path.split(os.getcwd())[1] == "datasets":
                os.chdir("../models")
            self.server.active_model.save(f"{self.server.active_model_name}.{SAVED_MODEL_FORMAT}", save_format='h5')
            for met in metrics.history:
                vals = metrics.history[met]
                for i in range(len(vals)):
                    vals[i] = str(vals[i])
            return metrics.history
        except ValueError as e:
            print("Encountered Error: ", e.args)
            return False
        except IOError as e:
            print("Encountered Error: ", e.args)
            return False
        except Exception as e:
            print("Encountered Error: ", e.args)
            return False


    def send_bad_response(self):
        """Sends a http 400 response.
        """   
        self.send_response(400)
        self.end_headers()


    def do_GET(self):
        """Handles GET-requests.
        """
        length = int(self.headers['Content-Length'])
        payload_raw = self.rfile.read(length)
        payload = json.loads(payload_raw)
        if payload.get("type") is None:
            self.send_bad_response()
        elif payload["type"] == 1:
            models = self.get_available_models()
            resp = {"data" : models}
            resp = json.dumps(resp).encode()
            self.send_response(200)
            self.send_header("Content-Type", "json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        elif payload["type"] == 5:
            if payload.get("session") is not None:
                session = payload["session"]
                model = self.get_active_model(session)
                resp = {"data" : model}
                resp = json.dumps(resp).encode()
                self.send_response(200)
                self.send_header("Content-Type", "json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            else:
                self.send_bad_response()
        elif payload["type"] == 6:
            self.send_response(204)
            self.end_headers()
        elif payload["type"] == 10:
            datasets = self.get_data()
            resp = {"data" : datasets}
            resp = json.dumps(resp).encode()
            self.send_response(200)
            self.send_header("Content-Type", "json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_bad_response()


    def do_POST(self):
        """Handles POST-requests.
        """
        length = int(self.headers['Content-Length'])
        payload_raw = self.rfile.read(length)
        payload = json.loads(payload_raw)
        if payload.get("type") is None:
            self.send_bad_response()
        elif payload["type"] == 2:
            if payload.get("datasets") is not None and payload.get("batch_size") is not None and payload.get("train_time") is not None and payload.get("session") is not None:
                datasets = payload["datasets"]
                batch_size = payload["batch_size"]
                train_time = payload["train_time"]
                session = payload["session"]
                resp = self.new_train(datasets, batch_size, train_time, session)
                if resp != False:
                    resp = {"data" : resp}
                    resp = json.dumps(resp).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "json")
                    self.send_header("Content-Length", str(len(resp)))
                    self.end_headers()
                    self.wfile.write(resp)
                else:
                    self.send_bad_response()
            else:
                self.send_bad_response()
        elif payload["type"] == 3:
            if payload.get("data") is not None and payload.get("shape") is not None and payload.get("session") is not None:
                data = payload["data"]
                shape = payload["shape"]
                session = payload["session"]
                resp = self.evaluate(data, shape, session)
                if resp != False:
                    resp = {"data" : resp}
                    resp = json.dumps(resp).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "json")
                    self.send_header("Content-Length", str(len(resp)))
                    self.end_headers()
                    self.wfile.write(resp)
                else:
                    self.send_bad_response()
            else:
                self.send_bad_response()
        elif payload["type"] == 4:
            if payload.get("model") is not None and payload.get("session") is not None:
                model = payload["model"]
                session = payload["session"]
                if self.set_active_model(model, session):
                    self.send_response(204)
                    self.end_headers()
                else:
                    self.send_bad_response()
            else:
                self.send_bad_response()
        elif payload["type"] == 11:
            if payload.get("datasets") is not None and payload.get("batch_size") is not None and payload.get("session") is not None:
                datasets = payload["datasets"]
                batch_size = payload["batch_size"]
                session = payload["session"]
                resp = self.test(datasets, batch_size, session)
                if resp != False:
                    resp = {"data" : resp}
                    resp = json.dumps(resp).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "json")
                    self.send_header("Content-Length", str(len(resp)))
                    self.end_headers()
                    self.wfile.write(resp)
                else:
                    self.send_bad_response()
            else:
                self.send_bad_response()
        elif payload["type"] == 12:
            resp = self.get_session()
            if resp != False:
                resp = {"data" : resp}
                resp = json.dumps(resp).encode()
                self.send_response(200)
                self.send_header("Content-Type", "json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            else:
                self.send_bad_response()
        else:
            self.send_bad_response()


    def do_PUT(self):
        """Handles PUT-requests.
        """
        length = int(self.headers['Content-Length'])
        payload_raw = self.rfile.read(length)
        payload = json.loads(payload_raw)
        if payload.get("type") is None:
            self.send_bad_response()
        elif payload["type"] == 0:
            if payload.get("data") is not None and payload.get("model") is not None and payload.get("comp") is not None and payload.get("kind") is not None:
                data = payload["data"]
                model = payload["model"]
                comp = payload["comp"]
                kind = payload["kind"]
                if self.save_model(model, data, kind, comp):
                    self.send_response(204)
                    self.end_headers()
                else:
                    self.send_response(500)
                    self.end_headers()
            else:
                self.send_bad_response()
        elif payload["type"] == 7:
            if payload.get("model") is not None:
                name = payload["model"]
                if self.delete_model(name):
                    self.send_response(204)
                    self.end_headers()
                else:
                    self.send_response(500)
                    self.end_headers()
            else:
                self.send_bad_response()
        elif payload["type"] == 8:
            if payload.get("data") is not None and payload.get("board") is not None and payload.get("count") is not None and payload.get("x_dim") is not None and payload.get("y_dim") is not None and payload.get("aug") is not None:
                data = payload["data"]
                name = payload["board"]
                count = payload["count"]
                x_dim = payload["x_dim"]
                y_dim = payload["y_dim"]
                augment = payload["aug"]
                if self.save_data(data, name, count, x_dim, y_dim, augment):
                    self.send_response(204)
                    self.end_headers()
                else:
                    self.send_response(500)
                    self.end_headers()
            else:
                self.send_bad_response()
        elif payload["type"] == 9:
            if payload.get("board") is not None:
                name = payload["board"]
                if self.delete_data(name):
                    self.send_response(204)
                    self.end_headers()
                else:
                    self.send_response(500)
                    self.end_headers()
            else:
                self.send_bad_response()
        elif payload["type"] == 13:
            if payload.get("session") is not None:
                session = payload["session"]
                if self.remove_session(session):
                    self.send_response(204)
                    self.end_headers()
                else:
                    self.send_response(500)
                    self.end_headers()
            else:
                self.send_bad_response()
        else:
            self.send_bad_response()


class BaseServer(HTTPServer):
    """Subclass of HTTPServer modified to provide a ML-Model to be accesed by the http-Handler.
    """
    def __init__(self, adress, handler):
        """Initializes the BaseServer.

        Args:
            adress (Tuple): The IP-Adress and port of the server.
            handler (BaseHTTPRequestHandler): The handler of the server.
        """
        super().__init__(adress, handler)

        # session -> ((model_name, active_model), timeout_timestamp, train_lock)
        self.sessions = dict()
        self.session_lock = Lock()
        self.session_counter = random.randint(2, 10000)

        timer = Thread(target=self.scheduled_dead_session_check)
        timer.setDaemon(True)
        timer.start()
    
    def scheduled_dead_session_check(self):
        while True:
            with self.session_lock:
                tmp = []
                cur_time = int(time.time())
                for x in self.sessions.keys():
                    if self.sessions[x][1] + 30*60 < cur_time:
                        tmp.append(x)
                for x in tmp:
                    self.sessions.pop(x)
            time.sleep(60)


class MainServer:
    """The Main Server class. Can be started with "start" method and stopped with the "close" method.
     Is automatically started if the module is run.
    """    
    def __init__(self, port, ip_override):
        """Initializes the main server.

        Args:
            port (int): The port of the server.
            ip_override (string): The IP-Address of the server.
        """
        self._server = BaseServer((ip_override, port), AnomalyHandler)
        self._thread = None

    def start(self):
        """Used to start the server."""
        if self._thread is None:
            self._thread = Thread(target=self._server.serve_forever)
        self._thread.deamon = True
        self._thread.start()

    def close(self):
        """Used to stop the server."""
        self._server.shutdown()
        self._thread = None

def main(port, ip_override=IP, save_local=False):
    if not save_local:
        if os.name == 'nt':
            # windows
            project_path = r'%APPDATA%\.anopcb'
            project_path = os.path.expandvars(project_path)
        elif os.name == 'posix':
            # linux
            project_path = '~/.anopcb/'
            project_path = os.path.expanduser(project_path)
        else:
            print("Not compatible OS detected. Please use windows or linux.")
            return
        project_path_2 = os.path.join(project_path, 'anopcb-server')
        try:
            os.mkdir(project_path)
            # if this passes, no data was put in place yet
            os.mkdir(project_path_2)
            datasets_path = os.path.join(project_path_2, 'datasets')
            os.mkdir(datasets_path)
            models_path = os.path.join(project_path_2, 'models')
            os.mkdir(models_path)
            package_path = os.path.split(__file__)[0]
            for filename in os.scandir(os.path.join(package_path, 'datasets')):
                shutil.copy2(filename.path, datasets_path)
            for filename in os.scandir(os.path.join(package_path, 'models')):
                shutil.copy2(filename.path, models_path)
        except Exception:
            pass
        os.chdir(project_path_2)
    main_server = MainServer(port, ip_override)
    main_server.start()
    print(f"Server serving at ({ip_override}, {port}{' local' if save_local else ''}).")

def main2():
    arguments = argv.copy()
    try:
        arguments.remove('--local')
        save_local = True
    except Exception:
        save_local = False
    
    if(len(arguments)==3):
        main(int(arguments[2]), arguments[1], save_local=save_local)
    elif(len(arguments)==2):
        main(int(arguments[1]), save_local=save_local)
    else:
        print("usage: <programm name> <port> | <programm name> <ip-address> <port>")

if __name__ == "__main__":
    main2()