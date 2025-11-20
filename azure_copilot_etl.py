"""
ModelOp Partner ETL Script: Azure M365 Copilot -> ModelOp Center
================================================================
INTENDED AUDIENCE: ModelOp Partners & Solutions Engineers
CONTEXT: ModelOp Partner Demo Lab (Stages 3 & 4)

DESCRIPTION:
    This script creates the "Model Implementation" data required to demonstrate 
    ModelOp's LLM Governance capabilities. 
    
    It operates in two modes:
    1. MOCK MODE (Default): Generates synthetic data with intentional defects 
       (PII, Toxicity, Negative Sentiment) to trigger ModelOp OOTB Monitors.
    2. LIVE MODE: Connects to your Azure Tenant to pull real Copilot interaction 
       logs via the Microsoft Graph API.

INSTRUCTIONS:
    1. Run 'as is' to generate synthetic data for the Demo Lab.
    2. To use real data, set USE_MOCKS = False and populate the AZURE_CREDENTIALS section.
    3. Upload the resulting JSON file to the ModelOp Partner Demo Lab.

AUTHOR: ModelOp Solutions Engineering
"""

import json
import random
import re
import uuid
import string
import time
import requests # Requires: pip install requests
from datetime import datetime, timedelta
from faker import Faker # Requires: pip install faker

# =============================================================================
#  GLOBAL CONFIGURATION (START HERE)
# =============================================================================

# TOGGLE THIS TO SWITCH BETWEEN SYNTHETIC AND REAL AZURE DATA
USE_MOCKS = True 

# -----------------------------------------------------------------------------
# SECTION A: REAL AZURE CREDENTIALS (Used only if USE_MOCKS = False)
# -----------------------------------------------------------------------------
# INSTRUCTIONS FOR PARTNERS:
# 1. Go to Azure Portal > App Registrations: https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps
# 2. Create a New Registration. Copy the Client ID and Tenant ID below.
# 3. In the App > Certificates & secrets, create a "New client secret" and copy the Value.
# 4. In the App > API Permissions, add 'Microsoft Graph' -> 'Application permissions' -> 'Chat.Read.All'
# 5. Grant Admin Consent for the permissions.

AZURE_CREDENTIALS = {
    "TENANT_ID":     "YOUR_TENANT_ID_HERE",     # e.g., "b19c4...", found in Azure AD Overview
    "CLIENT_ID":     "YOUR_CLIENT_ID_HERE",     # Application (client) ID
    "CLIENT_SECRET": "YOUR_CLIENT_SECRET_HERE", # Generated Client Secret Value
    "USER_ID":       "TARGET_USER_ID_OR_EMAIL"  # Optional: Target specific user email to scrape
}

# -----------------------------------------------------------------------------
# SECTION B: MOCK DATA SIMULATION SETTINGS (Used only if USE_MOCKS = True)
# -----------------------------------------------------------------------------
# These settings control the "Fault Injection" to ensure ModelOp Monitors light up red/yellow.
# References "Stage 6: Ongoing Monitoring" in the Partner Guide.

MOCK_CONFIG = {
    "NUM_CHATS": 50,                  # Volume of conversations to generate
    "COPILOT_AGENT_ID": "modelop-copilot-agent-001",
    
    # --- INJECTION RATES (0.0 to 1.0) ---
    # Higher rates = More alerts in ModelOp Dashboard
    "PII_RATE": 0.10,                 # 10% of rows contain Fake SSNs (Triggers PII Monitor)
    "TOXICITY_RATE": 0.05,            # 5% of rows contain insults (Triggers Toxicity Monitor)
    "GIBBERISH_RATE": 0.05,           # 5% of rows contain nonsense (Triggers Gibberish Monitor)
    "NEGATIVE_SENTIMENT_RATE": 0.20   # 20% of rows are angry (Triggers Sentiment Monitor)
}

# Initialize Faker
fake = Faker()
Faker.seed(4321)

# =============================================================================
#  HELPER FUNCTIONS
# =============================================================================

