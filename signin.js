// Shared sign-in logic for Frank's QR pages (home search, listing help).
// Each page sets <body data-form="..."> and marks every question with data-q="Label".
(function(){
var RELAY='https://lucido-signin.frankjr.workers.dev/';
var $=function(id){return document.getElementById(id)};
var form=document.body.getAttribute('data-form');

// Tap-to-choose buttons: one answer per group, or several when the group has data-multi.
document.addEventListener('click',function(e){
  var b=e.target.closest('.ch button'); if(!b) return;
  var g=b.parentNode;
  if(g.hasAttribute('data-multi')) b.classList.toggle('on');
  else [].forEach.call(g.querySelectorAll('button'),function(x){x.classList.toggle('on',x===b)});
});

function answerOf(q){
  var g=q.querySelector('.ch');
  if(g) return [].map.call(g.querySelectorAll('button.on'),function(b){return b.textContent.trim()}).join(', ');
  return [].map.call(q.querySelectorAll('input,select,textarea'),function(el){return el.value.trim()}).filter(Boolean).join(' to ');
}

$('go').addEventListener('click',function(){
  var name=$('name').value.trim(),phone=$('phone').value.trim(),email=$('email').value.trim(),err=$('err');
  if(!name){err.textContent='Please add your name.';$('name').focus();return}
  if(!phone&&!email){err.textContent='Please add a cell phone or an email.';$('phone').focus();return}
  if(!$('consent').checked){err.textContent='Please check the box so Frank can follow up with you.';return}
  err.textContent='';
  var answers=[].map.call(document.querySelectorAll('[data-q]'),function(q){return [q.getAttribute('data-q'),answerOf(q)]}).filter(function(a){return a[1]});
  var nm=name.split(/\s+/), val=function(id){return $(id)?$(id).value.trim():''};
  var payload={form:form,firstName:nm[0],lastName:nm.slice(1).join(' '),phone:phone,email:email,consent:true,website:$('website').value,
    answers:answers,street:val('street'),city:val('city'),state:'MI'};
  var body=[document.title.split(' · ')[0],'Name: '+name,'Cell: '+phone,'Email: '+email].concat(answers.map(function(a){return a[0]+': '+a[1]})).join('\n');
  function finish(sent){
    $('ty').textContent='Thank you, '+nm[0]+'!';
    $('sms').href='sms:+15864197607?&body='+encodeURIComponent(body);
    $('mail').href='mailto:frankjr@fjlucido.com?subject='+encodeURIComponent(document.title.split(' · ')[0])+'&body='+encodeURIComponent(body);
    $('fallback').hidden=sent;$('form').hidden=true;$('done').hidden=false;window.scrollTo(0,0);
  }
  var go=$('go'),label=go.textContent;go.disabled=true;go.textContent='Sending...';
  var ctl=window.AbortController?new AbortController():null,t=setTimeout(function(){if(ctl)ctl.abort()},12000);
  fetch(RELAY,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:ctl?ctl.signal:undefined})
    .then(function(r){return r.json().then(function(j){return {s:r.status,j:j}})})
    .then(function(o){clearTimeout(t);
      if(o.j&&o.j.ok){finish(true);return}
      if(o.s===400&&o.j&&o.j.error){go.disabled=false;go.textContent=label;err.textContent=o.j.error;return}
      finish(false)})
    .catch(function(){clearTimeout(t);finish(false)});
});
})();
