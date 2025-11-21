<head></head>

Welcome to the **ModelOp Partner Demo Lab**! This "Quick Start" helps bridge the gap between the Microsoft Azure AI ecosystem and ModelOp Center's governance capabilities.

### **Why this matters to your customers**

Your enterprise clients are rapidly deploying Microsoft AI tools, but their GRC (Governance, Risk, and Compliance) teams are flying blind. They are asking questions you can now help answer:

1. **Microsoft 365 Copilot (The "Shadow AI" Risk):**

    - *The Fear:* "Employees are pasting sensitive project data into Copilot to write summaries. How do we know if PII is leaking into the model context?"
    - *The Solution:* Use this tool's **Real Data Mode** to ingest actual Copilot chat logs and run ModelOp's PII Monitor to flag violations instantly.
2. **Azure OpenAI Custom Bots (The "Brand Risk"):**

    - *The Fear:* "We built a customer support bot on GPT-4. What if it starts giving rude or toxic answers to our VIP clients?"
    - *The Solution:* Use this tool's **Simulation Mode** to generate "toxic" test cases and demonstrate how ModelOp's Toxicity Monitor catches bad behavior *before* it reaches a customer.
3. **Power Virtual Agents (The "Accuracy" Risk):**

    - *The Fear:* "Our HR bot is answering questions about 401k matching. If it hallucinates a wrong policy, we could be liable."
    - *The Solution:* This tool generates "Ground Truth" reference data alongside the bot's answers, allowing ModelOp's Accuracy Monitor to mathematically prove if the bot is hallucinating.

### **How to use this tool**

This script is designed for every stage of your prospect's journey, now featuring a new **"Story Mode"** for instant demos:

1. **Story Mode (Fastest):** Don't have time to install LLMs? Run the `generate_demo_data.py` script. It instantly creates a "Day 1 / Day 2 / Day 3" folder structure with pre-cooked data. Drag and drop these files to show ModelOp catching PII leaks and attacks over time.
2. **Simulate Data (Deep Dive):** Use `azure_copilot_etl.py` with local AI (Ollama) to generate fresh, randomized conversations. You control the "toxicity" dial in `config.yaml` to make the dashboard light up exactly how you want.
3. **Connect Real Data (Production):** By toggling a single flag in `config.yaml`, connect to a customer's *actual* Azure Tenant to audit their live Copilot usage.

**Quick Start Steps:**

**Option A: The 30-Second Demo (No AI Required)**

1. Run `python generate_demo_data.py`.
2. Open the new `phase_1_lite_demo/` folder.
3. Upload the **Baseline** file, then the **Day 1**, **Day 2**, and **Day 3** snapshots to ModelOp Center to tell a risk story.

**Option B: Full Simulation**

1. **Install the "Brains":** Install [Ollama](https://ollama.com/ "https://ollama.com/") and pull the model (`ollama pull qwen2.5`).
2. **Configure:** Edit `config.yaml` to set your desired defect rates (e.g., `toxicity: 0.5`).
3. **Run:** `python azure_copilot_etl.py`.
4. **Upload:** The script updates `generated_chats/comparator_data.json` for you to upload.

Full instructions are in the **README.md**.