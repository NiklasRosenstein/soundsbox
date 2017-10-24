# soundsbox

Play sounds through your microphone! (Windows)

## Setup

1) Install [VBCABLE Driver Pack43](https://www.vb-audio.com/Cable/index.htm)
2) Configure "CABLE Output" as your new microphone input (eg. in Discord)
3) Configure your actual microphone to redirect into "CABLE Input"
4) Install Python dependencies with `pip install -r requirements.txt`
5) To play MP3 sounds, make sure [ffmpeg](http://ffmpeg.zeranoe.com/builds/)
   is in your `PATH`

## Usage

List available output devices:

```
$ python soundsbox.py -l
Available Output Devices:
  #3: Microsoft Sound Mapper - Output (maxOutputChannels: 2)
  #4: Dell S2716DG-8 (NVIDIA High Def (maxOutputChannels: 2)
  #5: CABLE Input (VB-Audio Virtual C (maxOutputChannels: 2)
  #6: Realtek Digital Output (Realtek (maxOutputChannels: 2)
```

Play a sound file to one or more devices:

```
$ python soundsbox.py -p tonsdmg -d 4,5
```

---

<p align="center">Copyright &copy; 2017 Niklas Rosenstein</p>
