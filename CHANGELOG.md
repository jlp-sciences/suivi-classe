# Historique des versions

## 3.12 — 13 novembre 2026
- Note d'implication : retour à la règle « 2 RAS de suite = −0,5 » (plafond passivité 3). Nouveau : les RAS isolés (entre deux séances où l'élève s'est manifesté) sont comptés, malus de −0,5 tous les 4, non rattrapable par la participation. Chaque RAS ne compte que dans une règle.
- Réglages › Étiquettes : série de RAS, pénalité, nombre de RAS isolés par malus (0 = désactivé), malus, seuil de l'alerte « à regarder ».
- « Progrès / effort » reste à +0,25.

## 3.11 — 13 novembre 2026
- Note d'implication : chaque RAS coûte −0,33 (au lieu de « 2 RAS de suite = −0,5 ») ; la note monte si l'élève se manifeste à plus de 2 séances sur 5. Plafond passivité porté à 4. Alerte « à regarder » après 3 RAS de suite (réglable).
- « Progrès / effort » rapporte +0,25, comme Actif et Travail soigné.

## 3.10 — 10 novembre 2026
- Notes : import direct de l'export Excel « Les devoirs » d'École Directe (glisser le fichier ou le choisir), lu sur l'appareil. Classe reconnue d'après l'en-tête ; codes TP → TP, DL → Écrit · maison, autres → Écrit ; notes en bleu → non comptées ; évaluations encore vides ignorées ; lignes de synthèse ignorées.
- Aperçu : contrôle des moyennes calculées par rapport à celles d'École Directe, écarts signalés.
- Suivi : trier ou filtrer les élèves ne fait plus remonter la page.
- Sous-catégorie « Écrit · maison » (comptée dans l'écrit), ○ sur la courbe ; notes non comptées affichées en gris.

## 3.09 — 10 novembre 2026
- Notes : page « Notes » par classe (onglet Suivi), import depuis une capture d'École Directe lue par Claude (format [E1] … / NOM Prénom | note), aperçu de contrôle, réimport sans doublon, correction note par note.
- Fiche élève : carte Résultats (moyennes écrit, TP, générale, comparées à la classe), courbe d'évolution de la moyenne, liste des notes.
- Suivi : colonne Moy. (tendance sur 3 évaluations), pastille Moy. dans la grille, ligne de synthèse ; récapitulatif des appréciations avec les moyennes.
- Fiche élève : passer à l'élève précédent / suivant (flèches, glissement du doigt, clavier), dans l'ordre du tableau de bord.
- Moyenne en pastille pleine, implication en pastille en contour (tableau, grille, fiche).
- Délégués : D plein (délégué) et S en pointillés gris (suppléant) à la place des étoiles.
- Courbes d'implication et de moyenne : curseur à faire glisser, bulle de détail (séance : date, remarques, points, note ; évaluation : date, intitulé, type, note, coef, classe, moyenne après).

## 3.08 — 8 novembre 2026
- Note d'implication : « Actif » et « Travail soigné » valent + 0,25 par séance (travail attendu) ; Participe, Moteur, Bonne question, Aide, Progrès restent à + 0,5.

## 3.07 — 8 novembre 2026
- Fiche élève : tableau « Ce que vaut chaque remarque » (barème et valeurs dans la classe), aussi dans Réglages › Étiquettes.
- Chronologie par séance : remarques, points gagnés ou perdus, note après la séance, RAS automatiques, séances hors calcul (absence, évaluation), plafonds et rattrapages indiqués.

## 3.06 — 8 novembre 2026
- Note d'implication : série de 2 RAS = − 0,5 ; alerte « à regarder » une séance avant la deuxième pénalité.
- Tableau de bord du Suivi : colonne Implication (triable, tendance), colonnes Devoirs et Oublis, comptes en séances, ligne de synthèse (moyenne, élèves sous 10, à regarder) ; note en pastille dans la vue grille.

## 3.05 — 8 novembre 2026
- Nouvelle étiquette « Oubli de blouse ».
- Une étiquette ne compte qu'une fois par séance pour un élève (déjà notée : grisée dans le panneau).
- Réglages › Étiquettes : choisir les étiquettes affichées dans le bilan.
- Résumé et fiche : comptes en séances avec pourcentage des séances suivies ; « Peu observé » si moins de 30 % des séances ont une observation.
- Appréciations de bulletin : récapitulatif à copier pour Claude, import des réponses, relecture et copie vers École Directe ; appréciation visible dans la fiche.
- Note d'implication (modèle « capital ») : départ 15, + 0,5 par séance positive (bonus jusqu'à + 5), − 1 bavardage/dissipation/comportement, − 0,5 passif, − 1 devoir non fait, − 0,5 oubli/retard, − 0,5 par série de 2 RAS ; plafonds nets par famille (souples au-delà) ; valeurs adaptées au rythme de la classe (30 séances = référence) ; plancher 3 ; arrondi au demi-point ; note proposée + note retenue ; courbe d'évolution ; barème réglable (Réglages › Étiquettes).
- RAS automatique : séance terminée dont le bilan a été commencé = RAS pour les présents sans remarque.
- Alerte « à regarder » une séance avant la deuxième pénalité de RAS (3 RAS de suite).
- Séances d'évaluation : bilan considéré comme fait, non comptées pour la participation ni les RAS.

## 3.04 — 3 novembre 2026
- Résumé automatique de l'élève (fiche et Suivi) : points forts / à améliorer, devoirs, matériel, retards, absences, tendance sur 3 semaines.
- Notes de suivi dans la fiche élève (conseil de classe, rencontre parents, autre), synchronisées.
- Saisie des notes du conseil élève par élève (depuis le créneau du conseil ou l'onglet Suivi).

## 3.03 — 27 octobre 2026
- Tests intégrés : Réglages › Sauvegarde › « Vérifier l'application » (60 vérifications sur des élèves fictifs).
- Tests de non-régression en ligne de commande (`tests/run_all.py`).

## 3.02 — 27 octobre 2026
- Conseil de classe : créneau hachuré, bordure en pointillés, étiquette « Conseil de classe ».
- Heure de vie de classe : case dans l'éditeur de créneau ; ni chapitre, ni devoirs, ni cahier de textes ; appel, bilan et commentaire de préparation.
- Progression : les lignes « Vérifié » ne sont plus affichées (seul « À vérifier » reste).

## 3.01 — 26 octobre 2026
- Les mises à jour automatiques (synchronisation, horloge) attendent la fin du défilement et gardent la position.

## 3.0 — 22 octobre 2026
- Onglet Contenu en une seule vue (bandeau précédente / séance / suivante, contenu en grand, « À voir en début d'heure »).
- Bouton « Recopier pour le G2 » : devoirs liés entre groupes, une seule ligne à la vérification.
- Progression : la position ne remonte plus en haut toute seule.

## 2.15 — 13 octobre 2026
- Deuxième répartition Ga / Gb ; devoirs vérifiés élève par élève à leur prochaine séance.

## Versions antérieures
2.12 à 2.14 : vue semaine (pastilles, ÉVAL / NOTÉ), salles PC1 à PC6, placement aléatoire (îlots choisis, « Ensemble », « À séparer »), délégués, Suivi en grille, absences (fantôme), conseils de classe.
