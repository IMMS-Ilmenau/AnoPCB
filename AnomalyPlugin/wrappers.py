"""
A module containing Wrapper classes for pcbnews components,
which are just C++ classes mirrored by Swig.
"""

class Track:
    """Wrapper Class for pcbnew.TRACK.
    Vias are also Tracks, test with .GetClass() == "TRACK" before creating Wrapper.
    """
    def __init__(self, track):
        """Initializes the Track.

        Args:
            track (pcbnew.Track): The Track.
        """
        self.track = track

    def get_startx(self, step_value=1):
        """Gets x-coordinate of starting point.

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- x-coordinate
        """
        return self.track.GetStart().x // step_value

    def get_start_y(self, step_value=1):
        """Gets y-coordinate of starting point.

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- y-coordinate
        """
        return self.track.GetStart().y // step_value

    def get_end_x(self, step_value=1):
        """Gets x-coordinate of end point.

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- x-coordinate
        """
        return self.track.GetEnd().x // step_value

    def get_end_y(self, step_value=1):
        """Gets y-coordinate of end point.

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- x-coordinate
        """
        return self.track.GetEnd().y // step_value

    def get_layer_name(self):
        """Gets name of the layer this track is on.

        Returns:
            str -- layer name
        """
        return self.track.GetLayerName()

    def get_layer_id(self):
        """Gets ID of the layer this track is on.
        Copperlayers are 0 to 31, 0 is always top, 31 always bottom, inner are counted up from 1.

        Returns:
            int -- layer ID
        """
        return self.track.GetLayer()

    def get_width(self, step_value=1):
        """Gets width of the track.

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- width
        """
        return self.track.GetWidth() // step_value

    def get_netcode(self):
        """Gets netcode of the net this track is in.

        Returns:
            int -- netcode
        """
        return self.track.GetNetCode()

    def get_netname(self):
        """Gets name of the net the track is in.

        Returns:
            str -- name
        """
        return self.track.GetNetname()


class Via:
    """Wrapper Class for pcbnew.VIA.
    Vias are also Tracks, test with .GetClass() == "VIA" before creating Wrapper.
    """

    def __init__(self, track):
        """Initializes a Via by a Track.

        Args:
            track (pcbnew.Via): The track.
        """
        self.track = track

    def get_x_pos(self, step_value=1):
        """Gets x-coordinate of the via.

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- x-coordinate
        """
        return self.track.GetStart().x // step_value

    def get_y_pos(self, step_value=1):
        """Gets y-coordinate of the via.

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- y-coordinate
        """
        return self.track.GetStart().y // step_value

    def get_width(self, step_value=1):
        """Gets width of the via.

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- width
        """
        return self.track.GetWidth() // step_value

    def get_netcode(self):
        """Gets netcode of the net this via is in.

        Returns:
            int -- netcode
        """
        return self.track.GetNetCode()

    def get_netname(self):
        """Gets name of the net the via is in.

        Returns:
            str -- name
        """
        return self.track.GetNetname()

    def get_top_layer_id(self):
        """Gets ID of the uppermost layer the via punctures.
        Copperlayers are 0 to 31, 0 is always top, 31 always bottom, inner are counted up from 1.

        Returns:
            int -- ID
        """
        return self.track.TopLayer()

    def get_bottom_layer_id(self):
        """Gets ID of the lowermost layer the via punctures.
        Copperlayers are 0 to 31, 0 is always top, 31 always bottom, inner are counted up from 1.

        Returns:
            int -- ID
        """
        return self.track.BottomLayer()


