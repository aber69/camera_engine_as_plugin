#!/usr/bin/env python
#  $ export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$PWD/plugin
#  $ GST_DEBUG=python:4 gst-launch-1.0 fakesrc num-buffers=10 ! camera_engine_py ! fakesink

import gi
gi.require_version('GstBase', '1.0')

from gi.repository import Gst, GObject, GstBase
Gst.init(None)

from fov_management import FovManager, Point2D

class CameraEngine(GstBase.BaseTransform):
    __gstmetadata__ = ('Camera Engine', 'Transform', \
                      'Simple identity element written in python', 'Marianna S. Buschle')

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                           Gst.PadDirection.SRC,
                                           Gst.PadPresence.ALWAYS,
                                           Gst.Caps.new_any()),
                       Gst.PadTemplate.new("sink",
                                           Gst.PadDirection.SINK,
                                           Gst.PadPresence.ALWAYS,
                                           Gst.Caps.new_any()))

    def do_transform_ip(self, buffer):
        Gst.info("timestamp(buffer):%s" % (Gst.TIME_ARGS(buffer.pts)))
        return Gst.FlowReturn.OK

    def __init__(self):
        super().__init__()
        print(__file__, ":\t init")

GObject.type_register(CameraEngine)
__gstelementfactory__ = ("camera_engine_py", Gst.Rank.NONE, CameraEngine)
