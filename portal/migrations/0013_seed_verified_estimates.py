"""Conservative, explicitly provisional pricing: 9 source-supported introductory offers.

This data migration never overwrites a manager's existing pricing, deposits or timelines.
Other offers remain quote-only and flagged for review; source coverage has been logged.
Amounts are provisional working proposals, not approved customer quotes.
"""
from datetime import date
from decimal import Decimal
from django.db import migrations

DATE = date(2026, 11, 15)
ROWS = [["nl-monterrey-licencia-funcionamiento",None,None,None,None,None,"business permit depends on activity and municipal requirements","https://www.monterrey.gob.mx/"],["nl-monterrey-uso-suelo",None,None,None,None,None,"land use depends on zone, floor area, land use classification","https://www.monterrey.gob.mx/"],["nl-monterrey-construccion",None,None,25,45,None,"Variable by m² and project; provider offers permit management MXN 12000, excluding municipal fees; do not invent a project government fee.","https://truimedificaciones.net/producto/gestion-de-licencia-de-construccion"],["nl-sanpedro-uso-suelo",None,None,None,None,None,"zone and project-dependent; await official rights table","https://www.sanpedro.gob.mx/"],["nl-sanpedro-construccion-nueva",None,None,25,60,None,"Variable by area, construction classification and project; market fee MXN 12000 for management (excludes government)","https://truimedificaciones.net/producto/gestion-de-licencia-de-construccion"],["cdmx-bj-establecimiento",0,3500,2,7,"per low-impact notice","Only low-impact SIAPEM notice is free; additional zoning, safety, sanitation authorizations are not included","https://www.sedeco.cdmx.gob.mx/tramites/aviso-para-el-funcionamiento-de-establecimientos-mercantiles-con-giro-de-bajo-impacto"],["cdmx-cuauhtemoc-establecimiento",0,3500,2,7,"per low-impact notice","Only low-impact SIAPEM notice is free; additional authorizations excluded","https://www.sedeco.cdmx.gob.mx/tramites/aviso-para-el-funcionamiento-de-establecimientos-mercantiles-con-giro-de-bajo-impacto"],["qro-qro-funcionamiento",None,None,None,None,None,"government fee depends on classification, site and type of license; no verified local entry tariff","https://tramitesqro.municipiodequeretaro.gob.mx/"],["qro-qro-sare",None,None,None,None,None,"SARE is restricted to eligible low-risk activities; confirm precise SARE tariff and site inspection","https://tramitesqro.municipiodequeretaro.gob.mx/"],["jal-gdl-giro-a",675,3500,3,10,"per standard type A license","Municipal official MXN 618 issue plus MXN 57 form; market management listing from MXN 3500; extra fees possible","https://tramitesdigitales.guadalajara.gob.mx/detalle/Licencia-de-Giro-Tipo-A/379/informacion"],["col-funcionamiento",None,None,None,None,None,"Colima SARE listed on gov.mx but stated fee 207.48 (UMA) ambiguous; do not interpret as MXN without validation","https://www.gob.mx/public/tramites/detalleTramite.xhtml?homoclave=TM-2022-8228-003-A"],["tam-reynosa-funcionamiento",None,None,None,None,None,"missing verified municipality-specific current fee schedule","https://www.reynosa.gob.mx/"],["tx-notarization",10,30,1,5,"per one standard acknowledgment","Texas statute caps the notarial acknowledgment first signature at USD 10; optional separate coordination fee estimated USD 30; no additional notarial fee beyond cap.","https://www.sos.texas.gov/statdoc/edinfo.shtml"],["tx-apostille",15,100,5,15,"per document","Texas SOS apostille USD 15/document; handling coordination fee proposed USD 100, couriers extra","https://www.sos.texas.gov/authfaqs.shtml"],["tx-translation",0,45,2,6,"per standard page (up to 250 words)","Professional translation is a private service; no uniform government filing fee; provider USD 30–39/page","https://www.uslanguageservices.com/texas/"],["tx-entity-filing",300,150,10,20,"per standard domestic LLC formation","Standard Texas LLC certificate of formation USD 300 government; estimated USD 150 filing assistance; other entity types/agents excluded","https://www.sos.texas.gov/corp/instructions/205.shtml"],["fr-translation",0,59,3,7,"per standard page (250 words)","No fixed government fee for private certified translations; market €39–90+/page depending on language and document","https://transdoc.fr/page/tarifs-traduction-assermentee/"],["fr-apostille-legalization",10,70,4,10,"per individual document","Individuals up to 3 ordinary apostilles €10 before VAT; legal entities €20 before VAT. Estimate excludes tax and postage; review applicant type.","https://www.service-public.gouv.fr/particuliers/vosdroits/F1400"],["fr-admin-review",None,None,None,None,None,"Complex administrative consultation; authority and review scope differ; no single official fee","https://www.service-public.gouv.fr/"]]
MARKET = [["cdmx-bj-establecimiento","https://mexicoderecho.org/abogados/acta-de-funcionamiento-en-mexico-requisitos-tramite-y-todo-lo-que-debes-saber-para-obtenerla/",2000,4000,"Private gestoría MXN 2000–4000 indicated for CDMX; the official low-impact notice itself is free."],["cdmx-cuauhtemoc-establecimiento","https://mexicoderecho.org/abogados/acta-de-funcionamiento-en-mexico-requisitos-tramite-y-todo-lo-que-debes-saber-para-obtenerla/",2000,4000,"Private gestoría MXN 2000–4000; official low-impact notice free."],["jal-gdl-giro-a","https://contalia.mx/perfil/hector-manuel-rios-guadalajara",3500,None,"Guadalajara gestor advertises management starting MXN 3500, separate government fees unspecified."],["nl-monterrey-construccion","https://truimedificaciones.net/producto/gestion-de-licencia-de-construccion",12000,12000,"Quoted MXN 12000 management service, government rights excluded."],["nl-sanpedro-construccion-nueva","https://truimedificaciones.net/producto/gestion-de-licencia-de-construccion",12000,12000,"Quoted MXN 12000 management service, government rights excluded."],["tx-notarization","https://accordandink.com/pricing",10,39,"Texas statutory notarial act fee USD 10 and provider notarization/coordination examples; service-fee portion separate."],["tx-apostille","https://www.apostilleservices.com/texas-apostille/",75,255,"Texas apostille provider advertises as low as USD 75 with premium packages USD 255; check scope of governmental fee inclusion."],["tx-translation","https://accordandink.com/pricing",30,45,"Certified translation USD 30 per standard page, rush USD 45."],["tx-entity-filing","https://www.txregisteredagent.org/pricing/",199,199,"Texas LLC filing assistance provider lists USD 199 service fee excluding filing fees."],["fr-translation","https://transdoc.fr/page/tarifs-traduction-assermentee/",39,90,"Certified translation priced from EUR 39 per page; variation by language."],["fr-apostille-legalization","https://www.notaires.fr/fr/actualites/apostille-et-legalisation",None,None,"No comparable private coordination service price verified; government fee tariff is not a provider market range."]]

