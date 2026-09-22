const $=s=>document.querySelector(s);let users=[];
async function api(path,options={}){const r=await fetch(path,{credentials:'same-origin',headers:{'Content-Type':'application/json',...(options.headers||{})},...options});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||'Não foi possível concluir.');return d}
function notice(msg){const n=$('#notice');n.textContent=msg;n.classList.add('show');clearTimeout(window.noticeTimer);window.noticeTimer=setTimeout(()=>n.classList.remove('show'),3200)}
function formatDate(iso){if(!iso)return'—';try{return new Intl.DateTimeFormat('pt-BR',{day:'2-digit',month:'2-digit',year:'numeric'}).format(new Date(iso))}catch{return iso}}
function showPanel(){ $('#login-view').classList.add('hidden');$('#admin-view').classList.remove('hidden');loadUsers() }
function renderUsers(){
 $('#user-count').textContent=users.length;const select=$('#user-id');select.innerHTML='<option value="">Selecione um usuário</option>'+users.map(u=>`<option value="${u.id}">${u.name} · ${u.email}</option>`).join('');
 $('#users').innerHTML=users.length?users.map(u=>{const status=u.status==='active'?`Ativo até ${formatDate(u.expires_at)}`:u.status==='revoked'?'Revogado':'Sem plano';return`<div class="user-row"><div><div class="user-name">${u.name}</div><div class="user-email">${u.email}</div></div><span class="user-status ${u.status||''}">${status}</span></div>`}).join(''):'<p class="muted">Nenhum usuário cadastrado ainda.</p>';
}
async function loadUsers(){try{const d=await api('/api/admin/users');users=d.users;renderUsers()}catch(e){notice(e.message)}}
$('#admin-login').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/login',{method:'POST',body:JSON.stringify(Object.fromEntries(f.entries()))});showPanel()}catch(err){notice(err.message)}});
$('#release-form').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/subscriptions',{method:'POST',body:JSON.stringify(Object.fromEntries(f.entries()))});notice('Plano liberado com sucesso.');e.target.reset();await loadUsers()}catch(err){notice(err.message)}});
$('#refresh').addEventListener('click',loadUsers);$('#logout').addEventListener('click',async()=>{await api('/api/admin/logout',{method:'POST'});location.reload()});
(async()=>{try{const d=await api('/api/admin/me');if(d.authenticated)showPanel()}catch{}})();
