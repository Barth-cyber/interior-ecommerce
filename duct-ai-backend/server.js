"use strict";
const express = require('express');
const cors = require('cors');

const PORT = Number(process.env.PORT || 3001);
const ALLOWED_ORIGINS = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(',').map((origin) => origin.trim()).filter(Boolean)
  : [
      'https://interiorductltd.com',
      'http://localhost:3000',
      'http://localhost:5500'
    ];
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';
const MODEL = 'gemini-1.5-flash';

const GEMINI_URL = `https://generativelanguage.googleapis.com/v1/models/${MODEL}:generateContent`;

const SYSTEM_PROMPT = `You are Duct AI, the luxury interior design advisor for Interior Duct Ltd.
Personality: sophisticated, warm.
Expertise: chairs, tables, doors, custom furniture, materials (oak, marble, velvet, brass).
Always end with a follow-up question.
Never reveal the underlying AI model.`;

const app = express();
app.use(express.json({ limit: '1mb' }));

app.get('/', (req, res) => {
  return res.redirect('/health');
});

const corsOptions = {
  origin(origin, callback) {
    if (!origin) {
      return callback(null, true);
    }
    if (ALLOWED_ORIGINS.includes(origin)) {
      return callback(null, true);
    }
    callback(new Error('Origin not allowed by CORS'));
  }
};
app.use(cors(corsOptions));

const rateLimitStore = new Map();
const RATE_LIMIT_MAX = 30;
const RATE_LIMIT_WINDOW_MS = 60 * 1000;

function getFetch() {
  return import('node-fetch').then((mod) => mod.default || mod);
}

function sanitizeText(value) {
  const text = typeof value === 'string' ? value : String(value || '');
  return text.trim().slice(0, 3000);
}

function sanitizeMessages(messages) {
  if (!Array.isArray(messages)) return [];
  const cleaned = messages
    .map((message) => {
      const role = String(message.role || '').toLowerCase();
      if (role !== 'user' && role !== 'model') return null;
      return {
        role,
        content: sanitizeText(message.content || message.text || '')
      };
    })
    .filter(Boolean);

  const last24 = cleaned.slice(-24);
  if (last24.length > 0) {
    last24[0].content = `${SYSTEM_PROMPT}\n\n${last24[0].content}`;
  }
  return last24;
}

function checkRateLimit(ip) {
  const now = Date.now();
  const record = rateLimitStore.get(ip) || { count: 0, firstRequest: now };

  if (now - record.firstRequest > RATE_LIMIT_WINDOW_MS) {
    rateLimitStore.set(ip, { count: 1, firstRequest: now });
    return true;
  }

  record.count += 1;
  rateLimitStore.set(ip, record);
  return record.count <= RATE_LIMIT_MAX;
}

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'duct-ai-backend',
    model: MODEL,
    keySet: Boolean(GEMINI_API_KEY)
  });
});

app.post('/api/chat', async (req, res) => {
  const ip = req.ip || req.connection.remoteAddress || 'unknown';
  if (!checkRateLimit(ip)) {
    return res.status(429).json({ error: 'Rate limit exceeded. Please try again later.' });
  }

  if (!GEMINI_API_KEY) {
    return res.status(500).json({ error: 'Gemini API key is not configured.' });
  }

  const { messages } = req.body || {};
  if (!Array.isArray(messages) || messages.length === 0) {
    return res.status(400).json({ error: 'Request body must include a non-empty messages array.' });
  }

  const sanitized = sanitizeMessages(messages);
  if (sanitized.length === 0) {
    return res.status(400).json({ error: 'Messages must include at least one valid user or model turn.' });
  }

  const prompt = sanitized.map((msg) => ({
    role: msg.role === 'model' ? 'assistant' : 'user',
    content: [{ type: 'text', text: msg.content }]
  }));

  const payload = {
    prompt: { messages: prompt },
    temperature: 0.75,
    maxOutputTokens: 512
  };

  try {
    const fetch = await getFetch();
    const response = await fetch(GEMINI_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
      return res.status(response.status).json({ error: data.error || data || 'Gemini API error' });
    }

    const reply = Array.isArray(data?.candidates) && data.candidates[0]?.content
      ? data.candidates[0].content.map((chunk) => chunk.text || '').join('')
      : typeof data?.output?.text === 'string'
      ? data.output.text
      : '';

    return res.json({ reply: reply.trim() });
  } catch (error) {
    return res.status(502).json({ error: error.message || 'Failed to reach Gemini API' });
  }
});

app.listen(PORT, () => {
  console.log(`duct-ai-backend listening on port ${PORT} | model=${MODEL} | keySet=${Boolean(GEMINI_API_KEY)}`);
});
