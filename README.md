# Pi5 Bird Feeder - Individual Recognition System

Système autonomous de surveillance du mangeoir à oiseaux avec reconnaissance individuelle des mésanges par IA légère et dashboard web temps-réel.

**Objectif**: Identifier les ~50 mésanges individuelles qui viennent au mangeoir, suivre leur fréquentation (4x aujourd'hui, 28x ce mois), et exposer les données via un dashboard web avec courbes et métriques environnementales.

---

## 📊 État d'Avancement

### Phase 1: Setup & Capture ⏳ EN COURS
- [x] Repo + structure dossier
- [x] Configuration de base (config.py)
- [x] Dépendances (requirements.txt)
- [ ] Test caméra Pi5 (capture 1 image)
- [ ] Sauvegarde images timestampées
- [ ] Détection mouvement simple (frame-diff)

### Phase 2: Détection 🔍 À FAIRE
- [ ] Télécharger YOLOv8-nano TFLite
- [ ] Implémentation détection oiseaux
- [ ] Cropping oiseaux individuels
- [ ] Tests détection unittest

### Phase 3: Reconnaissance Individuelle 🧠 À FAIRE
- [ ] SQLite schema + tables
- [ ] Feature extraction (MobileNetV2)
- [ ] Matching par distance cosinus
- [ ] Enregistrement des individus (#1 → #50)
- [ ] Tests matching

### Phase 4: Web Dashboard 🌐 À FAIRE
- [ ] Flask API REST (/api/birds, /api/sightings)
- [ ] WebSocket temps-réel
- [ ] Dashboard HTML/CSS/JS
- [ ] Graphes (fréquentation, courbes)
- [ ] Tests intégration

### Phase 5: Autonomie & Production 🔋 À FAIRE
- [ ] Monitoring batterie (voltage)
- [ ] Mode low-power si batterie faible
- [ ] Logs + alertes (fichier log)
- [ ] Optimisations (cache embeddings, compression)
- [ ] Tests endurance (24h+)

---

## 🚀 Installation

### Prérequis
- **Raspberry Pi 5** avec Ubuntu
- **Caméra Pi Camera v3** (18MP)
- **VRAM**: min 2GB
- **SD Card**: min 16GB

### Setup

```bash
# Cloner repo
cd ~/Documents/py/iot/
git clone <url-repo> pi5-birdfeeder
cd pi5-birdfeeder

# Env Python (optionnel, recommandé)
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Copier .env
cp .env.example .env
# éditer .env si nécessaire (ports, résolutions, etc.)
```

---

## 🏃 Lancement

### Phase 1 (Setup)
```bash
python src/main.py
```

**Output attendu**:
```
2026-03-22 15:30:45,123 - __main__ - INFO - 🐦 Pi5 Bird Feeder - Starting...
2026-03-22 15:30:45,124 - __main__ - INFO - Phase 1: Setup & Camera Capture
✅ Config loaded successfully
⏳ Phase 1 implementation coming next...
```

### Phase 4 (Web)
```bash
python src/api.py
# Accder à http://localhost:5000/
```

---

## 🏗️ Architecture

```
pi5-birdfeeder/
├── src/
│   ├── __init__.py
│   ├── config.py              # Paramètres centralisés (à partir .env)
│   ├── main.py                # Entry point
│   ├── camera.py              # Capture caméra Pi5 (libcamera)
│   ├── detection.py           # YOLOv8-nano TFLite (Phase 2)
│   ├── features.py            # MobileNetV2 embedding (Phase 3)
│   ├── database.py            # SQLite CRUD (Phase 3)
│   ├── matching.py            # Distance cosinus matching (Phase 3)
│   ├── api.py                 # Flask REST + WebSocket (Phase 4)
│   └── logger.py              # Logging config
├── tests/
│   ├── __init__.py
│   ├── test_camera.py
│   ├── test_detection.py
│   ├── test_database.py
│   └── test_matching.py
├── web/
│   ├── index.html             # Dashboard UI
│   ├── style.css              # Styles
│   └── app.js                 # Logic frontend
├── models/                    # Modèles TFLite (à télécharger)
│   ├── yolov8n.tflite         # (Phase 2)
│   └── mobilenetv2.tflite     # (Phase 3)
├── data/
│   ├── birdfeeder.db          # DB SQLite (créée Phase 3)
│   └── captures/              # Images captures
├── docs/
│   ├── DATAFLOW.md            # Flux de données complet
│   ├── API.md                 # Endpoints REST (Phase 4)
│   └── DATABASE.md            # Schéma SQLite (Phase 3)
├── logs/
│   └── birdfeeder.log         # Log fichier
├── .gitignore
├── .env.example               # Variables d'environnement
├── config.py                  # Configuration (charge .env)
├── README.md                  # Cette file
└── requirements.txt           # Dépendances Python
```

---

## 📡 Flux de Données

Voir [docs/DATAFLOW.md](docs/DATAFLOW.md)

```
Camera (18MP) → Detection (YOLOv8) → Feature Extraction (MobileNetV2)
    ↓
Matching (distance cosinus) → SQLite → Flask API → WebSocket → Dashboard
```

**Latence totale**: ~1.2-2.4 sec (acceptable, bien dans les 4-5 sec)

---

## 🔌 Configuration

### `.env.example` → `.env`

```bash
cp .env.example .env
```

Édite `.env` si besoin:

```env
# Camera
CAMERA_RESOLUTION=4608x3456       # 18MP du Pi Camera v3
CAMERA_FRAMERATE=30

# Detection
YOLO_CONFIDENCE=0.5               # Confiance min détection
YOLO_IOU=0.45

# Recognition
EMBEDDING_THRESHOLD=0.7           # Threshold distance cosinus
MAX_INDIVIDUALS=50

# Database
DB_PATH=data/birdfeeder.db

# Flask
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
FLASK_DEBUG=False

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/birdfeeder.log
```

---

## 🧪 Tests

```bash
# Run all tests
pytest tests/

# Run spécific module
pytest tests/test_camera.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📚 Documentation Détaillée

- **[DATAFLOW.md](docs/DATAFLOW.md)** - Architecture flux de données
- **[API.md](docs/API.md)** - Endpoints REST + WebSocket
- **[DATABASE.md](docs/DATABASE.md)** - Schéma SQLite détaillé

---

## 🤝 Gestion de Projet

### Git Workflow
```
main (stable)
  ← develop (intégration)
    ← feature/camera-capture
    ← feature/detection
    ← feature/recognition
    ← feature/api
```

### Issues & Milestones
- 1 issue par étape/fonctionnalité
- Labels: `phase-1`, `phase-2`, ..., `bug`, `enhancement`
- Milestones: `Phase 1: Setup`, `Phase 2: Detection`, etc.

### Commits
```bash
git commit -m "feat: implement camera capture"
git commit -m "fix: config path issue"
git commit -m "docs: update README for Phase 2"
```

---

## 🚦 Roadmap

| Version | Phase | État | ETA |
|---------|-------|------|-----|
| **v0.1** | Phase 1 | ⏳ En cours | 1 semaine |
| **v0.2** | Phase 2 | À faire | 2 semaines |
| **v0.5** | Phase 3 | À faire | 2 semaines |
| **v1.0** | Phase 4 | À faire | 2 semaines |
| **v1.1** | Phase 5 | À faire | 1 semaine |

---

## 🐛 Troubleshooting

### Camera non détectée
```bash
libcamera-hello --list
v4l2-ctl --list-devices
```

### Import errors
```bash
pip install --upgrade -r requirements.txt
```

### DB lockée
```bash
rm data/birdfeeder.db
# Relancer (recréera la DB)
```

---

## 📝 License

MIT

---

**Dernière mise à jour**: 22 mars 2026 - Phase 1 ⏳
