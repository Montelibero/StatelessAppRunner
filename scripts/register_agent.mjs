#!/usr/bin/env node

import { createHash, randomBytes } from 'node:crypto';

const BASE_URL = (process.env.APP_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
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
  return toBase32(digest);
}

function challengeOk(agentId) {
  return agentId.endsWith('MTL') && agentId.length >= 8 && /^[A-Z]{8}/.test(agentId);
}

function newSecret() {
  return randomBytes(18).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

async function register(agentSecret) {
  const res = await fetch(`${BASE_URL}/api/agent/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      agent_secret: agentSecret,
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

async function main() {
  let tries = 0;
  let agentSecret;
  while (true) {
    tries += 1;
    const secret = newSecret();
    const agentId = deriveAgentId(secret);
    if (challengeOk(agentId)) {
      agentSecret = secret;
      break;
    }
  }

  console.log(`Challenge solved in ${tries} tries`);
  const data = await register(agentSecret);
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
