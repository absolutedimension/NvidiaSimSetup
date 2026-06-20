---
title: "Module 3 — Tools & Integrations: Giving It Hands"
course: "Build Agentic AI Systems"
module: 3
video_type: full_lesson
length_target_sec: 510
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: hybrid
music: ambient_low
aspect: 16:9
---

## scenes

### scene_01_hook
narration: |
  An agent is only as capable as the tools you give it.
  Today we give ours real hands. It will search the web, read your files,
  read and write a database, update a Google Sheet, and send email.
  This is where the agent stops being a toy.
on_screen:
  title: Tools & Integrations
  subtitle: Module 3 — Giving It Hands
  layout: center
visual: brain with four reaching arms toward tool icons; circuit shader
duration_hint_sec: 18

### scene_02_what_makes_a_good_tool
narration: |
  Before we add tools, one rule. A good tool does one clear thing.
  Read a file. Send one email. Query the database. Not a giant do-everything function.
  Small, sharp tools are easier for the model to choose correctly, and easier for you to trust.
  When a tool is vague, the agent misuses it. When it is sharp, the agent shines.
on_screen:
  title: One Tool, One Job
  body: Small sharp tools → the model chooses correctly and you can trust it
  layout: center
visual: a bloated tool splits into three clean, single-purpose tools
duration_hint_sec: 36

### scene_03_web_and_files
narration: |
  Start with two everyday tools. Web search, so the agent can pull in fresh information.
  And file access, so it can read the documents you point it at.
  Together these let the agent work with the real world's knowledge and your own.
  We wire each one, describe it clearly, and add it to the menu.
on_screen:
  title: Web Search + Files
  bullets: ["Search — fresh outside info", "Files — read your documents"]
  layout: bullets
visual: search icon pulls in a web snippet; file icon opens a document into the loop
duration_hint_sec: 36

### scene_04_database_and_sheets
narration: |
  Next, structured data. A database the agent can read and write.
  And a Google Sheet, because so much real business work lives in a spreadsheet.
  Now the agent can look up a record, update a status, or append a row.
  This is the difference between an assistant that talks and one that keeps your books.
on_screen:
  title: Database + Google Sheet
  bullets: ["Read & write records", "Append & update sheet rows"]
  layout: bullets
visual: agent writes a row into a sheet; updates a record in a database table
duration_hint_sec: 38

### scene_05_email
narration: |
  Then, communication. An email tool so the agent can send a message.
  This is powerful, and a little scary, which is exactly why we are careful.
  At first the agent drafts, and you approve before anything goes out.
  Power with a checkpoint. We will formalize that safety in module six.
on_screen:
  title: Email — with a Checkpoint
  body: The agent drafts; a human approves before it sends (for now)
  layout: center
visual: agent composes an email; a human-approval gate before "send"
duration_hint_sec: 36

### scene_06_authentication
narration: |
  Real tools need keys. An API key for search, credentials for the sheet, access for email.
  We store these safely, in environment variables, never hard-coded, never shared.
  Good agent engineering is also good security. We treat every key with respect.
  An agent with real hands also has real reach. Lock the keys down.
on_screen:
  title: Keys & Access — Handle With Care
  bullets: ["Use environment variables", "Never hard-code secrets", "Least access needed"]
  layout: bullets
visual: a vault holding keys feeding the tools; a hard-coded key crossed out
duration_hint_sec: 36

### scene_07_let_the_agent_choose
narration: |
  Here is the magic. We do not tell the agent which tool to use.
  We give it the goal and the menu, and it chooses. Search first, then read, then update, then email.
  We just watch it reason through the steps. Each tool we added is now an option it can reach for.
  More good tools means a more capable agent.
on_screen:
  title: The Agent Chooses the Tools
  body: Goal + a menu → it sequences the tools itself
  layout: center
visual: the agent picks tools in sequence across one task, each lighting as used
duration_hint_sec: 38

### scene_08_ops_agent_link
narration: |
  Our Ops Agent now has its hands. It can read the inbox, pull the documents,
  update the sheet, and draft the replies. The capability is there.
  What it still lacks is memory across steps, and a plan for long jobs.
  Those are the next two modules. The agent is taking shape.
on_screen:
  title: The Ops Agent Has Hands
  bullets: ["Reads inbox & docs", "Updates the sheet", "Drafts replies"]
  layout: bullets
visual: Ops Agent diagram lights up its tool connections
duration_hint_sec: 32

### scene_09_cta
narration: |
  Your agent can now act in the real world. That is a big step.
  Next we give it memory, so it remembers what it did and what it learned.
  Without memory, even a tooled-up agent goes in circles. Let us fix that.
on_screen:
  title: Next — Memory & Context
  subtitle: Module 4
  layout: center
visual: memory layers preview; "Module 4" rises; logo + presenter
duration_hint_sec: 22
