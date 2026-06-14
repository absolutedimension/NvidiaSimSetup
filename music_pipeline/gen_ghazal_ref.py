#!/usr/bin/env python3
"""Reference-style ghazal — audio2audio. Captures the reference's STYLE only
(instrumentation, tempo, ghazal feel); sings our ORIGINAL judaai couplets.
Female vocal. ACE-Step v1 3.5B. Copyright-clean output."""
import time, os, sys
from acestep.pipeline_ace_step import ACEStepPipeline

REF = "/home/ubuntu/ref_ghazal_clip.wav"
STRENGTH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5  # 0.3 loose .. 0.7 close
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 88
OUT = f"/home/ubuntu/music_out/ghazal_ref_s{int(STRENGTH*100)}_seed{SEED}.wav"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

PROMPT = ("hindi ghazal, soulful female vocal, harmonium, tabla, sarangi, slow tempo, "
          "melancholic, emotional, intimate, acoustic, reverb, classical indian")

# Original ghazal — radif 'नहीं', qafiya: ढलती/सँभलती/टलती/निकलती/चलती (judaai / separation)
LYRICS = """[verse]
तेरे बिना ये शाम अब ढलती नहीं
दिल की ये बेचैनियाँ सँभलती नहीं

[verse]
तेरी यादों के सिवा कुछ भी नहीं
ये तन्हाई अब मुझसे टलती नहीं

[chorus]
रोता है दिल हर रात तेरे नाम से
आँखों से ये नमी अब निकलती नहीं

[verse]
जुदाई की ये रात लम्बी हो गई
तेरे बिन ये ज़िंदगी चलती नहीं
"""

print(f"[ghazal-ref] strength={STRENGTH} seed={SEED} loading...", flush=True)
t0 = time.time()
pipe = ACEStepPipeline(checkpoint_dir="", dtype="bfloat16", cpu_offload=False)
print(f"[ghazal-ref] ready in {time.time()-t0:.1f}s", flush=True)

t1 = time.time()
pipe(
    format="wav",
    audio_duration=110.0,
    prompt=PROMPT,
    lyrics=LYRICS,
    infer_step=60,
    guidance_scale=15.0,
    guidance_scale_lyric=2.5,
    audio2audio_enable=True,
    ref_audio_input=REF,
    ref_audio_strength=STRENGTH,
    manual_seeds=[SEED],
    save_path=OUT,
    batch_size=1,
)
print(f"[ghazal-ref] generated in {time.time()-t1:.1f}s -> {OUT}", flush=True)
print("[ghazal-ref] DONE", flush=True)
