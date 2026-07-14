# Copilot Prompt — SDM Valuación Inteligente

Pegar completo en GitHub Copilot Chat (Ctrl+Alt+I) dentro del proyecto Rayfin.

---

Build a used vehicle valuation app for Santo Domingo Motors (Dominican Republic).

The app is used by a sales advisor who receives a used vehicle and needs to valuate it.

## MAIN FLOW

1. **Upload Section**: allow uploading 2-6 photos of the vehicle (front, rear, interior, dashboard, damage detail). Show photo thumbnails after upload. Minimum 2 photos required.

2. **Vehicle Form**: fields for brand, model, year, kilometers, declared condition.
   - Brands: Nissan, Chevrolet, Suzuki, Infiniti, Cadillac, Yamaha
   - Models per brand (populate dynamically based on brand selection):
     - Nissan: Sentra, Versa, X-Trail, Frontier, Kicks, Qashqai, Pathfinder
     - Chevrolet: Tracker, Cruze, Equinox, Trax, Silverado, Onix
     - Suzuki: Swift, Vitara, Jimny, S-Cross, Grand Vitara
     - Infiniti: Q50, QX50, Q60, QX60, QX80
     - Cadillac: CT4, CT5, XT4, XT5, XT6, Escalade
     - Yamaha: MT-03, YZF-R3, FZ-25, XMAX 300, Tenere 700
   - Conditions: Excelente, Muy Bueno, Bueno, Regular, Deteriorado
   - Year range: 2010-2024

3. **Analyze Button**: sends all photos to Azure OpenAI GPT-4.1 Vision.

   Vision prompt must evaluate:
   - Vehicle brand and model (confirm vs declared)
   - Visible damage (scratches, dents, broken lights, fire/flood damage)
   - Interior condition (seats, dashboard, steering wheel)
   - Dashboard reading (mileage if visible)
   - Overall condition score using THESE EXACT CRITERIA:
     - Excelente: no visible damage, interior pristine, low mileage confirmed
     - MuyBueno: minor superficial scratches only, interior in good shape
     - Bueno: some visible scratches or dents, acceptable interior
     - Regular: multiple dents, worn interior, high mileage confirmed
     - Deteriorado: severe structural damage, fire or flood damage, major accidents, missing parts, engine exposed, or any condition that makes the vehicle unsafe or non-operational

4. **Results Panel**: show
   - Vision analysis summary (in Spanish)
   - Detected condition vs declared condition
   - Suggested purchase price in RD$ (use local pricing table below)
   - Alert banner if detected condition differs from declared condition

5. **Confirm & Save Button**: saves the valuation to Rayfin SQL Database using RayfinClient.
   - Entity name: VehicleValuation
   - Fields: vehicleId (auto UUID), brand, model, year, km, declaredCondition, detectedCondition, purchasePriceRD, visibleDamage, advisorNotes, createdAt (timestamp), sucursal

6. **History Tab**: shows last 10 valuations from RayfinClient query.
   - Columns: Date, Brand, Model, Year, Detected Condition, Price RD$

## LOCAL PRICING TABLE (no external API call — fallback only)

```javascript
const PRICING = {
  'Nissan':    { base: 850000, models: ['Sentra','Versa','X-Trail','Frontier','Kicks','Qashqai','Pathfinder'], modelOverrides: { 'Qashqai': 950000, 'Pathfinder': 1800000 } },
  'Chevrolet': { base: 950000, models: ['Tracker','Cruze','Equinox','Trax','Silverado','Onix'], modelOverrides: { 'Silverado': 2500000 } },
  'Suzuki':    { base: 650000, models: ['Swift','Vitara','Jimny','S-Cross','Grand Vitara'] },
  'Infiniti':  { base: 1800000, models: ['Q50','QX50','Q60','QX60','QX80'] },
  'Cadillac':  { base: 3500000, models: ['CT4','CT5','XT4','XT5','XT6','Escalade'] },
  'Yamaha':    { base: 280000, models: ['MT-03','YZF-R3','FZ-25','XMAX 300','Tenere 700'] },
};

// Price calculation:
// basePrice = modelOverrides[model] ?? brand.base
// factor_year = 1.0 - (2024 - year) * 0.07
// factor_km   = 1.0 - (km / 200000) * 0.25
// factor_cond = { Excelente:0.90, MuyBueno:0.78, Bueno:0.65, Regular:0.50, Deteriorado:0.32 }
// precio_mercado = basePrice * factor_year * factor_km * factor_cond
// precio_compra_sugerido = precio_mercado * 0.82
```

## ENVIRONMENT VARIABLES

```javascript
import.meta.env.VITE_RAYFIN_AZURE_OPENAI_ENDPOINT
import.meta.env.VITE_RAYFIN_AZURE_OPENAI_KEY
import.meta.env.VITE_RAYFIN_AZURE_OPENAI_DEPLOYMENT
```

## STYLE

- Professional dark blue (#0078D4) as primary color
- All UI labels in Spanish
- Currency: Dominican Peso (RD$)
- Use Tailwind CSS
- No HTML form tags — use onClick/onChange handlers only
- Alert for condition mismatch must be visually prominent (red banner)
