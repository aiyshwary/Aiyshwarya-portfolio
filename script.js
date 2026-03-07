document.addEventListener('DOMContentLoaded', async () => {
  // highlight active nav link (adds `active` + aria-current)
  (function(){
    const current = (location.pathname || '').split('/').pop() || 'index.html';
    document.querySelectorAll('.site-header nav a').forEach(a => {
      const href = a.getAttribute('href');
      if(!href) return;
      if(href === current || (href === 'index.html' && current === '') || (href === '' && current === 'index.html')){
        a.classList.add('active');
        a.setAttribute('aria-current','page');
      }
    });
  })();

  // Basic skills (edit in the file)
  const skills = ['Python','Machine Learning','Computer Vision','Deep Learning','React','SQL'];
  const skillsEl = document.getElementById('skills-list');
  if(skillsEl){
    skills.forEach(s => { const d = document.createElement('div'); d.className='skill'; d.textContent = s; skillsEl.appendChild(d); });
  }

  // Choose a small set of featured projects (auto-selected)
  const featuredTitles = [
    'Hybrid Search & Retrieval Poc',
    'Video Rag Retrieval Project',
    'Synthetic Image Generation',
    'Annotation Transfer Tool',
    'Facial Emotion Recognition',
    'Object Detection Extension'
  ];

  // utility: clean extracted text for display
  function cleanText(str){
    if(!str) return '';
    return str.replace(/[●○✔■◆•►🔹]/g,' ').replace(/[\u2460-\u24FF]/g,' ').replace(/\s+/g,' ').trim();
  }
  function truncate(s, n=160){ return s.length>n ? s.slice(0,n).trim() + '…' : s; }

  // infer tags from title+summary using simple keyword heuristics
  function inferTags(title, summary){
    const text = (title + ' ' + summary).toLowerCase();
    const tags = new Set();
    const map = [
      ['object detection','Object Detection'],
      ['detection','Computer Vision'],
      ['facial','Computer Vision'],
      ['image','Computer Vision'],
      ['synthetic','Synthetic Data'],
      ['annotation','Annotation Tool'],
      ['faiss','Retrieval'],
      ['bm25','Retrieval'],
      ['retrieval','Retrieval'],
      ['video','Video'],
      ['rag','RAG'],
      ['sentiment','NLP'],
      ['hugging face','NLP'],
      ['event','Web App'],
      ['java','Java'],
      ['network','Analysis'],
      ['classification','Computer Vision'],
      ['ocr','OCR']
    ];
    map.forEach(([k,label]) => { if(text.includes(k)) tags.add(label); });
    if(tags.size === 0) tags.add('Other');
    return Array.from(tags);
  }

  // infer tech short names
  function inferTechs(text){
    const t = text.toLowerCase();
    const techs = new Set();
    const techMap = {
      'faiss':'FAISS','bm25':'BM25','opensearch':'OpenSearch','aws s3':'AWS S3','aws':'AWS','s3':'S3','hugging face':'Hugging Face','huggingface':'Hugging Face','rapidminer':'RapidMiner','tesseract':'Tesseract','python':'Python','java':'Java','hnsw':'HNSW','faiss':'FAISS'
    };
    Object.keys(techMap).forEach(k => { if(t.includes(k)) techs.add(techMap[k]); });
    return Array.from(techs);
  }

  // Load extracted projects and render cards (only when a projects grid exists on the page)
  try{
    const grid = document.getElementById('projects-grid');
    if(!grid) return; // nothing to do on other pages

    const basePath = (location.pathname || '').replace(/[^/]*$/, '');
    const absolutePath = location.origin + basePath + 'projects.json';
    const repoPath = location.origin + '/Aiyshwarya-portfolio/projects.json';
    let res = await fetch(absolutePath, { cache: 'no-store' });
    if(!res.ok){ res = await fetch(basePath + 'projects.json', { cache: 'no-store' }); }
    if(!res.ok){ res = await fetch('projects.json', { cache: 'no-store' }); }
    if(!res.ok){ res = await fetch(repoPath, { cache: 'no-store' }); }
    if(!res.ok){ throw new Error('projects.json not found'); }
    const projects = await res.json();
    grid.innerHTML = '';
    if(!projects.length){ grid.innerHTML = '<p>No projects found — check `projects.json`.</p>'; }

    // helper to create URL-safe slug from title
    function slugify(t){ return t.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,''); }
    function makeThumb(title, subtitle){
      const safe = (title || 'Project').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      const sub = (subtitle || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="480" viewBox="0 0 800 480">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0b1220" />
      <stop offset="100%" stop-color="#081226" />
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#06b6d4" />
      <stop offset="100%" stop-color="#7c3aed" />
    </linearGradient>
  </defs>
  <rect width="800" height="480" fill="url(#bg)" />
  <rect x="50" y="60" width="700" height="360" rx="18" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.06)" />
  <text x="80" y="170" font-family="Poppins, Arial, sans-serif" font-size="26" fill="#e6eef6" font-weight="600">${safe}</text>
  <text x="80" y="205" font-family="Poppins, Arial, sans-serif" font-size="14" fill="#9aa4b2">${sub}</text>
  <rect x="80" y="235" width="200" height="10" rx="5" fill="url(#accent)" opacity="0.9" />
  <rect x="80" y="260" width="320" height="10" rx="5" fill="rgba(255,255,255,0.12)" />
  <rect x="80" y="285" width="280" height="10" rx="5" fill="rgba(255,255,255,0.10)" />
</svg>`;
      return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
    }

    projects.forEach(p => {
      const tags = inferTags(p.title, p.summary);
      const inferred = inferTechs((p.title + ' ' + p.summary));
      const techs = (p.techs && p.techs.length) ? p.techs : inferred;
      const isFeatured = featuredTitles.includes(p.title);
      const brief = truncate(cleanText(p.summary), 180);
      const slug = slugify(p.title);

      const card = document.createElement('article');
      card.className = 'card';
      card.id = slug;
      card.setAttribute('data-tags', tags.join(','));
      if(isFeatured) card.setAttribute('data-featured','true');

      const techHtml = techs.map(t=>`<span class="tag tech">${t}</span>`).join(' ');
      const tagsHtml = tags.map(t=>`<span class="tag">${t}</span>`).join(' ');

      const summaryLine = truncate(cleanText(p.summary || ''), 72);
      const fallbackThumb = makeThumb(p.title, summaryLine);
      const thumb = p.thumbnail || fallbackThumb;
      const impact = p.impact ? p.impact : brief;

      card.innerHTML = `
        <img class="project-thumb" src="${thumb}" alt="${p.title} thumbnail" data-fallback="${fallbackThumb}" onerror="this.src=this.dataset.fallback">
        <div class="card-head">
          <h4>${p.title} ${isFeatured?'<span class="badge-featured">Featured</span>':''}</h4>
          <div class="meta">${techHtml}</div>
        </div>
        <p class="lead-card">${impact}</p>
        <div class="tags-row">${tagsHtml}</div>
        <div class="actions">
          <a class="btn-ghost" href="${p.pdf}" target="_blank" rel="noopener">Open PDF</a>
          <button class="btn-ghost btn-details">Details</button>
          <a class="btn" href="contact.html">Discuss</a>
          <a class="btn-ghost" href="projects.html#${slug}" style="margin-left:8px">Link</a>
        </div>
      `;

      // details modal
      card.querySelector('.btn-details').addEventListener('click', () => { location.hash = slug; openModal(p, tags, techs); });
      grid.appendChild(card);
    });

    // Filters
    const filterButtons = document.querySelectorAll('.filter');
    filterButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        filterButtons.forEach(b=>b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.dataset.filter;
        Array.from(grid.children).forEach(card => {
          if(filter === 'all'){ card.style.display = ''; return; }
          if(filter === 'featured'){ card.style.display = (card.dataset.featured === 'true') ? '' : 'none'; return; }
          const tags = (card.dataset.tags || '').toLowerCase();
          card.style.display = tags.includes(filter) ? '' : 'none';
        });
      });
    });

    // modal wiring
    const modal = document.getElementById('project-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalTechs = document.getElementById('modal-techs');
    const modalPdf = document.getElementById('modal-pdf');
    const modalClose = document.querySelector('.modal-close');
    if(modalClose) modalClose.addEventListener('click', closeModal);
    if(modal) modal.addEventListener('click', (e)=>{ if(e.target === modal) closeModal(); });
    document.addEventListener('keydown', (e)=>{ if(e.key === 'Escape') closeModal(); });

    function openModal(p, tags, techs){
      modalTitle.textContent = p.title;
      const techList = (p.techs && p.techs.length) ? p.techs : techs;
      modalTechs.textContent = (techList && techList.length) ? 'Tech: ' + techList.join(' · ') : 'Tags: ' + tags.join(' · ');

      const imgHtml = `<img class="modal-thumb" src="${thumb}" alt="${p.title}" data-fallback="${fallbackThumb}" onerror="this.src=this.dataset.fallback">`;
      const bullets = (p.bullets && p.bullets.length) ? `<ul class="project-bullets">${p.bullets.map(b=>`<li>${b}</li>`).join('')}</ul>` : `<pre class="project-full">${cleanText(p.summary)}</pre>`;

      modalBody.innerHTML = imgHtml + bullets + `<div style="margin-top:12px;color:var(--muted)">${cleanText(p.summary)}</div>`;
      modalPdf.href = p.pdf;
      modal.classList.add('open');
      modal.setAttribute('aria-hidden','false');
    }
    function closeModal(){
      modal.classList.remove('open');
      modal.setAttribute('aria-hidden','true');
      // clear hash without scrolling
      if(location.hash) history.replaceState(null, '', location.pathname + location.search);
    }

    // deep-link: open modal when page loads with #slug
    const hash = (location.hash || '').replace('#','');
    if(hash){
      const target = projects.find(x => slugify(x.title) === hash);
      if(target) openModal(target, inferTags(target.title, target.summary), target.techs || inferTechs(target.title + ' ' + target.summary));
    }

  }catch(err){
    console.error(err);
    const gridEl = document.getElementById('projects-grid');
    if(gridEl) gridEl.innerHTML = '<p>Unable to load projects.json. Please refresh or clear cache.</p>';
  }
});