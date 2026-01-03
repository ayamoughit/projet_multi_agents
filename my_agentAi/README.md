# Système Multi-Agents pour Restaurant - "Le Gourmet Digital"

## Description du Projet

Ce projet est un **système de chatbot intelligent multi-agents** développé avec **Google ADK (Agent Development Kit)** pour gérer un restaurant virtuel appelé **"Le Gourmet Digital"**.

Au lieu d'avoir un seul chatbot qui fait tout, le système utilise **plusieurs agents spécialisés** qui collaborent ensemble pour offrir une expérience client complète : de la consultation du menu jusqu'à la livraison, en passant par les réservations et le support client.

## Fonctionnalités Principales

Ce système permet de :
- **Consulter le menu** du restaurant avec des prix détaillés
- **Prendre des commandes** via le menu_agent
- **Réserver une table** avec vérification de disponibilité
- **Consulter la météo** pour planifier sa visite
- **Gérer la livraison** avec validation du numéro de téléphone
- **Donner son avis** sur l'expérience client
- **Démontrer les callbacks ADK** (before_agent, before_model, before_tool)

---

## Architecture du Système

Le système utilise une **architecture séquentielle** avec un agent racine qui dirige les utilisateurs vers le bon pipeline :

![Architecture Séquentielle](./Screens/shema%20s%C3%A9quentielle.png)

### Flux de traitement

```
Client
  ↓
  > root_agent (Réceptionniste)
        ↓
        > Restaurant_Pipeline (Agent Séquentiel)
              1. menu_agent         → Présente le menu
              2. chef_agent         → Conseils culinaires
              3. reservation_agent  → Réservations + Météo
              4. delivery_agent     → Livraison
              5. support_agent      → Support client
        ↓
        > feedback_agent → Collecte des avis
```

### Agents du Système

| Agent | Rôle | Outils Disponibles | Modèle IA |
|-------|------|-------------------|-----------|
| **root_agent** | Réceptionniste - Dirige vers le bon service | Aucun | Qwen 2.5 7B |
| **menu_agent** | Présente la carte et prend les commandes | Aucun | Qwen 2.5 7B |
| **chef_agent** | Donne des conseils culinaires | Aucun | Qwen 2.5 7B |
| **reservation_agent** | Gère les réservations de tables | `get_weather`, `check_table_availability` | Qwen 2.5 7B |
| **delivery_agent** | Organise la livraison | `validate_phone_number`, `calculate_total_bill` | Qwen 2.5 7B |
| **support_agent** | Support client général | Aucun | Llama 3.2 1B |
| **feedback_agent** | Collecte et analyse les avis | `save_feedback` | Qwen 2.5 7B |

---

## Démonstration avec Screenshots

### 1. Callbacks Before Agent

Les **callbacks before agent** s'exécutent **avant** que l'agent ne traite la requête. Ils permettent de :
- Logger l'entrée dans un agent
- Bloquer l'exécution de l'agent selon des conditions
- Inspecter l'état de la session

![Callbacks Before Agent](./Screens/callbaks%20agents%20.png)

**Ce qu'on voit :**
- `[Callback] Entering agent: root_agent` → L'agent racine démarre
- `Inv: e-557a5bd...` → Un ID unique d'invocation pour le traçage
- L'heure exacte du démarrage
- `State condition not met: Proceeding` → Pas de condition de blocage, l'agent continue

---

### 2. Callbacks Before Model (Menu Agent)

Les **callbacks before model** s'exécutent **avant** l'appel au modèle IA. Ils permettent de :
- Inspecter le message de l'utilisateur
- Modifier les instructions système
- Bloquer l'appel au modèle (ex: mot-clé "BLOCK")

![Callbacks Before Model](./Screens/callbaks%20model%20menu%20.png)

**Ce qu'on voit :**
- `Before model call for agent: menu_agent` → Le menu_agent va appeler le modèle IA
- `Inspecting last user message: 'bonjour'` → Le message utilisateur est analysé
- `Proceeding with LLM call` → Aucun blocage, l'appel au modèle est autorisé

---

### 3. Callbacks Before Tool

Les **callbacks before tool** s'exécutent **avant** l'utilisation d'un outil. Ils permettent de :
- Voir quels arguments sont passés à l'outil
- Modifier les arguments (ex: corriger une ville)
- Bloquer l'utilisation de l'outil

![Callbacks Before Tool](./Screens/callback%20tool.png)

**Ce qu'on voit :**
- `Before tool call for tool 'check_table_availability'` → L'outil de réservation va être appelé
- `in agent 'reservation_agent'` → C'est l'agent de réservation qui l'utilise
- `Original args: {'date': '2023-10-15', 'location': 'terrasse', 'people': 2}` → Les paramètres de la réservation
- `Proceeding with original args` → Les arguments sont acceptés tels quels

---

### 4. Callbacks Before Tool - Outil Météo

L'agent `reservation_agent` peut appeler l'**API OpenWeatherMap** pour donner la météo :

![Tool Weather](./Screens/tool%20weather%20.png)

**Ce qu'on voit :**
- Le callback before tool s'exécute avant l'appel à `get_weather`
- L'utilisateur demande : *"quelle est la météo ?"*
- Le système appelle automatiquement l'outil `get_weather`
- Réponse : *"Météo (Simulation) à Casablanca : Ensoleillé, 22°C"*

> **Note** : Si vous ajoutez une vraie clé API dans `.env`, vous obtiendrez les données réelles !

