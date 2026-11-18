"""Small context-aware interface translations for the Galiel client portal.

No middleware or settings changes. Uses ?lang=, the galiel_lang cookie, then
the authenticated user's preferred language. Never accepts arbitrary locales.
"""
from django import template
from django.utils.html import format_html

register = template.Library()

PHRASES = {
  "Overview": ("Resumen", "Vue d’ensemble"),
  "My processes": ("Mis trámites", "Mes démarches"),
  "Services": ("Servicios", "Services"),
  "Documents": ("Documentos", "Documents"),
  "Invoices & payments": ("Facturas y pagos", "Factures et paiements"),
  "Messages": ("Mensajes", "Messages"),
  "My profile": ("Mi perfil", "Mon profil"),
  "YOUR WORKSPACE": ("TU ESPACIO", "VOTRE ESPACE"),
  "Sign out": ("Cerrar sesión", "Se déconnecter"),
  "Language": ("Idioma", "Langue"),
  "Service": ("Servicio", "Service"),
  "Your information": ("Tu información", "Vos informations"),
  "Review": ("Revisión", "Vérification"),
  "Payment": ("Pago", "Paiement"),
  "Confirmation": ("Confirmación", "Confirmation"),
  "Your service": ("Tu servicio", "Votre service"),
  "Price": ("Precio", "Prix"),
  "Estimated timeline": ("Plazo estimado", "Délai estimé"),
  "To be confirmed": ("Por confirmar", "À confirmer"),
  "Quote required": ("Cotización requerida", "Devis requis"),
  "Save & continue": ("Guardar y continuar", "Enregistrer et continuer"),
  "Continue": ("Continuar", "Continuer"),
  "Back": ("Atrás", "Retour"),
  "Edit": ("Editar", "Modifier"),
  "Your information is needed to continue.": ("Se necesita tu información para continuar.", "Vos informations sont nécessaires pour continuer."),
  "Comments or questions for our team": ("Comentarios o preguntas para nuestro equipo", "Commentaires ou questions pour notre équipe"),
  "This information is kept with your application.": ("Esta información se guarda con tu solicitud.", "Ces informations sont conservées avec votre demande."),
  "Required documents": ("Documentos requeridos", "Documents requis"),
  "Optional documents": ("Documentos opcionales", "Documents facultatifs"),
  "Add an optional document": ("Agregar un documento opcional", "Ajouter un document facultatif"),
  "Upload file": ("Subir archivo", "Téléverser le fichier"),
  "Replace file": ("Reemplazar archivo", "Remplacer le fichier"),
  "Delete": ("Eliminar", "Supprimer"),
  "Download": ("Descargar", "Télécharger"),
  "No required documents are configured for this service.": ("Este servicio aún no tiene documentos obligatorios configurados.", "Aucun document obligatoire n’est encore configuré pour ce service."),
  "You may still send optional supporting documents.": ("Aun así puedes enviar documentos de apoyo opcionales.", "Vous pouvez tout de même fournir des documents complémentaires facultatifs."),
  "Review your application": ("Revisa tu solicitud", "Vérifiez votre demande"),
  "Your information and comments": ("Tus datos y comentarios", "Vos informations et commentaires"),
  "Documents uploaded": ("Documentos cargados", "Documents téléversés"),
  "None provided": ("No se proporcionaron", "Aucun renseignement"),
  "Subtotal": ("Subtotal", "Sous-total"),
  "Applicable tax": ("Impuesto aplicable", "Taxe applicable"),
  "Total": ("Total", "Total"),
  "Payments are currently on hold.": ("Los pagos están suspendidos por el momento.", "Les paiements sont actuellement suspendus."),
  "Return to review": ("Volver a la revisión", "Retour à la vérification"),
  "Submit for a quote": ("Solicitar cotización", "Demander un devis"),
  "Accept & continue": ("Aceptar y continuar", "Accepter et continuer"),
  "Upload a PDF, JPG or PNG (maximum 10 MB).": ("Sube un PDF, JPG o PNG (máximo 10 MB).", "Téléversez un PDF, JPG ou PNG (10 Mo maximum)."),
  "Client information": ("Datos del cliente", "Informations du client"),
  "First name": ("Nombre", "Prénom"),
  "Last name": ("Apellido", "Nom"),
  "Email address": ("Correo electrónico", "Adresse e-mail"),
  "Phone number": ("Teléfono", "Téléphone"),
  "Company / legal name": ("Empresa / razón social", "Entreprise / raison sociale"),
  "Address": ("Domicilio", "Adresse"),
  "City": ("Ciudad", "Ville"),
  "Country": ("País", "Pays"),
  "Save changes": ("Guardar cambios", "Enregistrer les modifications"),
  "Edit my information": ("Editar mis datos", "Modifier mes informations"),
  "My account": ("Mi cuenta", "Mon compte"),
  "Your details": ("Tus datos", "Vos coordonnées"),
  "Account settings": ("Configuración de cuenta", "Paramètres du compte"),
  "Back to overview": ("Volver al resumen", "Retour à la vue d’ensemble"),
  "Start service": ("Iniciar trámite", "Démarrer la démarche"),
  "Explore services": ("Explorar servicios", "Explorer les services"),
  "Check your inbox": ("Revisa tu correo", "Vérifiez votre messagerie"),
  "Welcome back": ("Te damos la bienvenida", "Bon retour"),
  "Sign in": ("Iniciar sesión", "Se connecter"),
  "Create an account": ("Crear una cuenta", "Créer un compte"),
  "Everything in its right place.": ("Todo en su lugar.", "Tout à sa place."),
  "Your client space": ("Tu espacio de cliente", "Votre espace client"),
}

def get_locale(context):
    request = context.get("request")
    if request is None:
        return "en"
    value = request.GET.get("lang") or request.COOKIES.get("galiel_lang")
    if not value and getattr(request.user, "is_authenticated", False):
        try:
            value = request.user.profile.preferred_language
        except (AttributeError, Exception):
            value = None
    return value if value in ("en", "es", "fr") else "en"

@register.simple_tag(takes_context=True)
def galiel_locale(context):
    return get_locale(context)

@register.simple_tag(takes_context=True)
def ui(context, phrase):
    language = get_locale(context)
    if language == "en":
        return phrase
    translations = PHRASES.get(str(phrase))
    return translations[0 if language == "es" else 1] if translations else phrase
