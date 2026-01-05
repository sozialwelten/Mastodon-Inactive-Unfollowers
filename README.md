# Mastodon-Inactive-Unfollowers

Findet Accounts, denen du folgst, die dir aber nicht zurückfolgen und seit mindestens 3 Jahren (oder einem anderen konfigurierbaren Zeitraum) inaktiv sind.

## Features

- 🔍 Analysiert deine Following/Follower-Liste
- 👻 Findet inaktive Accounts, die dir nicht folgen
- 📊 Zeigt detaillierte Statistiken
- 💾 Exportiert Ergebnisse als CSV
- 🗑️ Optional: Automatisches Entfolgen (mit Bestätigung)

## Installation

```bash
pip install requests
```

## Access Token erstellen

1. Gehe zu: `https://DEINE-INSTANZ/settings/applications`
2. Erstelle neue Anwendung
3. Benötigte Scopes:
   - `read:accounts`
   - `read:follows`
   - `write:follows` (nur für `--unfollow`)
4. Kopiere den Access Token

## Verwendung

```bash
# Grundlegend (Standard: 36 Monate Inaktivität)
python inactive_unfollowers.py -i mastodon.social -t YOUR_TOKEN

# Andere Zeiträume (z.B. 2 Jahre = 24 Monate)
python inactive_unfollowers.py -i mastodon.social -t YOUR_TOKEN --inactive-months 24

# Als CSV exportieren
python inactive_unfollowers.py -i mastodon.social -t YOUR_TOKEN --export inactive.csv

# Mit automatischem Unfollow (fragt vorher nach Bestätigung)
python inactive_unfollowers.py -i mastodon.social -t YOUR_TOKEN --unfollow
```

## Optionen

```
required arguments:
  -i, --instance        Deine Mastodon-Instanz (z.B. mastodon.social)
  -t, --token          Dein Access Token

optional arguments:
  -h, --help           Hilfe anzeigen
  --inactive-months    Inaktivitätszeitraum in Monaten (Standard: 36)
  --export            Exportiere Ergebnisse als CSV
  --unfollow          Entfolge gefundenen Accounts (nach Bestätigung)
```

## Beispiel-Output

```
👻 Inaktive Accounts, die dir nicht zurückfolgen:

@alice@mastodon.social
├─ Name: Alice Developer
├─ Letzter Post: 2021-03-15 (vor 3 Jahre, 9 Monate)
├─ Folgt dir: ❌ Nein
└─ Profil: https://mastodon.social/@alice

📊 Zusammenfassung:
   Du folgst: 347 Accounts
   Folgen dir zurück: 289 (83.3%)
   Folgen dir nicht: 58 (16.7%)
   └─ davon inaktiv >36 Monate: 12 (3.5%)
```

## Lizenz

GPL-3.0

## Autor

Michael Karbacher