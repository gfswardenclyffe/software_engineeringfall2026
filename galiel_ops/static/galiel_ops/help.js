/* Deterministic button-only assistant. No AI, freeform text, telemetry or personal data cache. */
(() => {
  const root=document.querySelector("[data-galiel-help]");
  if(!root)return;
  const language=(root.dataset.lang||document.documentElement.lang||"en").slice(0,2);
  const lang=["es","fr"].includes(language)?language:"en";
  const labels={
    en:["How can we help?","Services & prices","What documents do I need?","Where is my process?","Talk to a person","Select a service","No documents listed for this service.","Sign in to view your processes.","Message the team","WhatsApp details will be added soon."],
    es:["¿En qué podemos ayudarte?","Servicios y precios","¿Qué documentos necesito?","¿Dónde está mi trámite?","Hablar con una persona","Selecciona un servicio","Este servicio aún no tiene documentos registrados.","Inicia sesión para ver tus trámites.","Enviar mensaje al equipo","WhatsApp estará disponible próximamente."],
    fr:["Comment pouvons-nous vous aider ?","Services et tarifs","Quels documents fournir ?","Où en est ma démarche ?","Parler à une personne","Choisir un service","Aucun document encore indiqué.","Connectez-vous pour consulter vos démarches.","Écrire à l’équipe","WhatsApp sera bientôt disponible."]
  }[lang];
  const toggle=root.querySelector(".galiel-help-toggle"), panel=root.querySelector(".galiel-help-panel"),
        options=root.querySelector(".galiel-help-options"), output=root.querySelector(".galiel-help-output");
  root.querySelector(".galiel-help-intro").textContent=labels[0];
  root.querySelector(".galiel-help-close").addEventListener("click",()=>{
    panel.hidden=true;toggle.setAttribute("aria-expanded","false");toggle.focus();
  });
  toggle.addEventListener("click",()=>{
    panel.hidden=!panel.hidden;toggle.setAttribute("aria-expanded",String(!panel.hidden));
  });
  const url=(path)=>path+"?lang="+encodeURIComponent(lang);
  const renderLinks=(items)=>{
    output.replaceChildren();
    for(const item of items){const line=document.createElement("p");
      const a=document.createElement("a");a.textContent=item.label;a.href=item.href;
      line.appendChild(a);output.appendChild(line);
    }
  };
  async function loadJson(path){
    const response=await fetch(url(path),{credentials:"same-origin",headers:{"Accept":"application/json"}});
    if(!response.ok)throw new Error("Request unavailable");
    return response.json();
  }
  const choices=[
    async()=>renderLinks([{label:labels[1],href:"/services/"}]),
    async()=>{
      const data=await loadJson("/help/services/");
      const select=document.createElement("select");
      select.setAttribute("aria-label",labels[5]);
      const first=document.createElement("option");first.value="";first.textContent=labels[5];select.appendChild(first);
      for(const service of data.services){const op=document.createElement("option");op.value=service.id;op.textContent=service.title;select.appendChild(op);}
      output.replaceChildren(select);
      select.addEventListener("change",async()=>{
        if(!select.value)return;
        try{
          const result=await loadJson("/help/requirements/"+encodeURIComponent(select.value)+"/");
          output.replaceChildren(select);
          const list=document.createElement("ul");
          if(!result.requirements.length){const p=document.createElement("p");p.textContent=labels[6];output.appendChild(p);}
          else for(const req of result.requirements){const li=document.createElement("li");li.textContent=req.label+(req.required?" *":"");list.appendChild(li);}
          output.appendChild(list);
        }catch(_){output.textContent=labels[6];}
      });
    },
    async()=>{
      try{
        const data=await loadJson("/help/my-processes/");
        renderLinks(data.processes.map(x=>({label:x.reference+" · "+x.status,href:x.url})));
      }catch(_){renderLinks([{label:labels[7],href:"/login/"}]);}
    },
    async()=>{renderLinks([{label:labels[8],href:"/messages/"}]);const p=document.createElement("p");p.textContent=labels[9];output.appendChild(p);}
  ];
  for(let i=0;i<4;i++){const button=document.createElement("button");button.type="button";button.textContent=labels[i+1];
    button.addEventListener("click",async()=>{output.textContent="…";try{await choices[i]();}catch(_){output.textContent="Unavailable right now."}});
    options.appendChild(button);
  }
})();
