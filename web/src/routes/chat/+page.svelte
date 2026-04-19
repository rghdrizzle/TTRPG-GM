<script lang="ts">
  import { onMount } from "svelte"
  import { goto } from "$app/navigation"
  import { requireAuth, getToken } from "$lib/auth"

  type Phase = "form" | "creating" | "created"

  let phase       = $state<Phase>("form")
  let campaign    = $state<any>(null)
  let sessionId   = $state("")
  let now         = $state("")

  let name        = $state("")
  let rulebook    = $state("")
  let customRules = $state("")
  let description = $state("")
  let maxPlayers  = $state("4")
  let errors      = $state<Record<string, string>>({})
  let bootLines   = $state<string[]>([])

  const RULESETS = [
    "D&D 5e",
    "Pathfinder 2e",
    "Call of Cthulhu 7e",
    "Shadowrun 6e",
    "Blades in the Dark",
    "Mothership",
    "Cairn",
    "Custom / Homebrew",
  ]

  const BOOT_SEQUENCE = [
    "ALLOCATING CAMPAIGN NODE...",
    "INITIALIZING VECTOR DATABASE...",
    "LOADING RULEBOOK EMBEDDINGS...",
    "SEEDING WORLD STATE REGISTRY...",
    "CONFIGURING NPC REGISTRY...",
    "ESTABLISHING GM CONTEXT WINDOW...",
    "SYNCING SESSION MEMORY LAYER...",
    "CAMPAIGN NODE ONLINE ✓",
  ]

  onMount(() => {
    requireAuth()
    sessionId = Math.random().toString(36).substring(2, 10).toUpperCase()
    now = new Date().toLocaleString("en-GB", { hour12: false }).replace(",", "")
  })

  function validate() {
    const e: Record<string, string> = {}
    if (!name.trim()) e.name = "CAMPAIGN NAME REQUIRED"
    if (!rulebook)    e.rulebook = "SELECT A RULESET"
    if (rulebook === "Custom / Homebrew" && !customRules.trim())
      e.customRules = "DESCRIBE YOUR SYSTEM"
    errors = e
    return Object.keys(e).length === 0
  }

  async function submit() {
    if (!validate()) return
    phase = "creating"
    bootLines = []

    const apiCall = createCampaign()
    for (const line of BOOT_SEQUENCE.slice(0, -1)) {
      await delay(280 + Math.random() * 180)
      bootLines = [...bootLines, line]
    }

    const result = await apiCall
    if (result) {
      campaign = result
      await delay(200)
      bootLines = [...bootLines, BOOT_SEQUENCE.at(-1)!]
      await delay(600)
      phase = "created"
    } else {
      errors = { submit: "TRANSMISSION FAILED — CHECK CONNECTION" }
      phase = "form"
      bootLines = []
    }
  }

  async function createCampaign() {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/campaigns`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          name:        name.trim(),
          rulebook:    rulebook === "Custom / Homebrew" ? customRules.trim() : rulebook,
          description: description.trim() || null,
          max_players: parseInt(maxPlayers, 10),
        }),
      })
      if (!res.ok) return null
      return await res.json()
    } catch {
      return null
    }
  }

  function delay(ms: number) {
    return new Promise(r => setTimeout(r, ms))
  }
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Bebas+Neue&display=swap" rel="stylesheet">
</svelte:head>

<style>
  :global(body) { background: #000; cursor: crosshair; }
  .mono    { font-family: 'Share Tech Mono', monospace; }
  .display { font-family: 'Bebas Neue', sans-serif; }
  .scanline {
    background: repeating-linear-gradient(
      0deg, transparent, transparent 3px,
      rgba(255,255,255,0.015) 3px, rgba(255,255,255,0.015) 4px
    );
  }
  .ticker { animation: ticker 20s linear infinite; white-space: nowrap; }
  @keyframes ticker { from { transform: translateX(100%); } to { transform: translateX(-100%); } }
  .blink { animation: blink 1.2s step-end infinite; }
  @keyframes blink { 50% { opacity: 0; } }
  .pulse { animation: pulse 2s ease-in-out infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }

  .rule-h { border-top: 1px solid rgba(255,255,255,0.15); }
  .rule-v { border-left: 1px solid rgba(255,255,255,0.15); }

  .scroll::-webkit-scrollbar       { width: 2px; }
  .scroll::-webkit-scrollbar-track { background: transparent; }
  .scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); }

  .field {
    border: 1px solid rgba(255,255,255,0.1);
    transition: border-color 0.15s;
  }
  .field:focus-within { border-color: rgba(255,255,255,0.3); }
  .field.err          { border-color: rgba(255,80,80,0.4); }

  .field input,
  .field select,
  .field textarea {
    background: transparent;
    border: none;
    outline: none;
    width: 100%;
    color: rgba(255,255,255,0.8);
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    padding: 10px 12px;
    resize: none;
  }
  .field input::placeholder,
  .field textarea::placeholder { color: rgba(255,255,255,0.15); }
  .field select option { background: #0a0a0a; color: rgba(255,255,255,0.8); }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateX(-4px); }
    to   { opacity: 1; transform: none; }
  }
  .boot-line { animation: fadeIn 0.18s ease forwards; }

  .action-btn {
    border: 1px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.45);
    transition: border-color 0.15s, color 0.15s, background 0.15s;
    cursor: pointer;
    width: 100%;
    padding: 14px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .action-btn:hover { border-color: rgba(255,255,255,0.45); color: rgba(255,255,255,0.85); }
  .action-btn.primary { border-color: rgba(255,255,255,0.35); color: rgba(255,255,255,0.85); }
  .action-btn.primary:hover { background: #fff; color: #000; }
  .action-btn.primary:hover .sub { color: rgba(0,0,0,0.45); }
</style>

<div class="min-h-screen bg-black text-white scanline mono">

  <!-- Grid overlay -->
  <div class="fixed inset-0 pointer-events-none"
    style="background-image:linear-gradient(rgba(255,255,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.03) 1px,transparent 1px);background-size:60px 60px;">
  </div>

  <!-- ═══ CHROME ═══ -->
  <div class="fixed top-0 left-0 right-0 z-50">

    <div class="bg-[#0a0a0a] border-b border-white/10 px-4 h-9 flex items-center gap-4">
      <div class="flex gap-1.5">
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
      </div>
      <div class="flex-1 bg-black/60 border border-white/10 h-5 flex items-center px-3 max-w-sm">
        <span class="text-white/40 text-xs">HTTPS://TTRPG.GM.SYSTEM/CAMPAIGNS/NEW</span>
      </div>
      <div class="ml-auto flex gap-3">
        <span class="text-white/20 text-xs">□</span>
        <span class="text-white/20 text-xs">—</span>
        <span class="text-white/20 text-xs">✕</span>
      </div>
    </div>

    <div class="bg-black/95 border-b border-white/10 h-10 flex items-center px-6">
      <div class="flex items-center gap-8 flex-1">
        <span class="display text-xl tracking-wider">/CAMPAIGNS</span>
        <div class="rule-v h-5"></div>
        <a href="/dashboard" class="text-xs text-white/30 tracking-widest hover:text-white/60 transition-colors">CAMPAIGNS 戰役</a>
        <a href="/rulebook"  class="text-xs text-white/30 tracking-widest hover:text-white/60 transition-colors">RULEBOOK 規則</a>
        <a href="/sessions"  class="text-xs text-white/30 tracking-widest hover:text-white/60 transition-colors">SESSIONS 會話</a>
      </div>
      <div class="flex items-center gap-6">
        <span class="text-xs text-white/30">NODE [{sessionId}]</span>
        <a href="/dashboard" class="text-xs text-white/30 tracking-widest hover:text-white transition-colors border border-white/10 hover:border-white/40 px-3 py-1">
          ← EXIT 退出
        </a>
      </div>
    </div>

    <div class="bg-black border-b border-white/10 h-4 flex items-end px-6 overflow-hidden">
      {#each Array(40) as _, i}
        <div class="flex-1 flex items-end justify-center">
          <div class="w-px bg-white"
            style="height:{i % 5 === 0 ? 8 : 4}px; opacity:{i % 5 === 0 ? 0.2 : 0.08};">
          </div>
        </div>
      {/each}
    </div>
  </div>

  <!-- ═══ BODY — fixed between chrome (88px) and footer (56px) ═══ -->
  <div class="fixed left-0 right-0 flex flex-col" style="top:88px; bottom:56px;">

    <!-- Step bar -->
    <div class="border-b border-white/10 px-6 h-10 flex items-center shrink-0">
      <div class="flex items-center gap-3">
        <div class="h-px w-6" style="background:rgba(255,255,255,{phase === 'form' ? 0.9 : 0.3});"></div>
        <span class="text-xs tracking-widest" style="color:rgba(255,255,255,{phase === 'form' ? 0.9 : 0.25});">01 CONFIGURE</span>
      </div>
      <div class="rule-v h-4 mx-5"></div>
      <div class="flex items-center gap-3">
        <div class="h-px w-6" style="background:rgba(255,255,255,{phase === 'creating' ? 0.9 : phase === 'created' ? 0.3 : 0.08});"></div>
        <span class="text-xs tracking-widest" style="color:rgba(255,255,255,{phase === 'creating' ? 0.9 : phase === 'created' ? 0.25 : 0.12});">02 DEPLOY</span>
      </div>
      <div class="rule-v h-4 mx-5"></div>
      <div class="flex items-center gap-3">
        <div class="h-px w-6" style="background:rgba(255,255,255,{phase === 'created' ? 0.9 : 0.08});"></div>
        <span class="text-xs tracking-widest" style="color:rgba(255,255,255,{phase === 'created' ? 0.9 : 0.12});">03 ACTIVE</span>
      </div>
      <div class="ml-auto text-xs text-white/20">
        {#if phase === 'form'}CONFIGURE CAMPAIGN NODE
        {:else if phase === 'creating'}<span class="blink">ESTABLISHING NODE_</span>
        {:else}CAMPAIGN NODE ONLINE
        {/if}
      </div>
    </div>

    <!-- Content row -->
    <div class="flex flex-1 overflow-hidden">

      <!-- Scrollable main -->
      <div class="flex-1 overflow-y-auto scroll px-6 py-8">

        <!-- ══ PHASE: FORM ══ -->
        {#if phase === "form"}
          <div class="max-w-lg">

            <div class="mb-7">
              <div class="text-white/20 text-xs tracking-widest mb-1">NEW_CAMPAIGN_NODE</div>
              <div class="display text-5xl tracking-wider leading-none">FORGE A<br>CAMPAIGN</div>
            </div>

            {#if errors.submit}
              <div class="mb-5 border border-red-500/30 bg-red-500/5 px-4 py-2.5">
                <span class="text-red-400 text-xs">{errors.submit}</span>
              </div>
            {/if}

            <div class="space-y-5">

              <!-- Name -->
              <div>
                <div class="text-white/30 text-xs tracking-widest mb-1.5">
                  CAMPAIGN NAME <span class="text-white/15">*</span>
                </div>
                <div class="field {errors.name ? 'err' : ''}">
                  <input
                    type="text"
                    bind:value={name}
                    placeholder="THE LOST MINES OF PHANDELVER"
                    maxlength="80"
                    oninput={() => delete errors.name}
                  />
                </div>
                {#if errors.name}
                  <p class="text-red-400/80 text-xs mt-1">{errors.name}</p>
                {/if}
              </div>

              <!-- Ruleset -->
              <div>
                <div class="text-white/30 text-xs tracking-widest mb-1.5">
                  RULE SYSTEM <span class="text-white/15">*</span>
                </div>
                <div class="field {errors.rulebook ? 'err' : ''}">
                  <select bind:value={rulebook} onchange={() => delete errors.rulebook}>
                    <option value="" disabled selected>SELECT RULESET...</option>
                    {#each RULESETS as r}
                      <option value={r}>{r}</option>
                    {/each}
                  </select>
                </div>
                {#if errors.rulebook}
                  <p class="text-red-400/80 text-xs mt-1">{errors.rulebook}</p>
                {/if}
              </div>

              <!-- Custom rules -->
              {#if rulebook === "Custom / Homebrew"}
                <div>
                  <div class="text-white/30 text-xs tracking-widest mb-1.5">
                    SYSTEM DESCRIPTION <span class="text-white/15">*</span>
                  </div>
                  <div class="field {errors.customRules ? 'err' : ''}">
                    <textarea
                      bind:value={customRules}
                      rows="3"
                      placeholder="DESCRIBE YOUR HOMEBREW SYSTEM, CORE MECHANICS, DICE CONVENTIONS..."
                      oninput={() => delete errors.customRules}
                    ></textarea>
                  </div>
                  {#if errors.customRules}
                    <p class="text-red-400/80 text-xs mt-1">{errors.customRules}</p>
                  {/if}
                </div>
              {/if}

              <!-- Description -->
              <div>
                <div class="text-white/30 text-xs tracking-widest mb-1.5">
                  CAMPAIGN DESCRIPTION
                  <span class="text-white/15 ml-2">OPTIONAL</span>
                </div>
                <div class="field">
                  <textarea
                    bind:value={description}
                    rows="4"
                    placeholder="SETTING, TONE, PLOT HOOKS, AND WORLD CONTEXT FOR THE GM AI..."
                  ></textarea>
                </div>
                <p class="text-white/15 text-xs mt-1">INJECTED INTO GM SYSTEM PROMPT AS WORLD CONTEXT</p>
              </div>

              <!-- Max players -->
              <div>
                <div class="text-white/30 text-xs tracking-widest mb-2">MAX PLAYERS</div>
                <div class="flex gap-1.5">
                  {#each ["1","2","3","4","5","6","8"] as n}
                    <button
                      type="button"
                      onclick={() => maxPlayers = n}
                      class="w-9 h-9 border text-xs transition-all
                        {maxPlayers === n
                          ? 'border-white/50 text-white bg-white/8'
                          : 'border-white/10 text-white/30 hover:border-white/25 hover:text-white/55'}"
                    >{n}</button>
                  {/each}
                </div>
              </div>

              <!-- Submit -->
              <div class="pt-3 flex items-center gap-5">
                <button
                  onclick={submit}
                  class="border border-white/35 hover:border-white hover:bg-white hover:text-black transition-all px-7 py-2.5 text-sm tracking-widest"
                >
                  DEPLOY CAMPAIGN →
                </button>
                <a href="/dashboard" class="text-white/20 text-xs hover:text-white/45 transition-colors tracking-widest">
                  CANCEL
                </a>
              </div>

            </div>
          </div>

        <!-- ══ PHASE: CREATING ══ -->
        {:else if phase === "creating"}
          <div class="max-w-md">

            <div class="mb-7">
              <div class="text-white/20 text-xs tracking-widest mb-1">DEPLOYING NODE</div>
              <div class="display text-5xl tracking-wider leading-none">ESTABLISHING<br>CAMPAIGN...</div>
            </div>

            <div class="border border-white/10 bg-white/[0.02]">
              <div class="border-b border-white/10 px-4 py-2 flex items-center gap-3">
                <span class="text-white/20 text-xs tracking-widest">SYSTEM OUTPUT</span>
                <span class="text-white/10 text-xs">///</span>
                <span class="text-white blink text-xs">● LIVE</span>
              </div>
              <div class="p-4 space-y-2" style="min-height:210px;">
                {#each bootLines as line}
                  <div class="boot-line flex items-start gap-3">
                    <span class="text-white/20 text-xs mt-px">›</span>
                    <span class="text-white/65 text-xs">{line}</span>
                  </div>
                {/each}
                <div class="flex items-center gap-3">
                  <span class="text-white/20 text-xs">›</span>
                  <span class="text-white/30 text-xs blink">_</span>
                </div>
              </div>
            </div>

            <div class="mt-3 h-px bg-white/5 relative overflow-hidden">
              <div
                class="absolute inset-y-0 left-0 bg-white/35 transition-all duration-300"
                style="width:{Math.round((bootLines.length / BOOT_SEQUENCE.length) * 100)}%;"
              ></div>
            </div>
            <div class="flex justify-between mt-1.5">
              <span class="text-white/15 text-xs">PROGRESS</span>
              <span class="text-white/30 text-xs">{Math.round((bootLines.length / BOOT_SEQUENCE.length) * 100)}%</span>
            </div>
          </div>

        <!-- ══ PHASE: CREATED ══ -->
        {:else if phase === "created"}
          <div class="max-w-md">

            <div class="mb-7">
              <div class="text-white/20 text-xs tracking-widest mb-1">NODE ONLINE</div>
              <div class="display text-5xl tracking-wider leading-none">CAMPAIGN<br>DEPLOYED ✓</div>
            </div>

            <div class="border border-white/15 mb-6">
              <div class="border-b border-white/10 px-4 py-2.5 flex items-center justify-between">
                <span class="text-white/20 text-xs tracking-widest">CAMPAIGN_NODE</span>
                <span class="text-white/40 text-xs pulse">● ACTIVE</span>
              </div>
              <div class="p-4 space-y-4">
                <div>
                  <div class="text-white/20 text-xs mb-1">IDENT</div>
                  <div class="display text-3xl tracking-wider">{campaign?.name?.toUpperCase()}</div>
                </div>
                <div class="rule-h pt-3 grid grid-cols-2 gap-3">
                  <div>
                    <div class="text-white/20 text-xs mb-0.5">SYSTEM</div>
                    <div class="text-white/60 text-xs">{campaign?.rulebook ?? "—"}</div>
                  </div>
                  <div>
                    <div class="text-white/20 text-xs mb-0.5">PLAYERS</div>
                    <div class="text-white/60 text-xs">{campaign?.max_players ?? maxPlayers}</div>
                  </div>
                  <div>
                    <div class="text-white/20 text-xs mb-0.5">NODE ID</div>
                    <div class="text-white/40 text-xs truncate">{campaign?.id ?? "—"}</div>
                  </div>
                  <div>
                    <div class="text-white/20 text-xs mb-0.5">CREATED</div>
                    <div class="text-white/40 text-xs">{now}</div>
                  </div>
                </div>
                {#if campaign?.description}
                  <div class="rule-h pt-3">
                    <div class="text-white/20 text-xs mb-1">LORE</div>
                    <div class="text-white/35 text-xs leading-relaxed line-clamp-3">{campaign.description}</div>
                  </div>
                {/if}
              </div>
            </div>

            <div class="space-y-2">
              <div class="text-white/20 text-xs tracking-widest mb-3">NEXT ACTION 下一步</div>

              <button onclick={() => goto(`/campaigns/${campaign.id}`)} class="action-btn primary">
                <div>
                  <div class="text-sm tracking-widest">START CAMPAIGN →</div>
                  <div class="sub text-white/40 text-xs mt-0.5">OPEN GM CHAT // BEGIN SESSION</div>
                </div>
                <span class="display text-xl opacity-50">▶</span>
              </button>

              <button onclick={() => goto(`/campaigns/${campaign.id}/sessions`)} class="action-btn">
                <div>
                  <div class="text-sm tracking-widest">VIEW SESSIONS</div>
                  <div class="text-white/25 text-xs mt-0.5">MANAGE PAST & UPCOMING SESSIONS</div>
                </div>
                <span class="display text-xl opacity-30">≡</span>
              </button>

              <button onclick={() => goto('/dashboard')} class="action-btn">
                <div>
                  <div class="text-sm tracking-widest">BACK TO DASHBOARD</div>
                  <div class="text-white/25 text-xs mt-0.5">RETURN TO CAMPAIGNS LIST</div>
                </div>
                <span class="display text-xl opacity-30">⌂</span>
              </button>
            </div>
          </div>
        {/if}

      </div>

      <!-- ── Right sidebar ── -->
      <div class="w-56 border-l border-white/10 flex flex-col shrink-0 overflow-y-auto scroll">

        <div class="p-4 border-b border-white/10">
          <div class="text-white/20 text-xs tracking-widest mb-3">SYSTEM STATUS</div>
          <div class="space-y-2.5">
            {#each [
              { label: "GM ENGINE",     ok: true },
              { label: "VECTOR DB",     ok: true },
              { label: "RAG CONTEXT",   ok: true },
              { label: "DICE ENGINE",   ok: true },
              { label: "CAMPAIGN NODE", ok: phase === "created" },
            ] as item}
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style="background:rgba(255,255,255,{item.ok ? 0.5 : 0.12});"></div>
                <span class="text-xs" style="color:rgba(255,255,255,{item.ok ? 0.35 : 0.15});">{item.label}</span>
                <span class="ml-auto text-xs" style="color:rgba(255,255,255,{item.ok ? 0.25 : 0.1});">
                  {item.ok ? "OK" : "—"}
                </span>
              </div>
            {/each}
          </div>
        </div>

        <div class="p-4 flex-1">
          <div class="text-white/20 text-xs tracking-widest mb-3">TIPS 提示</div>
          <div class="space-y-3">
            {#each [
              "Description is injected as GM world context.",
              "Rulebook embeddings load automatically from the vector DB.",
              "Players can be added after creating the campaign.",
              "Session history persists across all game sessions.",
            ] as tip}
              <div class="flex gap-2">
                <span class="text-white/15 text-xs flex-shrink-0 mt-0.5">›</span>
                <span class="text-white/25 text-xs leading-relaxed">{tip}</span>
              </div>
            {/each}
          </div>
        </div>

        <div class="p-4 border-t border-white/10">
          <div class="flex gap-px h-10">
            {#each Array(30) as _, i}
              <div class="flex-1 bg-white"
                style="opacity:{Math.random() > 0.45 ? Math.random() * 0.3 + 0.05 : 0};"></div>
            {/each}
          </div>
        </div>

      </div>
    </div>
  </div>

  <!-- ═══ FOOTER ═══ -->
  <div class="fixed bottom-0 left-0 right-0 bg-black border-t border-white/10 z-50 h-14">
    <div class="border-b border-white/10 h-6 overflow-hidden flex items-center">
      <div class="ticker mono text-xs text-white/20">
        TTRPG-GM-SYSTEM &nbsp;///&nbsp; AI GAME MASTER ONLINE &nbsp;///&nbsp; RAG ENABLED &nbsp;///&nbsp;
        CAMPAIGN FORGE ACTIVE &nbsp;///&nbsp; VECTOR DB SYNCED &nbsp;///&nbsp; CLAUDE SONNET CONNECTED &nbsp;///&nbsp;
      </div>
    </div>
    <div class="h-8 px-6 flex items-center gap-8">
      <span class="mono text-xs text-white/20">NODE [{sessionId}]</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs text-white/20">/CAMPAIGNS/NEW</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs text-white/20 blink">● FORGE MODE</span>
      <div class="ml-auto mono text-xs text-white/20">TTRPG INDUSTRIAL // COPYRIGHT © 2077</div>
    </div>
  </div>

</div>