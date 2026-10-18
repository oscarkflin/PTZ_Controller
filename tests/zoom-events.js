// Run with macOS JavaScriptCore's jsc from the project directory.
const source=readFile('static/app.js');
const handlers={};
const button={dataset:{zoom:'1'},focus(){},setPointerCapture(){},addEventListener(name,fn){handlers[name]=fn;}};
const commands=[];
const setup=new Function('document','start','stop','ready','liveEnabled','held',source.slice(source.indexOf('let zoomPointer='),source.indexOf("$('speed').oninput")));
setup({querySelectorAll(){return [button];},addEventListener(){}},data=>commands.push(data),()=>commands.push({action:'stop'}),true,true,null);
const pointer={pointerId:1,preventDefault(){}};
handlers.pointerdown(pointer);
if(commands.length!==1 || commands[0].action!=='zoom' || commands[0].direction!==1) throw Error('Press must start zoom');
handlers.pointerup(pointer);
handlers.lostpointercapture(pointer);
if(commands.length!==2 || commands[1].action!=='stop') throw Error('Release must stop zoom once');
handlers.pointerdown(pointer);
handlers.pointercancel(pointer);
if(commands.length!==4 || commands[3].action!=='stop') throw Error('Cancellation must stop zoom');
print('Zoom press, release, and cancellation checks passed');
