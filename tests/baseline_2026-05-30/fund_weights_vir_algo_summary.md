# Fund Weights, VIR, And Algo Summary

Snapshot date: 2026-04-06

This report summarizes the combined fund-level ACID table built from rolled exposures, VIR, and latest algo signals.

## Coverage

- funds covered: 9
- total fund-acid rows: 529
- rows matched to VIR: 405
- rows matched to algo: 340

## MStar Alternatives

- ACID rows: 1
- VIR matched rows: 0
- algo matched rows: 0
- summed target rolled exposure: 100.0000
- summed benchmark rolled exposure: 0.0000

### Largest Active Overweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| Alts | acid_bond | 100.0000 | 0.0000 | 100.0000 |  |  |  |  | 3 | MS ALTS BLACKROCK; MS ALTS SSI; MS ALTS WATER ISLAND |

### Largest Active Underweights

No rows available.

### Highest VIR STF Exposures

No rows available.

### Largest VIR And Fund Active Gaps

No rows available.

### Largest Algo And Fund Active Gaps

No rows available.

## MStar Defensive Bond

- ACID rows: 11
- VIR matched rows: 4
- algo matched rows: 2
- summed target rolled exposure: 100.4117
- summed benchmark rolled exposure: 0.0000

### Largest Active Overweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| US T: 1-10 | acid_bond | 44.8452 | 0.0000 | 44.8452 |  |  |  |  | 3 | USD Treasury_AA: 1-3yr; USD Treasury_AA: 3-5yr; USD Treasury_AA: 3m-1yr |
| US Secu | acid_bond | 26.7016 | 0.0000 | 26.7016 |  |  |  |  | 24 | USD Agency Mortgage-Backed: 10-20yr; USD Asset-Backed: 5-7yr; USD Asset-Backed: 3-5yr; USD Commercial Mortgage-Backed... |
| USD Cash | acid_bond | 13.1013 | 0.0000 | 13.1013 |  |  |  |  | 2 | USD Cash & Equivalents; EUR Cash & Equivalents |
| US IL: 1-10 | acid_bond | 5.5000 | 0.0000 | 5.5000 |  |  |  |  | 2 | USD Govt Inflation Linked_AA: 3-5yr; USD Govt Inflation Linked_AA: 1-3yr |
| US Corp: 1-10 | acid_bond | 3.7021 | 0.0000 | 3.7021 |  |  |  |  | 7 | USD Corporate Bond Inv. Grade_A: 1-3yr; USD Corporate Bond Inv. Grade_BBB: 1-3yr; USD Corporate Bond Inv. Grade_AAA: ... |
| US Corp: HY | acid_bond | 3.6068 | 0.0000 | 3.6068 |  |  |  |  | 6 | USD Corporate Bond High Yield; USD Corporate Bond High Yield: 1-3yr; USD Corporate Bond High Yield: 7-10yr; USD Corpo... |
| US EQ | acid_country | 1.5334 | 0.0000 | 1.5334 | -0.0276 | 0.0023 |  |  | 3 | PHI GROUP INC COM; COPPER PPTY CTL PASS; WTS. UNITI GROUP INC |
| US EN EQ | acid_region_sector | 1.2751 | 0.0000 | 1.2751 | -0.0208 | -0.0076 | 0.0324 | 0.0107 | 1 | PHI GROUP INC COM |
| US Muni: 1-10y (1-12) | acid_bond | 0.0778 | 0.0000 | 0.0778 |  |  |  |  | 1 | USD Municipal Inv. Grade_AAA: 7-10yr |
| US SML EQ | acid_country | 0.0342 | 0.0000 | 0.0342 | -0.0142 | -0.0004 |  |  | 1 | Uniti Group Inc |

### Largest Active Underweights

No rows available.

### Highest VIR STF Exposures

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|
| US SML EQ | acid_country | 0.0342 | 0.0000 | 0.0342 | -0.0142 | -0.0004 | 1 | Uniti Group Inc |
| US EN EQ | acid_region_sector | 1.2751 | 0.0000 | 1.2751 | -0.0208 | -0.0076 | 1 | PHI GROUP INC COM |
| US TL EQ | acid_region_sector | 0.0342 | 0.0000 | 0.0342 | -0.0228 | 0.0073 | 1 | Uniti Group Inc |
| US EQ | acid_country | 1.5334 | 0.0000 | 1.5334 | -0.0276 | 0.0023 | 3 | PHI GROUP INC COM; COPPER PPTY CTL PASS; WTS. UNITI GROUP INC |

### Largest VIR And Fund Active Gaps

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US EQ | acid_country | 1.5334 | 0.0000 | 1.5334 | -0.0276 | 0.0023 | 1.5611 | 3 | PHI GROUP INC COM; COPPER PPTY CTL PASS; WTS. UNITI GROUP INC |
| US EN EQ | acid_region_sector | 1.2751 | 0.0000 | 1.2751 | -0.0208 | -0.0076 | 1.2959 | 1 | PHI GROUP INC COM |
| US TL EQ | acid_region_sector | 0.0342 | 0.0000 | 0.0342 | -0.0228 | 0.0073 | 0.0570 | 1 | Uniti Group Inc |
| US SML EQ | acid_country | 0.0342 | 0.0000 | 0.0342 | -0.0142 | -0.0004 | 0.0484 | 1 | Uniti Group Inc |

### Largest Algo And Fund Active Gaps

| ACID | Type | Target | Bench | Active | Algo Abs | Algo Active | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US EN EQ | acid_region_sector | 1.2751 | 0.0000 | 1.2751 | 0.0324 | 0.0107 | 1.2644 | 1 | PHI GROUP INC COM |
| US TL EQ | acid_region_sector | 0.0342 | 0.0000 | 0.0342 | 0.0499 | -0.0167 | 0.0509 | 1 | Uniti Group Inc |

## MStar Global Income

- ACID rows: 153
- VIR matched rows: 108
- algo matched rows: 91
- summed target rolled exposure: 137.1739
- summed benchmark rolled exposure: 149.7958

### Largest Active Overweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| US Corp: HY | acid_bond | 14.7441 | 1.0364 | 13.7077 |  |  |  |  | 44 | USD Corporate Bond High Yield_CCC&Below: 5-7yr; USD Corporate Bond High Yield_B: 1-3yr; USD Corporate Bond High Yield... |
| US LRG V EQ | acid_country | 13.8807 | 6.5797 | 7.3010 | -0.0226 | -0.0017 | 0.2219 | -0.0261 | 70 | Enterprise Products Partners LP; Chevron Corp; Johnson & Johnson; JPMorgan Chase & Co; EXXON MOBIL CORP; Verizon Comm... |
| US EN EQ | acid_region_sector | 7.4988 | 1.5484 | 5.9504 | -0.0208 | -0.0076 | 0.0324 | 0.0107 | 82 | Enterprise Products Partners LP; Chevron Corp; Energy Transfer LP; Enbridge Inc; EXXON MOBIL CORP; ONEOK Inc; ConocoP... |
| US T: 10+ | acid_bond | 7.5000 | 2.1813 | 5.3187 |  |  |  |  | 4 | USD Treasury_AA: 20+yr; USD Treasury_AA: 10-20yr; USD Treasury: 10-20yr; USD Government-Related_AA: 20+yr |
| US RE EQ | acid_region_sector | 4.1574 | 0.6994 | 3.4579 | -0.0148 | -0.0057 |  |  | 146 | VICI Properties Inc Ordinary Shares; Crown Castle Inc; Federal Realty Investment Trust; Welltower Inc; Prologis Inc; ... |
| UK EQ | acid_country | 4.6642 | 1.6706 | 2.9936 | -0.0195 | -0.0052 | 0.0418 | 0.0086 | 204 | BAE Systems PLC; British American Tobacco PLC ADR; National Grid PLC; Amcor PLC Ordinary Shares; ASTRAZENECA PLC; HSB... |
| US MID V EQ | acid_country | 4.7389 | 1.8044 | 2.9345 | -0.0173 | -0.0038 | 0.0665 | 0.0023 | 131 | Energy Transfer LP; VICI Properties Inc Ordinary Shares; ONEOK Inc; Crown Castle Inc; Kenvue Inc; Dominion Energy Inc... |
| US Secu | acid_bond | 8.7336 | 6.0805 | 2.6531 |  |  |  |  | 69 | USD Commercial Mortgage-Backed: 7-10yr; USD Commercial Mortgage-Backed_BBB: 3-5yr; USD Commercial Mortgage-Backed_AAA... |
| EU UT EQ | acid_region_sector | 2.7065 | 0.3724 | 2.3341 | -0.0395 | -0.0094 | 0.0077 | 0.0000 | 51 | Enel SpA; National Grid PLC; Iberdrola SA; Engie SA; E.ON SE; RWE AG Class A; SSE PLC; Veolia Environnement SA; Snam ... |
| EM HC T: Gbl Div. | acid_bond | 2.2777 | 0.1028 | 2.1749 |  |  |  |  | 42 | USD EM Hard Currency Debt_BB: 5-7yr; USD EM Hard Currency Debt_B: 3-5yr; USD EM Corporate_B: 7-10yr; USD EM Corporate... |

### Largest Active Underweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| US IT EQ | acid_region_sector | 0.8659 | 9.6145 | -8.7486 | -0.0354 | 0.0054 | 0.1353 | -0.0620 | 185 | Texas Instruments Inc; International Business Machines Corp; Cisco Systems Inc; Qualcomm Inc; NetApp Inc; NVIDIA Corp... |
| US LRG EQ | acid_country | 2.9918 | 10.1023 | -7.1106 | -0.0320 | 0.0031 |  |  | 50 | Johnson Controls International PLC Registered Shares; COCA-COLA CO/THE; CME GRP. INC; Texas Instruments Inc; MCDONALD... |
| US LRG G EQ | acid_country | 0.2018 | 5.8351 | -5.6333 | -0.0408 | 0.0069 | 0.1795 | -0.0602 | 29 | Welltower Inc; NVIDIA Corp; Broadcom Inc; TESLA INC; Eli Lilly and Co; Netflix Inc; Advanced Micro Devices Inc; Palan... |
| US T: 1-10 | acid_bond | 3.0000 | 8.3394 | -5.3394 |  |  |  |  | 10 | USD Treasury_AA: 3-5yr; USD Treasury_AA: 5-7yr; USD Treasury_AA: 7-10yr; USD Treasury_AA: 1-3yr; USD Treasury_AA: 3m-... |
| USD Cash | acid_bond | -4.5758 | 0.0000 | -4.5758 |  |  |  |  | 5 | GBP Cash & Equivalents; USD Cash & Equivalents; EUR Cash & Equivalents; AUD Cash & Equivalents; USD Bank Loan High Yi... |
| EM LC T: Gbl Div. (JPM) | acid_bond | 1.8726 | 5.8556 | -3.9831 |  |  |  |  | 44 | BRL EM Local Currency Debt_BB: 3-5yr; CNY EM Local Currency Debt_A: 1-3yr; CNY EM Local Currency Debt_A: 3-5yr; CNY E... |
| EU T: 1-10 | acid_bond | 1.3143 | 4.9232 | -3.6089 |  |  |  |  | 26 | EUR Treasury_A: 1-3yr; EUR Treasury_A: 3-5yr; EUR Treasury_A: 7-10yr; EUR Treasury_AAA: 1-3yr; EUR Treasury_A: 5-7yr;... |
| US Corp: 1-10 | acid_bond | 0.4575 | 3.1549 | -2.6974 |  |  |  |  | 59 | USD Corporate Bond Inv. Grade_BBB: 5-7yr; USD Corporate Bond Inv. Grade_BBB: 3-5yr; USD Corporate Bond Inv. Grade_BBB... |
| US CD EQ | acid_region_sector | 0.6498 | 3.0722 | -2.4224 | -0.0295 | 0.0068 | 0.0416 | -0.0192 | 143 | MCDONALDS CORP COM; Hasbro Inc; Starbucks Corp; Amazon.com Inc; TESLA INC; HOME DEPOT INC/THE; TJX Companies Inc; Boo... |
| JP T: 1-10 | acid_bond | 0.7221 | 2.7048 | -1.9827 |  |  |  |  | 4 | JPY Treasury_A: 1-3yr; JPY Treasury_A: 7-10yr; JPY Treasury_A: 3-5yr; JPY Treasury_A: 5-7yr |

