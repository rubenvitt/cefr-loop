"""Beispielabsätze — sämtlich selbst geschrieben, synthetisch.

Keine Zeile stammt aus einem echten Bescheid, Vertrag, Kundendokument oder
Patientenbogen. Die Absätze imitieren den jeweiligen Stil, beschreiben aber
erfundene Sachverhalte.
"""

SAMPLES = [
    {
        "id": "bescheid",
        "title": "Behördenbescheid",
        "note": "Nominalstil, Schachtelsatz, Verweis auf einen anderen Absatz",
        "text": (
            "Die Gewährung der beantragten Leistung setzt voraus, dass die antragstellende "
            "Person die in Absatz 2 genannten Voraussetzungen kumulativ erfüllt und deren "
            "Vorliegen binnen einer Frist von vier Wochen nach Zugang dieses Bescheides "
            "durch geeignete Nachweise belegt; eine Fristverlängerung kann auf begründeten "
            "Antrag hin gewährt werden, sofern die Verzögerung nicht von der antragstellenden "
            "Person zu vertreten ist."
        ),
    },
    {
        "id": "aufklaerung",
        "title": "Patientenaufklärung",
        "note": "Fachwortschatz ohne Erklärung, Passivkonstruktionen",
        "text": (
            "Im Rahmen des Eingriffs wird unter Lokalanästhesie ein Zugang gelegt, über den "
            "das Kontrastmittel appliziert wird. Trotz sorgfältiger Indikationsstellung kann "
            "es in seltenen Fällen zu Unverträglichkeitsreaktionen kommen, die eine "
            "medikamentöse Intervention erforderlich machen; über die statistische Häufigkeit "
            "derartiger Komplikationen informiert der beigefügte Aufklärungsbogen."
        ),
    },
    {
        "id": "fehlermeldung",
        "title": "Fehlermeldung im Produkt",
        "note": "technischer Jargon in einem Text, den Endnutzer lesen",
        "text": (
            "Die Synchronisation wurde abgebrochen, da die Validierung des übermittelten "
            "Tokens fehlschlug. Möglicherweise liegt eine Inkonsistenz zwischen dem lokal "
            "persistierten Zustand und der serverseitigen Repräsentation vor. Eine "
            "Reinitialisierung der Sitzung kann den Konflikt auflösen, führt jedoch zum "
            "Verwerfen nicht übertragener Änderungen."
        ),
    },
    {
        "id": "agb",
        "title": "Vertragsklausel",
        "note": "juristische Verweisketten, Konditionalgefüge",
        "text": (
            "Soweit der Auftragnehmer die Leistung aus Gründen nicht erbringen kann, die "
            "weder von ihm zu vertreten noch bei Vertragsschluss vorhersehbar waren, ruhen "
            "die wechselseitigen Hauptleistungspflichten für die Dauer des Hindernisses, "
            "längstens jedoch für drei Monate; im Anschluss steht beiden Parteien ein Recht "
            "zur außerordentlichen Kündigung zu, unbeschadet bereits entstandener "
            "Vergütungsansprüche für erbrachte Teilleistungen."
        ),
    },
    {
        "id": "einfach",
        "title": "Bereits einfach (Gegenprobe)",
        "note": "sollte ohne Umschreiben durchlaufen — prüft die Abbruchbedingung",
        "text": (
            "Ihr Paket ist unterwegs. Der Bote bringt es morgen zwischen 9 und 13 Uhr. "
            "Sind Sie nicht zu Hause, legt er es beim Nachbarn ab. Sie bekommen dann eine "
            "Nachricht, wo das Paket liegt."
        ),
    },
]

BY_ID = {sample["id"]: sample for sample in SAMPLES}
