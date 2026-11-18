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

  const longerStrings = {
    es: {
      "Sign in to access your account, documents, and service updates.":"Inicia sesión para acceder a tus datos, documentos y actualizaciones.",
      "Forgot your password?":"¿Olvidaste tu contraseña?",
      "New to Galiel?":"¿Aún no tienes cuenta?",
      "← Back to Galiel":"← Volver a Galiel",
      "Create your client account. We'll email you a confirmation link before you can access your private workspace.":"Crea tu cuenta. Te enviaremos un enlace de confirmación por correo antes de acceder a tu espacio privado.",
      "Create account and send confirmation →":"Crear cuenta y enviar confirmación →",
      "We verify your email before activating the account. Phone verification is not yet enabled; your phone number is used only as contact information.":"Verificamos tu correo antes de activar tu cuenta. El teléfono solo se usa como dato de contacto.",
      "Already registered?":"¿Ya tienes cuenta?",
      "For security, unconfirmed accounts cannot sign in. Verification links expire after 24 hours.":"Por seguridad, las cuentas sin confirmar no pueden iniciar sesión. Los enlaces vencen a las 24 horas.",
      "Need a new link?":"¿Necesitas otro enlace?",
      "Resend confirmation":"Reenviar confirmación",
      "Already confirmed? Sign in":"¿Ya confirmaste? Inicia sesión",
      "Account confirmation":"Confirmación de cuenta",
      "Link unavailable.":"Enlace no disponible.",
      "This confirmation link is invalid, expired, or already used. You can request a fresh link below.":"Este enlace no es válido, venció o ya fue utilizado. Puedes solicitar uno nuevo.",
      "Request a new link":"Solicitar enlace nuevo",
      "Back to sign in":"Volver a iniciar sesión",
      "Enter your account email. If an active account exists, we'll send a recovery link.":"Escribe tu correo. Si existe una cuenta activa, enviaremos un enlace de recuperación.",
      "Send reset link":"Enviar enlace de recuperación",
      "Your password has been updated. You can now sign in.":"Tu contraseña se actualizó. Ya puedes iniciar sesión.",
      "Your workspace is ready.":"Tu espacio está listo.",
      "No processes yet. Choose a service and save your application as a draft.":"Aún no tienes trámites. Elige un servicio y guarda la solicitud como borrador.",
      "Your profile stores the contact details you provided when registering. You can review or update them at any time.":"Tu perfil guarda los datos de contacto de tu registro. Puedes revisarlos o actualizarlos cuando quieras.",
      "Resume a saved draft, respond to a quotation, or follow an active process.":"Continúa un borrador, responde a una cotización o consulta un trámite activo.",
      "Explore within your workspace":"Explora servicios desde tu espacio",
      "Find services by location, review published fees and estimates, and start a saved application without leaving your workspace.":"Busca servicios por ubicación, revisa precios y comienza una solicitud sin salir de tu espacio.",
      "Your information, all in one place. Keep it current so we can serve you better.":"Tus datos en un solo lugar. Mantenlos actualizados para brindarte un mejor servicio.",
      "Only you and authorized Wardenclyffe personnel should have access to your client information.":"Solo tú y el personal autorizado de Wardenclyffe deben poder consultar tus datos.",
      "Update your contact and billing details anytime using the Edit button. Password changes are managed separately for security.":"Actualiza tus datos de contacto y facturación con Editar. Los cambios de contraseña se gestionan por separado.",
      "Update the information Wardenclyffe uses to contact you about your services.":"Actualiza los datos que Wardenclyffe utiliza para comunicarse contigo.",
      "Messages are saved in Galiel so you can return to your conversation at any time.":"Los mensajes se guardan en Galiel para que puedas consultar tus conversaciones.",
      "PDF files up to 10 MB. Only you and authorized administrators can access documents you upload.":"PDF de hasta 10 MB. Solo tú y los administradores autorizados pueden acceder a los archivos.",
      "Your files stay private. Only documents requested for this process can be uploaded here.":"Tus archivos son privados. Aquí puedes subir los documentos solicitados.",
      "No documents uploaded yet.":"Todavía no hay documentos cargados."
    },
    fr: {
      "Sign in to access your account, documents, and service updates.":"Connectez-vous pour accéder à votre compte, vos documents et vos mises à jour.",
      "Forgot your password?":"Mot de passe oublié ?",
      "New to Galiel?":"Vous découvrez Galiel ?",
      "← Back to Galiel":"← Retour à Galiel",
      "Create your client account. We'll email you a confirmation link before you can access your private workspace.":"Créez votre compte. Nous vous enverrons un lien de confirmation avant l’accès à votre espace privé.",
      "Create account and send confirmation →":"Créer le compte et envoyer la confirmation →",
      "We verify your email before activating the account. Phone verification is not yet enabled; your phone number is used only as contact information.":"Nous vérifions votre adresse e-mail avant l’activation. Le téléphone sert uniquement aux échanges.",
      "Already registered?":"Déjà inscrit ?",
      "For security, unconfirmed accounts cannot sign in. Verification links expire after 24 hours.":"Pour votre sécurité, les comptes non confirmés ne peuvent pas se connecter. Les liens expirent après 24 heures.",
      "Need a new link?":"Besoin d’un nouveau lien ?",
      "Resend confirmation":"Renvoyer la confirmation",
      "Already confirmed? Sign in":"Déjà confirmé ? Se connecter",
      "Account confirmation":"Confirmation du compte",
      "Link unavailable.":"Lien indisponible.",
      "This confirmation link is invalid, expired, or already used. You can request a fresh link below.":"Ce lien est invalide, expiré ou déjà utilisé. Vous pouvez en demander un nouveau.",
      "Request a new link":"Demander un nouveau lien",
      "Back to sign in":"Retour à la connexion",
      "Enter your account email. If an active account exists, we'll send a recovery link.":"Saisissez votre adresse e-mail. Si le compte est actif, nous enverrons un lien de récupération.",
      "Send reset link":"Envoyer le lien de réinitialisation",
      "Your password has been updated. You can now sign in.":"Votre mot de passe a été modifié. Vous pouvez vous connecter.",
      "Your workspace is ready.":"Votre espace est prêt.",
      "No processes yet. Choose a service and save your application as a draft.":"Aucune démarche pour le moment. Choisissez un service et enregistrez votre demande en brouillon.",
      "Your profile stores the contact details you provided when registering. You can review or update them at any time.":"Votre profil conserve vos coordonnées. Vous pouvez les consulter ou les modifier à tout moment.",
      "Resume a saved draft, respond to a quotation, or follow an active process.":"Reprenez un brouillon, répondez à un devis ou suivez une démarche en cours.",
      "Explore within your workspace":"Explorez les services dans votre espace",
      "Find services by location, review published fees and estimates, and start a saved application without leaving your workspace.":"Recherchez des services par région, consultez les tarifs et commencez une demande depuis votre espace.",
      "Your information, all in one place. Keep it current so we can serve you better.":"Vos informations réunies au même endroit. Tenez-les à jour.",
      "Only you and authorized Wardenclyffe personnel should have access to your client information.":"Seuls vous et le personnel autorisé de Wardenclyffe doivent avoir accès à vos données.",
      "Update your contact and billing details anytime using the Edit button. Password changes are managed separately for security.":"Modifiez vos coordonnées et informations de facturation à l’aide du bouton Modifier. Les mots de passe sont gérés séparément.",
      "Update the information Wardenclyffe uses to contact you about your services.":"Modifiez les informations utilisées par Wardenclyffe pour vous contacter.",
      "Messages are saved in Galiel so you can return to your conversation at any time.":"Les messages sont conservés dans Galiel pour vous permettre de retrouver vos échanges.",
      "PDF files up to 10 MB. Only you and authorized administrators can access documents you upload.":"PDF de 10 Mo maximum. Seuls vous et les administrateurs autorisés peuvent accéder à vos fichiers.",
      "Your files stay private. Only documents requested for this process can be uploaded here.":"Vos fichiers restent privés. Vous pouvez y téléverser les documents demandés.",
      "No documents uploaded yet.":"Aucun document téléversé."
    }
  };
  Object.assign(dictionaries.es, longerStrings.es);
  Object.assign(dictionaries.fr, longerStrings.fr);

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
