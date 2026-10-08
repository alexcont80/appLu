const initialRows = [
  { label: 'Docente', value: 'Docente dimostrativo', source: 'Lettera incarico', complete: true },
  { label: 'Email', value: 'docente.demo@example.test', source: 'Lettera incarico', complete: true },
  { label: 'Tipologia', value: 'Esterno · tariffa oraria', source: 'Email esatta', complete: true },
  { label: 'Corso', value: 'Corso BLSD dimostrativo', source: 'Oggetto lettera', complete: true },
  { label: 'Protocollo', value: 'Dato dimostrativo', source: 'Lettera incarico', complete: true },
  { label: 'Compenso', value: '€ 250,00', source: 'Lettera + programma', complete: true },
  { label: 'Data e orario', value: '15 ottobre · 14:00–18:00', source: 'Documenti demo', complete: true },
  { label: 'Conto di imputazione', value: '', display: 'Da classificare', source: 'CV · Titoli di studio', complete: false, issue: 'Titolo di studio da classificare secondo i criteri aziendali.' },
  { label: 'Centro di costo', value: '', display: 'In attesa di conferma', source: 'Decisione richiesta · BLSD', complete: false, issue: 'Confermare se il corso BLSD è una convenzione.' },
];

const dataTable = document.querySelector('#dataTable');
const issueList = document.querySelector('#issueList');
const toast = document.querySelector('#toast');
let rows = structuredClone(initialRows);
let decision = null;
let toastTimer;

function renderRows() {
  dataTable.replaceChildren();
  rows.forEach((row) => {
    const line = document.createElement('div');
    line.className = 'data-row';
    const label = document.createElement('span');
    label.className = 'data-label';
    label.textContent = row.label;
    const value = document.createElement('span');
    value.className = `data-value${row.complete ? '' : ' uncertain'}`;
    value.textContent = row.complete ? row.value : (row.display || '');
    const source = document.createElement('span');
    source.className = 'data-source';
    source.textContent = row.source;
    line.append(label, value, source);
    dataTable.append(line);
  });

  const unresolved = rows.filter((row) => !row.complete);
  const isComplete = unresolved.length === 0;
  document.querySelector('#overallState').textContent = isComplete ? 'COMPLETO' : 'DA COMPLETARE';
  document.querySelector('#overallState').className = `state-chip ${isComplete ? 'state-info' : 'state-pending'}`;
  document.querySelector('#statusTitle').textContent = isComplete ? 'Completo' : 'Da completare';
  document.querySelector('#statusCopy').textContent = isComplete
    ? 'Tutti i dati dimostrativi risultano verificati.'
    : `${unresolved.length} ${unresolved.length === 1 ? 'verifica richiesta' : 'verifiche richieste'} prima di chiudere il documento.`;
  const done = rows.length - unresolved.length;
  document.querySelector('#progressText').textContent = `${done} di ${rows.length}`;
  document.querySelector('#progressBar').style.width = `${Math.round(done / rows.length * 100)}%`;
  issueList.replaceChildren();
  unresolved.forEach(({ issue }) => {
    const item = document.createElement('li');
    const bullet = document.createElement('span');
    bullet.className = 'issue-bullet';
    bullet.textContent = '•';
    const text = document.createElement('span');
    text.textContent = issue;
    item.append(bullet, text);
    issueList.append(item);
  });
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 3200);
}

document.querySelector('#chooseFolder').addEventListener('click', () => {
  document.querySelector('#folderInput').click();
});

document.querySelector('#folderInput').addEventListener('change', (event) => {
  const files = [...event.target.files];
  if (!files.length) return;
  showToast(`Anteprima: ${files.length} nomi file rilevati nel browser. Nessun file è stato letto o caricato.`);
  event.target.value = '';
});

document.querySelectorAll('[data-convention]').forEach((button) => {
  button.addEventListener('click', () => {
    decision = button.dataset.convention;
    document.querySelectorAll('[data-convention]').forEach((choice) => choice.classList.toggle('selected', choice === button));
    const centerCost = rows.find((row) => row.label === 'Centro di costo');
    if (decision === 'yes') {
      centerCost.value = 'PAC Formest';
      centerCost.display = 'PAC Formest';
      centerCost.complete = true;
      centerCost.issue = '';
      document.querySelector('#decisionResult').textContent = 'Conferma registrata · centro di costo: PAC Formest';
    } else {
      centerCost.value = '';
      centerCost.display = 'Da definire';
      centerCost.complete = false;
      centerCost.issue = 'Per BLSD non convenzione manca una regola sul centro di costo.';
      document.querySelector('#decisionResult').textContent = 'Conferma registrata · centro di costo non definito dalla regola';
    }
    renderRows();
  });
});

document.querySelector('#resetDemo').addEventListener('click', () => {
  rows = structuredClone(initialRows);
  decision = null;
  document.querySelectorAll('[data-convention]').forEach((choice) => choice.classList.remove('selected'));
  document.querySelector('#decisionResult').textContent = 'In attesa di conferma · campo lasciato vuoto';
  renderRows();
  showToast('La demo è stata ripristinata.');
});

document.querySelector('#showRules').addEventListener('click', () => {
  document.querySelector('#regole').scrollIntoView({ behavior: 'smooth', block: 'start' });
});

document.querySelector('#generateButton').addEventListener('click', () => {
  showToast('Anteprima dimostrativa: generazione Word/PDF non attiva in questa fase.');
});

renderRows();
