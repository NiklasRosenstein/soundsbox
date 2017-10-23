# Copyright (c) 2017 Niklas Rosenstein
"""
Play sounds to one or more output devices.
"""

from __future__ import print_function

import argparse
import atexit
import pyaudio
import numpy as np
import sys
import wave

audio = pyaudio.PyAudio()
atexit.register(audio.terminate)

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--list', action='store_true', help='List available input and output devices.')
parser.add_argument('-d', '--device', help='Output device indices (comma separated).')
parser.add_argument('-p', '--play', help='Play the specified sound file.')
parser.add_argument('-v', '--volume', type=float, default=0.05, help='Volume of the played sound.')


def main():
  args = parser.parse_args()

  if args.list:
    info = audio.get_host_api_info_by_index(0)
    inputs = []
    outputs = []
    for i in range(info['deviceCount']):
      dev = audio.get_device_info_by_host_api_device_index(0, i)
      if dev['maxInputChannels'] > 0:
        inputs.append((i, dev))
      if dev['maxOutputChannels'] > 0:
        outputs.append((i, dev))
    print('Available Input Devices:')
    for i, dev in inputs:
      print('  #{}: {} (maxInputChannels: {})'.format(i, dev['name'], dev['maxInputChannels']))
    print('Available Output Devices:')
    for i, dev in outputs:
      print('  #{}: {} (maxOutputChannels: {})'.format(i, dev['name'], dev['maxOutputChannels']))
    return

  if args.play:
    sound = wave.open(args.play)
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

    devices = [None]
    if args.device:
      devices = map(int, args.device.split(','))
    streams = []
    for device in devices:
      stream = audio.open(format=format,
                          channels=sound.getnchannels(),
                          rate=sound.getframerate(),
                          output=True,
                          output_device_index=device)
      streams.append(stream)
    while True:
      data = (np.fromstring(sound.readframes(2048), dtype) * args.volume).astype(dtype)
      if len(data) == 0: break
      data = data.tobytes()
      [x.write(data) for x in streams]
    [x.stop_stream() for x in streams]
    [x.close() for x in streams]
    return


if __name__ == '__main__':
  sys.exit(main())
