# Suivi de classe

Application web (un seul fichier `index.html`) pour suivre ses classes sur tablette et téléphone :
emploi du temps, contenu des séances, devoirs, bilans des élèves, plans de classe, progression.
Aucune donnée d'élève n'est stockée ici : elles restent sur l'appareil (et dans OneDrive si la synchronisation est activée).

## Fichiers
- `index.html` : toute l'application (code, styles, tests intégrés).
- `sw.js` : fonctionnement hors ligne. **Changer le numéro `CACHE` à chaque version** pour que les appareils se mettent à jour.
- `manifest.webmanifest`, icônes, `pdf.min.js`, `pdf.worker.min.js` : installation et lecture du trombinoscope PDF.
- `tests/run_all.py` : tests de non-régression.
- `CHANGELOG.md` : historique des versions.

## Tests
Dans l'application : Réglages › Sauvegarde › « Vérifier l'application » (élèves fictifs, vos données ne sont pas touchées).

En ligne de commande (avant chaque livraison) :
```
pip install playwright && playwright install chromium
python3 tests/run_all.py
```

## Branches
- `dev` : travail en cours, tests.
- `main` : version en ligne (GitHub Pages). On n'y met une version qu'après validation.
