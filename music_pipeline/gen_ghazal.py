#!/usr/bin/env python3
"""Hindi ghazal — pain of separation (viraha), female vocal. ACE-Step v1 3.5B."""
import time, os
from acestep.pipeline_ace_step import ACEStepPipeline

OUT = "/home/ubuntu/music_out/ghazal_viraha.wav"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# Soulful, traditional ghazal palette: harmonium + tabla, slow, reverberant, melancholic.
PROMPT = ("hindi ghazal, soulful female vocal, harmonium, tabla, sarangi, slow tempo, "
          "melancholic, emotional, romantic, acoustic, intimate, reverb, classical indian")

# Ghazal of judaai (separation) — couplets of longing and pain.
LYRICS = """[verse]
तेरे जाने के बाद ये दिल वीरान हो गया
हर साँस में बस तेरा ही अरमान खो गया

[chorus]
जुदाई की ये रात अब कटती नहीं
तेरे बिना ये ज़िंदगी सजती नहीं

[verse]
वो आँखें जो कभी मुझमें बसा करती थीं
अब ख़्वाबों में भी तुझको ढूँढा करती हैं

[bridge]
दर्द-ए-जुदाई सहती रही मैं चुपचाप
तेरी यादों के साये में बहती रही मैं चुपचाप

[chorus]
जुदाई की ये रात अब कटती नहीं
तेरे बिना ये ज़िंदगी सजती नहीं
"""

print("[ghazal] loading pipeline...", flush=True)
t0 = time.time()
pipe = ACEStepPipeline(checkpoint_dir="", dtype="bfloat16", cpu_offload=False)
print(f"[ghazal] ready in {time.time()-t0:.1f}s", flush=True)

t1 = time.time()
pipe(
    format="wav",
    audio_duration=110.0,
    prompt=PROMPT,
    lyrics=LYRICS,
    infer_step=60,
    guidance_scale=15.0,
    guidance_scale_lyric=2.5,   # nudge stronger lyric adherence for non-latin script
    manual_seeds=[77],
    save_path=OUT,
    batch_size=1,
)
print(f"[ghazal] generated in {time.time()-t1:.1f}s -> {OUT}", flush=True)
print("[ghazal] DONE", flush=True)
