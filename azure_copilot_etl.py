"""
ModelOp Partner Connector: Azure MOC Data Bridge
================================================
CONTEXT: ModelOp Partner Demo Lab
OUTPUT: JSON dataset compatible with ModelOp Standardized Tests.

DESCRIPTION:
    This script acts as a Data Pipeline for ModelOp Center.
    
    PIPELINE STAGES:
    1. ACQUISITION (Convergence Point):
       - Fetches Real Azure Data OR Generates Base Synthetic Data.
       - CRITICAL: All data leaves this stage wrapped in the standard 
         Microsoft Graph API JSON Schema (nested 'body', 'from', etc.).
       
    2. RED TEAM LAYER (Post-Convergence):
       - Acting on the standardized stream, this layer applies:
         a. Data Expansion (Adding records based on file style)
         b. Defect Injection (Rewriting for PII, Toxicity, Sentiment)
         c. Adversarial Injection (Adding pure attack records)
         d. Reference Answer Generation (Optional factual grounding)

    3. ETL & FLATTENING:
       - Unwraps the Azure Schema into the flat ModelOp Schema for CSV/JSON output.

CONFIGURATION:
    Managed in 'config.yaml'.
"""

import json
import random
import uuid
import time
import sys
import re
import os
import shutil
import requests
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional

# Third-party imports
import spacy
from faker import Faker
import ollama 
from tqdm import tqdm 

# =============================================================================
#  CONFIGURATION & SETUP
# =============================================================================

CONFIG_FILE = 'config.yaml'

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE):
        print(f"[!] ERROR: {CONFIG_FILE} not found.")
        sys.exit(1)
    with open(CONFIG_FILE, 'r') as f: #type: ignore
        return yaml.safe_load(f)

CONF = load_config()
fake = Faker()

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli.download import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# =============================================================================
#  HELPER: OLLAMA INTERFACE
# =============================================================================

def check_ollama_status() -> bool:
    try:
        ollama.list()
        return True
    except Exception:
        return False

