# Branly's Gambit

Petit jeu en style Pokémon où les enseignants de l’IUT de Lannion s’affrontent, chacun représentant une des 6 compétences du BUT Informatique. L’idée est d’avoir des repères visuels pour découvrir l’IUT plutôt que de longues descriptions.

## Jouer rapidement
1. Installe Python 3 et les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
2. Lance le jeu :
   ```bash
   python main.py
   ```
3. Pour générer un exécutable :
   * Windows : `build_exe.bat`
   * Linux : `./build_exe.sh`

## À savoir
- Tour par tour, menu de sélection des attaques, buffs/statuts.
- Assets, configs et données sont chargés depuis `assets/`, `configs/`, `data/`.
- Aucun son activé par défaut (remplace-les si besoin).
