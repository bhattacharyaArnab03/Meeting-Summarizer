const form = document.querySelector('#upload-form');
const input = document.querySelector('#audio-file');
const label = document.querySelector('#file-label');
const status = document.querySelector('#status');
const results = document.querySelector('#results');
const button = document.querySelector('.process-button');

input.addEventListener('change', () => {
  label.textContent = input.files[0]?.name || 'Choose meeting audio';
});

function fillList(id, values) {
  const element = document.querySelector(id);
  element.replaceChildren();
  (values.length ? values : ['None identified in the transcript.']).forEach(value => {
    const item = document.createElement('li');
    item.textContent = value;
    element.append(item);
  });
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (!input.files[0]) return;
  button.disabled = true;
  status.className = 'status';
  status.textContent = 'Transcribing audio and extracting decisions...';
  results.hidden = true;
  const body = new FormData(form);
  try {
    const response = await fetch('/api/meetings/process', { method: 'POST', body });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Meeting processing failed.');
    document.querySelector('#meeting-id').textContent = payload.meeting_id;
    document.querySelector('#executive-summary').textContent = payload.summary.executive_summary;
    document.querySelector('#transcript').textContent = payload.transcript;
    fillList('#decisions', payload.summary.decisions);
    fillList('#key-points', payload.summary.key_points);
    fillList('#risks', payload.summary.risks);
    fillList('#follow-ups', payload.summary.follow_ups);
    const rows = document.querySelector('#action-items');
    rows.replaceChildren();
    if (!payload.summary.action_items.length) {
      rows.innerHTML = '<tr><td colspan="3">No supported action items identified.</td></tr>';
    } else payload.summary.action_items.forEach(action => {
      const row = document.createElement('tr');
      [action.task, action.owner || 'Not specified', action.deadline || 'Not specified'].forEach(value => { const cell = document.createElement('td'); cell.textContent = value; row.append(cell); });
      rows.append(row);
    });
    results.hidden = false;
    status.textContent = 'Complete. Review the meeting record below.';
    results.scrollIntoView({ behavior: 'smooth' });
  } catch (error) {
    status.className = 'status error';
    status.textContent = error.message;
  } finally { button.disabled = false; }
});
