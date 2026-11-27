/* Galiel X-Ray: opt-in, read-only walkthrough of real application pages.
   No customer data is collected or transmitted. */
(()=>{"use strict";
const stops=[
["Homepage","Ready-made homepage","The public page is served by Apache without a database query.","INFRASTRUCTURE","/","header"],
["Homepage","Three languages","The language switcher makes the interface available in English, Spanish and French.","TEMPLATE","/","header"],
["Homepage","Routing","Services opens the Django catalog and applies the visitor's access rules.","VIEW","/","a[href*='services']"],
["Homepage","Catalog hierarchy","Country, region, municipality and service determine each offering.","MODEL","/services/","#country"],
["Homepage","Sign-in security","Django stores hashed passwords and protects private views.","VIEW","/login/","form"],
["Homepage","Real Galiel design","The actual page uses the Galiel signature and its shared styling; no placeholder wordmark is inserted.","TEMPLATE","/","header"],
["Homepage","Request journey","Browser → Apache → FastCGI → Django → SQLite.","INFRASTRUCTURE","/","main"],
["Homepage","Agile releases","Changes are tested, reviewed and deployed with a database backup and rollback plan.","PROCESS","/","main"],
["Accounts","Registration records","A registration creates a User and an associated Profile.","MODEL","/register/","form"],
["Accounts","Email activation","Activation uses a signed, expiring token.","INFRASTRUCTURE","/register/","form"],
["Accounts","Service-aware login","After authentication the client resumes a chosen service or enters their workspace.","VIEW","/login/","form"],
["Client dashboard","Shared workspace","The same header, navigation and visual system appear throughout the portal.","TEMPLATE","/dashboard/","header"],
["Client dashboard","Private counts","Dashboard totals are filtered by the authenticated client.","MODEL","/dashboard/","main"],
["Client dashboard","GAL process number","Cases have a readable GAL reference, status and next step.","VIEW","/dashboard/","main"],
["Client dashboard","Scripted assistance","Help follows predefined choices, without accessing other clients' cases.","VIEW","/dashboard/","[data-help], #galiel-help, main"],
["A process","Create a draft","Starting a service creates a draft application and an initial event.","VIEW","/services/","main"],
["A process","Six-stage workflow","The application guides the client through details, questions, documents and review.","VIEW","/services/","main"],
["A process","File validation","Uploads check file content and enforce a 10 MB limit.","VIEW","/documents/upload/","main"],
["A process","Private file storage","Client documents remain outside public static files and require authorization to download.","INFRASTRUCTURE","/documents/upload/","main"],
["A process","Process status history","Status changes are represented as application events.","MODEL","/dashboard/","main"],
["Alerts and news","Unread bell","Only the signed-in client's unread reminder count is returned.","VIEW","/alerts/","main"],
["Alerts and news","Automatic alerts","Eligible status transitions produce client reminders.","MODEL","/alerts/","main"],
["Alerts and news","Scheduled jobs","Scheduled tasks can deliver reminders and create private backups.","INFRASTRUCTURE","/alerts/","main"],
["Alerts and news","Announcements","Publishing windows control the visibility of staff-authored announcements.","MODEL","/updates/","main"],
["The staff side","Django administration","Authorized employees manage services, applications and records through Django Admin.","VIEW","/admin/","main"],
["The staff side","Status changes","Staff updates can create an event, notification and next action.","MODEL","/admin/","main"],
["The staff side","Access control","Clients cannot access Django Admin, and staff permissions are checked on the server.","VIEW","/admin/","main"],
["The staff side","Conversations","Client conversations keep correspondence attached to the right process.","MODEL","/messages/","main"]
];
const colors={MODEL:"#5b8def",VIEW:"#e8875a",TEMPLATE:"#4cc08a",INFRASTRUCTURE:"#a98be6",PROCESS:"#e3c35a"};
const key="galiel-xray-step";let active=false,index=0,backdrop=null,anchor=null;
const norm=p=>p.replace(/\/+$/,"")||"/";
function findTarget(s){for(const selector of s.split(", ")){const el=document.querySelector(selector);if(el)return el;}return document.body;}
function ui(){if(backdrop)return;const style=document.createElement("style");style.textContent=`
.gx-trigger{position:fixed;right:18px;bottom:18px;z-index:9990;background:#06121c;color:#fff;border:2px solid #7fe3ff;padding:12px 17px;border-radius:24px;font:700 14px system-ui;cursor:pointer;box-shadow:0 0 20px #7fe3ff77}
.gx-layer{position:fixed;inset:0;z-index:9991;background:rgba(5,13,24,.78);backdrop-filter:grayscale(1) contrast(1.2);color:#fff;font-family:Inter,system-ui,sans-serif}
.gx-layer:before{content:"";position:absolute;inset:0;border-top:3px solid #7fe3ff;animation:gx-scan 1.3s ease-out both;pointer-events:none}
@keyframes gx-scan{from{top:0}to{top:100%}}@media(prefers-reduced-motion:reduce){.gx-layer:before{animation:none}}
.gx-target{position:fixed;z-index:9992;border:3px solid #7fe3ff;box-shadow:0 0 0 9999px #06121c33,0 0 25px #7fe3ff88;pointer-events:none;border-radius:8px}
.gx-card{position:fixed;z-index:9993;left:50%;top:50%;transform:translate(-50%,-50%);width:min(440px,calc(100vw - 32px));max-height:calc(100vh - 32px);overflow:auto;padding:23px;background:#101012;border:1px solid #dc7444;border-radius:12px;box-sizing:border-box}
.gx-meta{font:700 12px system-ui;letter-spacing:.1em;color:#9edffe}.gx-card h2{font:800 22px system-ui;margin:12px 0}.gx-card p{line-height:1.55;color:#e9e9ec}.gx-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}
.gx-actions button{font:700 14px system-ui;padding:11px 16px;border:1px solid #777;border-radius:24px;cursor:pointer;background:#dc7444;color:#111}.gx-actions button.secondary{background:transparent;color:white}.gx-card button:focus-visible,.gx-trigger:focus-visible{outline:3px solid #7fe3ff;outline-offset:3px}
`;document.head.append(style);const trigger=document.createElement("button");trigger.type="button";trigger.className="gx-trigger";trigger.textContent="Switch on X-Ray";trigger.setAttribute("aria-label","Switch on X-Ray presentation tour");trigger.addEventListener("click",()=>start(0));document.body.append(trigger);}
function close(){active=false;sessionStorage.removeItem(key);backdrop?.remove();anchor?.remove();backdrop=anchor=null;document.querySelector(".gx-trigger").hidden=false;document.removeEventListener("keydown",keys);}
function start(n){index=n;active=true;document.querySelector(".gx-trigger").hidden=true;document.addEventListener("keydown",keys);show();}
function go(n){if(n>=stops.length){close();return;}if(n<0)n=0;index=n;const next=stops[n];sessionStorage.setItem(key,String(n));if(norm(location.pathname)!==norm(next[4])){location.href=next[4];return;}show();}
function keys(e){if(e.key==="Escape")close();else if(e.key==="ArrowRight"){e.preventDefault();go(index+1);}else if(e.key==="ArrowLeft"){e.preventDefault();go(index-1);}}
function show(){backdrop?.remove();anchor?.remove();const [part,title,body,kind,path,selector]=stops[index];backdrop=document.createElement("div");backdrop.className="gx-layer";backdrop.setAttribute("role","presentation");document.body.append(backdrop);const t=findTarget(selector);const r=t.getBoundingClientRect();anchor=document.createElement("div");anchor.className="gx-target";anchor.style.cssText=`top:${Math.max(0,r.top-5)}px;left:${Math.max(0,r.left-5)}px;width:${Math.min(innerWidth-r.left,Math.max(20,r.width+10))}px;height:${Math.min(innerHeight-r.top,Math.max(20,r.height+10))}px`;document.body.append(anchor);
const card=document.createElement("section");card.className="gx-card";card.setAttribute("role","dialog");card.setAttribute("aria-modal","true");card.setAttribute("aria-labelledby","gx-title");const meta=document.createElement("div");meta.className="gx-meta";meta.style.color=colors[kind];meta.textContent=`X-RAY TOUR · ${part} · ${kind} · ${index+1} / 28`;const h=document.createElement("h2");h.id="gx-title";h.textContent=title;const p=document.createElement("p");p.textContent=body;const nav=document.createElement("div");nav.className="gx-actions";function button(label,fn,secondary=false){const b=document.createElement("button");b.type="button";b.textContent=label;b.className=secondary?"secondary":"";b.onclick=fn;nav.append(b);return b;}button("← Back",()=>go(index-1),true).disabled=index===0;button(index===27?"Finish tour":"Next →",()=>go(index+1));button("× Exit",close,true);card.append(meta,h,p,nav);backdrop.append(card);card.querySelector("button:not([disabled])").focus();}
document.addEventListener("DOMContentLoaded",()=>{ui();const stored=sessionStorage.getItem(key);if(stored!==null){const n=Number(stored);if(Number.isInteger(n)&&n>=0&&n<28)start(n);}});
})();