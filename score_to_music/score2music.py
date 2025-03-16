import os
import subprocess
import tempfile
import platform
import traceback
from pathlib import Path
import shutil
from music21 import converter, stream, instrument
from pydub import AudioSegment
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def convert_score_to_musicxml(score_path, output_xml_path):
    """
    Convert a score file to MusicXML based on its format.
    Handles MXL, MIDI, and MuseScore formats.
    
    Args:
        score_path (str): Path to the score file
        output_xml_path (str): Path where the MusicXML will be saved
        
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    # Check file extension
    ext = Path(score_path).suffix.lower()
    
    # If already MusicXML, just copy it
    if ext in ['.xml', '.musicxml', '.mxl']:
        console.print(f"[green]Input is already in MusicXML format. Using directly.")
        try:
            # For .mxl files, we need to convert them to uncompressed .xml
            score = converter.parse(score_path)
            score.write('musicxml', fp=output_xml_path)
            return True
        except Exception as e:
            console.print(f"[red]Error converting MusicXML file: {str(e)}")
            return False
    
    # If MIDI, try to convert to MusicXML using multiple approaches
    elif ext in ['.mid', '.midi']:
        console.print(f"[cyan]Converting MIDI to MusicXML...")
        
        # For MIDI files, we'll try multiple approaches
        try:
            # Approach 1: Try direct MIDI to MIDI conversion first (bypassing MusicXML)
            console.print(f"[cyan]Attempting direct MIDI processing without MusicXML conversion...")
            
            # Simply copy the MIDI file to the temporary location
            midi_path = output_xml_path.with_suffix('.mid')
            shutil.copy(score_path, midi_path)
            
            # Write a placeholder XML file so the rest of the pipeline works
            with open(output_xml_path, 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?><placeholder>MIDI</placeholder>')
            
            # Set a flag to indicate we're using direct MIDI
            os.environ['USING_DIRECT_MIDI'] = 'true'
            os.environ['MIDI_PATH'] = str(midi_path)
            
            return True
            
        except Exception as e:
            console.print(f"[yellow]Direct MIDI approach failed: {str(e)}")
            console.print(f"[cyan]Trying alternative approach with MuseScore...")
            
            # Approach 2: Use MuseScore if available
            try:
                # Find MuseScore
                mscore_path = None
                for possible_path in [
                    "mscore", "musescore", "MuseScore", 
                    "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
                    "/Applications/MuseScore 3.app/Contents/MacOS/mscore"
                ]:
                    try:
                        result = subprocess.run(
                            ["which", possible_path], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE
                        )
                        if result.returncode == 0:
                            mscore_path = possible_path.strip()
                            break
                    except:
                        continue
                
                if mscore_path:
                    console.print(f"[cyan]Using MuseScore to convert MIDI...")
                    result = subprocess.run([
                        mscore_path,
                        "-o", output_xml_path,
                        score_path
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    if result.returncode == 0 and Path(output_xml_path).exists():
                        console.print("[green]Successfully converted MIDI to MusicXML using MuseScore!")
                        return True
                else:
                    console.print("[yellow]MuseScore not found. Cannot use it for conversion.")
            except Exception as e:
                console.print(f"[yellow]MuseScore conversion failed: {str(e)}")
            
            # Approach 3: Fall back to music21
            try:
                console.print(f"[cyan]Falling back to music21 for MIDI conversion...")
                # Try with different import parameters
                midi_score = converter.parse(
                    score_path, 
                    quantizePost=True, 
                    quarterLengthDivisors=(4, 3),
                    maxLevoDistance=1
                )
                
                # Stream to MIDI without try to convert to MusicXML
                midi_path = output_xml_path.with_suffix('.mid')
                midi_score.write('midi', fp=midi_path)
                
                # Write a placeholder XML file so the rest of the pipeline works
                with open(output_xml_path, 'w') as f:
                    f.write('<?xml version="1.0" encoding="UTF-8"?><placeholder>MIDI</placeholder>')
                
                # Set a flag to indicate we're using direct MIDI
                os.environ['USING_DIRECT_MIDI'] = 'true'
                os.environ['MIDI_PATH'] = str(midi_path)
                
                return True
                
            except Exception as e:
                console.print(f"[red]All MIDI conversion approaches failed:")
                tb = traceback.format_exc()
                console.print(f"[yellow]{tb}")
                return False
    
    # If MuseScore format, use mscore to convert
    elif ext in ['.mscz', '.mscx']:
        console.print(f"[cyan]Converting MuseScore file to MusicXML...")
        try:
            # Find the mscore executable
            mscore_path = None
            for possible_path in [
                "mscore", "musescore", "MuseScore", 
                "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
                "/Applications/MuseScore 3.app/Contents/MacOS/mscore",
                # Windows paths
                r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe",
                r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe",
                r"C:\Program Files (x86)\MuseScore 4\bin\MuseScore4.exe",
                r"C:\Program Files (x86)\MuseScore 3\bin\MuseScore3.exe"
            ]:
                try:
                    # For Windows, check if file exists
                    if platform.system() == "Windows" and possible_path.startswith("C:"):
                        if os.path.exists(possible_path):
                            mscore_path = possible_path
                            break
                    else:
                        # For Unix-like systems, use which command
                        result = subprocess.run(
                            ["which", possible_path], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE
                        )
                        if result.returncode == 0:
                            mscore_path = possible_path.strip()
                            break
                except:
                    continue
                    
            if not mscore_path:
                console.print("[red]MuseScore not found. Cannot convert MuseScore file.")
                return False
                
            # Convert using MuseScore
            result = subprocess.run([
                mscore_path,
                "-o", output_xml_path,
                score_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode == 0 and Path(output_xml_path).exists():
                console.print("[green]Successfully converted MuseScore file to MusicXML!")
                return True
            else:
                console.print("[red]Failed to convert MuseScore file.")
                return False
        except Exception as e:
            console.print(f"[red]Error converting MuseScore file: {str(e)}")
            return False
    
    # Unsupported format
    else:
        console.print(f"[red]Unsupported score format: {ext}")
        console.print("[yellow]Supported formats: .xml, .musicxml, .mxl, .mid, .midi, .mscz, .mscx")
        return False

def adapt_score_for_instrument(xml_path, instrument_program=0):
    """
    Parse the MusicXML file and adapt it for the selected instrument.
    
    Args:
        xml_path (str): Path to the MusicXML file
        instrument_program (int): MIDI program number for the instrument
    
    Returns:
        music21.stream.Score: The adapted score
    """
    # Check if we're using direct MIDI
    if os.environ.get('USING_DIRECT_MIDI') == 'true':
        console.print("[green]Using direct MIDI file. Skipping score adaptation...")
        return None
    
    # Load the MusicXML file
    score = converter.parse(xml_path)
    parts = score.parts

    # Create a new score
    adapted_score = stream.Score()
    instrument_part = stream.Part()
    
    # Apply the instrument if not using piano
    if instrument_program != 0:
        try:
            # Create the instrument object
            instr = instrument.Instrument()
            instr.midiProgram = instrument_program
            
            # Add it to the part
            instrument_part.insert(0, instr)
            console.print(f"[green]Added instrument (program {instrument_program}) to the score")
        except Exception as e:
            console.print(f"[yellow]Could not set instrument in the score: {str(e)}")
    
    # Combine all parts into one part
    for part in parts:
        for note_or_chord in part.recurse().getElementsByClass(['Note', 'Chord']):
            instrument_part.append(note_or_chord)

    adapted_score.insert(0, instrument_part)
    return adapted_score

def synthesize_wav(midi_path, wav_path, soundfont_path, instrument_program=0):
    """
    Synthesize a MIDI file into WAV using FluidSynth with the specified SoundFont.
    
    Args:
        midi_path (str): Path to the MIDI file
        wav_path (str): Path where WAV file will be saved
        soundfont_path (str): Path to the SoundFont file (.sf2)
        instrument_program (int): MIDI program number (0-127) for the instrument
                                  Default is 0 (piano)
    """
    try:
        # This is a simplified approach that will work reliably
        if instrument_program != 0:
            console.print(f"[yellow]Note: Using instrument {instrument_program}. Your SoundFont must have this instrument.")
            console.print(f"[yellow]The MIDI file will need tracks with this instrument to hear it.")
            
        # Run FluidSynth with basic parameters
        subprocess.run(["fluidsynth", "-F", wav_path, soundfont_path, midi_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error during MIDI synthesis: {str(e)}")
        return False
    except FileNotFoundError:
        console.print("[red]FluidSynth not found. Please install FluidSynth on your system.")
        return False

def compress_audio(wav_path, output_audio, format):
    """
    Compress a WAV file into MP3 or AAC using pydub.
    """
    try:
        audio = AudioSegment.from_wav(wav_path)
        if format == "mp3":
            audio.export(output_audio, format="mp3")
        elif format == "aac":
            # For AAC, we need to use a container format that supports AAC
            # 'adts' is a common container for AAC audio
            if output_audio.endswith('.aac'):
                # Try different encoding options for AAC
                # Option 1: Use mp4 container with aac codec
                audio.export(
                    output_audio, 
                    format="ipod",  # ipod format uses AAC in an MP4 container
                    parameters=["-acodec", "aac", "-strict", "experimental"]
                )
                
                console.print("[yellow]Note: AAC files work best with .m4a extension instead of .aac")
                
            else:
                console.print("[red]Error: For AAC output, please use .aac file extension")
                return False
        else:
            raise ValueError(f"The provided media file extension {format} is not supported. Use mp3 or aac.")
        return True
    except Exception as e:
        console.print(f"[red]Error during audio compression: {str(e)}")
        # Show more details about the error
        import traceback
        console.print(f"[yellow]{traceback.format_exc()}")
        
        # Suggest alternative approach
        console.print("\n[cyan]Try using an alternative approach:")
        if format == "aac":
            console.print("1. Change the output extension to .m4a instead of .aac")
            console.print("2. Or convert the WAV file manually using:")
            console.print(f"   ffmpeg -i {wav_path} -c:a aac {output_audio}")
        
        return False

def main(score_file_path, soundfont_sf2_file_path, media_file_path, instrument_program=0):
    """
    Main function to convert a score to an audio file using the specified SoundFont and instrument.
    
    Args:
        score_file_path (str): Path to the input score file
        soundfont_sf2_file_path (str): Path to the SoundFont file (.sf2)
        media_file_path (str): Path to the output audio file
        instrument_program (int): MIDI program number (0-127) for the instrument
                                 Default is 0 (piano)
    """
    # Determine the output format from the media file extension
    output_extension = Path(media_file_path).suffix[1:].lower()  # Remove the dot and convert to lowercase
    
    if output_extension not in ["mp3", "aac", "m4a"]:
        console.print(f"[red]Error: Unsupported output format: {output_extension}")
        console.print("[yellow]Supported output formats: .mp3, .m4a (recommended for AAC)")
        console.print("[yellow]Note: .aac extension can be problematic with some systems; .m4a is more reliable")
        return False
    
    # Map extensions to audio formats
    format_map = {
        "mp3": "mp3",
        "aac": "aac",
        "m4a": "aac"  # m4a is just a container for AAC
    }
    
    audio_format = format_map[output_extension]

    # Define intermediate file paths
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    xml_path = temp_dir / "score.xml"
    midi_path = temp_dir / "adapted_version.mid"
    wav_path = temp_dir / "audio.wav"

    success = True
    
    try:
        # Reset environment variables
        if 'USING_DIRECT_MIDI' in os.environ:
            del os.environ['USING_DIRECT_MIDI']
        if 'MIDI_PATH' in os.environ:
            del os.environ['MIDI_PATH']
            
        # Display instrument information
        if instrument_program == 0:
            console.print(f"[cyan]Using default instrument: Piano (program 0)")
        else:
            # Get instrument names
            instrument_names = {
                0: "Piano", 24: "Acoustic Guitar (nylon)", 25: "Acoustic Guitar (steel)",
                26: "Electric Guitar (jazz)", 27: "Electric Guitar (clean)", 28: "Electric Guitar (muted)",
                29: "Overdriven Guitar", 30: "Distortion Guitar", 32: "Acoustic Bass",
                33: "Electric Bass (finger)", 34: "Electric Bass (pick)", 40: "Violin",
                41: "Viola", 42: "Cello", 43: "Contrabass", 56: "Trumpet",
                60: "French Horn", 68: "Oboe", 71: "Clarinet", 73: "Flute",
                # Add more as needed
            }
            instrument_name = instrument_names.get(instrument_program, f"Instrument {instrument_program}")
            console.print(f"[cyan]Using instrument: {instrument_name} (program {instrument_program})")
            
        # Step 1: Convert score to MusicXML based on format
        console.print(f"Converting {score_file_path} to MusicXML...")
        xml_conversion_success = convert_score_to_musicxml(score_file_path, xml_path)
        
        if not xml_conversion_success:
            console.print("[red]Error: Score conversion failed.")
            console.print("[yellow]Please ensure you're using a supported format: .xml, .musicxml, .mxl, .mid, .midi, .mscz, .mscx")
            if Path(score_file_path).suffix.lower() in ['.mid', '.midi']:
                console.print("[yellow]For MIDI files with conversion issues, try:")
                console.print("[yellow]1. Using a simpler MIDI file")
                console.print("[yellow]2. Pre-converting the MIDI to MusicXML using notation software like MuseScore")
            return False
        
        # Step 2: Adapt the score for the instrument
        try:
            console.print(f"Adapting score for SoundFont instrument...")
            
            # If we're using direct MIDI, use that file
            if os.environ.get('USING_DIRECT_MIDI') == 'true':
                midi_path = Path(os.environ.get('MIDI_PATH'))
                console.print(f"[green]Using direct MIDI file: {midi_path}")
            else:
                # Otherwise, adapt the score with the instrument
                adapted_score = adapt_score_for_instrument(xml_path, instrument_program)
                adapted_score.write('midi', fp=midi_path)
                
        except Exception as e:
            console.print(f"[red]Error adapting score: {str(e)}")
            success = False
            return False

        # Step 3: Synthesize audio (WAV) using the specified SoundFont
        console.print(f"Synthesizing audio using SoundFont: {Path(soundfont_sf2_file_path).name}...")
        if not synthesize_wav(midi_path, wav_path, soundfont_sf2_file_path, instrument_program):
            success = False
            return False

        # Step 4: Compress audio (MP3 or AAC)
        console.print(f"Compressing audio to {audio_format.upper()}...")
        if not compress_audio(wav_path, media_file_path, format=audio_format):
            success = False
            return False

        if success:
            console.print(f"[green]Audio file successfully generated: {media_file_path}")
            return True
        else:
            console.print("[red]Failed to generate audio file. Please check the error messages above.")
            return False
    finally:
        # Keep the intermediate files if there was an error
        if success:
            # Clean up temporary files
            for file in [xml_path, midi_path, wav_path]:
                if file.exists():
                    file.unlink()
            
            # Clean up environment variables
            if 'USING_DIRECT_MIDI' in os.environ:
                del os.environ['USING_DIRECT_MIDI']
            if 'MIDI_PATH' in os.environ:
                del os.environ['MIDI_PATH']

def cli():
    """Command-line interface using argparse."""
    import argparse
    import sys
    
    # Create a more descriptive help text
    description = """
