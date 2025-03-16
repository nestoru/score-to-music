import os
from pathlib import Path
from copy import deepcopy
from music21 import converter, stream, instrument, volume
from rich.console import Console

console = Console()

def adapt_score_for_instruments(xml_path: Path, instrument_programs: list = [0], uniform_velocity: int = 64) -> stream.Score:
    """
    Parse the MusicXML file and adapt it to include multiple instrument parts.
    Each instrument gets its own part with the same musical content, assigned to a unique MIDI channel.
    Additionally, each note/chord is cloned and its velocity is set to a uniform value to ensure equal volume.

    Args:
        xml_path (Path): Path to the MusicXML file.
        instrument_programs (List[int]): List of MIDI program numbers.
        uniform_velocity (int): The MIDI velocity (volume) to assign to every note. Defaults to 64.

    Returns:
        music21.stream.Score: The adapted score with multiple instrument parts.
    """
    if os.environ.get('USING_DIRECT_MIDI') == 'true':
        console.print("[green]Using direct MIDI file. Skipping score adaptation...")
        return None

    score = converter.parse(str(xml_path))
    parts = score.parts
    adapted_score = stream.Score()

    # For each instrument, create a part, assign a unique MIDI channel, and copy all notes/chords with uniform velocity
    for idx, program in enumerate(instrument_programs):
        instrument_part = stream.Part()
        try:
            instr = instrument.Instrument()
            instr.midiProgram = program
            # Assign a unique channel for each instrument part (0-based)
            instr.midiChannel = idx  
            instrument_part.insert(0, instr)
            console.print(f"[green]Added instrument (program {program}, channel {idx}) to a new part")
        except Exception as e:
            console.print(f"[yellow]Could not set instrument for program {program}: {str(e)}")
        
        # Duplicate all note/chord events from all parts into this instrument part,
        # making a deepcopy and setting a uniform velocity.
        for part in parts:
            for elem in part.recurse().getElementsByClass(['Note', 'Chord']):
                new_elem = deepcopy(elem)
                # Ensure the note/chord has a volume object and set its velocity uniformly
                if new_elem.volume is None:
                    new_elem.volume = volume.Volume(velocity=uniform_velocity)
                else:
                    new_elem.volume.velocity = uniform_velocity
                instrument_part.append(new_elem)
        
        # Append this part to the adapted score
        adapted_score.append(instrument_part)

    return adapted_score

