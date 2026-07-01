#!/usr/bin/env python3
import dawdreamer as daw, numpy as np, librosa, soundfile as sf
SR=44100
print("dawdreamer", daw.__version__ if hasattr(daw,"__version__") else "?")
eng = daw.RenderEngine(SR, 512)
# load 8s of the base track as stereo
y,_ = librosa.load("/home/ubuntu/dj_engine/burmeister/burmeister_track_v12.mp3", sr=SR, mono=True, offset=180, duration=8)
data = np.stack([y,y]).astype(np.float32)   # (2, n)
pb = eng.make_playback_processor("play", data)
# real filter + compressor + reverb chain
methods = [m for m in dir(eng) if m.startswith("make_")]
print("processors:", methods)
try:
    comp = eng.make_compressor_processor("comp", -18.0, 3.0, 10.0, 120.0)  # thr,ratio,atk,rel
    rev  = eng.make_reverb_processor("rev")
    eng.load_graph([(pb, []), (comp, ["play"]), (rev, ["comp"])])
    eng.render(8.0)
    out = eng.get_audio()
    sf.write("/tmp/dd_test.wav", out.T, SR)
    print("RENDERED /tmp/dd_test.wav shape", out.shape)
except Exception as e:
    print("ERR", repr(e))
