#!/usr/bin/env node
// Scene Composer bridge — runs locally on the Mac as a stand-in for the
// future :8005 FastAPI Scene Composer Agent. Wraps the 3 EC2-side CLI
// scripts (osm_to_usd.py, city_add_colliders.py, city_enrich_textures.py)
// + usd_to_glb.py over SSH, SCPs the resulting GLB back to a local cache,
// and serves the GLB to the Asset Studio frontend.
//
// HTTP contract matches the other NVIDIA Content Agents so this can be
// swapped for a real service later without touching the frontend:
//   GET  /health                          -> { status: 'healthy' }
//   GET  /pipeline/presets                -> [{ id, label, lat, lon, radius }]
//   POST /pipeline      (JSON body)       -> { session_id }
//   GET  /pipeline/:id/status             -> PipelineStatusBody
//   GET  /artifacts/:id/preview-glb       -> binary GLB
//
// Env:
//   COMPOSER_PORT  default 8005
//   EC2_IP         REQUIRED — current public IP of TrigunAI-Omniverse
//   SSH_KEY        path to trigunai_key.pem (default ~/.ssh/trigunai_key.pem)
//   SSH_USER       default 'ubuntu'
//   REMOTE_BASE    default /home/ubuntu/assets/cities
//   REMOTE_BIN     default /home/ubuntu  (where the 4 .py scripts live on EC2)
//   SYNC_SCRIPTS   if '1', SCP local scripts up to REMOTE_BIN at startup

