# Pi5 Bird Feeder - Individual Recognition System

Système autonome de surveillance de mangeoire à oiseaux avec reconnaissance individuelle des mésanges par IA légère et dashboard web temps-réel.

**Objectif**: Identifier les ~50 mésanges individuelles qui viennent au mangeoir, suivre leur fréquentation, et exposer les données via un dashboard web avec galerie d'événements et métriques.

## Validation caméra

Capture réelle obtenue avec la caméra IMX219 branchée sur le port CSI0 du Raspberry Pi 5.

![Dernière capture caméra](docs/images/camera-latest.jpg)

---

## 📊 État d'Avancement

### Phase 1: Setup & Capture ✅ TERMINÉ
- [x] Repo + structure dossier
- [x] Configuration de base (config.py)
- [x] Dépendances (requirements.txt)
- [x] Détection caméra Pi5 (IMX219 / CSI0)
- [x] Capture 1 image réelle (1920×1080, 344KB)
- [x] Sauvegarde images timestampées (microseconde pour éviter collisions à 0.5s)
- [x] Boucle de capture dans `src/main.py` (interval float configurable, ex: 0.5s)
- [x] Détection mouvement PIL frame-diff (scores réels: 0.001–0.18)
- [x] Pipeline staging → captures (motion-gated)
- [x] SQLite `motion_events` + enregistrement automatique
- [x] Nettoyage staging au démarrage

### Phase 2: Détection ✅ TERMINÉ
- [x] Modèle YOLO11n ONNX (10MB, CPU, ~185ms/inférence sur Pi5)
- [x] `onnxruntime` installé sur Pi5
- [x] `BirdDetector.detect()` avec preprocessing letterbox + NMS
- [x] Validé sur mésange réelle : **conf=0.862**
- [x] Détection intégrée dans la boucle principale (après motion)
- [x] Colonne `bird_detections` enregistrée dans `motion_events`

