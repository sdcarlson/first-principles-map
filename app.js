'use strict';
const $ = id => document.getElementById(id);
const label = kind => kind.replaceAll('-', ' ');
let graph, pathId, selectedId;
function element(tag, text, className) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (className) e.className = className;
  return e;
}
function badge(node) {
  const e = element('span', label(node.kind), 'badge');
  e.style.setProperty('--node-color', `var(--${node.kind})`);
  return e;
}
function sourceLink(id) {
  const s = graph.sources.find(s => s.id === id);
  const a = element('a', s.title);
  a.href = s.url; a.target = '_blank'; a.rel = 'noopener noreferrer';
  return a;
}
function route() {
  const params = new URLSearchParams(location.hash.slice(1));
  const candidate = params.get('path');
  pathId = candidate === 'all' || graph.paths.some(p => p.id === candidate) ? candidate : graph.paths[0].id;
  const ids = pathId === 'all' ? graph.nodes.map(n => n.id) : graph.paths.find(p => p.id === pathId).nodes;
  selectedId = ids.includes(params.get('node')) ? params.get('node') : ids[0];
  $('search').value = ''; $('kind').value = '';
  render();
}
function navigate(path, node) {
  const hash = new URLSearchParams({path, ...(node ? {node} : {})}).toString();
  if (location.hash.slice(1) === hash) route();
  else location.hash = hash;
}
function selectNode(id) {
  selectedId = id;
  history.replaceState(null, '', '#' + new URLSearchParams({path:pathId,node:id}));
  renderCards(); renderDetail();
}
function render() {
  $('detail').hidden = false;
  const path = graph.paths.find(p => p.id === pathId);
  $('topic').textContent = path ? path.subtitle.toUpperCase() : 'THE COMPLETE MAP';
  $('title').textContent = path ? path.title : 'Find a claim. Follow its evidence.';
  $('intro').textContent = path ? path.intro : 'Search across every question. Open an idea to inspect its sources, limits and connections.';
  document.querySelectorAll('[data-path]').forEach(b => b.setAttribute('aria-current', String(b.dataset.path === pathId)));
  $('browse').setAttribute('aria-pressed', String(pathId === 'all'));
  $('takeaway').replaceChildren(); $('takeaway').hidden = !path;
  if (path) $('takeaway').append(element('strong', 'THE DISTINCTION TO KEEP'), element('p', path.takeaway));
  renderCards(); renderDetail();
}
function visibleNodes() {
  const path = graph.paths.find(p => p.id === pathId);
  const nodes = path ? path.nodes.map(id => graph.nodes.find(n => n.id === id)) : graph.nodes;
  const query = $('search').value.trim().toLowerCase();
  return nodes.filter(n => (!$('kind').value || n.kind === $('kind').value) &&
    [n.label,n.claim,n.scope,n.limits,n.question,n.domain,...(n.assumptions || [])].join(' ').toLowerCase().includes(query));
}
function renderCards() {
  const nodes = visibleNodes();
  $('cards').replaceChildren();
  $('count').textContent = `${nodes.length} ${nodes.length === 1 ? 'idea' : 'ideas'} · ${pathId === 'all' ? 'Across all questions' : 'A reading path, not a chain of deductions'}`;
  $('empty').hidden = nodes.length > 0;
  for (const n of nodes) {
    const b = element('button', undefined, 'node-card'); b.type = 'button';
    b.style.setProperty('--node-color', `var(--${n.kind})`);
    b.setAttribute('aria-pressed', String(n.id === selectedId));
    b.setAttribute('aria-controls','detail');
    b.append(badge(n),element('span',n.label,'node-title'),element('span',`${n.domain} · Open evidence ↓`,'step'));
    b.addEventListener('click', () => {
      selectNode(n.id);
      // Re-rendering the cards must not strand keyboard focus on the document.
      const replacement = [...$('cards').children].find(c => c.getAttribute('aria-pressed') === 'true');
      replacement?.focus({preventScroll:true});
    });
    $('cards').append(b);
  }
}
function section(title, content) {
  const s = element('section'); s.append(element('h3',title),element('p',content)); return s;
}
function renderDetail() {
  const n = graph.nodes.find(n => n.id === selectedId);
  const panel = $('detail'); panel.replaceChildren();
  panel.append(badge(n),element('h2',n.label),element('p',n.claim,'claim'));
  const grid = element('div',undefined,'detail-grid'), left = element('div'), right = element('div');
  left.append(section('Where this applies',n.scope),section('What this does not establish',n.limits));
  if (n.assumptions) {
    const s = element('section'); const list = element('ul');
    n.assumptions.forEach(a => list.append(element('li',a)));
    s.append(element('h3','Assumptions'),list); left.append(s);
  }
  const prompt = element('div',undefined,'prompt');
  const think = element('a','Work through this question ↗'); think.href = 'think.html?' + new URLSearchParams({question:n.question});
  prompt.append(element('h3','Think it through'),element('p',n.question),think); left.append(prompt);
  const connections = element('section'); connections.append(element('h3','Actual connections'));
  const list = element('div',undefined,'connections');
  graph.edges.filter(e => e.src === n.id || e.dst === n.id).forEach(e => {
    const other = graph.nodes.find(x => x.id === (e.src === n.id ? e.dst : e.src));
    const row = element('div',undefined,'connection');
    const relation = e.src === n.id ? `This idea ${graph.edge_types[e.type]} →` : `← ${graph.edge_types[e.type]} this idea`;
    row.append(element('div',relation,'relation'));
    const b = element('button',other.label); b.type = 'button';
    b.addEventListener('click', () => {
      const currentPath = graph.paths.find(p => p.id === pathId);
      const destination = currentPath?.nodes.includes(other.id) || pathId === 'all' ? pathId : graph.paths.find(p => p.nodes.includes(other.id)).id;
      navigate(destination, other.id);
    });
    row.append(b,element('p',e.explanation));
    const refs = element('div',undefined,'muted');
    e.sources.forEach((id,i) => { if(i) refs.append(document.createTextNode(' · ')); const a = sourceLink(id); a.textContent = graph.sources.find(s=>s.id===id).author; refs.append(a); });
    row.append(refs); list.append(row);
  });
  connections.append(list); right.append(connections);
  const sources = element('section'); sources.append(element('h3','Sources for this claim'));
  const refs = element('ul',undefined,'source-list');
  n.sources.forEach(ref => {
    const source = graph.sources.find(s => s.id === ref.id);
    const li = element('li'); li.append(sourceLink(ref.id),element('small',`${source.author} · ${source.type}`),element('p',ref.supports)); refs.append(li);
  });
  sources.append(refs); right.append(sources); grid.append(left,right); panel.append(grid);
}
fetch('graph.json').then(r => {if(!r.ok) throw new Error('Map unavailable'); return r.json();}).then(g => {
  graph = g;
  for(const p of g.paths) {
    const b = element('button',undefined,'path'); b.type='button'; b.dataset.path=p.id;
    b.append(element('span',p.subtitle),document.createTextNode(p.title));
    b.addEventListener('click',()=>navigate(p.id)); $('paths').append(b);
  }
  Object.entries(g.kinds).forEach(([kind,description]) => {
    const option = element('option',label(kind)); option.value=kind; $('kind').append(option);
    const p = element('p'); p.append(badge({kind}),document.createTextNode(description)); $('legend').append(p);
  });
  $('editorial').textContent = `${g.editorial_note} Content reviewed ${g.reviewed}.`;
  $('browse').addEventListener('click',()=>navigate('all'));
  for (const id of ['search','kind']) $(id).addEventListener(id==='search'?'input':'change',()=>{
    const nodes = visibleNodes();
    if(nodes.length && !nodes.some(n => n.id === selectedId)) selectNode(nodes[0].id);
    else renderCards();
    $('detail').hidden = !nodes.length;
  });
  window.addEventListener('hashchange',()=>{ $('detail').hidden=false; route(); });
  $('explorer').hidden=false; route();
}).catch(error => { console.error(error); $('error').hidden=false; $('intro').textContent='The map is temporarily unavailable.'; });
