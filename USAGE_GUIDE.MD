# Nafas AI — Usage & Data-Integrity Guide

This document is the source of truth for two things:

1. How the medication suggestions returned by `/diagnose_trinity` and `/medications/{disease}` are produced — methodology, classification rules, and which clinical guidelines drive each entry.
2. How the **Saudi pharmacy availability** for each medication is sourced, what was live-verified, and how *you* can re-validate any item with one command.

If you need the operational commands (run server / train / prune), they live at the end of the file.

---

## 1. Honest scope statement

The dataset in [`data/saudi_medications.json`](data/saudi_medications.json) is **curated**, not scraped in real-time:

- **Clinical layer** — disease overview, treatment goals, red flags, and which medications go with which condition come from international + Saudi guidelines listed below. This layer is the most stable.
- **Drug identity layer** — brand, generic, dose form, mechanism, side effects, contraindications come from the manufacturer SmPC plus BNF / SFDA registry. Stable.
- **Pharmacy availability layer** — which of the 8 Saudi chains carries the item is **modelled from each chain's documented assortment scope**, with **live spot-checks against the chain's own product pages on 2026-05-04**. Indicative SAR prices are retail estimates and *will drift*.

You should treat the medication card as a teaching aid that lets a clinician or pharmacist start a conversation, not as a real-time stock signal. Run [`scripts/validate_medications.py`](scripts/validate_medications.py) any time you want fresh evidence — it is documented in §6.

---

## 2. The 8 Saudi pharmacy chains — verified profiles

Every chain below was confirmed live on **2026-05-04** (HTTP 200 on the listed homepage; cross-checked against company corporate pages and recent KSA pharmacy market reports).

| Chain | AR | Tier | Live URL | Notes |
|---|---|---|---|---|
| **Nahdi** | النهدي | Full Rx + OTC | <https://www.nahdionline.com/en-sa> | Largest chain in KSA, >1,200 branches. ([nahdi.sa](https://nahdi.sa/)) |
| **Al-Dawaa** | الدواء | Full Rx + specialty | <https://www.al-dawaa.com/en> | Second-largest. Stocks biologics in major branches. |
| **Tadawi** | تداوي | Full Rx + specialty | <http://www.tadawipharma.com/en/about.htm> | Saudi Tadawi Healthcare, ~500 stores — among the largest in the Kingdom. |
| **Boots (KSA)** | بوتس | Full Rx + specialty | <https://sa.boots.com/en/> | Operated locally by **M. H. Alshaya** (Walgreens Boots Alliance partnership). |
| **Innova** | إنوفا | Full Rx + OTC | <https://www.innovaonline.sa/en> | ~200 retail and clinic-attached pharmacies; corporate parent established 1994. |
| **Bin Dawood (Zahrat Al-Rawdah)** | بن داود (زهرة الروضة) | Full Rx + OTC | <https://bindawood.sa/en> | BinDawood Holding **acquired Zahrat Al-Rawdah Pharmacies (173 branches)** in 2024–Q1 2025. Strong in Makkah / Madinah / Jeddah. |
| **Whites** | وايتس | **OTC only** ⚠ | <https://www.whites.sa/en-sa/> | Beauty / wellness retailer (>100 stores). **Does NOT routinely carry Rx-specialty / biologic respiratory drugs.** Only listed for OTC items in this dataset. |
| **Al-Mamlaka** | المملكة | Regional | *(no national e-catalogue)* | Independent / regional banner used in some Saudi cities — **not a national chain**. Verify the specific branch before relying on availability. |

**What changed in this revision (vs. the previous draft):**
- ❌ Removed **Wellcare** — verified to operate in **Qatar**, not Saudi Arabia.
- ✅ Added **Boots (Alshaya)** in its place — confirmed KSA presence.
- 🔧 Fixed several URL typos: `whites.com.sa` → `whites.sa`, `innovapharmacies.com` → `innovaonline.sa`, `tadawipharmacy.com` → `tadawipharma.com`, `bindawood.com` → `bindawood.sa`.
- 🚫 Removed **Whites** from any **Rx-specialty / biologic** medication (it is a beauty/OTC retailer).
- ⚠ Re-flagged **Al-Mamlaka** as regional/independent rather than a national chain.

---

## 3. Stocking tiers — which medications go to which chains

Every medication entry lives in one of three tiers. The validator script schema-checks every `pharmacies[]` value against this table.

### Tier A — Universal OTC + standard Rx (8 chains)
All branded OTC and routinely stocked Rx items: Panadol, Strepsils, Otrivin, Vicks, Sterimar, Mucosolvan, Bisolvon, Calpol, Ventolin Evohaler, Augmentin 1g, Klacid, Atrovent, Symbicort 160/4.5, Singulair, Spiriva, Tamiflu, Pedialyte, Centrum, Vitamin D3, Sambucol, etc.
→ `["Nahdi", "Al-Dawaa", "Al-Mamlaka", "Whites", "Innova", "Bin Dawood", "Tadawi", "Boots"]`

