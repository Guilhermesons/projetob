"""Generate speech in a separate process to isolate the Windows voice engine."""
import sys
import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
english = [v for v in voices if 'english' in v.name.lower() or any('en' in str(lang).lower() for lang in v.languages)]
if not english:
    raise RuntimeError('Instale uma voz inglesa nas configurações de fala do Windows.')
engine.setProperty('voice', english[0].id)
engine.setProperty('rate', 155)
engine.save_to_file(sys.stdin.read(), sys.argv[1])
engine.runAndWait()