def clean_html(raw_html):
    """
    Azure Graph API returns messages wrapped in HTML divs.
    This strips tags to provide clean text for NLP analysis.
    """
    if not raw_html: return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def get_mock_injected_content(standard_text):
    """
    Injects defects into synthetic data to ensure OOTB monitors trigger.
    """
    roll = random.random()
    
    # 1. Gibberish (Triggers 'Impl_Gib' Monitor)
    if roll < MOCK_CONFIG["GIBBERISH_RATE"]:
        noise = ''.join(random.choices(string.ascii_letters + string.digits, k=45))
        return f"SYSTEM FAULT {noise} {noise}"

    # 2. Toxicity (Triggers 'Impl_Tox' Monitor)
    elif roll < (MOCK_CONFIG["GIBBERISH_RATE"] + MOCK_CONFIG["TOXICITY_RATE"]):
        toxic_phrases = [
            "You are absolutely useless.", "I hate this stupid AI.",
            "Shut up you terrible software.", "This is an idiotic response."
        ]
        return random.choice(toxic_phrases)

    # 3. PII (Triggers 'Impl_PII' Monitor)
    elif roll < (MOCK_CONFIG["GIBBERISH_RATE"] + MOCK_CONFIG["TOXICITY_RATE"] + MOCK_CONFIG["PII_RATE"]):
        return f"My SSN is {fake.ssn()} and phone is {fake.phone_number()}."

    # 4. Negative Sentiment (Triggers 'Impl_Sent' Monitor)
    elif roll < (MOCK_CONFIG["GIBBERISH_RATE"] + MOCK_CONFIG["TOXICITY_RATE"] + 
                 MOCK_CONFIG["PII_RATE"] + MOCK_CONFIG["NEGATIVE_SENTIMENT_RATE"]):
        return "I am extremely disappointed and frustrated with this service."

    return standard_text

# =============================================================================
#  CORE LOGIC: DATA INGESTION
# =============================================================================

