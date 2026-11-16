// ---------- Modo claro e escuro ----------
const raiz = document.documentElement;
function rotuloTema() {
  document.querySelectorAll('[data-tema-alternar]').forEach(b => {
    b.textContent = raiz.dataset.tema === 'light' ? 'Modo escuro' : 'Modo claro';
  });
}
document.querySelectorAll('[data-tema-alternar]').forEach(b => b.addEventListener('click', () => {
  const novo = raiz.dataset.tema === 'light' ? 'dark' : 'light';
  raiz.dataset.tema = novo;
  try { localStorage.setItem('tema', novo); } catch (e) {}
  rotuloTema();
}));
rotuloTema();

// ---------- Tela cheia (útil quando o computador está ligado ao projetor) ----------
function alternarTelaCheia() {
  if (document.fullscreenElement) document.exitFullscreen();
  else document.documentElement.requestFullscreen().catch(() => {});
}
document.querySelectorAll('[data-tela-cheia]').forEach(b => b.addEventListener('click', alternarTelaCheia));

// ---------- Navegação por setas (teclado ou controle remoto) ----------
const player = document.getElementById('player');
if (!player) {
  document.addEventListener('keydown', e => {
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
    if (e.key === 'f' || e.key === 'F') { alternarTelaCheia(); return; }
    const dir = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key];
    if (!dir) return;
    const itens = [...document.querySelectorAll('[data-nav]')].filter(el => el.offsetParent !== null);
    const atual = document.activeElement && document.activeElement.matches('[data-nav]') ? document.activeElement : null;
    e.preventDefault();
    if (!atual) { const primeiro = itens.find(el => el.matches('.hero .btn, .grade .card, .card, .chip')) || itens[0]; primeiro && primeiro.focus(); return; }
    const r = atual.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    let melhor = null, menor = Infinity;
    for (const el of itens) {
      if (el === atual) continue;
      const b = el.getBoundingClientRect();
      const dx = b.left + b.width / 2 - cx, dy = b.top + b.height / 2 - cy;
      const frente = dx * dir[0] + dy * dir[1];
      if (frente <= 4) continue;
      const lado = Math.abs(dx * dir[1]) + Math.abs(dy * dir[0]);
      const nota = frente + lado * 2.5;
      if (nota < menor) { menor = nota; melhor = el; }
    }
    if (melhor) {
      melhor.focus({ preventScroll: true });
      melhor.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
    }
  });
}

// ---------- Player ----------
if (player) {
  const video = document.getElementById('video');
  const erro = document.getElementById('erro');
  const fim = document.getElementById('fim');
  const { salvar, csrf, retomar, voltar } = player.dataset;
  let ultimoSalvo = 0, idleTimer;

  function guardar(forcar) {
    if (!video.duration || isNaN(video.duration)) return;
    const agora = Date.now();
    if (!forcar && agora - ultimoSalvo < 5000) return;
    ultimoSalvo = agora;
    const dados = new FormData();
    dados.append('_csrf', csrf);
    dados.append('segundo', Math.floor(video.currentTime));
    dados.append('pct', Math.round(video.currentTime / video.duration * 100));
    fetch(salvar, { method: 'POST', body: dados, keepalive: true }).catch(() => {});
  }

  video.addEventListener('loadedmetadata', () => {
    const t = parseInt(retomar, 10) || 0;
    if (t > 0 && t < video.duration - 5) video.currentTime = t;
  });
  video.addEventListener('timeupdate', () => guardar(false));
  video.addEventListener('pause', () => guardar(true));
  video.addEventListener('ended', () => { guardar(true); fim.hidden = false; fim.querySelector('a').focus(); });
  video.addEventListener('error', () => { erro.hidden = false; });
  window.addEventListener('pagehide', () => guardar(true));

  // esconde os controles quando o mouse para
  function acordar() {
    player.classList.remove('idle');
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => { if (!video.paused) player.classList.add('idle'); }, 3000);
  }
  ['mousemove', 'keydown', 'click'].forEach(ev => document.addEventListener(ev, acordar));
  acordar();

  document.addEventListener('keydown', e => {
    if (!fim.hidden || !erro.hidden) return;
    const k = e.key;
    if (k === ' ' || k === 'k' || k === 'K') { e.preventDefault(); video.paused ? video.play() : video.pause(); }
    else if (k === 'ArrowRight') { e.preventDefault(); video.currentTime = Math.min(video.duration, video.currentTime + 10); }
    else if (k === 'ArrowLeft') { e.preventDefault(); video.currentTime = Math.max(0, video.currentTime - 10); }
    else if (k === 'ArrowUp') { e.preventDefault(); video.volume = Math.min(1, video.volume + 0.1); }
    else if (k === 'ArrowDown') { e.preventDefault(); video.volume = Math.max(0, video.volume - 0.1); }
    else if (k === 'f' || k === 'F') { document.fullscreenElement ? document.exitFullscreen() : video.requestFullscreen().catch(() => {}); }
    else if (k === 'm' || k === 'M') { video.muted = !video.muted; }
    else if (k === 'Escape' || k === 'Backspace') { if (!document.fullscreenElement) { guardar(true); location.href = voltar; } }
  });

  // se o navegador bloquear o autoplay, o usuário aperta play
  video.play().catch(() => {});
}
