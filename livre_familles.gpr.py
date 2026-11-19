# Copyright (C) 2026 Pierre Laminette (geoglorus)
#
# Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou le
# modifier selon les termes de la Licence Publique Générale GNU telle que
# publiée par la Free Software Foundation, soit la version 3 de la licence,
# soit (à votre option) toute version ultérieure.
#
# Ce programme est distribué dans l'espoir qu'il sera utile, mais SANS AUCUNE
# GARANTIE ; sans même la garantie implicite de COMMERCIALISATION ou
# D'ADÉQUATION À UN USAGE PARTICULIER. Consultez la Licence Publique Générale
# GNU pour plus de détails.
#
# Assistance au développement et à la mise au point réalisée avec l'aide
# d'une intelligence artificielle (Gemini).

register(
    REPORT,
    id="LivreFamilles",
    name=_("Livre des Familles"),
    description=_(
        "Génère un livre des familles structuré avec index et options de filtrage."
        "(export TXT, ODT, HTML, PDF)."
    ),
    version="1.0.0",
    gramps_target_version="6.0",
    status=STABLE,
    fname="livre_familles.py",
    authors=["Pierre Laminette (geoglorus)"],
    authors_email=[""],
    category=CATEGORY_TEXT,
    reportclass="LivreFamillesReport",
    optionclass="LivreFamillesOptions",
    report_modes=[REPORT_MODE_GUI, REPORT_MODE_CLI],
    require_active=False,
)
