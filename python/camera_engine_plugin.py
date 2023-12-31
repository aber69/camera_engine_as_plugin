#!/usr/bin/env python
#  $ export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$PWD/plugin
#  $ GST_DEBUG=python:4 gst-launch-1.0 fakesrc num-buffers=10 ! camera_engine_py ! fakesink
from pathlib import Path

import gi
gi.require_version('GstBase', '1.0')

from gi.repository import Gst, GObject, GstBase
Gst.init(None)

from fov_management import FovManager, Point2D

class CameraEngine(GstBase.BaseTransform):
    # In Caps
    IN_CAPS = Gst.Caps(Gst.Structure('video/x-raw',
                                 format=Gst.ValueList(["RGB", "GRAY8"]),
                                 width=Gst.ValueList([320, 640, 1280, 1920]),
                                 height=Gst.ValueList([240, 480, 720, 1080])))

    # Output caps
    OUT_CAPS = Gst.Caps(Gst.Structure('video/x-raw',
                                    format=Gst.ValueList(["RGB"]),
                                    width=Gst.ValueList([640, 1280, 1920]),
                                    height=Gst.ValueList([480, 720, 1080])))

    # The contents of this tuple will be used to call gst_element_class_set_metadata
    # Gst.Element.get_metadata is python wrapper for 'gst_element_get_metadata'
    __gstmetadata__ = ('Camera Engine', 'Transform', \
                      'Digital Pan, Zoom and Fixed Size Rescaling Transform', 'Matrix AI for MaLaM')

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                           Gst.PadDirection.SRC,
                                           Gst.PadPresence.ALWAYS,
                                           Gst.Caps.new_any()),
                       Gst.PadTemplate.new("sink",
                                           Gst.PadDirection.SINK,
                                           Gst.PadPresence.ALWAYS,
                                           Gst.Caps.new_any()))

    __gproperties__ = {
        "config-file-name":  (
            GObject.TYPE_STRING,
            "Configuration File name",
            "file name of fov configuration file",
            "./camera_engine.json",
            GObject.ParamFlags.READWRITE #GObject.PARAM_READABLE
        ),
        "zoom": (
            int,
            "Zoom Enum",
            "Current Zoom Value",
            0,
            10,
            0,
            GObject.ParamFlags.READWRITE
            ),
        "pan-x": (
            int,
            "Pan X Enum",
            "Pan X Value To Set",
            -10,
            10,
            0,
            GObject.ParamFlags.READWRITE
        ),
        "pan-y": (
            int,
            "Pan Y Enum",
            "Pan Y Value To Set",
            -10,
            10,
            0,
            GObject.ParamFlags.READWRITE
        )
    }

    # https://lazka.github.io/pgi-docs/GstBase-1.0/classes/BaseTransform.html
    def __init__(self):
        super().__init__(self)
        print(__file__, ":\t init")
        # print(Path(".").resolve())

        self.config_file_name = "./camera_engine.json"
        assert Path(self.config_file_name).exists()

        self.zoom = 0
        self.pan_x_set = 0
        self.pan_y_set = 0

        print(self.IN_CAPS.to_string())
        print(self.OUT_CAPS.to_string())


    # GstBase.BaseTransform.reconfigure_src  -
    # Instructs trans to renegotiate a new downstream transform on the next buffer.
    # This function is typically called after properties on the transform were set that influence the output format.
    #    Parameters: trans (GstBase.BaseTransform)

    # do_before_transform (trans, buffer):
    # This method is called right before the base class will start processing. Dynamic properties or other delayed configuration could be performed in this method.
    #  Parameters:  trans (GstBase.BaseTransform), buffer (Gst.Buffer) –

    def do_get_property(self, prop):
        if prop.name == "config_file_name":
            return self.config_file_name
        elif prop.name == 'zoom':
            return self.zoom
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop, value):
        if prop.name == "config-file-name":
            self.config_file_name = value
            assert Path(self.config_file_name).exists()
        elif prop.name == 'zoom':
            self.zoom = value
        elif prop.name == 'pan-x':
            self.pan_x_set = value
        elif prop.name == 'pan-y':
            self.pan_y_set = value
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_transform_ip(self, buffer):
        Gst.info("timestamp(buffer):%s" % (Gst.TIME_ARGS(buffer.pts)))
        return Gst.FlowReturn.OK

#%% Register CameraEngine as plugin
GObject.type_register(CameraEngine)
__gstelementfactory__ = ("camera_engine_py", Gst.Rank.NONE, CameraEngine)
