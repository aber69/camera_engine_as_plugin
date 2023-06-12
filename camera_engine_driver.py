#!/usr/bin/env python3

import sys
import time
import os
import random

try:
    import pydantic
except ModuleNotFoundError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'pydantic'])

# https://gist.github.com/hum4n0id/cda96fb07a34300cdb2c0e314c14df0a

#%% Setup path to python plugins
assert os.path.exists(os.path.dirname(__file__) + '/python')

os.environ['GST_PLUGIN_PATH'] = str(os.environ['GST_PLUGIN_PATH']+":" if 'GST_PLUGIN_PATH' in os.environ else "") + \
    os.path.dirname(__file__)
os.environ['GST_PLUGIN_PATH'] = ":".join(set(os.environ['GST_PLUGIN_PATH'].split(':')))
# print(os.environ['GST_PLUGIN_PATH'])

#%%
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import GLib,  Gst


class InputSelectorProbeData:
    def __init__(self, pipeline, input_selector, num_input_sources, pad_start_idx=0):
        self.pipeline = pipeline
        self.input_selector = input_selector

        self.current_pad_idx = pad_start_idx
        self.num_inputs = num_input_sources
        print("Num of num_inputs", num_input_sources)

    def update_stream(self):
        next_pad_idx = (self.current_pad_idx + 1) % self.num_inputs
        print(f"Input selector updating camera to {next_pad_idx}")
        active_pad = self.input_selector.get_static_pad(f"sink_{next_pad_idx}")
        self.input_selector.set_property("active-pad", active_pad)
        self.current_pad_idx = next_pad_idx

def change_active_source_callback(probe_data: InputSelectorProbeData):
    probe_data.update_stream()
    return True

def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.EOS:
        sys.stderr.write("Caught End-of-Stream")
        loop.quit()
    elif t == Gst.MessageType.WARNING:
        err, debug = message.parse_warnings()
        sys.stderr.write("Warning: %s: %s\n" % (err, debug))
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    #else:
    #    print("Some Other Element Info:\t", t)
    return True


def Gst_ElementFactory_make_with_test(factory_name, name):
    element = Gst.ElementFactory.make(factory_name, name)
    if element is None:
        sys.stderr.write("Gst.ElementFactory.make failed for: " +
                        f"{factory_name} as {name}\n")
        assert False
    return element

def add_usb_source_for_selection(pipeline, input_selector, ind, video_device_idx):
    source = Gst_ElementFactory_make_with_test("v4l2src", f"source-video-{ind}")

    buffer_1 = Gst_ElementFactory_make_with_test("queue", f"queue-1-{ind}")

    capsfilter = Gst_ElementFactory_make_with_test(
        "capsfilter", f"source-{ind}-capsfilter")

    jpeg_parser = Gst_ElementFactory_make_with_test("jpegparse", f"jpeg-parser-{ind}")

    buffer_2 = Gst_ElementFactory_make_with_test("queue", f"queue-2-{ind}")

    jpeg_decoder = Gst_ElementFactory_make_with_test("jpegdec", f"jpeg-decode-{ind}")

    source.set_property("device", f"/dev/video{video_device_idx}")
    capsfilter.set_property("caps", Gst.Caps.from_string(
        "video/x-raw, width=640, height=480, framerate=30/1"))

    pipeline.add(source)
    pipeline.add(buffer_1)
    pipeline.add(capsfilter)
    pipeline.add(jpeg_parser)
    pipeline.add(buffer_2)
    pipeline.add(jpeg_decoder)

    source.link(buffer_1)
    buffer_1.link(capsfilter)
    capsfilter.link(jpeg_parser)
    jpeg_parser.link(buffer_2)
    buffer_2.link(jpeg_decoder)

    decoder_src_pad = jpeg_decoder.get_static_pad("src")
    selector_sink_pad = Gst.Element.request_pad_simple(
        input_selector, f"sink_{ind}")
    decoder_src_pad.link(selector_sink_pad)
    return pipeline


