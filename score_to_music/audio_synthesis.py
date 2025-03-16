import os
import subprocess
from pathlib import Path
from pydub import AudioSegment
from rich.console import Console

console = Console()

def synthesize_wav(midi_path: Path, wav_path: Path, soundfont_path: str) -> bool:
    """
    Synthesize a MIDI file into WAV using FluidSynth with the specified SoundFont.

    Args:
        midi_path (Path): Path to the MIDI file.
        wav_path (Path): Path where WAV file will be saved.
        soundfont_path (str): Path to the SoundFont file (.sf2).

    Returns:
        bool: True if synthesis was successful, False otherwise.
    """
    try:
        console.print(f"[yellow]Synthesizing with SoundFont. Ensure your SoundFont supports the assigned instruments.")
        subprocess.run(["fluidsynth", "-F", str(wav_path), soundfont_path, str(midi_path)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error during MIDI synthesis: {str(e)}")
        return False
    except FileNotFoundError:
        console.print("[red]FluidSynth not found. Please install FluidSynth on your system.")
        return False

def compress_audio(wav_path: Path, output_audio: str, format: str) -> bool:
    """
    Compress a WAV file into MP3 or AAC using pydub.

    Args:
        wav_path (Path): Path to the input WAV file.
        output_audio (str): Path to the output audio file.
        format (str): Audio format ("mp3" or "aac").

    Returns:
        bool: True if compression was successful, False otherwise.
    """
    try:
        audio = AudioSegment.from_wav(str(wav_path))
        if format == "mp3":
            audio.export(output_audio, format="mp3")
        elif format == "aac":
            if output_audio.endswith('.aac'):
                audio.export(output_audio, format="ipod", parameters=["-acodec", "aac", "-strict", "experimental"])
                console.print("[yellow]Note: AAC files work best with .m4a extension instead of .aac")
            else:
                console.print("[red]Error: For AAC output, please use .aac file extension")
                return False
        else:
            raise ValueError(f"Unsupported media file extension: {format}. Use mp3 or aac.")
        return True
    except Exception as e:
        console.print(f"[red]Error during audio compression: {str(e)}")
        return False

