let currentQuestion = null;
let curriculum = {};

async function api(path, options = {}) {
  const res = await fetch(path, { headers: {"Content-Type": "application/json", ...(options.headers || {})}, ...options });
  if (res.status === 401) { document.querySelector('#app').classList.add('hidden'); document.querySelector('#loginCard').classList.remove('hidden'); }
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

async function login() {
  const password = document.querySelector('#password').value;
  const data = await api('/api/auth/login', {method:'POST', body: JSON.stringify({password})});
  if (!data.ok) { document.querySelector('#loginMsg').textContent = 'Incorrect password'; return; }
  await boot();
}

async function boot() {
  document.querySelector('#loginCard').classList.add('hidden');
  document.querySelector('#app').classList.remove('hidden');
  curriculum = await api('/api/curriculum');
  const subject = document.querySelector('#subject');
  subject.innerHTML = Object.keys(curriculum).map(s => `<option>${s}</option>`).join('');
  refreshTopics();
  await loadStudents();
}

function refreshTopics() {
  const s = document.querySelector('#subject').value;
  document.querySelector('#topic').innerHTML = (curriculum[s] || []).map(t => `<option>${t}</option>`).join('');
}

async function loadStudents() {
  const students = await api('/api/students');
  const select = document.querySelector('#studentSelect');
  select.innerHTML = students.map(s => `<option value="${s.id}">${s.display_name} (Grade ${s.grade})</option>`).join('');
  if (students.length) { await refreshRecommendation(); await loadDashboard(); }
}

async function addStudent() {
  const display_name = document.querySelector('#newStudent').value.trim();
  const grade = Number(document.querySelector('#grade').value || 2);
  if (!display_name) return;
  await api('/api/students', {method:'POST', body:JSON.stringify({display_name, grade})});
  document.querySelector('#newStudent').value = '';
  await loadStudents();
}

function studentId() { return Number(document.querySelector('#studentSelect').value); }

async function teach() {
  if (!studentId()) return;
  const subject = document.querySelector('#subject').value;
  const topic = document.querySelector('#topic').value;
  const data = await api('/api/tutor', {method:'POST', body:JSON.stringify({student_id:studentId(), subject, topic})});
  document.querySelector('#teacher').textContent = `👩‍🏫 ${data.text}`;
}

async function nextQuestion() {
  const subject = document.querySelector('#subject').value;
  const topic = document.querySelector('#topic').value;
  let difficulty = 1;
  if (studentId()) {
    const rec = await api(`/api/recommendation/${studentId()}`);
    if (rec.subject === subject && rec.topic === topic) difficulty = rec.difficulty || 1;
  }
  currentQuestion = await api(`/api/quiz?subject=${encodeURIComponent(subject)}&topic=${encodeURIComponent(topic)}&difficulty=${difficulty}`);
  document.querySelector('#question').textContent = currentQuestion.question;
  document.querySelector('#answer').value = '';
  document.querySelector('#feedback').textContent = '';
  document.querySelector('#quizBox').classList.remove('hidden');
  document.querySelector('#answer').focus();
}

async function submitAnswer() {
  if (!currentQuestion || !studentId()) return;
  const submitted_answer = document.querySelector('#answer').value;
  const data = await api('/api/quiz/answer', {method:'POST', body:JSON.stringify({
    student_id: studentId(),
    question_id: currentQuestion.question_id,
    submitted_answer
  })});
  document.querySelector('#feedback').textContent = `${data.feedback} Mastery: ${data.mastery}%`;
  await refreshRecommendation();
  await loadDashboard();
}

async function refreshRecommendation() {
  if (!studentId()) return;
  const r = await api(`/api/recommendation/${studentId()}`);
  document.querySelector('#recommendation').textContent = `🧠 Next: ${r.action.toUpperCase()} — ${r.subject} / ${r.topic}. ${r.reason}`;
}

async function buildAbacus() {
  const number = Number(document.querySelector('#abacusNumber').value || 0);
  const data = await api('/api/abacus', {method:'POST', body:JSON.stringify({number})});
  document.querySelector('#abacusBoard').innerHTML = data.columns.map(c => `
    <div class="rod"><strong>${c.place}</strong><div>${c.digit}</div>
    ${Array.from({length:9}, (_,i) => `<div class="bead ${i < c.active_beads ? 'active':''}"></div>`).join('')}
    </div>`).join('');
  document.querySelector('#abacusSteps').innerHTML = data.steps.map(s => `<li>${s}</li>`).join('');
}

async function loadDashboard() {
  if (!studentId()) return;
  const d = await api(`/api/dashboard/${studentId()}`);
  document.querySelector('#summary').textContent = `${d.student.name}: ${d.summary.questions} questions • ${d.summary.accuracy}% accuracy`;
  document.querySelector('#progressRows').innerHTML = d.topics.map(t => `<tr><td>${t.subject}</td><td>${t.topic}</td><td>${t.attempted}</td><td>${t.mastery}%</td><td>${t.difficulty}</td></tr>`).join('');
}

function showTab(name) {
  document.querySelectorAll('.tab').forEach(x => x.classList.add('hidden'));
  document.querySelector(`#${name}`).classList.remove('hidden');
  if (name === 'parent') loadDashboard();
}

document.querySelector('#studentSelect')?.addEventListener('change', async () => { await refreshRecommendation(); await loadDashboard(); });

(async () => {
  try {
    const s = await api('/api/auth/status');
    if (s.authenticated) await boot();
  } catch (_) {}
})();
