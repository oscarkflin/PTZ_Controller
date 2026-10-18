const source=readFile('static/app.js');
const handlers={}, windowHandlers={}, commands=[];
const joystick={focus(){},setPointerCapture(){},getBoundingClientRect(){return {left:0,top:0,width:280,height:280};},addEventListener(name,fn){handlers[name]=fn;}};
const stick={style:{}};
const block=source.slice(source.indexOf('const joystick ='),source.indexOf('function presetLabel'));
const setup=new Function('$','window','commands',`
  let held=null, ready=true, liveEnabled=true;
  const speed=()=>3;
  function start(data){held=data; commands.push(data);}
  function stop(){held=null; commands.push({action:'stop'});}
  ${block}
`);
setup(id=>id==='joystick'?joystick:stick,{addEventListener(name,fn){windowHandlers[name]=fn;}},commands);
const event={pointerId:7,pointerType:'mouse',buttons:1,clientX:225,clientY:140,preventDefault(){}};
handlers.pointerdown(event);
if(commands[0]?.action!=='move') throw Error('Drag must start motion');
windowHandlers.pointerup(event);
if(commands[1]?.action!=='stop' || !stick.style.transform.includes('0px')) throw Error('Release outside must stop and recenter');
handlers.pointermove(event);
if(commands.length!==2) throw Error('Move after release must not restart');
handlers.pointerdown(event);
handlers.pointermove({...event,buttons:0});
if(commands[3]?.action!=='stop') throw Error('Lost mouse-up must stop');
handlers.pointerdown(event);
windowHandlers.blur();
if(commands[5]?.action!=='stop') throw Error('Window blur must stop');
print('Joystick outside release, lost release, and blur checks passed');
