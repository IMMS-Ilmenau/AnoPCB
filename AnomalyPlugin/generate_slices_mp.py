"""Method to generate slices from a PCB using multiprocessing"""
import sys
if __package__ is None or __package__ == "":
    sys.path.append("..")
import pcbnew
import numpy as np
from skimage import io as skio
from skimage import draw
import re
from AnomalyPlugin.wrappers import Track, Pad, Via, Net
from multiprocessing import RawArray, Pool, cpu_count
from ctypes import c_byte
from time import localtime, strftime
import json


var_dict = {}
def _worker_init(layers_raw, layers_shape, layercount, width, step_value, board_name, min_x, min_y):
    """Initializes the workers for multiprocessing."""
    var_dict["layers_raw"] = layers_raw
    var_dict["layers_shape"] = layers_shape
    var_dict["layercount"] = layercount
    var_dict["width"] = width
    var_dict["step_value"] = step_value
    var_dict["board_name"] = board_name
    var_dict["min_x"] = min_x
    var_dict["min_y"] = min_y


def _slice_track(start, stop):
    """Slices all tracks in pcbnews TrackList from start to stop"""
    slices = []
    layers = np.frombuffer(var_dict["layers_raw"], np.uint8).reshape(var_dict["layers_shape"])
    layercount = var_dict["layercount"]
    width = var_dict["width"]
    step_value = var_dict["step_value"]
    min_x = var_dict["min_x"]
    min_y = var_dict["min_y"]
    board = pcbnew.GetBoard()
    track_list = board.GetTracks()
    tracks = list(filter(lambda x: x.GetClass() != "VIA", track_list))

    for t in tracks[start:stop]:
        t = Track(t)
        t_xstart = t.get_startx(step_value)
        t_ystart = t.get_start_y(step_value)
        t_xend = t.get_end_x(step_value)
        t_yend = t.get_end_y(step_value)
        t_width = t.get_width(step_value)
        x_pos = t_xstart - min_x
        y_pos = t_ystart - min_y
        direc = np.array([t_xend - t_xstart, t_yend - t_ystart])
        direc_l = np.linalg.norm(direc)
        if direc_l == 0:
            continue
        else:
            direc = direc / np.linalg.norm(direc)
        x_dir = 1 if direc[0] > 0 else -1
        y_dir = 1 if direc[1] > 0 else -1
        end_x = t_xend - min_x
        end_y = t_yend - min_y
        count = 0
        # cross-section in y- and x-direction depending on the tracks direction
        actual_t_width = t_width / max(np.sqrt(1-np.square(np.dot(direc, np.array([1, 0])))), np.abs(np.dot(direc, np.array([1, 0]))))

        if actual_t_width < width:
            # go along the track and create slices
            while (x_pos - end_x) * x_dir <= 0 and (y_pos - end_y) * y_dir <= 0:
                slicerino1 = np.zeros((layercount, width), np.uint8)
                slicerino2 = np.zeros((layercount, width), np.uint8)
                for i in range(layercount):
                    for j in range(width):
                        try:
                            slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                        except IndexError:
                            pass
                        try:
                            slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                        except IndexError:
                            pass
                # skio.imsave(name + " track" + " x:" + str(t.get_startx(100000)/10) + " y:" + str(t.get_start_y(100000)/10) + " " + str(count) + ".png", slicerino)
                slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                count = count + 1
                x_pos = x_pos + direc[0]
                y_pos = y_pos + direc[1]
        else:
            rot90 = np.array([[0, 1], [-1, 0]])
            offsets = np.dot(direc, rot90)
            offsets = offsets * t_width // 2
            buffer = direc * t_width // 2
            x_pos = x_pos + offsets[0] - buffer[0]
            end_x = end_x + offsets[0] + buffer[0]
            y_pos = y_pos + offsets[1] - buffer[1]
            end_y = end_y + offsets[1] + buffer[1]
            # go along the edges of the track and create slices
            while (x_pos - end_x) * x_dir <= 0 and (y_pos - end_y) * y_dir <= 0:
                slicerino1 = np.zeros((layercount, width), np.uint8)
                slicerino2 = np.zeros((layercount, width), np.uint8)
                for i in range(layercount):
                    for j in range(width):
                        try:
                            slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                        except IndexError:
                            pass
                        try:
                            slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                        except IndexError:
                            pass
                # skio.imsave(name + " track" + " x:" + str(t.get_startx(100000)/10) + " y:" + str(t.get_start_y(100000)/10) + " " + str(count) + ".png", slicerino)
                slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                count = count + 1
                x_pos = x_pos + direc[0]
                y_pos = y_pos + direc[1]

            x_pos = t_xstart - min_x - offsets[0] - buffer[0]
            y_pos = t_ystart - min_y - offsets[1] - buffer[1]
            end_x = t_xend - min_x - offsets[0] + buffer[0]
            end_y = t_yend - min_y - offsets[1] + buffer[1]
            while (x_pos - end_x) * x_dir <= 0 and (y_pos - end_y) * y_dir <= 0:
                slicerino1 = np.zeros((layercount, width), np.uint8)
                slicerino2 = np.zeros((layercount, width), np.uint8)
                for i in range(layercount):
                    for j in range(width):
                        try:
                            slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                        except IndexError:
                            pass
                        try:
                            slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                        except IndexError:
                            pass
                # skio.imsave(name + " track" + " x:" + str(t.get_startx(100000)/10) + " y:" + str(t.get_start_y(100000)/10) + " " + str(count) + ".png", slicerino)
                slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                count = count + 1
                x_pos = x_pos + direc[0]
                y_pos = y_pos + direc[1]

    return slices


