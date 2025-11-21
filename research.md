

# **Architecting the Bridge: Enterprise AI Governance, Microsoft Graph, and ModelOp Center**

## **1\. The Strategic Imperative of AI Governance in the Azure Cloud**

The contemporary enterprise landscape is undergoing a seismic shift, driven principally by the rapid democratization of Artificial Intelligence (AI) and the proliferation of Large Language Models (LLMs). For organizations entrenched in the Microsoft Azure ecosystem, this transformation is not merely a matter of adopting new software but represents a fundamental reimagining of how business value is created, captured, and delivered. The introduction of "Shadow AI"—the unsanctioned or loosely governed use of generative tools—alongside sanctioned, enterprise-grade deployments of Microsoft Copilot Studio and Azure OpenAI, has created a complex duality. On one hand, there is the promise of unprecedented agility and productivity; on the other, a sprawling, opaque attack surface that traditional IT governance frameworks struggle to encompass.

ModelOp Center (MOC) positions itself as the critical "Application Gold Source" (AGS) 1 in this chaotic environment, offering a centralized governance plane to manage the lifecycle of these probabilistic systems. However, the value of ModelOp Center is directly proportional to its visibility. To govern effectively, MOC must "see" the interactions occurring between human employees and AI agents. This report details the architectural and procedural blueprint for developing a Proof of Concept (POC) repository designed to extract, normalize, and ingest chat history data from the Microsoft/Azure ecosystem using the Microsoft Graph API. By feeding this data into ModelOp’s Out-of-the-Box (OOTB) LLM Standardized Test FULL, enterprise administrators can transition from passive observation to active, data-driven governance.

### **1.1. The "Agility Layer" and the Rise of Citizen Development**

To understand the necessity of this POC, one must first appreciate the environment from which the data originates. The Microsoft Power Platform has evolved into what industry analysts describe as a core "agility layer" for the enterprise.2 It allows organizations to bypass the rigid, multi-year development cycles of traditional software engineering in favor of rapid, low-code solutions. This layer leverages data and services provided by mission-critical core business systems—such as SAP, Salesforce, or Oracle—and exposes them through intuitive interfaces in Power Apps, Power Automate, and Microsoft Copilot Studio.2

The implication for AI governance is profound. We are no longer dealing solely with models deployed by data science teams in controlled Python environments. We are dealing with "Makers"—business users, citizen developers, and domain experts—who are building custom copilots and deploying them into Microsoft Teams channels.3 These agents interact with sensitive corporate data, make decisions, and generate content. The governance whitepaper explicitly notes that makers can now take advantage of Copilot features to accelerate development, further blurring the lines between human-authored and machine-generated logic.2

Consequently, the "chat history" is not just a log of conversation; it is an audit trail of business decisions. It is the primary artifact required to assess model performance, safety, and alignment with corporate policy. The POC detailed herein is the mechanism to retrieve this artifact.

### **1.2. The Regulatory and Compliance Landscape**

The urgency of this initiative is underscored by the tightening regulatory environment. Frameworks such as the EU AI Act and the NIST AI Risk Management Framework (AI RMF) demand rigorous auditing and traceability of high-risk AI systems. Within the Azure ecosystem, tools like Microsoft Purview are already being integrated to provide data mapping and discovery.2 However, Purview is primarily a compliance tool for *data*, whereas ModelOp Center is a governance tool for *models*.

The intersection of these two domains is where the POC operates. Support tickets from financial institutions (e.g., FINRA) utilizing ModelOp reveal a preoccupation with "Audit Services" and the need to verify that logs are written and services are working.4 This indicates that enterprise customers are not just asking for functionality; they are demanding proof of control. By extracting chat history via the Graph API and subjecting it to ModelOp’s Standardized Test, the enterprise creates a defensible position. They can demonstrate that every interaction with an LLM—whether a sanctioned Azure OpenAI model or a "Shadow" agent built in Power Virtual Agents—is subject to automated evaluation for hallucination, toxicity, and efficacy.

### **1.3. ModelOp Center as the Governance Nexus**

The research material identifies ModelOp Center as the "AGS" (Application Gold Source) 1, a designation that implies it is the single source of truth for model inventory and risk status. The POC is designed to reinforce this status by operationalizing the feedback loop.

