import os
import shutil
import subprocess
import platform
from pathlib import Path
import traceback
from music21 import converter
from rich.console import Console

console = Console()

def convert_score_to_musicxml(score_path: str, output_xml_path: Path) -> bool:
    """
    Convert a score file to MusicXML based on its format.
    Handles MXL, MIDI, and MuseScore formats.

    Args:
        score_path (str): Path to the score file.
        output_xml_path (Path): Path where the MusicXML will be saved.

    Returns:
        bool: True if conversion was successful, False otherwise.
    """
    ext = Path(score_path).suffix.lower()

    if ext in ['.xml', '.musicxml', '.mxl']:
        console.print("[green]Input is already in MusicXML format. Using directly.")
        try:
            score = converter.parse(score_path)
            score.write('musicxml', fp=str(output_xml_path))
            return True
        except Exception as e:
            console.print(f"[red]Error converting MusicXML file: {str(e)}")
            return False

    elif ext in ['.mid', '.midi']:
        console.print("[cyan]Converting MIDI to MusicXML...")
        try:
            # Approach 1: Direct MIDI processing (bypassing full MusicXML conversion)
            console.print("[cyan]Attempting direct MIDI processing without MusicXML conversion...")
            midi_path = output_xml_path.with_suffix('.mid')
            shutil.copy(score_path, midi_path)
            with open(output_xml_path, 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?><placeholder>MIDI</placeholder>')
            os.environ['USING_DIRECT_MIDI'] = 'true'
            os.environ['MIDI_PATH'] = str(midi_path)
            return True
        except Exception as e:
            console.print(f"[yellow]Direct MIDI approach failed: {str(e)}")
            console.print("[cyan]Trying alternative approach with MuseScore...")
            try:
                mscore_path = None
                for possible_path in [
                    "mscore", "musescore", "MuseScore",
                    "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
                    "/Applications/MuseScore 3.app/Contents/MacOS/mscore"
                ]:
                    try:
                        result = subprocess.run(["which", possible_path],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                        if result.returncode == 0:
                            mscore_path = possible_path.strip()
                            break
                    except:
                        continue
                if mscore_path:
                    console.print("[cyan]Using MuseScore to convert MIDI...")
                    result = subprocess.run([mscore_path, "-o", str(output_xml_path), score_path],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                    if result.returncode == 0 and output_xml_path.exists():
                        console.print("[green]Successfully converted MIDI to MusicXML using MuseScore!")
                        return True
                else:
                    console.print("[yellow]MuseScore not found. Cannot use it for conversion.")
            except Exception as e:
                console.print(f"[yellow]MuseScore conversion failed: {str(e)}")
            try:
                console.print("[cyan]Falling back to music21 for MIDI conversion...")
                midi_score = converter.parse(score_path,
                                             quantizePost=True,
                                             quarterLengthDivisors=(4, 3),
                                             maxLevoDistance=1)
                midi_path = output_xml_path.with_suffix('.mid')
                midi_score.write('midi', fp=str(midi_path))
                with open(output_xml_path, 'w') as f:
                    f.write('<?xml version="1.0" encoding="UTF-8"?><placeholder>MIDI</placeholder>')
                os.environ['USING_DIRECT_MIDI'] = 'true'
                os.environ['MIDI_PATH'] = str(midi_path)
                return True
            except Exception as e:
                console.print("[red]All MIDI conversion approaches failed:")
                tb = traceback.format_exc()
                console.print(f"[yellow]{tb}")
                return False

    elif ext in ['.mscz', '.mscx']:
        console.print("[cyan]Converting MuseScore file to MusicXML...")
        try:
            mscore_path = None
            for possible_path in [
                "mscore", "musescore", "MuseScore",
                "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
                "/Applications/MuseScore 3.app/Contents/MacOS/mscore",
                r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe",
                r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe",
                r"C:\Program Files (x86)\MuseScore 4\bin\MuseScore4.exe",
                r"C:\Program Files (x86)\MuseScore 3\bin\MuseScore3.exe"
            ]:
                try:
                    if platform.system() == "Windows" and possible_path.startswith("C:"):
                        if Path(possible_path).exists():
                            mscore_path = possible_path
                            break
                    else:
                        result = subprocess.run(["which", possible_path],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                        if result.returncode == 0:
                            mscore_path = possible_path.strip()
                            break
                except:
                    continue
            if not mscore_path:
                console.print("[red]MuseScore not found. Cannot convert MuseScore file.")
                return False
            result = subprocess.run([mscore_path, "-o", str(output_xml_path), score_path],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            if result.returncode == 0 and output_xml_path.exists():
                console.print("[green]Successfully converted MuseScore file to MusicXML!")
                return True
            else:
                console.print("[red]Failed to convert MuseScore file.")
                return False
        except Exception as e:
            console.print(f"[red]Error converting MuseScore file: {str(e)}")
            return False

    else:
        console.print(f"[red]Unsupported score format: {ext}")
        console.print("[yellow]Supported formats: .xml, .musicxml, .mxl, .mid, .midi, .mscz, .mscx")
        return False

