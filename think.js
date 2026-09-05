'use strict';
const fields = ['question','observations','constraints','alternatives','prediction','test'];
const titles = ['Question','Observations and sources','Constraints and assumptions','Competing explanations','Different predictions','Next test'];
const question = new URLSearchParams(location.search).get('question');
if(question) document.getElementById('question').value = question;
document.getElementById('notebook').addEventListener('submit',e=>e.preventDefault());
document.getElementById('download').addEventListener('click',()=>{
  const text = '# First-principles notebook\n\n' + fields.map((id,i)=>`## ${titles[i]}\n\n${document.getElementById(id).value.trim() || '(Not yet recorded)'}\n`).join('\n');
  const url = URL.createObjectURL(new Blob([text],{type:'text/markdown;charset=utf-8'}));
  const a = document.createElement('a'); a.href=url; a.download='first-principles-notes.md';
  document.body.append(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(url),1000);
  document.getElementById('status').textContent='Notes prepared for download. Keep the downloaded file before closing this page.';
});