In current deployments, we see evidence of complex process definitions (BPMN) used to manage model lifecycle events, such as "ModelChangedNotification" 4 or "LLM\_USE\_CASE\_DEPLOYMENT".5 These workflows orchestrate the movement of a model from development to production. However, without the *actual* conversational data, these workflows are blind to the model's runtime behavior. The POC bridges this gap. It feeds the "LLM Standardized Test FULL" with real-world data, allowing the ModelOp engine to calculate risk scores based on empirical evidence rather than theoretical validation. This alignment enables the creation of dynamic dashboards—referenced in support tickets as "Dashboard Support" where heatmaps show Safety and Performance 6—that reflect the true state of the AI estate.

---

## **2\. Architectural Deep Dive: The Microsoft Ecosystem**

Before a single line of code is written for the POC, the architect must possess a nuanced understanding of the Microsoft Azure and Power Platform architecture. Data extraction is not a simple file download; it is a query against a distributed, secured, and highly complex graph of objects.

### **2.1. The Centrality of Dataverse**

At the heart of the Microsoft business application ecosystem lies **Dataverse**. Formerly known as the Common Data Service (CDS), Dataverse provides the structured data storage, security, and logic for Power Apps and Copilot Studio.2 It is not merely a database; it is a governance engine that enforces role-based access control (RBAC), auditing, and business rules.

When an employee chats with an AI agent in Microsoft Teams, that interaction typically touches multiple substrates. The message itself is stored in the Exchange/Teams infrastructure, but the metadata regarding the agent, its configuration, and potentially the business data it accesses, resides in Dataverse. The whitepaper highlights that Dataverse environments can be "Managed," offering enhanced visibility and control.2 For the POC, this means that the target "Chat History" is effectively a composite entity. The *content* is retrieved via Microsoft Graph (accessing the Exchange/Teams data store), but the *context*—what agent is this? who owns it? is it in a production environment?—is often derived from Dataverse entities.

### **2.2. Environment Strategy and Security Boundaries**

The Microsoft ecosystem is partitioned into "Environments." These can be Sandbox, Production, or Developer environments, and they serve as containers for apps, flows, and data.2 A crucial insight from the administration whitepaper is the existence of "Default" environments versus dedicated environments. Misfired governance often leads to critical assets living in the Default environment, accessible to everyone.

The POC must be environment-aware. It is insufficient to scrape all chats. The extraction logic must be capable of distinguishing between a chat with a "Dev" version of an agent and a "Prod" version. This is complicated by the fact that different environments may have different security policies.

* **IP Firewalls:** Dataverse environments may restrict access to specific IP ranges.3 The machine running the POC extraction script must be whitelisted.  
* **Tenant Restrictions:** Organizations may block cross-tenant connections to prevent data exfiltration.3 If the POC is running in a ModelOp-hosted environment attempting to reach a client's Azure tenant, it must navigate these restrictions, likely requiring a dedicated Service Principal with explicit exemptions.  
* **Continuous Access Evaluation (CAE):** Azure AD (Entra ID) employs CAE to revoke access tokens in real-time upon critical events (e.g., user account disabled, password changed).3 The POC code cannot assume a token is valid for its entire 60-minute lifetime; it must handle 401 Unauthorized challenges gracefully and re-authenticate immediately.

### **2.3. The Identity Fabric: Microsoft Entra ID (Azure AD)**

Identity is the perimeter. All access to the Graph API is mediated by Microsoft Entra ID. The research snippets reveal specific configuration challenges in existing ModelOp deployments related to identity synchronization. Specifically, application.yaml configurations utilize oauth2-group-claim-name: groups to map Azure AD groups to ModelOp roles.1

However, the logs document a critical failure mode: "New AD Group cannot be synced to the app".1 This was traced to an incorrect regex filter (group-authorities-regex-filter). The regex ^ModelOp\_EntAI\_ failed to capture a group named ModelOp\_EntAI\_Model\_Reader because of a subtle mismatch or propagation delay. This lesson is vital for the POC. The extraction tool will rely on Application Permissions (Service Principal), but to map the "User" field in the Standardized Test, it must resolve User IDs to human-readable names. If the POC relies on group membership to filter *which* users' chats to harvest, it is susceptible to the same synchronization delays and regex fragility observed in the support tickets.

**Architectural Decision:** The POC should utilize direct User ID resolution via the Graph API (/users/{id}) rather than relying on potentially stale group claims within the token itself, ensuring the metadata provided to ModelOp is accurate at the moment of extraction.

### **2.4. The Connector Ecosystem and DLP Policies**

