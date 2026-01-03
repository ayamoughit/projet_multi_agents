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
# 1. CONFIGURATION
# ==========================================
MODEL_SMART = LiteLlm(model="ollama_chat/qwen2.5:7b-instruct")
MODEL_TINY = LiteLlm(model="ollama_chat/llama3.2:1b")

# ==========================================
# 2. TOOLS (OUTILS)
# ==========================================
def get_weather(city: str) -> str:
    api_key = os.getenv("OpenWeather_API")
    if not api_key: return f"Météo (Simulation) à {city} : Ensoleillé, 22°C."
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = { "q": city, "appid": api_key, "units": "metric", "lang": "fr" }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"Météo actuelle à {city}: {data['weather'][0]['description']}, {data['main']['temp']}°C."
        return "Erreur API."
    except Exception as e: return f"Erreur Connexion: {str(e)}"

def save_feedback(avis: str, sentiment: str) -> str:
    print(f"💾 [DB] Feedback saved: {avis} (Sentiment: {sentiment})", flush=True)
    return "Avis enregistré avec succès."

def check_table_availability(date: str, people: int, location: str = "salle") -> str:
    return f"Table OK pour {people} pers en {location} le {date}."

def validate_phone_number(phone: str) -> str: return f"Numéro {phone} validé."
def calculate_total_bill(items: str) -> str: return "Total: 42.50€."

# ==========================================
# 3. CALLBACKS (VOTRE STRUCTURE + LOGIQUE MÉMOIRE)
# ==========================================

def callback_before_agent_log(callback_context: CallbackContext) -> Optional[types.Content]:
    """Log simple (Pour les agents du pipeline)."""
    agent_name = callback_context.agent_name
    now = datetime.datetime.now()
    time_part = now.strftime("%H:%M")
    print(f"\n[CALLBACK]  Agent '{agent_name}' actif à {time_part}", flush=True)
    return None

def check_if_agent_should_run(callback_context: CallbackContext) -> Optional[types.Content]:
    """Log détaillé (Pour le ROOT)."""
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict()
    now = datetime.datetime.now()
    time_part = now.strftime("%H:%M")

    print(f"\n[Callback] Entering agent: {agent_name} (Inv: {invocation_id}) à {time_part}", flush=True)

    if current_state.get("skip_llm_agent", False):
        print(f"[Callback] State condition 'skip_llm_agent=True' met: Skipping agent {agent_name}.", flush=True)
        return types.Content(parts=[types.Part(text=f"Agent {agent_name} skipped.")], role="model")
    else:
        print(f"[Callback] State condition not met: Proceeding with agent {agent_name}.", flush=True)
        return None

