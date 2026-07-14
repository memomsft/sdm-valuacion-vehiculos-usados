# SDM — Valuación Inteligente de Vehículos Usados
**Microsoft Fabric + Azure OpenAI GPT-4.1 Vision**

Demo end-to-end de valuación inteligente de vehículos usados para AI Days y presentaciones ejecutivas.

---

## Arquitectura

```
Fotos del vehículo
      ↓
Fabric App (Rayfin) — UI del asesor
      ↓
GPT-4.1 Vision — analiza condición, daños, kilometraje
      ↓
Tabla de precios local (fallback) → precio sugerido en RD$
      ↓
SQL Database de Fabric — historial de valuaciones

Momento 2 — separado en demo:
Fabric Data Agent → consultas en lenguaje natural sobre Lakehouse
```

### ⚠️ Limitación crítica — Lakehouse desde la Fabric App

El token de sesión de Rayfin **no tiene scope para llamar a la Fabric API**. Cualquier intento de consultar el Lakehouse desde el frontend devuelve 401.

**Solución:** los precios viven como fallback local hardcodeado en el código del app. El Lakehouse se usa exclusivamente para el **Fabric Data Agent**, que corre con identidad de usuario y no tiene este problema.

---

## Pre-requisitos

| Requisito | Detalle |
|---|---|
| Microsoft Fabric | Capacidad F-SKU — no Trial |
| Región del workspace | North Central US, West US, o West US 2 — **NO Mexico Central** |
| Azure OpenAI | Deployment de `gpt-4.1` con Vision habilitado |
| Node.js | v22 LTS |
| Tenant setting | Admin Portal → Tenant settings → Fabric Apps (preview) → Enable |

---

## Estructura del repo

```
sdm-valuacion-inteligente/
├── README.md
├── notebooks/
│   └── nb_generar_datos_sdm.py     ← ejecutar en Fabric Notebook
├── prompts/
│   └── copilot_prompt.md           ← prompt para GitHub Copilot
├── imagenes/
│   ├── auto01_nissan_versa_*.png
│   ├── auto02_suzuki_vitara_*.png
│   ├── auto03_chevrolet_silverado_*.png
│   └── auto04_nissan_qashqai_*.png  ← vehículo con daño por incendio
└── data/
    └── precios_mercado_usados.csv
```

---

## Pasos de despliegue

### 1 — Crear el workspace en Fabric

1. Ir a `app.fabric.microsoft.com`
2. **Workspaces → + New workspace**
3. Nombre: `sdm-inteligencia-comercial`
4. **Advanced → Fabric capacity** → seleccionar capacity en región soportada
5. Apply

### 2 — Crear el Lakehouse

1. En el workspace: **+ New item → Lakehouse**
2. Nombre: `lh_sdm_usados` → Create

### 3 — Generar datos sintéticos

1. **+ New item → Notebook**
2. Nombre: `nb_generar_datos_sdm`
3. Copiar el contenido de `notebooks/nb_generar_datos_sdm.py`
4. Ejecutar — resultado esperado:
```
Tabla creada: 200 registros
Rango de precios: RD$ 45,000 – RD$ 2,800,000
```

### 4 — Crear el Fabric Data Agent

1. **+ New item → Data agent**
2. Nombre: `agent_valuacion_sdm`
3. **+ Add data → lh_sdm_usados → precios_mercado_usados → Confirm**

**Data source description:**
```
Tabla de precios de mercado de vehículos usados de Santo Domingo Motors (SDM),
República Dominicana. Contiene precios de mercado y precios de compra sugeridos
por marca, modelo, año, kilometraje y condición. Incluye inventario por sucursal
y días en inventario.
```

**Data source instructions:**
```
- Usa siempre pesos dominicanos (RD$)
- precio_compra_sugerido_rd es lo que SDM debería pagar al cliente
- precio_mercado_rd es el precio de reventa estimado
- Busca el registro más cercano por marca, modelo, año y condición
- Responde siempre en español
```

**System prompt:**
```
Eres el agente de valuación de vehículos usados de Santo Domingo Motors.
Responde siempre en español. Usa pesos dominicanos (RD$).
Cuando pidan comparaciones o análisis de múltiples registros, genera
visualizaciones con Code Interpreter. Usa gráficos de barras para
comparaciones por marca o sucursal, y pie charts para distribución de condición.
```

