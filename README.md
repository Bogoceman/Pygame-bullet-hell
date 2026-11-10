# Crazy Safari

Un petit *bullet hell* façon Touhou, situé dans la savane. On pilote le camion
du chasseur, on esquive les projectiles des animaux.

## Lancer le jeu

```bash
pip install -r requirements.txt
python main.py
```

Le jeu a été testé avec Python 3.13/3.14 et pygame 2.6 / pygame-ce 2.5.

## Commandes

| Touche | Action |
| --- | --- |
| `ZQSD` / flèches | Déplacer le camion |
| `MAJ` | Mode focus (déplacement lent + hitbox visible) |
| `X` | Bombe (détruit les balles et blesse les ennemis) |
| `ÉCHAP` / `P` | Pause |
| `R` | Recommencer |
| `M` | Retour au menu (pause / fin de partie) |

Le tir est automatique : le chasseur alterne ses deux images de tir, et la
boucle du fusil (`fusil_rafale_rapide_loop.wav`) est calée sur le même rythme
(10 coups par seconde). Le son s'arrête en pause, dans le menu et en fin de
partie.

## Contenu

- Menu principal animé avec le bouton **JOUER** cliquable.
- Savane qui défile, HUD et cadres extraits de `assets/game/bg_and_HUD.mp4`
  (image fixe `assets/game/game_hud.png`).
- Vagues de hyènes avec tirs visés, puis un ou plusieurs boss enchaînés
  (tirs visés, anneaux et double spirale en phase 2 pour la reine hyène).
- Score, graze, vies, bombes, record sauvegardé dans `highscore.txt`.

## Ajouter un boss

Les boss sont des classes dans `bosses.py`. La classe `Boss` gère l'entrée,
les déplacements, les PV, le flash, le dessin et un tir visé simple ; il suffit
de créer une sous-classe puis de l'ajouter à `BOSS_CLASSES` dans l'ordre
d'apparition :

```python
class HyenaAlpha(Boss):
    name = "HYÈNE ALPHA"
    max_hp_value = 600
    score_value = 2500
    bar_color = (120, 220, 140)

    def attack(self, dt, player_pos, bullets):
        ...  # motifs de tir personnalisés


BOSS_CLASSES = [HyenaQueen, HyenaAlpha]
```

Le jeu enchaîne automatiquement les boss, affiche leur nom et leur barre de
vie, puis déclenche la victoire après le dernier.

## Structure

- `main.py` : point d'entrée.
- `game.py` : états du jeu (menu, jeu, pause, game over, victoire) et HUD.
- `entities.py` : joueur, projectiles, hyènes et particules.
- `bosses.py` : classe de base `Boss`, boss concrets et registre `BOSS_CLASSES`.
- `assets.py` : chargement et découpe des images.
- `constants.py` : réglages et constantes.
- `music.py` : musique du menu et boucle du fusil.
