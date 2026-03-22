# API REST - Flask Endpoints

**Phase 4 - À compléter**

## GET /api/birds
Liste tous les oiseaux avec stats.

### Response (Phase 4)
```json
[
  {
    "id": 1,
    "label": "Oiseau #412",
    "count_today": 4,
    "count_month": 28,
    "last_seen": "2026-03-22T14:30:15Z",
    "confidence": 0.95,
    "thumbnail": "/data/birds/412/latest.jpg"
  },
  {
    "id": 2,
    "label": "Oiseau #413",
    "count_today": 2,
    "count_month": 15,
    "last_seen": "2026-03-22T13:45:20Z",
    "confidence": 0.92,
    "thumbnail": "/data/birds/413/latest.jpg"
  }
]
```

---

## GET /api/bird/<id>
Détail d'un oiseau + historique sightings.

### Response (Phase 4)
```json
{
  "id": 412,
  "label": "Oiseau #412",
  "count_today": 4,
  "count_month": 28,
  "count_total": 87,
  "first_seen": "2026-03-01T09:15:00Z",
  "last_seen": "2026-03-22T14:30:15Z",
  "avg_confidence": 0.94,
  "sightings": [
    {
      "timestamp": "2026-03-22T14:30:15Z",
      "confidence": 0.95,
      "image": "/data/captures/20260322_143015.jpg"
    }
  ]
}
```

---

## GET /api/sightings?limit=100&order=desc
Derniers sightings (temps-réel).

### Response (Phase 4)
```json
[
  {
    "id": 12543,
    "individual_id": 412,
    "label": "Oiseau #412",
    "timestamp": "2026-03-22T14:30:15Z",
    "confidence": 0.95,
    "image": "/data/captures/20260322_143015.jpg"
  }
]
```

---

## WebSocket /ws
Flux temps-réel de nouveaux sightings.

### Message (Phase 4)
```json
{
  "type": "new_sighting",
  "individual_id": 412,
  "label": "Oiseau #412",
  "timestamp": "2026-03-22T14:30:15Z",
  "confidence": 0.95,
  "image": "/data/captures/20260322_143015.jpg"
}
```

---

## Status Codes

- `200 OK` - Requête réussie
- `404 Not Found` - Oiseau/ressource non trouvé
- `500 Internal Server Error` - Erreur serveur

---

**Status**: Phase 4 WIP