5. Settings → Tools → habilitar **Code Interpreter**
6. Probar con:
   - *"¿Cuál es el precio promedio de compra por marca?"*
   - *"¿Qué vehículos llevan más de 60 días en inventario?"*
   - *"¿Cuál es la distribución de condición del inventario?"*
7. **Publish**

### 5 — Crear el Fabric App item

1. **+ New item → App**
2. Nombre: `sdm-valuacion`
3. Copiar el comando de deploy que genera Fabric

### 6 — Scaffold con Rayfin CLI

En PowerShell (no cmd):

```powershell
# Usar el comando que generó Fabric en el paso anterior
npm create @microsoft/rayfin@latest -- "sdm-valuacion" --workspace "sdm-inteligencia-comercial"
cd sdm-valuacion
code .
```

Cuando pregunte template: seleccionar **`dataapp`**

### 7 — Configurar variables de entorno

Crear el archivo `rayfin/.env` — **no `.env.local`** (Rayfin lo sobreescribe en cada deploy):

```env
RAYFIN_PUBLIC_AZURE_OPENAI_ENDPOINT=https://<tu-recurso>.openai.azure.com/
RAYFIN_PUBLIC_AZURE_OPENAI_KEY=<tu-api-key>
RAYFIN_PUBLIC_AZURE_OPENAI_DEPLOYMENT=gpt-4.1
```

### 8 — Construir el app con GitHub Copilot

Abrir VS Code → Copilot Chat (`Ctrl+Alt+I`) → pegar el contenido completo de `prompts/copilot_prompt.md`.

Dejar que Copilot complete todos los pasos sin interrumpir.

### 9 — Deploy

```powershell
npx rayfin login
npx rayfin up
```

El proceso toma 2-4 minutos. Al finalizar aparece la URL pública del app en el workspace.

---

## Errores comunes

| Error | Causa | Solución |
|---|---|---|
| Vision API 401 | Credenciales en `.env.local` | Mover a `rayfin/.env` con prefijo `RAYFIN_PUBLIC_*` |
| GraphQL error en Historial | Sin valuaciones guardadas aún | Normal — guardar una valuación primero |
| App no aparece en workspace | Tenant setting deshabilitado | Admin Portal → Fabric Apps → Enable |
| Workspace no soporta Fabric Apps | Región incorrecta | Crear workspace en North Central US o West US |
| ReadKey error en CLI | Ejecutando desde cmd.exe | Usar PowerShell |
| `rayfin` not found | Sin npx | Siempre usar `npx rayfin up` |

---

## Lógica de precios — alineación Lakehouse ↔ App

```
precio_mercado         = base * factor_año * factor_km * factor_condición
precio_compra_sugerido = precio_mercado * 0.82

factor_año = 1.0 - (2024 - año) * 0.07
factor_km  = 1.0 - (km / 200,000) * 0.25

factor_condición:
  Excelente   → 0.90
  Muy Bueno   → 0.78
  Bueno       → 0.65
  Regular     → 0.50
  Deteriorado → 0.32
```

| Marca | Modelo | Base RD$ |
|---|---|---|
| Nissan | Sentra, Versa, X-Trail, Frontier, Kicks | 850,000 |
| Nissan | Qashqai | 950,000 |
| Nissan | Pathfinder | 1,800,000 |
| Chevrolet | Tracker, Cruze, Equinox, Trax, Onix | 950,000 |
| Chevrolet | Silverado | 2,500,000 |
| Suzuki | Todos | 650,000 |
| Infiniti | Todos | 1,800,000 |
| Cadillac | Todos | 3,500,000 |
| Yamaha | Todos | 280,000 |

---

## Flujo del demo (30 min)

1. Workspace Fabric → señalar Lakehouse, App, SQL Database
2. **Nissan Versa** → valuación normal, precio en RD$, historial
3. **Nissan Qashqai** → daño por incendio, alerta de discrepancia ← momento WOW
4. **Fabric Data Agent** → 3 preguntas con gráficos por Code Interpreter

---

*Microsoft Solution Engineering — SMEC Region*
*Stack: Microsoft Fabric · Azure OpenAI GPT-4.1 Vision · Rayfin CLI · React*
