# Legal Radar

Een kleine Nederlandstalige tool die bij een vrij beschreven ondernemersidee aanwijst **op welke rechtsgebieden iemand moet letten**. De tool geeft nooit een oordeel over of iets mag. Het is een portfolioproject, geen juridisch product.

**Demo online:** https://juliguan.github.io/legal-radar/ (draait in de browser met trefwoorden, zonder model)

*Laatst gecontroleerd op 5 oktober 2026 (bronnen en wetgeving). De inhoud van `data/legal_areas.yaml` staat overal op `verified: false`: er is nog geen jurist overheen gegaan.*

## Welk probleem lost het op

Beginnende ondernemers weten vaak niet *welke* regels bij hun idee kunnen spelen: pas als er een boete of een klacht komt, blijkt dat er een claimsverordening, een productveiligheidsregeling of een vergunningplicht was. Legal Radar beantwoordt alleen de vraag "waar moet ik kijken?" voor vijf gebieden:

1. Privacy (AVG)
2. Consumentenrecht en oneerlijke handelspraktijken
3. Productaansprakelijkheid en productveiligheid
4. Voedsel- en gezondheidsclaims
5. Financiële regelgeving (Wft, MiCA, witwassen)

## Hoe werkt het

```
vrije omschrijving ──► model (alleen status + triggervraag + citaat) ──► code-controles ──► rapport uit de YAML
```

- Het model krijgt de **vaste lijst gebieden met triggervragen** en bepaalt per gebied alleen: `status` (`relevant` / `niet_relevant` / `onzeker`), de toepasselijke triggervraag en een **letterlijk citaat** uit de invoer. Het mag geen gebieden bijverzinnen; onbekende gebieden worden genegeerd, ontbrekende worden `onzeker`.
- De output is JSON, gevalideerd met pydantic (`src/legal_radar/models.py`).
- **De code controleert elk citaat** (hoofdlettergevoeligheid, witruimte en typografische aanhalingstekens worden genegeerd, woorden niet). Staat het citaat niet in de invoer, dan wordt de status `onzeker` en vermeldt het rapport dat.
- **Wetsverwijzingen, uitleg en bronnen komen uitsluitend uit `data/legal_areas.yaml`**, nooit uit de modeloutput. Het model ziet geen wetsartikelen.
- Het rapport (Markdown) toont per gebied: status, reden (de triggervraag), citaat, wetsverwijzingen, bronnen en onderaan een disclaimer dat dit een oriëntatie is en geen juridisch advies.

De kennisbank is ontstaan uit onderzoek in `research/*.md` (één samenvatting per gebied, met bronnen, tegenstrijdigheden en open punten). Elk feit heeft een bron-URL. Artikelnummers zijn alleen ingevuld als ik ze in de gedownloade wettekst heb teruggevonden; anders staat er `TODO verify`. Het veld `evidence` laat zien hoe sterk de onderbouwing is (`text_checked`, `primary_page`, `search_snippet`, `secondary`).