### Phase 3: Reconnaissance Individuelle 🧠 EN COURS
- [x] SQLite schema + tables (`individuals`, `sightings`)
- [x] Feature extraction baseline (histogrammes couleur + luminance)
- [x] Matching par distance cosinus
- [x] Enregistrement des individus (#1 → #50, `sightings_count`)
- [ ] Remplacer l'extracteur baseline par MobileNetV2 embeddings
- [ ] Calibrer le seuil de matching sur séries réelles de mésanges

### Phase 4: Web Dashboard 🌐 EN COURS
- [x] Serveur Flask (`src/api.py`) avec services systemd
- [x] Dashboard HTML/CSS/JS (`web/`)
- [x] API REST complète (voir section Endpoints)
- [x] Galerie événements motion avec pagination (`web/events.html`)
- [x] GIF clips auto-générés par événement (PIL, post-frames configurables)
- [x] Plein écran sur photos et clips GIF (double-clic ou bouton)
- [x] Mode cadrage / pause détection depuis l'interface (`web/live.html`)
- [x] Stats dashboard : events, individuals, sightings, solos, identifiés, faux positifs
- [ ] Graphes fréquentation par heure
- [ ] Filtre "sauvegarder uniquement les events oiseaux"

### Phase 5: Autonomie & Production 🔋 À FAIRE
- [ ] Nettoyage automatique des captures anciennes (logrotate-style)
- [ ] Filtre anti-vent / cooldown post-event
- [ ] Mode strict : `SAVE_BIRD_EVENTS_ONLY=true`
- [ ] Tests endurance (24h+)

---

## 🚀 Installation

### Prérequis
- **Raspberry Pi 5** avec Raspberry Pi OS Bookworm
- **Caméra IMX219** compatible Raspberry Pi (testée Arducam IMX219)
- **Connexion CSI0**
- **RAM**: 2 GB minimum (4 GB recommandé)
- **SD Card**: min 16 GB

### Setup

```bash
git clone <url-repo> pi5-birdfeeder
cd pi5-birdfeeder

cp .env.example .env
# éditer .env si nécessaire

sudo apt install -y python3-picamera2 python3-libcamera python3-dotenv
pip install -r requirements.txt
```

### Services systemd

Deux services gèrent le fonctionnement en production :

```bash
# Boucle principale : capture → motion → YOLO → reconnaissance → DB
sudo systemctl enable --now pi5-birdfeeder-main.service

# API Flask (port 5000)
sudo systemctl enable --now pi5-birdfeeder-api.service
```

> ⚠️ La caméra est exclusive : `main.service` et le live stream ne peuvent pas tourner simultanément. Utiliser le **mode cadrage** dans l'interface web pour basculer entre les deux.

---

## 🏃 Lancement manuel

```bash
# Boucle principale
python3 src/main.py

# Serveur web
python3 src/api.py
# Accéder à http://<IP_DU_PI>:5000/
```

---

## 📡 Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/health` | Santé du service |
| GET | `/api/stats` | Compteurs globaux (events, individuals, sightings, solos, identifiés, autres) |
| GET | `/api/latest` | Dernière capture |
| GET | `/api/sightings` | Liste des passages |
| GET | `/api/events` | Galerie événements motion (paginée) |
| DELETE | `/api/events/<id>` | Supprimer un événement |
| GET | `/api/camera/status` | État de la caméra / du service main |
| GET | `/api/camera/stream` | Flux MJPEG live |
| GET | `/api/mode` | Mode actuel (detection / cadrage) |
| POST | `/api/mode` | Basculer detection ↔ cadrage |
| POST | `/api/admin/reset` | Réinitialiser la DB |

---

## 🏗️ Architecture

```
pi5-birdfeeder/
├── src/
│   ├── config.py              # Paramètres centralisés (.env)
│   ├── main.py                # Boucle capture → motion → YOLO → ID → DB → GIF
│   ├── camera.py              # Wrapper picamera2 (timestamps microseconde)
│   ├── detection.py           # YOLO11n ONNX — bird detection
│   ├── motion.py              # PIL frame-diff motion detection
│   ├── database.py            # SQLite (motion_events + clip_path, individuals, sightings)
│   ├── features.py            # Feature extraction (histogrammes)
│   ├── matching.py            # Distance cosinus matching
│   └── api.py                 # Flask API + pages web
├── web/
│   ├── index.html             # Dashboard stats
│   ├── events.html            # Galerie événements + GIF clips
│   ├── live.html              # Flux live + mode cadrage
│   ├── style.css              # Styles globaux
│   └── app.js                 # Logique JS dashboard
├── models/
│   └── yolo11n.onnx           # YOLO11n ONNX (non versionné, ~10MB)
├── data/
│   ├── birdfeeder.db          # DB SQLite
│   ├── staging/               # Frames temporaires (nettoyées au démarrage)
│   ├── captures/              # Images avec mouvement détecté
│   └── events_video/          # GIF clips par événement
├── .env.example
├── requirements.txt
└── README.md
```

---

## 📡 Flux de Données

```
Camera IMX219 → Staging (frame N)
  ↓
Motion Detection (PIL diff, score) → si détecté → Persist (captures/)
  ↓                                               ↓
YOLO11n ONNX → bird_detections               SQLite (motion_events)
  ↓                                               ↓
Feature extraction → Matching cosinus       GIF clip (data/events_video/)
  ↓
Individu #N → SQLite (individuals, sightings)
  ↓
Flask API → Dashboard / Galerie events
```

**Latence (Pi5)** : capture ~80ms + inférence YOLO ~185ms = ~265ms/cycle

---

## 🔌 Configuration `.env`

```env
# Camera
CAPTURE_INTERVAL_SECONDS=0.5      # float, 2 captures/sec
CAMERA_RESOLUTION=1920x1080

# Motion detection
MOTION_SCORE_THRESHOLD=0.02
MOTION_RESIZE_WIDTH=320
MOTION_RESIZE_HEIGHT=180

# Detection
YOLO_CONFIDENCE=0.5
YOLO_IOU=0.45

# Recognition
EMBEDDING_THRESHOLD=0.7
MAX_INDIVIDUALS=50

# GIF clips
EVENT_CLIP_ENABLED=true
EVENT_CLIP_POST_FRAMES=6
EVENT_CLIP_FRAME_INTERVAL_SECONDS=0.2
EVENT_CLIP_MAX_WIDTH=960

# Database
DB_PATH=data/birdfeeder.db

# Flask
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
LOG_LEVEL=INFO
```

---

## 🚦 Roadmap

| Version | Phase | État |
|---------|-------|------|
| **v0.1** | Phase 1: Setup & Capture | ✅ Terminé |
| **v0.2** | Phase 2: Détection YOLO | ✅ Terminé |
| **v0.5** | Phase 3: Reconnaissance individuelle | ⏳ En cours |
| **v1.0** | Phase 4: Web Dashboard complet | ⏳ En cours |
| **v1.1** | Phase 5: Autonomie & Production | 🔜 À faire |

---

## 🐛 Troubleshooting

### Camera non détectée
```bash
rpicam-still --list-cameras
```

Pour une IMX219 branchée sur CSI0 :
```
camera_auto_detect=0
dtoverlay=imx219,cam0
```
Puis redémarrage du Pi.

### Caméra occupée (busy)
Si `main.service` et le live stream tournent en même temps, la caméra est exclusive.
Utiliser le bouton **"Activer mode cadrage"** dans `web/live.html` pour stopper la détection avant d'ouvrir le flux live.

### Service qui ne démarre pas
```bash
sudo systemctl status pi5-birdfeeder-main.service
journalctl -u pi5-birdfeeder-main.service -n 50
```

### DB lockée
```bash
sudo systemctl stop pi5-birdfeeder-main.service pi5-birdfeeder-api.service
rm data/birdfeeder.db
sudo systemctl start pi5-birdfeeder-main.service pi5-birdfeeder-api.service
```

---

## 📝 License

MIT
