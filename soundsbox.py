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

  sound = wave.open(filename)
  width = sound.getsampwidth()

  if width == 1:
    format = pyaudio.paInt8
    dtype = np.int8
  elif width == 2:
    format = pyaudio.paInt16
    dtype = np.int16
  else:
    print('error: unexpected wave sample width:', width)
    return 1

  # Open output streams for every device specified.
  streams = []
  for device in devices:
    streams.append(audio.open(
      format=format,
      channels=sound.getnchannels(),
      rate=sound.getframerate(),
      output=True,
      output_device_index=device
    ))

  # Write to the streams.
  while True:
    data = sound.readframes(2048)
    if not data:
      break
    data = (np.fromstring(data, dtype) * volume).astype(dtype).tobytes()
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
