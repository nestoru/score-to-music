# Score-to-Music
This project converts music scores into audio files using specified SoundFonts, supporting multiple input formats including digital score formats.

## Features
- **Multiple input format support**:
  - Digital score formats (MusicXML, MuseScore)
  - MIDI files (with conversion to MusicXML)
- **Customizable instrument sounds** via SoundFont files
- **Multi-instrument support** for creating orchestral arrangements
- **Instrument selection** using MIDI program numbers
- **High-quality audio synthesis** with FluidSynth
- **Audio compression** to MP3 or AAC formats

## Prerequisites
- Python 3.11 or 3.12
- **MuseScore** - Recommended for score conversion
- FluidSynth for audio synthesis
- FFmpeg for audio compression

## Installation

### 1. Install Poetry
Follow the instructions on Poetry's website: https://python-poetry.org/docs/#installation.

### 2. Install MuseScore (Recommended)
MuseScore provides the best results for format conversion:

- **macOS**: 
  ```
  brew install --cask musescore
  ```
  Or download from [MuseScore website](https://musescore.org/en/download)
  
- **Linux**: 
  ```
  sudo apt install musescore
  ```
  
- **Windows**:
  Download from [MuseScore website](https://musescore.org/en/download)

### 3. Install FluidSynth and FFmpeg
- **macOS**:
  ```
  brew install fluid-synth ffmpeg
  ```
- **Linux**:
  ```
  sudo apt install fluidsynth ffmpeg
  ```
- **Windows**:
  Download from respective websites or use package managers like Chocolatey

### 4. Set Up Python Environment
```
poetry env use python3.12
poetry shell
```

### 5. Install Project Dependencies
```
poetry install
```

### 6. Get a SoundFont File
You need a SoundFont (.sf2) file for the instrument sounds. Some options:
- [FluidR3 GM SoundFont](https://musical-artifacts.com/artifacts/713) - General MIDI sound set
- [GeneralUser GS SoundFont](https://musical-artifacts.com/artifacts/631) - Another high-quality GM set
- Specialized instrument SoundFonts (piano, organ, orchestra, etc.)

## Usage
Convert a score to audio with a single command:

### Single Instrument
```
poetry run score2music <score_file_path> <soundfont_sf2_file_path> <media_file_path> [--instrument PROGRAM_NUMBER]
```

For example, to render as piano (default):
```
poetry run score2music "Bach_BWV_733.mxl" "GeneralUser_GS.sf2" "Bach_BWV_733.mp3"
```

To render with a guitar sound (program 24):
```
poetry run score2music "Bach_BWV_733.mxl" "GeneralUser_GS.sf2" "Bach_BWV_733_guitar.mp3" --instrument 24
```

### Multiple Instruments (Orchestra Mode)
New in this version: you can now specify multiple instruments to create orchestral arrangements!
Use comma-separated values to specify multiple instruments:

```
poetry run score2music <score_file_path> <soundfont_sf2_file_path> <media_file_path> -i <program_number_1>,<program_number_2>,...
```

For example, to create a string quartet:
```
poetry run score2music "Bach_BWV_733.mxl" "GeneralUser_GS.sf2" "Bach_BWV_733_quartet.mp3" -i 40,41,42,43
```

This combines Violin (40), Viola (41), Cello (42), and Contrabass (43).

For a full orchestra arrangement:
```
poetry run score2music "Bach_BWV_733.mxl" "GeneralUser_GS.sf2" "Bach_BWV_733_orchestra.mp3" -i 0,40,41,42,56,60,68,71,73
```

This combines Piano, Violin, Viola, Cello, Trumpet, French Horn, Oboe, Clarinet, and Flute.

### View Available Instruments
To see a list of all available MIDI program numbers and instrument names:

```
poetry run score2music --list-instruments
```

### Common MIDI Program Numbers
| Program | Instrument         | Program | Instrument         | Program | Instrument         |
|---------|-------------------|---------|-------------------|---------|-------------------|
| 0       | Piano (default)    | 24      | Nylon Guitar       | 25      | Steel Guitar       |
| 26      | Jazz Guitar        | 33      | Electric Bass      | 40      | Violin             |
| 41      | Viola              | 42      | Cello              | 56      | Trumpet            |
| 60      | French Horn        | 68      | Oboe               | 71      | Clarinet           |
| 73      | Flute              | 19      | Church Organ       | 47      | Orchestral Harp    |

For a complete list of MIDI program numbers, see the [General MIDI specification](https://en.wikipedia.org/wiki/General_MIDI#Program_change_events).

### Supported Input Formats:
- **Digital Formats**:
  - MusicXML (.xml, .musicxml, .mxl) - Primary recommended format
  - MIDI (.mid, .midi) - Note: Some complex MIDI files may require pre-processing
  - MuseScore (.mscz, .mscx)

### Supported Output Formats:
- MP3 (.mp3)
- M4A (.m4a) - Recommended container for AAC audio
- AAC (.aac) - May have compatibility issues on some systems

## How It Works

1. **Score Processing**: The program adapts to the input format
   - MusicXML formats are processed directly
   - MIDI files are converted to MusicXML
   - MuseScore files are converted to MusicXML

2. **Instrument Adaptation**:
   - The score is prepared for playback
   - Each instrument is assigned to a separate track
   - When multiple instruments are specified, parts are assigned intelligently
   - Each instrument track uses the specified MIDI program

3. **Audio Generation**:
   - Creates MIDI tracks for each instrument
   - Synthesizes audio for each instrument using FluidSynth with the specified SoundFont
   - Mixes all instrument tracks together
   - Compresses to MP3 or AAC based on file extension

## Troubleshooting

- **Digital Score Formats**: For best results, use MusicXML, or MuseScore files directly
- **MIDI Conversion Issues**: 
  - Some complex MIDI files may not convert properly to MusicXML
  - If experiencing conversion errors, try first converting the MIDI file to MusicXML using a DAW or notation software
- **Instrument Selection**:
  - If the specified instrument doesn't sound right, ensure your SoundFont includes that instrument
  - Some SoundFonts only include a limited set of instruments
  - For full instrument support, use a complete General MIDI SoundFont
- **Multi-instrument Mode**:
  - The program will intelligently assign instruments to available parts in the score
  - If there are more instruments than parts, some instruments will play all parts
  - For best results, match the number of instruments to the number of parts in the score
- **AAC Output Issues**:
  - For AAC audio, use .m4a extension instead of .aac for better compatibility
  - If AAC encoding fails, try MP3 format or manually convert using FFmpeg
- **MuseScore Not Found**: Make sure MuseScore is installed and in your PATH
- **SoundFont Quality**: The sound quality depends greatly on the SoundFont used

## Finding Digital Scores
Many classical works in the public domain are available in digital formats:

- **MuseScore.com** - User-created scores in MuseScore format (.mscz)
- **IMSLP** - Sometimes includes MusicXML and MIDI alongside PDFs
- **OpenScore** - High-quality digital transcriptions of classical works
- **Various GitHub repositories** - Digital score collections

## Working with the Virtual Environment
To work within the Poetry-managed virtual environment, you can:

1. **Enter the Shell**:
   ```
   poetry shell
   score2music <score_file_path> <soundfont_sf2_file_path> <media_file_path>
   ```

2. **Use Poetry Run**:
   ```
   poetry run score2music <score_file_path> <soundfont_sf2_file_path> <media_file_path>
   ```

## Share relevant project files and their content
```
fd -H -t f --exclude '.git' --exclude 'poetry.lock' -0 | xargs -0 -I {} sh -c 'echo "File: {}"; cat {}'
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Nestor Urquiza
