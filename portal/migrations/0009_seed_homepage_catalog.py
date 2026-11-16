"""Seed the actual homepage-advertised catalog as quotation-only offerings.

No unverified price or government processing estimate is asserted.
Records remain fully editable in Django Admin.
"""
from django.db import migrations


REGIONS = [
    ("MX", "nuevo-leon", "Nuevo León"),
    ("MX", "ciudad-de-mexico", "Ciudad de México"),
    ("MX", "queretaro", "Querétaro"),
    ("MX", "jalisco", "Jalisco"),
    ("MX", "colima", "Colima"),
    ("MX", "tamaulipas", "Tamaulipas"),
    ("US", "texas", "Texas"),
]
MUNICIPALITIES = [
    ("nuevo-leon", "monterrey", "Monterrey"),
    ("nuevo-leon", "san-pedro-garza-garcia", "San Pedro Garza García"),
    ("ciudad-de-mexico", "benito-juarez", "Benito Juárez"),
    ("ciudad-de-mexico", "cuauhtemoc", "Cuauhtémoc"),
    ("queretaro", "santiago-de-queretaro", "Santiago de Querétaro"),
    ("jalisco", "guadalajara", "Guadalajara"),
    ("colima", "colima", "Colima"),
    ("tamaulipas", "reynosa", "Reynosa"),
]
# code, country, region, municipality, English, Spanish, French
OFFERINGS = [
    ("nl-monterrey-licencia-funcionamiento", "MX", "nuevo-leon", "monterrey", "Business operating permit", "Licencia de funcionamiento", "Permis d'exploitation"),
    ("nl-monterrey-uso-suelo", "MX", "nuevo-leon", "monterrey", "Land-use authorization", "Uso de suelo", "Autorisation d'urbanisme"),
    ("nl-monterrey-construccion", "MX", "nuevo-leon", "monterrey", "Construction permit", "Licencia de construcción", "Permis de construire"),
    ("nl-sanpedro-uso-suelo", "MX", "nuevo-leon", "san-pedro-garza-garcia", "Land-use authorization", "Licencia de uso de suelo", "Autorisation d'urbanisme"),
    ("nl-sanpedro-construccion-nueva", "MX", "nuevo-leon", "san-pedro-garza-garcia", "New construction permit", "Construcción de obra nueva", "Permis de construction neuve"),
    ("cdmx-bj-establecimiento", "MX", "ciudad-de-mexico", "benito-juarez", "Business establishment filing", "Establecimiento mercantil", "Déclaration d'établissement commercial"),
    ("cdmx-cuauhtemoc-establecimiento", "MX", "ciudad-de-mexico", "cuauhtemoc", "Business establishment filing", "Establecimiento mercantil", "Déclaration d'établissement commercial"),
    ("qro-qro-funcionamiento", "MX", "queretaro", "santiago-de-queretaro", "Business operating permit", "Licencia de funcionamiento", "Permis d'exploitation"),
    ("qro-qro-sare", "MX", "queretaro", "santiago-de-queretaro", "Rapid business opening (SARE)", "Apertura rápida (SARE)", "Ouverture accélérée (SARE)"),
    ("jal-gdl-giro-a", "MX", "jalisco", "guadalajara", "Type A business license", "Licencia de giro Tipo A", "Licence commerciale de type A"),
    ("col-funcionamiento", "MX", "colima", "colima", "Municipal operating permit", "Licencia municipal de funcionamiento", "Permis d'exploitation municipal"),
    ("tam-reynosa-funcionamiento", "MX", "tamaulipas", "reynosa", "Business operating permit", "Licencia de funcionamiento", "Permis d'exploitation"),
    ("tx-notarization", "US", "texas", "", "Notarization assistance", "Asistencia para notarización", "Assistance à la notarisation"),
    ("tx-apostille", "US", "texas", "", "Apostille coordination", "Coordinación de apostillas", "Coordination des apostilles"),
    ("tx-translation", "US", "texas", "", "Professional translations", "Traducciones profesionales", "Traductions professionnelles"),
    ("tx-entity-filing", "US", "texas", "", "Selected business filings", "Trámites empresariales seleccionados", "Formalités d'entreprise sélectionnées"),
    ("fr-translation", "FR", "", "", "Translations", "Traducciones", "Traductions"),
    ("fr-apostille-legalization", "FR", "", "", "Apostille / legalization coordination", "Coordinación de apostillas y legalizaciones", "Coordination apostille / légalisation"),
    ("fr-admin-review", "FR", "", "", "Administrative process review", "Revisión de trámites administrativos", "Examen des démarches administratives"),
]


def seed(apps, schema_editor):
    Country = apps.get_model("portal", "CatalogCountry")
    Region = apps.get_model("portal", "CatalogRegion")
    Municipality = apps.get_model("portal", "CatalogMunicipality")
    Service = apps.get_model("portal", "CatalogService")
    Offering = apps.get_model("portal", "ServiceOffering")
    for country_code, slug, title in REGIONS:
        country = Country.objects.get(pk=country_code)
        Region.objects.get_or_create(country=country, slug=slug,
                                     defaults={"name_en": title, "name_es": title, "name_fr": title})
    for region_slug, slug, title in MUNICIPALITIES:
        region = Region.objects.get(country_id="MX", slug=region_slug)
        Municipality.objects.get_or_create(region=region, slug=slug,
                                           defaults={"name_en": title, "name_es": title, "name_fr": title})
    for code, country_code, region_slug, municipality_slug, en, es, fr in OFFERINGS:
        service, _ = Service.objects.get_or_create(slug=code, defaults={
            "title_en": en, "title_es": es, "title_fr": fr
        })
        region = Region.objects.filter(country_id=country_code, slug=region_slug).first() if region_slug else None
        municipality = (Municipality.objects.filter(region=region, slug=municipality_slug).first()
                        if municipality_slug else None)
        Offering.objects.get_or_create(
            service=service, country_id=country_code, region=region, municipality=municipality,
            defaults={"price_type": "quote", "price": None, "currency": {
                "MX": "MXN", "US": "USD", "FR": "EUR",
            }[country_code], "is_published": True},
        )


class Migration(migrations.Migration):
    dependencies = [("portal", "0008_seed_countries")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
