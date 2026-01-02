import os
import datetime
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from google.genai import types

# Charge les variables d'environnement
load_dotenv()

# --- IMPORTS FRAMEWORK ADK ---
from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.lite_llm import LiteLlm 
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

# ==========================================
# 1. CONFIGURATION (MULTI-MODÈLES)
# ==========================================
# Modèle Puissant (Pour la logique, la mémoire, les outils)
MODEL_SMART = LiteLlm(model="ollama_chat/qwen2.5:7b-instruct")

# Modèle Léger (Pour les tâches simples - Exigence Prof)
MODEL_TINY = LiteLlm(model="ollama_chat/llama3.2:1b")

# ==========================================
# 2. TOOLS (OUTILS)
# ==========================================
def get_weather(city: str) -> str:
    """Récupère la météo via OpenWeatherMap ou simule si pas de clé."""
    api_key = os.getenv("OpenWeather_API")
    
    if not api_key:
        return f"Météo (Simulation) à {city} : Ensoleillé, 22°C (Clé API manquante)."
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = { "q": city, "appid": api_key, "units": "metric", "lang": "fr" }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            return f"Météo actuelle à {city}: {desc}, {temp}°C."
        else:
            return f"Impossible de récupérer la météo pour {city} (Erreur API)."
    except Exception as e:
        return f"Erreur de connexion météo pour {city}: {str(e)}"

def save_feedback(avis: str, sentiment: str) -> str:
    print(f"💾 [DB] Feedback saved: {avis} (Sentiment: {sentiment})")
    return "Avis enregistré avec succès."

def check_table_availability(date: str, people: int, location: str = "salle") -> str:
    return f"Table OK pour {people} pers en {location} le {date}."

def validate_phone_number(phone: str) -> str:
    return f"Numéro {phone} validé."

def calculate_total_bill(items: str) -> str:
    return "Total: 42.50€."

# ==========================================
# 3. CALLBACKS (MÉMOIRE & LOGS)
# ==========================================

def callback_before_agent_log(callback_context: CallbackContext) -> Optional[types.Content]:
    agent_name = callback_context.agent_name
    now = datetime.datetime.now()
    time_part = now.strftime("%H:%M")
    print(f"\n[CALLBACK] 🚀 Agent '{agent_name}' actif à {time_part}")
    return None

# --- LE CERVEAU DU SYSTÈME (MÉMOIRE + INJECTION) ---
def my_before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Gère la détection (Panier/Allergies) ET l'injection dans le Prompt."""
    
    agent_name = callback_context.agent_name
    
    # 1. Récupération du message utilisateur
    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts:
            part = llm_request.contents[-1].parts[0]
            last_user_message = getattr(part, 'text', '') or ""
            last_user_message = last_user_message.lower()

    # 2. MISE À JOUR DU STATE (La mémoire)
    
    # Allergies
    if "allergie" in last_user_message or "allergic" in last_user_message:
        callback_context.state["user:allergies?"] = "⚠️ OUI (Noté dans le dossier client)"
        print("💾 [Mémoire] Allergie notée.")

    # Panier (On remplit la liste)
    current_order = callback_context.state.get("current_order", [])
    added = False
    
    # Logique simple de détection de mots-clés
    if "burger" in last_user_message and "Burger du Chef" not in current_order:
        current_order.append("Burger du Chef")
        added = True
    if "salade" in last_user_message and "Salade Océane" not in current_order:
        current_order.append("Salade Océane")
        added = True
    if "pâtes" in last_user_message and "Pâtes aux Truffes" not in current_order:
        current_order.append("Pâtes aux Truffes")
        added = True
        
    if added:
        callback_context.state["current_order"] = current_order
        print(f"🛒 [Mémoire] Panier mis à jour : {current_order}")

    # 3. SÉCURITÉ
    if "terrasse" in last_user_message:
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(text="⛔ Désolé, la terrasse est fermée.")] ))
    if "secret" in last_user_message and "recipe" in last_user_message:
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(text="Désolé, c'est confidentiel.")] ))

    # 4. INJECTION 
    # On récupère les valeurs à jour
    actual_menu = callback_context.state.get("app:menu_text_formatted", "Menu non chargé")
    actual_order = callback_context.state.get("current_order", [])
    actual_allergies = callback_context.state.get("user:allergies?", "Aucune")

    # On prépare le texte à injecter dans le cerveau de l'agent
    context_injection = f"""
    [MÉMOIRE SYSTÈME VIVANTE]
    -------------------------
    1. MENU RESTAURANT : {actual_menu}
    2. PANIER CLIENT ACTUEL : {actual_order} 
       (IMPORTANT : Si cette liste n'est pas vide, le client a DÉJÀ commandé ça. Confirme-le.)
    3. ALLERGIES CLIENT : {actual_allergies}
    -------------------------
    """

    # On l'ajoute à l'instruction système
    original_instruction = llm_request.config.system_instruction
    if not original_instruction:
         llm_request.config.system_instruction = types.Content(role="system", parts=[types.Part(text=context_injection)])
    else:
        if not isinstance(original_instruction, types.Content):
             original_instruction = types.Content(role="system", parts=[types.Part(text=str(original_instruction))])
        if not original_instruction.parts:
            original_instruction.parts.append(types.Part(text=""))
        
        original_instruction.parts[0].text += f"\n\n{context_injection}"
        llm_request.config.system_instruction = original_instruction

    print(f"🧠 [Injection] L'agent {agent_name} voit le panier : {actual_order}")

    return None

