import os
import sys
import argparse
import traceback
from pathlib import Path

from rich.console import Console
from score_to_music import score_conversion, score_adaptation, audio_synthesis

console = Console()

def parse_instruments(instr_str: str):
    """
    Parse a comma-separated list of instrument program numbers.
    """
    try:
        instruments = [int(num.strip()) for num in instr_str.split(',')]
        for i in instruments:
            if i < 0 or i > 127:
                raise ValueError(f"Instrument {i} is out of valid MIDI range 0-127.")
        return instruments
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Invalid instrument list: {e}")

def get_available_presets(soundfont_file: str):
    """
    Return a set of preset numbers available in the specified SoundFont file.
    Requires the 'sf2utils' package.
    """
    try:
        from sf2utils.sf2parse import Sf2File
    except ImportError:
        console.print("[red]The 'sf2utils' package is required to list instruments. Please install it with 'pip install sf2utils'")
        sys.exit(1)
    available = set()
    try:
        with open(soundfont_file, 'rb') as f:
            sf2 = Sf2File(f)
            for preset in sf2.presets:
                try:
                    preset_num = getattr(preset, 'preset', None)
                    if preset_num is not None:
                        available.add(preset_num)
                except Exception:
                    continue
        return available
    except Exception as e:
        console.print(f"[red]Error reading SoundFont file: {e}")
        sys.exit(1)

def list_instruments(soundfont_file: str):
    """
    List all presets available in the specified SoundFont file.
    Requires the 'sf2utils' package.
    Safely ignores presets that do not have a preset number.
    The output is sorted by preset number.
    """
    try:
        from sf2utils.sf2parse import Sf2File
    except ImportError:
        console.print("[red]The 'sf2utils' package is required to list instruments. Please install it with 'pip install sf2utils'")
        sys.exit(1)
    try:
        with open(soundfont_file, 'rb') as f:
            sf2 = Sf2File(f)
            presets = []
            for preset in sf2.presets:
                try:
                    preset_num = getattr(preset, 'preset', None)
                    if preset_num is None:
                        continue
                    presets.append((preset_num, preset.name, preset.bank))
                except Exception:
                    continue
            presets.sort(key=lambda x: x[0])
            if presets:
                console.print(f"[green]SoundFont '{soundfont_file}' contains the following presets:")
                for num, name, bank in presets:
                    console.print(f"  {num:3d}: {name} (Bank {bank})")
            else:
                console.print("[yellow]No presets found in the SoundFont.")
    except Exception as e:
        console.print(f"[red]Error reading SoundFont file: {e}")
        sys.exit(1)
    sys.exit(0)

def main(score_file_path: str, soundfont_sf2_file_path: str, media_file_path: str, instrument_programs: list):
    """
    Main function to convert a score to an audio file using the specified SoundFont and instruments.
    Before conversion, this function reads the available presets from the SoundFont file and verifies that
    every requested instrument is present. If one or more instruments are missing, an error is printed and
    conversion is aborted.
    """
    # Verify requested instruments are available
    available = get_available_presets(soundfont_sf2_file_path)
    missing = [str(inst) for inst in instrument_programs if inst not in available]
    if missing:
        console.print(f"[red]Error: The following requested instrument(s) are not available in the provided SoundFont: {', '.join(missing)}")
        console.print("Please use the --list-instruments flag to see the full list of available presets.")
        return False

    output_extension = Path(media_file_path).suffix[1:].lower()
    if output_extension not in ["mp3", "aac", "m4a"]:
        console.print(f"[red]Error: Unsupported output format: {output_extension}")
        console.print("[yellow]Supported output formats: .mp3, .m4a (recommended for AAC)")
        return False

    format_map = {"mp3": "mp3", "aac": "aac", "m4a": "aac"}
    audio_format = format_map[output_extension]

    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    xml_path = temp_dir / "score.xml"
    midi_path = temp_dir / "adapted_version.mid"
    wav_path = temp_dir / "audio.wav"

    # Reset any existing environment flags
    os.environ.pop('USING_DIRECT_MIDI', None)
    os.environ.pop('MIDI_PATH', None)

    console.print(f"[cyan]Using instruments: {', '.join(str(i) for i in instrument_programs)}")

    # Step 1: Convert score to MusicXML
    console.print(f"Converting {score_file_path} to MusicXML...")
    xml_conversion_success = score_conversion.convert_score_to_musicxml(score_file_path, xml_path)
    if not xml_conversion_success:
        console.print("[red]Error: Score conversion failed.")
        return False

    # Step 2: Adapt the score for the specified instruments
    try:
        if os.environ.get('USING_DIRECT_MIDI') == 'true':
            midi_path = Path(os.environ.get('MIDI_PATH'))
            console.print(f"[green]Using direct MIDI file: {midi_path}")
        else:
            console.print("Adapting score for multiple instruments...")
            adapted_score = score_adaptation.adapt_score_for_instruments(xml_path, instrument_programs)
            if adapted_score is None:
                console.print("[red]Score adaptation returned no result.")
                return False
            adapted_score.write('midi', fp=str(midi_path))
    except Exception as e:
        console.print(f"[red]Error adapting score: {str(e)}")
        traceback.print_exc()
        return False

    # Step 3: Synthesize audio (WAV) using FluidSynth
    console.print(f"Synthesizing audio using SoundFont: {Path(soundfont_sf2_file_path).name}...")
    if not audio_synthesis.synthesize_wav(midi_path, wav_path, soundfont_sf2_file_path):
        return False

    # Step 4: Compress audio to final format (MP3 or AAC)
    console.print(f"Compressing audio to {audio_format.upper()}...")
    if not audio_synthesis.compress_audio(wav_path, media_file_path, format=audio_format):
        return False

    console.print(f"[green]Audio file successfully generated: {media_file_path}")

    # Clean up temporary files on success
    for file in [xml_path, midi_path, wav_path]:
        if file.exists():
            file.unlink()
    os.environ.pop('USING_DIRECT_MIDI', None)
    os.environ.pop('MIDI_PATH', None)
    return True

