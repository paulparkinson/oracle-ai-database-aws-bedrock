const button = document.querySelector('#ask');
button.addEventListener('click', async () => {
  button.disabled = true;
  document.querySelector('#result').hidden = true;
  const status = document.querySelector('#status');
  status.textContent = 'Running live: embed → query Oracle → generate cited answer…';
  try {
    const response = await fetch('/ask', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question:document.querySelector('#question').value})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Live request failed');
    document.querySelector('#answer').textContent = data.answer;
    const evidence = document.querySelector('#evidence'); evidence.replaceChildren();
    for (const row of data.evidence) {
      const card = document.createElement('div'); card.className = 'evidence';
      const title = document.createElement('strong'); title.textContent = `${row.id} · cosine distance ${row.distance.toFixed(6)}`;
      const text = document.createElement('p'); text.textContent = row.text;
      card.append(title, text); evidence.append(card);
    }
    document.querySelector('#verification').textContent = data.verification;
    document.querySelector('#result').hidden = false;
    status.textContent = 'Complete. Live services returned the evidence and answer below.';
  } catch (error) { status.textContent = error.message; }
  finally { button.disabled = false; }
});