Power Platform utilizes "Connectors" to talk to external services. There are over 1,000 connectors, ranging from Salesforce to Twitter (X).3 Governance relies on Data Loss Prevention (DLP) policies that categorize these connectors as "Business," "Non-Business," or "Blocked."

When an LLM Agent is built, it often uses a "Custom Connector" to call the LLM inference endpoint (e.g., Azure OpenAI). The "Chat History" we seek captures the input and output of this connector.

* **Insight:** If the POC attempts to "replay" a chat or validate a model by sending a test prompt, it acts as a client. If strict DLP policies are in place, the POC's service principal might be blocked from invoking the agent if it hasn't been added to the allow-list.  
* **Extraction Implication:** We are primarily *reading* history (Passive), not *invoking* the model (Active). Therefore, the Chat.Read.All permission is the primary requirement. However, if the "Standardized Test" requires *active* probing (sending a prompt to see the response), the architecture becomes significantly more complex, requiring the POC to act as a sanctioned "User" within the Power Platform environment.

---

## **3\. Technical Specification: The Proof of Concept (POC) Design**

The objective of the POC is to demonstrate value by executing the "LLM Standardized Test FULL." To do this, we need data. The following section provides a step-by-step technical specification for building the extraction repository, tailored for the MS/Azure Enterprise Admin user.

### **3.1. Step 1: Microsoft Entra ID App Registration**

The gateway to the Microsoft Graph API is an App Registration in Entra ID. This establishes the identity of the POC extraction tool.

User Action: The Admin must navigate to the Azure Portal \> Entra ID \> App Registrations.  
Configuration Details:

* **Name:** ModelOp\_POC\_Extractor  
* **Account Type:** "Accounts in this organizational directory only (Single tenant)".2 This restricts the blast radius to the specific enterprise tenant.  
* **Redirect URI:** Not required for a daemon/background service.

Authentication Strategy:  
The extraction runs as a background process, not an interactive user session. Therefore, the Client Credentials Grant Flow is mandatory.

* **Credential Type:** While a Client Secret (string) is often used for rapid prototyping, the Power Platform governance whitepaper emphasizes security.2 The "Best Practice" recommendation for the Admin is to upload a **Certificate (public key)**. This prevents secret leakage in code repositories.  
* **Output:** The Admin must record the Application (client) ID and Directory (tenant) ID for the POC configuration.

### **3.2. Step 2: Permission Scoping and Admin Consent**

This is the most sensitive step. Accessing chat history requires high-privilege Application Permissions. The "Principle of Least Privilege" must be balanced against the need for comprehensive data.

| Permission Scope | Type | Necessity | Risk | Mitigation Strategy |
| :---- | :---- | :---- | :---- | :---- |
| Chat.Read.All | Application | **Critical.** Allows reading all 1:1 and Group chats to capture interactions with AI Agents. | High. Exposes private employee conversations. | Use **Resource Specific Consent (RSC)** where possible to limit access to specific chats, or use **Protected APIs** in Graph which require extra validation. |
| ChannelMessage.Read.All | Application | **Critical.** Required if the AI Agent operates in a Team Channel (collaborative mode). | High. Exposes all Team channel data. | Configure the POC to only target specific Team IDs. |
| User.Read.All | Application | **High.** Needed to resolve User GUIDs to Names/Emails for the ModelOp user\_id metadata. | Low/Medium. PII exposure. | Hash user IDs in the output if privacy is a concern (GDPR). |
| Team.ReadBasic.All | Application | **Medium.** Provides context (Team Name) for the conversation. | Low. | None required. |

**Admin Consent:** After adding these permissions, the "Grant admin consent for \[Organization\]" button must be clicked. Without this, the API calls will return 403 Forbidden.

### **3.3. Step 3: The Extraction Logic (The Code)**

The POC repository should utilize Python or Node.js. Python is recommended due to its dominance in the data engineering and AI domains.

#### **3.3.1. Authentication & Token Acquisition**

The script initiates by acquiring a Bearer Token from the Microsoft identity platform.

* **Endpoint:** POST https://login.microsoftonline.com/{tenant\_id}/oauth2/v2.0/token  
* **Payload:** client\_id, scope=https://graph.microsoft.com/.default, client\_credential, grant\_type=client\_credentials.  
* **Error Handling:** The script must handle connection timeouts or DNS failures, akin to the "Could not open JDBC Connection" errors observed in the support logs.4 These infrastructure-level failures should trigger a retry with exponential backoff.

