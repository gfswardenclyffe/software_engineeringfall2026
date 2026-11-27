/* Galiel X-Ray presenter mode. Vanilla JS; silent and inert without opt-in. */
(()=>{"use strict";
const KEY="galiel:xray", STEP="galiel:xray:step", INTRO="galiel:xray:intro";
const COLORS={model:"#5b8def",view:"#e8875a",template:"#4cc08a",infra:"#a98be6",process:"#e3c35a"};
const NAMES={model:"Model",view:"View",template:"Template",infra:"Infrastructure",process:"Process"};
const ROOT="/static/portal/";const GITHUB="https://github.com/gfswardenclyffe/software_engineeringfall2026/blob/main/";
const get=(k)=>{try{return sessionStorage.getItem(k)}catch(_){return null}};
const put=(k,v)=>{try{sessionStorage.setItem(k,v)}catch(_){}};
const del=k=>{try{sessionStorage.removeItem(k)}catch(_){}};
const param=new URLSearchParams(location.search).get("xray");
if(param==="0"){del(KEY);del(STEP);del(INTRO);return}
if(param!=="1"&&get(KEY)!=="1")return;
put(KEY,"1");
let data=null,idx=0,root=null,trigger=null,card=null,anchor=null,timer=null,ready=false,scanPending=false,activeMode="intro",layoutFrame=0;
const h=(tag,cls,text)=>{const x=document.createElement(tag);if(cls)x.className="gx-"+cls;if(text!==undefined)x.textContent=text;return x};
const btn=(label,fn,cls)=>{const x=h("button",cls||"",label);x.type="button";x.addEventListener("click",fn);return x};
const slug=p=>p.replace(/\/+$/,"")||"/";
const visible=el=>{if(!el)return false;const style=getComputedStyle(el);if(style.display==="none"||style.visibility==="hidden")return false;const r=el.getBoundingClientRect();return r.width>0&&r.height>0};
const targetOf=s=>{const exact=document.querySelector('[data-xray="'+s.id+'"]');if(visible(exact))return exact;try{const fallback=s.target?document.querySelector(s.target):null;return visible(fallback)?fallback:null}catch(_){return null}};
const pageOf=s=>{let url=s.page;if(url.includes("{demo_process_id}")){const id=data.settings.demo_process_id;if(!id)return null;url=url.replace("{demo_process_id}",String(id))}return url};
function remove(){if(timer){clearTimeout(timer);timer=null}if(layoutFrame){cancelAnimationFrame(layoutFrame);layoutFrame=0}root?.remove();root=null;anchor=null;card=null}
function scheduleGeometry(){if(!root||layoutFrame)return;layoutFrame=requestAnimationFrame(()=>{layoutFrame=0;syncGeometry()})}
function syncGeometry(){if(!root||!data)return;
 const bones=root.querySelector(".gx-bones");if(!bones)return;
 bones.replaceChildren();root.querySelectorAll(".gx-marker").forEach(x=>x.remove());
 const step=data.stops[idx],part=currentPart();
 for(const x of data.stops.filter(v=>v.part===part.id)){
  const route=pageOf(x);if(!route||slug(location.pathname)!==slug(route))continue;
  const t=targetOf(x);if(!t)continue;const r=t.getBoundingClientRect();
  const bone=h("div","bone");Object.assign(bone.style,{left:r.left+"px",top:r.top+"px",width:r.width+"px",height:r.height+"px"});
  bone.append(h("small","",x.tech.split(" · ")[0].split(" → ")[0]));bones.append(bone);
  const marker=btn(String(x.id),()=>transition(x.id-1),"marker");marker.style.setProperty("--gx-color",COLORS[x.layer]);
  marker.setAttribute("aria-label","Jump to stop "+x.id+": "+x.title);
  marker.setAttribute("aria-current",String(x.id===step.id));
  Object.assign(marker.style,{left:Math.max(8,r.left-16)+"px",top:Math.max(60,r.top-16)+"px"});
  root.append(marker);
 }
 const t=activeMode==="stop"?targetOf(step):null;const rect=t?t.getBoundingClientRect():null;
 if(anchor){anchor.remove();anchor=null}
 if(rect){anchor=h("div","ring");anchor.style.setProperty("--gx-color",COLORS[step.layer]);
  Object.assign(anchor.style,{left:Math.max(0,rect.left-4)+"px",top:Math.max(55,rect.top-4)+"px",width:rect.width+8+"px",height:rect.height+8+"px"});root.append(anchor)}
 if(card)position(card,rect);
}
function exit(){del(KEY);del(STEP);del(INTRO);ready=false;window.removeEventListener("scroll",scheduleGeometry,true);window.removeEventListener("resize",scheduleGeometry);if(root){if(!root.querySelector(".gx-scan"))root.append(h("div","scan"));root.classList.add("gx-scanning-up");const duration=matchMedia("(prefers-reduced-motion: reduce)").matches?0:1100;setTimeout(()=>{remove();trigger?.remove();trigger=null},duration)}else{trigger?.remove();trigger=null}document.removeEventListener("keydown",keyboard)}
function position(el,rect){const w=innerWidth,hh=innerHeight,cw=Math.min(400,w-32),height=el.offsetHeight||260;
const right=rect?rect.right+24:Math.round((w-cw)/2);
const left=rect?(right+cw<w-14?right:rect.left-cw-24>10?rect.left-cw-24:Math.round((w-cw)/2)):Math.round((w-cw)/2);
let top=rect?rect.top:Math.round((hh-height)/2);top=Math.min(Math.max(70,top),Math.max(70,hh-height-10));
el.style.left=left+"px";el.style.top=top+"px"}
function currentPart(){return data.parts.find(p=>p.id===data.stops[idx].part)}
function transition(next){if(next<0)next=0;if(next>=data.stops.length){idx=27;render("end");return}
const dest=data.stops[next],route=pageOf(dest),partChanged=dest.part!==data.stops[idx].part;idx=next;put(STEP,String(idx));if(partChanged){put(INTRO,"1");scanPending=true;}
if(route&&slug(location.pathname)!==slug(route)){location.href=route+(route.includes("?")?"&":"?")+"xray=1";return}
render(partChanged?"intro":"stop");if(partChanged)del(INTRO)}
function keyboard(e){if(!ready)return;if(e.key==="Escape"){e.preventDefault();exit()}else if(e.key==="ArrowRight"){e.preventDefault();transition(idx+1)}else if(e.key==="ArrowLeft"){e.preventDefault();transition(idx-1)}}
function start(){trigger?.remove();trigger=null;ready=true;scanPending=true;render("intro");document.addEventListener("keydown",keyboard);window.addEventListener("scroll",scheduleGeometry,true);window.addEventListener("resize",scheduleGeometry)}
function render(mode){
remove();activeMode=mode;
const s=data.stops[idx],p=currentPart(),path=pageOf(s),onPage=!!path&&slug(path)===slug(location.pathname),el=onPage?targetOf(s):null;
if(el&&typeof el.scrollIntoView==="function")el.scrollIntoView({behavior:"instant",block:"center"});
root=h("div","shell");root.setAttribute("aria-label","X-Ray presentation tour");const wash=h("div","wash");root.append(wash);
if(scanPending){root.append(h("div","scan"));scanPending=false;}const top=h("header","bar");const label=h("strong","brand","X-RAY TOUR · PART "+p.id+" OF 6 · "+p.name.toUpperCase());top.append(label);
const legend=h("div","key");for(const layer of ["model","view","template","infra","process"]){const t=h("span","key-item");const dot=h("i","dot");dot.style.background=COLORS[layer];t.append(dot,document.createTextNode(NAMES[layer]));legend.append(t)}top.append(legend);
const end=h("div","end");end.append(h("span","counter","Stop "+s.id+" of 28"));end.append(btn("×",exit,"exit"));top.append(end);root.append(top);
const bones=h("div","bones");root.append(bones);
card=h("section","card");card.setAttribute("role","dialog");card.setAttribute("aria-modal","true");card.setAttribute("aria-labelledby","gx-title");card.style.setProperty("--gx-color",COLORS[s.layer]);const buttons=h("div","actions");
if(mode==="intro"){card.append(h("div","kicker","PART "+p.id+" OF 6"),h("h2","",p.intro),h("p","",p.description));buttons.append(btn("Start →",()=>render("stop"),"primary"))}
else if(mode==="end"){card.append(h("div","kicker","END OF TOUR"),h("h2","","That is the whole of Galiel"),h("p","","28 stops, six parts, one working system."));buttons.append(btn("← Back",()=>transition(27)),btn("Restart",()=>{idx=0;transition(0);render("intro")},"primary"))}
else{card.append(h("div","kicker",s.id+" · "+NAMES[s.layer].toUpperCase()),h("h2","",s.title),h("p","",s.body),h("div","tech",s.tech));if(s.github_path&&!s.github_path.startsWith("stop")){const link=h("a","","View on GitHub ↗");link.href=GITHUB+s.github_path;link.target="_blank";link.rel="noopener noreferrer";card.append(link)}
if(!onPage){const warning=h("p","","This stop belongs to "+(path||"a demo process that has not been configured")+".");card.append(warning)}
if(s.panel){const panel=h("div","panel");panel.textContent=s.id===7?"Browser → Apache → FastCGI → Django → SQLite":s.id===8?"Agile · automated tests · dry-run · backup · rollback":s.id===10?"Registration → signed email link → activation": "Scheduled reminder email + private daily backup";root.append(panel)}
const back=btn("← Back",()=>transition(idx-1));back.disabled=idx===0;buttons.append(back);
const nextAtEnd=idx===data.stops.length-1;const partEnd=idx===currentStops[currentStops.length-1].id-1;
buttons.append(btn(nextAtEnd?"Finish tour →":partEnd?"Next part →":"Next →",()=>{if(nextAtEnd)render("end");else if(partEnd){transition(idx+1);}else transition(idx+1)},"primary"))}
buttons.append(btn("× Exit",exit));card.append(buttons);root.append(card);
document.body.append(root);syncGeometry();if(innerWidth<768){const mobile=h("div","mobile","X-Ray tour is designed for a large screen");mobile.append(btn("× Exit",exit));root.append(mobile)}
const focus=card.querySelector("button:not(:disabled)");focus?.focus();
}
function mount(){if(param==="1"&&get(STEP)===null){trigger=btn("Switch on X-Ray",start,"trigger");document.body.append(trigger);return}let n=Number(get(STEP));idx=Number.isInteger(n)&&n>=0&&n<28?n:0;ready=true;const intro=get(INTRO)==="1"||get(STEP)===null;scanPending=intro;del(INTRO);render(intro?"intro":"stop");document.addEventListener("keydown",keyboard);window.addEventListener("scroll",scheduleGeometry,true);window.addEventListener("resize",scheduleGeometry)}
function init(){fetch(ROOT+"galiel-xray-stops.json",{credentials:"same-origin"}).then(r=>{if(!r.ok)throw Error("stop data unavailable");return r.json()}).then(payload=>{if(payload.stops?.length!==28||payload.parts?.length!==6)return;data=payload;mount()}).catch(()=>{/* no messages in normal page */})}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();