### Highest VIR STF Exposures

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|
| AU EN EQ | acid_region_sector | 0.0000 | 0.0431 | -0.0431 | 0.0414 | -0.0078 | 14 | Woodside Energy Group Ltd; Santos Ltd; Ampol Ltd; Whitehaven Coal Ltd; Paladin Energy Ltd; New Hope Corp Ltd; Viva En... |
| TR EQ | acid_country | 0.0000 | 0.0491 | -0.0491 | 0.0307 | 0.0063 | 100 | Aselsan Elektronik Sanayi Ve Ticaret AS; Bim Birlesik Magazalar AS; Tupras-Turkiye Petrol Rafineleri AS; Turk Hava Yo... |
| EM RE EQ | acid_region_sector | 0.8249 | 0.1089 | 0.7160 | 0.0226 | 0.0026 | 170 | PROLOGIS PROP. MEXICO SA; EMAAR PROPS. PJSC; China Resources Land Ltd; KE Holdings Inc Class A; Aldar Properties PJSC... |
| DK EQ | acid_country | 0.0000 | 0.1918 | -0.1918 | 0.0194 | 0.0187 | 38 | Novo Nordisk AS Class B; DSV AS; Danske Bank AS; Vestas Wind Systems AS; Novonesis (Novozymes) B Class B; Genmab AS; ... |
| ID EQ | acid_country | 0.0000 | 0.0732 | -0.0732 | 0.0180 | 0.0005 | 88 | PT Bank Central Asia Tbk; PT Bank Rakyat Indonesia (Persero) Tbk Registered Shs Series -B-; PT Bank Mandiri (Persero)... |
| PH EQ | acid_country | 0.0000 | 0.0288 | -0.0288 | 0.0152 | -0.0066 | 42 | International Container Terminal Services Inc; SM Investments Corp; BDO Unibank Inc; SM Prime Holdings Inc; Bank of t... |
| AU HC EQ | acid_region_sector | 0.0000 | 0.0571 | -0.0571 | 0.0124 | 0.0144 | 19 | CSL Ltd; Fisher & Paykel Healthcare Corp Ltd; Sigma Healthcare Ltd; Cochlear Ltd; Sino Biopharmaceutical Ltd; Sonic H... |
| QA EQ | acid_country | 0.0000 | 0.0422 | -0.0422 | 0.0107 | 0.0003 | 23 | Qatar National Bank SAQ; Qatar Islamic Bank QPSC; Industries Qatar QSC; Qatar Gas Transport Co Ltd (Nakilat) QSC; AlR... |
| CN EQ | acid_country | 0.0226 | 1.5160 | -1.4935 | 0.0080 | 0.0067 | 1513 | MIDEA GRP. CO LTD; TENCENT HLDGS. LTD; Alibaba Group Holding Ltd Ordinary Shares; PDD Holdings Inc ADR; Xiaomi Corp C... |
| MY EQ | acid_country | 0.0000 | 0.1084 | -0.1084 | 0.0076 | 0.0004 | 112 | Malayan Banking Bhd; Public Bank Bhd; Tenaga Nasional Bhd; CIMB Group Holdings Bhd; RHB Bank Bhd; Press Metal Alumini... |

### Largest VIR And Fund Active Gaps

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US IT EQ | acid_region_sector | 0.8659 | 9.6145 | -8.7486 | -0.0354 | 0.0054 | 8.7132 | 185 | Texas Instruments Inc; International Business Machines Corp; Cisco Systems Inc; Qualcomm Inc; NetApp Inc; NVIDIA Corp... |
| US LRG V EQ | acid_country | 13.8807 | 6.5797 | 7.3010 | -0.0226 | -0.0017 | 7.3237 | 70 | Enterprise Products Partners LP; Chevron Corp; Johnson & Johnson; JPMorgan Chase & Co; EXXON MOBIL CORP; Verizon Comm... |
| US LRG EQ | acid_country | 2.9918 | 10.1023 | -7.1106 | -0.0320 | 0.0031 | 7.0785 | 50 | Johnson Controls International PLC Registered Shares; COCA-COLA CO/THE; CME GRP. INC; Texas Instruments Inc; MCDONALD... |
| US EN EQ | acid_region_sector | 7.4988 | 1.5484 | 5.9504 | -0.0208 | -0.0076 | 5.9713 | 82 | Enterprise Products Partners LP; Chevron Corp; Energy Transfer LP; Enbridge Inc; EXXON MOBIL CORP; ONEOK Inc; ConocoP... |
| US LRG G EQ | acid_country | 0.2018 | 5.8351 | -5.6333 | -0.0408 | 0.0069 | 5.5925 | 29 | Welltower Inc; NVIDIA Corp; Broadcom Inc; TESLA INC; Eli Lilly and Co; Netflix Inc; Advanced Micro Devices Inc; Palan... |
| US RE EQ | acid_region_sector | 4.1574 | 0.6994 | 3.4579 | -0.0148 | -0.0057 | 3.4727 | 146 | VICI Properties Inc Ordinary Shares; Crown Castle Inc; Federal Realty Investment Trust; Welltower Inc; Prologis Inc; ... |
| UK EQ | acid_country | 4.6642 | 1.6706 | 2.9936 | -0.0195 | -0.0052 | 3.0131 | 204 | BAE Systems PLC; British American Tobacco PLC ADR; National Grid PLC; Amcor PLC Ordinary Shares; ASTRAZENECA PLC; HSB... |
| US MID V EQ | acid_country | 4.7389 | 1.8044 | 2.9345 | -0.0173 | -0.0038 | 2.9518 | 131 | Energy Transfer LP; VICI Properties Inc Ordinary Shares; ONEOK Inc; Crown Castle Inc; Kenvue Inc; Dominion Energy Inc... |
| US CD EQ | acid_region_sector | 0.6498 | 3.0722 | -2.4224 | -0.0295 | 0.0068 | 2.3929 | 143 | MCDONALDS CORP COM; Hasbro Inc; Starbucks Corp; Amazon.com Inc; TESLA INC; HOME DEPOT INC/THE; TJX Companies Inc; Boo... |
| EU UT EQ | acid_region_sector | 2.7065 | 0.3724 | 2.3341 | -0.0395 | -0.0094 | 2.3736 | 51 | Enel SpA; National Grid PLC; Iberdrola SA; Engie SA; E.ON SE; RWE AG Class A; SSE PLC; Veolia Environnement SA; Snam ... |

### Largest Algo And Fund Active Gaps

| ACID | Type | Target | Bench | Active | Algo Abs | Algo Active | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US IT EQ | acid_region_sector | 0.8659 | 9.6145 | -8.7486 | 0.1353 | -0.0620 | 8.6866 | 185 | Texas Instruments Inc; International Business Machines Corp; Cisco Systems Inc; Qualcomm Inc; NetApp Inc; NVIDIA Corp... |
| US LRG V EQ | acid_country | 13.8807 | 6.5797 | 7.3010 | 0.2219 | -0.0261 | 7.3271 | 70 | Enterprise Products Partners LP; Chevron Corp; Johnson & Johnson; JPMorgan Chase & Co; EXXON MOBIL CORP; Verizon Comm... |
| US EN EQ | acid_region_sector | 7.4988 | 1.5484 | 5.9504 | 0.0324 | 0.0107 | 5.9397 | 82 | Enterprise Products Partners LP; Chevron Corp; Energy Transfer LP; Enbridge Inc; EXXON MOBIL CORP; ONEOK Inc; ConocoP... |
| US LRG G EQ | acid_country | 0.2018 | 5.8351 | -5.6333 | 0.1795 | -0.0602 | 5.5731 | 29 | Welltower Inc; NVIDIA Corp; Broadcom Inc; TESLA INC; Eli Lilly and Co; Netflix Inc; Advanced Micro Devices Inc; Palan... |
| UK EQ | acid_country | 4.6642 | 1.6706 | 2.9936 | 0.0418 | 0.0086 | 2.9850 | 204 | BAE Systems PLC; British American Tobacco PLC ADR; National Grid PLC; Amcor PLC Ordinary Shares; ASTRAZENECA PLC; HSB... |
| US MID V EQ | acid_country | 4.7389 | 1.8044 | 2.9345 | 0.0665 | 0.0023 | 2.9322 | 131 | Energy Transfer LP; VICI Properties Inc Ordinary Shares; ONEOK Inc; Crown Castle Inc; Kenvue Inc; Dominion Energy Inc... |
| US CD EQ | acid_region_sector | 0.6498 | 3.0722 | -2.4224 | 0.0416 | -0.0192 | 2.4032 | 143 | MCDONALDS CORP COM; Hasbro Inc; Starbucks Corp; Amazon.com Inc; TESLA INC; HOME DEPOT INC/THE; TJX Companies Inc; Boo... |
| EU UT EQ | acid_region_sector | 2.7065 | 0.3724 | 2.3341 | 0.0077 | 0.0000 | 2.3341 | 51 | Enel SpA; National Grid PLC; Iberdrola SA; Engie SA; E.ON SE; RWE AG Class A; SSE PLC; Veolia Environnement SA; Snam ... |
| IT EQ | acid_country | 2.4818 | 0.3558 | 2.1260 | 0.0066 | -0.0002 | 2.1262 | 71 | Enel SpA; UniCredit SpA; INTESA SANPAOLO SPA; Eni SpA; Generali; Prysmian SpA; Leonardo SpA Az nom Post raggruppament... |
| US TL EQ | acid_region_sector | 1.0682 | 3.0477 | -1.9796 | 0.0499 | -0.0167 | 1.9629 | 51 | Verizon Communications Inc; Comcast Corp Class A; ALPHABET INC; Alphabet Inc Class C; Meta Platforms Inc Class A; Net... |

## MStar Global Opportunistic Equity