---

### 5. Test de Feedback

L'agent `feedback_agent` collecte et enregistre les avis clients :

![Test Feedback](./Screens/test%20de%20feedback.png)

**Flux du processus :**
1. L'utilisateur signale qu'il veut donner un avis
2. Le `root_agent` transfère vers `feedback_agent`
3. Le `feedback_agent` pose des questions pour collecter l'avis
4. L'avis est sauvegardé via l'outil `save_feedback`

---

### 6. Enregistrement de Feedback

Détail de l'enregistrement des feedbacks dans la base de données :

![Enregistrer Feedback](./Screens/enregistrer%20feedback.png)

**Ce qu'on voit :**
- L'agent demande : *"Bonjour, c'est le service qualité. Votre avis ?"*
- L'utilisateur donne son avis
- L'outil `save_feedback` est appelé pour enregistrer l'avis dans la base de données
- Message de confirmation : *"Avis enregistré avec succès"*

---

### 7. Test d'Évaluation (Evalset)

Les **evalsets** permettent de tester automatiquement le système avec des scénarios prédéfinis :

![Test Eval](./Screens/test%20eval%20.png)

**Ce qu'on voit :**
- Des conversations tests sont lancées automatiquement
- Le système vérifie que les agents répondent correctement
- Les résultats montrent si les tests passent ou échouent

---

### 8. Affichage de la Mémoire dans le Terminal (Partie 1)

Le système affiche en temps réel les informations stockées dans la mémoire durant la conversation :

![Mémoire Terminal 1](./Screens/memoir%20.png)

**Ce qu'on voit :**
- Affichage détaillé de la **App Memory** (mémoire globale)
- Informations sur le restaurant : menu, prix, horaires
- Affichage de la **User Memory** (mémoire utilisateur)
- Données personnalisées par utilisateur : allergies, préférences

---

### 9. Affichage de la Mémoire dans le Terminal (Partie 2)

Suite de l'affichage des informations mémoire :

![Mémoire Terminal 2](./Screens/memoir%202.png)

**Ce qu'on voit :**
- Affichage de la **Session Memory** (mémoire de session)
- Panier actuel de l'utilisateur
- Date et heure de la session
- Contexte conversationnel temporaire

---

### 10. État de l'Agent et Mémoire Active

Vue détaillée de l'état actuel de l'agent et de la mémoire en cours d'utilisation :

![État Agent et Mémoire](./Screens/memoir%203.png)

**Ce qu'on voit :**
- L'agent actuel en cours d'exécution (`current_state`)
- Les variables d'état : `burger_count` et `salade_count`
- Informations de traçage et session ID
- Communication entre l'utilisateur et l'agent Balade-Océane

---

## Système de Mémoire à 3 Niveaux

### App Memory (Mémoire Globale)
Partagée par **tous les utilisateurs** :
- Nom du restaurant : "Le Gourmet Digital"
- Menu complet avec prix
- Horaires d'ouverture
- Statut de la terrasse

### User Memory (Mémoire Utilisateur)
Spécifique à **chaque utilisateur** :
- Allergies déclarées
- Plats préférés
- Historique de réservations

### Session Memory (Mémoire de Session)
Temporaire, pour la **conversation actuelle** :
- Panier en cours
- Date et heure
- Contexte de la conversation

---

## Sécurité et Callbacks

### 3 Types de Callbacks

1. **`before_agent_callback`**
   - S'exécute avant l'entrée dans un agent
   - Exemple : Logger, bloquer un agent selon l'état

2. **`before_model_callback`**
   - S'exécute avant l'appel au modèle IA
   - Exemple : Modifier les instructions, bloquer certains mots

3. **`before_tool_callback`**
   - S'exécute avant l'utilisation d'un outil
   - Exemple : Valider/modifier les arguments, bloquer un outil

### Règles de Sécurité Implémentées

- **Terrasse bloquée** : Refus automatique des réservations en terrasse
- **Secrets protégés** : Impossible de demander la recette secrte
- **Allergies** : Détection et alerte automatique

---

## Exemples de Conversation

### Scénario 1 : Commander un repas

```
→ User: "Bonjour, je voudrais voir le menu"
← menu_agent: "Voici notre carte :
   ENTRÉES: Salade César (12€), Soupe à l'oignon (10€)
   PLATS: Burger du Chef (18€), Salade Océane (14€), Pâtes aux Truffes (22€)
   DESSERTS: Tiramisu (8€), Crème Brûlée (9€)"

→ User: "Je prends le Burger du Chef"
← menu_agent: "Très bon choix ! Le Burger du Chef est noté. Autre chose ?"

→ User: "Un Tiramisu aussi"
← menu_agent: "Parfait ! Votre panier : Burger du Chef, Tiramisu"
```

### Scénario 2 : Réserver avec météo

```
→ User: "Je veux réserver une table pour 4 personnes"
← reservation_agent: "Bien sûr ! Pour quelle date ?"

→ User: "Ce soir à 20h. Au fait, quelle est la météo ?"
← reservation_agent: [Appel API] "Météo actuelle : Ensoleillé, 22°C"
```

### Scénario 3 : Allergies

```
→ User: "J'ai une allergie aux noix"
← system: [✓ Enregistré dans User Memory]

→ User: "Je veux la Salade Océane"
← menu_agent: "⚠ Attention ! La Salade Océane contient des noix."
```

---

