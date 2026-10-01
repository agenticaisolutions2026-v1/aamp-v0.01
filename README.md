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

<pre class="overflow-visible! px-0!" data-start="1585" data-end="1697"><div class="relative w-full mt-4 mb-1"><div class=""><div class="contents"><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-(--code-block-surface) corner-superellipse/1.1 overflow-clip rounded-3xl [--code-block-surface:var(--bg-elevated-secondary)] dark:[--code-block-surface:var(--composer-surface-primary)] lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>✓ Email Sent
✓ Response Received
✓ Response Classified
🔵 Human Action Required
○ Campaign Completed</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></div></pre>

### Path 4 — Opted out

<pre class="overflow-visible! px-0!" data-start="1723" data-end="1811"><div class="relative w-full mt-4 mb-1"><div class=""><div class="contents"><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-(--code-block-surface) corner-superellipse/1.1 overflow-clip rounded-3xl [--code-block-surface:var(--bg-elevated-secondary)] dark:[--code-block-surface:var(--composer-surface-primary)] lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>✓ Email Sent
✓ Response Received
✓ Response Classified
🛑 Campaign Opted Out</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></div></pre>

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
└── campaign_response_actions   ← NEW
      └── response-driven actions