- ACID rows: 112
- VIR matched rows: 108
- algo matched rows: 91
- summed target rolled exposure: 181.9843
- summed benchmark rolled exposure: 199.8790

### Largest Active Overweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| USD Cash | acid_bond | 16.7035 | 0.0000 | 16.7035 |  |  |  |  | 2 | USD Cash & Equivalents; GBP Cash & Equivalents |
| US SML V EQ | acid_country | 8.0227 | 1.0311 | 6.9916 | -0.0024 | -0.0004 | 0.0076 | 0.0057 | 1480 | H&R Block Inc; International Game Technology PLC; Dentsply Sirona Inc; The Campbell's Co; Brown-Forman Corp Registere... |
| US MID V EQ | acid_country | 7.6346 | 3.6089 | 4.0258 | -0.0173 | -0.0038 | 0.0665 | 0.0023 | 130 | Omnicom Group Inc; Fiserv Inc; Cognizant Technology Solutions Corp Class A; Paychex Inc; REALTY INC. CORP; Target Cor... |
| US CS EQ | acid_region_sector | 6.4656 | 3.1966 | 3.2689 | -0.0288 | -0.0092 | 0.0396 | 0.0065 | 142 | The Campbell's Co; Walmart Inc; Costco Wholesale Corp; Procter & Gamble Co; Philip Morris International Inc; COCA-COL... |
| EU CS EQ | acid_region_sector | 3.6561 | 1.2318 | 2.4243 | -0.0008 | -0.0107 | 0.0375 | 0.0240 | 79 | Henkel AG & Co KGaA Participating Preferred; Diageo PLC; Kerry Group PLC Class A; NESTLE SA; Unilever PLC; British Am... |
| US RE EQ | acid_region_sector | 3.7287 | 1.3988 | 2.3298 | -0.0148 | -0.0057 |  |  | 197 | Welltower Inc; Prologis Inc; Equinix Inc; Digital Realty Trust Inc; Simon Property Group Inc; REALTY INC. CORP; Ameri... |
| UK EQ | acid_country | 5.5631 | 3.3411 | 2.2220 | -0.0195 | -0.0052 | 0.0418 | 0.0086 | 207 | Bunzl PLC; United Utilities Group PLC Class A; Severn Trent PLC; Autotrader Group PLC; Diageo PLC; Experian PLC; Unil... |
| FR EQ | acid_country | 4.0921 | 1.9927 | 2.0994 | -0.0194 | -0.0057 | 0.0306 | 0.0088 | 114 | Edenred SE; FDJ United Ordinary Shares; L'Oreal SA; DANONE SA; KERING SA; Lvmh Moet Hennessy Louis Vuitton SE; Ose To... |
| BR EQ | acid_country | 2.6879 | 0.6071 | 2.0808 | 0.0012 | -0.0033 | 0.0182 | 0.0118 | 100 | Vale SA; Petroleo Brasileiro SA Petrobras Participating Preferred; Petroleo Brasileiro SA Petrobras; Itau Unibanco Ho... |
| US HC EQ | acid_region_sector | 8.0623 | 6.0141 | 2.0483 | -0.0139 | -0.0021 | 0.0654 | 0.0031 | 721 | Dentsply Sirona Inc; Eli Lilly and Co; Johnson & Johnson; AbbVie Inc; Merck & Co Inc; UnitedHealth Group Inc; Amgen I... |

### Largest Active Underweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| US LRG EQ | acid_country | 11.0665 | 20.2047 | -9.1382 | -0.0320 | 0.0031 |  |  | 50 | Apple Inc; Microsoft Corp; Amazon.com Inc; ALPHABET INC; Walmart Inc; Visa Inc Class A; Costco Wholesale Corp; Alphab... |
| US IT EQ | acid_region_sector | 13.9220 | 19.2290 | -5.3070 | -0.0354 | 0.0054 | 0.1353 | -0.0620 | 433 | NVIDIA Corp; Apple Inc; Microsoft Corp; Cognizant Technology Solutions Corp Class A; Adobe Inc; Broadcom Inc; Micron ... |
| JP EQ | acid_country | 0.9193 | 6.0080 | -5.0888 | -0.0332 | -0.0071 | 0.0436 | -0.0102 | 870 | SECOM Co Ltd; Japan Tobacco Inc; AEON Co Ltd; Seven & i Holdings Co Ltd; Ajinomoto Co Inc; Kao Corp; Asahi Group Hold... |
| US LRG G EQ | acid_country | 6.8932 | 11.6702 | -4.7770 | -0.0408 | 0.0069 | 0.1795 | -0.0602 | 29 | NVIDIA Corp; Eli Lilly and Co; Broadcom Inc; TESLA INC; Welltower Inc; Netflix Inc; GE Aerospace; Intuitive Surgical ... |
| US LRG V EQ | acid_country | 8.9933 | 13.1594 | -4.1661 | -0.0226 | -0.0017 | 0.2219 | -0.0261 | 70 | Adobe Inc; Johnson & Johnson; Procter & Gamble Co; Berkshire Hathaway Inc Class B; Philip Morris International Inc; P... |
| US FN EQ | acid_region_sector | 5.5974 | 8.6704 | -3.0730 | -0.0163 | 0.0059 | 0.0606 | -0.0136 | 632 | Fiserv Inc; Visa Inc Class A; Berkshire Hathaway Inc Class B; JPMorgan Chase & Co; MASTERCARD INC; Bank of America Co... |
| CA EQ | acid_country | 0.1773 | 3.1917 | -3.0145 | -0.0434 | -0.0065 | 0.0254 | -0.0060 | 210 | Alimentation Couche-Tard Inc; Loblaw Companies Ltd; Metro Inc; George Weston Ltd; Waste Connections Inc; Saputo Inc; ... |
| US ID EQ | acid_region_sector | 3.9723 | 6.5205 | -2.5482 | -0.0441 | -0.0058 | 0.0246 | -0.0351 | 533 | Paychex Inc; Caterpillar Inc; GE Aerospace; RTX Corp; GE Vernova Inc; MASCO CORP; Otis Worldwide Corp Ordinary Shares... |
| US TL EQ | acid_region_sector | 3.8611 | 6.0954 | -2.2343 | -0.0228 | 0.0073 | 0.0499 | -0.0167 | 159 | Omnicom Group Inc; ALPHABET INC; Alphabet Inc Class C; Meta Platforms Inc Class A; Netflix Inc; AT&T Inc; Verizon Com... |
| US EN EQ | acid_region_sector | 0.9722 | 3.0968 | -2.1247 | -0.0208 | -0.0076 | 0.0324 | 0.0107 | 174 | EXXON MOBIL CORP; Chevron Corp; ConocoPhillips; Williams Companies Inc; SLB Ltd; EOG Resources Inc; Baker Hughes Co C... |

### Highest VIR STF Exposures

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|
| AU EN EQ | acid_region_sector | 0.0000 | 0.0863 | -0.0863 | 0.0414 | -0.0078 | 14 | Woodside Energy Group Ltd; Santos Ltd; Ampol Ltd; Whitehaven Coal Ltd; Paladin Energy Ltd; New Hope Corp Ltd; Viva En... |
| TR EQ | acid_country | 0.1355 | 0.0981 | 0.0373 | 0.0307 | 0.0063 | 100 | Tupras-Turkiye Petrol Rafineleri AS; Koc Holding AS; Bim Birlesik Magazalar AS; Turk Hava Yollari AO; Akbank TAS; Ere... |
| EM RE EQ | acid_region_sector | 0.1279 | 0.2178 | -0.0899 | 0.0226 | 0.0026 | 171 | China Resources Land Ltd; China Overseas Land & Investment Ltd; Longfor Group Holdings Ltd; EMAAR PROPS. PJSC; KE Hol... |
| DK EQ | acid_country | 0.0182 | 0.3835 | -0.3653 | 0.0194 | 0.0187 | 38 | Carlsberg AS Class B; Novo Nordisk AS Class B; DSV AS; Danske Bank AS; Vestas Wind Systems AS; Novonesis (Novozymes) ... |
| ID EQ | acid_country | 0.1074 | 0.1463 | -0.0389 | 0.0180 | 0.0005 | 88 | PT Telkom Indonesia (Persero) Tbk Registered Shs Series -B-; PT Bank Rakyat Indonesia (Persero) Tbk Registered Shs Se... |
| PH EQ | acid_country | 0.0000 | 0.0576 | -0.0576 | 0.0152 | -0.0066 | 42 | International Container Terminal Services Inc; SM Investments Corp; BDO Unibank Inc; SM Prime Holdings Inc; Bank of t... |
| AU HC EQ | acid_region_sector | 0.8152 | 0.1141 | 0.7011 | 0.0124 | 0.0144 | 20 | CSL Ltd; WAVE Life Sciences Ltd; Fisher & Paykel Healthcare Corp Ltd; Sigma Healthcare Ltd; Cochlear Ltd; Sino Biopha... |
| QA EQ | acid_country | 0.0407 | 0.0844 | -0.0437 | 0.0107 | 0.0003 | 23 | Qatar National Bank SAQ; Qatar Fuel QSC; Ooredoo QPSC; Qatar Islamic Bank QPSC; Industries Qatar QSC; Qatar Gas Trans... |
| CN EQ | acid_country | 2.4841 | 3.0321 | -0.5480 | 0.0080 | 0.0067 | 1530 | Alibaba Group Holding Ltd Ordinary Shares; TENCENT HLDGS. LTD; JD.com Inc ADR; Industrial And Commercial Bank Of Chin... |
| MY EQ | acid_country | 0.0770 | 0.2168 | -0.1398 | 0.0076 | 0.0004 | 112 | Malayan Banking Bhd; Tenaga Nasional Bhd; Public Bank Bhd; CIMB Group Holdings Bhd; Sime Darby Bhd; Axiata Group Bhd;... |

