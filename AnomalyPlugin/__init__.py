"""The plugin, that gets called by pcbnew and registers itself."""
import sys

if __package__ is None:
    sys.path.append("..")
from AnomalyPlugin.anomaly_plugin_main import MainPlugin

MainPlugin().register()
