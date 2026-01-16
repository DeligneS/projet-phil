# Évaluation des travaux étudiants

Application Streamlit permettant d'évaluer automatiquement les travaux d'étudiants via un LLM OpenAI.

## Fonctionnalités

- Upload de grilles d'évaluation (PDF, Word, Excel, TXT, HTML)
- Upload des travaux étudiants via fichier ZIP (compatible Moodle)
- Base de connaissances (fichiers, URLs, texte)
- Évaluation parallèle pour un traitement rapide
- Export en Excel ou Word avec fichiers Markdown

---

## Installation sur Windows (VS Code)

### 1. Prérequis

- **Python 3.12+** installé ([télécharger ici](https://www.python.org/downloads/))
- **VS Code** installé ([télécharger ici](https://code.visualstudio.com/))

> Lors de l'installation de Python, cochez **"Add Python to PATH"**.

### 2. Installer uv (gestionnaire de packages Python)

Ouvrez le terminal VS Code (`Ctrl + ù` ou `Terminal > New Terminal`) et exécutez :

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Fermez et rouvrez le terminal VS Code pour que `uv` soit reconnu.

Vérifiez l'installation :

```powershell
uv --version
```

### 3. Télécharger le projet

**Option A : Avec Git**

```powershell
git clone https://github.com/votre-repo/projet-phil.git
cd projet-phil
```

**Option B : Sans Git**

1. Téléchargez le projet en ZIP depuis GitHub
2. Extrayez le dossier
3. Ouvrez le dossier dans VS Code (`File > Open Folder`)

### 4. Configurer la clé API OpenAI

Créez un fichier `.env` à la racine du projet :

```powershell
New-Item -Path ".env" -ItemType File
```

Ouvrez le fichier `.env` et ajoutez votre clé API :

```
OPENAI_API_KEY=sk-votre-cle-api-openai
```

> Obtenez votre clé API sur [platform.openai.com](https://platform.openai.com/api-keys)

### 5. Lancer l'application

Dans le terminal VS Code, exécutez :

```powershell
uv sync
uv run streamlit run main.py
```

> La première exécution installera automatiquement toutes les dépendances.

L'application s'ouvrira dans votre navigateur à l'adresse : `http://localhost:8501`

---

## Utilisation

1. **Grille d'évaluation** : Uploadez vos critères de notation (PDF, Word, Excel) ou saisissez-les directement
2. **Travaux étudiants** : Uploadez un fichier ZIP contenant un dossier par étudiant
3. **Base de connaissances** (optionnel) : Ajoutez des documents de référence, URLs ou texte
4. **Format de sortie** : Choisissez Excel, Word structuré, ou Word libre
5. Cliquez sur **"Lancer l'évaluation"**
6. Téléchargez le ZIP contenant les résultats

### Structure du ZIP des travaux étudiants

```
travaux.zip/
├── Jean Dupont/
│   ├── devoir.pdf
│   └── annexe.docx
├── Marie Martin/
│   └── rapport.pdf
└── ...
```

Ou format Moodle :

```
export_moodle.zip/
├── Devoir_Nom/
│   ├── Jean Dupont_12345_assignsubmission_file/
│   │   └── devoir.pdf
│   └── Marie Martin_67890_assignsubmission_onlinetext/
│       └── texteenligne.html
```

---

## Paramètres avancés

- **Modèle OpenAI** : Choisissez le modèle (gpt-4.1, gpt-4o, gpt-4o-mini)
- **Évaluations parallèles** : Nombre d'évaluations simultanées (défaut: 5)
- **Prompt système** : Personnalisez le comportement de l'IA

---

## Dépannage

### "uv n'est pas reconnu"

Fermez et rouvrez VS Code, ou redémarrez votre ordinateur.

### Erreur de clé API

Vérifiez que le fichier `.env` existe et contient :
```
OPENAI_API_KEY=sk-...
```

---

## License

MIT