### Largest VIR And Fund Active Gaps

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US LRG EQ | acid_country | 11.0665 | 20.2047 | -9.1382 | -0.0320 | 0.0031 | 9.1062 | 50 | Apple Inc; Microsoft Corp; Amazon.com Inc; ALPHABET INC; Walmart Inc; Visa Inc Class A; Costco Wholesale Corp; Alphab... |
| US SML V EQ | acid_country | 8.0227 | 1.0311 | 6.9916 | -0.0024 | -0.0004 | 6.9940 | 1480 | H&R Block Inc; International Game Technology PLC; Dentsply Sirona Inc; The Campbell's Co; Brown-Forman Corp Registere... |
| US IT EQ | acid_region_sector | 13.9220 | 19.2290 | -5.3070 | -0.0354 | 0.0054 | 5.2716 | 433 | NVIDIA Corp; Apple Inc; Microsoft Corp; Cognizant Technology Solutions Corp Class A; Adobe Inc; Broadcom Inc; Micron ... |
| JP EQ | acid_country | 0.9193 | 6.0080 | -5.0888 | -0.0332 | -0.0071 | 5.0556 | 870 | SECOM Co Ltd; Japan Tobacco Inc; AEON Co Ltd; Seven & i Holdings Co Ltd; Ajinomoto Co Inc; Kao Corp; Asahi Group Hold... |
| US LRG G EQ | acid_country | 6.8932 | 11.6702 | -4.7770 | -0.0408 | 0.0069 | 4.7362 | 29 | NVIDIA Corp; Eli Lilly and Co; Broadcom Inc; TESLA INC; Welltower Inc; Netflix Inc; GE Aerospace; Intuitive Surgical ... |
| US LRG V EQ | acid_country | 8.9933 | 13.1594 | -4.1661 | -0.0226 | -0.0017 | 4.1434 | 70 | Adobe Inc; Johnson & Johnson; Procter & Gamble Co; Berkshire Hathaway Inc Class B; Philip Morris International Inc; P... |
| US MID V EQ | acid_country | 7.6346 | 3.6089 | 4.0258 | -0.0173 | -0.0038 | 4.0431 | 130 | Omnicom Group Inc; Fiserv Inc; Cognizant Technology Solutions Corp Class A; Paychex Inc; REALTY INC. CORP; Target Cor... |
| US CS EQ | acid_region_sector | 6.4656 | 3.1966 | 3.2689 | -0.0288 | -0.0092 | 3.2978 | 142 | The Campbell's Co; Walmart Inc; Costco Wholesale Corp; Procter & Gamble Co; Philip Morris International Inc; COCA-COL... |
| US FN EQ | acid_region_sector | 5.5974 | 8.6704 | -3.0730 | -0.0163 | 0.0059 | 3.0567 | 632 | Fiserv Inc; Visa Inc Class A; Berkshire Hathaway Inc Class B; JPMorgan Chase & Co; MASTERCARD INC; Bank of America Co... |
| CA EQ | acid_country | 0.1773 | 3.1917 | -3.0145 | -0.0434 | -0.0065 | 2.9711 | 210 | Alimentation Couche-Tard Inc; Loblaw Companies Ltd; Metro Inc; George Weston Ltd; Waste Connections Inc; Saputo Inc; ... |

### Largest Algo And Fund Active Gaps

| ACID | Type | Target | Bench | Active | Algo Abs | Algo Active | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US SML V EQ | acid_country | 8.0227 | 1.0311 | 6.9916 | 0.0076 | 0.0057 | 6.9859 | 1480 | H&R Block Inc; International Game Technology PLC; Dentsply Sirona Inc; The Campbell's Co; Brown-Forman Corp Registere... |
| US IT EQ | acid_region_sector | 13.9220 | 19.2290 | -5.3070 | 0.1353 | -0.0620 | 5.2450 | 433 | NVIDIA Corp; Apple Inc; Microsoft Corp; Cognizant Technology Solutions Corp Class A; Adobe Inc; Broadcom Inc; Micron ... |
| JP EQ | acid_country | 0.9193 | 6.0080 | -5.0888 | 0.0436 | -0.0102 | 5.0786 | 870 | SECOM Co Ltd; Japan Tobacco Inc; AEON Co Ltd; Seven & i Holdings Co Ltd; Ajinomoto Co Inc; Kao Corp; Asahi Group Hold... |
| US LRG G EQ | acid_country | 6.8932 | 11.6702 | -4.7770 | 0.1795 | -0.0602 | 4.7168 | 29 | NVIDIA Corp; Eli Lilly and Co; Broadcom Inc; TESLA INC; Welltower Inc; Netflix Inc; GE Aerospace; Intuitive Surgical ... |
| US LRG V EQ | acid_country | 8.9933 | 13.1594 | -4.1661 | 0.2219 | -0.0261 | 4.1400 | 70 | Adobe Inc; Johnson & Johnson; Procter & Gamble Co; Berkshire Hathaway Inc Class B; Philip Morris International Inc; P... |
| US MID V EQ | acid_country | 7.6346 | 3.6089 | 4.0258 | 0.0665 | 0.0023 | 4.0235 | 130 | Omnicom Group Inc; Fiserv Inc; Cognizant Technology Solutions Corp Class A; Paychex Inc; REALTY INC. CORP; Target Cor... |
| US CS EQ | acid_region_sector | 6.4656 | 3.1966 | 3.2689 | 0.0396 | 0.0065 | 3.2624 | 142 | The Campbell's Co; Walmart Inc; Costco Wholesale Corp; Procter & Gamble Co; Philip Morris International Inc; COCA-COL... |
| US FN EQ | acid_region_sector | 5.5974 | 8.6704 | -3.0730 | 0.0606 | -0.0136 | 3.0594 | 632 | Fiserv Inc; Visa Inc Class A; Berkshire Hathaway Inc Class B; JPMorgan Chase & Co; MASTERCARD INC; Bank of America Co... |
| CA EQ | acid_country | 0.1773 | 3.1917 | -3.0145 | 0.0254 | -0.0060 | 3.0085 | 210 | Alimentation Couche-Tard Inc; Loblaw Companies Ltd; Metro Inc; George Weston Ltd; Waste Connections Inc; Saputo Inc; ... |
| US ID EQ | acid_region_sector | 3.9723 | 6.5205 | -2.5482 | 0.0246 | -0.0351 | 2.5131 | 533 | Paychex Inc; Caterpillar Inc; GE Aerospace; RTX Corp; GE Vernova Inc; MASCO CORP; Otis Worldwide Corp Ordinary Shares... |

## MStar International Equity

- ACID rows: 110
- VIR matched rows: 107
- algo matched rows: 90
- summed target rolled exposure: 198.1274
- summed benchmark rolled exposure: 199.7253

### Largest Active Overweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| UK EQ | acid_country | 11.2401 | 8.4679 | 2.7721 | -0.0195 | -0.0052 | 0.0418 | 0.0086 | 200 | Shell PLC; BAE Systems PLC; Rio Tinto PLC Ordinary Shares; GSK PLC; Haleon PLC; Reckitt Benckiser Group Plc; 3i Group... |
| FR EQ | acid_country | 7.6757 | 5.0831 | 2.5926 | -0.0194 | -0.0057 | 0.0306 | 0.0088 | 113 | TotalEnergies SE; Legrand SA; BNP Paribas Act. Cat.A; Lvmh Moet Hennessy Louis Vuitton SE; Accor SA; L'Oreal SA; SCHN... |
| MX EQ | acid_country | 3.2207 | 0.6746 | 2.5462 | -0.0156 | -0.0068 | 0.0033 | 0.0005 | 48 | Fomento Economico Mexicano SAB de CV ADR; FOMENTO ECONOMICO MEXICAN; Grupo Financiero Banorte SAB de CV Class O; Bols... |
| EM CS EQ | acid_region_sector | 3.6142 | 1.2394 | 2.3748 | 0.0073 | -0.0004 | 0.0142 | 0.0103 | 275 | Fomento Economico Mexicano SAB de CV ADR; Ambev SA; FOMENTO ECONOMICO MEXICAN; KT&G Corp; Dongsuh Companies Inc; Wal ... |
| EU ID EQ | acid_region_sector | 9.4545 | 7.1535 | 2.3010 | -0.0367 | -0.0035 | 0.0171 | -0.0125 | 270 | BAE Systems PLC; Atlas Copco AB Class A; Legrand SA; SKF AB; Alfa Laval AB; Epiroc AB Ordinary Shares - Class A; KONE... |
| BR EQ | acid_country | 3.5399 | 1.3330 | 2.2069 | 0.0012 | -0.0033 | 0.0182 | 0.0118 | 97 | Ambev SA; MercadoLibre Inc; Vale SA; B3 SA - Brasil Bolsa Balcao; Petroleo Brasileiro SA Petrobras ADR; Vibra Energia... |
| EU CD EQ | acid_region_sector | 4.4128 | 2.4765 | 1.9363 | 0.0065 | -0.0022 | 0.0288 | 0.0183 | 129 | adidas AG; Lvmh Moet Hennessy Louis Vuitton SE; Accor SA; Bayerische Motoren Werke AG; Compass Group PLC; Prosus NV O... |
| USD Cash | acid_bond | 1.8726 | 0.0000 | 1.8726 |  |  |  |  | 1 | USD Cash & Equivalents |
| EU CS EQ | acid_region_sector | 4.8099 | 3.1018 | 1.7081 | -0.0008 | -0.0107 | 0.0375 | 0.0240 | 78 | NESTLE SA; Reckitt Benckiser Group Plc; Diageo PLC; L'Oreal SA; Anheuser-Busch InBev SA/NV; Unilever PLC; Pernod Rica... |
| SE EQ | acid_country | 3.8487 | 2.2540 | 1.5947 | -0.0269 | -0.0050 | 0.0140 | 0.0055 | 158 | Atlas Copco AB Class A; SKF AB; Alfa Laval AB; Epiroc AB Ordinary Shares - Class A; Skandinaviska Enskilda Banken AB ... |

### Largest Active Underweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| CA EQ | acid_country | 2.8118 | 8.0762 | -5.2644 | -0.0434 | -0.0065 | 0.0254 | -0.0060 | 207 | Manulife Financial Corp; Canadian National Railway Co; Alimentation Couche-Tard Inc; Parex Resources Inc; Rogers Comm... |
| JP EQ | acid_country | 12.5777 | 15.6231 | -3.0455 | -0.0332 | -0.0071 | 0.0436 | -0.0102 | 870 | Chugai Pharmaceutical Co Ltd; Keyence Corp; ZENKOKU HOSHO CO LTD; Japan Exchange Group Inc; Lasertec Corp; Sony Group... |
| AU EQ | acid_country | 1.5407 | 4.1914 | -2.6507 | -0.0294 | -0.0060 | 0.0169 | 0.0013 | 204 | ASX Ltd; Fortescue Ltd; Woodside Energy Group Ltd; Deterra Royalties Ltd Ordinary Shares; ANZ Group Holdings Ltd; Ram... |
| IN EQ | acid_country | 2.0244 | 4.5318 | -2.5074 | -0.0212 | 0.0003 | 0.0354 | 0.0199 | 560 | Tata Consultancy Services Ltd; HDFC BANK LTD ADR; Indus Towers Ltd Ordinary Shares; Axis Bank Ltd; HDFC BANK LTD; Inf... |
| EU FN EQ | acid_region_sector | 6.5280 | 8.8835 | -2.3555 | -0.0360 | 0.0026 | 0.0182 | -0.0193 | 198 | Banco Bilbao Vizcaya Argentaria SA; Allianz SE; Skandinaviska Enskilda Banken AB Class A; BNP Paribas Act. Cat.A; 3i ... |
| US FN EQ | acid_region_sector | 0.9427 | 2.6348 | -1.6920 | -0.0163 | 0.0059 | 0.0606 | -0.0136 | 28 | Manulife Financial Corp; The Toronto-Dominion Bank; Bank of Montreal; Royal Bank of Canada; Canadian Imperial Bank of... |
| US MT EQ | acid_region_sector | 0.2102 | 1.7275 | -1.5173 | -0.0349 | -0.0083 | 0.0177 | 0.0039 | 60 | James Hardie Industries PLC; Winpak Ltd; Agnico Eagle Mines Ltd; Barrick Mining Corp; Wheaton Precious Metals Corp; F... |
| EU UT EQ | acid_region_sector | 0.4493 | 1.9304 | -1.4811 | -0.0395 | -0.0094 | 0.0077 | 0.0000 | 51 | Veolia Environnement SA; SSE PLC; RWE AG Class A; Iberdrola SA; National Grid PLC; Enel SpA; Engie SA; E.ON SE; Snam ... |
| JP RE EQ | acid_region_sector | 0.0000 | 1.4303 | -1.4303 | -0.0373 | -0.0122 |  |  | 93 | SoftBank Group Corp; Nintendo Co Ltd; KDDI Corp; SoftBank Corp; Mitsubishi Estate Co Ltd; Mitsui Fudosan Co Ltd; NTT ... |
| IT EQ | acid_country | 0.5013 | 1.8356 | -1.3344 | -0.0348 | -0.0023 | 0.0066 | -0.0002 | 71 | Eni SpA; INTESA SANPAOLO SPA; Nexi SpA; UniCredit SpA; Enel SpA; Generali; Prysmian SpA; Leonardo SpA Az nom Post rag... |

