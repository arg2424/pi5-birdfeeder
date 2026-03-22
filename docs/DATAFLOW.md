# Data Flow - Pi5 Bird Feeder

## Architecture Flux

```
[1. Camera]
    ↓ (18MP image)
[2. Detection] (YOLOv8-nano TFLite)
    ↓ (bounding boxes per bird)
[3. Crop & Extract]
    ↓ (individual bird images)
[4. Features] (MobileNetV2 embedding)
    ↓ (1280-dim vector per bird)
[5. Matching]
    ↓ (distance cosinus vs DB)
[6. Database] (SQLite)
    ↓ (store sighting + embedding)
[7. API] (Flask REST + WebSocket)
    ↓
[8. Dashboard] (Web UI real-time)
```

## Phase 1: Camera Capture

- Caméra Pi5 capture image (18MP)
- Image sauvegardée avec timestamp
- Path: `data/captures/YYYYMMDD_HHMMSS.jpg`
- Métadata: résolution, framerate

## Phase 2: Detection

- Load YOLOv8-nano TFLite modèle
- Inférence: ~500-1000ms
- Output: liste de (x, y, w, h, confidence) pour chaque oiseau
- Crop chaque oiseau individuellement

## Phase 3: Recognition

- Extract embedding via MobileNetV2 TFLite: ~300-800ms
- Vecteur 1280-dimensionnel par oiseau
- Comparer distance cosinus contre les ~50 individus déjà enregistrés: ~100-200ms
- Match: si distance < threshold → même oiseau
- Pas de match: créer nouvel individu (#51, #52...)

## Phase 4: Web API

- Store sighting dans DB
- REST API expose /api/birds, /api/sightings
- WebSocket pour événements temps-réel
- Dashboard HTML/JS affiche "Oiseau #412 vu 4x aujourd'hui"

## Phase 5: Autonomie

- Monitoring batterie (voltage ADC)
- Mode low-power si batterie faible
- Logs d'erreurs + alertes
- Optimisations: cache embeddings, compression images anciennes

## Latence Totale (1 capture → 1 sighting)

- Capture: 200-400ms
- Detection: 500-1000ms
- Feature extraction: 300-800ms
- Matching: 100-200ms
- **Total: ~1.2-2.4 secondes** ✅ (dans les 4-5 sec acceptables)
