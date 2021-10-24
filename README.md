# AnoPCB

AnoPCB is a plugin for KiCad to spot potential anomalies with machine learning.
Using this tools requires preparation, as a (fitting) machine learning model must be provided. The creation of a machine learning model also involves training on data (in this case good known PCB designs).
Take a look at this [publication](https://ieeexplore.ieee.org/abstract/document/9547913) for further information on the machine learning algorithm used.

### Setup

To use the plugin, it is also required to provide a server. Though this server may get setup and started by the plugin itself if so wished.

# Development

### Setup docker server development

If you start your server with docker and the plugin and want to apply changes of server code without rebuilding the docker image each time, you can mount your code into the image. To do this add a environment variable like this:

`ANOPCB_SERVER_SOURCE=/absolute/path/to/folder/with/serversourcecode`

For a change to happen, an existing docker container must be deleted beforehand:
Find the container with `docker container ls -all` and delete it with `docker container rm <container>`.
