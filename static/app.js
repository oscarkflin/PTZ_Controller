const $ = id => document.getElementById(id);
let presetNames = {};
let liveEnabled=false;
let commandQueue=Promise.resolve();
const clientId=Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
let commandOrder=0;
let token = '', held = null, timer = null, busy = false, ready = false;
const speed = () => Number($('speed').value);
const status = message => { $('status').textContent = message; };
async function post(path, data) {
  if (!ready) return;
  const response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json','X-PTZ-Token':token}, body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  status(result.event); return result;
}
async function send(data) {
  if(!liveEnabled) {status('Live control is OFF — turn it on to control the camera'); return;}
  const message={...data,client:clientId,order:++commandOrder};
  // Stop bypasses queued motion; the server rejects any older delayed requests.
  const request=data.action==='stop'?post('/api/command',message):commandQueue.then(()=>post('/api/command',message));
  commandQueue=request.catch(()=>{});
  try {return await request;}
  catch(error) {status(error.message); held=null; clearInterval(timer);}
}

function stop() {
  zoomPointer=null;
  held = null; clearInterval(timer);
  if($('stick')) $('stick').style.transform='translate(0px, 0px)';
  document.querySelectorAll('.active').forEach(button => button.classList.remove('active'));
  return send({action:'stop'});
}
async function pulse() {
  if (busy || !held) return;
  busy = true; await send({...held, speed:held.speed || speed()}); busy = false;
}
function start(data, button) {
  if (!ready || !liveEnabled || held) return;
  held = data; button?.classList.add('active'); pulse(); timer = setInterval(pulse, 180);
}
let zoomPointer=null;
document.querySelectorAll('[data-zoom]').forEach(button=>{
  button.addEventListener('pointerdown',event=>{
    if(!ready || !liveEnabled || held || zoomPointer!==null) return;
    event.preventDefault(); button.focus();
    zoomPointer=event.pointerId;
    button.setPointerCapture(event.pointerId);
    start({action:'zoom',direction:Number(button.dataset.zoom)},button);
  });
  const release=event=>{
    if(event.pointerId!==zoomPointer) return;
    zoomPointer=null; stop();
  };
  ['pointerup','pointercancel','lostpointercapture'].forEach(name=>button.addEventListener(name,release));
  button.addEventListener('keydown',event=>{
    if((event.code==='Space' || event.code==='Enter') && !event.repeat) {
      event.preventDefault(); start({action:'zoom',direction:Number(button.dataset.zoom)},button);
    }
  });
  button.addEventListener('keyup',event=>{
    if(event.code==='Space' || event.code==='Enter') {event.preventDefault(); stop();}
  });
  button.addEventListener('contextmenu',event=>event.preventDefault());
});
document.addEventListener('pointerup',()=>{if(held?.action==='zoom') stop();},true);
document.addEventListener('pointercancel',()=>{if(held?.action==='zoom') stop();},true);
$('speed').oninput = () => { $('speed-value').value = speed(); };
$('stop').onclick = () => {joystickPointer=null; zoomPointer=null; heldKey=null; return stop();};
const joystick = $('joystick');
let joystickPointer = null;
function positionStick(event) {
  const bounds = joystick.getBoundingClientRect();
  const radius = bounds.width / 2 - 43;
  let x = (event.clientX - bounds.left - bounds.width/2) / radius;
  let y = (event.clientY - bounds.top - bounds.height/2) / radius;
  const distance = Math.hypot(x,y);
  if(distance>1) {x/=distance; y/=distance;}
  $('stick').style.transform = `translate(${x*radius}px, ${y*radius}px)`;
  if(distance < .16) {
    if(held) stop();
    return;
  }
  const data = {action:'move',x:Math.abs(x)<.2?0:Math.sign(x),y:Math.abs(y)<.2?0:Math.sign(y),speed:Math.max(1,Math.round(Math.min(1,distance)*speed()))};
  if(held) held=data;
  else start(data);
}
joystick.addEventListener('pointerdown', event => {
  if(!ready || !liveEnabled || joystickPointer!==null || held) return;
  event.preventDefault(); joystick.focus(); joystickPointer=event.pointerId;
  joystick.setPointerCapture(event.pointerId); positionStick(event);
});
joystick.addEventListener('pointermove', event => {
  if(event.pointerId!==joystickPointer) return;
  if(event.pointerType==='mouse' && event.buttons===0) {releaseStick(event); return;}
  positionStick(event);
});
function releaseStick(event) {
  if(event && event.pointerId!==joystickPointer) return;
  joystickPointer=null; $('stick').style.transform='translate(0px, 0px)';
  stop();
}
['pointerup','pointercancel','lostpointercapture'].forEach(name=>joystick.addEventListener(name, event=>{if(joystickPointer!==null) releaseStick(event);}));
joystick.addEventListener('contextmenu',event=>event.preventDefault());
// Capture release anywhere, including outside the control or browser content area.
window.addEventListener('pointerup',event=>{if(event.pointerId===joystickPointer) releaseStick(event);},true);
window.addEventListener('pointercancel',event=>{if(event.pointerId===joystickPointer) releaseStick(event);},true);
window.addEventListener('blur',()=>{if(joystickPointer!==null) releaseStick();});
function presetLabel(i) {return presetNames[String(i)] || `Preset ${i+1}`;}
function renderPresets() {
  $('presets').replaceChildren();
  for(let i=0;i<6;i++) {
    const card=document.createElement('div'); card.className='preset-card';
    const button=document.createElement('button'); button.className='preset-recall';
    button.disabled=!liveEnabled; button.textContent=presetLabel(i); button.title=`Camera preset ${i+1}`;
    button.onclick=async()=>{
      const save=$('save-mode').checked;
      if(save && !confirm(`Replace “${presetLabel(i)}” with the current camera position?`)) return;
      $('save-mode').checked=false; if(held) await stop(); await send({action:save?'save':'recall',preset:i});
    };
    const rename=document.createElement('button'); rename.className='preset-rename'; rename.textContent='Rename';
    rename.setAttribute('aria-label',`Rename preset ${i+1}`);
    rename.onclick=async()=>{
      const name=prompt(`Name for preset ${i+1} (up to 40 characters):`,presetLabel(i));
      if(name===null) return;
      try {
        await post('/api/preset-name',{preset:i,name});
        presetNames[String(i)]=name.trim(); renderPresets();
      } catch(error) {status(error.message);}
    };
    card.append(button,rename); $('presets').append(card);
  }
}
renderPresets();
const keys = {ArrowUp:{action:'move',x:0,y:-1},ArrowDown:{action:'move',x:0,y:1},ArrowLeft:{action:'move',x:-1,y:0},ArrowRight:{action:'move',x:1,y:0},'+':{action:'zoom',direction:1},'=':{action:'zoom',direction:1},'-':{action:'zoom',direction:-1}};
let heldKey = null;
document.addEventListener('keydown', event => {
  if(/INPUT|SELECT|TEXTAREA|BUTTON/.test(event.target.tagName)) return;
  if(event.code==='Space') {event.preventDefault(); stop(); return;}
  if(keys[event.key]) {event.preventDefault(); if(!event.repeat && !held) {heldKey=event.key; start(keys[event.key]);}}
});
document.addEventListener('keyup', event => {if(event.key===heldKey) {heldKey=null; stop();}});
window.addEventListener('blur', () => {if(held) stop();});
document.addEventListener('visibilitychange', () => {if(document.hidden && held) stop();});
window.addEventListener('pagehide', () => {if(ready && liveEnabled) fetch('/api/command',{method:'POST',headers:{'Content-Type':'application/json','X-PTZ-Token':token},body:JSON.stringify({action:'stop',client:clientId,order:++commandOrder}),keepalive:true}).catch(()=>{});});
function showMode(config, connectionStatus, live) {
  liveEnabled=Boolean(live);
  $('live-toggle').checked=liveEnabled;
  document.querySelectorAll('[data-zoom], .preset-recall').forEach(button=>button.disabled=!liveEnabled);
  $('joystick').setAttribute('aria-disabled',String(!liveEnabled));
  $('live-description').textContent=liveEnabled?'ON · camera commands enabled':'OFF · camera commands blocked';
  $('badge').textContent=liveEnabled?'LIVE CONTROL ON':'LIVE CONTROL OFF';
  $('badge').dataset.state=liveEnabled?'responding':'unverified';
  $('connection-label').textContent=config.mode==='demo'?'Demo':config.host;
  for(const name of ['mode','host','port']) $(name).disabled=liveEnabled;
  if(!liveEnabled) {held=null; clearInterval(timer); $('stick').style.transform='translate(0px,0px)';}
}
$('settings').onsubmit=event=>event.preventDefault();
$('live-toggle').onchange=async()=>{
  const enabled=$('live-toggle').checked;
  $('live-toggle').disabled=true;
  $('live-description').textContent=enabled?'Enabling camera commands…':'Stopping and disabling…';
  try {
    if(enabled) {
      const config={mode:$('mode').value,host:$('host').value.trim(),port:Number($('port').value),framing:'sony'};
      await post('/api/config',config);
    }
    held=null; clearInterval(timer);
    const result=await post('/api/live',{enabled});
    showMode({mode:$('mode').value,host:$('host').value},result.connection_status,result.live);
  } catch(error) {
    // Re-read authoritative state, including failures while stopping.
    try {await refreshState();} catch(_) {}
    status(error.message);
  } finally {$('live-toggle').disabled=false;}
};
async function refreshState() {
  const response=await fetch('/api/state');
  if(!response.ok) throw new Error('Cannot reach local service');
  const data=await response.json();
  showMode(data.config,data.connection_status,data.live);
  return data;
}
// Live control is shared by Mac and iPad. The server also rejects commands while off.
setInterval(()=>{if(ready && !$('live-toggle').disabled) refreshState().catch(()=>{liveEnabled=false; held=null; clearInterval(timer); $('badge').textContent='SERVICE UNAVAILABLE';});},2000);
fetch('/api/state').then(response=>response.json()).then(data=>{
  token=data.token; ready=true;
  for(const name of ['mode','host','port']) $(name).value=data.config[name];
  presetNames=data.preset_names || {}; renderPresets();
  showMode(data.config,data.connection_status,data.live); status(data.event);
}).catch(()=>status('Cannot reach the local service. Start PTZ Local and reload.'));