import http from 'node:http'
import { spawn } from 'node:child_process'
import {
  mkdirSync, existsSync, createReadStream, statSync,
} from 'node:fs'
import { resolve, dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { homedir } from 'node:os'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = resolve(__dirname, '..', '..')

const PORT = Number(process.env.COMPOSER_PORT ?? 8005)
const EC2_IP = process.env.EC2_IP ?? ''
const SSH_KEY = process.env.SSH_KEY ?? resolve(homedir(), '.ssh', 'trigunai_key.pem')
const SSH_USER = process.env.SSH_USER ?? 'ubuntu'
const REMOTE_BASE = process.env.REMOTE_BASE ?? '/home/ubuntu/assets/cities'
const REMOTE_BIN = process.env.REMOTE_BIN ?? '/home/ubuntu'
const CACHE_DIR = resolve(__dirname, '.city-cache')
const SYNC_SCRIPTS = process.env.SYNC_SCRIPTS === '1'

mkdirSync(CACHE_DIR, { recursive: true })

const SCRIPTS_TO_SYNC = [
  'webxr-showcase/scripts/osm_to_usd.py',
  'webxr-showcase/scripts/city_add_colliders.py',
  'webxr-showcase/scripts/city_enrich_textures.py',
  'webxr-showcase/scripts/usd_to_glb.py',
]

const PHASES = [
  { name: 'osm', display_name: 'Fetch OSM buildings', target_percent: 20 },
  { name: 'colliders', display_name: 'Add collision shapes', target_percent: 35 },
  { name: 'textures', display_name: 'Generate AI façade', target_percent: 70 },
  { name: 'glb', display_name: 'Export GLB', target_percent: 92 },
  { name: 'download', display_name: 'Copy to local cache', target_percent: 99 },
]

const PRESETS = [
  { id: 'manhattan_times_sq', label: 'Manhattan / Times Sq', lat: 40.7580, lon: -73.9855, radius: 500 },
  { id: 'sf_soma', label: 'SF / SoMa', lat: 37.7800, lon: -122.4000, radius: 500 },
  { id: 'bangalore_mg_road', label: 'Bangalore / MG Road', lat: 12.9756, lon: 77.6050, radius: 500 },
  { id: 'london_city', label: 'London / City', lat: 51.5145, lon: -0.0900, radius: 500 },
  { id: 'tokyo_shibuya', label: 'Tokyo / Shibuya', lat: 35.6595, lon: 139.7005, radius: 400 },
]

// id => job
const jobs = new Map()
let nextId = 1

function jobView(j) {
  const stepIndex = j.completedSteps.length
  return {
    session_id: j.id,
    status: j.status,
    current_step: j.currentStep,
    completed_steps: j.completedSteps,
    overall_progress: {
      current_step: stepIndex,
      total_steps: PHASES.length,
      percent: j.percent,
    },
    elapsed_seconds: Math.round((Date.now() - j.startedAt) / 1000),
    error: j.error,
    preview_glb_url: j.glbUrl,
    log_tail: j.log.slice(-40),
  }
}

function sshArgs(remoteCmd) {
  return [
    '-i', SSH_KEY,
    '-o', 'StrictHostKeyChecking=no',
    '-o', 'BatchMode=yes',
    `${SSH_USER}@${EC2_IP}`,
    remoteCmd,
  ]
}

function scpArgs(src, dst) {
  return [
    '-i', SSH_KEY,
    '-o', 'StrictHostKeyChecking=no',
    '-o', 'BatchMode=yes',
    src, dst,
  ]
}

function runProc(job, phase, label, cmd, args) {
  job.currentStep = { name: phase, display_name: label }
  job.log.push(`[${phase}] $ ${cmd} ${args.join(' ')}`)
  const startedAt = Date.now()
  return new Promise((res, rej) => {
    const p = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'] })
    const push = (chunk) => {
      const lines = chunk.toString().split(/\r?\n/)
      for (const line of lines) {
        if (line) job.log.push(`[${phase}] ${line}`)
      }
      if (job.log.length > 600) job.log = job.log.slice(-400)
    }
    p.stdout.on('data', push)
    p.stderr.on('data', push)
    p.on('error', rej)
    p.on('close', (code) => {
      const duration = Math.round((Date.now() - startedAt) / 1000)
      if (code === 0) {
        job.completedSteps.push({ name: phase, display_name: label, duration_seconds: duration })
        res()
      } else {
        rej(new Error(`${phase} exited ${code}`))
      }
    })
  })
}

async function syncScripts(job) {
  for (const rel of SCRIPTS_TO_SYNC) {
    const local = resolve(REPO_ROOT, rel)
    if (!existsSync(local)) {
      throw new Error(`missing local script: ${rel}`)
    }
    const remote = `${SSH_USER}@${EC2_IP}:${REMOTE_BIN}/`
    await runProc(job, 'sync', `sync ${rel.split('/').pop()}`, 'scp', scpArgs(local, remote))
  }
}

async function runJob(job) {
  const { lat, lon, radius, name, prompt } = job.params
  job.status = 'running'
  try {
    if (SYNC_SCRIPTS) await syncScripts(job)

    const remoteUsd = `${REMOTE_BASE}/${name}/city.usd`
    const remoteGlb = `${REMOTE_BASE}/${name}/city.glb`

    job.percent = PHASES[0].target_percent
    await runProc(
      job, PHASES[0].name, PHASES[0].display_name, 'ssh',
      sshArgs(
        `python3 ${REMOTE_BIN}/osm_to_usd.py --lat ${lat} --lon ${lon} ` +
        `--radius ${radius} --name ${shellEscape(name)} --out ${REMOTE_BASE}`,
      ),
    )

    job.percent = PHASES[1].target_percent
    await runProc(
      job, PHASES[1].name, PHASES[1].display_name, 'ssh',
      sshArgs(`python3 ${REMOTE_BIN}/city_add_colliders.py --city ${remoteUsd}`),
    )

    job.percent = PHASES[2].target_percent
    await runProc(
      job, PHASES[2].name, PHASES[2].display_name, 'ssh',
      sshArgs(
        `python3 ${REMOTE_BIN}/city_enrich_textures.py --city ${remoteUsd} ` +
        `--prompt ${shellEscape(prompt)}`,
      ),
    )

    job.percent = PHASES[3].target_percent
    await runProc(
      job, PHASES[3].name, PHASES[3].display_name, 'ssh',
      sshArgs(
        `blender45 --background --python ${REMOTE_BIN}/usd_to_glb.py -- ` +
        `--input ${remoteUsd} --output ${remoteGlb} --max-texture 1024`,
      ),
    )

    const localGlb = join(CACHE_DIR, `${name}_${job.id}.glb`)
    job.percent = PHASES[4].target_percent
    await runProc(
      job, PHASES[4].name, PHASES[4].display_name, 'scp',
      scpArgs(`${SSH_USER}@${EC2_IP}:${remoteGlb}`, localGlb),
    )

    job.localGlb = localGlb
    job.glbUrl = `/artifacts/${job.id}/preview-glb`
    job.percent = 100
    job.currentStep = null
    job.status = 'completed'
  } catch (err) {
    job.status = 'failed'
    job.error = err.message
    job.log.push(`[ERROR] ${err.message}`)
  }
}

// Single-quote escape for bash on the remote side. We pass a single string to
// `ssh` which the remote shell re-parses, so any user-supplied substring
// (city name, façade prompt) has to survive that re-parse safely.
function shellEscape(s) {
  return `'${String(s).replace(/'/g, `'\\''`)}'`
}

function newJob(params) {
  const id = String(nextId++)
  const job = {
    id,
    status: 'queued',
    currentStep: null,
    completedSteps: [],
    percent: 0,
    log: [],
    glbUrl: null,
    localGlb: null,
    error: null,
    startedAt: Date.now(),
    params,
  }
  jobs.set(id, job)
  runJob(job)
  return job
}

function sendJSON(res, status, body) {
  res.writeHead(status, {
    'content-type': 'application/json',
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'GET,POST,OPTIONS',
    'access-control-allow-headers': 'content-type',
  })
  res.end(JSON.stringify(body))
}

function validateParams(p) {
  const lat = Number(p.lat)
  const lon = Number(p.lon)
  const radius = Number(p.radius)
  if (!Number.isFinite(lat) || lat < -90 || lat > 90) return 'lat out of range'
  if (!Number.isFinite(lon) || lon < -180 || lon > 180) return 'lon out of range'
  if (!Number.isFinite(radius) || radius < 50 || radius > 5000) {
    return 'radius must be 50–5000 m'
  }
  if (typeof p.name !== 'string' || !/^[a-zA-Z0-9_-]{1,40}$/.test(p.name)) {
    return 'name must be 1–40 chars, alphanumeric/_/-'
  }
  if (typeof p.prompt !== 'string' || p.prompt.length > 400) {
    return 'prompt must be a string ≤ 400 chars'
  }
  return { lat, lon, radius, name: p.name, prompt: p.prompt }
}

const server = http.createServer((req, res) => {
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET,POST,OPTIONS',
      'access-control-allow-headers': 'content-type',
    })
    return res.end()
  }

  if (req.method === 'GET' && req.url === '/health') {
    return sendJSON(res, 200, {
      status: EC2_IP ? 'healthy' : 'misconfigured',
      ec2_ip: EC2_IP || null,
      ssh_key: SSH_KEY,
      cache_dir: CACHE_DIR,
      sync_scripts: SYNC_SCRIPTS,
    })
  }

  if (req.method === 'GET' && req.url === '/pipeline/presets') {
    return sendJSON(res, 200, PRESETS)
  }

  if (req.method === 'POST' && req.url === '/pipeline') {
    if (!EC2_IP) return sendJSON(res, 503, { error: 'EC2_IP not set on bridge' })
    let body = ''
    req.on('data', (c) => { body += c })
    req.on('end', () => {
      let raw
      try { raw = JSON.parse(body) } catch { return sendJSON(res, 400, { error: 'invalid JSON' }) }
      const validated = validateParams(raw)
      if (typeof validated === 'string') return sendJSON(res, 400, { error: validated })
      const job = newJob(validated)
      sendJSON(res, 200, { session_id: job.id })
    })
    return
  }

  let m = req.url && req.url.match(/^\/pipeline\/([^/]+)\/status$/)
  if (req.method === 'GET' && m) {
    const job = jobs.get(m[1])
    if (!job) return sendJSON(res, 404, { error: 'session not found' })
    return sendJSON(res, 200, jobView(job))
  }

  m = req.url && req.url.match(/^\/artifacts\/([^/]+)\/preview-glb$/)
  if (req.method === 'GET' && m) {
    const job = jobs.get(m[1])
    if (!job) return sendJSON(res, 404, { error: 'session not found' })
    if (!job.localGlb || !existsSync(job.localGlb)) {
      return sendJSON(res, 404, { error: 'glb not ready' })
    }
    const stat = statSync(job.localGlb)
    res.writeHead(200, {
      'content-type': 'model/gltf-binary',
      'content-length': stat.size,
      'access-control-allow-origin': '*',
      'cache-control': 'public, max-age=300',
    })
    return createReadStream(job.localGlb).pipe(res)
  }

  sendJSON(res, 404, { error: 'not found' })
})

server.listen(PORT, '127.0.0.1', () => {
  console.log(`scene-composer bridge: http://localhost:${PORT}`)
  console.log(`  EC2_IP=${EC2_IP || '(not set)'}  SSH_KEY=${SSH_KEY}`)
  console.log(`  cache=${CACHE_DIR}  sync_scripts=${SYNC_SCRIPTS}`)
  if (!EC2_IP) {
    console.error('WARN: EC2_IP env var not set — POST /pipeline will reject with 503.')
  }
  if (!existsSync(SSH_KEY)) {
    console.error(`WARN: SSH key not found at ${SSH_KEY}`)
  }
})