def cli():
    """
    Command-line interface.
    Sub-modes:
      - Conversion mode (default): Convert a score to audio.
      - Instrument listing mode: List the instruments available in the provided SoundFont.
        In instrument listing mode, provide only the SoundFont file as the first positional argument.
    The sample preset numbers shown below are for example only.
    To view the full list of available instruments, use the --list-instruments flag.
    
    Sample preset numbers:
      0: Piano (default)       6: Harpsichord       19: Church Organ
      24: Nylon Guitar         25: Steel Guitar       26: Jazz Guitar
      33: Electric Bass        40: Violin             41: Viola
      42: Cello                56: Trumpet            60: French Horn
      68: Oboe                 69: English Horn       70: Bassoon
      71: Clarinet             73: Flute              74: Recorder
    """
    description = """
Convert a music score to an audio file using a specified SoundFont.

Sub-modes:
  Conversion mode (default): Convert a score to audio.
  Instrument listing mode: List the instruments available in the provided SoundFont.
    In instrument listing mode, provide only the SoundFont file as the first positional argument.

Supported input formats (conversion mode):
  - MusicXML (.xml, .musicxml, .mxl)
  - MIDI (.mid, .midi)
  - MuseScore (.mscz, .mscx)

Supported output formats (conversion mode):
  - MP3 (.mp3)
  - M4A (.m4a) – recommended container for AAC audio
  - AAC (.aac) – may have compatibility issues on some systems

Sample preset numbers:
  0: Piano (default)       6: Harpsichord       19: Church Organ
  24: Nylon Guitar         25: Steel Guitar       26: Jazz Guitar
  33: Electric Bass        40: Violin             41: Viola
  42: Cello                56: Trumpet            60: French Horn
  68: Oboe                 69: English Horn       70: Bassoon
  71: Clarinet             73: Flute              74: Recorder

Note: The -i flag accepts a comma-separated list to mix multiple instruments.
To view the full list of available instruments in the SoundFont, use the --list-instruments flag.
    """

    class ArgumentParserWithHelp(argparse.ArgumentParser):
        def error(self, message):
            self.print_usage(sys.stderr)
            self.exit(2, f"{self.prog}: error: {message}\n\n{description}\n")

    parser = ArgumentParserWithHelp(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # In conversion mode, three positional arguments are required.
    # In instrument listing mode, only one positional argument (SoundFont file path) is required.
    parser.add_argument(
        "score_file_path",
        type=str,
        nargs="?",
        help="(Conversion mode) Path to the input score file (.xml, .musicxml, .mxl, .mid, .midi, .mscz, .mscx) or (Listing mode) the SoundFont file (.sf2)"
    )
    parser.add_argument(
        "soundfont_sf2_file_path",
        type=str,
        nargs="?",
        help="(Conversion mode) Path to the SoundFont file (.sf2)"
    )
    parser.add_argument(
        "media_file_path",
        type=str,
        nargs="?",
        help="(Conversion mode) Path to the output audio file (.mp3, .m4a, or .aac)"
    )
    parser.add_argument(
        "-i", "--instrument",
        type=parse_instruments,
        default=[0],
        help="Comma-separated MIDI program numbers (0-127) for the instruments. Default is 0 (Piano)"
    )
    parser.add_argument(
        "--list-instruments",
        action="store_true",
        help="List the instruments contained in the provided SoundFont file and exit. In this mode, provide only the SoundFont file as the first positional argument."
    )

    args = parser.parse_args()

    if args.list_instruments:
        if args.score_file_path is None:
            parser.error("SoundFont file path is required for instrument listing mode (--list-instruments).")
        list_instruments(args.score_file_path)

    if args.score_file_path is None or args.soundfont_sf2_file_path is None or args.media_file_path is None:
        parser.error("score_file_path, soundfont_sf2_file_path, and media_file_path are required for conversion mode.")

    success = main(args.score_file_path, args.soundfont_sf2_file_path, args.media_file_path, args.instrument)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    cli()

