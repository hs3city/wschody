import board
import busio
import usb_midi

import adafruit_midi
import adafruit_vl53l0x
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
import neopixel

from keyboard import white_midi_notes, black_midi_notes

midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

i2c = None
while i2c is None:
    try:
        i2c = busio.I2C(scl=board.GP1, sda=board.GP0)
    except Exception:
        pass

pixels = neopixel.NeoPixel(board.A0, 300)

step_size = 20

step_offset = 10

num_sensors = 1

black_key_threshold = 400
white_key_threshold = 800

debug = True


class Key:
    def __init__(self, note):
        self._note = note
        self._playing = False

    def stop_note(self):
        if self._playing:
            print("Shutting up {0}".format(self._note))
            midi.send(NoteOff(self._note))
            self._playing = False

    def play_note(self):
        if not self._playing:
            print("Playing {0}".format(self._note))
            midi.send(NoteOn(self._note))
            self._playing = True


class Step:
    def __init__(self, sensor, address, white_note, black_note, pixels):
        self._sensor = sensor
        self._address = address
        self._white_key = Key(white_note)
        self._black_key = Key(black_note)
        self._pixels = pixels

    def bling(self, color):
        self.pixels = [color] * step_size

    def tick(self):
        if self._sensor.range < black_key_threshold:
            self._white_key.stop_note()
            self._black_key.play_note()
            self.bling((255, 0, 0))
        elif self._sensor.range < white_key_threshold:
            self._black_key.stop_note()
            self._white_key.play_note()
            self.bling((0, 255, 0))
        else:
            self._black_key.stop_note()
            self._white_key.stop_note()
            self.bling((0, 0, 0))
        if debug:
            print("Sensor range: {0}mm".format(self._sensor.range))


class Piano:
    def __init__(self):
        self._steps = []

    def add_step(self, step):
        self._steps.append(step)
        print("Added sensor with address {0}".format(step._address))

    def initialize_sensors(self):
        for i in range(num_sensors):
            sensor = None
            address = i + 0x30
            print("Waiting for sensor {0}".format(i))
            while sensor is None:
                try:
                    sensor = adafruit_vl53l0x.VL53L0X(i2c)
                except Exception as _:
                    pass
                    # print(".")
            print(sensor)
            sensor.set_address(address)
            step = Step(
                sensor,
                address,
                white_midi_notes[i],
                black_midi_notes[i],
                pixels[i * step_size + (i + 1) * step_size + step_offset],
            )
            self.add_step(step)

    def tick(self):
        for i in range(num_sensors):
            self._steps[i].tick()
        if debug:
            print()


piano = Piano()
piano.initialize_sensors()

while True:
    piano.tick()
