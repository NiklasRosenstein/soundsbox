# Copyright (c) 2017 Niklas Rosenstein
"""
Play sounds to one or more output devices.
"""

from __future__ import print_function
from xml.dom import minidom

import argparse
import atexit
import numpy as np
import os
import pyaudio
import pydub
import random
import sys
import wave

SOUNDS_DIR = os.path.join(os.path.dirname(__file__), 'sounds')

audio = pyaudio.PyAudio()
atexit.register(audio.terminate)

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--list', action='store_true', help='List available input and output devices.')
parser.add_argument('-d', '--device', help='Output device indices (comma separated).')
parser.add_argument('-p', '--play', help='Play the specified sound file.')
parser.add_argument('-v', '--volume', type=float, default=0.2, help='Volume of the played sound.')


class Sound(object):

  def __init__(self, filename, name, labels, volume):
    self.filename = filename
    self.name = name
    self.labels = labels
    self.volume = volume

  def __repr__(self):
    return 'Sound(filename={!r}, name={!r}, labels={!r}, volume={!r})'\
      .format(self.filename, self.name, self.labels, self.volume)


class SoundData(object):

  @staticmethod
  def bytes_to_array(bytes, sample_width):
    dtype = {1: np.int8, 2: np.int16, 4: np.float32}[sample_width]
    return np.fromstring(bytes, dtype)

  @classmethod
  def from_file(cls, filename):
    if filename.endswith('.wav'):
      return cls.from_wav(filename)
    elif filename.endswith('.mp3'):
      return cls.from_mp3(filename)
    else:
      raise ValueError('unsupported file format: "{}"'.format(self.filename))

  @classmethod
  def from_wav(cls, filename):
    with wave.open(filename) as wf:
      rate = wf.getframerate()
      channels = wf.getnchannels()
      width = wf.getsampwidth()
      data = wf.readframes(wf.getnframes())
    return cls(cls.bytes_to_array(data, width), rate, channels)

  @classmethod
  def from_mp3(cls, filename):
    sound = pydub.AudioSegment.from_mp3(filename)
    data = cls.bytes_to_array(sound._data, sound.sample_width)
    return cls(data, sound.frame_rate, sound.channels)

  def __init__(self, data, rate, channels):
    assert isinstance(data, np.ndarray)
    assert data.dtype in (np.int8, np.int16, np.float32)
    self.data = data
    self.rate = rate
    self.channels = channels

  @property
  def pyaudio_format(self):
    if self.data.dtype == np.int8:
      return pyaudio.paInt8
    elif self.data.dtype == np.int16:
      return pyaudio.paInt16
    elif self.data.dtype == np.float32:
      return pyaudio.paFloat32
    else:
      raise ValueError('unexpected sound data type: {!r}'.format(self.data.dtype))


def read_sounds(filename):
  directory = os.path.dirname(os.path.abspath(filename))
  with open(filename) as fp:
    sounds = minidom.parse(fp).childNodes[0]
  if sounds.nodeName != 'sounds':
    print('warning: invalid sounds configuration (expected <sounds/> node)')
    print('warning:   in', filename)
    return []
  result = []
  labels = list(filter(bool, sounds.getAttribute('labels').split(' ')))
  volume = float(sounds.getAttribute('volume') or '1.0')
  for sound in sounds.childNodes:
    if sound.nodeType != sound.ELEMENT_NODE:
      continue
    if sound.nodeName != 'sound':
      print('warning: invalid sounds configuration (expected <sound/> node)')
      print('warning:   in', filename)
      return []
    filename = os.path.join(directory, sound.getAttribute('file'))
    sound_labels = list(filter(bool, sound.getAttribute('labels').split(' ')))
    name = sound.getAttribute('name') or os.path.splitext(os.path.basename(filename))[0]
    sound_volume = float(sound.getAttribute('volume') or '1.0') * volume
    result.append(Sound(filename, name, labels + sound_labels, sound_volume))
  return result


def read_all_sounds(directory):
  if not os.path.isdir(directory):
    return; yield

  config = os.path.join(directory, '_sounds.xml')
  if os.path.isfile(config):
    yield from read_sounds(config)

  for name in os.listdir(directory):
    name = os.path.join(directory, name)
    if os.path.isdir(name):
      yield from read_all_sounds(name)


def list_devices():
  info = audio.get_host_api_info_by_index(0)
  inputs = []
  outputs = []
  for i in range(info['deviceCount']):
    dev = audio.get_device_info_by_host_api_device_index(0, i)
    if dev['maxInputChannels'] > 0:
      inputs.append((i, dev))
    if dev['maxOutputChannels'] > 0:
      outputs.append((i, dev))
  #print('Available Input Devices:')
  #for i, dev in inputs:
  #  print('  #{}: {} (maxInputChannels: {})'.format(i, dev['name'], dev['maxInputChannels']))
  print('Available Output Devices:')
  for i, dev in outputs:
    print('  #{}: {} (maxOutputChannels: {})'.format(i, dev['name'], dev['maxOutputChannels']))


def play_sound(filename, devices, volume):
  if devices is None:
    devices = [None]  # Default output stream
  elif isinstance(devices, str):
    devices = [None if x == '' else int(x) for x in devices.split(',')]

  sound = SoundData.from_file(filename)

  # Open output streams for every device specified.
  streams = []
  for device in devices:
    streams.append(audio.open(
      format=sound.pyaudio_format,
      channels=sound.channels,
      rate=sound.rate,
      output=True,
      output_device_index=device
    ))

  # Write to the streams.
  for i in range(0, len(sound.data), 2048):
    data = (sound.data[i:i+2048] * volume).astype(sound.data.dtype).tobytes()
    [x.write(data) for x in streams]

  [x.stop_stream() for x in streams]
  [x.close() for x in streams]


def main():
  args = parser.parse_args()

  if args.list:
    list_devices()
    return

  if args.play:
    if not os.path.exists(args.play):
      matches = []
      for sound in read_all_sounds(SOUNDS_DIR):
        if sound.name == args.play or args.play in sound.labels:
          matches.append(sound)
      if not matches:
        print('error: could not find sound for {!r}'.format(args.play))
        return 1
      choice = random.choice(matches)
      args.play = choice.filename
      args.volume *= choice.volume
    play_sound(args.play, args.device, args.volume)
    return


if __name__ == '__main__':
  sys.exit(main())