#### **3.3.2. Target Identification (Finding the Agent)**

We do not want *human-to-human* chat history. We want *human-to-AI* history. The POC must identify the specific User ID or App ID of the AI Agent.

* **Lookup:** GET https://graph.microsoft.com/v1.0/users?$filter=startswith(displayName,'Copilot')  
* **Logic:** Store the id (GUID) of the target bot. Let's call this AGENT\_GUID.

#### **3.3.3. Retrieving Chat Threads**

The most efficient way to retrieve relevant chats without scanning the entire organization is to iterate through a target list of "Test Users" or "Pilot Group" members, or to use the Cross-Tenant/Cross-User endpoints if Chat.Read.All is fully enabled.

* **Endpoint:** GET https://graph.microsoft.com/v1.0/chats?$filter=participants/any(p:p/upn eq '{user\_upn}')  
* **Filtering:** For each chat returned, check if the AGENT\_GUID is a participant. If yes, process the chat. If no, discard.

#### **3.3.4. Message Extraction & Pagination**

Once a relevant chatId is found, the messages must be harvested.

* **Endpoint:** GET https://graph.microsoft.com/v1.0/chats/{chatId}/messages?$top=50&$orderby=createdDateTime desc  
* **Pagination:** The Graph API utilizes OData pagination. If more than 50 messages exist, the response includes an @odata.nextLink. The POC **must** implement a while loop to traverse these links until null. Failing to do so creates an incomplete dataset, compromising the validity of the "Standardized Test."

**Data Payload Structure:**

JSON

{  
    "id": "12345",  
    "createdDateTime": "2025-11-17T10:00:00Z",  
    "from": { "user": { "id": "USER\_GUID", "displayName": "John Doe" } },  
    "body": { "contentType": "html", "content": "\<div\>What is the PTO policy?\</div\>" },  
    "attachments":  
}

### **3.4. Step 4: Handling "Async" and Orchestration Failures**

The research indicates that the enterprise environment is prone to "Process Orchestration" failures. Support tickets detail numerous instances of "Async" tasks failing or stalling.4

* **Implication for POC:** The extraction script cannot be a synchronous "fire and forget" script. It needs state management. If the script crashes after processing 100 chats, it should resume from chat 101, not restart.  
* **Mechanism:** Implement a "Cursor" file (JSON) that saves the last\_processed\_chat\_id and last\_sync\_timestamp. This mimics the robustness required in the "Jira Notification" polling logic referenced in the logs.1

---

## **4\. Data Transformation: Mapping to ModelOp Schema**

The raw data from Microsoft Graph is unstructured JSON, often laden with HTML tags. To demonstrate value to ModelOp Center, this data must be transformed into the strict schema required for the **LLM Standardized Test FULL**.

### **4.1. Sanitization and Parsing**

The body.content field in Graph API responses typically contains HTML (e.g., \<p\>Hello\</p\>).

