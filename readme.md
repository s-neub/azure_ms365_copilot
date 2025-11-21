# 🤖 ModelOp Center: Enterprise Chatbot Data Generator

Welcome! This tool creates realistic conversation data to help you test drive **ModelOp Center**.

It simulates a **Corporate AI Assistant** (like an IT Helpdesk bot) handling questions about VPNs, passwords, and benefits. It generates the three things ModelOp needs to see:
1.  **The Prompt:** A realistic employee question (e.g., *"How do I reset my MFA?"*).
2.  **The Response:** The AI's answer.
3.  **The Ground Truth:** The "correct" policy answer (used to test accuracy).


---

### 🧠 The Philosophy of the Baseline: "Defining Normal"
*Read this before generating data!*

In ModelOp Center, the **Baseline** dataset serves as your "Gold Standard." It represents your AI model operating exactly as intended—safe, accurate, and helpful.

**Why is this crucial?**
Governance monitors don't just look for "bad" things; they look for *deviations* from the norm. To effectively detect a problem later (in the Comparator dataset), you must first define what "No Problem" looks like.

#### 📉 Recommended Settings for a Solid Baseline
To generate a clean baseline that produces **zero alerts** (an "All Green" dashboard), you should configure the `simulation` section of your `config.yaml` with the values below. This creates a "Business as Usual" day at the office.

```yaml
# config.yaml (Baseline Configuration)
simulation:
    rates:
        # Philosophy: Strict Compliance. 
        # In a perfect world, users never type SSNs into chat. 
        pii: 0.0

        # Philosophy: Professional Standards.
        # Corporate bots must remain polite, even when users are not.
        toxicity: 0.0

        # Philosophy: Realistic Tolerance.
        # IT Helpdesks naturally involve frustration ("My printer is broken").
        # A 5% background level establishes "normal" frustration, so monitors 
        # only alert on major spikes in anger (e.g., 20%+).
        negative_sentiment: 0.05
```
---

### ☕ The "Coffee Break" Factor
**Read this first!** Running Artificial Intelligence on a standard laptop is hard work.
* **Speed:** Expect each conversation to take **1–5 minutes** to generate.
* **Total Time:** Generating the full dataset (25 records) can take **up to an hour**.
* **Pro Tip:** Start the script, grab a coffee, and let it do the heavy lifting in the background.

---

### 🛠️ Step 1: Get the "Brains" (Ollama)
*Skip this step if you are connecting to real Azure data (Phase 3).*

To make the text look real, this script uses a local AI model called **Ollama**.
1.  **Download It:** Go to [ollama.com](https://ollama.com) and install it.
2.  **Get the Model:** Open your terminal (or command prompt) and type:
    ```bash
    ollama pull qwen2.5
    ```

---

### 📦 Step 2: Install the Tools
**⚠️ Using OneDrive, Google Drive, or Box?**
If this folder is syncing to the cloud, you **MUST PAUSE SYNCING** for 1 hour before running the commands below. (Otherwise, the install will fail with an "Access Denied" error).

**Installation:**
Open your terminal in this folder and run these two commands:

1.  **Install the Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Download the grammar tool:**
    ```bash
    python -m spacy download en_core_web_sm
    ```

*(You can resume cloud syncing once these are done).*

---

### ⚙️ Step 3: Choose Your Adventure (Configuration)
This script supports three distinct testing phases. Open `config.yaml` to choose your path.

#### 🟢 Phase 1: "Kick the Tires" (Fastest)
*Goal: See the dashboard light up immediately without waiting for data generation.*
1.  We have included pre-generated files in the `pregenerated_data/` folder.
2.  In `config.yaml`, set `baseline_source_file` to point to one of these existing files.
3.  Run the script. It will instantly copy these files to `baseline_data.json` and `comparator_data.json` without running the AI.
4.  **Upload** these two files to the Partner Demo Lab immediately.

#### 🟡 Phase 2: Custom Simulation
*Goal: Test specific scenarios (e.g., "What if my bot is rude?" or "What if it leaks PII?").*
1.  In `config.yaml`:
    * Set `use_real_azure: false`.
    * Adjust `rates` (e.g., increase `toxicity` to 0.5 to see more red alerts).
    * Edit the `topics` list to match your industry (e.g., change "VPN" to "Mortgage Rates").
2.  **Run the script.** It will generate fresh data matching your criteria.
3.  **Upload** the new `comparator_data.json` to see how the monitors react to your specific data.

#### 🔴 Phase 3: Real World Data
*Goal: Connect to your actual Microsoft 365 Copilot to audit real user interactions.*
1.  In `config.yaml`:
    * Set `use_real_azure: true`.
    * Fill in your `azure` credentials (Tenant ID, Client ID, Secret).
2.  **Run the script.** It will connect to your Azure tenant, download real chat logs, and format them for ModelOp.
3.  **Upload** the resulting file to audit your live environment.

---

### 🚀 Step 4: Let's Run It!
In your terminal, run:
    ```bash
    python azure_copilot_etl_advanced.py
    ```

**What happens next?**

1. **The Progress Bar:** You will see a status bar showing the estimated time left (if generating data).
2. **The Auto-Save:** When finished, the script automatically updates `baseline_data.json` and `comparator_data.json` based on your `config.yaml` settings.

---

### 📤 Step 5: Upload to ModelOp

Now you are ready for the Demo Lab!

1. Log in to the **Partner Demo Lab**.
2. Follow your Companion Guide to **Stage 3: Add Model Implementation**.
3. When asked for Assets, upload the `comparator_data.json` file generated by the script.