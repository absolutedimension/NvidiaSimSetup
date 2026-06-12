"""
Generate a content-matched background-music bed with ACE-Step.

The prompt is derived from the content mood ("system decides by content type"):
this reel is an energetic, motivational tech/education hook -> uplifting corporate
electronic, instrumental.

Run with the ACE-Step venv:
  /home/ubuntu/acestep_venv/bin/python /home/ubuntu/reel_build/ace_gen.py
"""
import sys
sys.path.insert(0, "/home/ubuntu/ACE-Step")
from acestep.pipeline_ace_step import ACEStepPipeline

# ---- content -> music prompt (the selection brain) ----
MOOD_PROMPTS = {
    "energetic": ("uplifting corporate technology, energetic and motivational, modern "
                  "electronic, bright plucky synth, warm pads, light four-on-the-floor "
                  "beat, claps, optimistic, inspiring, clean, instrumental, no vocals, "
                  "120 bpm"),
    "calm": ("calm ambient study, soft warm pads, gentle piano, mellow, focused, "
             "spacious, instrumental, no vocals, 80 bpm"),
}
MOOD = "energetic"
DURATION = 62.0
OUT = "/home/ubuntu/reel_build/ace_music.wav"

pipe = ACEStepPipeline(checkpoint_dir="", dtype="bfloat16",
                       torch_compile=False, cpu_offload=False, overlapped_decode=False)

pipe(
    audio_duration=DURATION,
    prompt=MOOD_PROMPTS[MOOD],
    lyrics="[inst]",
    infer_step=60,
    guidance_scale=15,
    scheduler_type="euler",
    cfg_type="apg",
    omega_scale=10,
    manual_seeds="42",
    guidance_interval=0.7,
    guidance_interval_decay=0,
    min_guidance_scale=3,
    use_erg_tag=True,
    use_erg_lyric=False,
    use_erg_diffusion=True,
    oss_steps="",
    guidance_scale_text=0.0,
    guidance_scale_lyric=0.0,
    save_path=OUT,
)
print("ACE_MUSIC_DONE", OUT)