def _slice_via(start, stop):
    """Slices all vias in pcbnews TrackList from start to stop"""
    slices = []
    layers = np.frombuffer(var_dict["layers_raw"], np.uint8).reshape(var_dict["layers_shape"])
    layercount = var_dict["layercount"]
    width = var_dict["width"]
    step_value = var_dict["step_value"]
    min_x = var_dict["min_x"]
    min_y = var_dict["min_y"]
    board = pcbnew.GetBoard()
    track_list = board.GetTracks()
    vias = list(filter(lambda x: x.GetClass() == "VIA", track_list))

    for v in vias[start:stop]:
        v = Via(v)
        v_xpos = v.get_x_pos(step_value)
        v_ypos = v.get_y_pos(step_value)
        v_width = v.get_width(step_value)
        # if the via is bigger than the slice: create slices along its edge
        if v_width >= width:
            radius = v_width // 2
            direc = np.array([radius, 0])
            x_pos = v_xpos - min_x
            y_pos = v_ypos - min_y
            rot = np.array([[np.cos(1/radius), np.sin(1/radius)], [-np.sin(1/radius), np.cos(1/radius)]])
            # rotate around via and create slices
            for _ in range(int(2 * np.pi * radius)+1):
                slicerino1 = np.zeros((layercount, width), np.uint8)
                slicerino2 = np.zeros((layercount, width), np.uint8)
                for i in range(layercount):
                    for j in range(width):
                        try:
                            slicerino1[i, j] = layers[i, int(y_pos+direc[1]), int(x_pos+direc[0]+j-(width//2))]
                        except IndexError:
                            pass
                        try:
                            slicerino2[i, j] = layers[i, int(y_pos+direc[1]+j-(width//2)), int(x_pos+direc[0])]
                        except IndexError:
                            pass
                slices.append((str(int(x_pos+direc[0])) + "_" + str(int(y_pos+direc[1])) + "_0", slicerino1.tobytes()))
                slices.append((str(int(x_pos+direc[0])) + "_" + str(int(y_pos+direc[1])) + "_1", slicerino2.tobytes()))
                direc = np.dot(direc, rot)
        else:
            x_pos = v_xpos - min_x - (v_width//2)
            y_pos = v_ypos - min_y
            # create slices through via along the x-axis
            for _ in range(v_width):
                slicerino1 = np.zeros((layercount, width), np.uint8)
                slicerino2 = np.zeros((layercount, width), np.uint8)
                for i in range(layercount):
                    for j in range(width):
                        try:
                            slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                        except IndexError:
                            pass
                        try:
                            slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                        except IndexError:
                            pass
                slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                x_pos = x_pos + 1

            # create slices through via along the y-axis
            x_pos = v_xpos - min_x
            y_pos = v_ypos - min_y - (v_width//2)
            for _ in range(v_width):
                slicerino1 = np.zeros((layercount, width), np.uint8)
                slicerino2 = np.zeros((layercount, width), np.uint8)
                for i in range(layercount):
                    for j in range(width):
                        try:
                            slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                        except IndexError:
                            pass
                        try:
                            slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                        except IndexError:
                            pass
                slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                y_pos = y_pos + 1
    return slices


def _slice_pad(start, stop):
    """Slices all pads in pcbnews TrackList from start to stop"""
    slices = []
    layers = np.frombuffer(var_dict["layers_raw"], np.uint8).reshape(var_dict["layers_shape"])
    layercount = var_dict["layercount"]
    width = var_dict["width"]
    step_value = var_dict["step_value"]
    min_x = var_dict["min_x"]
    min_y = var_dict["min_y"]

    board = pcbnew.GetBoard()
    pad_list = board.GetPads()
    for p in pad_list[start:stop]:
        p = Pad(p)
        p_shape = p.get_shape()
        p_xpos = p.get_x_pos(step_value)
        p_ypos = p.get_y_pos(step_value)
        p_xsize = p.get_x_size(step_value)
        p_ysize = p.get_y_size(step_value)
        p_orien = p.get_orientation()

        # if pad is circular: treat it like a via
        if p_shape == 0:
            if p_xsize >= width:
                radius = p_xsize // 2
                direc = np.array([radius, 0])
                x_pos = p_xpos - min_x
                y_pos = p_ypos - min_y
                rot = np.array([[np.cos(1/radius), np.sin(1/radius)], [-np.sin(1/radius), np.cos(1/radius)]])
                for _ in range(int(2 * np.pi * radius)+1):
                    slicerino1 = np.zeros((layercount, width), np.uint8)
                    slicerino2 = np.zeros((layercount, width), np.uint8)
                    for i in range(layercount):
                        for j in range(width):
                            try:
                                slicerino1[i, j] = layers[i, int(y_pos+direc[1]), int(x_pos+direc[0]+j-(width//2))]
                            except IndexError:
                                pass
                            try:
                                slicerino2[i, j] = layers[i, int(y_pos+direc[1]+j-(width//2)), int(x_pos+direc[0])]
                            except IndexError:
                                pass
                    slices.append((str(int(x_pos+direc[0])) + "_" + str(int(y_pos+direc[1])) + "_0", slicerino1.tobytes()))
                    slices.append((str(int(x_pos+direc[0])) + "_" + str(int(y_pos+direc[1])) + "_1", slicerino2.tobytes()))
                    direc = np.dot(direc, rot)
            else:
                x_pos = p_xpos - min_x - (p_xsize//2)
                y_pos = p_ypos - min_y

                for _ in range(p_xsize):
                    slicerino1 = np.zeros((layercount, width), np.uint8)
                    slicerino2 = np.zeros((layercount, width), np.uint8)
                    for i in range(layercount):
                        for j in range(width):
                            try:
                                slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                            except IndexError:
                                pass
                            try:
                                slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                            except IndexError:
                                pass
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                    x_pos = x_pos + 1

                x_pos = p_xpos - min_x
                y_pos = p_ypos - min_y - (p_xsize//2)
                for _ in range(p_xsize):
                    slicerino1 = np.zeros((layercount, width), np.uint8)
                    slicerino2 = np.zeros((layercount, width), np.uint8)
                    for i in range(layercount):
                        for j in range(width):
                            try:
                                slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                            except IndexError:
                                pass
                            try:
                                slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                            except IndexError:
                                pass
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                    y_pos = y_pos + 1

        # if pad is not circular: treat it as a rectangle
        else:
            orien = p_orien
            rot = np.array([[np.cos(orien), -np.sin(orien)], [np.sin(orien), np.cos(orien)]])
            directions_y = [-p_ysize // 2, p_ysize // 2, p_ysize // 2, -p_ysize // 2]
            directions_x = [-p_xsize // 2, -p_xsize // 2, p_xsize // 2, p_xsize // 2]
            directions = np.array([directions_x, directions_y]).transpose()
            directions = np.dot(directions, rot).transpose()
            x_vertices = directions[0] + p_xpos - min_x
            y_vertices = directions[1] + p_ypos - min_y
            x_vector = np.array([x_vertices[3] - x_vertices[0], y_vertices[3] - y_vertices[0]])
            y_vector = np.array([x_vertices[1] - x_vertices[0], y_vertices[1] - y_vertices[0]])
            x_vector = x_vector / np.linalg.norm(x_vector)
            y_vector = y_vector / np.linalg.norm(y_vector)
            
            # if there is the possibility (depending on its angle) that the pad is bigger than the slice: create slices along its edge
            if np.sqrt(np.square(p_xsize) + np.square(p_ysize)) >= width:
                x_pos = x_vertices[0]
                y_pos = y_vertices[0]
                for _ in range(p_xsize):
                    slicerino1 = np.zeros((layercount, width), np.uint8)
                    slicerino2 = np.zeros((layercount, width), np.uint8)
                    for i in range(layercount):
                        for j in range(width):
                            try:
                                slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                            except IndexError:
                                pass
                            try:
                                slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                            except IndexError:
                                pass
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                    x_pos = x_pos + x_vector[0]
                    y_pos = y_pos + x_vector[1]

                x_pos = x_vertices[1]
                y_pos = y_vertices[1]
                for _ in range(p_xsize):
                    slicerino1 = np.zeros((layercount, width), np.uint8)
                    slicerino2 = np.zeros((layercount, width), np.uint8)
                    for i in range(layercount):
                        for j in range(width):
                            try:
                                slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                            except IndexError:
                                pass
                            try:
                                slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                            except IndexError:
                                pass
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                    x_pos = x_pos + x_vector[0]
                    y_pos = y_pos + x_vector[1]

                x_pos = x_vertices[0]
                y_pos = y_vertices[0]
                for _ in range(p_ysize):
                    slicerino1 = np.zeros((layercount, width), np.uint8)
                    slicerino2 = np.zeros((layercount, width), np.uint8)
                    for i in range(layercount):
                        for j in range(width):
                            try:
                                slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                            except IndexError:
                                pass
                            try:
                                slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                            except IndexError:
                                pass
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                    x_pos = x_pos + y_vector[0]
                    y_pos = y_pos + y_vector[1]

                x_pos = x_vertices[3]
                y_pos = y_vertices[3]
                for _ in range(p_ysize):
                    slicerino1 = np.zeros((layercount, width), np.uint8)
                    slicerino2 = np.zeros((layercount, width), np.uint8)
                    for i in range(layercount):
                        for j in range(width):
                            try:
                                slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                            except IndexError:
                                pass
                            try:
                                slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                            except IndexError:
                                pass
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                    x_pos = x_pos + y_vector[0]
                    y_pos = y_pos + y_vector[1]
            # if the pad is smaller than the slice: create slices along its x- and y-axis
            else:
                x_pos = x_vertices[0] + (y_vector[0] * p_ysize // 2)
                y_pos = y_vertices[0] + (y_vector[1] * p_ysize // 2)
                for _ in range(p_xsize):
                    slicerino1 = np.zeros((layercount, width), np.uint8)
                    slicerino2 = np.zeros((layercount, width), np.uint8)
                    for i in range(layercount):
                        for j in range(width):
                            try:
                                slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                            except IndexError:
                                pass
                            try:
                                slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                            except IndexError:
                                pass
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                    x_pos = x_pos + x_vector[0]
                    y_pos = y_pos + x_vector[1]

                x_pos = x_vertices[0] + (x_vector[0] * p_xsize // 2)
                y_pos = y_vertices[0] + (x_vector[1] * p_xsize // 2)
                for _ in range(p_ysize):
                    slicerino1 = np.zeros((layercount, width), np.uint8)
                    slicerino2 = np.zeros((layercount, width), np.uint8)
                    for i in range(layercount):
                        for j in range(width):
                            try:
                                slicerino1[i, j] = layers[i, int(y_pos), int(x_pos+j-(width//2))]
                            except IndexError:
                                pass
                            try:
                                slicerino2[i, j] = layers[i, int(y_pos+j-(width//2)), int(x_pos)]
                            except IndexError:
                                pass
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_0", slicerino1.tobytes()))
                    slices.append((str(int(x_pos)) + "_" + str(int(y_pos)) + "_1", slicerino2.tobytes()))
                    x_pos = x_pos + y_vector[0]
                    y_pos = y_pos + y_vector[1]
    return slices

def createSlicesMP(plugin):
    """Creates slices from the PCB layout by converting the entire board into a byte array and slicing along its components.
     Uses all CPU cores except for one (so the computer does not freeze). Rasterizes the Board with a precision of "minimum track width / 4".
     Extremely big boards may cause the RAM to overflow.

    Arguments:
        plugin (PrototypePlugin): The Plugin wanting the slices.

    Returns:
        list: A list of slices as byte object. Contain no information about the slice dimensions (reshape in plugin).
    """
    start = localtime()
    board = pcbnew.GetBoard()
    layercount = plugin.get_preference("slice_y")
    track_list = board.GetTracks()
    pad_list = board.GetPads()
    tracks = [Track(t) for t in filter(lambda x: x.GetClass() != "VIA", track_list)]
    vias = [Via(t) for t in filter(lambda x: x.GetClass() == "VIA", track_list)]
    pads = [Pad(p) for p in pad_list]

    scalefactor = 4
    # step_value is rasterization precision
    step_value = board.GetDesignSettings().GetSmallestClearanceValue() // scalefactor
    box = board.GetBoardEdgesBoundingBox()
    min_x = box.GetLeft() // step_value
    min_y = box.GetTop() // step_value
    max_x = box.GetRight() // step_value
    max_y = box.GetBottom() // step_value
    layers_shape = (layercount, max_y-min_y, max_x-min_x)
    # array in shared memory for multiprocessing
    layers_raw = RawArray(c_byte, layers_shape[0]*layers_shape[1]*layers_shape[2])
    layers = np.frombuffer(layers_raw, np.uint8).reshape(layers_shape)

    for i in range(layercount):
        for p in pads:
            p_shape = p.get_shape()
            p_xpos = p.get_x_pos(step_value)
            p_ypos = p.get_y_pos(step_value)
            p_xsize = p.get_x_size(step_value)
            p_ysize = p.get_y_size(step_value)
            p_orien = p.get_orientation()

            # pads penetrate layers
            if (p.get_top_layer_id() <= i and p.get_bottom_layer_id() >= i):
                # everything that is not a circle is treated as a rectangle
                if p_shape == 0:
                    rr, cc = draw.disk((p_ypos - min_y, p_xpos - min_x), p_xsize // 2)
                else:
                    orien = p_orien
                    rot = np.array([[np.cos(orien), -np.sin(orien)], [np.sin(orien), np.cos(orien)]])
                    directions_y = [-p_ysize // 2, p_ysize // 2, p_ysize // 2, -p_ysize // 2]
                    directions_x = [-p_xsize // 2, -p_xsize // 2, p_xsize // 2, p_xsize // 2]
                    directions = np.array([directions_x, directions_y]).transpose()
                    directions = np.dot(directions, rot).transpose()
                    c = directions[0] + p_xpos - min_x
                    r = directions[1] + p_ypos - min_y
                    rr, cc = draw.polygon(r, c)
                signal = plugin.get_annotated_net(p.get_netcode())
                try:
                    layers[i, rr, cc] = 0 if signal is None else signal
                except IndexError:
                    pass


        for v in vias:
            v_xpos = v.get_x_pos(step_value)
            v_ypos = v.get_y_pos(step_value)
            v_width = v.get_width(step_value)

            # vias penetrate layers
            if (v.get_top_layer_id() <= i and v.get_bottom_layer_id() >= i):
                # vias are always circles
                rr, cc = draw.disk((v_ypos - min_y, v_xpos - min_x), v_width // 2)
                signal = plugin.get_annotated_net(v.get_netcode())
                try:
                    layers[i, rr, cc] = 0 if signal is None else signal
                except IndexError:
                    pass

        for t in tracks:
            t_xstart = t.get_startx(step_value)
            t_ystart = t.get_start_y(step_value)
            t_xend = t.get_end_x(step_value)
            t_yend = t.get_end_y(step_value)
            t_width = t.get_width(step_value)

            if t.get_layer_id() == i or (t.get_layer_id() == 31 and i == layercount-1):
                direction1 = np.array([t_xend - t_xstart, t_yend - t_ystart])
                rot90 = np.array([[0, 1], [-1, 0]])
                direc_l = np.linalg.norm(direction1)
                if direc_l == 0:
                    continue
                else:
                    direction1 = direction1 / direc_l
                direction1 = direction1 * t_width // 2
                direction1 = np.dot(direction1, rot90)
                direction2 = -direction1
                direction3 = direction2
                direction4 = direction1
                r = np.array([t_ystart + direction1[1] - min_y, t_ystart + direction2[1] - min_y, t_yend + direction3[1] - min_y, t_yend + direction4[1] - min_y])
                c = np.array([t_xstart + direction1[0] - min_x, t_xstart + direction2[0] - min_x, t_xend + direction3[0] - min_x, t_xend + direction4[0] - min_x])
                # a track is represented as a rectangle with two half-circles at its ends
                rr, cc = draw.polygon(r, c)
                qq, tt = draw.disk((t_ystart - min_y, t_xstart - min_x), t_width // 2)
                vv, ww = draw.disk((t_yend - min_y, t_xend - min_x), t_width // 2)
                signal = plugin.get_annotated_net(t.get_netcode())
                try:
                    layers[i, rr, cc] = 0 if signal is None else signal
                    layers[i, qq, tt] = 0 if signal is None else signal
                    layers[i, vv, ww] = 0 if signal is None else signal
                except IndexError:
                    pass

    # the name of the project
    filename = board.GetFileName()
    name = re.search(r'[^\/]*\.kicad_pcb', filename).group(0)[:-10]
    # for i in range(layercount):
    #     skio.imsave(name + "-layer" + str(i) + ".png", layers[i])

    width = plugin.get_preference("slice_x")
    cpus = cpu_count()-1
    cpus = 1 if cpus == 0 else cpus
    with Pool(processes=cpus, initializer=_worker_init, initargs=(layers_raw, layers_shape, layercount, width, step_value, name, min_x, min_y)) as pool:
        if len(tracks) > 100:
            res1 = [pool.apply_async(_slice_track, (i * len(tracks) // cpus, (i+1) * len(tracks) // cpus)) for i in range(cpus)]
        else:
            res1 = [pool.apply_async(_slice_track, (0, len(tracks)))]

        if len(vias) > 100:
            res2 = [pool.apply_async(_slice_via, (i * len(vias) // cpus, (i+1) * len(vias) // cpus)) for i in range(cpus)]
        else:
            res2 = [pool.apply_async(_slice_via, (0, len(vias)))]

        if len(pads) > 100:
            res3 = [pool.apply_async(_slice_pad, (i * len(pads) // cpus, (i+1) * len(pads) // cpus)) for i in range(cpus)]
        else:
            res3 = [pool.apply_async(_slice_pad, (0, len(pads)))]

        tmp = res1 + res2 + res3
        tmp = [x.get() for x in tmp]

    # the workers return a list each, the resulting nested list must be flattened
    final = [x for y in tmp for x in y]
    # with open(name + "_slices.json", "w") as f:
    #     tosave = [(x, y.decode("utf-8")) for x,y in final]
    #     json.dump(tosave, f)
    return (layers, final)