def seed(apps, schema_editor):
    Service = apps.get_model("portal", "CatalogService")
    Offering = apps.get_model("portal", "ServiceOffering")
    Research = apps.get_model("portal", "OfferingPriceResearch")
    for slug, gov, service_fee, days_min, days_max, unit, note, official_url in ROWS:
        offering = Offering.objects.filter(service__slug=slug).first()
        if offering is None:
            continue
        # Record research even where the correct result is "quotation required".
        Research.objects.get_or_create(
            offering=offering, source_kind="government",
            source_url=official_url, checked_on=DATE,
            defaults={
                "source_title": "2026 authority/procedure reference" if gov is not None else "Authority reference — fee verification needed",
                "currency": offering.currency,
                "government_fee": Decimal(str(gov)) if gov is not None else None,
                "fee_unit": unit or "",
                "research_notes": note,
                "verified": False,
            },
        )
        if gov is not None and service_fee is not None and offering.price_type == "quote" and offering.price is None:
            offering.price_type = "starting"
            offering.price = Decimal(str(gov)) + Decimal(str(service_fee))
            offering.government_fee_estimate = Decimal(str(gov))
            offering.service_fee_estimate = Decimal(str(service_fee))
            offering.price_unit = unit
            offering.is_temporary_price = True
            offering.pricing_review_required = True
            offering.estimated_min_business_days = days_min
            offering.estimated_max_business_days = days_max
            offering.save(update_fields=["price_type", "price", "government_fee_estimate",
              "service_fee_estimate", "price_unit", "is_temporary_price", "pricing_review_required",
              "estimated_min_business_days", "estimated_max_business_days"])
        elif gov is None and days_min and offering.estimated_min_business_days is None:
            offering.estimated_min_business_days = days_min
            offering.estimated_max_business_days = days_max
            offering.pricing_review_required = True
            offering.save(update_fields=["estimated_min_business_days","estimated_max_business_days","pricing_review_required"])
    for slug, url, low, high, notes in MARKET:
        offering = Offering.objects.filter(service__slug=slug).first()
        if offering is None:
            continue
        Research.objects.get_or_create(offering=offering, source_kind="market", source_url=url, checked_on=DATE,
            defaults={"source_title": "Published provider market reference", "currency": offering.currency,
                "market_low": Decimal(str(low)) if low is not None else None,
                "market_high": Decimal(str(high)) if high is not None else None,
                "research_notes": notes, "verified": False})

class Migration(migrations.Migration):
    dependencies = [("portal", "0012_pricing_research")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