def get_azure_access_token():
    """
    Authenticates with Azure AD to get a Bearer Token.
    Endpoint: https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
    """
    print("  > Authenticating with Azure Active Directory...")
    url = f"https://login.microsoftonline.com/{AZURE_CREDENTIALS['TENANT_ID']}/oauth2/v2.0/token"
    
    payload = {
        'client_id': AZURE_CREDENTIALS['CLIENT_ID'],
        'client_secret': AZURE_CREDENTIALS['CLIENT_SECRET'],
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        print(f"  [ERROR] Azure Auth Failed. Check your Client ID/Secret. Details: {e}")
        exit(1)

def fetch_real_azure_data():
    """
    Connects to Microsoft Graph API to pull actual chat history.
    Docs: https://learn.microsoft.com/en-us/graph/api/chat-list
    """
    token = get_azure_access_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    # 1. Get List of Chats
    # Note: In a real production script, you would implement pagination handling (odata.nextLink)
    print("  > Fetching Chat Threads from Microsoft Graph...")
    chats_url = "https://graph.microsoft.com/v1.0/chats" 
    
    try:
        response = requests.get(chats_url, headers=headers)
        response.raise_for_status()
        chats = response.json().get('value', [])
    except Exception as e:
        print(f"  [ERROR] Failed to fetch chats. Ensure 'Chat.Read.All' permission is granted. Details: {e}")
        return []

    raw_data = []
    print(f"  > Found {len(chats)} threads. Fetching messages...")

    # 2. Loop through threads and get messages
    for i, chat in enumerate(chats[:50]): # Limit to 50 for the POC
        chat_id = chat['id']
        msgs_url = f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages"
        msg_resp = requests.get(msgs_url, headers=headers)
        
        if msg_resp.status_code == 200:
            messages = msg_resp.json().get('value', [])
            raw_data.append({
                "meta": {"id": chat_id, "topic": chat.get('topic', 'No Topic')},
                "messages": messages
            })
        time.sleep(0.2) # Slight delay to respect rate limits
        
    return raw_data

def generate_mock_data():
    """
    Generates synthetic data mimicking the Azure Graph API Schema.
    """
    print(f"  > Generating {MOCK_CONFIG['NUM_CHATS']} synthetic Azure chat threads...")
    raw_data = []
    users = [{"id": str(uuid.uuid4()), "name": fake.name()} for _ in range(10)]
    
    for _ in range(MOCK_CONFIG["NUM_CHATS"]):
        user = random.choice(users)
        chat_id = f"19:{uuid.uuid4()}@thread.v2"
        base_time = datetime.now() - timedelta(days=random.randint(0, 30))
        
        messages = []
        # Create conversation turns
        for i in range(random.randint(2, 5)):
            # User Message
            user_text = get_mock_injected_content(fake.sentence(nb_words=10))
            messages.append({
                "id": str(uuid.uuid4()),
                "createdDateTime": (base_time + timedelta(minutes=i*5)).isoformat() + "Z",
                "from": {"user": {"id": user["id"], "displayName": user["name"]}},
                "body": {"content": f"<div>{user_text}</div>"}
            })
            
            # Copilot Response
            bot_text = fake.paragraph(nb_sentences=2)
            messages.append({
                "id": str(uuid.uuid4()),
                "createdDateTime": (base_time + timedelta(minutes=i*5, seconds=30)).isoformat() + "Z",
                "from": {"user": {"id": MOCK_CONFIG["COPILOT_AGENT_ID"], "displayName": "Copilot"}},
                "body": {"content": f"<p>{bot_text}</p>"}
            })
            
        raw_data.append({
            "meta": {"id": chat_id, "topic": "Copilot Help"},
            "messages": messages
        })
    return raw_data

# =============================================================================
#  CORE LOGIC: TRANSFORMATION (ETL)
# =============================================================================

def transform_to_modelop_schema(raw_data, agent_id):
    """
    Transforms the nested Azure JSON into the flat ModelOp Standardized format.
    """
    print("  > Transforming data to ModelOp Schema...")
    modelop_dataset = []
    
    for chat in raw_data:
        # Ensure chronological order to pair prompts/responses
        msgs = sorted(chat['messages'], key=lambda x: x.get('createdDateTime', ''))
        
        current_prompt = None
        current_user_id = None
        
        for msg in msgs:
            sender_data = msg.get('from', {}).get('user', {})
            # Handle cases where sender might be 'application' or null
            sender_id = sender_data.get('id') if sender_data else "unknown"
            
            content = clean_html(msg.get('body', {}).get('content', ''))
            
            # LOGIC: If sender is NOT the bot, it's a User Prompt
            if sender_id != agent_id:
                current_prompt = content
                current_user_id = sender_id
            
            # LOGIC: If sender IS the bot, and we have a pending prompt, it's a Response
            elif sender_id == agent_id and current_prompt:
                
                # Create "Ground Truth" for SBERT Similarity Monitor
                # In a real scenario, this might come from a golden dataset.
                ground_truth = content + " (verified)" 

                record = {
                    # --- ModelOp Monitor Requirements ---
                    # 1. The input/output pair
                    "prompt": current_prompt,
                    "response": content,
                    
                    # 2. 'score_column' is the primary target for NLP Monitors 
                    # (Sentiment, Toxicity, PII, Gibberish)
                    "score_column": content,       
                    
                    # 3. 'label_column' is required for Accuracy/Similarity Monitors
                    "label_column": ground_truth,  
                    
                    # 4. 'protected_class' is required for Bias/Fairness Monitors
                    "protected_class_gender": random.choice(["Male", "Female", "Non-Binary"]),

                    # --- Metadata for Dashboard Slicing ---
                    "interaction_id": msg.get('id'),
                    "timestamp": msg.get('createdDateTime'),
                    "session_id": chat['meta']['id'],
                }
                
                modelop_dataset.append(record)
                current_prompt = None # Reset for next turn

    return modelop_dataset

# =============================================================================
#  MAIN EXECUTION
# =============================================================================

def main():
    print("\n--- ModelOp Partner ETL Script Started ---")
    
    if USE_MOCKS:
        print("[MODE] MOCK SIMULATION ACTIVE")
        print("       Generating synthetic data with fault injection.")
        agent_id = MOCK_CONFIG["COPILOT_AGENT_ID"]
        raw_data = generate_mock_data()
    else:
        print("[MODE] REAL AZURE CONNECTION ACTIVE")
        print("       Connecting to Microsoft Graph API.")
        # Note: In real Azure calls, the Bot ID needs to be identified. 
        # Usually, Copilot messages have specific 'application' types, but for this script
        # we will assume the partner knows the Object ID of their Bot.
        # For now, we auto-detect or use a placeholder.
        agent_id = "THE_OBJECT_ID_OF_YOUR_BOT_IN_AZURE_AD" 
        raw_data = fetch_real_azure_data()

    if not raw_data:
        print("No data found. Exiting.")
        return

    # Transform
    clean_dataset = transform_to_modelop_schema(raw_data, agent_id)
    
    # Load (Save to file)
    output_file = "modelop_llm_partner_data.json"
    with open(output_file, "w") as f:
        json.dump(clean_dataset, f, indent=2)
        
    print(f"\n--- SUCCESS ---")
    print(f"Generated {len(clean_dataset)} interaction records.")
    print(f"File saved to: {output_file}")
    print("\nNEXT STEPS (Refer to Partner Demo Lab Guide):")
    print("1. Log in to https://partner-demo.modelop.center/")
    print("2. Navigate to 'Inventory' -> 'Add Use Case' (Stage 1)")
    print("3. Add a Model Implementation (Stage 3)")
    print(f"4. Upload '{output_file}' as your 'Baseline Data' or 'Comparator Data'")

if __name__ == "__main__":
    main()