# Schermontwerpen — Desktop ↔ Mobile nummering

Zelfde proces, zelfde volgorde; **mobile gebruikt vaak +3 in het inkoop-blok** (2.2.x desktop → 2.2.(x+3) mobile).

| Proces | Desktop (`Desktop/`) | Mobile (`Mobile/`) | Flask-template |
|--------|----------------------|--------------------|----------------|
| Verkoop | Schermopname **1.2.1**–**1.2.4** | `Klant_zoeken (1.2).svg`, `Klant (1.2).svg`, `Bestelling (1.2).svg`, `Afronden (1.2).svg` | `index.html` (secties 1.2.1–1.2.4) |
| Inkoop minimum | **2.2.1** | **2.2.4** `2.2.4-products-below-minimum-stock.png` | `inkoop-2-2-1.html` |
| Inkoop leverancier | **2.2.2** | **2.2.5** `2.2.5-cheapest-manufacturer.png` | `inkoop-2-2-2.html` |
| Inkoop bevestigd | **2.2.3** | **2.2.6** `2.2.6-purchase-order-registered.png` | `inkoop-2-2-3.html` |
| Orderpicking | **3.2.1** desktop | **3.2.2** `3.2.2 Wireframe orderpicking - mobiel.png` | `orderpicking.html` |
| Distributie | **4.2.1** (responsive) | — (zelfde scherm, mobiel layout) | `distributie.html` |
| Administratie | **5.2** `TimaFlu - Wireframe (5.2).svg` | **5.2** `TimaFlu - Mobiel wireframe (5.2).svg` | `administratie.html` |
| Acquisitie | **6.21**–**6.23** | — | `acquisition-6-22.html` |

Breakpoint app: **≤768px** = mobile variant (`wf-board--mobile` / card layouts).
