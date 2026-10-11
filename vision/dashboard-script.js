
(() => {
if(new URLSearchParams(location.search).get('marker')==='blue') {
  document.title='SWARMFLOW · Blue calibration marker';
  const sheet=document.createElement('style');
  sheet.textContent='body{background:white;color:#123b8b;padding:0;margin:0} .marker-toolbar{font:14px system-ui;padding:12px} .marker-sheet{width:min(200mm,100%);margin:0 auto}.marker-sheet svg{display:block;width:100%;height:auto}@media print{.marker-toolbar{display:none}.marker-sheet{width:200mm;height:240mm;margin:0}.marker-sheet svg{width:200mm;height:240mm}}@page{size:A4;margin:5mm}';
  document.head.append(sheet);
  const svg=new TextDecoder().decode(Uint8Array.from(atob("PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDBtbSIgaGVpZ2h0PSIyNDBtbSIgdmlld0JveD0iMCAwIDIwMCAyNDAiPgo8cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI0MCIgZmlsbD0id2hpdGUiLz48ZyBmaWxsPSIjMTIzYjhiIj48cmVjdCB4PSIyMCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjQwIiB5PSIyMCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iNjAiIHk9IjIwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSI4MCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEwMCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEyMCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE0MCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE2MCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjIwIiB5PSI0MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iNDAiIHk9IjQwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSI2MCIgeT0iNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEwMCIgeT0iNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEyMCIgeT0iNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE0MCIgeT0iNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE2MCIgeT0iNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjIwIiB5PSI2MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iNDAiIHk9IjYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxMDAiIHk9IjYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxNDAiIHk9IjYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxNjAiIHk9IjYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIyMCIgeT0iODAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjQwIiB5PSI4MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iNjAiIHk9IjgwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSI4MCIgeT0iODAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEyMCIgeT0iODAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE2MCIgeT0iODAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjIwIiB5PSIxMDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjQwIiB5PSIxMDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjYwIiB5PSIxMDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjgwIiB5PSIxMDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE0MCIgeT0iMTAwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxNjAiIHk9IjEwMCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iMjAiIHk9IjEyMCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iNjAiIHk9IjEyMCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iMTQwIiB5PSIxMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE2MCIgeT0iMTIwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIyMCIgeT0iMTQwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSI2MCIgeT0iMTQwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxMDAiIHk9IjE0MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iMTYwIiB5PSIxNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjIwIiB5PSIxNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjQwIiB5PSIxNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjYwIiB5PSIxNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjgwIiB5PSIxNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEwMCIgeT0iMTYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxMjAiIHk9IjE2MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iMTQwIiB5PSIxNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE2MCIgeT0iMTYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48L2c+CjxnIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9ImJsYWNrIj4KPHRleHQgeD0iMTAwIiB5PSIxOTkiPlNXQVJNRkxPVyDCtyBBcHJpbFRhZyAzNmgxMSDCtyBJRCAwPC90ZXh0Pgo8dGV4dCB4PSIxMDAiIHk9IjIwNyI+UHJpbnQgYXQgMTAwJSAvIGFjdHVhbCBzaXplLiBCbHVlIG91dGVyIHNxdWFyZSA9IDE2MCBtbS48L3RleHQ+Cjx0ZXh0IHg9IjEwMCIgeT0iMjE1Ij5WZXJpZnkgdGhlIGJsdWUgZWRnZSB3aXRoIGEgcnVsZXIgYmVmb3JlIGNhbGlicmF0aW5nLjwvdGV4dD4KPHRleHQgeD0iMTAwIiB5PSIyMjMiPlBsYWNlIEZMQVQgb24gdGhlIHNhbWUgZ3JvdW5kIHBsYW5lIGFzIHRoZSB0cmFja2VkIGZlZXQuPC90ZXh0Pgo8dGV4dCB4PSIxMDAiIHk9IjIzMSI+S2VlcCB0aGUgY2FtZXJhIGZpeGVkIGFmdGVyIGNhbGlicmF0aW9uLjwvdGV4dD48L2c+PC9zdmc+"), c=>c.charCodeAt(0)));
  document.body.innerHTML='<div class="marker-toolbar"><a href="/">Back to dashboard</a> · <a id="blue-svg-download" download="calibration-marker-blue.svg" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDBtbSIgaGVpZ2h0PSIyNDBtbSIgdmlld0JveD0iMCAwIDIwMCAyNDAiPgo8cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI0MCIgZmlsbD0id2hpdGUiLz48ZyBmaWxsPSIjMTIzYjhiIj48cmVjdCB4PSIyMCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjQwIiB5PSIyMCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iNjAiIHk9IjIwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSI4MCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEwMCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEyMCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE0MCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE2MCIgeT0iMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjIwIiB5PSI0MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iNDAiIHk9IjQwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSI2MCIgeT0iNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEwMCIgeT0iNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEyMCIgeT0iNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE0MCIgeT0iNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE2MCIgeT0iNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjIwIiB5PSI2MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iNDAiIHk9IjYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxMDAiIHk9IjYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxNDAiIHk9IjYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxNjAiIHk9IjYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIyMCIgeT0iODAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjQwIiB5PSI4MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iNjAiIHk9IjgwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSI4MCIgeT0iODAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEyMCIgeT0iODAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE2MCIgeT0iODAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjIwIiB5PSIxMDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjQwIiB5PSIxMDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjYwIiB5PSIxMDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjgwIiB5PSIxMDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE0MCIgeT0iMTAwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxNjAiIHk9IjEwMCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iMjAiIHk9IjEyMCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iNjAiIHk9IjEyMCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iMTQwIiB5PSIxMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE2MCIgeT0iMTIwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIyMCIgeT0iMTQwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSI2MCIgeT0iMTQwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxMDAiIHk9IjE0MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iMTYwIiB5PSIxNDAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjIwIiB5PSIxNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjQwIiB5PSIxNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjYwIiB5PSIxNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjgwIiB5PSIxNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjEwMCIgeT0iMTYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48cmVjdCB4PSIxMjAiIHk9IjE2MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIi8+PHJlY3QgeD0iMTQwIiB5PSIxNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIvPjxyZWN0IHg9IjE2MCIgeT0iMTYwIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiLz48L2c+CjxnIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9ImJsYWNrIj4KPHRleHQgeD0iMTAwIiB5PSIxOTkiPlNXQVJNRkxPVyDCtyBBcHJpbFRhZyAzNmgxMSDCtyBJRCAwPC90ZXh0Pgo8dGV4dCB4PSIxMDAiIHk9IjIwNyI+UHJpbnQgYXQgMTAwJSAvIGFjdHVhbCBzaXplLiBCbHVlIG91dGVyIHNxdWFyZSA9IDE2MCBtbS48L3RleHQ+Cjx0ZXh0IHg9IjEwMCIgeT0iMjE1Ij5WZXJpZnkgdGhlIGJsdWUgZWRnZSB3aXRoIGEgcnVsZXIgYmVmb3JlIGNhbGlicmF0aW5nLjwvdGV4dD4KPHRleHQgeD0iMTAwIiB5PSIyMjMiPlBsYWNlIEZMQVQgb24gdGhlIHNhbWUgZ3JvdW5kIHBsYW5lIGFzIHRoZSB0cmFja2VkIGZlZXQuPC90ZXh0Pgo8dGV4dCB4PSIxMDAiIHk9IjIzMSI+S2VlcCB0aGUgY2FtZXJhIGZpeGVkIGFmdGVyIGNhbGlicmF0aW9uLjwvdGV4dD48L2c+PC9zdmc+">Download blue marker</a> · Print at 100% / actual size. Outer square: 16 × 16 cm.</div><div class="marker-sheet"></div>';
  document.querySelector('.marker-sheet').innerHTML=svg;
  return;
}

const EGG = location.hostname;
let ws;
function connect(){
  ws = new WebSocket(`${location.protocol==='https:'?'wss:':'ws:'}//${location.host}/ws`);
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if(d.error){el("error").textContent=d.error;return;}
    const st = document.getElementById('status');
    st.textContent = d.mcu_ok ? 'MCU live' : `MCU DOWN (${d.mcu_age_s}s) ${d.err||''}`;
    st.className = d.mcu_ok ? 'ok' : 'bad';
    renderBrightness(d);
    renderEffects(d);
    renderLedStatus(d);
    renderVision(d);
    let s = d.sensors; if(!s) return;
    if (typeof s === 'string') { try { s = JSON.parse(s); } catch(e) { return; } }
    set('light', s.light, s.light*100/16383);
    setTxt('pir', s.pir ? 'MOTION' : 'clear', s.pir ? 'on' : 'off');
    setTxt('th', s.aht_ok===false?'Sensor unavailable':`${Number.isFinite(s.temp_c)?s.temp_c.toFixed(1):"—"}°C · ${Number.isFinite(s.hum_pct)?s.hum_pct.toFixed(0):"—"}%`);
    document.getElementById('thb').style.width = Math.min(100, s.hum_pct) + '%';
    const gm = Math.max(Math.abs(s.gx||0), Math.abs(s.gy||0), Math.abs(s.gz||0));
    setTxt('mv', gm > 3 ? 'MOVING' : 'still', gm > 3 ? 'on' : '');
    document.getElementById('mvb').style.width = Math.min(100, gm * 10) + '%';
    markMode(s.led_mode);
  };
  ws.onclose = () => { document.getElementById('status').className='bad'; setTimeout(connect, 2000); };
}
function set(id, v, pct){ document.getElementById(id).textContent = v;
  if(id==='light'||id==='force') document.getElementById(id+'b').style.width = pct+'%'; }
function setTxt(id, v, cls){ const e=document.getElementById(id); e.textContent=v; e.className=cls||''; }
const COLORS = {person:'#e34',car:'#39f',truck:'#fa0',bus:'#fa0',motorcycle:'#0bb',bicycle:'#0a6',trafficlight:'#ff0'};
let recordingBusy=false,recordingListBusy=false,recordingPollAt=0;
let visionState=null,cameraState=null,editing=null,editPoints=[],latestFrameKey=null,thresholdEditing=false,lastStopContext=null;
const el=id=>document.getElementById(id);
let brightnessEditing=false;
const pendingControls=new Map();
function syncControl(id,value,property='value'){
 const input=el(id),pending=pendingControls.get(id);
 if(pending){
  if(value===pending.value||Date.now()>pending.until)pendingControls.delete(id);
  else return;
 }
 if(document.activeElement===input&&(input.tagName==='SELECT'||input.type==='color'||input.type==='range'))return;
 if(input[property]!==value)input[property]=value;
}
async function updateControl(id,data,property='value'){
 const pending={value:el(id)[property],until:Date.now()+5000};pendingControls.set(id,pending);
 const result=await config(data);
 if(!result&&pendingControls.get(id)===pending)pendingControls.delete(id);
 return result;
}
let pendingLed=null;
function ledStatus(message,bad=false){const node=el('ledcommandstatus');node.textContent=message;node.style.color=bad?'#ffb6b6':'#9cabbc';}
function renderLedStatus(d){
 if(!pendingLed)return;
 if(!d.mcu_ok){ledStatus('MCU offline · LED command not confirmed',true);return;}
 const ack=d.vision?.led_command,confirmed=ack&&ack.at!==pendingLed.previousCommand&&ack.method===pendingLed.method&&JSON.stringify(ack.args)===JSON.stringify(pendingLed.args);
 if(confirmed&&d.sensors?.led_mode===pendingLed.mode){ledStatus('MCU confirmed '+pendingLed.name+' · brightness '+d.sensors.brightness_percent+'%');pendingLed=null;}
 else if(Date.now()>pendingLed.until){ledStatus('LED command was not confirmed. Try again.',true);pendingLed=null;}
}
function renderBrightness(d){
 const b=d.led;if(!b)return;
 if(!brightnessEditing){el('brightness').value=b.brightness_percent;el('brightnessvalue').textContent=b.brightness_percent+'%';}
 const actual=d.mcu_ok?d.sensors?.brightness_percent:null;
 el('brightnessstatus').textContent=actual===b.brightness_percent?'Applied '+actual+'%':d.mcu_ok?'Applying '+b.brightness_percent+'%…':'MCU offline · setting saved';
}
const editingEffects=new Set();
function paletteStyle(){
 const primary=el('ledprimary').value,secondary=el('ledsecondary').value;
 document.documentElement.style.setProperty('--effect-accent',primary);
 document.documentElement.style.setProperty('--effect-secondary',secondary);
 el('brightness').style.accentColor=primary;
}
function renderEffects(d){
 const settings=d.led?.effects;if(!settings)return;
 if(!editingEffects.has('ledprimary')&&!editingEffects.has('ledsecondary'))syncControl('ledtheme',settings.theme);
 for(const [id,key] of [['ledprimary','primary'],['ledsecondary','secondary'],['ledspeed','speed'],['ledwidth','wave_width']]){
  if(!editingEffects.has(id))syncControl(id,String(settings[key]));
 }
 el('ledspeedvalue').textContent=(Number(el('ledspeed').value)/100)+'×';
 el('ledwidthvalue').textContent=el('ledwidth').value+' LEDs';paletteStyle();
 const actual=d.led.status,applied=actual&&actual.primary===parseInt(settings.primary.slice(1),16)&&actual.secondary===parseInt(settings.secondary.slice(1),16)&&actual.speed===settings.speed&&actual.wave_width===settings.wave_width;
 el('ledsettingsstatus').textContent=!d.mcu_ok?'Settings saved · MCU offline':applied?'Applied · '+settings.theme+' · '+settings.speed/100+'× · '+settings.wave_width+' LEDs':'Applying animation settings to MCU…';
}
el('ledtheme').onchange=()=>updateControl('ledtheme',{led_theme:el('ledtheme').value});
for(const [id,key] of [['ledprimary','led_primary'],['ledsecondary','led_secondary'],['ledspeed','led_speed'],['ledwidth','led_wave_width']]){
 el(id).oninput=()=>{editingEffects.add(id);if(id==='ledprimary'||id==='ledsecondary'){el('ledtheme').value='custom';paletteStyle();}el('ledspeedvalue').textContent=Number(el('ledspeed').value)/100+'×';el('ledwidthvalue').textContent=el('ledwidth').value+' LEDs';};
 el(id).onchange=async()=>{const value=(id==='ledspeed'||id==='ledwidth')?Number(el(id).value):el(id).value;await updateControl(id,{[key]:value});editingEffects.delete(id);};
}
el('ledpintest').onclick=async()=>{
 ledStatus('Checking LED data signal…');
 try{const r=await fetch('/api/led-test',{method:'POST'}),data=await r.json();if(!r.ok)throw Error(data.error||'Signal check failed');const t=data.pin;
 ledStatus(t.high===1&&t.low===0?'D6 switches HIGH / LOW correctly. If the strip stays fixed, check the 5 V supply, common ground and DIN connection.':'D6 signal cannot switch correctly. Check the existing pull-up resistor and its 5 V connection.',!(t.high===1&&t.low===0));}
 catch(e){ledStatus(e.message,true);}
};
el('brightness').oninput=()=>{brightnessEditing=true;el('brightnessvalue').textContent=el('brightness').value+'%';};
el('brightness').onchange=async()=>{const value=Number(el('brightness').value);el('brightnessstatus').textContent='Applying '+value+'%…';await config({brightness:value});brightnessEditing=false;};
async function config(data){
 try{const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const j=await r.json();if(!r.ok)throw Error(j.error||'Update failed');el('error').textContent='';return j;}
 catch(e){el('error').textContent=e.message;return null;}
}
function renderVision(d){
 updateRecording(d.recording);
 const v=d.vision;if(!v)return;visionState=v;cameraState=d.camera;
 const c=d.camera,kind=c?.source_kind,stop=v.bus_stop||{},busMode=v.camera_mode==='bus_stop';
 const context=v.source+':'+v.camera_mode;if(context!==lastStopContext){lastStopContext=context;thresholdEditing=false;editing=null;editPoints=[];el('calbox').style.display='none';el('geometryhelp').textContent=busMode?'Choose Bus stop boundary, then click four corners around the waiting area on the ground.':'The dashed line counts passing objects. Choose a crosswalk zone for pedestrian LED alerts.';}
 el('mobilitycounts').style.display=busMode?'none':'';el('crossingeventsbox').hidden=el('ledlatencybox').hidden=el('resetcounts').hidden=busMode;
 syncControl('cameramode',v.camera_mode||'crosswalk');el('visiontitle').textContent=busMode?'Vision & bus stop occupancy':'Vision & crossing safety';el('busstopbox').hidden=!busMode;el('crossingstatus').hidden=el('crossingledrow').hidden=el('alerthelp').hidden=busMode;el('drawzone').hidden=el('clearzone').hidden=el('drawline').hidden=busMode;el('drawstop').hidden=el('clearstop').hidden=!busMode;
 if(!thresholdEditing&&document.activeElement!==el('stopthreshold'))el('stopthreshold').value=stop.threshold||10;
 el('stopcount').textContent=(stop.count==null?'—':stop.count)+' / '+(stop.threshold||10)+' people';el('stopprogress').value=Math.min(100,stop.occupancy_percent||0);el('stopprogress').style.accentColor=stop.threshold_reached?'#ffc865':'#66dac6';el('stoppercent').textContent=stop.occupancy_percent==null?'Occupancy not available':stop.occupancy_percent+'% of threshold';el('stopstatus').textContent=(stop.preview?'Preview · ':'')+(stop.status||'Set the bus stop boundary');el('stopstatus').className='banner '+(stop.threshold_reached?'warn':'');el('stophelp').textContent=stop.preview?'Preview counts only. Saved warnings come from the live camera.':'Count confirmed people whose feet are inside the waiting area. A warning is saved after two consecutive frames at or above the threshold.';
 el('stopwarnings').replaceChildren();for(const warning of (stop.warnings||[]).slice(0,20)){const item=document.createElement('div');item.textContent=new Date(warning.ts*1000).toLocaleString()+' · Threshold reached · '+warning.people+' people / '+warning.threshold;el('stopwarnings').append(item);}if(!stop.warnings?.length)el('stopwarnings').textContent='No warnings saved.';
 syncControl('camerarotation',String(v.camera_rotation||0));el('camerarotation').disabled=v.source!=='camera';
 syncControl('source',v.source);syncControl('model',v.model);syncControl('colour',v.colour||'natural');syncControl('exposure',v.exposure||'lowlight');syncControl('autoled',v.auto_led,'checked');syncControl('autoexposure',v.auto_exposure!==false,'checked');syncControl('autogain',v.auto_gain!==false,'checked');el('exposure').disabled=v.auto_exposure===false||v.source!=='camera';el('autoexposure').disabled=el('autogain').disabled=v.source!=='camera';
 el('autoled').disabled=!v.profile.zone||!v.live;el('alerthelp').textContent=!v.profile.zone?'Select Crosswalk zone and click four corners around the crossing to enable this switch.':!v.live?'Switch to the live camera and wait for fresh frames to enable alerts.':v.auto_led?'Automatic alerts are active. A confirmed person inside the zone triggers the warning. Manual LED controls switch automation off.':'Enable this switch for live crossing warnings. Manual LED controls switch automation off.';syncControl('detectionmode',v.detection_mode||(v.crosswalk_detail?'crosswalk':'full'));el('detectionmode').disabled=v.source!=='camera';const detailOption=el('detectionmode').querySelector('[value="crosswalk"]'),detailDisabled=!(busMode?stop.boundary:v.profile.zone),detailLabel=busMode?'Bus stop detail · balanced':'Crosswalk detail · balanced';if(detailOption.disabled!==detailDisabled)detailOption.disabled=detailDisabled;if(detailOption.textContent!==detailLabel)detailOption.textContent=detailLabel;
 const requested=v.detection_mode||'full',applied=c?.detection_mode;el('detectionstatus').textContent=applied===requested?'Detector using '+(requested==='tiles2'?'2× tile sweep':requested==='tiles4'?'4× tile sweep':requested==='crosswalk'?'selected-area detail':'full view'):applied?'Applying detection setting…':'Waiting for detector';
 el('ledownership').textContent=v.auto_led?'Automatic':'Manual';
 const status=el('feedstatus');
 if(kind==='simulation'){status.textContent='SIMULATION · Generated traffic and detections. Counts and speeds are simulated; automatic LEDs are disabled.';status.className='banner warn';}
 else if(kind==='replay'){status.textContent='VIDEO REPLAY · Counts and speeds use video timestamps. Automatic LEDs are disabled.';status.className='banner warn';}
 else if(v.live){status.textContent='LIVE CAMERA · '+c.src+' · '+(c.model||v.model);status.className='banner good';}
 else{status.textContent=c?.error||'Live camera unavailable. Counting and automatic crossing warnings are paused.';status.className='banner bad';}
 if(c?.colour_warning)el('error').textContent=c.colour_warning;
 const counts=v.counts||{},liveCounts={};for(const t of v.tracks)liveCounts[t.cls]=(liveCounts[t.cls]||0)+1;
 el('countpeople').textContent=liveCounts.person||0;el('countbikes').textContent=liveCounts.bicycle||0;
 el('countvehicles').textContent=['car','bus','truck','motorcycle'].reduce((n,k)=>n+(liveCounts[k]||0),0);
 el('passedpeople').textContent='Passed '+(counts.person||0);el('passedbikes').textContent='Passed '+(counts.bicycle||0);
 el('passedvehicles').textContent='Passed '+['car','bus','truck','motorcycle'].reduce((n,k)=>n+(counts[k]||0),0)+' · cars/buses/trucks/motorbikes';
 el('visible').textContent=Object.values(counts).reduce((a,b)=>a+b,0);el('directioncounts').textContent='A→B '+(v.directions?.['A→B']||0)+' · B→A '+(v.directions?.['B→A']||0);
 el('frameage').textContent=v.frame_age_ms==null?'—':v.frame_age_ms+' ms';
 const stages=c?.timings;if(stages?.selected_age_ms!=null)el('pipelineage').textContent='Capture / preparation: '+Math.round(stages.selected_age_ms)+' ms\nDetection: '+Math.round(c.inference_ms||0)+' ms\nPreview encoding: '+Math.round(stages.encode_ms||0)+' ms\nWaiting / delivery: '+Math.round(Math.max(0,(v.frame_age_ms||0)-(stages.worker_publish_age_ms||0)))+' ms';else el('pipelineage').textContent='Waiting for stage measurements';
 el('inference').textContent='Inference '+(c?.inference_ms||0)+' ms'+(c?.exposure_ms!=null?' · exposure '+c.exposure_ms+' ms':'')+(c?.gain_x!=null?' · gain '+c.gain_x+'×':'');el('detectionhelp').textContent=(v.detection_mode==='tiles2'||v.detection_mode==='tiles4')?'Full view + one native tile per frame; sweeps '+(v.detection_mode==='tiles2'?'2':'4')+' overlapping areas. '+(c?.detection_passes||0)+' passes · '+(c?.inference_ms||0)+' ms. Objects update less often; late frames pause alerts. Use full view 416 for dependable live updates.':v.detection_mode==='crosswalk'?'Full view + native crosswalk detail on alternate frames. The preview stays wide.':'One full-view pass per frame for the highest speed.';
 el('alertlatency').textContent=v.command_latency_ms==null?'—':Math.round(v.command_latency_ms)+' ms';
 el('confirmedlatency').textContent='Mode readback '+(v.mode_confirmed_ms==null?'—':Math.round(v.mode_confirmed_ms)+' ms after ACK');
 el('camfps').textContent=c?.fps||'—';el('camsrc').textContent=c?.src||'No source';
 el('crossingstatus').textContent=v.crossing_status+(v.inside?' · '+v.inside+' person(s)':'');
 el('crossingstatus').className='banner '+(v.occupied?'warn':'');
 el('calibrationmessage').textContent=v.calibration_message||'';el('autocal').textContent=v.marker_searching?'Stop marker search':v.profile.calibration?'Recalibrate with marker':'Auto calibrate';el('speedhelp').textContent=v.marker_searching?'Looking for AprilTag ID 0. Print at 100%, verify its black edge is 16 cm, and lay it flat on the ground. Keep it large and clear in the preview.':v.profile.calibration?'Saved calibration: '+v.profile.calibration.width+' × '+v.profile.calibration.length+' m. '+(kind==='simulation'?'Synthetic scene measurements.':'Reused automatically after restart. Speeds extend across the same flat ground plane; keep the camera fixed.'):'Speed needs one known ground measurement. Save a measured rectangle once or use the printed calibration marker.';
 const rows=el('tracks');rows.replaceChildren();
 for(const t of v.tracks){const tr=document.createElement('tr');tr.title=t.speed_status+(t.retained?' · last seen '+t.last_seen_s+' seconds ago':'');if(t.retained)tr.style.opacity='.6';for(const value of [t.cls.charAt(0).toUpperCase()+t.cls.slice(1)+' #'+t.id,Math.round(t.conf*100)+'%',t.speed_kmh==null?(t.image_speed_px_s==null?t.speed_status:t.image_speed_px_s.toFixed(1)+' px/s'):'≈ '+t.speed_kmh.toFixed(1)+' km/h']){const td=document.createElement('td');td.textContent=value;tr.append(td);}rows.append(tr);}
 if(!v.tracks.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=3;td.textContent='No tracked objects';tr.append(td);rows.append(tr);}
 el('events').replaceChildren();for(const e of (v.events||[]).slice(0,12)){const div=document.createElement('div');div.textContent=e.message;el('events').append(div);}if(!v.events?.length)el('events').textContent='No crossings recorded.';
 drawCam(c);
}
function updateRecording(recording){
 if(!recording)return;const clean=recording.clean||{},video=recording.annotated||{};
 el('cleanrecordstatus').textContent=clean.error?'Clean buffer: '+clean.error:clean.ready?'Clean rolling buffer: '+clean.buffered_seconds+' / 15 seconds · '+clean.sample_fps+' fps · on Arduino':'Clean buffer waiting for live camera frames';
 el('yolorecordstatus').textContent=video.active?'RECORDING YOLO · '+video.seconds+' seconds · '+video.frames+' video frames'+(video.dropped_frames?' · '+video.dropped_frames+' input frames skipped':''):video.finishing?'Finalizing video…':video.error||'YOLO recording stopped';
 el('yolorecordstatus').style.color=video.active?'#ff9292':'';
 el('saveclean').disabled=recordingBusy||!clean.ready;el('recordyolo').disabled=recordingBusy||video.active||video.finishing||!visionState?.live;
 el('recordyolo').hidden=video.active;el('stoprecord').hidden=!video.active;el('stoprecord').disabled=recordingBusy;
 if(Date.now()-recordingPollAt>5000&&!recordingListBusy){recordingPollAt=Date.now();refreshRecordings();}
}
async function refreshRecordings(){
 if(recordingListBusy)return;recordingListBusy=true;
 try{const r=await fetch('/api/recordings');const data=await r.json();if(!r.ok)throw new Error(data.error||'Unable to list videos');const list=el('recordingdownloads');list.replaceChildren();
  for(const clip of (data.clips||[]).slice(0,8)){const row=document.createElement('div');row.style.margin='6px 0';const link=document.createElement('a');link.href='/recordings/'+encodeURIComponent(clip.name);link.textContent=(clip.kind==='clean'?'Clean':'YOLO')+' · '+clip.duration_seconds+' s · '+(clip.bytes/1048576).toFixed(1)+' MB · Download AVI';link.style.color='#66dac6';row.append(link);const timestamps=document.createElement('a');timestamps.href='/recordings/'+encodeURIComponent(clip.name.replace(/\.avi$/,'.json'));timestamps.textContent=' · Capture timestamps';timestamps.style.color='#8bb5ff';row.append(timestamps);list.append(row);}
  if(!data.clips?.length)list.textContent='Saved clips will appear here.';
 }catch(error){el('yolorecordstatus').textContent=error.message;}finally{recordingListBusy=false;}
}
async function recordingAction(action){
 if(recordingBusy)return;recordingBusy=true;el('saveclean').disabled=el('recordyolo').disabled=el('stoprecord').disabled=true;
 if(action==='save_clean')el('cleanrecordstatus').textContent='Saving the latest clean footage on Arduino…';
 try{const r=await fetch('/api/recordings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});const data=await r.json();if(!r.ok)throw new Error(data.error||'Recording command failed');await refreshRecordings();}
 catch(error){el('error').textContent=error.message;}finally{recordingBusy=false;}
}
el('saveclean').onclick=()=>recordingAction('save_clean');el('recordyolo').onclick=()=>recordingAction('start');el('stoprecord').onclick=()=>recordingAction('stop');el('refreshrecordings').onclick=refreshRecordings;
function drawCam(c){
 const img=el('camimg'),cv=el('camcv');
 if(!c?.frame||!c.w||!c.h){img.hidden=true;el('emptycam').style.display='grid';cv.getContext('2d').clearRect(0,0,cv.width,cv.height);return;}
 el('emptycam').style.display='none';img.hidden=false;el('camwrap').style.aspectRatio=c.w+'/'+c.h;
 const key=c.stream_id+':'+c.frame_id;
 if(key!==latestFrameKey){latestFrameKey=key;img.onload=drawOverlay;img.src='data:image/jpeg;base64,'+c.frame;}else drawOverlay();
}
function drawOverlay(){
 const cv=el('camcv'),wrap=el('camwrap');cv.width=Math.round(wrap.clientWidth);cv.height=Math.round(wrap.clientHeight);
 const ctx=cv.getContext('2d'),v=visionState;if(!v)return;
 const poly=(pts,color,fill,close=true)=>{if(!pts?.length)return;ctx.beginPath();pts.forEach((p,i)=>{const x=p[0]*cv.width,y=p[1]*cv.height;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});if(close)ctx.closePath();ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke();if(fill){ctx.fillStyle=fill;ctx.fill();}};
 if(v.camera_mode==='bus_stop')poly(v.bus_stop?.boundary,v.bus_stop?.threshold_reached?'#ffc865':'#71c9ff','#71c9ff18');else poly(v.profile.zone,v.occupied?'#ffc865':'#66dac6','#66dac614');
 if(editing==='calibration')poly(v.profile.calibration?.points,'#a592ff',null);
 if(v.camera_mode!=='bus_stop'){ctx.setLineDash([7,5]);poly(v.profile.line,'#d8e5f6',null,false);ctx.setLineDash([]);}
 for(const t of v.tracks){const col=v.camera_mode==='bus_stop'&&v.bus_stop?.inside_ids?.includes(t.id)?'#ffc865':COLORS[t.cls]||'#fff';const [a,b,c,d]=t.box;ctx.strokeStyle=col;ctx.lineWidth=2;ctx.strokeRect(a*cv.width,b*cv.height,(c-a)*cv.width,(d-b)*cv.height);poly(t.trail,col,null,false);
 const label=t.cls+' #'+t.id+(t.retained?' (recent)':'')+' · '+Math.round(t.conf*100)+'%'+(t.speed_kmh==null?(t.image_speed_px_s==null?'':' · '+t.image_speed_px_s.toFixed(1)+' px/s'):' · '+t.speed_kmh.toFixed(1)+' km/h');ctx.font='12px system-ui';const x=Math.min(a*cv.width,Math.max(0,cv.width-ctx.measureText(label).width-8)),y=Math.max(17,b*cv.height);ctx.fillStyle='#0b121ce8';ctx.fillRect(x,y-17,ctx.measureText(label).width+8,19);ctx.fillStyle=col;ctx.fillText(label,x+4,y-3);}
 poly(editPoints,'#ffdb73',null,editing!=='line');for(const [i,p]of editPoints.entries()){ctx.fillStyle='#ffdb73';ctx.beginPath();ctx.arc(p[0]*cv.width,p[1]*cv.height,5,0,Math.PI*2);ctx.fill();ctx.fillText(String(i+1),p[0]*cv.width+8,p[1]*cv.height);}
}
function beginGeometry(kind){editing=kind;editPoints=[];el('calbox').style.display=kind==='calibration'?'block':'none';el('geometryhelp').textContent=kind==='line'?'Click two endpoints. Each confirmed track is counted once when it crosses this line.':kind==='bus_stop_boundary'?'Click four corners around the bus stop waiting area on the ground, following its perimeter.':kind==='zone'?'Click four corners around the crosswalk. Pedestrian footpoints inside this zone trigger warnings.':'Click ground corners: top-left → top-right → bottom-right → bottom-left.';drawOverlay();}
el('autocal').onclick=()=>config({auto_calibrate:!visionState?.marker_searching});el('drawline').onclick=()=>beginGeometry('line');el('drawzone').onclick=()=>beginGeometry('zone');el('drawstop').onclick=()=>beginGeometry('bus_stop_boundary');el('drawcal').onclick=()=>beginGeometry('calibration');
el('cancelgeom').onclick=()=>{editing=null;editPoints=[];el('calbox').style.display='none';el('geometryhelp').textContent='Geometry selection cancelled.';drawOverlay();};
el('camcv').onclick=async e=>{if(!editing||!cameraState?.frame)return;const r=e.currentTarget.getBoundingClientRect();if(editing==='white'){await config({white_point:[(e.clientX-r.left)/r.width,(e.clientY-r.top)/r.height]});editing=null;editPoints=[];el('geometryhelp').textContent='White reference requested. Colours stay locked after balancing.';return;}if(editPoints.length>=(editing==='line'?2:4))return;editPoints.push([(e.clientX-r.left)/r.width,(e.clientY-r.top)/r.height]);drawOverlay();const count=editing==='line'?2:4;if(editPoints.length===count&&editing!=='calibration'){const kind=editing;const result=await config({[kind]:editPoints});if(result){editing=null;editPoints=[];el('geometryhelp').textContent=kind==='line'?'Counting line saved.':kind==='bus_stop_boundary'?'Bus stop boundary saved. Confirmed people inside it count toward the threshold.':'Crosswalk zone saved. Enable automatic LEDs when the live feed is ready.';}}};
el('applycal').onclick=async()=>{if(editPoints.length!==4){el('error').textContent='Select all four ground corners first.';return;}const width=Number(el('calwidth').value),length=Number(el('callength').value);const result=await config({calibration:{points:editPoints,width,length}});if(result){editing=null;editPoints=[];el('calbox').style.display='none';el('geometryhelp').textContent='Calibration saved. Speeds appear after enough track history.';}};
el('cameramode').onchange=async()=>{const mode=el('cameramode').value;if(await updateControl('cameramode',{camera_mode:mode})){editing=null;editPoints=[];el('calbox').style.display='none';el('geometryhelp').textContent=mode==='bus_stop'?'Choose Bus stop boundary, then click four corners around the waiting area on the ground.':'The dashed line counts passing objects. Choose a crosswalk zone for pedestrian LED alerts.';}};el('clearstop').onclick=()=>config({bus_stop_boundary:null});el('stopthreshold').oninput=()=>{thresholdEditing=true;};el('savestopthreshold').onclick=async()=>{if(await config({bus_stop_threshold:Number(el('stopthreshold').value)})){thresholdEditing=false;el('geometryhelp').textContent='Bus stop threshold saved.';}};
el('clearzone').onclick=()=>config({zone:null,auto_led:false});el('clearcal').onclick=()=>config({calibration:null});
el('autoled').onchange=()=>updateControl('autoled',{auto_led:el('autoled').checked},'checked');el('resetcounts').onclick=()=>config({reset_counts:true});
el('source').onchange=()=>{if(el('source').value==='replay'){el('video').click();return;}updateControl('source',{source:el('source').value});};
el('camerarotation').onchange=async()=>{if(await updateControl('camerarotation',{camera_rotation:Number(el('camerarotation').value)})){editing=null;editPoints=[];el('calbox').style.display='none';el('geometryhelp').textContent='Rotation saved. Detection, zones and calibration follow the rotated view. Recalibrate if the camera position changes.';}};
el('model').onchange=()=>updateControl('model',{model:el('model').value});el('detectionmode').onchange=()=>updateControl('detectionmode',{detection_mode:el('detectionmode').value});el('autoexposure').onchange=()=>updateControl('autoexposure',{auto_exposure:el('autoexposure').checked},'checked');el('autogain').onchange=()=>updateControl('autogain',{auto_gain:el('autogain').checked},'checked');
el('colour').onchange=()=>updateControl('colour',{colour:el('colour').value});el('exposure').onchange=()=>updateControl('exposure',{exposure:el('exposure').value});el('rebalance').onclick=()=>config({rebalance:true});el('whitepoint').onclick=()=>{editing='white';editPoints=[];el('geometryhelp').textContent='Hold matte white paper in the scene lighting and click its centre in the preview. Avoid clipped ceiling lights.';};
el('video').onchange=async()=>{const file=el('video').files[0];if(!file)return;const body=new FormData();body.append('video',file);el('error').textContent='Uploading video…';try{const r=await fetch('/api/video',{method:'POST',body});const j=await r.json();el('error').textContent=r.ok?'':j.error;}catch(e){el('error').textContent=e.message;}};
window.addEventListener('resize',drawOverlay);
const MODE_NAMES={0:"Ambient",1:"Rainbow",2:"Breathe",3:"Knight-Rider",6:"Off",7:"Red",8:"Green",9:"Blue",10:"Manual",11:"Yellow flash",12:"Red alert",13:"Hazard",14:"Siren",15:"Crossing wave",16:"Flow left",17:"Flow right",18:"Comet",19:"Theatre chase",20:"Heartbeat",21:"Bus-stop beacon",22:"Ocean waves",23:"Ripple",24:"Aurora",25:"Sparkle",26:"Meteor shower",27:"Bounce",28:"Fill & drain",29:"Gradient drift",30:"Fireflies",31:"Twin wave",32:"Chase blocks",33:"Fire glow"};
function sendMode(m){
 if(!ws||ws.readyState!==1){ledStatus('Dashboard disconnected · reconnecting. Try again when MCU is live.',true);return;}
 pendingLed={mode:m===6?10:m,name:MODE_NAMES[m]||String(m),method:m===6?'set_led':'set_mode',args:m===6?[0,0,0]:[m],previousCommand:visionState?.led_command?.at,until:Date.now()+5000};
 ledStatus('Sending '+pendingLed.name+' to MCU…');ws.send(JSON.stringify({mode:m}));
}
document.querySelectorAll(".ab").forEach(b => {
  b.onclick = () => sendMode(+b.dataset.mode);
  b.style.margin = "2px";
});
function markMode(m){
  const n = document.getElementById('modeName');
  n.textContent = MODE_NAMES[m] ?? m;
  document.querySelectorAll(".ab").forEach(b => b.classList.toggle("active", +b.dataset.mode === m));
}
function sendLed(){ const c=document.getElementById('col').value;
  if(!ws||ws.readyState!==1){ledStatus('Dashboard disconnected · colour not sent',true);return;}
  const rgb=[parseInt(c.slice(1,3),16),parseInt(c.slice(3,5),16),parseInt(c.slice(5,7),16)];
  pendingLed={mode:10,name:'colour '+c,method:'set_led',args:rgb,previousCommand:visionState?.led_command?.at,until:Date.now()+5000};ledStatus('Sending colour to MCU…');
  ws.send(JSON.stringify({led:rgb})); }
connect();

window.sendLed=sendLed;
})();
