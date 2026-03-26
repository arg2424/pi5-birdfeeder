async function loadStats() {
  const res = await fetch('/api/stats');
  const data = await res.json();
  document.getElementById('stat-motion').textContent = data.motion_events;
  document.getElementById('stat-sightings').textContent = data.sightings;
  document.getElementById('stat-individuals').textContent = data.individuals;
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
  const res = await fetch('/api/sightings?limit=24');
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

async function refresh() {
  await Promise.all([loadStats(), loadLatest(), loadSightings()]);
}

refresh();
setInterval(refresh, 5000);
