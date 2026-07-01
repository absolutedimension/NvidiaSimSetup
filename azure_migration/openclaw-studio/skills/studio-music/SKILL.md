---
name: studio-music
description: "Produce finished, mastered, copyright-clean MUSIC and audio on the EC2 render farm via ACE-Step. Use when the user wants to MAKE audio: 'make music', 'create a song', 'generate a track', 'background/focus/study music', 'meditation music', '432Hz', 'isochronic tones', 'binaural', 'ghazal', 'lofi', 'ambient', 'instrumental', 'beat', 'music bed', 'AI singer', 'sing this', 'song from these lyrics', 'make a track like <reference>', 'royalty-free / copyright-free music'. Picks a style, drives make_music.py to a final MP3, delivers the file. NOT for video (use studio-video / studio-faceless)."
metadata: { "openclaw": { "emoji": "🎵", "requires": { "bins": ["ssh", "scp"] } } }
---

# studio-music — Music & Audio Production

Drive `make_music.py` (ACE-Step, MIT-licensed → safe to monetize) on the EC2 render farm. One command → finished, mastered MP3.

## When to Use
✅ Songs (vocals or instrumental), focus/study music, meditation, ghazal, lofi, ambient, trailer beds, any length 2 min–2 hr, AI singers.

## When NOT to Use
❌ Video → `studio-video` / `studio-faceless`. ❌ Just writing lyrics → `studio-script` then come back.

## Step 0 — resolve the farm (auto EC2 → T4 fallback)
Music runs on EITHER farm. The resolver picks EC2 (fast) if up, else the T4 (slower, cpu-offload). Source it:
```bash
source ~/.openclaw/farm.sh    # exports FARM_NAME, FARM_IP, FARM_USER, FARM_KEY, FARM_HOME, FARM_OFFLOAD, FARM_ENV, FARM_PY_ACE
# prints: FARM=ec2 (...) | FARM=t4 (...) | FARM=none
```
- `FARM=ec2` → fast render. `FARM=t4` → works but **slower** (tell Deepak: "EC2 is down, rendering on the T4 fallback — this is slower").
- `FARM=none` → both down → tell Deepak to start a box. Don't fake it.

## Styles (presets)
`focus-house · meditation-432 · sitar-heal · lofi · ambient · ghazal · pop`
Or a freeform `--prompt "epic orchestral, taiko drums, rising tension"`.

## Clarify (only what matters)
- Style/mood? • Length (`--minutes`)? • Vocals or instrumental? • Language? • Reference track to match?
Pick defaults and state them; one or two questions max.

## Commands (farm-agnostic — uses the resolved farm)
After `source ~/.openclaw/farm.sh`, build a runner that targets whichever farm is up. `$FARM_OFFLOAD` is empty on EC2 and `--cpu-offload` on the T4; `$FARM_ENV` carries the T4's alloc setting; paths use `$FARM_HOME` (EC2=`/home/ubuntu`, T4=`/home/dk-gpu-ubuntu`).
```bash
source ~/.openclaw/farm.sh
[ "$FARM_NAME" = none ] && { echo "both farms down — ask Deepak to start one"; exit 1; }
ssh -i "$FARM_KEY" -o StrictHostKeyChecking=no "$FARM_USER@$FARM_IP" "mkdir -p $FARM_HOME/music_work $FARM_HOME/music_out"

MUSIC(){  # $1 = make_music args (style/minutes/etc.), $2 = output filename
  ssh -i "$FARM_KEY" -o StrictHostKeyChecking=no "$FARM_USER@$FARM_IP" \
    "cd $FARM_HOME && $FARM_ENV $FARM_PY_ACE make_music.py $1 $FARM_OFFLOAD --workdir $FARM_HOME/music_work --out $FARM_HOME/music_out/$2"
}

# examples (note: on the T4 fallback these are SLOWER — long tracks take a while):
MUSIC '--style lofi --freq alpha --minutes 45' lofi.mp3
MUSIC '--style meditation-432 --minutes 20'     raga.mp3
MUSIC '--style focus-house --freq beta --minutes 30' study.mp3
MUSIC '--style ghazal --lyrics-file '"$FARM_HOME"'/couplets.txt --minutes 4' ghazal.mp3
MUSIC '--prompt "epic orchestral, taiko drums" --minutes 2' trailer.mp3
```
**Long tracks: run detached + poll** (especially on the T4 — it's ~7× realtime):
```bash
ssh -i "$FARM_KEY" "$FARM_USER@$FARM_IP" "cd $FARM_HOME && setsid nohup bash -c '$FARM_ENV $FARM_PY_ACE make_music.py <args> $FARM_OFFLOAD --workdir $FARM_HOME/music_work --out $FARM_HOME/music_out/out.mp3' > /tmp/m1.log 2>&1 </dev/null & echo started"
# poll: ssh ... 'grep "\[m1\]" /tmp/m1.log | tail -3'  (ignore tqdm)
```
Deliver: `scp -i "$FARM_KEY" "$FARM_USER@$FARM_IP:$FARM_HOME/music_out/<file>" /tmp/out.mp3` → SendUserFile.

### Key flags
`--minutes` `--style` `--prompt` `--lyrics-file` `--freq beta|alpha|theta|delta` `--iso-db`(−20) `--tune432` `--ref`/`--ref-strength` `--unique`(4, raise for less repetition over long durations) `--seg-len`(180) `--seed` `--steps`(60).

## AI singers (optional)
Convert a sung vocal to a TrigunAI singer (Trigun-Maya F / Trigun-Ravi M):
```bash
RUN '~/m2_venv/bin/python singerize.py --input /home/ubuntu/music_out/song.wav --singer maya --out /home/ubuntu/music_out/song_maya.mp3'
```
Note: singers are good on English; Hindi accent is a known weak spot (deferred).

## Deliver
```bash
scp -i "$EC2_KEY" "$EC2_USER@$EC2_IP:/home/ubuntu/music_out/study.mp3" /tmp/study.mp3
# then SendUserFile /tmp/study.mp3
```

## Gotchas
- Lyrics: tag `[verse]`/`[chorus]`/`[bridge]`; instrumental needs `[inst]` (presets handle this). Hindi vocals: Romanized often sounds crisper than Devanagari on v1.
- `--ref` needs a short (60–90s) representative clip, kept under `/home/ubuntu/` (not `/tmp`).
- Output too repetitive on long tracks → raise `--unique` / `--seg-len`.
- Isochronic tone level: `--iso-db -16` audible, `-24` subliminal.
