// FAQ Manager UI for Admin Panel
// Allows reviewing user logs and adding new FAQs to knowledge_base.json

let userLogs = [];
let faqs = [];

async function fetchUserLogs() {
  const res = await fetch('/user-log');
  if (!res.ok) return [];
  return await res.json();
}

async function fetchFAQs() {
  const res = await fetch('/kb');
  if (!res.ok) return [];
  const kb = await res.json();
  return kb.faqs || [];
}

async function renderFAQManager() {
  userLogs = await fetchUserLogs();
  faqs = await fetchFAQs();
  const container = document.getElementById('faq-manager');
  if (!container) return;
  container.innerHTML = '<h2>FAQ Manager</h2>';
  container.innerHTML += '<h3>User Questions (not in FAQ):</h3>';
  const faqQuestions = new Set(faqs.map(f => f.q.toLowerCase()));
  const newQs = userLogs.filter(log => log.query && !faqQuestions.has(log.query.toLowerCase()));
  if (!newQs.length) {
    container.innerHTML += '<p>No new user questions found.</p>';
  } else {
    newQs.forEach(log => {
      const div = document.createElement('div');
      div.style = 'border:1px solid #ccc;padding:8px;margin:8px 0;border-radius:6px;';
      // Auto-suggest answer from closest FAQ
      let suggestion = '';
      let bestScore = 0;
      faqs.forEach(faq => {
        const q1 = log.query.toLowerCase();
        const q2 = faq.q.toLowerCase();
        let score = 0;
        if (q1 === q2) score = 1;
        else if (q1.includes(q2) || q2.includes(q1)) score = 0.8;
        else if (q1.split(' ').some(w => q2.includes(w))) score = 0.6;
        if (score > bestScore) {
          bestScore = score;
          suggestion = faq.a;
        }
      });
      div.innerHTML = `<strong>Q:</strong> ${log.query}<br><label>Add answer: <input type="text" id="ans-${log.query.replace(/[^a-z0-9]/gi,'_')}" style="width:60%" value="${suggestion}"></label> <button onclick="addFAQ('${log.query.replace(/'/g,"&#39;")}")">Add to FAQ</button>`;
      container.appendChild(div);
    });
  }
}

async function addFAQ(question) {
  const inputId = `ans-${question.replace(/[^a-z0-9]/gi,'_')}`;
  const answer = document.getElementById(inputId).value.trim();
  if (!answer) return alert('Please provide an answer.');
  const kbRes = await fetch('/kb');
  const kb = await kbRes.json();
  kb.faqs = kb.faqs || [];
  kb.faqs.push({q: question, a: answer});
  await fetch('/kb', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(kb)
  });
  alert('FAQ added!');
  renderFAQManager();
}

document.addEventListener('DOMContentLoaded', renderFAQManager);