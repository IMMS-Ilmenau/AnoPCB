"""Contains the ResultDialog used by the TrainModelDialog to display
 the training results."""
import wx
import wx.aui
import numpy as np
import matplotlib.pyplot as plt


class ResultDialog(wx.Dialog):
    """Displays training and validation losses.
    """
    def __init__(self, parent, resp):
        wx.Dialog.__init__(self, parent, size=(400, 400), style=wx.DEFAULT_DIALOG_STYLE)
        resp = resp["data"]
        losses = np.array(resp)

        self.list = wx.ListCtrl(self, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list.ClearAll()
        self.list.InsertColumn(0, "Loss")
        self.list.SetColumnWidth(0, 200)
        self.list.InsertColumn(1, "Val. loss")
        self.list.SetColumnWidth(1, 200)
        for item0, item1 in reversed(losses):
            self.list.InsertItem(0, item0)
            self.list.SetItem(0, 1, item1)
        only_sizer = wx.BoxSizer(wx.HORIZONTAL)
        only_sizer.Add(self.list, flag=wx.EXPAND)
        self.SetSizer(only_sizer)

        losses = np.transpose(losses).astype(np.float32)
        legends = []
        if np.any((losses[1] != 0)):
            legend1, = plt.plot(losses[1], label="Validation loss")
            legends.append(legend1)
        legend2, = plt.plot(losses[0], label="Training loss")
        legends.append(legend2)
        plt.xlabel("Epochs")
        plt.ylabel("Loss")
        plt.legend(handles=legends)
        plt.show()
