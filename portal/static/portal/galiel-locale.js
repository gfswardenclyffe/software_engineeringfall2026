/* Galiel EN/ES/FR shared interface localization.
 * Complements Django's server-rendered translations without modifying settings.
 * Text map applies to standalone legacy pages as well as the shared shells.
 * Never alters form values, client data, message bodies, or monetary amounts.
 */
(() => {
  "use strict";
  const dictionaries = {
    es: {
      "Welcome back.":"Bienvenido de nuevo.","Sign in":"Iniciar sesión",
      "Sign in →":"Iniciar sesión →","Create an account":"Crear cuenta",
      "Create an account →":"Crear cuenta →",
      "Your client space / Sign in":"Tu espacio / Iniciar sesión",
      "Your client space":"Tu espacio de cliente",
      "New account / Step 1 of 2":"Nueva cuenta / Paso 1 de 2",
      "New account / Step 2 of 2":"Nueva cuenta / Paso 2 de 2",
      "Let's get started.":"Comencemos.","Check your inbox.":"Revisa tu correo.",
      "Account recovery":"Recuperar cuenta","Reset your password.":"Restablece tu contraseña.",
      "Choose a new password.":"Elige una contraseña nueva.",
      "You're all set.":"Todo listo.","Save new password":"Guardar contraseña",
      "Your private place to manage services, documents, and updates.":"Tu espacio privado para gestionar trámites, documentos y novedades.",
      "Overview":"Resumen","My processes":"Mis trámites","Services":"Servicios",
      "Documents":"Documentos","Invoices & payments":"Facturas y pagos","Messages":"Mensajes",
      "My profile":"Mi perfil","Sign out":"Cerrar sesión","YOUR WORKSPACE":"TU ESPACIO",
      "My account / Edit profile":"Mi cuenta / Editar perfil",
      "Your details.":"Tus datos.","Account & privacy":"Cuenta y privacidad",
      "Edit my information ↗":"Editar mis datos ↗","Manage my details":"Administrar mis datos",
      "Save changes →":"Guardar cambios →","← Cancel and return to profile":"← Cancelar y volver al perfil",
      "First name":"Nombre","Last name":"Apellido","Email":"Correo electrónico",
      "Email address":"Correo electrónico","Phone":"Teléfono","Phone number":"Teléfono",
      "Preferred language":"Idioma preferido","Country":"País","City":"Ciudad",
      "Tax ID (if applicable)":"Identificación fiscal (si corresponde)",
      "Company / legal name":"Empresa / razón social","Address":"Domicilio",
      "Street":"Calle","Street number":"Número exterior",
      "Apartment / Suite":"Departamento / oficina","ZIP / Postal code":"Código postal",
      "State / Province / Region":"Estado / provincia / región",
      "Your information":"Tu información","Required documents":"Documentos requeridos",
      "Optional documents":"Documentos opcionales","Review your application":"Revisa tu solicitud",
      "Upload file":"Subir archivo","Save & continue":"Guardar y continuar",
      "← Back":"← Atrás","Continue →":"Continuar →","Price":"Precio",
      "Quote required":"Cotización requerida","Estimated timeline":"Plazo estimado",
      "To be confirmed":"Por confirmar","Your service":"Tu servicio",
      "Business size":"Superficie del negocio","Start service →":"Iniciar trámite →",
      "View details":"Ver detalles","Delete":"Eliminar","Edit":"Editar",
      "Administration process review":"Revisión de trámite administrativo",
      "Administrative process review":"Revisión de trámite administrativo",
      "No additional service questions are configured yet.":"Aún no hay preguntas adicionales configuradas.",
      "No required documents are configured for this service.":"Este servicio aún no tiene documentos obligatorios configurados.",
      "No conversations yet.":"Aún no hay conversaciones.",
      "Your conversations":"Tus conversaciones","Client conversations":"Conversaciones con clientes",
      "New message to Wardenclyffe":"Nuevo mensaje a Wardenclyffe",
      "Send message":"Enviar mensaje","Send reply":"Enviar respuesta",
      "Subject":"Asunto","Message":"Mensaje","Your message":"Tu mensaje",
      "Back to overview":"Volver al resumen","← Back to overview":"← Volver al resumen",
      "Back to Documents":"Volver a documentos","Upload a document":"Subir un documento",
      "Document title":"Título del documento","Choose PDF":"Seleccionar PDF",
      "Upload document":"Subir documento",
      "Account settings / 01":"Configuración de cuenta / 01",
      "Account & assistance":"Cuenta y asistencia",
      "Need help?":"¿Necesitas ayuda?","Open my profile →":"Abrir mi perfil →",
      "Your processes":"Tus trámites","Start a new service →":"Iniciar otro trámite →",
      "Your information, all in one place. Keep it current so we can serve you better.":"Tus datos en un solo lugar. Mantenlos actualizados.",
      "Signed in securely":"Sesión iniciada de forma segura",
      "Member since":"Miembro desde","Required":"Obligatorio","Optional":"Opcional",
      "Draft":"Borrador","Submitted to authority":"Presentado ante la autoridad",
      "In process":"En trámite","Under review":"En revisión",
      "Track":"Seguimiento","Review":"Revisión","Payment":"Pago",
      "Confirmation":"Confirmación","Continue":"Continuar","Service":"Servicio"
    },
    fr: {
      "Welcome back.":"Bon retour.","Sign in":"Se connecter",
      "Sign in →":"Se connecter →","Create an account":"Créer un compte",
      "Create an account →":"Créer un compte →",
      "Your client space / Sign in":"Espace client / Connexion",
      "Your client space":"Votre espace client",
      "New account / Step 1 of 2":"Nouveau compte / Étape 1 sur 2",
      "New account / Step 2 of 2":"Nouveau compte / Étape 2 sur 2",
      "Let's get started.":"Commençons.","Check your inbox.":"Consultez vos e-mails.",
      "Account recovery":"Récupération du compte","Reset your password.":"Réinitialisez votre mot de passe.",
      "Choose a new password.":"Choisissez un nouveau mot de passe.",
      "You're all set.":"Tout est prêt.","Save new password":"Enregistrer le nouveau mot de passe",
      "Your private place to manage services, documents, and updates.":"Votre espace privé pour gérer vos démarches, documents et mises à jour.",
      "Overview":"Vue d’ensemble","My processes":"Mes démarches","Services":"Services",
      "Documents":"Documents","Invoices & payments":"Factures et paiements","Messages":"Messages",
      "My profile":"Mon profil","Sign out":"Se déconnecter","YOUR WORKSPACE":"VOTRE ESPACE",
      "My account / Edit profile":"Mon compte / Modifier le profil",
      "Your details.":"Vos coordonnées.","Account & privacy":"Compte et confidentialité",
      "Edit my information ↗":"Modifier mes informations ↗","Manage my details":"Gérer mes coordonnées",
      "Save changes →":"Enregistrer →","← Cancel and return to profile":"← Annuler et revenir au profil",
      "First name":"Prénom","Last name":"Nom","Email":"E-mail",
      "Email address":"Adresse e-mail","Phone":"Téléphone","Phone number":"Numéro de téléphone",
      "Preferred language":"Langue préférée","Country":"Pays","City":"Ville",
      "Tax ID (if applicable)":"Identifiant fiscal (le cas échéant)",
      "Company / legal name":"Entreprise / raison sociale","Address":"Adresse",
      "Street":"Rue","Street number":"Numéro de rue",
      "Apartment / Suite":"Appartement / bureau","ZIP / Postal code":"Code postal",
      "State / Province / Region":"État / province / région",
      "Your information":"Vos informations","Required documents":"Documents requis",
      "Optional documents":"Documents facultatifs","Review your application":"Vérifiez votre demande",
      "Upload file":"Téléverser le fichier","Save & continue":"Enregistrer et continuer",
      "← Back":"← Retour","Continue →":"Continuer →","Price":"Prix",
      "Quote required":"Devis requis","Estimated timeline":"Délai estimé",
      "To be confirmed":"À confirmer","Your service":"Votre service",
      "Business size":"Surface du local","Start service →":"Démarrer la démarche →",
      "View details":"Voir les détails","Delete":"Supprimer","Edit":"Modifier",
      "Administrative process review":"Examen d'une démarche administrative",
      "No additional service questions are configured yet.":"Aucune question supplémentaire n’est configurée.",
      "No required documents are configured for this service.":"Aucun document obligatoire n’est encore configuré pour ce service.",
      "No conversations yet.":"Aucune conversation pour le moment.",
      "Your conversations":"Vos conversations","Client conversations":"Conversations clients",
      "New message to Wardenclyffe":"Nouveau message à Wardenclyffe",
      "Send message":"Envoyer","Send reply":"Envoyer la réponse",
      "Subject":"Objet","Message":"Message","Your message":"Votre message",
      "Back to overview":"Retour à la vue d’ensemble","← Back to overview":"← Retour à la vue d’ensemble",
      "Back to Documents":"Retour aux documents","Upload a document":"Téléverser un document",
      "Document title":"Titre du document","Choose PDF":"Choisir un PDF",
      "Upload document":"Téléverser",
      "Account settings / 01":"Paramètres du compte / 01",
      "Account & assistance":"Compte et assistance",
      "Need help?":"Besoin d’aide ?","Open my profile →":"Ouvrir mon profil →",
      "Your processes":"Vos démarches","Start a new service →":"Démarrer une nouvelle démarche →",
      "Your information, all in one place. Keep it current so we can serve you better.":"Vos coordonnées réunies en un seul endroit. Gardez-les à jour.",
      "Signed in securely":"Connexion sécurisée",
      "Member since":"Membre depuis","Required":"Obligatoire","Optional":"Facultatif",
      "Draft":"Brouillon","Submitted to authority":"Déposé auprès de l’autorité",
      "In process":"En cours","Under review":"En cours d’examen",
      "Track":"Suivi","Review":"Vérification","Payment":"Paiement",
      "Confirmation":"Confirmation","Continue":"Continuer","Service":"Service"
    }
  };
  function readCookie() {
    const part = document.cookie.split(";").map(x=>x.trim()).find(x=>x.startsWith("galiel_lang="));
    return part ? decodeURIComponent(part.split("=")[1]) : "";
  }
  const q = new URLSearchParams(location.search);
  const requested = q.get("lang");
  const language = ["en","es","fr"].includes(requested) ? requested :
    (["en","es","fr"].includes(readCookie()) ? readCookie() : document.documentElement.lang);
  if (!["en","es","fr"].includes(language)) return;
  document.documentElement.lang = language;
  for (const a of document.querySelectorAll('a[lang][href*="lang="]')) {
    a.setAttribute("aria-current",a.lang===language?"page":"false");
    a.addEventListener("click",()=>{document.cookie="galiel_lang="+a.lang+"; Path=/; Max-Age=31536000; Secure; SameSite=Lax"});
  }
  if(language==="en")return;
  const map=dictionaries[language];
  const excluded=new Set(["SCRIPT","STYLE","NOSCRIPT","TEXTAREA","CODE","PRE"]);
  function translateNode(node) {
    if(!node || !node.parentElement)return;
    let parent=node.parentElement;
    if(excluded.has(parent.tagName) || parent.closest("[data-no-translate], .ws-identity, .galiel-info-grid, .galiel-doc-row .client-data"))return;
    const original=node.nodeValue;
    const trim=original.trim();
    if(!trim || !Object.prototype.hasOwnProperty.call(map,trim))return;
    node.nodeValue=original.replace(trim,map[trim]);
  }
  function apply(root){
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    let node;while((node=walker.nextNode()))translateNode(node);
  }
  apply(document.body);
  // Keep dynamic service cards translated when applicable.
  const observer=new MutationObserver(records=>{
    for(const rec of records)for(const node of rec.addedNodes)
      if(node.nodeType===Node.TEXT_NODE)translateNode(node);
      else if(node.nodeType===Node.ELEMENT_NODE)apply(node);
  });
  observer.observe(document.body,{childList:true,subtree:true});
})();