Convert a music score to an audio file using a specified SoundFont.

Supported input formats:
- MusicXML (.xml, .musicxml, .mxl) - primary recommended format
- MIDI (.mid, .midi)
- MuseScore (.mscz, .mscx)

Supported output formats:
- MP3 (.mp3)
- M4A (.m4a) - recommended container for AAC audio
- AAC (.aac) - may have compatibility issues on some systems

Common MIDI instrument programs:
0: Piano (default)     24: Nylon Guitar    25: Steel Guitar    26: Jazz Guitar
33: Electric Bass      40: Violin          41: Viola           42: Cello
56: Trumpet            60: French Horn     68: Oboe            71: Clarinet
73: Flute              
    """
    
    # Create a custom argument parser that shows help on error
    class ArgumentParserWithHelp(argparse.ArgumentParser):
        def error(self, message):
            # Print usage info first
            self.print_usage(sys.stderr)
            # Print the error message
            self.exit(2, f"{self.prog}: error: {message}\n\n{description}\n")
    
    # Create the parser with the enhanced description and custom behavior
    parser = ArgumentParserWithHelp(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter  # This preserves the formatting in the help text
    )
    
    # Add arguments with improved help text
    parser.add_argument(
        "score_file_path", 
        type=str, 
        help="Path to the input score file (.xml, .musicxml, .mxl, .mid, .midi, .mscz, .mscx)"
    )
    parser.add_argument(
        "soundfont_sf2_file_path", 
        type=str, 
        help="Path to the SoundFont file (.sf2) that defines the instrument sounds"
    )
    parser.add_argument(
        "media_file_path", 
        type=str, 
        help="Path to the output audio file. Extension (.mp3, .m4a, or .aac) determines the format"
    )
    parser.add_argument(
        "-i", "--instrument", 
        type=int, 
        default=0, 
        help="MIDI program number (0-127) for the instrument. Default is 0 (Piano)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate instrument program number
    if args.instrument < 0 or args.instrument > 127:
        parser.error(f"Instrument program number must be between 0 and 127, got {args.instrument}")
    
    # Run the main function
    success = main(args.score_file_path, args.soundfont_sf2_file_path, args.media_file_path, args.instrument)
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(cli())
