from pathlib import Path
from faster_whisper import WhisperModel

model=WhisperModel("small",device="cpu",compute_type="int8")

def transcribe_audio(audio_file_path):
    audio_path=Path(audio_file_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"fiel not found {audio_path}")
    segments,info=model.transcribe(str(audio_path),language="en",beam_size=5,best_of=5,patience=2,vad_filter=True,condition_on_previous_text=True)
    transcript=" ".join(segment.text.strip()for segment in segments)
    return transcript.strip()


