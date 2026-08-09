1. **Base Agent using Python's `ABC` (Abstract Base Class)**

* `ABC` means  **Abstract Base Class** . It comes from Python's `abc` module : ---> from abc import ABC
* `BaseAgent` is an abstract/base class that defines a common structure for other agents.
* `@abstractmethod` means: ---> Every child class  **must implement the base method** .

The Base Agent says:

> "Every agent must have an `execute()` method."

But it doesn't decide what each agent actually does.

* `self` represents the  **current object/agent** : ---> Which agent object is executing this method?

 For example:

<pre class="overflow-visible! px-0!" data-start="2535" data-end="2573"><div class="relative w-full mt-4 mb-1"><div class=""><div class="contents"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="relative h-full w-full border-radius-3xl bg-(--code-block-surface) corner-superellipse/1.1 overflow-clip rounded-3xl [--code-block-surface:var(--bg-elevated-secondary)] dark:[--code-block-surface:var(--composer-surface-primary)] lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class=""><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼm">lead_agent</span><span></span><span class="ͼg">=</span><span></span><span class="ͼm">LeadAgent</span><span>()</span></code></pre></div></div></div></div></div></div></div></div></div></div></div></div></div></div></pre>

When we call:

<pre class="overflow-visible! px-0!" data-start="2590" data-end="2629"><div class="relative w-full mt-4 mb-1"><div class=""><div class="contents"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="relative h-full w-full border-radius-3xl bg-(--code-block-surface) corner-superellipse/1.1 overflow-clip rounded-3xl [--code-block-surface:var(--bg-elevated-secondary)] dark:[--code-block-surface:var(--composer-surface-primary)] lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class=""><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼm">lead_agent</span><span class="ͼg">.</span><span>execute(</span><span class="ͼm">state</span><span>)</span></code></pre></div></div></div></div></div></div></div></div></div></div></div></div></div></div></pre>

Python internally treats it approximately like:

<pre class="overflow-visible! px-0!" data-start="2680" data-end="2730"><div class="relative w-full mt-4 mb-1"><div class=""><div class="contents"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="relative h-full w-full border-radius-3xl bg-(--code-block-surface) corner-superellipse/1.1 overflow-clip rounded-3xl [--code-block-surface:var(--bg-elevated-secondary)] dark:[--code-block-surface:var(--composer-surface-primary)] lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class=""><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼm">LeadAgent</span><span class="ͼg">.</span><span>execute(</span><span class="ͼm">lead_agent</span><span>, </span><span class="ͼm">state</span><span>)</span></code></pre></div></div></div></div></div></div></div></div></div></div></div></div></div></div></pre>

* `state` represents the  **current information/data of the workflow** .

**Run the test_agents.py :** ---> python -m backend.tests.test_agents

ANS :

User Query: What is the current updates in the CRM system for our customers?
Selected Agent: CRMAgent
Status: This is all are our customers updated list till now.
Result: {"customer": "Naresh-SSIET", "status": "Updated"}
Error: None


**START Bakend : --->** python **-m** uvicorn backend.main:app **--reload**

**STATR Frontend** : ---> python run.py

**Database coneection** : ---> python -m backend.database.test_connection

# **Current database work completed**

backend/database/
├── __init__.py
├── connection.py       ✅ PostgreSQL connection
├── test_connection.py  ✅ connection tested
├── base.py             ✅ SQLAlchemy Base
├── session.py          ✅ database session
├── dependencies.py     ✅ FastAPI DB dependency
└── models.py           ✅ Organization model
