async function loadStats() {
  const res = await fetch('/api/stats');
  const data = await res.json();
  document.getElementById('stat-motion').textContent = data.motion_events;
  document.getElementById('stat-sightings').textContent = data.sightings;
  document.getElementById('stat-individuals').textContent = data.individuals;
  document.getElementById('stat-identified').textContent = data.individuals_identified ?? 0;
  document.getElementById('stat-solo').textContent = data.individuals_solo ?? 0;
  document.getElementById('stat-other').textContent = data.other_not_mesange ?? 0;
}

function getSightingFilters() {
  const individual = document.getElementById('filter-individual').value;
  const minConfidence = document.getElementById('filter-confidence').value || '0';
  const dateFrom = document.getElementById('filter-from').value;
  const dateTo = document.getElementById('filter-to').value;

  const params = new URLSearchParams();
  params.set('limit', '24');
  params.set('min_confidence', minConfidence);

  if (individual) {
    params.set('individual_id', individual);
  }
  if (dateFrom) {
    params.set('date_from', `${dateFrom}T00:00:00`);
  }
  if (dateTo) {
    params.set('date_to', `${dateTo}T23:59:59`);
  }

  return params.toString();
}

function renderCameraStatus(data) {
  const pill = document.getElementById('camera-status-pill');
  const text = document.getElementById('camera-status-text');
  if (!pill || !text) {
    return;
  }

  if (data.available) {
    pill.textContent = 'OK';
    pill.className = 'status-pill status-ok';
  } else if (data.detected) {
    pill.textContent = 'BUSY';
    pill.className = 'status-pill status-warn';
  } else {
    pill.textContent = 'KO';
    pill.className = 'status-pill status-bad';
  }

  text.textContent = `${data.message || 'no detail'} | detected=${data.detected} | stream_active=${data.stream_active}`;
}

async function loadCameraStatus() {
  try {
    const res = await fetch('/api/camera/status');
    const data = await res.json();
    renderCameraStatus(data);
  } catch (err) {
    renderCameraStatus({
      available: false,
      detected: false,
      stream_active: false,
      message: `status fetch failed: ${err}`,
    });
  }
}

async function loadLatest() {
  const res = await fetch('/api/latest');
  const data = await res.json();
  const img = document.getElementById('latest-image');
  const meta = document.getElementById('latest-meta');

  if (!data.latest || !data.latest.image_url) {
    img.removeAttribute('src');
    meta.textContent = 'Pas encore de capture.';
    return;
  }

  img.src = `${data.latest.image_url}?t=${Date.now()}`;
  meta.textContent = `At ${data.latest.created_at} | motion=${Number(data.latest.motion_score).toFixed(4)} | birds=${data.latest.bird_detections}`;
}

async function loadSightings() {
  const query = getSightingFilters();
  const res = await fetch(`/api/sightings?${query}`);
  const data = await res.json();
  const container = document.getElementById('sightings');
  container.innerHTML = '';

  for (const item of data.items) {
    const el = document.createElement('article');
    el.className = 'card';
    const imgUrl = item.image_url ? `${item.image_url}?t=${Date.now()}` : '';
    el.innerHTML = `
      <img src="${imgUrl}" alt="sighting ${item.id}" />
      <div class="info">
        #${item.id} | indiv #${item.individual_id}<br/>
        conf=${Number(item.confidence).toFixed(3)}<br/>
        total indiv sightings=${item.sightings_count}
      </div>
    `;
    container.appendChild(el);
  }
}

function renderTimeline(items) {
  const el = document.getElementById('timeline');
  el.innerHTML = '';

  if (!items.length) {
    el.textContent = 'Pas assez de données pour les dernières 24h.';
    return;
  }

  const maxMotion = Math.max(...items.map((x) => Number(x.motion_events || 0)), 1);

  for (const item of items) {
    const motion = Number(item.motion_events || 0);
    const birds = Number(item.bird_events || 0);
    const widthPct = Math.max(4, Math.round((motion / maxMotion) * 100));
    const row = document.createElement('div');
    row.className = 'timeline-row';
    row.innerHTML = `
      <span class="timeline-label">${item.bucket.slice(11, 16)}</span>
      <div class="timeline-track">
        <div class="timeline-bar" style="width:${widthPct}%"></div>
      </div>
      <span class="timeline-values">${motion} evt / ${birds} bird</span>
    `;
    el.appendChild(row);
  }
}

async function loadTimeline() {
  const res = await fetch('/api/stats/timeline?hours=24');
  const data = await res.json();
  renderTimeline(data.items || []);
}

async function loadHighlights() {
  const res = await fetch('/api/highlights?limit=8');
  const data = await res.json();
  const container = document.getElementById('highlights');
  container.innerHTML = '';

  for (const item of data.items || []) {
    const el = document.createElement('article');
    el.className = 'card';
    const imgUrl = item.crop_url || item.image_url || '';
    el.innerHTML = `
      <img src="${imgUrl ? `${imgUrl}?t=${Date.now()}` : ''}" alt="highlight ${item.id}" />
      <div class="info">
        #${item.id} | indiv #${item.individual_id}<br/>
        conf=${Number(item.confidence).toFixed(3)}<br/>
        sightings indiv=${item.sightings_count}
      </div>
    `;
    container.appendChild(el);
  }
}

function setFeedback(message, isError = false) {
  const feedback = document.getElementById('action-feedback');
  feedback.textContent = message;
  feedback.style.color = isError ? '#6b1416' : '#6b695f';
}

async function testAlert() {
  try {
    const res = await fetch('/api/alerts/test', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      setFeedback(`Alerte KO: ${data.error || res.status}`, true);
      return;
    }
    setFeedback('Alerte test envoyée.');
  } catch (err) {
    setFeedback(`Alerte KO: ${err}`, true);
  }
}

async function exportDaily() {
  try {
    const res = await fetch('/api/export/daily?days=7', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      setFeedback(`Export KO: ${data.error || res.status}`, true);
      return;
    }
    const fileUrl = data.url || '';
    setFeedback(`Export OK (${data.rows} lignes). ${fileUrl}`);
  } catch (err) {
    setFeedback(`Export KO: ${err}`, true);
  }
}

async function refresh() {
  await Promise.all([
    loadStats(),
    loadLatest(),
    loadSightings(),
    loadCameraStatus(),
    loadTimeline(),
    loadHighlights(),
  ]);
}

document.getElementById('btn-apply-filters').addEventListener('click', () => {
  loadSightings();
});
document.getElementById('btn-test-alert').addEventListener('click', testAlert);
document.getElementById('btn-export').addEventListener('click', exportDaily);

refresh();
setInterval(refresh, 5000);
