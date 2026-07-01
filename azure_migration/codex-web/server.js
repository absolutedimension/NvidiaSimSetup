'use strict';
/*
 * codex-web — thin web client that drives the Codex CLI (Azure OpenAI) on this VM.
 *
 * Browser  --HTTP/SSE-->  this server  --spawn-->  `codex exec --json`
 *
 * Two profiles (defined in ~/.codex/{dev,plan}.config.toml):
 *   dev  -> gpt-5.3-codex  (coding)
 *   plan -> gpt-5.5        (reasoning / planning)
 *
 * Multi-turn: each chat keeps a Codex thread_id; follow-ups use `codex exec resume <id>`.
 * Auth: a shared access key (CODEX_WEB_KEY) checked on every /api call.
 */
const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const PORT = parseInt(process.env.CODEX_WEB_PORT || '7878', 10);
const ACCESS_KEY = process.env.CODEX_WEB_KEY || '';
const WORKSPACE_ROOT = process.env.CODEX_WORKSPACE || path.join(os.homedir(), 'projects');
const CODEX_BIN = process.env.CODEX_BIN || 'codex';

fs.mkdirSync(WORKSPACE_ROOT, { recursive: true });

const app = express();
app.use(express.json({ limit: '4mb' }));

// ---- auth gate (all /api/* except the public config probe) ----
app.get('/api/public-config', (_req, res) => {
  res.json({ authRequired: Boolean(ACCESS_KEY) });
});
app.use('/api', (req, res, next) => {
  if (!ACCESS_KEY) return next();
  const key = req.get('x-access-key') || req.query.key;
  if (key !== ACCESS_KEY) return res.status(401).json({ error: 'unauthorized' });
  next();
});

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, workspace: WORKSPACE_ROOT, models: { dev: 'gpt-5.3-codex', plan: 'gpt-5.5' } });
});

// list project folders under the workspace root so the dev can pick one
app.get('/api/dirs', (_req, res) => {
  try {
    const dirs = fs.readdirSync(WORKSPACE_ROOT, { withFileTypes: true })
      .filter(d => d.isDirectory() && !d.name.startsWith('.'))
      .map(d => d.name)
      .sort();
    res.json({ root: WORKSPACE_ROOT, dirs });
  } catch (e) {
    res.json({ root: WORKSPACE_ROOT, dirs: [], error: String(e) });
  }
});

// resolve a user-supplied subdir safely inside the workspace root
function resolveWorkdir(cwd) {
  if (!cwd) return WORKSPACE_ROOT;
  const candidate = path.resolve(WORKSPACE_ROOT, cwd);
  if ((candidate === WORKSPACE_ROOT || candidate.startsWith(WORKSPACE_ROOT + path.sep)) && fs.existsSync(candidate)) {
    return candidate;
  }
  return WORKSPACE_ROOT;
}

// ---- the agent turn: streams Codex JSONL events to the browser over SSE ----
app.post('/api/chat', (req, res) => {
  const { prompt, profile, threadId, cwd, sandbox } = req.body || {};
  if (!prompt || !String(prompt).trim()) return res.status(400).json({ error: 'empty prompt' });

  const prof = profile === 'plan' ? 'plan' : 'dev';
  const sbx = ['read-only', 'workspace-write', 'danger-full-access'].includes(sandbox) ? sandbox : 'workspace-write';
  const workdir = resolveWorkdir(cwd);

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');
  if (res.flushHeaders) res.flushHeaders();
  const send = (event, data) => res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);

  let args;
  if (threadId) {
    // resume an existing conversation (profile/model are inherited from the session)
    args = ['exec', 'resume', String(threadId), '--json', '--skip-git-repo-check', '-c', `sandbox_mode="${sbx}"`, String(prompt)];
  } else {
    args = ['exec', '--json', '--skip-git-repo-check', '-p', prof, '-s', sbx, '-C', workdir, String(prompt)];
  }

  send('meta', { profile: prof, sandbox: sbx, workdir, model: prof === 'plan' ? 'gpt-5.5' : 'gpt-5.3-codex' });

  let child;
  try {
    // stdin = 'ignore' so codex gets immediate EOF and never blocks waiting on a piped <stdin> block
    child = spawn(CODEX_BIN, args, { env: process.env, cwd: workdir, stdio: ['ignore', 'pipe', 'pipe'] });
  } catch (e) {
    send('error', { text: 'failed to spawn codex: ' + String(e) });
    send('done', { code: -1 });
    return res.end();
  }

  let buf = '';
  child.stdout.on('data', (chunk) => {
    buf += chunk.toString();
    let idx;
    while ((idx = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, idx).trim();
      buf = buf.slice(idx + 1);
      if (!line) continue;
      try { send('codex', JSON.parse(line)); }
      catch (_e) { send('log', { text: line }); }
    }
  });

  let errbuf = '';
  child.stderr.on('data', (c) => { errbuf += c.toString(); });

  child.on('error', (e) => {
    send('error', { text: 'codex process error: ' + String(e) });
  });

  child.on('close', (code) => {
    const tail = buf.trim();
    if (tail) { try { send('codex', JSON.parse(tail)); } catch (_e) { send('log', { text: tail }); } }
    if (code !== 0 && errbuf.trim()) send('error', { text: errbuf.trim().slice(-3000), code });
    send('done', { code });
    res.end();
  });

  // res 'close' fires when the client actually disconnects (req 'close' fires as soon as the
  // request body is consumed, which would kill the child immediately).
  let finished = false;
  child.on('close', () => { finished = true; });
  res.on('close', () => { if (!finished) { try { child.kill('SIGTERM'); } catch (_e) {} } });
});

app.use(express.static(path.join(__dirname, 'public')));

app.listen(PORT, '0.0.0.0', () => {
  console.log(`[codex-web] listening on :${PORT}  workspace=${WORKSPACE_ROOT}  auth=${ACCESS_KEY ? 'on' : 'OFF'}`);
});
