# TrigunAI — NVIDIA Isaac Sim Cloud Infrastructure Report
**Prepared for:** Developer Handoff  
**Date:** 2026-05-14  
**Purpose:** Replace local laptop GPU with AWS cloud GPU for NVIDIA Isaac Sim development

---

## 1. Instance Summary

| Field | Value |
|---|---|
| **Instance Name** | TrigunAI-Omniverse |
| **Instance ID** | i-047ebf759f2386e71 |
| **Instance Type** | g5.2xlarge |
| **GPU** | NVIDIA A10G (24 GB VRAM) |
| **vCPUs** | 8 |
| **RAM** | 32 GiB |
| **Public IP** | 98.91.224.40 |
| **Public DNS** | ec2-98-91-224-40.compute-1.amazonaws.com |
| **Region** | us-east-1 (N. Virginia) |
| **AMI** | NVIDIA GPU Cloud VMI Base 2026.4.1 |
| **AMI ID** | ami-059e868ce2e616dab |
| **OS** | Ubuntu Linux (x86_64) |
| **Status** | Running ✅ |

---

## 2. Storage

| Volume | Size | Type |
|---|---|---|
| Root EBS volume | 200 GiB | gp3 (3000 IOPS) |
| NVMe instance store | 450 GiB | Local SSD (free, ephemeral) |

> **Note:** The NVMe instance store is fast local SSD but is **ephemeral** — data on it is lost if the instance is stopped/terminated. Use the EBS root volume for anything that must persist.

---

## 3. SSH Access

**Key pair file:** `trigunai_key.pem`  
(Developer must obtain this file securely from Deepak)

**Set permissions (run once):**
```bash
chmod 400 /path/to/trigunai_key.pem
```

**SSH command:**
```bash
ssh -i /path/to/trigunai_key.pem ubuntu@98.91.224.40
```

**Alternative using DNS:**
```bash
ssh -i /path/to/trigunai_key.pem ubuntu@ec2-98-91-224-40.compute-1.amazonaws.com
```

---

## 4. Security Group (Firewall Rules)

| Port | Protocol | Source | Purpose |
|---|---|---|---|
| 22 | TCP | 0.0.0.0/0 | SSH access |
| 8443 | TCP | 0.0.0.0/0 | NICE DCV remote desktop |

> If additional ports are needed (e.g., Nucleus server port 3009, 3010), they can be added to security group `sg-09c8965b2567b844d`.

---

## 5. Pre-installed Software (from NVIDIA AMI)

The AMI comes with the following pre-installed:
- Ubuntu OS (latest LTS)
- NVIDIA GPU drivers
- CUDA toolkit
- Docker + NVIDIA Container Toolkit
- NGC CLI tools

---

## 6. Developer Setup Instructions for Isaac Sim

### Step 1: SSH into the instance
```bash
ssh -i trigunai_key.pem ubuntu@98.91.224.40
```

### Step 2: Verify GPU is detected
```bash
nvidia-smi
```
Expected: NVIDIA A10G, 24GB VRAM

### Step 3: Install NICE DCV (remote desktop) — for GUI access to Isaac Sim
```bash
# Download and install NICE DCV server
wget https://d1uj6qtbmh3dt5.cloudfront.net/2023.1/Servers/nice-dcv-2023.1-16388-ubuntu2204-x86_64.tgz
tar -xvzf nice-dcv-2023.1-16388-ubuntu2204-x86_64.tgz
cd nice-dcv-2023.1-16388-ubuntu2204-x86_64
sudo apt install ./nice-dcv-server_2023.1.16388-1_amd64.ubuntu2204.deb
sudo apt install ./nice-dcv-gl_2023.1.16388-1_amd64.ubuntu2204.deb

# Start DCV server
sudo systemctl enable dcvserver
sudo systemctl start dcvserver

# Create DCV session
dcv create-session --type=virtual --gl-displays :0 mysession
```

### Step 4: Connect via NICE DCV (remote desktop)
In a browser or NICE DCV client, connect to:
```
https://98.91.224.40:8443
```
Username: `ubuntu`  
Session name: `mysession`

### Step 5: Install NVIDIA Omniverse + Isaac Sim
```bash
# Install Omniverse Launcher (headless)
wget https://install.launcher.omniverse.nvidia.com/installers/omniverse-launcher-linux.AppImage
chmod +x omniverse-launcher-linux.AppImage

# OR use Isaac Sim container from NGC (recommended for cloud)
docker pull nvcr.io/nvidia/isaac-sim:latest

# Run Isaac Sim container
docker run --gpus all -it --rm \
  -v ~/isaac-sim-data:/root/isaac-sim \
  nvcr.io/nvidia/isaac-sim:latest
```

### Step 6: Run Isaac Sim in headless mode (no GUI needed for scripting)
```bash
docker run --gpus all -it --rm \
  nvcr.io/nvidia/isaac-sim:latest \
  ./python.sh /path/to/your_script.py
```

---

## 7. Cost Estimate

| Resource | Rate | Notes |
|---|---|---|
| g5.2xlarge EC2 | ~$1.006/hr | Only charged when instance is **Running** |
| EBS storage (200 GiB) | ~$16/month | Charged even when instance is stopped |
| Software (AMI) | $0.00/hr | Free NVIDIA GPU-Optimized AMI |
| Data transfer out | ~$0.09/GB | For downloading results |

> **Important:** **Stop the instance** when not in use to avoid EC2 charges. Storage charges continue even when stopped. Only **Terminate** the instance when done permanently.

**To stop the instance:**
- AWS Console → EC2 → Instances → select TrigunAI-Omniverse → Instance state → Stop

---

## 8. Instance Management

**Start instance:** AWS Console → EC2 → Instances → Start  
**Stop instance:** AWS Console → EC2 → Instances → Stop  
**Note:** Public IP changes each time the instance starts. To get a permanent IP, allocate an **Elastic IP** (free while instance is running).

**AWS Account:** TrigunAIAWS (Account ID: 253571483681)  
**AWS Region:** us-east-1

---

## 9. For Claude Agent — Key Facts

- **Machine is already running** at `98.91.224.40`
- **GPU:** NVIDIA A10G, 24GB VRAM — fully compatible with Isaac Sim
- **NVIDIA drivers and CUDA pre-installed** — no driver setup needed
- **Docker + NVIDIA Container Toolkit pre-installed** — can pull Isaac Sim NGC container directly
- **SSH access** via `trigunai_key.pem` as user `ubuntu`
- **GUI access** via NICE DCV on port 8443 (needs DCV server installation first)
- **Isaac Sim NGC container** is the fastest path to get running: `nvcr.io/nvidia/isaac-sim:latest`
- Developer's existing local Isaac Sim scripts/configs can be transferred via `scp`:
  ```bash
  scp -i trigunai_key.pem -r /local/isaac-project/ ubuntu@98.91.224.40:~/
  ```
