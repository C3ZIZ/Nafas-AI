# Nafas
An AI-powered health project that analyzes breath sounds to detect potential respiratory diseases.

## Quick Start

- Run the API locally:

```bash
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /` — Root endpoint, returns a simple alive message.
- `GET /inspect/{filename}` — Inspect an audio file under `data/` and return metadata (sample rate, duration, samples, device info).
- `GET /plot/{filename}` — Return a PNG waveform image for the given audio file.
- `GET /process/{filename}` — Process audio and return annotated segments summary (uses `.txt` annotation files when present).

## Utilities (app/utils.py)

- `get_audio_info(file_path)` — Load audio and return sample rate, duration, total samples, and GPU/device info.
- `generate_waveform_plot(file_path)` — Produce a PNG bytes buffer containing a waveform plot ready to stream.
- `butter_bandpass_filter(data, ...)` — Apply a Butterworth band-pass filter to audio data.
- `get_segments(audio_path, annotation_path)` — Read annotation file and slice audio into labeled segments.

## Notes

- Place audio files and their `.txt` annotations in the `data/` folder. Annotation files should match the audio filename (e.g., `101_1b1_Al_sc_Meditron.wav` and `101_1b1_Al_sc_Meditron.txt`).