def callback_before_tool_security(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    if tool.name == "check_table_availability":
        location = args.get("location", "").lower()
        if any(mot in location for mot in ["terrasse", "dehors", "extérieur"]):
            print(f"\n[Security] Zone interdite : {location}")
            return {"available": False, "reason": "Zone fermée."}
    return None

# ==========================================
# 4. AGENTS
# ==========================================

menu_agent = Agent(
    name="menu_agent",
    model=MODEL_SMART,
    description="Prend la commande.",
    instruction="""
    Tu es le serveur.
    
    ⚡ RÈGLE IMPORTANTE :
    Dès que tu reçois le client, regarde IMMÉDIATEMENT le [PANIER CLIENT ACTUEL] dans ta mémoire.
    - Si le panier contient un plat (ex: Burger), dis : "Bonjour ! Je vois que vous avez choisi le [Nom du Plat]. C'est noté. Désirez-vous autre chose ?"
    - Sinon, propose le menu.
    """,
    before_agent_callback=[callback_before_agent_log],
    before_model_callback=[my_before_model_callback] # ✅ Callback activé
)

chef_agent = Agent(
    name="chef_agent",
    model=MODEL_SMART,
    instruction="Tu es le Chef.",
    before_agent_callback=[callback_before_agent_log]
)

reservation_agent = Agent(
    name="reservation_agent",
    model=MODEL_SMART,
    instruction="Gère les réservations et la MÉTÉO (avec get_weather).",
    tools=[check_table_availability, get_weather], 
    before_agent_callback=[callback_before_agent_log],
    before_tool_callback=[callback_before_tool_security] 
)

delivery_agent = Agent(
    name="delivery_agent",
    model=MODEL_SMART,
    instruction="Gère la livraison. Confirme le panier final et le total.",
    tools=[validate_phone_number, calculate_total_bill],
    before_agent_callback=[callback_before_agent_log],
    before_model_callback=[my_before_model_callback] # ✅ Callback activé
)

# ✅ Utilisation du Modèle TINY pour le support (Exigence Prof)
support_agent = Agent(
    name="support_agent",
    model=MODEL_TINY, 
    instruction="Support Client basique.",
    tools=[], 
    before_agent_callback=[callback_before_agent_log]
)

restaurant_pipeline = SequentialAgent(
    name="Restaurant_Pipeline",
    description="Flux complet du restaurant",
    sub_agents=[menu_agent, chef_agent, reservation_agent, delivery_agent, support_agent],
    before_agent_callback=[callback_before_agent_log]
)

# ==========================================
# 5. AGENT FEEDBACK
# ==========================================
feedback_agent = Agent(
    name="feedback_agent",
    model=MODEL_SMART,
    instruction="""
    Tu es l'agent de Feedback.
    
    PROTOCOLE :
    1. Si le client ne parle pas, PRENDS L'INITIATIVE : Dis "Bonjour, c'est le service qualité. Votre avis ?"
    2. ATTENDS la réponse.
    3. ENSUITE utilise l'outil `save_feedback`.
    """,
    tools=[save_feedback],
    before_agent_callback=[callback_before_agent_log]
)

# ==========================================
# 6. INITIALISATION & ROOT AGENT
# ==========================================
async def init_state(callback_context: CallbackContext):
    print("\n[Init] 🟢 Initialisation du State...")
    
    callback_context.state["app:restaurant_name"] = "Le Gourmet Digital"
    callback_context.state["app:menu_text_formatted"] = """
    - Burger du Chef (18€)
    - Salade Océane (14€) - Contient des Noix
    - Pâtes aux Truffes (22€)
    """
    
    if "user:allergies?" not in callback_context.state:
        callback_context.state["user:allergies?"] = "Aucune" 
    if "current_order" not in callback_context.state:
        callback_context.state["current_order"] = []

    callback_before_agent_log(callback_context)

root_agent = Agent(
    name="root_agent",
    model=MODEL_SMART,
    instruction="""
    Tu es le réceptionniste.
    - Commande / Menu / Météo -> Transfère à 'Restaurant_Pipeline'
    - Avis -> Transfère à 'feedback_agent'
    Utilise `transfer_to_agent`.
    """,
    sub_agents=[restaurant_pipeline, feedback_agent],
    before_agent_callback=[init_state],
    # 👇 LA CORRECTION EST ICI 👇
    # On ajoute la mémoire au Root pour qu'il remplisse le panier AVANT de transférer
    before_model_callback=[my_before_model_callback]
)