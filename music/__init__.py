from math import floor, pi, cos
import os
import logging

from gi.repository import Gtk, Gdk, Gst, GObject, Pango, PangoCairo

# Not really used yet
os.environ['GST_DEBUG_DUMP_DOT_DIR'] = '/tmp'
os.putenv('GST_DEBUG_DUMP_DIR_DIR', '/tmp')

_log = logging.getLogger(__name__)


class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title='Music')

        self.set_size_request(1280, 720)

        self.music_generator = MusicGenerator()
        self.music_generator.play()

        self.drawing_area = MainWidget()
        self.drawing_area.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.drawing_area.connect('motion-notify-event', self.on_pointer_motion)
        self.drawing_area.show()

        self.add(self.drawing_area)

        self.connect('delete-event', Gtk.main_quit)
        self.connect('key-press-event', self.on_key_press)

    def on_pointer_motion(self, widget, ev, data=None):
        _log.debug('%s', (ev.x, ev.y))
        self.music_generator.set_freq(ev.x)

        width, height = self.get_size()

        self.drawing_area.update_size(width, height)

        rel_height = ev.y / height

        wave_mapping = {
            0: 0,  # sine
            1: 1,  # square
            2: 2,  # saw
            3: 3,  # triangle
            4: 7,  # sine-table
        }

        self.music_generator.set_wave(
            wave_mapping.get(
                floor(rel_height * 4)))

    @staticmethod
    def on_key_press(widget, ev, data=None):
        _log.debug('%s, %s, %s', widget, ev, data)
        _log.info('%s', ev.keyval)


class MainWidget(Gtk.DrawingArea):
    LINES_MAP = {
        0: (228, 213, 163),
        1: (200, 99, 104),
        2: (95, 25, 44),
        3: (111, 138, 121),
        4: (229, 230, 216),
        5: (66, 40, 51)
    }

    def __init__(self, *args, **kw):
        Gtk.DrawingArea.__init__(self)

        self._radius = 150
        self._number_of_lines = 6
        self.connect('draw', self.on_draw)
        self.size = 0, 0

    def update_size(self, width, height):
        self.size = width, height

    def on_draw(self, widget, cr):
        width, height = self.size
        for i in range(0, self._number_of_lines):
            line_height = width / self._number_of_lines

            cr.save()

            cr.scale(1, 1)
            color = map(lambda x: x / 255.0, self.LINES_MAP[i % len(self.LINES_MAP)])
            _log.debug('color: %s', color)
            cr.set_source_rgb(*color)

            cr.rectangle(0, i * line_height, width, line_height)
            cr.fill()
            cr.restore()


class MusicGenerator():
    def __init__(self):
        self.pipeline = Gst.Pipeline()

        self.audiosrc = Gst.ElementFactory.make('audiotestsrc', 'src')
        self.audiosrc.set_property('freq', 50)
        self.audiosrc.set_property('is-live', True)

        self.audiosink = Gst.ElementFactory.make('autoaudiosink', 'sink')

        self.pipeline.add(self.audiosrc)
        self.pipeline.add(self.audiosink)

        self.audiosrc.link(self.audiosink)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

    def on_message(self, bus, message):
        _log.debug('Generator: %s', message)

    def set_freq(self, freq):
        _log.info('freq: %d', freq)
        self.audiosrc.set_property('freq', freq)

    def set_wave(self, wave):
        _log.info('wave: %d', wave)
        self.audiosrc.set_property('wave', wave)

    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    # GStreamer needs this in order to start up all the message passing and
    # worker components i guess.
    GObject.threads_init()
    Gst.init(None)

    win = MainWindow()
    win.show_all()
    Gtk.main()