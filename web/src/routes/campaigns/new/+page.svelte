<script lang="ts">
  import { onMount } from "svelte"
  import { goto } from "$app/navigation"
  import { requireAuth, getToken } from "$lib/auth"

  // ── Types ─────────────────────────────────────────────────
  type Phase = "form" | "creating" | "created"

  // ── State ─────────────────────────────────────────────────
  let phase       = $state<Phase>("form")
  let campaign    = $state<any>(null)
  let sessionId   = $state("")
  let now         = $state("")

  // Form fields
  let name        = $state("")
  let rulebook    = $state("")
  let customRules = $state("")
  let description = $state("")
  let maxPlayers  = $state("4")
  let errors      = $state<Record<string, string>>({})

  // Boot sequence lines (creating phase)
  let bootLines   = $state<string[]>([])

  const RULESETS = [
    "FIST"
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

  // ── Validation ────────────────────────────────────────────
  function validate() {
    const e: Record<string, string> = {}
    if (!name.trim())     e.name     = "CAMPAIGN NAME REQUIRED"
    if (!rulebook)        e.rulebook = "SELECT A RULESET"
    if (rulebook === "Custom / Homebrew" && !customRules.trim())
                          e.customRules = "DESCRIBE YOUR SYSTEM"
    errors = e
    return Object.keys(e).length === 0
  }

  // ── Submit ─────────────────────────────────────────────────
  async function submit() {
    if (!validate()) return
    phase = "creating"
    bootLines = []

    // Animate boot sequence while calling API in parallel
    const apiCall = createCampaign()
    for (const line of BOOT_SEQUENCE.slice(0, -1)) {
      await delay(280 + Math.random() * 180)
      bootLines = [...bootLines, line]
    }

    // Await API
    const result = await apiCall
    if (result) {
      campaign = result
      await delay(200)
      bootLines = [...bootLines, BOOT_SEQUENCE.at(-1)!]
      await delay(600)
      phase = "created"
    } else {
      // Error — back to form
      errors = { submit: "TRANSMISSION FAILED — CHECK CONNECTION" }
      phase = "form"
      bootLines = []
    }
  }

  async function createCampaign() {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/campaigns`, {
        method:  "POST",
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

  function startCampaign() {
    goto(`/campaigns/${campaign.id}`)
  }

  function viewSessions() {
    goto(`/campaigns/${campaign.id}/sessions`)
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

  .rule-h { border-top: 1px solid rgba(255,255,255,0.15); }
  .rule-v { border-left:  1px solid rgba(255,255,255,0.15); }

  /* Form inputs — override browser defaults */
  .field-input {
    background: transparent;
    border: none;
    outline: none;
    width: 100%;
    color: rgba(255,255,255,0.8);
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    padding: 10px 14px;
  }
  .field-input::placeholder { color: rgba(255,255,255,0.15); }
  .field-input:disabled     { opacity: 0.4; cursor: not-allowed; }

  select.field-input option {
    background: #0a0a0a;
    color: rgba(255,255,255,0.8);
  }

  /* Fieldset wrapper */
  .field-wrap {
    border: 1px solid rgba(255,255,255,0.1);
    transition: border-color 0.15s;
  }
  .field-wrap:focus-within { border-color: rgba(255,255,255,0.35); }
  .field-wrap.has-error    { border-color: rgba(255,80,80,0.5); }

  /* Step bar */
  .step-active   { background: rgba(255,255,255,0.9); }
  .step-done     { background: rgba(255,255,255,0.3); }
  .step-inactive { background: rgba(255,255,255,0.08); }

  /* Boot lines fade in */
  @keyframes fadeSlide {
    from { opacity: 0; transform: translateX(-6px); }
    to   { opacity: 1; transform: translateX(0); }
  }
  .boot-line { animation: fadeSlide 0.2s ease forwards; }

  /* Pulse on created node ID */
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
  .pulse { animation: pulse 2s ease-in-out infinite; }

  /* Action button hover */
  .action-btn {
    border: 1px solid rgba(255,255,255,0.2);
    color: rgba(255,255,255,0.5);
    transition: border-color 0.15s, color 0.15s, background 0.15s;
    cursor: pointer;
  }
  .action-btn:hover {
    border-color: rgba(255,255,255,0.8);
    color: #fff;
  }
  .action-btn.primary {
    border-color: rgba(255,255,255,0.6);
    color: rgba(255,255,255,0.9);
  }
  .action-btn.primary:hover {
    background: #fff;
    color: #000;
  }

  .player-dot { animation: pulse 2s ease-in-out infinite; }
</style>

<div class="min-h-screen bg-black text-white scanline relative overflow-hidden mono">

  <!-- Grid overlay -->
  <div class="fixed inset-0 pointer-events-none"
    style="background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
           linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
           background-size: 60px 60px;">
  </div>

  <!-- ═══ CHROME ═══ -->
  <div class="fixed top-0 left-0 right-0 z-50">
    <!-- Tab bar -->
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

    <!-- Nav bar -->
    <div class="bg-black/95 border-b border-white/10 h-10 flex items-center px-6">
      <div class="flex items-center gap-8 flex-1">
        <span class="display text-xl tracking-wider text-white">/CAMPAIGNS</span>
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

    <!-- Tick ruler -->
    <div class="bg-black border-b border-white/10 h-4 flex items-end px-6 overflow-hidden">
      {#each Array(40) as _, i}
        <div class="flex-1 flex items-end justify-center">
          <div class="w-px bg-white/{i % 5 === 0 ? '20' : '10'}" style="height: {i % 5 === 0 ? 8 : 4}px;"></div>
        </div>
      {/each}
    </div>
  </div>

  <!-- ═══ CONTENT ═══ -->
  <div class="pt-[88px] pb-14 min-h-screen flex flex-col">

    <!-- Step indicator -->
    <div class="border-b border-white/10 px-12 py-4 flex items-center gap-6">
      <div class="flex items-center gap-3">
        <div class="w-20 h-0.5 {phase === 'form' ? 'step-active' : 'step-done'}"></div>
        <span class="text-xs tracking-widest {phase === 'form' ? 'text-white' : 'text-white/30'}">01 CONFIGURE</span>
      </div>
      <div class="w-px h-3 bg-white/10"></div>
      <div class="flex items-center gap-3">
        <div class="w-20 h-0.5 {phase === 'creating' ? 'step-active' : phase === 'created' ? 'step-done' : 'step-inactive'}"></div>
        <span class="text-xs tracking-widest {phase === 'creating' ? 'text-white' : phase === 'created' ? 'text-white/30' : 'text-white/15'}">02 DEPLOY</span>
      </div>
      <div class="w-px h-3 bg-white/10"></div>
      <div class="flex items-center gap-3">
        <div class="w-20 h-0.5 {phase === 'created' ? 'step-active' : 'step-inactive'}"></div>
        <span class="text-xs tracking-widest {phase === 'created' ? 'text-white' : 'text-white/15'}">03 ACTIVE</span>
      </div>
      <div class="ml-auto text-white/20 text-xs">
        {#if phase === 'form'}     CONFIGURE CAMPAIGN NODE
        {:else if phase === 'creating'} ESTABLISHING NODE...
        {:else}                   CAMPAIGN NODE ONLINE
        {/if}
      </div>
    </div>

    <div class="flex-1 flex">

      <!-- ── Main area ── -->
      <div class="flex-1 px-12 py-10">

        <!-- ══ PHASE: FORM ══ -->
        {#if phase === "form"}
          <div class="max-w-xl">
            <div class="mb-8">
              <div class="text-white/20 text-xs tracking-widest mb-1">NEW_CAMPAIGN_NODE</div>
              <div class="display text-5xl text-white tracking-wider">FORGE A<br>CAMPAIGN</div>
            </div>

            <!-- Global error -->
            {#if errors.submit}
              <div class="mb-6 border border-red-500/30 bg-red-500/5 px-4 py-3">
                <span class="text-red-400 text-xs">{errors.submit}</span>
              </div>
            {/if}

            <div class="space-y-5">

              <!-- Campaign Name -->
              <div>
                <div class="text-white/30 text-xs tracking-widest mb-1.5">CAMPAIGN NAME *</div>
                <div class="field-wrap {errors.name ? 'has-error' : ''}">
                  <div class="flex items-center border-b border-white/10 px-3 py-1.5">
                    <span class="text-white/20 text-xs">IDENT:</span>
                  </div>
                  <input
                    type="text"
                    bind:value={name}
                    placeholder="THE LOST MINES OF PHANDELVER"
                    maxlength="80"
                    class="field-input"
                    oninput={() => delete errors.name}
                  />
                </div>
                {#if errors.name}
                  <p class="text-red-400 text-xs mt-1">{errors.name}</p>
                {/if}
              </div>

              <!-- Rulebook -->
              <div>
                <div class="text-white/30 text-xs tracking-widest mb-1.5">RULE SYSTEM *</div>
                <div class="field-wrap {errors.rulebook ? 'has-error' : ''}">
                  <div class="flex items-center border-b border-white/10 px-3 py-1.5">
                    <span class="text-white/20 text-xs">SYS:</span>
                  </div>
                  <select
                    bind:value={rulebook}
                    class="field-input"
                    onchange={() => delete errors.rulebook}
                  >
                    <option value="" disabled selected>SELECT RULESET...</option>
                    {#each RULESETS as r}
                      <option value={r}>{r}</option>
                    {/each}
                  </select>
                </div>
                {#if errors.rulebook}
                  <p class="text-red-400 text-xs mt-1">{errors.rulebook}</p>
                {/if}
              </div>

              <!-- Custom rules — only if Homebrew selected -->
              {#if rulebook === "Custom / Homebrew"}
                <div>
                  <div class="text-white/30 text-xs tracking-widest mb-1.5">SYSTEM DESCRIPTION *</div>
                  <div class="field-wrap {errors.customRules ? 'has-error' : ''}">
                    <div class="flex items-center border-b border-white/10 px-3 py-1.5">
                      <span class="text-white/20 text-xs">RULES:</span>
                    </div>
                    <textarea
                      bind:value={customRules}
                      placeholder="DESCRIBE YOUR HOMEBREW SYSTEM, CORE MECHANICS, AND DICE CONVENTIONS..."
                      rows="3"
                      class="field-input"
                      style="resize: none; outline: none;"
                      oninput={() => delete errors.customRules}
                    ></textarea>
                  </div>
                  {#if errors.customRules}
                    <p class="text-red-400 text-xs mt-1">{errors.customRules}</p>
                  {/if}
                </div>
              {/if}

              <!-- Description -->
              <div>
                <div class="text-white/30 text-xs tracking-widest mb-1.5">CAMPAIGN DESCRIPTION <span class="text-white/15">OPTIONAL</span></div>
                <div class="field-wrap">
                  <div class="flex items-center border-b border-white/10 px-3 py-1.5">
                    <span class="text-white/20 text-xs">LORE:</span>
                  </div>
                  <textarea
                    bind:value={description}
                    placeholder="SETTING, TONE, PLOT HOOKS, AND WORLD CONTEXT FOR THE GM AI..."
                    rows="4"
                    class="field-input"
                    style="resize: none; outline: none;"
                  ></textarea>
                </div>
                <p class="text-white/15 text-xs mt-1">INJECTED INTO GM SYSTEM PROMPT AS WORLD CONTEXT</p>
              </div>

              <!-- Max Players -->
              <div>
                <div class="text-white/30 text-xs tracking-widest mb-1.5">MAX PLAYERS</div>
                <div class="flex gap-2">
                  {#each ["1","2","3","4","5","6","8"] as n}
                    <button
                      type="button"
                      onclick={() => maxPlayers = n}
                      class="w-10 h-10 border text-xs transition-all {maxPlayers === n
                        ? 'border-white/60 text-white bg-white/10'
                        : 'border-white/10 text-white/30 hover:border-white/30 hover:text-white/60'}"
                    >{n}</button>
                  {/each}
                </div>
              </div>

              <!-- Submit -->
              <div class="pt-4 flex items-center gap-4">
                <button
                  onclick={submit}
                  class="border border-white/40 hover:border-white hover:bg-white hover:text-black transition-all px-8 py-3 text-sm tracking-widest text-white"
                >
                  DEPLOY CAMPAIGN →
                </button>
                <a href="/dashboard" class="text-white/20 text-xs hover:text-white/50 transition-colors tracking-widest">
                  CANCEL
                </a>
              </div>

            </div>
          </div>

        <!-- ══ PHASE: CREATING ══ -->
        {:else if phase === "creating"}
          <div class="max-w-lg">
            <div class="mb-8">
              <div class="text-white/20 text-xs tracking-widest mb-1">DEPLOYING NODE</div>
              <div class="display text-5xl text-white tracking-wider">ESTABLISHING<br>CAMPAIGN...</div>
            </div>

            <!-- Boot sequence terminal -->
            <div class="border border-white/10 bg-white/[0.02]">
              <div class="border-b border-white/10 px-4 py-2 flex items-center gap-3">
                <span class="text-white/20 text-xs tracking-widest">SYSTEM OUTPUT</span>
                <span class="text-white/10 text-xs">///</span>
                <span class="text-white blink text-xs">● LIVE</span>
              </div>
              <div class="p-5 space-y-2 min-h-[220px]">
                {#each bootLines as line}
                  <div class="boot-line flex items-center gap-3">
                    <span class="text-white/20 text-xs">&gt;</span>
                    <span class="text-white/70 text-xs">{line}</span>
                  </div>
                {/each}
                <div class="flex items-center gap-3">
                  <span class="text-white/20 text-xs">&gt;</span>
                  <span class="text-white/30 text-xs blink">_</span>
                </div>
              </div>
            </div>

            <!-- Progress bar -->
            <div class="mt-4 h-px bg-white/5 relative overflow-hidden">
              <div
                class="absolute inset-y-0 left-0 bg-white/40 transition-all"
                style="width: {Math.round((bootLines.length / BOOT_SEQUENCE.length) * 100)}%;"
              ></div>
            </div>
            <div class="flex justify-between mt-1">
              <span class="text-white/15 text-xs">0%</span>
              <span class="text-white/30 text-xs">{Math.round((bootLines.length / BOOT_SEQUENCE.length) * 100)}%</span>
              <span class="text-white/15 text-xs">100%</span>
            </div>
          </div>

        <!-- ══ PHASE: CREATED ══ -->
        {:else if phase === "created"}
          <div class="max-w-lg">
            <div class="mb-8">
              <div class="text-white/20 text-xs tracking-widest mb-1">NODE ONLINE</div>
              <div class="display text-5xl text-white tracking-wider">CAMPAIGN<br>DEPLOYED ✓</div>
            </div>

            <!-- Campaign card -->
            <div class="border border-white/20 mb-8">
              <!-- Header -->
              <div class="border-b border-white/10 px-5 py-3 flex items-center justify-between">
                <span class="text-white/20 text-xs tracking-widest">CAMPAIGN_NODE</span>
                <span class="text-white/40 text-xs pulse">● ACTIVE</span>
              </div>
              <!-- Body -->
              <div class="p-5 space-y-4">
                <div>
                  <div class="text-white/20 text-xs mb-1">IDENT</div>
                  <div class="display text-3xl text-white tracking-wider">{campaign?.name?.toUpperCase()}</div>
                </div>
                <div class="grid grid-cols-2 gap-4 rule-h pt-4">
                  <div>
                    <div class="text-white/20 text-xs mb-1">SYSTEM</div>
                    <div class="text-white/70 text-xs">{campaign?.rulebook ?? "—"}</div>
                  </div>
                  <div>
                    <div class="text-white/20 text-xs mb-1">MAX PLAYERS</div>
                    <div class="text-white/70 text-xs">{campaign?.max_players ?? maxPlayers}</div>
                  </div>
                  <div>
                    <div class="text-white/20 text-xs mb-1">NODE ID</div>
                    <div class="text-white/50 text-xs">{campaign?.id ?? "—"}</div>
                  </div>
                  <div>
                    <div class="text-white/20 text-xs mb-1">CREATED</div>
                    <div class="text-white/50 text-xs">{now}</div>
                  </div>
                </div>
                {#if campaign?.description}
                  <div class="rule-h pt-4">
                    <div class="text-white/20 text-xs mb-1">LORE CONTEXT</div>
                    <div class="text-white/40 text-xs leading-relaxed">{campaign.description}</div>
                  </div>
                {/if}
              </div>
            </div>

            <!-- Actions -->
            <div class="space-y-3">
              <div class="text-white/20 text-xs tracking-widest mb-3">NEXT ACTION 下一步</div>

              <!-- Primary: Start Campaign -->
              <button
                onclick={startCampaign}
                class="action-btn primary w-full px-5 py-4 flex items-center justify-between"
              >
                <div class="text-left">
                  <div class="text-sm tracking-widest">START CAMPAIGN →</div>
                  <div class="text-white/40 text-xs mt-0.5">OPEN GM CHAT // BEGIN SESSION</div>
                </div>
                <span class="display text-2xl opacity-40">▶</span>
              </button>

              <!-- Secondary: View Sessions -->
              <button
                onclick={viewSessions}
                class="action-btn w-full px-5 py-4 flex items-center justify-between"
              >
                <div class="text-left">
                  <div class="text-sm tracking-widest">VIEW SESSIONS</div>
                  <div class="text-white/30 text-xs mt-0.5">MANAGE PAST & UPCOMING SESSIONS</div>
                </div>
                <span class="display text-2xl opacity-30">≡</span>
              </button>

              <!-- Tertiary: Dashboard -->
              <button
                onclick={() => goto('/dashboard')}
                class="action-btn w-full px-5 py-4 flex items-center justify-between"
              >
                <div class="text-left">
                  <div class="text-sm tracking-widest">BACK TO DASHBOARD</div>
                  <div class="text-white/30 text-xs mt-0.5">RETURN TO CAMPAIGNS LIST</div>
                </div>
                <span class="display text-2xl opacity-30">⌂</span>
              </button>
            </div>
          </div>
        {/if}

      </div>

      <!-- ── Right sidebar ── -->
      <div class="w-64 border-l border-white/10 flex flex-col shrink-0 p-5 space-y-6">

        <!-- Status -->
        <div>
          <div class="text-white/20 text-xs tracking-widest mb-3">SYSTEM STATUS</div>
          <div class="space-y-2">
            {#each [
              { label: "GM ENGINE",    ok: true },
              { label: "VECTOR DB",    ok: true },
              { label: "RAG CONTEXT",  ok: true },
              { label: "DICE ENGINE",  ok: true },
              { label: "CAMPAIGN NODE",ok: phase === "created" },
            ] as item}
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full {item.ok ? 'bg-white/60' : 'bg-white/15'}"></div>
                <span class="text-xs {item.ok ? 'text-white/40' : 'text-white/15'}">{item.label}</span>
                <span class="ml-auto text-xs {item.ok ? 'text-white/30' : 'text-white/10'}">
                  {item.ok ? 'OK' : '—'}
                </span>
              </div>
            {/each}
          </div>
        </div>

        <!-- Tips -->
        <div class="rule-h pt-4">
          <div class="text-white/20 text-xs tracking-widest mb-3">TIPS 提示</div>
          <div class="space-y-3">
            {#each [
              "Campaign description is injected as GM world context.",
              "Rulebook embeddings are auto-loaded from the vector DB.",
              "You can add players after creating the campaign.",
              "Session history persists across all game sessions.",
            ] as tip}
              <div class="flex gap-2">
                <span class="text-white/15 text-xs mt-0.5">▸</span>
                <span class="text-white/25 text-xs leading-relaxed">{tip}</span>
              </div>
            {/each}
          </div>
        </div>

        <!-- Atmospheric barcode -->
        <div class="rule-h pt-4 mt-auto">
          <div class="flex gap-px h-12">
            {#each Array(32) as _, i}
              <div class="flex-1 bg-white" style="opacity: {Math.random() > 0.4 ? Math.random() * 0.3 + 0.05 : 0};"></div>
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
        CAMPAIGN FORGE ACTIVE &nbsp;///&nbsp; VECTOR DB SYNCED &nbsp;///&nbsp;
        CLAUDE SONNET CONNECTED &nbsp;///&nbsp;
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