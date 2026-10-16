# Regulace hladiny – dokumentace řešení

Aplikace reguluje hladinu v dolní nádrži levé věže pomocí čerpadla. Regulátor je PI,
běží v aplikaci s periodou 0,5 s a čte i zapisuje přes kartu NI USB-6001.

## Zapojení

| Signál | Kanál karty | Svorka budiče |
|---|---|---|
| Napětí čerpadla (výstup regulátoru) | `ao1` | uL |
| Hladina dolní nádrže (snímač TMDG 338 Z3H) | `ai0` | yL |

Karta se v systému jmenuje `Dev1`. Pravá věž se nepoužívá.

Při spuštění se aplikace připojí ke kartě. Pokud karta není dostupná, zapíše varování
a pokračuje se simulovanou věží (model dvou nádrží s parametry identifikovanými ze
7. 10.). UI i regulátor pracují se simulací stejně jako se skutečnou věží.

## Regulační smyčka

Časovač UI volá `RegulationService.tick()` každých 100 ms. Jednou za 0,5 s
(`CONTROL_PERIOD_S`) proběhne krok regulace:

1. přečte se hladina z čidla a převede na cm (viz Kalibrace),
2. medián z posledních 5 vzorků odfiltruje ojedinělé špičky,
3. kontrola: neplatné měření a překročení havarijní hladiny (viz Bezpečnost),
4. žádaná hodnota se omezí na povolený rozsah 3–22 cm,
5. PI regulátor spočítá napětí čerpadla,
6. napětí se omezí na 0–7,5 V a zapíše na `ao1`,
7. dopočítá se průtok a příkon a vzorek se uloží do záznamu (1 vzorek za sekundu).

Když regulace neběží, čerpadlo stojí (0 V) a hladina se dál čte každých 0,5 s, aby
obsluha viděla aktuální stav a výpadek karty se projevil ještě před spuštěním.

## PI regulátor

u = Kp · e + Ki · ∫ e dt, kde e = žádaná − skutečná hladina v metrech.

| Parametr | Hodnota |
|---|---|
| Kp | 46,8 V/m |
| Ki | 1,28 V/(m·s) (Ti ≈ 37 s) |
| Výstup | 1,5–7,5 V |
| Perioda | 0,5 s |

Parametry jsou navržené metodou CHR z odezev naměřených na věži. Dolní mez 1,5 V je
těsně pod napětím, od kterého čerpadlo začíná dopravovat vodu (≈ 1,56 V). Nad 7,5 V
přetéká horní nádrž.

Ošetření:

- **antiwindup:** při saturaci výstupu se integrál nezvětšuje ve směru saturace,
  opačná chyba ho ale zmenšovat může, takže regulátor ze saturace rychle vyjede,
- **neplatné měření (NaN):** výstup je minimum 1,5 V a integrál se nemění.

Kód: `backend/regulation/controllers/pi_controller.py`.

## Kalibrace čidla

Hladina se měří od dna dolní nádrže (odečet ze stupnice + 3,2 cm, stupnice začíná
3,2 cm nade dnem):

h = 3,17 · (U − U₀) + 1,54 cm

- **3,17 cm/V** a **1,54 cm** jsou proložené přes 4 body (16. 10.), odchylka od
  stupnice je do 1 mm:

  | Stupnice + 3,2 cm | Aplikace |
  |---|---|
  | 6,2 | 6,25 |
  | 10,35 | 10,35 |
  | 14,7 | 14,58 |
  | 20,8 | 20,85 |

- **1,54 cm** je výška nuly čidla nade dnem: po vypuštění zůstane v nádrži voda do
  výšky odtoku.
- **U₀** je napětí čidla při prázdné nádrži. Posouvá se (0,22–0,25 V, i během minut),
  proto se před každým měřením stiskne **Tare**: s vypuštěnou nádrží a vypnutým
  čerpadlem aplikace zprůměruje 10 vzorků a uloží novou nulu. Za běhu regulace je
  Tare zakázané.

Kód: `backend/hardware/tower.py`, konstanty `TOWER_LEVEL_*` v `config.py`.

## Bezpečnost

| Situace | Reakce |
|---|---|
| Žádaná hodnota mimo 3–22 cm | nejde zadat v UI, CSV profil s takovou hodnotou se odmítne, regulátor ji ořízne |
| Hladina ≥ 23 cm | varování v UI |
| Hladina ≥ 25 cm | regulace se zastaví, čerpadlo 0 V |
| 5 neplatných měření za sebou | regulace se zastaví, čerpadlo 0 V |
| Chyba karty (odpojení, chyba zápisu) | regulace se zastaví, čerpadlo 0 V |
| Tlačítko EMERGENCY STOP | regulace se zastaví, čerpadlo 0 V |

Důvod zastavení se zobrazí v panelu regulace a ve stavovém řádku a zapíše se do logu.
Bezpečný výchozí stav je čerpadlo na 0 V: nastaví se při připojení karty, při
zastavení regulace, při každé chybě i při ukončení aplikace.

## Průtok a příkon

- **Průtok** je odhad z rovnováhy přítok = odtok: q = c_L · √(2 g h), c_L =
  1,11 · 10⁻⁵ m². Přímo se neměří.
- **Příkon čerpadla** je z charakteristiky naměřené 7. 10.:
  P(u) = (3,5 + 0,6 u) · (0,408 + 0,0741 u) W. Energie je jeho integrál v čase.

## Ověření

- **7. 10., laboratorní skript:** PI drží hladinu v rozsahu 6–18 cm, průměrná
  ustálená chyba ≤ 0,7 mm, překmit 2–7 mm (zpráva `mereni_2026-10-07.pdf`).
- **16. 10., aplikace na reálné věži:** regulace na 6, 10, 14 a 20 cm, směrodatná
  odchylka hladiny za posledních 30 s 0,3–0,4 mm. Funkční nouzové zastavení a Tare.

## Nastavení

Všechny parametry jsou v `src/blobs_project/config.py`:

| Konstanta | Význam |
|---|---|
| `DAQ_DEVICE_NAME`, `TOWER_LEVEL_CHANNEL`, `TOWER_PUMP_CHANNEL` | karta a kanály |
| `TOWER_LEVEL_CM_PER_V`, `TOWER_LEVEL_ZERO_V`, `TOWER_LEVEL_OFFSET_CM` | kalibrace čidla |
| `TOWER_PUMP_MAX_V` | horní mez napětí čerpadla |
| `CONTROL_PERIOD_S` | perioda regulace |
| `PI_KP_V_PER_M`, `PI_KI`, `PI_MIN_V` | PI regulátor |
| `LEVEL_MEDIAN_SAMPLES`, `MAX_INVALID_SAMPLES` | filtr a neplatná měření |
| `SETPOINT_MIN_CM`, `SETPOINT_MAX_CM`, `LEVEL_WARNING_CM`, `LEVEL_TRIP_CM` | bezpečnostní meze |
