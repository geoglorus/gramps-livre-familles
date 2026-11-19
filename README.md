# Livre des Familles (Plugin Gramps)

Extension de rapport textuel pour **Gramps** permettant de générer un répertoire familial structuré (« Livre des Familles ») avec fiches numérotées, renvois croisés, gestion des notes selon leur confidentialité, sélection modulaire des sections et index thématiques.

## Fonctionnalités

- **Mise en forme structurée** :
  - Numérotation des fiches avec mise en valeur des noms et renvois.
  - Présentation hiérarchisée des unions, conjoints, enfants (avec dates, lieux et mariages) et notes.
  - Titre personnalisable (« Livre des Familles » par défaut) et police *Liberation Serif* par défaut.
- **Options d'export** :
  - Titre et sous-titre personnalisables.
  - Gestion des notes : *Toutes les notes*, *Uniquement les notes non privées*, *Uniquement les notes privées* ou *Aucune note*.
  - Option d'inclusion de la légende des abréviations.
- **Sélection des sections à générer** :
  - Répertoire des familles
  - Index des patronymes
  - Index des prénoms
  - Index des localités
  - Index des professions et fonctions
  - Index des épouses
- **Formats de sortie** : compatible avec les formats de rapport textuel de Gramps (notamment **ODT**, **TXT**, **HTML**, **PDF**).

## Installation (Gramps 6.0)

1. Créez le dossier d'extension dans le répertoire utilisateur de Gramps (adaptez le chemin selon votre installation, par exemple en version Flatpak sous Linux) :

mkdir -p ~/.var/app/org.gramps_project.Gramps/data/gramps/gramps60/plugins/LivreFamilles

2. Copiez dans ce dossier les fichiers du plugin :
   - `livre_familles.py`
   - votre fichier d'enregistrement `.gpr.py`
3. Redémarrez **Gramps**.
4. Rendez-vous dans **Rapports → Rapports textuels → Livre des Familles**.

## Utilisation rapide

1. Sélectionnez **Livre des Familles** dans les rapports textuels.
2. Réglez le titre, le sous-titre et le mode d'inclusion des notes.
3. Cochez ou décochez les sections et index souhaités.
4. Choisissez le format de sortie (ex. `.odt` ou `.txt`) et lancez la génération. Une fenêtre de confirmation s'affiche en fin de traitement.

## Pistes d'amélioration

- Activation complète du sélecteur de filtres de personnes dans l'interface d'export.

## Auteur et crédits

- **Auteur** : Pierre Laminette (`geoglorus`) — 2026
- **Licence** : GNU GPL v3 ou ultérieure (voir le fichier `LICENSE`)
- **Assistance IA** : Code généré, corrigé et adapté avec l'assistance de **Gemini**.
