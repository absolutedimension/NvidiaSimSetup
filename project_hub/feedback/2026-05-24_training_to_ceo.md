# Feedback: Training Agent → CEO

> Date: 2026-05-24
> Priority: normal
> Re: A4 gate — 25s drone-POV video ready for review
> Status: unread

## Context

Trained a PPO cinematographer drone policy (500 epochs, reward 7.00) on a Starling 2
quadcopter. The drone learns to fly around a dancer while filming. Exported the trajectory
(1250 frames @ 50fps = 25s) and rendered a verification video.

The 5s test clip was approved ("yes it looking good now"). Now the full 25s video is
rendering via OVRTX (~75 min total, currently batch 6/25).

## Feedback

The full 25s drone-POV video will be at:
- EC2: `/home/ubuntu/drone_pov_25s.mp4`
- To pull to Mac: `scp -i ~/.ssh/trigunai_key.pem ubuntu@<EC2_IP>:/home/ubuntu/drone_pov_25s.mp4 ~/Documents/01_Active/NvidiaSimSetup/cinematography/`

Please watch it and provide the A4 gate verdict:
> "Does the trained drone's video look more cinematic than the orbital baseline?"

## Requested action

- [ ] Watch the 25s drone-POV video
- [ ] Compare against the orbital baseline (cinematography/orbital_25s.mp4 or similar)
- [ ] Provide verdict: "approved" → proceed to A5 (GLB export) or "needs work" → retrain

## Artifacts referenced

| File | Location | Notes |
|---|---|---|
| `drone_pov_5s.mp4` | mac: `cinematography/` | 5s test, already approved |
| `drone_pov_25s.mp4` | ec2-ebs: `/home/ubuntu/` | Full 25s, rendering now |
| `drone_pov_25s.usda` | ec2-ebs: `/home/ubuntu/` | Scene file for debug |
| `cinematographer_trajectory.json` | ec2-ebs: `/home/ubuntu/` | 1250 frames @ 50fps |
