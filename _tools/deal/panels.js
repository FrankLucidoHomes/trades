/* ---- One template for every deal: core steps + add-ons, set up by tap-to-answer questions ---- */
const LIB=JSON.parse(document.getElementById('lib').textContent||'{}');let qOpen=false,wcOpen=false;
const firstShort=()=>String(D.first||'').replace(/ and /g,' & ');
function titleName(){const a=(D.answers||{}).title;if(a&&a!=='other')return a;const t=(D.terms||[]).find(x=>/^title company/i.test(x[0]));return t?String(t[1]).split(/[(,;]/)[0].trim():'the title company'}
const fill=x=>String(x||'').replace(/\{first\}/g,firstShort()).replace(/\{title\}/g,titleName());
function relOf(r){return r[0]==='insp'?['accepted','insp',r[1]||0]:[r[0],r[1]]}
function dateOf(r){const R=relOf(r);return addDays(D[R[0]],(R[1]==='insp'?(Number(D.inspDays)||7):R[1])+(Number(R[2])||0))}
/* switch an add-on on: its steps join the list in date order (steps already there keep their wording, dates and notes) */
function ensurePack(key){const p=(LIB.addons||[]).find(a=>a.key===key);if(!p)return 0;const a=M('steps');const rel=M('rel');let n=0;
  p.steps.forEach(x=>{const have=a.find(s=>s.id===x.id);if(have){if(!have.pack)have.pack=key;return}
    const s={id:x.id,t:fill(x.t),who:fill(x.who),what:fill(x.what),d:dateOf(x.rel),pack:key};rel[x.id]=relOf(x.rel);
    const i=a.findIndex(y=>!y.agent&&y.d&&s.d&&y.d>s.d&&y.id!=='accept');if(i<0){const j=a.findIndex(y=>y.agent);if(j<0)a.push(s);else a.splice(j,0,s)}else a.splice(i,0,s);n++});return n}
function setAddon(key,on){st.data=st.data||{};const A=Object.assign({},D.addons||{});if(on)A[key]=true;else delete A[key];st.data.addons=A;applyData();if(on)ensurePack(key);applyData()}
function setTerm(label,val){const T=M('terms');const i=T.findIndex(t=>(t[0]||'').toLowerCase()===label.toLowerCase());if(i>-1)T[i][1]=val;else T.push([label,val])}
const YN=[['yes','Yes'],['no','No']];
function QS(){const cityGuess=/grosse pointe farms/i.test(D.city||'');return [
  {k:'pay',q:'How are they paying?',o:[['cash','Cash'],['fin','Financing'],['tbd','Not decided yet']]},
  {k:'condo',q:'Is it a condo?',o:YN},
  {k:'pre78',q:'Built before 1978?',o:YN},
  {k:'cofo',q:'City C of O / city inspection needed?'+(cityGuess?' (Grosse Pointe Farms usually does)':''),o:YN},
  {k:'sale',q:'Do they have to sell a home first?',o:YN},
  {k:'poss',q:'Possession',o:[['close','At closing'],['stay','Sellers stay after closing'],['early','Early possession']]},
  {k:'insp',q:'Inspection period',o:[['5','5 days'],['7','7 days'],['10','10 days'],['14','14 days']]},
  {k:'close',q:'Closing date',date:1},
  {k:'title',q:'Title company',o:(LIB.titles||[]).map(x=>[x,x]).concat([['other','Other (type it in The deal)']])},
  {k:'repairs',q:'Repairs or a credit from the inspection?',o:[['yes','Yes'],['no','No'],['tbd','Not yet']]},
  {k:'warranty',q:'Home warranty?',o:YN},
  {k:'survey',q:'Survey?',o:YN}]}
/* what each question's answer looks like right now (from the deal itself when he hasn't answered yet) */
function cur(k){const A=D.answers||{},O=D.addons||{};if(A[k]!=null)return String(A[k]);
  const fin=((D.terms||[]).find(t=>/^financing/i.test(t[0]))||[])[1]||'';
  switch(k){case 'pay':return /deciding|undecided|or financ/i.test(fin)?'tbd':/cash/i.test(fin)?'cash':fin?'fin':'';
    case 'condo':return O.condo?'yes':'';case 'pre78':return O.lead?'yes':'';case 'cofo':return O.cofo?'yes':'';case 'sale':return O.sale?'yes':'';
    case 'poss':return O.occupancy?'stay':O.early?'early':'';case 'insp':return String(D.inspDays||'');case 'close':return D.close||'';
    case 'repairs':return O.repairs?'yes':'';case 'warranty':return O.warranty?'yes':'';case 'survey':return O.survey?'yes':'';case 'title':return '';}return ''}
function answer(k,v){st.data=st.data||{};st.data.answers=Object.assign({},D.answers||{},{[k]:v});applyData();let moved=[];
  if(k==='pay'){setAddon('financing',v==='fin');setTerm('Financing',v==='cash'?'Cash':v==='fin'?'Financing':'Cash or financing (still deciding)')}
  else if(k==='condo')setAddon('condo',v==='yes');else if(k==='pre78')setAddon('lead',v==='yes');else if(k==='cofo')setAddon('cofo',v==='yes');else if(k==='sale')setAddon('sale',v==='yes');
  else if(k==='poss'){setAddon('occupancy',v==='stay');setAddon('early',v==='early');if(v==='close')setTerm('Possession','At closing')}
  else if(k==='insp'){st.data.inspDays=Number(v);applyData();moved=redate()}
  else if(k==='close'){st.data.close=v;applyData();moved=redate()}
  else if(k==='title'&&v!=='other'){setTerm('Title company',v)}
  else if(k==='repairs')setAddon('repairs',v==='yes');else if(k==='warranty')setAddon('warranty',v==='yes');else if(k==='survey')setAddon('survey',v==='yes');
  changed();toast('Saved ✓'+(moved.length?' Dates moved: '+moved.slice(0,3).join('; ')+(moved.length>3?' and '+(moved.length-3)+' more':''):''))}
function renderQs(){const Q=QS();let h='<h3>Answer a few questions</h3><p class="small">Tap an answer and the tracker builds itself: the right steps switch on, dates follow the contract, and it saves right away. Change any answer later the same way.</p>';
  h+=Q.map(q=>{const c=cur(q.k);return '<div class="qrow"><b>'+esc(q.q)+'</b><div class="chips">'+(q.date?'<label class="chip on">'+'<input type="date" data-qdate="'+q.k+'" value="'+esc(c)+'"></label>':q.o.map(o=>'<button type="button" class="chip'+(o[0]===c?' on':'')+'" data-q="'+q.k+'" data-a="'+esc(o[0])+'">'+esc(o[1])+'</button>').join(''))+'</div></div>'}).join('');
  const O=D.addons||{};
  h+='<div class="qrow"><b>Add-ons on this deal</b><span class="small">The questions above switch these on for you; you can also flip any one here. Turning one off hides its steps but keeps your notes.</span>'+(LIB.addons||[]).map(a=>'<label class="addon"><input type="checkbox" data-addon="'+a.key+'"'+(O[a.key]?' checked':'')+'><span><b>'+esc(a.label)+'</b><span class="small">'+esc(a.desc)+'</span></span></label>').join('')+'<div class="chips" style="margin-top:8px"><button type="button" class="chip" data-custom="1">+ Custom item</button></div></div>';
  $('qsec').innerHTML=h}
/* What changed? the next open steps with one-tap answers */
function renderWc(){const open=D.steps.filter(s=>packOn(s)).filter(s=>!['Done','N/A'].includes(stepOf(s).status)).slice(0,8);
  let h='<h3>What changed?</h3><p class="small">The next open steps. Tap what happened; it saves right away. Pick a new date if one moved.</p>';
  h+=open.length?open.map(s=>{const o=stepOf(s);return '<div class="qrow"><b>'+esc(s.t)+(s.agent?' <span class="agentonly">only you</span>':'')+'</b><span class="small">'+(o.d?'Due '+esc(fmt(o.d))+' · ':'')+esc(o.status)+'</span><div class="chips" style="margin-top:6px">'+[['Done','Done ✓'],['Scheduled','Scheduled'],['Waiting','Waiting'],['N/A','Not needed']].map(x=>'<button type="button" class="chip'+(o.status===x[0]?' on':'')+'" data-wc="'+s.id+'" data-st="'+x[0]+'">'+x[1]+'</button>').join('')+'<label class="chip">New date <input type="date" data-k="d" data-id="'+s.id+'" value="'+esc(o.d)+'"></label></div></div>'}).join(''):'<p><b>Everything is done.</b></p>';
  $('wcsec').innerHTML=h}
document.addEventListener('click',e=>{const t=e.target.closest&&e.target.closest('button');if(!t||MODE!=='agent')return;
  if(t.id==='mQs'){qOpen=!qOpen;wcOpen=false;render();if(qOpen)$('qsec').scrollIntoView({behavior:'smooth',block:'start'})}
  else if(t.id==='mWc'){wcOpen=!wcOpen;qOpen=false;render();if(wcOpen)$('wcsec').scrollIntoView({behavior:'smooth',block:'start'})}
  else if(t.dataset.q){answer(t.dataset.q,t.dataset.a)}
  else if(t.dataset.wc){const o=st.steps[t.dataset.wc]=Object.assign({},st.steps[t.dataset.wc]||{});o.status=t.dataset.st;render();save();toast('Saved ✓')}
  else if(t.dataset.custom){M('steps').push({id:'x'+Date.now().toString(36),t:'New item',who:'Frank',what:'',d:''});qOpen=false;changed();toast('Added at the end of the steps. Type its name and details right in the list.');const l=$('steps').lastElementChild;if(l)l.scrollIntoView({behavior:'smooth',block:'center'})}},false);
document.addEventListener('change',e=>{const t=e.target;if(MODE!=='agent'||!t.dataset)return;
  if(t.dataset.addon){setAddon(t.dataset.addon,t.checked);changed();toast(t.checked?'Add-on on: its steps are in the list ✓':'Add-on off: its steps are hidden ✓')}
  else if(t.dataset.qdate&&t.value&&+t.value.slice(0,4)>=2020){answer(t.dataset.qdate,t.value)}},true);