def generate_ollama_json(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Generic wrapper for Ollama JSON generation."""
    try:
        response = ollama.chat(model=CONF['mode']['ollama_model'], messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ], format='json')
        return json.loads(response['message']['content'])
    except Exception as e:
        return {"prompt": "Error", "response": f"Generation failed: {e}", "reference_answer": "N/A"}

def get_spacy_context() -> Dict[str, str]:
    raw_name = fake.name()
    raw_dept = fake.job()
    doc = nlp(f"{raw_name} works in {raw_dept}.")
    person = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    return {"employee_name": person[0] if person else raw_name, "department": raw_dept}

def wrap_in_azure_schema(prompt_text: str, response_text: str, is_adversarial: bool = False, technique: str = "N/A") -> Dict[str, Any]:
    """
    Standardizes ANY data (Synthetic) into the Microsoft Graph API format.
    """
    user_id = str(uuid.uuid4())
    bot_id = CONF['simulation']['copilot_agent_id']
    
    # Construct User Message Object
    user_msg = {
        "id": str(uuid.uuid4()),
        "createdDateTime": datetime.now().isoformat() + "Z",
        "from": {"user": {"id": user_id, "displayName": "Employee"}},
        "body": {"contentType": "html", "content": f"<div>{prompt_text}</div>"}
    }

    # Construct Bot Message Object
    bot_msg = {
        "id": str(uuid.uuid4()),
        "createdDateTime": (datetime.now() + timedelta(seconds=2)).isoformat() + "Z",
        "from": {"user": {"id": bot_id, "displayName": "Copilot"}},
        "body": {"contentType": "html", "content": f"<div>{response_text}</div>"}
    }

    return {
        "interaction_id": str(uuid.uuid4()),
        "user_message": user_msg,
        "bot_message": bot_msg,
        "_pipeline_meta": {
            "is_adversarial": is_adversarial,
            "adversarial_technique": technique,
            "reference_answer": "N/A" 
        }
    }

# =============================================================================
#  PHASE 1: DATA ACQUISITION
# =============================================================================

def get_azure_access_token() -> str:
    """Authenticates with Azure AD and retrieves a Bearer token."""
    print("  > Authenticating with Azure Active Directory...")
    creds = CONF['azure']
    url = f"https://login.microsoftonline.com/{creds['tenant_id']}/oauth2/v2.0/token"
    
    payload = {
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        print(f"  [ERROR] Azure Auth Failed. Check config.yaml credentials. Details: {e}")
        return ""

def fetch_real_azure_stream() -> List[Dict[str, Any]]:
    """
    Connects to Microsoft Graph API and fetches real chat threads.
    Wraps them in the internal pipeline structure for Red Teaming.
    """
    token = get_azure_access_token()
    if not token: return []
    
    headers = {'Authorization': f'Bearer {token}'}
    bot_id = CONF['azure'].get("bot_user_id")
    
    print("  > Fetching Chat Threads from Microsoft Graph...")
    # Note: In production, filter by topic or date would happen here
    chats_url = "https://graph.microsoft.com/v1.0/chats"
    
    try:
        response = requests.get(chats_url, headers=headers)
        if response.status_code != 200:
            print(f"  [ERROR] Graph API Error: {response.text}")
            return []
        chats = response.json().get('value', [])
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")
        return []

    print(f"  > Processing {len(chats)} threads...")
    stream = []
    
    # Process threads to find User -> Bot turn pairs
    for chat in tqdm(chats[:20], desc="Fetching Messages", unit="chat"):
        chat_id = chat['id']
        msgs_url = f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages?$top=50"
        
        try:
            msg_resp = requests.get(msgs_url, headers=headers)
            if msg_resp.status_code == 200:
                messages = msg_resp.json().get('value', [])
                # Sort by time to reconstruct flow
                messages.sort(key=lambda x: x.get('createdDateTime', ''))
                
                current_user_msg = None
                
                for msg in messages:
                    sender_id = msg.get('from', {}).get('user', {}).get('id')
                    
                    # Logic: Capture User message, wait for Bot response
                    if sender_id != bot_id:
                        current_user_msg = msg
                    elif sender_id == bot_id and current_user_msg:
                        # We found a pair! Package it for the pipeline.
                        interaction = {
                            "interaction_id": chat_id,
                            "user_message": current_user_msg,
                            "bot_message": msg,
                            "_pipeline_meta": {
                                "is_adversarial": False, # Assume real data is clean initially
                                "adversarial_technique": "N/A",
                                "reference_answer": "N/A"
                            }
                        }
                        stream.append(interaction)
                        current_user_msg = None # Reset
                        
        except Exception:
            continue
            
    return stream

def generate_base_synthetic_stream() -> List[Dict[str, Any]]:
    count = CONF['simulation'].get('num_base_records', 5)
    topics = CONF['simulation']['topics']
    prompt_sys = CONF['prompts']['base_system_instruction']
    
    print(f"  > Generating {count} Base Synthetic Records...")
    stream = []
    for _ in tqdm(range(count), desc="Base Gen", unit="rec"):
        topic = random.choice(topics)
        ctx = get_spacy_context()
        user_input = (f"Context: Employee {ctx['employee_name']} in {ctx['department']}.\nTopic: {topic}.\n"
                      "Generate a standard employee question and a helpful chatbot response.")
        data = generate_ollama_json(prompt_sys, user_input)
        wrapped_record = wrap_in_azure_schema(data.get('prompt', ''), data.get('response', ''))
        stream.append(wrapped_record)
    return stream

# =============================================================================
#  PHASE 2: RED TEAM LAYER
# =============================================================================

def clean_html(raw_html: str) -> str:
    return re.sub('<.*?>', '', raw_html).strip()

def load_expansion_examples(file_path: str) -> List[Dict[str, str]]:
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, 'r') as f:
            raw_data = json.load(f)
        examples = []
        for item in raw_data:
            try:
                u_html = item['user_message']['body']['content']
                b_html = item['bot_message']['body']['content']
                examples.append({"prompt": clean_html(u_html), "response": clean_html(b_html)})
            except KeyError: continue
        return examples
    except Exception: return []

def run_red_team_layer(stream: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rt_conf = CONF['simulation']['red_teaming']
    if not rt_conf['active']: return stream
    
    print("\n[RED TEAM LAYER ACTIVE]")
    
    # 1. EXPANSION
    exp_conf = rt_conf['data_expansion']
    if exp_conf['active']:
        examples = load_expansion_examples(exp_conf['source_file_path'])
        count = exp_conf['num_additional_records']
        print(f"  > Expanding stream with {count} records mimicking {exp_conf['source_file_path']}...")
        sys_prompt = "You are a creative data generator. Generate a new Question/Answer pair that mimics the style of the examples."
        style_str = "\n".join([f"Ex: Q='{e['prompt']}' A='{e['response']}'" for e in examples[:3]])
        
        for _ in tqdm(range(count), desc="Expanding", unit="rec"):
            user_prompt = f"Generate 1 new pair.\n{style_str}"
            data = generate_ollama_json(sys_prompt, user_prompt)
            wrapped = wrap_in_azure_schema(data.get('prompt', ''), data.get('response', ''))
            stream.append(wrapped)

    # 2. DEFECTS
    rates = rt_conf['defect_injection']['rates']
    print("  > Scanning stream for defects...")
    for record in tqdm(stream, desc="Injecting Defects", unit="rec"):
        meta = record['_pipeline_meta']
        if meta['is_adversarial']: continue
        defects = []
        if random.random() < rates['pii']: defects.append("PII")
        if random.random() < rates['toxicity']: defects.append("Toxicity")
        if random.random() < rates['negative_sentiment']: defects.append("Negative Sentiment")
        
        if defects:
            curr_q = clean_html(record['user_message']['body']['content'])
            curr_a = clean_html(record['bot_message']['body']['content'])
            rewrite_prompt = (f"Original Q: {curr_q}\nOriginal A: {curr_a}\nTask: Rewrite to include defects: {', '.join(defects)}.")
            new_data = generate_ollama_json(CONF['prompts']['red_team_instruction'], rewrite_prompt)
            if new_data.get('prompt'): record['user_message']['body']['content'] = f"<div>{new_data['prompt']}</div>"
            if new_data.get('response'): record['bot_message']['body']['content'] = f"<div>{new_data['response']}</div>"

    # 3. ADVERSARIAL
    adv_conf = rt_conf['adversarial_injection']
    if adv_conf['active']:
        current_len = len(stream)
        prop = adv_conf['proportion']
        count = int((prop * current_len) / (1 - prop)) if prop < 1.0 else 5
        print(f"  > Injecting {count} Adversarial Attack records...")
        techniques = adv_conf['techniques']
        for _ in tqdm(range(count), desc="Adversarial Gen", unit="atk"):
            tech = random.choice(techniques)
            atk_prompt = f"Generate a user prompt using technique: '{tech}'. Generate a chatbot response. Return JSON."
            data = generate_ollama_json(CONF['prompts']['red_team_instruction'], atk_prompt)
            wrapped = wrap_in_azure_schema(data.get('prompt', ''), data.get('response', ''), is_adversarial=True, technique=tech)
            stream.append(wrapped)

    # 4. REFERENCE ANSWER
    if rt_conf['generate_reference_answer']:
        print("  > Generating Reference Answers for all records...")
        for record in tqdm(stream, desc="Ref Answers", unit="rec"):
            curr_q = clean_html(record['user_message']['body']['content'])
            ref_prompt = f"Question: {curr_q}\nTask: Generate a factual Reference Answer."
            data = generate_ollama_json(CONF['prompts']['red_team_instruction'], ref_prompt)
            record['_pipeline_meta']['reference_answer'] = data.get('response', 'N/A')

    return stream

# =============================================================================
#  PHASE 3: ETL & FLATTENING
# =============================================================================

def flatten_azure_to_modelop(stream: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flat_dataset = []
    for record in stream:
        raw_q = record['user_message']['body']['content']
        raw_a = record['bot_message']['body']['content']
        meta = record['_pipeline_meta']
        flat_record = {
            "interaction_id": record['interaction_id'],
            "timestamp": record['user_message']['createdDateTime'],
            "session_id": str(uuid.uuid4()),
            "prompt": clean_html(raw_q),
            "response": clean_html(raw_a),
            "reference_answer": meta['reference_answer'],
            "score_column": clean_html(raw_a),
            "label_column": meta['reference_answer'],
            "protected_class_gender": random.choice(["Male", "Female", "Non-Binary"]),
            "is_adversarial": meta['is_adversarial'],
            "adversarial_technique": meta['adversarial_technique']
        }
        flat_dataset.append(flat_record)
    return flat_dataset

# =============================================================================
#  FILE MANAGEMENT
# =============================================================================

def manage_master_files(latest_file_path: str):
    """
    Updates the ROOT level master files (baseline_data.json / comparator_data.json).
    """
    print("\n--- MASTER FILE MANAGEMENT ---")
    files_conf = CONF['files']
    
    # 1. Update Comparator (The "Variable" file)
    master_comp = files_conf.get('master_comparator_file', 'comparator_data.json')
    if files_conf['auto_update_comparator']:
        shutil.copy(latest_file_path, master_comp)
        print(f"  [UPDATE] Root '{master_comp}' overwritten with latest run data.")
    
    # 2. Check/Init Baseline (The "Control" file)
    master_base = files_conf.get('master_baseline_file', 'baseline_data.json')
    if not os.path.exists(master_base):
        shutil.copy(latest_file_path, master_base)
        print(f"  [INIT] Root '{master_base}' was missing. Created using latest data.")
    else:
        print(f"  [SKIP] Root '{master_base}' exists. (Delete it if you want to regenerate it).")

# =============================================================================
#  MAIN
# =============================================================================

def main():
    print("\n--- ModelOp Partner ETL: Enterprise Risk Simulation ---")
    
    if CONF['mode']['use_ai_generation'] and not check_ollama_status():
        print("  [!] Ollama not running. Exiting.")
        return

    # 1. ACQUISITION
    if CONF['mode']['use_real_azure']:
        stream = fetch_real_azure_stream()
    else:
        stream = generate_base_synthetic_stream()
        if not stream: stream = generate_base_synthetic_stream() # Fallback

    # 2. RED TEAM
    stream = run_red_team_layer(stream)

    # 3. EXPORT
    final_dataset = flatten_azure_to_modelop(stream)
    
    output_dir = CONF['files']['output_folder']
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"modelop_llm_data_{timestamp}.json")
    
    with open(out_path, "w") as f:
        json.dump(final_dataset, f, indent=2)
        
    print(f"\n--- PIPELINE COMPLETE ---")
    print(f"  Total Records: {len(final_dataset)}")
    print(f"  Adversarial Count: {len([x for x in final_dataset if x['is_adversarial']])}")
    print(f"  Archive Saved: {out_path}")

    # 4. UPDATE MASTER FILES
    manage_master_files(out_path)

if __name__ == "__main__":
    main()