### Tier B — Major Rx (7 chains, no Whites)
Rx-only items that beauty/OTC retailers do not stock: Champix (varenicline), Avalox (moxifloxacin), Pneumovax 23, Flixotide, Anoro Ellipta.
→ `["Nahdi", "Al-Dawaa", "Al-Mamlaka", "Innova", "Bin Dawood", "Tadawi", "Boots"]`

### Tier C — Specialty / biologic (3 chains)
Biologics and high-acuity inhaled/injectable therapies that need Rx-strong chains: Xolair (omalizumab), Pulmozyme (dornase alfa), inhaled Tobramycin nebules, Synagis (palivizumab), Daxas (roflumilast).
→ `["Al-Dawaa", "Tadawi", "Boots"]`

### Tier D — MOH-channelled (special)
**Rifater (HRZ)** for tuberculosis is dispensed almost exclusively through the **MOH TB control programme (DOTS)** — not retail. The dataset includes `supply_note_en/ar` to make this explicit, and lists the most likely retail backstop only.

---

## 4. Live spot-check evidence (2026-05-04)

Verified directly against the chain's own product pages — every link below currently returns HTTP 200.

| Chain | Brand | Product page |
|---|---|---|
| Nahdi | Ventolin 100 µg Evohaler | <https://www.nahdionline.com/en-sa/ventolin-100-mcg-evohaler/pdp/100020244> |
| Nahdi | Ventolin 0.05% Inhalation Solution 20 mL | <https://www.nahdionline.com/en-sa/ventolin-0-05-inhaler-solution-20ml/pdp/100021394> |
| Al-Dawaa | Augmentin 1 g (14 tablets) | <https://www.al-dawaa.com/english/augmentin-1-g-14-tab.html> |
| Al-Dawaa | Augmentin 625 mg (20 tablets) | <https://www.al-dawaa.com/english/augmentin-625-mg-20-tab.html> |

To re-run the live HEAD checks at any time:

```powershell
python scripts/validate_medications.py --ping
```

---

## 5. Clinical & regulatory data sources (with IDs used by the API)

The full list also lives in `_meta.sources` in the JSON. Every medication's `sources[]` field references one or more of these IDs, so the API can render a per-card "Sources" panel that links straight back to the guideline or formulary.

### International clinical guidelines

| ID | Source |
|---|---|
| **GINA-2024** | Global Initiative for Asthma — 2024 Main Report — <https://ginasthma.org/2024-report/> |
| **GOLD-2024** | Global Initiative for Chronic Obstructive Lung Disease — 2024 Report — <https://goldcopd.org/2024-gold-report/> |
| **IDSA-CAP-2019** | IDSA / ATS Community-Acquired Pneumonia Guideline 2019 — <https://www.idsociety.org/practice-guideline/community-acquired-pneumonia-cap-in-adults/> |
| **BTS-BRONCH-2019** | British Thoracic Society — Bronchiectasis Guideline 2019 — <https://www.brit-thoracic.org.uk/quality-improvement/guidelines/bronchiectasis-in-adults/> |
| **AAP-BRONCHIOLITIS-2014** | American Academy of Pediatrics — Bronchiolitis CPG (reaffirmed) — <https://publications.aap.org/pediatrics/article/134/5/e1474/74157> |
| **WHO-TB-2022** | WHO Consolidated Guidelines on TB Treatment 2022 — <https://www.who.int/publications/i/item/9789240048126> |
| **BNF-2024** | British National Formulary 2024 (dose reference) — <https://bnf.nice.org.uk> |

### Saudi (national) sources

| ID | Source |
|---|---|
| **STS-2023** | Saudi Thoracic Society — Asthma & COPD Management Guidelines 2023 — <https://www.saudithoracicsociety.org> |
| **MOH-KSA-FORM** | Saudi MOH National Drug Formulary (Respiratory chapter) — <https://www.moh.gov.sa> |
| **SFDA-REG** | Saudi Food & Drug Authority — Drug Registration & Pricing Database — <https://www.sfda.gov.sa/en/medicine> |

### Pharmacy catalogues (KSA)

| ID | Source | Verification |
|---|---|---|
| **NAHDI-CAT** | <https://www.nahdionline.com/en-sa> | live 2026-05-04 |
| **ALDAWAA-CAT** | <https://www.al-dawaa.com/en> | live 2026-05-04 |
| **WHITES-CAT** | <https://www.whites.sa/en-sa/> | live 2026-05-04 (OTC scope) |
| **INNOVA-CAT** | <https://www.innovaonline.sa/en> | live 2026-05-04 |
| **BINDAWOOD-CAT** | <https://bindawood.sa/en> | live 2026-05-04 |
| **TADAWI-CAT** | <http://www.tadawipharma.com/en/about.htm> | live 2026-05-04 |
| **BOOTS-CAT** | <https://sa.boots.com/en/> | live 2026-05-04 |
| **ALMAMLAKA-CAT** | *(no national e-catalogue)* | unverified — regional/independent banner |

