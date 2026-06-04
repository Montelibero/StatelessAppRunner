#!/usr/bin/env node

import { createHash, randomBytes } from 'node:crypto';

const BASE_URL = (process.env.APP_BASE_URL || 'https://mtlminiapps.us').replace(/\/$/, '');
const AGENT_NAME = process.env.AGENT_NAME || 'agent-node';

function toBase32(buf) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  let bits = 0;
  let value = 0;
  let out = '';
  for (const byte of buf) {
    value = (value << 8) | byte;
    bits += 8;
    while (bits >= 5) {
      out += alphabet[(value >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  if (bits > 0) {
    out += alphabet[(value << (5 - bits)) & 31];
  }
  return out;
}

function deriveAgentId(secret) {
  const digest = createHash('sha256').update(secret, 'utf8').digest();
  const body = toBase32(digest);
  return `MTLA${body.slice(4)}`;
}

function newSecret() {
  return randomBytes(18).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

async function fetchPowChallenge() {
  const res = await fetch(`${BASE_URL}/api/agent/register/challenge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`challenge failed: ${res.status} ${text}`);
  }
  return await res.json();
}

function base64UrlDecode(input) {
  const padLen = (4 - (input.length % 4)) % 4;
  const padded = input + '='.repeat(padLen);
  return Buffer.from(padded, 'base64url');
}

function parsePowChallenge(challenge) {
  const [payloadB64] = challenge.split('.', 1);
  const payload = JSON.parse(base64UrlDecode(payloadB64).toString('utf8'));
  return { seed: String(payload.n), bits: Number(payload.b) };
}

async function register(agentSecret, powChallenge, powNonce) {
  const res = await fetch(`${BASE_URL}/api/agent/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      agent_secret: agentSecret,
      pow_challenge: powChallenge,
      pow_nonce: powNonce,
      agent_name: AGENT_NAME,
      client: 'node',
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`register failed: ${res.status} ${text}`);
  }
  return await res.json();
}

function leadingZeroBits(buf) {
  let bits = 0;
  for (const byte of buf) {
    if (byte === 0) {
      bits += 8;
      continue;
    }
    return bits + (8 - Math.floor(Math.log2(byte)) - 1);
  }
  return bits;
}

function solveRegistrationPow(seed, secret, bits) {
  const startedAt = Date.now();
  let tries = 0;
  let nonce = 0;
  while (true) {
    tries += 1;
    nonce += 1;
    const nonceStr = String(nonce);
    const digest = createHash('sha256')
      .update(`${seed}:${secret}:${nonceStr}`, 'utf8')
      .digest();
    const elapsedSec = (Date.now() - startedAt) / 1000;
    if (leadingZeroBits(digest) >= bits) {
      return { nonce: nonceStr, tries, elapsedSec };
    }
  }
}

async function main() {
  const agentSecret = newSecret();
  const challengeResp = await fetchPowChallenge();
  const powChallenge = challengeResp.pow_challenge;
  const pow = parsePowChallenge(powChallenge);
  const solved = solveRegistrationPow(pow.seed, agentSecret, pow.bits);
  console.log(
    `Registration PoW solved in ${solved.tries} tries (${solved.elapsedSec.toFixed(1)}s), nonce=${solved.nonce}`
  );

  const data = await register(agentSecret, powChallenge, solved.nonce);
  const bearer_token = data.bearer_token;

  console.log('\nagent_id:', data.agent_id);
  console.log('bearer_token:', bearer_token);

  console.log('\nDefault mode example:');
  console.log(
    `curl -X POST ${BASE_URL}/api/agent/generate -H 'Content-Type: application/json' -H 'Authorization: Bearer ${bearer_token}' -d '{"html":"<h1>Hello</h1>"}'`
  );

  console.log('\nOptional persistent mode example:');
  console.log(
    `curl -X POST ${BASE_URL}/api/agent/apps -H 'Content-Type: application/json' -H 'Authorization: Bearer ${bearer_token}' -d '{"html":"<h1>Saved</h1>"}'`
  );
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
