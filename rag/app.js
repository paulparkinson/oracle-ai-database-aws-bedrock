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

let reviewReceipt = null;
const generateButton = document.querySelector('#nl-generate');
const executeButton = document.querySelector('#nl-execute');
const nlStatus = document.querySelector('#nl-status');
async function postJSON(path, payload) {
  const response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Live request failed');
  return data;
}
function clearReview() {
  reviewReceipt = null; executeButton.disabled = true;
  document.querySelector('#nl-review').hidden = true;
  document.querySelector('#nl-results').hidden = true;
}
document.querySelector('#nl-question').addEventListener('input', clearReview);
generateButton.addEventListener('click', async () => {
  clearReview(); generateButton.disabled = true;
  const question = document.querySelector('#nl-question').value;
  nlStatus.textContent = 'Calling live Bedrock Nova Lite to generate SQL…';
  try {
    const result = await postJSON('/nl2sql/generate', {question});
    if (question !== document.querySelector('#nl-question').value) {
      nlStatus.textContent = 'Question changed. Generate SQL again.'; return;
    }
    nlStatus.textContent = result.message;
    if (result.rejected) return;
    reviewReceipt = result.receipt;
    document.querySelector('#nl-sql').textContent = result.sql;
    document.querySelector('#nl-proof').textContent = 'Model: ' + result.model + ' · Bedrock request: ' + result.request_id;
    document.querySelector('#nl-bound').textContent = result.parameterized_sql + '\n\nBinds: ' + JSON.stringify(result.binds);
    document.querySelector('#nl-review').hidden = false;
    executeButton.disabled = false;
  } catch (error) { nlStatus.textContent = error.message; }
  finally { generateButton.disabled = false; document.querySelector('#nl-question').disabled = false; }
});
executeButton.addEventListener('click', async () => {
  const receipt = reviewReceipt;
  executeButton.disabled = true; generateButton.disabled = true; reviewReceipt = null;
  document.querySelector('#nl-question').disabled = true;
  nlStatus.textContent = 'Running the reviewed query on Oracle in a read-only transaction…';
  try {
    const result = await postJSON('/nl2sql/execute', {receipt});
    const body = document.querySelector('#nl-rows'); body.replaceChildren();
    for (const row of result.rows) {
      const tr = document.createElement('tr');
      for (const key of ['sku','product','warehouse','stockout_risk']) {
        const td = document.createElement('td'); td.textContent = row[key]; tr.append(td);
      }
      body.append(tr);
    }
    document.querySelector('#nl-verification').textContent = result.verification;
    document.querySelector('#nl-results').hidden = false;
    nlStatus.textContent = result.row_count + ' row(s) returned by Oracle. No persistent writes.';
  } catch (error) { nlStatus.textContent = error.message; }
  finally { generateButton.disabled = false; document.querySelector('#nl-question').disabled = false; }
});