## Gebruik

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env        # vul ANTHROPIC_API_KEY in; .env wordt nooit gecommit
.venv/bin/legal-radar "Ik verkoop een sportshot die spierkramp voorkomt"
.venv/bin/legal-radar -f cases/03_bitcoin_opsporen/idea.txt --json
.venv/bin/legal-radar-web      # webinterface op http://127.0.0.1:8000 (demo-modus zonder API-sleutel)
```

Het model stel je in met `LEGAL_RADAR_MODEL` (standaard `claude-sonnet-5-5`).

## Tests en evaluatie

```bash
.venv/bin/pytest                # citaat-check, YAML-validatie, rapport, scoring (geen API nodig)
.venv/bin/python eval.py        # draait de 8 cases met het echte model (API-sleutel nodig)
```

`eval.py` rapporteert per gebied: **gemiste gebieden**, **onterechte alarmen** en het **aantal keer dat de citaat-check faalde**. De 8 cases in `cases/` zijn: sportshot tegen spierkramp, veiligheidsproducten voor oudere fietsers, app die verloren bitcoin opspoort, AI-reisplanner, dashboard dat horecadrukte voorspelt uit kassadata, kledingresale-webshop, en twee controlecases zonder juridisch risico. De verwachtingen in `expected.yaml` zijn mijn eigen inschatting en horen door een jurist te worden bijgesteld; gebieden waar redelijke mensen van mening kunnen verschillen staan onder `optional` en tellen niet als gemist of onterecht alarm.

**Status van de evaluatie:** `eval.py` is getest met een nagebootste client, maar er is nog geen echte run met een model uitgevoerd (geen API-sleutel). Op de website staan wel voorbeelduitkomsten en een scorebord. Die zijn **handmatig opgesteld door Claude, zonder API** (`data/manual_runs.yaml`) en lopen door de echte citaat-check en scoring. Het is dus geen modelmeting. Het is ook niet blind: de verwachtingen in `expected.yaml` zijn door dezelfde auteur geschreven, dus een score van nul fouten zegt weinig. Een eerlijke meting vraagt `eval.py` met een model.

## Beperkingen

- **Geen advies, geen oordeel.** Een gebied als "relevant" markeren betekent alleen: kijk hier. Het zegt niets over wat wel of niet mag.
- **Vijf gebieden.** Arbeidsrecht, fiscaal recht, IE, medische hulpmiddelen, betaaldiensten (PSD2), DSA en vrijwel alle sectorwetgeving vallen erbuiten. Een idee zonder treffer is dus niet "veilig".
- **Kennisbank is ongecontroleerd en een momentopname.** Alles is `verified: false`. Bij negen wetsverwijzingen is het artikelnummer niet teruggevonden (`TODO verify`). Wetgeving verandert: zie `recent_changes` en de datum bovenaan.
- **Bronnen niet allemaal primair.** De AP- en DNB-sites waren niet op te halen; wat daarvan komt is secundair of uit zoekresultaten en staat zo gemarkeerd.
- **Rechtspraak is niet onderzocht.**
- **Het model kan misrekenen.** De citaat-check bewijst dat een citaat in de invoer staat, niet dat het de conclusie ondersteunt.
- **Triggervragen zijn mijn formulering** op basis van de wetteksten, niet overgenomen uit een officiële bron.
- Invoer wordt naar de Anthropic API gestuurd. Voer geen vertrouwelijke gegevens in.

## Waar een gewone chatbot net zo goed werkt

Voor één idee en een eenmalige verkenning kan een algemene chatbot dit net zo goed: "welke rechtsgebieden spelen hier?" levert vergelijkbare lijsten op. Legal Radar voegt alleen toe wat een jurist in een proces wil afdwingen:

- **Vaste gebieden en vaste triggervragen**, zodat uitkomsten vergelijkbaar en testbaar zijn (evaluatie over cases).
- **Controleerbaarheid**: elk "relevant" heeft een letterlijk citaat dat de code controleert.
- **Scheiding van oordeel en bron**: wetsverwijzingen komen uit een door jou na te lopen bestand, niet uit het geheugen van een model.

Als je die drie dingen niet nodig hebt, gebruik dan gewoon een chatbot, en controleer de antwoorden daarna zelf.

## Structuur

```
data/legal_areas.yaml      kennisbank (wetten, triggervragen, fouten, wijzigingen, bronnen)
research/<gebied>.md       leesbare samenvatting per gebied (gegenereerd uit de YAML + open punten)
src/legal_radar/           models, areas (YAML), classify (model), quotes (citaat-check), report, cli
cases/<case>/              idea.txt + expected.yaml
build_site.py             genereert docs/data.json (voorbeelden, scorebord, tijdlijn) voor de site
data/manual_runs.yaml     handmatige voorbeeldbeoordelingen (geen modelmeting)
docs/                     statische GitHub Pages-site
eval.py   tests/
```
