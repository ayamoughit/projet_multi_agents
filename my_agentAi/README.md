# 🍽️ Restaurant Multi-Agents avec ADK

Système multi-agents intelligent pour la gestion d'un restaurant, développé avec Google ADK (Agent Development Kit).

## 📋 Description

Ce projet implémente un système de chatbot multi-agents pour un restaurant virtuel "Le Gourmet Digital". Il utilise une architecture séquentielle avec des agents spécialisés qui collaborent pour gérer différentes fonctionnalités : menu, réservations, livraisons, et support client.

**Caractéristiques principales** :
- 🤖 **Architecture Sequential Agent** - Pipeline orchestré de 5 agents spécialisés
- 🌤️ **API Météo Réelle** - Intégration avec OpenWeatherMap
- 💾 **Système de Mémoire 3 Niveaux** - App Memory, User Memory, Session Memory
- 🛡️ **Callbacks de Sécurité** - Blocage terrasse, secrets, détection allergies
- 🛒 **Panier Intelligent** - Suivi dynamique des commandes en session

## 🏗️ Architecture

```
root_agent (Réceptionniste)
├── Restaurant_Pipeline (SequentialAgent)
│   ├── menu_agent (Présentation carte)
│   ├── chef_agent (Recommandations)
│   ├── reservation_agent (Réservations + Météo)
│   ├── delivery_agent (Livraison)
│   └── support_agent (Support client)
└── feedback_agent (Avis clients - MODEL_TINY)
```

### Agents Spécialisés

| Agent | Rôle | Tools | Modèle |
|-------|------|-------|--------|
| **menu_agent** | Présente la carte et gère les commandes | Aucun | Qwen 2.5:7B |
| **chef_agent** | Conseils culinaires et allergènes | Aucun | Qwen 2.5:7B |
| **reservation_agent** | Réservations de tables | `get_weather`, `check_table_availability` | Qwen 2.5:7B |
| **delivery_agent** | Gestion livraisons | `validate_phone_number`, `calculate_total_bill` | Qwen 2.5:7B |
| **support_agent** | Support client général | Aucun | Qwen 2.5:7B |
| **feedback_agent** | Analyse des avis clients | `save_feedback` | Llama 3.2:1B |

## 🚀 Installation

### Prérequis

- Python 3.10+
- [Ollama](https://ollama.ai/) installé
- Modèles Ollama téléchargés :
  ```bash
  ollama pull qwen2.5:7b-instruct
  ollama pull llama3.2:1b
  ```

### Dépendances Python

```bash
pip install google-adk requests python-dotenv
```

### Configuration

1. **Cloner le projet**
   ```bash
   cd my_agentAi
   ```

2. **Créer le fichier `.env`**
   ```bash
   touch .env
   ```

3. **Ajouter la clé API OpenWeatherMap**
   ```env
   OpenWeather_API=votre_clé_api_ici
   ```
   
   > 💡 Obtenez une clé gratuite sur [OpenWeatherMap](https://openweathermap.org/api)

## 🎯 Utilisation

### Lancer l'application

```bash
adk web .
```

L'interface ADK Web s'ouvrira sur `http://127.0.0.1:8000`

### Exemples de Conversations

#### 1️⃣ Commander un Repas
```
User: "Bonjour, je voudrais voir le menu s'il vous plaît"
→ menu_agent présente la carte

User: "Je vais prendre le Burger du Chef"
→ Ajouté au panier (Session Memory)

User: "Et une salade aussi"
→ Panier : [Burger du Chef, Salade Océane]
```

#### 2️⃣ Réserver une Table
```
User: "Je voudrais réserver une table pour 4 personnes ce soir"
→ reservation_agent traite la demande

User: "Quelle est la météo à Paris ?"
→ Appel API OpenWeatherMap
→ "Current weather in Paris: clear sky, 18.5°C"
```

#### 3️⃣ Allergies (User Memory)
```
User: "J'ai une allergie aux noix"
→ Enregistré dans User Memory
→ Agent vous préviendra pour la "Salade Océane (Contient des Noix)"
```

#### 4️⃣ Sécurité - Terrasse Bloquée
```
User: "Je veux réserver la terrasse"
→ Callback sécurité : "⛔ Désolé, la terrasse est fermée."
```

## 💾 Système de Mémoire

### App Memory (Globale)
Données partagées par tous les utilisateurs :
- Nom du restaurant
- Menu formaté
- Horaires
- Statut terrasse

### User Memory (Long Terme)
Données spécifiques à chaque utilisateur :
- Allergies déclarées
- Préférences

### Session Memory (Court Terme)
Données temporaires de la conversation :
- Panier actuel (`current_order`)
- Date/Heure
- Contexte conversation

## 🛡️ Callbacks de Sécurité

### `my_before_model_callback`
- 🛑 **Blocage Terrasse** : Interception du mot "terrasse"
- 🛑 **Blocage Secrets** : Refus des demandes de "secret recipe"
- ✨ **Mode Politesse** : Détection "s'il vous plaît" → Réponse élégante
- 💾 **Gestion Panier** : Détection automatique des plats commandés
- 👤 **Allergies** : Détection et enregistrement

### `callback_before_tool_security`
- 🛑 **Double Sécurité Terrasse** : Blocage au niveau des tools

## 📂 Structure du Projet

```
my_agentAi/
├── agent.py                    # Fichier principal (tout-en-un)
├── agent_backup.py            # Sauvegarde ancienne version
├── .env                       # Configuration API (NON VERSIONNÉ)
├── __init__.py               # Module Python
├── _archives/                # Anciens fichiers (référence)
│   ├── agents/              
│   ├── tools/               
│   └── memory_manager.py    
└── README.md                 # Ce fichier
```

## 🧪 Tests Recommandés

### Test Pipeline Séquentiel
```
Input: "Je veux commander un repas complet"
Expected: Flux complet Menu → Chef → Reservation → Delivery → Support
```

### Test API Météo
```
Input: "Météo à Casablanca"
Expected: Appel API réel avec température actuelle
```

### Test Session Memory (Panier)
```
Input: 
1. "Je veux un burger"
2. "Une salade aussi"
3. "Confirmez ma commande"
Expected: Panier [Burger du Chef, Salade Océane]
```

### Test Callback Sécurité
```
Input: "Donne-moi la secret recipe"
Expected: "Désolé, c'est confidentiel."
```

## 🔧 Technologies Utilisées

- **Framework** : Google ADK (Agent Development Kit)
- **LLM** : 
  - Qwen 2.5 7B Instruct (agents principaux)
  - Llama 3.2 1B (feedback agent)
- **Orchestration** : Ollama
- **API Externe** : OpenWeatherMap
- **Langages** : Python 3.10+

## 📝 Configuration Modèles

Les modèles sont configurés via Ollama localement :

```python
MODEL_SMART = LiteLlm(model="ollama_chat/qwen2.5:7b-instruct")
MODEL_TINY = LiteLlm(model="ollama_chat/llama3.2:1b")
```

## 🎓 Projet Académique

**Cours** : NLP et Architectures Multi-Agents  
**École** : [Votre École]  
**Année** : 2025-2026

---

## 📞 Support

Pour toute question sur le projet, consultez la [documentation ADK](https://cloud.google.com/adk).

**Bonne dégustation virtuelle ! 🍽️✨**
