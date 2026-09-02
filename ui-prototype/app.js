const toast = document.querySelector('#toast');
const show = message => { toast.textContent = message; toast.classList.add('show'); clearTimeout(window.toastTimer); window.toastTimer = setTimeout(() => toast.classList.remove('show'), 2100); };
document.querySelectorAll('[data-action]').forEach(button => button.addEventListener('click', () => show(`${button.dataset.action} — demo only`)));
document.querySelectorAll('.edit-binding').forEach(button => button.addEventListener('click', () => show(`Choose a new action for ${button.dataset.binding} — demo only`)));
document.querySelector('#emergencyStop').addEventListener('click', () => show('STOP ALL — demo only'));
document.querySelector('#speed').addEventListener('input', event => document.querySelector('#speedValue').textContent = event.target.value);
document.querySelectorAll('.preset:not(.add)').forEach(button => button.addEventListener('click', () => { document.querySelectorAll('.preset').forEach(item => item.classList.remove('active')); button.classList.add('active'); show(`Preset recalled: ${button.querySelector('strong').textContent} — demo only`); }));

let phase = 0;
setInterval(() => {
  phase += .13;
  const values = [Math.sin(phase) * .57, Math.cos(phase * .72) * .39, Math.sin(phase * 1.4) * .22, .62 + Math.sin(phase * .38) * .14];
  [['X', values[0]], ['Y', values[1]], ['Z', values[2]]].forEach(([axis, value]) => { document.querySelector(`#axis${axis}`).textContent = `${value >= 0 ? '+' : ''}${value.toFixed(2)}`; document.querySelector(`#bar${axis}`).style.width = `${50 + value * 50}%`; });
  document.querySelector('#axisT').textContent = `${Math.round(values[3] * 100)}%`; document.querySelector('#barT').style.width = `${values[3] * 100}%`;
}, 300);