def add_video_test_source(pipeline, input_selector, ind):
    # gst-launch-1.0 -v videotestsrc pattern=snow ! video/x-raw,width=1280,height=720 ! autovideosink
    source = Gst_ElementFactory_make_with_test("videotestsrc", f"source-video-{ind}")
    # buffer_1 = Gst_ElementFactory_make_with_test("queue", f"queue-1-{ind}")

    capsfilter = Gst_ElementFactory_make_with_test(
        "capsfilter", f"source-{ind}-capsfilter")

    source_pattern = [
        "smpte",   # SMPTE 100% color bars
        "snow",    # Random (television snow)
        "black",   # 100% Black
        "white",   # 100% White
        "red",     # Red
        "green",   # Green
        "blue",    # Blue
        "checkers-1",    # Checkers 1px
        "checkers-2",    # Checkers 2px
        "checkers-4",    # Checkers 4px
        "checkers-8",    # Checkers 8px
        "circular",   # Circular
        "blink",      # Blink
        "smpte75",    # SMPTE 75% color bars
        "zone-plate", # Zone plate
        "gamut",      # Gamut checkers
        "chroma-zone-plate",  # Chroma zone plate
        "solid-color",    # Solid color
        "ball",       # Moving ball
        "smpte100",   # SMPTE 100% color bars
        "bar",        # Bar
        "pinwheel",   # Pinwheel
        "spokes",     # Spokes
        "gradient",   # Gradient
        "colors",     # Colors
        "smpte-rp-219",    # SMPTE test pattern, RP 219 conformant
    ]

    source.set_property(
        "pattern", f"{source_pattern[random.randint(0, len(source_pattern)-1)]}")
    # https://brettviren.github.io/pygst-tutorial-org/pygst-tutorial.html
    capsfilter.set_property("caps", Gst.Caps.from_string(
        "video/x-raw, width=1280, height=720"))


    pipeline.add(source)
    # pipeline.add(buffer_1)
    pipeline.add(capsfilter)

    source.link(capsfilter)
    # buffer_1.link(capsfilter)
    #capsfilter.link(jpeg_parser)

    capsfilter_src_pad = capsfilter.get_static_pad("src")
    selector_sink_pad = Gst.Element.request_pad_simple(
        input_selector, f"sink_{ind}")
    capsfilter_src_pad.link(selector_sink_pad)
    return pipeline

def main():
    # init GStreamer
    Gst.init(None)
    pipeline = Gst.Pipeline()
    pipeline.set_name("camera_engine_with_external_camera_selector")

    input_selector = Gst_ElementFactory_make_with_test("input-selector", "camera-input-selector")
    pipeline.add(input_selector)

    print("Init Input Selector Test")
    #for src_i, video_device_idx in enumerate([0, 0, 0, 0, 0]):
    #    pipeline = add_usb_source_for_selection(
    #        pipeline, input_selector, src_i, video_device_idx)

    for src_i in range(4):
        pipeline = add_video_test_source(pipeline, input_selector, src_i)

    camera_engine = Gst_ElementFactory_make_with_test("camera_engine_py", f"camera_engine")
    display_sink = Gst_ElementFactory_make_with_test("autovideosink", f"display-sink")
    pipeline.add(camera_engine)
    pipeline.add(display_sink)
    display_sink.set_property("sync", False)
    camera_engine.set_property("config-file-name", "./camera_engine.json")
    camera_engine.set_property("zoom", 1)
    camera_engine.set_property("zoom", -11)
    camera_engine.set_property("pan", (1,1))
    input_selector.link(camera_engine)
    camera_engine.link(display_sink)

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # Initialise the stream-selector logic objects
    probe_data = InputSelectorProbeData(pipeline, input_selector, src_i+1, 0)
    GLib.timeout_add(1000, change_active_source_callback, probe_data)

    # start play back and listen to events
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Ctrl+C... Exiting!")
    except Exception as e:
        print("We are done...")
        print(e)

    # cleanup
    pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    main()
