### **AAMP Database Relationship Overview**
                         ┌─────────────────┐
                         │    COLLEGES     │
                         │                 │
                         │ id              │
                         │ name            │
                         │ enrichment data │
                         └────────┬────────┘
                                  │
                     ┌────────────┴────────────┐
                     │                         │
                     ▼                         ▼
              ┌─────────────┐          ┌─────────────┐
              │    LEADS    │          │  CAMPAIGNS  │
              │             │          │             │
              │ college_id  │          │ college_id  │
              │ qualification│         │ status      │
              │ lead_score  │          │ message     │
              │ priority    │          │ channel     │
              └─────────────┘          └──────┬──────┘
                                               │
                         ┌─────────────────────┼─────────────────────┐
                         │                     │                     │
                         ▼                     ▼                     ▼
                ┌─────────────────┐   ┌─────────────────┐   ┌────────────────┐
                │ CONVERSATION    │   │ STATUS HISTORY  │   │ RESPONSE       │
                │ MESSAGES        │   │                 │   │ ACTIONS        │
                └─────────────────┘   └─────────────────┘   └───────┬────────┘
                                                                     │
                                                        ┌────────────┴──────────┐
                                                        │                       │
                                                        ▼                       ▼
                                                ┌──────────────┐       ┌──────────────┐
                                                │   MEETINGS   │       │    CALLS     │
                                                └──────────────┘       └──────────────┘
### **Importance of Foreign Key in DB Tables Creation?**

- A foreign key connects one table to another table.

- Think of it as:

- "This value belongs to a record in another table."

### **AAMP project, the key files involved in creating/designing the database tables**
1. backend/models/
2. backend/config/settings.py
3. backend/database/
4. backend/alembic/versions/
5. backend/alembic/env.py


### **Auto Campaign Flow**

## The proper 4 lifecycle paths

### Path 1 — Approval Pending
✓ Qualified Lead
✓ Campaign Strategy
✓ Personalization
🔵 Human Approval
○ Email Sent
○ Waiting for College Response
○ Follow-up #1
○ Follow-up #2
○ Final Response Check
○ Campaign Completed

### Path 2 — Email sent / no response

This is the same lifecycle path, progressing through stages:

✓ Human Approval
✓ Email Sent
🔵 Waiting for College Response
○ Follow-up #1
○ Follow-up #2
○ Final Response Check
○ Campaign Completed


Then after Follow-up #1:

✓ Email Sent
✓ Waiting for College Response
✓ Follow-up #1
🔵 Follow-up #2
○ Final Response Check
○ Campaign Completed

Then after Follow-up #2:

✓ Email Sent
✓ Follow-up #1
✓ Follow-up #2
🔵 Final Response Check
○ Campaign Completed

### Path 3 — Response received

✓ Email Sent
✓ Response Received
✓ Response Classified
🔵 Human Action Required
○ Campaign Completed

### Path 4 — Opted out

✓ Email Sent
✓ Response Received
✓ Response Classified
🛑 Campaign Opted Out

### **Current AAMP DB architecture**

Campaign
│
├── campaigns
│     ├── current status
│     ├── response_category
│     ├── follow-up state
│     └── timestamps
│
├── campaign_status_history
│     └── campaign lifecycle history
│
├── conversation_messages
│     └── ALL inbound + outbound communication
│
└── campaign_response_actions   
      └── response-driven actions
