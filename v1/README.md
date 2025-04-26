# Hedra API Starter

This repository shows how to use the Hedra API, which is currently in beta.

We've included examples assets under the `assets` folder which are stored via `git-lfs`. You must install [git-lfs](https://git-lfs.com) prior to running the examples and cloning the repo or run `git lfs fetch`.

# Dependencies

* Python 3.10
* requests (`pip install requests`)
* `git-lfs`

# Notes

The Hedra API supports generating videos up to 4 minute videos. You provide either a 1:1, 16:9, or 9:16 `.jpg`, a `.wav`, and receive back an mp4 video.

# Documentation

Available [here](https://www.hedra.com/docs)

# Examples

## 16:9

```bash
python main.py --api-key sk_hedra-*** --audio assets/audio.wav --img assets/16_9.jpg --ar 16:9
```

## 9:16

```bash
python main.py --api-key sk_hedra-*** --audio assets/audio.wav --img assets/9_16.jpg --ar 9:16
```

## 1:1

```bash
python main.py --api-key sk_hedra-*** --audio assets/audio.wav --img assets/1:1.jpg --ar 1:1
```

## List available voices (how to get the voice ID)
```bash
python get_voices.py --api-key sk_hedra-***
```

## Generate audio and images
```bash
python main.py --api-key sk_hedra-*** --audio-text "hello world" --voice-id FGY2WhTYpPnrIDTdsKH5 --img-prompt "cowboy" --ar 16:9
```

# Questions?

Contact support@hedra.com
