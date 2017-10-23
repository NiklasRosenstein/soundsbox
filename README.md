# soundsbox

Play sounds through your microphone! (Windows)

## Setup

1) Install [VBCABLE Driver Pack43](https://www.vb-audio.com/Cable/index.htm)
2) Configure "CABLE Output" as your new microphone input (eg. in Discord)
3) Configure your actual microphone to redirect into "CABLE Input"
4) Install Python dependencies with `pip install -r requirements.txt`

## Usage

List available input and output devices:

```
$ python soundsbox.py -l
Available Input Devices:
  #0: Microsoft Sound Mapper - Input (maxInputChannels: 2)
  #1: CABLE Output (VB-Audio Virtual  (maxInputChannels: 2)
  #2: Microphone (USB MICROPHONE) (maxInputChannels: 2)
Available Output Devices:
  #3: Microsoft Sound Mapper - Output (maxOutputChannels: 2)
  #4: Dell S2716DG-8 (NVIDIA High Def (maxOutputChannels: 2)
  #5: CABLE Input (VB-Audio Virtual C (maxOutputChannels: 2)
  #6: Realtek Digital Output (Realtek (maxOutputChannels: 2)
```

Play a sound file to one or more output devices:

```
$ python soundsbox.py -p tonsdmg.wav -d 1,5
```

---

<p align="center">Copyright &copy; 2017 Niklas Rosenstein</p>