### Highest VIR STF Exposures

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|
| AU EN EQ | acid_region_sector | 0.3823 | 0.2179 | 0.1644 | 0.0414 | -0.0078 | 15 | BW LPG Ltd; Woodside Energy Group Ltd; Santos Ltd; Ampol Ltd; Whitehaven Coal Ltd; Paladin Energy Ltd; New Hope Corp ... |
| TR EQ | acid_country | 0.1228 | 0.2478 | -0.1250 | 0.0307 | 0.0063 | 100 | Bim Birlesik Magazalar AS; Aselsan Elektronik Sanayi Ve Ticaret AS; Tupras-Turkiye Petrol Rafineleri AS; Akbank TAS; ... |
| EM RE EQ | acid_region_sector | 1.1921 | 0.5522 | 0.6398 | 0.0226 | 0.0026 | 170 | EMAAR DEV. PJSC; Poly Property Services Co Ltd Class H; Country Garden Services Holdings Co Ltd; Fibra Danhos; EMAAR ... |
| DK EQ | acid_country | 1.4082 | 0.9796 | 0.4285 | 0.0194 | 0.0187 | 38 | DSV AS; Novo Nordisk AS Class B; Genmab AS; Coloplast AS Class B; Pandora AS; Danske Bank AS; Vestas Wind Systems AS;... |
| ID EQ | acid_country | 1.4907 | 0.3651 | 1.1256 | 0.0180 | 0.0005 | 89 | PT Telkom Indonesia (Persero) Tbk Registered Shs Series -B-; PT Bank Mandiri (Persero) Tbk; PT Telkom Indonesia (Pers... |
| PH EQ | acid_country | 0.1234 | 0.1462 | -0.0228 | 0.0152 | -0.0066 | 42 | International Container Terminal Services Inc; SM Investments Corp; BDO Unibank Inc; SM Prime Holdings Inc; Bank of t... |
| AU HC EQ | acid_region_sector | 0.3361 | 0.2867 | 0.0494 | 0.0124 | 0.0144 | 19 | Ramsay Health Care Ltd; Sonic Healthcare Ltd; CSL Ltd; Fisher & Paykel Healthcare Corp Ltd; Sigma Healthcare Ltd; Sin... |
| QA EQ | acid_country | 0.0000 | 0.2119 | -0.2119 | 0.0107 | 0.0003 | 23 | Qatar National Bank SAQ; Qatar Islamic Bank QPSC; Industries Qatar QSC; Ooredoo QPSC; The Commercial Bank (Q.S.C.); A... |
| CN EQ | acid_country | 8.8296 | 7.5253 | 1.3043 | 0.0080 | 0.0067 | 1520 | Contemporary Amperex Technology Co Ltd Class A; Alibaba Group Holding Ltd Ordinary Shares; TENCENT HLDGS. LTD; NetEas... |
| MY EQ | acid_country | 0.4142 | 0.5467 | -0.1325 | 0.0076 | 0.0004 | 112 | Bursa Malaysia Bhd; Inari Amertron Bhd; Greatech Technology Bhd; Malayan Banking Bhd; Public Bank Bhd; Tenaga Nasiona... |

### Largest VIR And Fund Active Gaps

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| CA EQ | acid_country | 2.8118 | 8.0762 | -5.2644 | -0.0434 | -0.0065 | 5.2210 | 207 | Manulife Financial Corp; Canadian National Railway Co; Alimentation Couche-Tard Inc; Parex Resources Inc; Rogers Comm... |
| JP EQ | acid_country | 12.5777 | 15.6231 | -3.0455 | -0.0332 | -0.0071 | 3.0123 | 870 | Chugai Pharmaceutical Co Ltd; Keyence Corp; ZENKOKU HOSHO CO LTD; Japan Exchange Group Inc; Lasertec Corp; Sony Group... |
| UK EQ | acid_country | 11.2401 | 8.4679 | 2.7721 | -0.0195 | -0.0052 | 2.7916 | 200 | Shell PLC; BAE Systems PLC; Rio Tinto PLC Ordinary Shares; GSK PLC; Haleon PLC; Reckitt Benckiser Group Plc; 3i Group... |
| AU EQ | acid_country | 1.5407 | 4.1914 | -2.6507 | -0.0294 | -0.0060 | 2.6213 | 204 | ASX Ltd; Fortescue Ltd; Woodside Energy Group Ltd; Deterra Royalties Ltd Ordinary Shares; ANZ Group Holdings Ltd; Ram... |
| FR EQ | acid_country | 7.6757 | 5.0831 | 2.5926 | -0.0194 | -0.0057 | 2.6120 | 113 | TotalEnergies SE; Legrand SA; BNP Paribas Act. Cat.A; Lvmh Moet Hennessy Louis Vuitton SE; Accor SA; L'Oreal SA; SCHN... |
| MX EQ | acid_country | 3.2207 | 0.6746 | 2.5462 | -0.0156 | -0.0068 | 2.5618 | 48 | Fomento Economico Mexicano SAB de CV ADR; FOMENTO ECONOMICO MEXICAN; Grupo Financiero Banorte SAB de CV Class O; Bols... |
| IN EQ | acid_country | 2.0244 | 4.5318 | -2.5074 | -0.0212 | 0.0003 | 2.4861 | 560 | Tata Consultancy Services Ltd; HDFC BANK LTD ADR; Indus Towers Ltd Ordinary Shares; Axis Bank Ltd; HDFC BANK LTD; Inf... |
| EM CS EQ | acid_region_sector | 3.6142 | 1.2394 | 2.3748 | 0.0073 | -0.0004 | 2.3674 | 275 | Fomento Economico Mexicano SAB de CV ADR; Ambev SA; FOMENTO ECONOMICO MEXICAN; KT&G Corp; Dongsuh Companies Inc; Wal ... |
| EU ID EQ | acid_region_sector | 9.4545 | 7.1535 | 2.3010 | -0.0367 | -0.0035 | 2.3377 | 270 | BAE Systems PLC; Atlas Copco AB Class A; Legrand SA; SKF AB; Alfa Laval AB; Epiroc AB Ordinary Shares - Class A; KONE... |
| EU FN EQ | acid_region_sector | 6.5280 | 8.8835 | -2.3555 | -0.0360 | 0.0026 | 2.3194 | 198 | Banco Bilbao Vizcaya Argentaria SA; Allianz SE; Skandinaviska Enskilda Banken AB Class A; BNP Paribas Act. Cat.A; 3i ... |

### Largest Algo And Fund Active Gaps

| ACID | Type | Target | Bench | Active | Algo Abs | Algo Active | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| CA EQ | acid_country | 2.8118 | 8.0762 | -5.2644 | 0.0254 | -0.0060 | 5.2584 | 207 | Manulife Financial Corp; Canadian National Railway Co; Alimentation Couche-Tard Inc; Parex Resources Inc; Rogers Comm... |
| JP EQ | acid_country | 12.5777 | 15.6231 | -3.0455 | 0.0436 | -0.0102 | 3.0353 | 870 | Chugai Pharmaceutical Co Ltd; Keyence Corp; ZENKOKU HOSHO CO LTD; Japan Exchange Group Inc; Lasertec Corp; Sony Group... |
| UK EQ | acid_country | 11.2401 | 8.4679 | 2.7721 | 0.0418 | 0.0086 | 2.7635 | 200 | Shell PLC; BAE Systems PLC; Rio Tinto PLC Ordinary Shares; GSK PLC; Haleon PLC; Reckitt Benckiser Group Plc; 3i Group... |
| AU EQ | acid_country | 1.5407 | 4.1914 | -2.6507 | 0.0169 | 0.0013 | 2.6520 | 204 | ASX Ltd; Fortescue Ltd; Woodside Energy Group Ltd; Deterra Royalties Ltd Ordinary Shares; ANZ Group Holdings Ltd; Ram... |
| FR EQ | acid_country | 7.6757 | 5.0831 | 2.5926 | 0.0306 | 0.0088 | 2.5838 | 113 | TotalEnergies SE; Legrand SA; BNP Paribas Act. Cat.A; Lvmh Moet Hennessy Louis Vuitton SE; Accor SA; L'Oreal SA; SCHN... |
| MX EQ | acid_country | 3.2207 | 0.6746 | 2.5462 | 0.0033 | 0.0005 | 2.5457 | 48 | Fomento Economico Mexicano SAB de CV ADR; FOMENTO ECONOMICO MEXICAN; Grupo Financiero Banorte SAB de CV Class O; Bols... |
| IN EQ | acid_country | 2.0244 | 4.5318 | -2.5074 | 0.0354 | 0.0199 | 2.5273 | 560 | Tata Consultancy Services Ltd; HDFC BANK LTD ADR; Indus Towers Ltd Ordinary Shares; Axis Bank Ltd; HDFC BANK LTD; Inf... |
| EM CS EQ | acid_region_sector | 3.6142 | 1.2394 | 2.3748 | 0.0142 | 0.0103 | 2.3645 | 275 | Fomento Economico Mexicano SAB de CV ADR; Ambev SA; FOMENTO ECONOMICO MEXICAN; KT&G Corp; Dongsuh Companies Inc; Wal ... |
| EU FN EQ | acid_region_sector | 6.5280 | 8.8835 | -2.3555 | 0.0182 | -0.0193 | 2.3362 | 198 | Banco Bilbao Vizcaya Argentaria SA; Allianz SE; Skandinaviska Enskilda Banken AB Class A; BNP Paribas Act. Cat.A; 3i ... |
| EU ID EQ | acid_region_sector | 9.4545 | 7.1535 | 2.3010 | 0.0171 | -0.0125 | 2.3135 | 270 | BAE Systems PLC; Atlas Copco AB Class A; Legrand SA; SKF AB; Alfa Laval AB; Epiroc AB Ordinary Shares - Class A; KONE... |

## MStar Multisector Bond

- ACID rows: 40
- VIR matched rows: 30
- algo matched rows: 24
- summed target rolled exposure: 96.3373
- summed benchmark rolled exposure: 0.0000

### Largest Active Overweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| US Corp: HY | acid_bond | 31.9944 | 0.0000 | 31.9944 |  |  |  |  | 31 | USD Corporate Bond High Yield_B: 3-5yr; USD Corporate Bond High Yield_BB: 3-5yr; USD Corporate Bond High Yield_BB: 7-... |
| EM HC T: Gbl Div. | acid_bond | 18.6724 | 0.0000 | 18.6724 |  |  |  |  | 61 | USD EM Hard Currency Debt_AA: 7-10yr; USD EM Hard Currency Debt_BB: 10-20yr; USD EM Hard Currency Debt_CCC&Below: 10-... |
| EM LC T: Gbl Div. (JPM) | acid_bond | 16.4149 | 0.0000 | 16.4149 |  |  |  |  | 37 | BRL EM Local Currency Debt_BB: 3-5yr; BRL EM Govt Inflation Linked_BB: 7-10yr; TRY EM Local Currency Debt_BB: 1-3yr; ... |
| US Corp: 1-10 | acid_bond | 12.8522 | 0.0000 | 12.8522 |  |  |  |  | 13 | USD Corporate Bond Inv. Grade_A: 5-7yr; USD Corporate Bond Inv. Grade_A: 7-10yr; USD Corporate Bond Inv. Grade_BBB: 3... |
| US Corp: 10+ | acid_bond | 9.7764 | 0.0000 | 9.7764 |  |  |  |  | 10 | USD Corporate Bond Inv. Grade_A: 10-20yr; USD Corporate Bond Inv. Grade_BBB: 20+yr; USD Corporate Bond Inv. Grade_BBB... |
| USD Cash | acid_bond | 3.5847 | 0.0000 | 3.5847 |  |  |  |  | 11 | USD Cash & Equivalents; EGP EM Cash & Equivalents: 0-3m; NGN EM Cash & Equivalents: 0-3m; USD Corporate Bond High Yie... |
| US T: 1-10 | acid_bond | 0.6659 | 0.0000 | 0.6659 |  |  |  |  | 8 | USD Treasury: 1-3yr; USD Government-Related_BB: 3-5yr; USD Treasury_BB: 5-7yr; USD Treasury_BB: 7-10yr; USD Treasury_... |
| US LRG V EQ | acid_country | 0.3531 | 0.0000 | 0.3531 | -0.0226 | -0.0017 | 0.2219 | -0.0261 | 17 | Bristol-Myers Squibb Co; Morgan Stanley; EXXON MOBIL CORP; Merck & Co Inc; Duke Energy Corp; U.S. Bancorp; Comcast Co... |
| US LRG EQ | acid_country | 0.2076 | 0.0000 | 0.2076 | -0.0320 | 0.0031 |  |  | 8 | ALPHABET INC; TJX Companies Inc; Apple Inc; Microsoft Corp; MASTERCARD INC; Costco Wholesale Corp; Moodys Corp; CME G... |
| US HC EQ | acid_region_sector | 0.2058 | 0.0000 | 0.2058 | -0.0139 | -0.0021 | 0.0654 | 0.0031 | 8 | BioMarin Pharmaceutical Inc; Bristol-Myers Squibb Co; Merck & Co Inc; Gilead Sciences Inc; AbbVie Inc; Cencora Inc; U... |

### Largest Active Underweights

No rows available.

### Highest VIR STF Exposures

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|
| EM RE EQ | acid_region_sector | 0.0005 | 0.0000 | 0.0005 | 0.0226 | 0.0026 | 3 | TIMES CHINA HOLDINGS LTD; YUZHOU GRP. HLDGS. CO LTD; Kaisa Group Holdings Ltd |
| CN EQ | acid_country | 0.0005 | 0.0000 | 0.0005 | 0.0080 | 0.0067 | 3 | TIMES CHINA HOLDINGS LTD; YUZHOU GRP. HLDGS. CO LTD; Kaisa Group Holdings Ltd |
| EU CD EQ | acid_region_sector | 0.0202 | 0.0000 | 0.0202 | 0.0065 | -0.0022 | 1 | Garmin Ltd |
| US SML V EQ | acid_country | 0.0121 | 0.0000 | 0.0121 | -0.0024 | -0.0004 | 1 | Altice USA Inc Class A |
| US HC EQ | acid_region_sector | 0.2058 | 0.0000 | 0.2058 | -0.0139 | -0.0021 | 8 | BioMarin Pharmaceutical Inc; Bristol-Myers Squibb Co; Merck & Co Inc; Gilead Sciences Inc; AbbVie Inc; Cencora Inc; U... |
| US SML EQ | acid_country | 0.0894 | 0.0000 | 0.0894 | -0.0142 | -0.0004 | 1 | BioMarin Pharmaceutical Inc |
| US RE EQ | acid_region_sector | 0.0233 | 0.0000 | 0.0233 | -0.0148 | -0.0057 | 1 | Simon Property Group Inc |
| US FN EQ | acid_region_sector | 0.1533 | 0.0000 | 0.1533 | -0.0163 | 0.0059 | 7 | Morgan Stanley; MASTERCARD INC; U.S. Bancorp; PNC Financial Services Group Inc; Moodys Corp; Citigroup Inc; CME GRP. INC |
| US MID V EQ | acid_country | 0.0218 | 0.0000 | 0.0218 | -0.0173 | -0.0038 | 2 | Kimberly-Clark Corp; Elevance Health Inc |
| DE EQ | acid_country | 0.0184 | 0.0000 | 0.0184 | -0.0181 | -0.0023 | 1 | SAP SE ADR |

### Largest VIR And Fund Active Gaps

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US LRG V EQ | acid_country | 0.3531 | 0.0000 | 0.3531 | -0.0226 | -0.0017 | 0.3757 | 17 | Bristol-Myers Squibb Co; Morgan Stanley; EXXON MOBIL CORP; Merck & Co Inc; Duke Energy Corp; U.S. Bancorp; Comcast Co... |
| US LRG EQ | acid_country | 0.2076 | 0.0000 | 0.2076 | -0.0320 | 0.0031 | 0.2397 | 8 | ALPHABET INC; TJX Companies Inc; Apple Inc; Microsoft Corp; MASTERCARD INC; Costco Wholesale Corp; Moodys Corp; CME G... |
| US HC EQ | acid_region_sector | 0.2058 | 0.0000 | 0.2058 | -0.0139 | -0.0021 | 0.2197 | 8 | BioMarin Pharmaceutical Inc; Bristol-Myers Squibb Co; Merck & Co Inc; Gilead Sciences Inc; AbbVie Inc; Cencora Inc; U... |
| US IT EQ | acid_region_sector | 0.1570 | 0.0000 | 0.1570 | -0.0354 | 0.0054 | 0.1924 | 7 | Broadcom Inc; Apple Inc; Microsoft Corp; Lam Research Corp; Amphenol Corp Class A; Salesforce Inc; Wolfspeed Inc Ordi... |
| US FN EQ | acid_region_sector | 0.1533 | 0.0000 | 0.1533 | -0.0163 | 0.0059 | 0.1696 | 7 | Morgan Stanley; MASTERCARD INC; U.S. Bancorp; PNC Financial Services Group Inc; Moodys Corp; Citigroup Inc; CME GRP. INC |
| US LRG G EQ | acid_country | 0.0943 | 0.0000 | 0.0943 | -0.0408 | 0.0069 | 0.1351 | 5 | Broadcom Inc; Lam Research Corp; Amphenol Corp Class A; GE Aerospace; Howmet Aerospace Inc |
| US MID EQ | acid_country | 0.1134 | 0.0000 | 0.1134 | -0.0211 | -0.0022 | 0.1344 | 7 | Corteva Inc; Simon Property Group Inc; EMERSON ELEC. CO; COLGATE-PALMOLIVE CO; NRG Energy Inc; Cencora Inc; Packaging... |
| US CD EQ | acid_region_sector | 0.0787 | 0.0000 | 0.0787 | -0.0295 | 0.0068 | 0.1082 | 3 | TJX Companies Inc; Royal Caribbean Group; Booking Holdings Inc |
| US SML EQ | acid_country | 0.0894 | 0.0000 | 0.0894 | -0.0142 | -0.0004 | 0.1035 | 1 | BioMarin Pharmaceutical Inc |
| US CS EQ | acid_region_sector | 0.0733 | 0.0000 | 0.0733 | -0.0288 | -0.0092 | 0.1021 | 4 | Costco Wholesale Corp; Procter & Gamble Co; Kimberly-Clark Corp; COLGATE-PALMOLIVE CO |

### Largest Algo And Fund Active Gaps

| ACID | Type | Target | Bench | Active | Algo Abs | Algo Active | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US LRG V EQ | acid_country | 0.3531 | 0.0000 | 0.3531 | 0.2219 | -0.0261 | 0.3792 | 17 | Bristol-Myers Squibb Co; Morgan Stanley; EXXON MOBIL CORP; Merck & Co Inc; Duke Energy Corp; U.S. Bancorp; Comcast Co... |
| US IT EQ | acid_region_sector | 0.1570 | 0.0000 | 0.1570 | 0.1353 | -0.0620 | 0.2190 | 7 | Broadcom Inc; Apple Inc; Microsoft Corp; Lam Research Corp; Amphenol Corp Class A; Salesforce Inc; Wolfspeed Inc Ordi... |
| US HC EQ | acid_region_sector | 0.2058 | 0.0000 | 0.2058 | 0.0654 | 0.0031 | 0.2027 | 8 | BioMarin Pharmaceutical Inc; Bristol-Myers Squibb Co; Merck & Co Inc; Gilead Sciences Inc; AbbVie Inc; Cencora Inc; U... |
| US FN EQ | acid_region_sector | 0.1533 | 0.0000 | 0.1533 | 0.0606 | -0.0136 | 0.1669 | 7 | Morgan Stanley; MASTERCARD INC; U.S. Bancorp; PNC Financial Services Group Inc; Moodys Corp; Citigroup Inc; CME GRP. INC |
| US LRG G EQ | acid_country | 0.0943 | 0.0000 | 0.0943 | 0.1795 | -0.0602 | 0.1545 | 5 | Broadcom Inc; Lam Research Corp; Amphenol Corp Class A; GE Aerospace; Howmet Aerospace Inc |
| US CD EQ | acid_region_sector | 0.0787 | 0.0000 | 0.0787 | 0.0416 | -0.0192 | 0.0979 | 3 | TJX Companies Inc; Royal Caribbean Group; Booking Holdings Inc |
| US ID EQ | acid_region_sector | 0.0545 | 0.0000 | 0.0545 | 0.0246 | -0.0351 | 0.0896 | 4 | GE Aerospace; EMERSON ELEC. CO; Howmet Aerospace Inc; UNITED PARCEL SERV. INC |
| US TL EQ | acid_region_sector | 0.0689 | 0.0000 | 0.0689 | 0.0499 | -0.0167 | 0.0856 | 3 | ALPHABET INC; Comcast Corp Class A; Altice USA Inc Class A |
| US CS EQ | acid_region_sector | 0.0733 | 0.0000 | 0.0733 | 0.0396 | 0.0065 | 0.0668 | 4 | Costco Wholesale Corp; Procter & Gamble Co; Kimberly-Clark Corp; COLGATE-PALMOLIVE CO |
| US MT EQ | acid_region_sector | 0.0535 | 0.0000 | 0.0535 | 0.0177 | 0.0039 | 0.0496 | 3 | Corteva Inc; Kinross Gold Corp; Packaging Corp of America |

## MStar Municipal Bond

- ACID rows: 5
- VIR matched rows: 0
- algo matched rows: 0
- summed target rolled exposure: 100.0000
- summed benchmark rolled exposure: 9.3490

### Largest Active Overweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| US Muni: 22+ | acid_bond | 33.4065 | 2.6598 | 30.7467 |  |  |  |  | 7 | USD Municipal Inv. Grade_A: 20+yr; USD Municipal High Yield: 20+yr; USD Municipal Inv. Grade_AA: 20+yr; USD Municipal... |
| US Muni: 15y (12-17) | acid_bond | 29.9553 | 1.0713 | 28.8840 |  |  |  |  | 7 | USD Municipal Inv. Grade_AA: 10-20yr; USD Municipal Inv. Grade_AAA: 10-20yr; USD Municipal Inv. Grade_BBB: 10-20yr; U... |
| US Muni: 1-10y (1-12) | acid_bond | 30.0330 | 5.6126 | 24.4204 |  |  |  |  | 28 | USD Municipal Inv. Grade_BBB: 3-5yr; USD Municipal Inv. Grade_A: 1-3yr; USD Municipal Inv. Grade_A: 3-5yr; USD Munici... |
| USD Cash | acid_bond | 4.9826 | 0.0000 | 4.9826 |  |  |  |  | 6 | USD Cash & Equivalents; USD Municipal Inv. Grade_A: 0-3m; USD Municipal High Yield: 0-3m; USD EM Municipal_A: 0-3m; U... |
| EM HC T: Gbl Div. | acid_bond | 1.6226 | 0.0054 | 1.6173 |  |  |  |  | 7 | USD EM Municipal: 3-5yr; USD EM Municipal: 20+yr; USD EM Municipal: 7-10yr; USD EM Municipal: 1-3yr; USD EM Municipal... |

### Largest Active Underweights

No rows available.

### Highest VIR STF Exposures

No rows available.

### Largest VIR And Fund Active Gaps

No rows available.

### Largest Algo And Fund Active Gaps

No rows available.

## MStar Total Return Bond

- ACID rows: 48
- VIR matched rows: 1
- algo matched rows: 0
- summed target rolled exposure: 86.0850
- summed benchmark rolled exposure: 0.0000

### Largest Active Overweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| US Secu | acid_bond | 38.3231 | 0.0000 | 38.3231 |  |  |  |  | 67 | USD Agency Mortgage-Backed: 20+yr; USD Asset-Backed: 10-20yr; USD Asset-Backed_AA: 10-20yr; USD Nonagency Residential... |
| US T: 1-10 | acid_bond | 26.4993 | 0.0000 | 26.4993 |  |  |  |  | 7 | USD Treasury_AA: 1-3yr; USD Treasury_AA: 3-5yr; USD Treasury_AA: 5-7yr; USD Treasury_AA: 7-10yr; USD Treasury_AA: 3m-... |
| US T: 10+ | acid_bond | 11.0348 | 0.0000 | 11.0348 |  |  |  |  | 5 | USD Treasury_AA: 20+yr; USD Treasury_AA: 10-20yr; USD Treasury: 10-20yr; USD Treasury: 20+yr; USD Government-Related_... |
| US Corp: 1-10 | acid_bond | 8.8020 | 0.0000 | 8.8020 |  |  |  |  | 17 | USD Corporate Bond Inv. Grade_BBB: 3-5yr; USD Corporate Bond Inv. Grade_A: 5-7yr; USD Corporate Bond Inv. Grade_BBB: ... |
| US Corp: 10+ | acid_bond | 5.0631 | 0.0000 | 5.0631 |  |  |  |  | 11 | USD Corporate Bond Inv. Grade_BBB: 20+yr; USD Corporate Bond Inv. Grade_A: 20+yr; USD Corporate Bond Inv. Grade_BBB: ... |
| US Corp: HY | acid_bond | 3.7301 | 0.0000 | 3.7301 |  |  |  |  | 24 | USD Corporate Bond High Yield_BB: 3m-1yr; USD Corporate Bond High Yield: 5-7yr; USD Corporate Bond High Yield: 3-5yr;... |
| US IL: 1-10 | acid_bond | 1.8328 | 0.0000 | 1.8328 |  |  |  |  | 2 | USD Govt Inflation Linked_AA: 7-10yr; USD Govt Inflation Linked_AA: 3-5yr |
| EM HC T: Gbl Div. | acid_bond | 1.0446 | 0.0000 | 1.0446 |  |  |  |  | 33 | USD EM Corporate_BBB: 3-5yr; USD EM Hard Currency Debt_BBB: 5-7yr; USD EM Corporate_AA: 10-20yr; USD EM Hard Currency... |
| EM LC T: Gbl Div. (JPM) | acid_bond | 0.8991 | 0.0000 | 0.8991 |  |  |  |  | 70 | PHP EM Local Currency Debt: 3-5yr; CNY EM Local Currency Debt_A: 1-3yr; CNY EM Local Currency Debt_A: 3-5yr; CNY EM C... |
| AU T: 1-10 | acid_bond | 0.4608 | 0.0000 | 0.4608 |  |  |  |  | 4 | AUD Treasury_AAA: 7-10yr; AUD Treasury_AAA: 3-5yr; AUD Treasury_AAA: 1-3yr; AUD Treasury_AAA: 5-7yr |

### Largest Active Underweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| USD Cash | acid_bond | -14.3260 | 0.0000 | -14.3260 |  |  |  |  | 12 | USD Cash & Equivalents; USD Corporate Bond Inv. Grade_BBB: 0-3m; USD Bank Loan High Yield: 0-3m; BRL EM Local Currenc... |

### Highest VIR STF Exposures

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|
| US EQ | acid_country | 0.0352 | 0.0000 | 0.0352 | -0.0276 | 0.0023 | 6 | FUT. EMINI S&P JUN26; OPT. CBOE VO C 35 19/5/26; OPT. CBOE VO C 35 15/4/26; OPT. CBOE VO C 50 15/4/26; OPT. CBOE VO C... |

### Largest VIR And Fund Active Gaps

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US EQ | acid_country | 0.0352 | 0.0000 | 0.0352 | -0.0276 | 0.0023 | 0.0629 | 6 | FUT. EMINI S&P JUN26; OPT. CBOE VO C 35 19/5/26; OPT. CBOE VO C 35 15/4/26; OPT. CBOE VO C 50 15/4/26; OPT. CBOE VO C... |

### Largest Algo And Fund Active Gaps

No rows available.

## MStar US Equity

- ACID rows: 49
- VIR matched rows: 47
- algo matched rows: 42
- summed target rolled exposure: 199.1426
- summed benchmark rolled exposure: 199.9778

### Largest Active Overweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| US ID EQ | acid_region_sector | 13.5426 | 10.1119 | 3.4307 | -0.0441 | -0.0058 | 0.0246 | -0.0351 | 278 | RTX Corp; Honeywell International Inc; Eaton Corp PLC; W.W. Grainger Inc; Boeing Co; General Dynamics Corp; EMERSON E... |
| US SML V EQ | acid_country | 4.6172 | 1.6520 | 2.9652 | -0.0024 | -0.0004 | 0.0076 | 0.0057 | 425 | Chord Energy Corp Ordinary Shares - New; Baxter International Inc; Clorox Co; Brown-Forman Corp Registered Shs -B- No... |
| US MID V EQ | acid_country | 8.4709 | 5.8568 | 2.6141 | -0.0173 | -0.0038 | 0.0665 | 0.0023 | 127 | The Cigna Group; Cognizant Technology Solutions Corp Class A; The Travelers Companies Inc; Dominion Energy Inc; Fox C... |
| US FN EQ | acid_region_sector | 15.0538 | 12.4971 | 2.5567 | -0.0163 | 0.0059 | 0.0606 | -0.0136 | 280 | JPMorgan Chase & Co; Visa Inc Class A; Progressive Corp; MASTERCARD INC; BLACKROCK INC; Morgan Stanley; Nasdaq Inc; T... |
| US SML G EQ | acid_country | 3.6737 | 1.3874 | 2.2864 | -0.0252 | -0.0005 | 0.0028 | 0.0014 | 214 | HealthEquity Inc; Everus Construction Group Inc; Balchem Corp; Federal Signal Corp; Ensign Group Inc; Enpro Inc; Site... |
| US SML EQ | acid_country | 4.8845 | 2.7007 | 2.1839 | -0.0142 | -0.0004 |  |  | 414 | Healthpeak Properties Inc; Standex International Corp; Kadant Inc; Jack Henry & Associates Inc; SEI Investments Co; C... |
| US HC EQ | acid_region_sector | 11.0562 | 9.6972 | 1.3590 | -0.0139 | -0.0021 | 0.0654 | 0.0031 | 188 | Johnson & Johnson; The Cigna Group; McKesson Corp; Intuitive Surgical Inc; Vertex Pharmaceuticals Inc; Pfizer Inc; Th... |
| US MID EQ | acid_country | 9.3868 | 8.4265 | 0.9602 | -0.0211 | -0.0022 |  |  | 170 | W.W. Grainger Inc; EMERSON ELEC. CO; Nasdaq Inc; Raymond James Financial Inc; Airbnb Inc Ordinary Shares - Class A; C... |
| USD Cash | acid_bond | 0.8333 | 0.0000 | 0.8333 |  |  |  |  | 3 | USD Cash & Equivalents; USD Government-Related: 0-3m; GBP Cash & Equivalents |
| EU IT EQ | acid_region_sector | 0.8117 | 0.0782 | 0.7335 | -0.0263 | -0.0021 | 0.0153 | 0.0029 | 2 | ASML Holding NV ADR; NXP Semiconductors NV |

### Largest Active Underweights

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Algo Abs | Algo Active | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|---|
| US LRG G EQ | acid_country | 12.2265 | 19.1116 | -6.8851 | -0.0408 | 0.0069 | 0.1795 | -0.0602 | 29 | NVIDIA Corp; Netflix Inc; Boeing Co; Broadcom Inc; Palo Alto Networks Inc; Analog Devices Inc; Intuitive Surgical Inc... |
| US IT EQ | acid_region_sector | 25.3669 | 31.0713 | -5.7044 | -0.0354 | 0.0054 | 0.1353 | -0.0620 | 222 | NVIDIA Corp; Apple Inc; Microsoft Corp; Cisco Systems Inc; Broadcom Inc; Palo Alto Networks Inc; Analog Devices Inc; ... |
| US LRG EQ | acid_country | 27.8910 | 33.0880 | -5.1971 | -0.0320 | 0.0031 |  |  | 50 | Apple Inc; Amazon.com Inc; Microsoft Corp; Meta Platforms Inc Class A; ALPHABET INC; Visa Inc Class A; MASTERCARD INC... |
| US CD EQ | acid_region_sector | 6.6346 | 9.8223 | -3.1877 | -0.0295 | 0.0068 | 0.0416 | -0.0192 | 198 | Amazon.com Inc; Lowe's Companies Inc; Marriott International Inc Class A; Airbnb Inc Ordinary Shares - Class A; TESLA... |
| US TL EQ | acid_region_sector | 7.5933 | 9.9179 | -2.3245 | -0.0228 | 0.0073 | 0.0499 | -0.0167 | 64 | Meta Platforms Inc Class A; ALPHABET INC; Netflix Inc; Fox Corp Class A; Comcast Corp Class A; Verizon Communications... |
| US MID G EQ | acid_country | 3.9298 | 5.4294 | -1.4996 | -0.0270 | -0.0012 | 0.0431 | -0.0185 | 118 | CHIPOTLE MEXICAN GRILL IN; Rockwell Automation Inc; Synopsys Inc; MONSTER BEVERAGE CORP; EQUIFAX INC; Dow Inc; Fabrin... |
| US LRG V EQ | acid_country | 20.9403 | 21.5503 | -0.6100 | -0.0226 | -0.0017 | 0.2219 | -0.0261 | 69 | JPMorgan Chase & Co; Johnson & Johnson; Progressive Corp; Cisco Systems Inc; EXXON MOBIL CORP; Honeywell Internationa... |
| US RE EQ | acid_region_sector | 1.7507 | 2.2406 | -0.4899 | -0.0148 | -0.0057 |  |  | 107 | Prologis Inc; Healthpeak Properties Inc; REALTY INC. CORP; Crown Castle Inc; AvalonBay Communities Inc; SBA Communica... |
| BR EQ | acid_country | 0.0000 | 0.1334 | -0.1334 | 0.0012 | -0.0033 | 0.0182 | 0.0118 | 1 | MercadoLibre Inc |
| EM CD EQ | acid_region_sector | 0.0000 | 0.1334 | -0.1334 | 0.0057 | 0.0025 | 0.0419 | 0.0288 | 1 | MercadoLibre Inc |

### Highest VIR STF Exposures

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|
| CN EQ | acid_country | 0.3555 | 0.1005 | 0.2550 | 0.0080 | 0.0067 | 3 | Camtek Ltd; Nova Ltd; TE Connectivity PLC Registered Shares |
| EU CD EQ | acid_region_sector | 0.0300 | 0.0732 | -0.0432 | 0.0065 | -0.0022 | 2 | Autoliv Inc; Garmin Ltd |
| EM CD EQ | acid_region_sector | 0.0000 | 0.1334 | -0.1334 | 0.0057 | 0.0025 | 1 | MercadoLibre Inc |
| BR EQ | acid_country | 0.0000 | 0.1334 | -0.1334 | 0.0012 | -0.0033 | 1 | MercadoLibre Inc |
| EU CS EQ | acid_region_sector | 0.3878 | 0.0000 | 0.3878 | -0.0008 | -0.0107 | 4 | NESTLE SA; Reckitt Benckiser Group Plc; Coca-Cola Europacific Partners PLC; Diageo PLC |
| US SML V EQ | acid_country | 4.6172 | 1.6520 | 2.9652 | -0.0024 | -0.0004 | 425 | Chord Energy Corp Ordinary Shares - New; Baxter International Inc; Clorox Co; Brown-Forman Corp Registered Shs -B- No... |
| EM FN EQ | acid_region_sector | 0.0152 | 0.0142 | 0.0010 | -0.0077 | -0.0004 | 4 | First BanCorp; OFG Bancorp; Evertec Inc; Popular Inc |
| EU HC EQ | acid_region_sector | 0.1898 | 0.0190 | 0.1708 | -0.0081 | -0.0014 | 3 | Roche Holding AG ADR; Roivant Sciences Ltd Ordinary Shares; uniQure NV |
| HK EQ | acid_country | 0.0021 | 0.0000 | 0.0021 | -0.0084 | -0.0012 | 1 | Alpha & Omega Semiconductor Ltd |
| IE EQ | acid_country | 0.0000 | 0.0338 | -0.0338 | -0.0136 | -0.0009 | 1 | Smurfit WestRock PLC |

### Largest VIR And Fund Active Gaps

| ACID | Type | Target | Bench | Active | VIR STF | VIR dSTF | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US LRG G EQ | acid_country | 12.2265 | 19.1116 | -6.8851 | -0.0408 | 0.0069 | 6.8443 | 29 | NVIDIA Corp; Netflix Inc; Boeing Co; Broadcom Inc; Palo Alto Networks Inc; Analog Devices Inc; Intuitive Surgical Inc... |
| US IT EQ | acid_region_sector | 25.3669 | 31.0713 | -5.7044 | -0.0354 | 0.0054 | 5.6690 | 222 | NVIDIA Corp; Apple Inc; Microsoft Corp; Cisco Systems Inc; Broadcom Inc; Palo Alto Networks Inc; Analog Devices Inc; ... |
| US LRG EQ | acid_country | 27.8910 | 33.0880 | -5.1971 | -0.0320 | 0.0031 | 5.1650 | 50 | Apple Inc; Amazon.com Inc; Microsoft Corp; Meta Platforms Inc Class A; ALPHABET INC; Visa Inc Class A; MASTERCARD INC... |
| US ID EQ | acid_region_sector | 13.5426 | 10.1119 | 3.4307 | -0.0441 | -0.0058 | 3.4748 | 278 | RTX Corp; Honeywell International Inc; Eaton Corp PLC; W.W. Grainger Inc; Boeing Co; General Dynamics Corp; EMERSON E... |
| US CD EQ | acid_region_sector | 6.6346 | 9.8223 | -3.1877 | -0.0295 | 0.0068 | 3.1582 | 198 | Amazon.com Inc; Lowe's Companies Inc; Marriott International Inc Class A; Airbnb Inc Ordinary Shares - Class A; TESLA... |
| US SML V EQ | acid_country | 4.6172 | 1.6520 | 2.9652 | -0.0024 | -0.0004 | 2.9676 | 425 | Chord Energy Corp Ordinary Shares - New; Baxter International Inc; Clorox Co; Brown-Forman Corp Registered Shs -B- No... |
| US MID V EQ | acid_country | 8.4709 | 5.8568 | 2.6141 | -0.0173 | -0.0038 | 2.6314 | 127 | The Cigna Group; Cognizant Technology Solutions Corp Class A; The Travelers Companies Inc; Dominion Energy Inc; Fox C... |
| US FN EQ | acid_region_sector | 15.0538 | 12.4971 | 2.5567 | -0.0163 | 0.0059 | 2.5730 | 280 | JPMorgan Chase & Co; Visa Inc Class A; Progressive Corp; MASTERCARD INC; BLACKROCK INC; Morgan Stanley; Nasdaq Inc; T... |
| US SML G EQ | acid_country | 3.6737 | 1.3874 | 2.2864 | -0.0252 | -0.0005 | 2.3115 | 214 | HealthEquity Inc; Everus Construction Group Inc; Balchem Corp; Federal Signal Corp; Ensign Group Inc; Enpro Inc; Site... |
| US TL EQ | acid_region_sector | 7.5933 | 9.9179 | -2.3245 | -0.0228 | 0.0073 | 2.3017 | 64 | Meta Platforms Inc Class A; ALPHABET INC; Netflix Inc; Fox Corp Class A; Comcast Corp Class A; Verizon Communications... |

### Largest Algo And Fund Active Gaps

| ACID | Type | Target | Bench | Active | Algo Abs | Algo Active | Gap | Sec Ct | Sample Securities |
|---|---|---|---|---|---|---|---|---|---|
| US LRG G EQ | acid_country | 12.2265 | 19.1116 | -6.8851 | 0.1795 | -0.0602 | 6.8249 | 29 | NVIDIA Corp; Netflix Inc; Boeing Co; Broadcom Inc; Palo Alto Networks Inc; Analog Devices Inc; Intuitive Surgical Inc... |
| US IT EQ | acid_region_sector | 25.3669 | 31.0713 | -5.7044 | 0.1353 | -0.0620 | 5.6424 | 222 | NVIDIA Corp; Apple Inc; Microsoft Corp; Cisco Systems Inc; Broadcom Inc; Palo Alto Networks Inc; Analog Devices Inc; ... |
| US ID EQ | acid_region_sector | 13.5426 | 10.1119 | 3.4307 | 0.0246 | -0.0351 | 3.4658 | 278 | RTX Corp; Honeywell International Inc; Eaton Corp PLC; W.W. Grainger Inc; Boeing Co; General Dynamics Corp; EMERSON E... |
| US CD EQ | acid_region_sector | 6.6346 | 9.8223 | -3.1877 | 0.0416 | -0.0192 | 3.1685 | 198 | Amazon.com Inc; Lowe's Companies Inc; Marriott International Inc Class A; Airbnb Inc Ordinary Shares - Class A; TESLA... |
| US SML V EQ | acid_country | 4.6172 | 1.6520 | 2.9652 | 0.0076 | 0.0057 | 2.9595 | 425 | Chord Energy Corp Ordinary Shares - New; Baxter International Inc; Clorox Co; Brown-Forman Corp Registered Shs -B- No... |
| US MID V EQ | acid_country | 8.4709 | 5.8568 | 2.6141 | 0.0665 | 0.0023 | 2.6118 | 127 | The Cigna Group; Cognizant Technology Solutions Corp Class A; The Travelers Companies Inc; Dominion Energy Inc; Fox C... |
| US FN EQ | acid_region_sector | 15.0538 | 12.4971 | 2.5567 | 0.0606 | -0.0136 | 2.5703 | 280 | JPMorgan Chase & Co; Visa Inc Class A; Progressive Corp; MASTERCARD INC; BLACKROCK INC; Morgan Stanley; Nasdaq Inc; T... |
| US TL EQ | acid_region_sector | 7.5933 | 9.9179 | -2.3245 | 0.0499 | -0.0167 | 2.3078 | 64 | Meta Platforms Inc Class A; ALPHABET INC; Netflix Inc; Fox Corp Class A; Comcast Corp Class A; Verizon Communications... |
| US SML G EQ | acid_country | 3.6737 | 1.3874 | 2.2864 | 0.0028 | 0.0014 | 2.2850 | 214 | HealthEquity Inc; Everus Construction Group Inc; Balchem Corp; Federal Signal Corp; Ensign Group Inc; Enpro Inc; Site... |
| US MID G EQ | acid_country | 3.9298 | 5.4294 | -1.4996 | 0.0431 | -0.0185 | 1.4811 | 118 | CHIPOTLE MEXICAN GRILL IN; Rockwell Automation Inc; Synopsys Inc; MONSTER BEVERAGE CORP; EQUIFAX INC; Dow Inc; Fabrin... |
