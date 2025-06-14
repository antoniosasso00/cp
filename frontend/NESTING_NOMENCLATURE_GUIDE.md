# Guida alla Nomenclatura Nesting CarbonPilot

## 🔧 **Chiarimenti Tecnici Fondamentali**

### **"L" = Linee Vuoto (NON Livelli)**

I badge **"12L", "16L", "8L"** nella tabella autoclavi si riferiscono al **numero di linee vuoto** disponibili, **NON ai livelli di nesting**.

#### ✅ **Significato Corretto:**
- **12L** = 12 linee vuoto disponibili
- **16L** = 16 linee vuoto disponibili  
- **8L** = 8 linee vuoto disponibili

#### ❌ **Interpretazione Errata:**
- ~~12L = 12 livelli di nesting~~
- ~~16L = 16 livelli di nesting~~

---

## 📋 **Distinzioni Tecniche Chiare**

### **1. Linee Vuoto (`num_linee_vuoto`)**
- **Definizione**: Numero di connessioni/linee di aspirazione vuoto disponibili nell'autoclave
- **Caratteristica**: Fisica dell'autoclave (non modificabile)
- **Scopo**: Collegamento degli stampi al sistema di vuoto
- **Esempio**: PANINI ha 16 linee, ISMAR ha 12 linee, MAROSO ha 8 linee
- **Display**: Badge "16 Linee", "12 Linee", "8 Linee"

### **2. Livelli di Nesting 2L (sempre 2)**
- **Livello 0**: Piano base dell'autoclave
- **Livello 1**: Cavalletti di supporto (altezza standard 100mm)
- **Caratteristica**: Sempre 2 livelli nel sistema nesting 2L
- **Scopo**: Ottimizzazione spazio verticale autoclave
- **Display**: Badge "2 Livelli" quando supportato

### **3. Numero Cavalletti (`max_cavalletti`)**
- **Definizione**: Numero massimo di cavalletti fisici supportati dall'autoclave
- **Variabile**: Da 0 (solo piano base) a 6+ (autoclavi grandi)
- **Scopo**: Supporto fisico per il livello 1
- **Esempio**: PANINI supporta 6 cavalletti, ISMAR 4 cavalletti, MAROSO 0 cavalletti
- **Display**: Badge "6 Cavalletti", "4 Cavalletti", "Piano Base"

---

## 🎯 **Implementazione UI Corretta**

### **Badge nella Tabella Autoclavi:**

```typescript
{/* ✅ CORRETTO: Linee Vuoto */}
<Badge variant="outline" className="text-xs">
  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
  {autoclave.num_linee_vuoto} Linee
</Badge>

{/* ✅ CORRETTO: Sistema 2L */}
<Badge variant="outline" className="text-xs bg-green-50">
  <Check className="w-3 h-3" />
  2 Livelli
</Badge>

{/* ✅ CORRETTO: Cavalletti */}
<Badge variant="outline" className="text-xs">
  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
  {autoclave.max_cavalletti} Cavalletti
</Badge>
```

### **❌ Badge Precedenti Confusi:**
```typescript
// ❌ CONFUSO: Poteva essere interpretato come "livelli"
<Badge>{autoclave.num_linee_vuoto}L</Badge>
```

---

## 🏭 **Configurazioni Autoclavi CarbonPilot**

### **AEROSPACE_PANINI_XL (ASP_001)**
- **Linee Vuoto**: 16 linee (collegamento stampi)
- **Sistema 2L**: ✅ Supportato (2 livelli sempre)
- **Cavalletti**: 6 cavalletti max (100mm altezza)
- **Caratteristiche**: Autoclave grande, massima flessibilità

### **AEROSPACE_ISMAR_L (ASI_002)**
- **Linee Vuoto**: 12 linee (collegamento stampi)
- **Sistema 2L**: ✅ Supportato (2 livelli sempre)
- **Cavalletti**: 4 cavalletti max (100mm altezza)
- **Caratteristiche**: Autoclave media, bilanciamento capacità/spazio

### **AEROSPACE_MAROSO_M (ASM_003)**
- **Linee Vuoto**: 8 linee (collegamento stampi)
- **Sistema 2L**: ❌ Non supportato (solo piano base)
- **Cavalletti**: 0 cavalletti (solo livello 0)
- **Caratteristiche**: Autoclave compatta, solo piano base

---

## 📊 **Schema Visuale**

```
AUTOCLAVI DISPONIBILI:
├── PANINI_XL   ● 16 Linee  ● 2 Livelli  ● 6 Cavalletti
├── ISMAR_L     ● 12 Linee  ● 2 Livelli  ● 4 Cavalletti  
└── MAROSO_M    ● 8 Linee   ● 1 Livello  ● 0 Cavalletti

LIVELLI NESTING 2L (quando supportato):
├── Livello 1: Cavalletti (100mm altezza)
└── Livello 0: Piano base autoclave

LINEE VUOTO:
├── Connessioni fisiche nell'autoclave
├── Per collegamento stampi al sistema vuoto
└── Numero fisso per ogni autoclave
```

---

## 🛠️ **Prossimi Passi per Chiarezza UI**

1. **✅ Completato**: Separato chiaramente linee vuoto, livelli e cavalletti nei badge
2. **✅ Completato**: Aggiunto tooltip esplicativi per ogni badge
3. **✅ Completato**: Sezione informativa per spiegare il sistema 2L
4. **🔄 In Progresso**: Documentazione completa per operatori
5. **📋 Pianificato**: Training materiale per distinguere le caratteristiche tecniche

---

**Nota Importante**: La confusione "L = Livelli" vs "L = Linee" è stata completamente risolta con questa implementazione UI migliorata. Ora ogni concetto tecnico ha una rappresentazione visiva distinta e chiara. 