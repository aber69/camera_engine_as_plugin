import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

from threading import Thread
import time
import os

class InputSelectorProbeData:
    def __init__(self, pipeline, input_selector, num_input_sources, pad_start_idx=0):
        self.pipeline = pipeline
        self.input_selector = input_selector

        self.current_pad_idx = pad_start_idx
        self.num_inputs = num_input_sources

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
        print("Caught End-of-Stream")
        loop.quit()
    elif t == Gst.MessageType.WARNING:
        err, debug = message.parse_warnings()
        print(err)
        print(debug)
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(err)
        print(debug)
        loop.quit()
    else:
        print("Some Other Element Info")
    return True


def main():
    Gst.init("test-input-selector")
    pipeline = Gst.Pipeline()
    pipeline.set_name("test-input-selector")

    input_selector = Gst.ElementFactory.make("input-selector", "test-input-selector")
    pipeline.add(input_selector)

    print("Running Input Selector Test")
    for i, video_device_idx in enumerate([2, 4]):
        source = Gst.ElementFactory.make("v4l2src", f"source-video-{i}")

        buffer_1 = Gst.ElementFactory.make("queue", f"queue-1-{i}")

        capsfilter = Gst.ElementFactory.make("capsfilter", f"source-{i}-capsfilter")

        jpeg_parser = Gst.ElementFactory.make("jpegparse", f"jpeg-parser-{i}")

        buffer_2 = Gst.ElementFactory.make("queue", f"queue-2-{i}")

        jpeg_decoder = Gst.ElementFactory.make("jpegdec", f"jpeg-decode-{i}")


        source.set_property("device", f"/dev/video{video_device_idx}")
        capsfilter.set_property("caps", Gst.Caps.from_string("image/jpeg, width=1280, height=720, format=MJPG, framerate=30/1"))

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
        selector_sink_pad = Gst.Element.request_pad_simple(input_selector, f"sink_{i}")
        decoder_src_pad.link(selector_sink_pad)

    display_sink = Gst.ElementFactory.make("ximagesink", f"display-sink-{i}")
    pipeline.add(display_sink)
    display_sink.set_property("sync", False)
    input_selector.link(display_sink)

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # Initalise the stream-selector logic objects
    probe_data = InputSelectorProbeData(pipeline, input_selector, 2, 0)
    GLib.timeout_add(1000, change_active_source_callback, probe_data)
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Ctrl+C... Exiting!")
    except Exception as e:
        print("We are done...")
        print(e)

    pipeline.set_state(Gst.State.NULL)




if __name__ == "__main__":
    main()
