# Getting Data Ready for ModelOp Center

Welcome! This tool helps you create a dataset to test out **ModelOp Center**. 

[cite_start]It generates chat logs (like you’d see from a customer service bot or Microsoft Copilot) and formats them perfectly for the **Partner Demo Lab**[cite: 704, 926].

You can use this tool in two ways:
1.  [cite_start]**The Easy Way (Simulation):** Create fake data with some "intentional mistakes" (like secrets leaking or rude robot responses) so you can see the ModelOp dashboard catch them[cite: 110, 580].
2.  **The Real Deal:** Connect to your own Microsoft Azure account to pull actual chat history.

---

### Step 1: The Setup
Before you run the script, you need to grab two free software libraries. Open your terminal (or command prompt) and run this command:

```bash
pip install -r requirements.txt