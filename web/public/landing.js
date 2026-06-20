// Build column guides for each spread
document.querySelectorAll('[id^=cols-]').forEach(function(el){
  var n = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--cols').trim()) || 12;
  for(var i=0;i<n;i++){
    var d=document.createElement('div');
    d.className='col';
    var s=document.createElement('span');
    s.textContent=i+1;
    d.appendChild(s);
    el.appendChild(d);
  }
});

// Toggle
var btn=document.getElementById('gtoggle');
btn.addEventListener('click',function(){document.body.classList.toggle('grid-on');});
document.addEventListener('keydown',function(e){if(e.key==='g'||e.key==='G') document.body.classList.toggle('grid-on');});

// Optical alignment — shift display type so INK lands on column line
document.fonts.ready.then(function(){
  alignInk();
  window.addEventListener('resize',alignInk);
});
function alignInk(){
  var cvs=document.createElement('canvas');
  var ctx=cvs.getContext('2d');
  document.querySelectorAll('.masthead-js,.numeral-js,.cta-js').forEach(function(el){
    el.style.marginLeft='0px';
    var cs=getComputedStyle(el);
    var ch=(el.textContent||'').trim()[0];
    if(!ch) return;
    if(cs.textTransform==='uppercase') ch=ch.toUpperCase();
    ctx.font=cs.fontStyle+' '+cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;
    ctx.textAlign='left';
    var m=ctx.measureText(ch);
    var abl=m.actualBoundingBoxLeft;
    if(isFinite(abl)) el.style.marginLeft=abl.toFixed(2)+'px';
  });
}


// Fetch and display version in footer
fetch('/api/version')
  .then(r => r.json())
  .then(data => {
    const el = document.getElementById('version-text');
    if (el) el.textContent = `v${data.version} · bolao.bigbase.click`;
  })
  .catch(() => {
    // Fallback if API fails
    const el = document.getElementById('version-text');
    if (el) el.textContent = 'bolao.bigbase.click';
  });
