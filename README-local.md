# Lokales Docker Setup für DictBench

## Quick Start

Das Projekt kann einfach mit Docker lokal gestartet werden:

```bash
# Docker Compose verwenden (empfohlen)
docker-compose -f docker-compose.local.yml up --build

# Oder manuell mit Docker
docker build -f Dockerfile.local -t dictbench:local .
docker run -p 8000:8000 dictbench:local
```

## Zugriff

- **Web-Anwendung**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin (falls Superuser erstellt)

## Features des lokalen Setups

- ✅ Django Development Server
- ✅ SQLite Datenbank (integriert)
- ✅ Alle Python Dependencies installiert
- ✅ Migrationen automatisch ausgeführt
- ✅ Hot-Reload für Entwicklung (bei Volume-Mount)
- ✅ Health Check integriert

## Bekannte Probleme

- **Warning**: URL namespace 'properties' ist nicht eindeutig - das ist nur eine Warnung
- **Static Files**: collectstatic wird übersprungen wegen WhiteNoise-Konflikten

## Troubleshooting

### Container stoppt sofort
```bash
# Logs anschauen
docker-compose -f docker-compose.local.yml logs

# Container interaktiv starten
docker run -it dictbench:local bash
```

### Port bereits belegt
```bash
# Anderen Port verwenden
docker run -p 8080:8000 dictbench:local
```

### Container neu bauen
```bash
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up --build
```

## Entwicklung

Für Entwicklung mit Live-Reload:

```bash
# Mit Volume-Mount für lokale Dateien
docker-compose -f docker-compose.local.yml up
```

Die `docker-compose.local.yml` mountet das lokale `propbench` Verzeichnis in den Container, so dass Änderungen sofort sichtbar sind.

## Nächste Schritte

1. Superuser erstellen: `docker exec -it dictbench-web-1 python manage.py createsuperuser`
2. Test-Daten laden (falls vorhanden)
3. API-Endpoints testen

## Status

✅ **Server läuft erfolgreich auf Port 8000**
✅ **Docker Image gebaut und getestet**
✅ **Docker Compose Setup funktioniert**