def simple_before_model_modifier(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    LE CERVEAU : C'est ici que je mets la mémoire (Burger/Allergie) et le correctif Root.
    """
    agent_name = callback_context.agent_name
    print(f"[Callback] Before model call for agent: {agent_name}", flush=True)

    # 1. Lecture du message utilisateur
    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
            print(f"[Callback] Inspecting last user message: '{last_user_message}'", flush=True)
            if last_user_message:
                last_user_message = last_user_message.lower()

    # 2. LOGIQUE MÉTIER (Mémoire)
    if "allergie" in last_user_message:
        callback_context.state["user:allergies?"] = " OUI (Noté)"
        print("[Mémoire] Allergie notée.", flush=True)

    # Panier (On remplit la liste avec les plats du menu)
    current_order = callback_context.state.get("current_order", [])
    added = False
    
    # Détection des plats
    if "burger" in last_user_message and "Burger Maison" not in current_order:
        current_order.append("Burger Maison"); added = True
    if "saumon" in last_user_message and "Pavé de Saumon" not in current_order:
        current_order.append("Pavé de Saumon"); added = True
    if "risotto" in last_user_message and "Risotto" not in current_order:
        current_order.append("Risotto aux Champignons"); added = True
    if "salade" in last_user_message and "Salade César" not in current_order:
        current_order.append("Salade César"); added = True
    if "soupe" in last_user_message and "Soupe" not in current_order:
        current_order.append("Soupe à l'oignon"); added = True
    if "tiramisu" in last_user_message and "Tiramisu" not in current_order:
        current_order.append("Tiramisu"); added = True
        
    if added:
        callback_context.state["current_order"] = current_order
        print(f" [Mémoire] Panier mis à jour : {current_order}", flush=True)

    # Sécurité Terrasse
    if "terrasse" in last_user_message:
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=" Désolé, la terrasse est fermée.")] ))

    # FIX ROOT : Le Root met à jour la mémoire mais ne reçoit pas l'injection
    if agent_name == "root_agent":
        print(f"[Callback] Agent Root détecté : Pas d'injection (Transfert requis).", flush=True)
        return None

    # 3. INJECTION DU PROMPT (Pour les autres agents)
    actual_menu = callback_context.state.get("app:menu_text_formatted", "Menu non chargé")
    actual_order = callback_context.state.get("current_order", [])
    actual_allergies = callback_context.state.get("user:allergies?", "Aucune")

    context_injection = f"""
    [MÉMOIRE SYSTÈME]
    -------------------------
    1. MENU ACTUEL : {actual_menu}
    2. PANIER CLIENT : {actual_order} (Si non vide, confirme l'ajout)
    3. ALLERGIES : {actual_allergies}
    -------------------------
    """

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

    print(f"[Injection] Prompt mis à jour pour {agent_name}", flush=True)
    return None

def simple_before_tool_modifier(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """Inspects/modifies tool args or skips the tool call."""
    agent_name = tool_context.agent_name
    tool_name = tool.name
    
  
    print(f"[Callback] Before tool call for tool '{tool_name}' in agent '{agent_name}'", flush=True)
    print(f"[Callback] Original args: {args}", flush=True)

    if tool_name == 'check_table_availability':
        location = args.get('location', '').lower()
        if any(mot in location for mot in ["terrasse", "dehors"]):
            print("[Callback]  SÉCURITÉ : Terrasse demandée -> BLOQUÉ.", flush=True)
            # On retourne un dictionnaire pour bloquer l'outil proprement
            return {"available": False, "reason": "Zone fermée."}

    # VOS LOGS DE FIN (Je n'y touche pas)
    print("[Callback] Proceeding with original or previously modified args.", flush=True)
    return None

# ==========================================
# 4. AGENTS (VOTRE CONFIGURATION EXACTE)
# ==========================================

menu_agent = Agent(
    name="menu_agent",
    model=MODEL_SMART,
    description="Prend la commande.",
    instruction="""
    Tu es le serveur du restaurant 'Le Gourmet Digital'.
    
    TES INSTRUCTIONS :
    1. Regarde le [PANIER CLIENT] et le [MENU] injectés.
    2. Si le client demande le menu ou si le panier est VIDE : 
       - Présente poliment les Entrées, Plats et Desserts disponibles.
    
    3. Si le client passe une commande (ex: "Je veux le Burger") :
       - Vérifie que l'article est dans le menu.
       - Confirme simplement l'ajout (ex: "Très bon choix, c'est noté.").
       - Demande s'il désire autre chose.
       
    4. NE DIS PAS "Bonjour" si la conversation est déjà commencée.
    """,
    before_agent_callback=[callback_before_agent_log], 
    before_model_callback=[simple_before_model_modifier]
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
    instruction="Gère les réservations et la MÉTÉO.",
    tools=[check_table_availability, get_weather], 
    before_agent_callback=[callback_before_agent_log],
    before_tool_callback=[simple_before_tool_modifier] 
)

delivery_agent = Agent(
    name="delivery_agent",
    model=MODEL_SMART,
    instruction="Gère la livraison. Confirme le panier final et le total.",
    tools=[validate_phone_number, calculate_total_bill],
    before_agent_callback=[callback_before_agent_log],
   
)

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

feedback_agent = Agent(
    name="feedback_agent",
    model=MODEL_SMART,
    instruction="Dis : 'Bonjour, c'est le service qualité. Votre avis ?' Puis utilise `save_feedback`.",
    tools=[save_feedback],
    before_agent_callback=[callback_before_agent_log]
)

# ==========================================
# 5. INITIALISATION & ROOT AGENT
# ==========================================
async def init_state(callback_context: CallbackContext):
    print("\n[Init]  Initialisation du State...", flush=True)
    callback_context.state["app:restaurant_name"] = "Le Gourmet Digital"
    
    # MENU SYNCHRONISÉ AVEC LE CODE
    callback_context.state["app:menu_text_formatted"] = """
    ENTRÉES:
    - Salade César (12€)
    - Soupe à l'oignon (10€)
    
    PLATS:
    - Burger Maison (18€)
    - Pavé de Saumon (22€)
    - Risotto aux Champignons (19€)
    
    DESSERTS:
    - Tiramisu (8€)
    - Crème Brûlée (9€)
    """
    
    if "user:allergies?" not in callback_context.state: callback_context.state["user:allergies?"] = "Aucune" 
    if "current_order" not in callback_context.state: callback_context.state["current_order"] = []
    
    callback_before_agent_log(callback_context) 

root_agent = Agent(
    name="root_agent",
    model=MODEL_SMART,
    instruction="Réceptionniste. Commande -> 'Restaurant_Pipeline'. Avis -> 'feedback_agent'.",
    sub_agents=[restaurant_pipeline, feedback_agent],
    
    before_agent_callback=[init_state, check_if_agent_should_run], 
    before_model_callback=[simple_before_model_modifier]
)