class Net:
    """Wrapper class for pcbnew.NETINFO_ITEM
    """
    def __init__(self, net):
        """Initializes the Net.

        Args:
            net (pcbnew.NETINFO_ITEM): The Net.
        """
        self.net = net

    def get_netcode(self):
        """Gets netcode of the net.

        Returns:
            int -- netcode
        """
        return self.net.GetNet()

    def get_name(self):
        """Gets name of the net.

        Returns:
            str -- name
        """
        return self.net.GetNetname()

    def get_layer_name(self):
        """Gets name of the layer this net is on.

        Returns:
            str -- layer name
        """
        return self.net.GetLayerName()

    def get_layer_id(self):
        """Gets ID of the layer this net is on.
        Copperlayers are 0 to 31, 0 is always top, 31 always bottom, inner are counted up from 1.

        Returns:
            int -- layer ID
        """
        return self.net.GetLayer()

    def get_tracks(self):
        """Gets the tracks in this net.

        Returns:
            tuple -- tuple of pcbnew.TRACK
        """
        return self.net.GetBoard().TracksInNet(self.net.GetNet())

    def get_pads(self):
        """Gets the pads in this net.

        Returns:
            tuple -- tuple of pcbnew.PAD
        """
        pads = self.net.GetBoard().GetPads()
        pad_list = []
        for pad in pads:
            if pad.GetNetCode() == self.net.GetNet():
                pad_list.append(pad)
        return tuple(pad_list)


class Pad:
    """Wrapper class for pcbnew.PAD
    """
    def __init__(self, pad):
        """Initializes the Pad.

        Args:
            pad (pcbnew.Pad): The pad.
        """
        self.pad = pad

    def get_name(self):
        """Gets name of this pad.

        Returns:
            str -- name
        """
        return self.pad.GetName()

    def get_netcode(self):
        """Gets netcode of the net this pad is in.

        Returns:
            int -- netcode
        """
        return self.pad.GetNetCode()

    def get_netname(self):
        """Gets name of the net the pad is in.

        Returns:
            str -- name
        """
        return self.pad.GetNetname()

    def get_top_layer_id(self):
        """Gets ID of the uppermost layer this pad is on / punctures.
        Copperlayers are 0 to 31, 0 is always top, 31 always bottom, inner are counted up from 1.

        Returns:
            int -- layer ID
        """
        layer_id = 0
        for i in range(0, 32):
            if self.pad.IsOnLayer(i):
                layer_id = i
                break

        return layer_id

    def get_bottom_layer_id(self):
        """Gets ID of the lowermost layer this pad is on / punctures.
        Copperlayers are 0 to 31, 0 is always top, 31 always bottom, inner are counted up from 1.

        Returns:
            int -- layer ID
        """
        layer_id = 0
        for i in range(31, -1, -1):
            if self.pad.IsOnLayer(i):
                layer_id = i
                break

        return layer_id

    def get_x_pos(self, step_value=1):
        """Gets x-coordinate of the pads position.

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- x-coordinate
        """
        return self.pad.GetPosition().x // step_value

    def get_y_pos(self, step_value=1):
        """Gets y-coordinate of the pads position.

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- y-coordinate
        """
        return self.pad.GetPosition().y // step_value

    def get_x_size(self, step_value=1):
        """Gets x-value of the pads size (ellipse or rectangle).

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- x-value
        """
        return self.pad.GetSize().x // step_value

    def get_y_size(self, step_value=1):
        """Gets y-value of the pads size (ellipse or rectangle).

        Keyword Arguments:
            step_value {int} -- factor result is divided by for scaling (default: {1})

        Returns:
            int -- y-value
        """
        return self.pad.GetSize().y // step_value

    def get_shape(self):
        """Gets the pads shape.

        circle: 0
        rectangle: 1
        oval: 2
        trapezoid: 3
        roundrect: 4
        custom: 5

        Returns:
            int -- shape ID
        """
        return self.pad.GetShape()

    def get_type(self):
        """Gets the pads type.

        through-hole: 0
        smd: 1
        connector: 2
        npth: 3

        Returns:
            int -- type ID
        """
        return self.pad.GetAttribute()

    def get_orientation(self):
        """Gets the pads orientation in radians.

        Returns:
            double -- value between 0 and 2*Pi
        """
        return self.pad.GetOrientationRadians()