* **Requirement:** The POC must implement an HTML sanitizer (e.g., Python's BeautifulSoup).  
* **Logic:** Strip all tags. Convert HTML entities (&) to text.  
* **Edge Case \- Adaptive Cards:** Azure Bots often reply with "Adaptive Cards" (rich UI elements). In these cases, body.content might be empty or contain a placeholder. The real data lies in the attachments array. The POC must parse the JSON content of the attachment to extract the text or value fields displayed to the user. Ignoring this will result in empty "Response" fields, leading to false negatives in the test.

### **4.2. Reconstructing the "Turn"**

The ModelOp Standardized Test expects pairs of (Prompt, Response). The Graph API provides a flat list of messages.

* **Algorithm:**  
  1. Sort messages by createdDateTime.  
  2. Iterate through the list.  
  3. If from.user.id\!= AGENT\_GUID, treat as **Prompt**.  
  4. If the *next* message has from.user.id \== AGENT\_GUID, treat as **Response**.  
  5. **Handling Concurrency:** If the user sends three messages in a row before the bot replies, concatenate the user messages into a single Prompt block. This captures the full context provided to the LLM.

### **4.3. Schema Mapping Table**

The following table defines the transformation rules required to populate the ModelOp readme.md requirements.

| ModelOp Field | Source (Graph API) | Transformation Logic |
| :---- | :---- | :---- |
| prompt | message.body.content (User) | Sanitize HTML. Concatenate multi-line inputs. |
| response | message.body.content (Agent) | Sanitize HTML. Parse Adaptive Cards from attachments. |
| context | chat.topic or team.displayName | Use the chat title or Team name to categorize the interaction domain. |
| timestamp | message.createdDateTime | Convert ISO-8601 to the specific ModelOp datetime format. |
| user\_id | from.user.id | **Anonymization Required:** Hash this value to comply with EU AI Act/GDPR while maintaining unique identification for analysis. |
| session\_id | chat.id | Maps the interaction to a specific session/thread. |

### **4.4. Integrating Metadata for "Gold Source" Tracking**

Support logs highlight the importance of metadata keys like "Datasets" and "Risk" in Model Lifecycle (MLC) definitions.4 The POC should enrich the extracted data with external metadata where possible.

* **Example:** If the chat occurred in a Team named "Finance \- Risk Model Dev", the POC should inject a department="Finance" tag into the ModelOp dataset. This enables the faceted dashboarding (Heatmaps by Business Unit) requested in snippet.6

---

## **5\. Integration Challenges & Real-World Troubleshooting**

Deploying this POC in an enterprise environment is rarely seamless. Analysis of the provided support tickets and configuration files reveals several recurring friction points that the Admin must be prepared to navigate.

### **5.1. The "Regex Filter" Pitfall in Spring Boot**

A major integration challenge documented in the logs involves the synchronization of Azure AD groups into ModelOp via Spring Boot. Specifically, the property group-authorities-regex-filter in application.yaml is prone to misconfiguration.1

* **The Issue:** A user defined a filter ^ModelOp\_EntAI\_ but found that a group ModelOp\_EntAI\_Model\_Reader was not syncing. The root cause was likely a subtle mismatch in the regex string (e.g., missing a wildcard .\* at the end) or the "Opaque Token" introspection URI configuration.1  
* **Relevance to POC:** When the POC runs, it will likely need to assign "Owners" to the extracted datasets in ModelOp. If the POC utilizes the same AD groups for permissioning, it will inherit these sync issues. The Admin must verify that the service account running the POC has its group memberships correctly exposed in the token claims, or the data ingestion into ModelOp will fail with a 403 Forbidden.

### **5.2. Network Connectivity and Timeouts**

The support logs are replete with JDBC Connection errors and 404 Not Found responses for notification endpoints.4 These often indicate ephemeral network partitions or service discovery failures in the microservices mesh (e.g., document-service failing to get an OAuth token 6).

* **Mitigation:** The POC must assume the network is unreliable. HTTP requests to Graph API should be wrapped in a "Retry Policy" (e.g., utilizing the tenacity library in Python). Furthermore, the extraction process should log the specific "Snapshot ID" or "Request ID" of failed calls, as requested by engineering in the support threads 6, to facilitate root cause analysis.

### **5.3. Dashboarding and "Model Promotion" Logic**

A significant portion of the research data concerns "Dashboard Support" and the "Model Promotion" workflow.6 Users expect the dashboard to reflect real-time status.

* **Challenge:** The POC extraction is likely a batch process (e.g., running nightly). This creates a latency between the "Chat" happening and it appearing in the ModelOp "Risk Dashboard."  
* **Managing Expectations:** The Admin must configure the POC frequency to align with the "Bimonthly CS Status" or "Weekly" reporting cadences mentioned in the transition documents.8 Real-time streaming from Graph API (using Webhooks) is possible but significantly increases complexity; a batch approach is recommended for the initial POC.

---

## **6\. Operationalizing the "LLM Standardized Test FULL"**

The ultimate goal is not just data extraction, but value demonstration. Once the JSON/CSV file is generated by the POC, it is uploaded to ModelOp Center. This triggers the "LLM Standardized Test FULL."

### **6.1. The Testing Methodology**

The "FULL" test likely encompasses several dimensions, which the extracted data feeds:

1. **Hallucination Detection:** Comparing the Agent's response against a ground\_truth (if available) or using a reference-free evaluation metric.  
2. **Toxicity Scanning:** analyzing the prompt and response for hate speech, PII leakage, or policy violations.  
3. **Topic Adherence:** Using the context field (e.g., Team Name) to determine if the Agent stayed on topic.

### **6.2. Workflow Integration**

According to the "ModelOp AI Lifecycle Management" workflow 7, the process flow is:

1. **View Model Card:** The extracted data populates the "Model Card" in MOC.  
2. **Route for AI COE Review:** The automated test results (Pass/Fail) trigger a notification to the AI Center of Excellence (COE).  
3. **Decision Card Generation:** Based on the test results, a decision (Approve/Reject) is generated.

The POC demonstrates value by automating the first step. Instead of a data scientist manually uploading a CSV of test prompts, the POC continuously populates the test registry with *actual* production traffic. This allows the AI COE to review *real* incidents rather than synthetic benchmarks.

### **6.3. Future-Proofing with Sentinel and Purview**

Finally, the governance whitepaper highlights the integration of **Microsoft Sentinel** for threat detection and **Purview** for data auditing.2

* **Advanced POC Feature:** A mature POC could cross-reference the extracted chat logs with Sentinel alerts. If Sentinel detected a "Mass Data Exfiltration" event, ModelOp could automatically trigger a "Model Risk" escalation workflow.4 This integration effectively closes the loop between Security Operations (SecOps) and Model Operations (ModelOps).

## **7\. Conclusion**

The development of a POC to extract chat history from the Microsoft Azure ecosystem via the Graph API is a foundational step in establishing a mature AI governance capability. It transforms ModelOp Center from a static registry into a dynamic, observant control plane.

By navigating the complexities of Microsoft Entra ID authentication, implementing granular Graph API queries, and rigorously mapping unstructured conversation data to the ModelOp Standardized Test schema, the Enterprise Admin can unlock visibility into the "Agility Layer" of the organization. This process not only satisfies the immediate need for testing and validation but also positions the enterprise to meet emerging regulatory requirements with confidence. The artifacts, logs, and whitepapers analyzed in this report confirm that while the integration is complex—fraught with potential regex pitfalls, connection timeouts, and security boundaries—the path to execution is clear, documented, and strategically vital.

#### **Works cited**

1. All Support Tickets Opened Since 1 Jan 2025 (JIRA).csv, [https://drive.google.com/open?id=1nlp\_pzwCC2Z6whESR7HZtZoMGyLfVJWc](https://drive.google.com/open?id=1nlp_pzwCC2Z6whESR7HZtZoMGyLfVJWc)  
2. Power-Platform-Admin-and-Governing-Whitepaper.pdf, [https://drive.google.com/open?id=1IIrP7qPW5R-u3O6jP4YynqXOrHRMn\_e\_](https://drive.google.com/open?id=1IIrP7qPW5R-u3O6jP4YynqXOrHRMn_e_)  
3. Power-Platform-Admin-and-Governing-Whitepaper.pdf, [https://drive.google.com/open?id=1tl2JT2wCXhhyJN\_w9oLc3tUoXr1p5OkT](https://drive.google.com/open?id=1tl2JT2wCXhhyJN_w9oLc3tUoXr1p5OkT)  
4. All Support Tickets Opened Since 1 Jan 2025 (JIRA) (1).csv, [https://drive.google.com/open?id=1l-YYsCyu3ErziPQ-Lt9BI0wwd\_SNPnkZ](https://drive.google.com/open?id=1l-YYsCyu3ErziPQ-Lt9BI0wwd_SNPnkZ)  
5. All Support Tickets Opened Since 1 Jan 2025 (JIRA) (1).csv, [https://drive.google.com/open?id=1nByNs6fFxKlZZmHLOZtG4I4Tun5Qgv9W](https://drive.google.com/open?id=1nByNs6fFxKlZZmHLOZtG4I4Tun5Qgv9W)  
6. rovo\_analysis\_20251111.csv, [https://drive.google.com/open?id=1f\_AAtoHiMiPlmfd-paDaMQeBZih5v-RG](https://drive.google.com/open?id=1f_AAtoHiMiPlmfd-paDaMQeBZih5v-RG)  
7. Wellstar\_ModelOp AI Lifecycle Management\_11Nov2025.pptx, [https://drive.google.com/open?id=1\_aEH9Sy2TFECZpGoHTkvDhXiTaCONZ1Y](https://drive.google.com/open?id=1_aEH9Sy2TFECZpGoHTkvDhXiTaCONZ1Y)  
8. CS\_Transition\_CM\_20250317, [https://drive.google.com/open?id=1fRw2E2K7oSYHwK5vRE0xOijeMSg\_hczwizmH61D1vWU](https://drive.google.com/open?id=1fRw2E2K7oSYHwK5vRE0xOijeMSg_hczwizmH61D1vWU)