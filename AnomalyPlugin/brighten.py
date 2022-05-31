"""Contains the brighten function used by the Show_layers- and ShowResultsDialog"""
from numba import prange, njit


@njit(parallel=True)
def brighten(layers):
    """
    Changes all non zero values in the "layers" array to
     255 so they can be represented in as grey scale images.

    Arguments:
        layers (array): layers as array.

    Returns:
        array: layers as array
    """
    for l in prange(len(layers)):
        for i in range(len(layers[l])):
            for j in range(len(layers[l][i])):
                layers[l][i][j] = 255 if layers[l][i][j] > 0 else 0
    return layers
