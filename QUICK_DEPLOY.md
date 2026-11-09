# QUICK_DEPLOY — mise en production de Loova

Loova tourne chez **o2switch**, en app Python cPanel (« Setup Python App »,
servie par Passenger).

- Code de l'app : `~/loova_app` (clone git du dépôt GitHub public)
- Virtualenv : `~/virtualenv/loova_app/3.12`
- Dossier du domaine `~/loova.studionobleval.xyz` : **ce n'est pas le code**,
  pas de `git` ici
- Logs Passenger : `~/logs/`
- Secrets de prod : `~/loova_app/.env` (ne jamais les taper en `export` dans le
  terminal, ils finissent dans `~/.bash_history`)

## 1. Depuis le poste de dev

```bash
git push origin main
```

## 2. Sur le serveur (cPanel → Avancé → Terminal)

```bash
source ~/virtualenv/loova_app/3.12/bin/activate && cd ~/loova_app
git status                 # doit être propre, sur main
git pull origin main
```

Seulement si le pull les touche :

```bash
pip install -r requirements.txt   # si requirements.txt a changé
flask db upgrade                  # si migrations/ a changé
```

Si `flask db upgrade` plante sur une erreur de threads OpenBLAS :
`export OPENBLAS_NUM_THREADS=1` puis relancer.

## 3. Redémarrer l'app

```bash
touch tmp/restart.txt
```

Passenger relance l'app au chargement de page suivant. Équivalent : bouton
**Restart** dans « Setup Python App ».

## 4. Vérifier

Charger une page de https://loova.studionobleval.xyz/ puis tester la
fonctionnalité déployée. En cas d'erreur 500 : consulter `~/logs/`.