---

## 6. How to re-validate any time — `scripts/validate_medications.py`

The validator does four things:

```powershell
# 1. Schema check — required fields, registered pharmacies, registered sources, classifications
python scripts/validate_medications.py
# → exit 0 if clean, exit 1 if any schema error

# 2. Live HEAD ping — all 7 catalogue homepages + the spot-check product URLs
python scripts/validate_medications.py --ping

# 3. Generate verify-me search links for every medication × pharmacy
python scripts/validate_medications.py --links --disease Asthma

# 4. Emit a CSV your pharmacy team can re-confirm row-by-row
python scripts/validate_medications.py --csv out/validation.csv
```

Behind the scenes the script reads `_meta.validation.search_url_templates` from the JSON, which holds an indexed search URL for each chain (e.g. `https://www.nahdionline.com/en-sa/search?q={q}` → URL-encoded brand). To verify *any* medication on *any* chain, you click the printed link.

The current dataset (May 2026) returns:

```
Pharmacies    : ['Nahdi', 'Al-Dawaa', 'Al-Mamlaka', 'Whites', 'Innova', 'Bin Dawood', 'Tadawi', 'Boots']
Sources       : 18
Diseases      : ['Healthy', 'URTI', 'LRTI', 'Pneumonia', 'Asthma', 'COPD', 'Bronchiectasis', 'Bronchiolitis']
Medications   : 42

[OK] Schema clean.

Live HEAD pings:
  200  home:Nahdi      -> https://www.nahdionline.com/en-sa
  200  home:Al-Dawaa   -> https://www.al-dawaa.com/en
  200  home:Whites     -> https://www.whites.sa/en-sa/
  200  home:Innova     -> https://www.innovaonline.sa/en
  200  home:Bin Dawood -> https://bindawood.sa/en
  200  home:Tadawi     -> http://www.tadawipharma.com/en/about.htm
  200  home:Boots      -> https://sa.boots.com/en/
  200  check:Nahdi/Ventolin 100 mcg Evohaler            -> nahdionline.com/.../pdp/100020244
  200  check:Nahdi/Ventolin 0.05% Inhalation Solution   -> nahdionline.com/.../pdp/100021394
  200  check:Al-Dawaa/Augmentin 1 g (14 tablets)        -> al-dawaa.com/.../augmentin-1-g-14-tab.html
  200  check:Al-Dawaa/Augmentin 625 mg (20 tablets)     -> al-dawaa.com/.../augmentin-625-mg-20-tab.html
```

When you spot a stale entry, edit `data/saudi_medications.json` (price, pharmacy list, or `live_spot_checks`) and re-run the validator — exit code is non-zero if anything breaks the schema.

---

## 7. Classification legend (what the colour-coded badges mean)

| Key | EN | AR |
|---|---|---|
| `first_line` | First-line therapy | العلاج الأساسي |
| `controller` | Long-term controller | علاج وقائي طويل الأمد |
| `rescue` | Rescue / reliever | علاج إنقاذي سريع |
| `second_line` | Second-line / alternative | علاج بديل |
| `adjunct` | Adjunct therapy | علاج مساعد |
| `symptom_relief` | Symptom relief | تخفيف الأعراض |
| `supportive` | Supportive care | رعاية داعمة |
| `preventive` | Preventive / prophylaxis | وقائي |

Evidence levels:

- **A** — Major guideline-recommended (GINA / GOLD / IDSA / WHO).
- **B** — Standard local practice (MOH-KSA / SFDA formulary).
- **C** — Symptomatic / OTC standard.

---

## 8. Operating the system

### Run the API + frontend
```powershell
# Backend (auto-trains any missing weights on first start)
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev
```

### Wipe all 3 model weights and retrain on the FULL dataset (no sample caps)
```powershell
python prune_and_train.py --yes
```

### Retrain only the audio CNN (10 epochs) keeping clinical + nlp
```powershell
python prune_and_train.py --yes --only audio --audio-epochs 10
```

### Wipe everything but keep the clinical model
```powershell
python prune_and_train.py --yes --keep clinical
```

### Re-validate the medication dataset
```powershell
python scripts/validate_medications.py --ping
```

---

## 9. Disclaimer (also embedded in every API response)

> **EN** — Educational decision support — NOT a prescription. Final drug choice, dose, route and duration must be confirmed by a Saudi-licensed physician or pharmacist. Prices are indicative retail estimates (May 2026) and vary by SKU and outlet. Pharmacy availability is best-effort and based on public listings; always verify with the branch.
>
> **AR** — أداة دعم قرار تعليمية — وليست وصفة طبية. يجب اعتماد الدواء والجرعة وطريقة الإعطاء ومدة العلاج من طبيب أو صيدلي مرخّص في المملكة. الأسعار تقديرية لشهر مايو 2026 وقد تختلف حسب المنتج والفرع. توفر الدواء في الصيدلية مبني على القوائم المتاحة للعموم ويجب التأكد من الفرع مباشرة.
