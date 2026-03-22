# Schéma SQLite - Bird Feeder DB

**Phase 3 - À compléter**

## Tables

### individuals
Table des ~50 individus uniques reconnus.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Identifiant unique |
| label | VARCHAR(50) | "Oiseau #412" |
| created_at | DATETIME | Date de première détection |
| last_seen | DATETIME | Dernière sighting |
| confidence_avg | FLOAT | Moyenne des confidences de détection |
| embedding_ref | BLOB | Embedding "référence" (MobileNetV2) |

**Index**: `CREATE INDEX idx_individuals_label ON individuals(label)`

---

### sightings
Historique de tous les sightings (détections).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Identifiant unique |
| individual_id | INTEGER FOREIGN KEY | Référence à `individuals.id` |
| timestamp | DATETIME | Moment du sighting |
| confidence | FLOAT | Confiance détection (0.0-1.0) |
| image_path | VARCHAR(255) | Chemin image brute |
| embedding | BLOB | Vecteur MobileNetV2 (1280 floats) |
| embedding_distance | FLOAT | Distance cosinus au match |
| temp | FLOAT | Température (NULL Phase 1) |
| humidity | FLOAT | Humidité (NULL Phase 1) |
| light | FLOAT | Luminosité (NULL Phase 1) |

**Index**: 
- `CREATE INDEX idx_sightings_individual ON sightings(individual_id)`
- `CREATE INDEX idx_sightings_timestamp ON sightings(timestamp DESC)`

---

### embeddings (optionnel, pour cache)
Cache des embeddings pour matching rapide (optionnel).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | |
| individual_id | INTEGER FOREIGN KEY | Référence individu |
| embedding | BLOB | Vecteur MobileNetV2 |
| created_at | DATETIME | Date extraction |
| photo_hash | VARCHAR(32) | MD5 image source |

---

## SQL Exemples

### Créer tables (Phase 3)
```sql
CREATE TABLE individuals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label VARCHAR(50) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME,
    confidence_avg FLOAT DEFAULT 0.0,
    embedding_ref BLOB
);

CREATE TABLE sightings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    individual_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence FLOAT NOT NULL,
    image_path VARCHAR(255),
    embedding BLOB,
    embedding_distance FLOAT,
    temp FLOAT,
    humidity FLOAT,
    light FLOAT,
    FOREIGN KEY (individual_id) REFERENCES individuals(id) ON DELETE CASCADE
);

CREATE INDEX idx_sightings_individual ON sightings(individual_id);
CREATE INDEX idx_sightings_timestamp ON sightings(timestamp DESC);
```

### Ajouter un oiseau
```sql
INSERT INTO individuals (label, last_seen, confidence_avg, embedding_ref)
VALUES ('Oiseau #412', CURRENT_TIMESTAMP, 0.94, embedding_blob);
```

### Ajouter un sighting
```sql
INSERT INTO sightings (individual_id, confidence, image_path, embedding, embedding_distance)
VALUES (1, 0.95, 'data/captures/20260322_143015.jpg', embedding_blob, 0.12);
```

### Requête: Oiseaux vus aujourd'hui
```sql
SELECT i.id, i.label, COUNT(*) as count_today
FROM individuals i
JOIN sightings s ON i.id = s.individual_id
WHERE DATE(s.timestamp) = DATE('now')
GROUP BY i.id
ORDER BY count_today DESC;
```

### Requête: Top 5 oiseaux ce mois
```sql
SELECT i.id, i.label, COUNT(*) as count_month
FROM individuals i
JOIN sightings s ON i.id = s.individual_id
WHERE strftime('%Y-%m', s.timestamp) = strftime('%Y-%m', 'now')
GROUP BY i.id
ORDER BY count_month DESC
LIMIT 5;
```

---

**Status**: Phase 3 WIP
