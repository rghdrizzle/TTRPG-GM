<script lang="ts">
  import { onMount, tick } from "svelte"
  import { page } from "$app/stores"
  import { goto } from "$app/navigation"
  import { requireAuth, getToken } from "$lib/auth"

  // ── Types ────────────────────────────────────────────────
  type Phase = "identity" | "role" | "stats" | "equipment" | "confirm"

  interface Stat {
    key: string
    label: string
    cn: string
    value: number | null
    rolled: boolean
    description: string
  }

  interface InventoryItem {
    name: string
    qty: number
  }

  // ── Params ───────────────────────────────────────────────
  const campaignId = $page.params.id

  // ── Phase ────────────────────────────────────────────────
  let phase = $state<Phase>("identity")
  const PHASES: Phase[] = ["identity", "role", "stats", "equipment", "confirm"]

  // ── Character data ───────────────────────────────────────
  let charName     = $state("")
  let charRole     = $state("")
  let charLevel    = $state(1)
  let charHP       = $state<number | null>(null)
  let charNotes    = $state("")
  let inventory    = $state<InventoryItem[]>([{ name: "", qty: 1 }])
  let newItemName  = $state("")
  let newItemQty   = $state(1)

  let stats = $state<Stat[]>([
    { key: "METAL", label: "METAL", cn: "金屬", value: null, rolled: false, description: "Strength, toughness, physical power" },
    { key: "WIRE",  label: "WIRE",  cn: "電線", value: null, rolled: false, description: "Speed, stealth, precision" },
    { key: "HEART", label: "HEART", cn: "心臟", value: null, rolled: false, description: "Charisma, morale, willpower" },
  ])

  // ── Rulebook data (fetched) ──────────────────────────────
  let roles        = $state<string[]>([])
  let startingGear = $state<string[]>([])
  let loadingRoles = $state(false)

  // ── Dice roller ──────────────────────────────────────────
  let diceType      = $state<4 | 6 | 8 | 10 | 12 | 20>(6)
  let diceResult    = $state<number | null>(null)
  let diceRolling   = $state(false)
  let diceDisplay   = $state("?")
  let diceHistory   = $state<{ notation: string; result: number }[]>([])

  // ── UI ───────────────────────────────────────────────────
  let saving    = $state(false)
  let errors    = $state<Record<string, string>>({})
  let nodeId    = $state("")
  let now       = $state("")

  // ── D6 ASCII faces ───────────────────────────────────────
  const D6_FACES = ["⠀1⠀", "⠀2⠀", "⠀3⠀", "⠀4⠀", "⠀5⠀", "⠀6⠀"]

  // ── Lifecycle ────────────────────────────────────────────
  onMount(async () => {
    requireAuth()
    nodeId = Math.random().toString(36).substring(2, 10).toUpperCase()
    now    = new Date().toLocaleString("en-GB", { hour12: false }).replace(",", "")
    await fetchRulebookOptions()
  })

  // ── Fetch rulebook character options via RAG ─────────────
  async function fetchRulebookOptions() {
    loadingRoles = true
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/campaigns/${campaignId}/rulebook/character-options`,
        { headers: { Authorization: `Bearer ${getToken()}` } }
      )
      if (res.ok) {
        const data = await res.json()
        roles        = data?.payload?.roles        ?? FIST_DEFAULTS.roles
        startingGear = data?.payload?.starting_gear ?? FIST_DEFAULTS.gear
      } else {
        roles        = FIST_DEFAULTS.roles
        startingGear = FIST_DEFAULTS.gear
      }
    } catch {
      roles        = FIST_DEFAULTS.roles
      startingGear = FIST_DEFAULTS.gear
    } finally {
      loadingRoles = false
    }
  }

  // ── FIST defaults (fallback if endpoint not ready) ───────
  const FIST_DEFAULTS = {
    roles: [
      "Assault",
      "Infiltrator",
      "Medic",
      "Demo Expert",
      "Sniper",
      "Hacker",
      "Heavy",
      "Scout",
    ],
    gear: [
      "Combat Knife",
      "9mm Pistol",
      "Flak Jacket",
      "Field Rations x3",
      "Radio",
      "Rope (30m)",
      "Medkit",
      "Flashbang x2",
    ],
  }

  // ── Dice roll ────────────────────────────────────────────
  async function rollDie(sides: number = diceType, targetStat?: string) {
    if (diceRolling) return
    diceRolling = true
    diceResult  = null

    // animate through random numbers
    let ticks = 0
    const maxTicks = 14
    const interval = setInterval(() => {
      diceDisplay = String(Math.ceil(Math.random() * sides))
      ticks++
      if (ticks >= maxTicks) {
        clearInterval(interval)
        const result    = Math.ceil(Math.random() * sides)
        diceDisplay     = String(result)
        diceResult      = result
        diceRolling     = false
        diceHistory     = [{ notation: `1d${sides}`, result }, ...diceHistory.slice(0, 7)]

        // if rolling for a stat, assign it
        if (targetStat) {
          stats = stats.map(s =>
            s.key === targetStat ? { ...s, value: result, rolled: true } : s
          )
          // auto-set HP from METAL if that's what was rolled
          if (targetStat === "METAL") charHP = result + 4
        }
      }
    }, 60)
  }

  function rollAllStats() {
    stats.forEach((s, i) => {
      setTimeout(() => rollDie(6, s.key), i * 800)
    })
  }

  // ── Inventory helpers ────────────────────────────────────
  function addItem() {
    if (!newItemName.trim()) return
    inventory = [...inventory, { name: newItemName.trim(), qty: newItemQty }]
    newItemName = ""
    newItemQty  = 1
  }

  function removeItem(i: number) {
    inventory = inventory.filter((_, idx) => idx !== i)
  }

  function toggleGear(item: string) {
    const exists = inventory.find(i => i.name === item)
    if (exists) {
      inventory = inventory.filter(i => i.name !== item)
    } else {
      inventory = [...inventory, { name: item, qty: 1 }]
    }
  }

  // ── Validation ───────────────────────────────────────────
  function validate(): boolean {
    const e: Record<string, string> = {}
    if (!charName.trim())  e.name = "NAME REQUIRED"
    if (!charRole)         e.role = "SELECT A ROLE"
    if (stats.some(s => s.value === null)) e.stats = "ROLL ALL STATS"
    errors = e
    return Object.keys(e).length === 0
  }

  // ── Save character ───────────────────────────────────────
  async function saveCharacter() {
    if (!validate()) return
    saving = true
    try {
      const payload = {
        campaign_id: campaignId,
        name:        charName.trim(),
        class:       charRole,
        level:       charLevel,
        hp:          charHP,
        stats:       Object.fromEntries(stats.map(s => [s.key, s.value])),
        inventory:   inventory.filter(i => i.name),
        notes:       charNotes,
      }
      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/campaigns/${campaignId}/characters`,
        {
          method:  "POST",
          headers: {
            Authorization:  `Bearer ${getToken()}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      )
      if (res.ok) {
        goto(`/campaigns/${campaignId}/sessions`)
      } else {
        errors.submit = "TRANSMISSION FAILED — RETRY"
      }
    } catch {
      errors.submit = "CONNECTION LOST"
    } finally {
      saving = false
    }
  }

  // ── Phase navigation ─────────────────────────────────────
  function nextPhase() {
    const idx = PHASES.indexOf(phase)
    if (idx < PHASES.length - 1) phase = PHASES[idx + 1]
  }
  function prevPhase() {
    const idx = PHASES.indexOf(phase)
    if (idx > 0) phase = PHASES[idx - 1]
  }

  const PHASE_LABELS: Record<Phase, string> = {
    identity:  "01 IDENTITY",
    role:      "02 ROLE",
    stats:     "03 STATS",
    equipment: "04 GEAR",
    confirm:   "05 CONFIRM",
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
      rgba(255,255,255,0.012) 3px, rgba(255,255,255,0.012) 4px
    );
  }
  .ticker { animation: ticker 24s linear infinite; white-space: nowrap; }
  @keyframes ticker { from { transform:translateX(100%); } to { transform:translateX(-100%); } }
  .blink { animation: blink 1.2s step-end infinite; }
  @keyframes blink { 50% { opacity:0; } }
  .rule-h { border-top: 1px solid rgba(255,255,255,0.1); }
  .rule-v { border-left: 1px solid rgba(255,255,255,0.12); }

  .scroll::-webkit-scrollbar       { width: 2px; }
  .scroll::-webkit-scrollbar-track { background: transparent; }
  .scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); }

  .field {
    border: 1px solid rgba(255,255,255,0.1);
    transition: border-color 0.15s;
  }
  .field:focus-within { border-color: rgba(255,255,255,0.3); }
  .field.err          { border-color: rgba(255,80,80,0.5); }
  .field input, .field select, .field textarea {
    background: transparent; border: none; outline: none;
    width: 100%; color: rgba(255,255,255,0.8);
    font-family: 'Share Tech Mono', monospace; font-size: 13px;
    padding: 10px 14px;
  }
  .field input::placeholder, .field textarea::placeholder { color: rgba(255,255,255,0.15); }
  .field select option { background: #0a0a0a; color: rgba(255,255,255,0.8); }

  /* dice */
  .dice-face {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 64px;
    line-height: 1;
    transition: all 0.06s;
    user-select: none;
  }
  .dice-rolling { animation: shake 0.06s infinite; }
  @keyframes shake {
    0%,100% { transform: translate(0,0) rotate(0deg); }
    25%      { transform: translate(-2px,1px) rotate(-1deg); }
    75%      { transform: translate(2px,-1px) rotate(1deg); }
  }
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
  .pulse { animation: pulse 2s ease-in-out infinite; }

  .action-btn {
    border: 1px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.4);
    transition: border-color 0.15s, color 0.15s, background 0.15s;
    cursor: pointer;
  }
  .action-btn:hover { border-color: rgba(255,255,255,0.45); color: rgba(255,255,255,0.85); }
  .action-btn.primary {
    border-color: rgba(255,255,255,0.35);
    color: rgba(255,255,255,0.85);
  }
  .action-btn.primary:hover { background: #fff; color: #000; }

  .stat-card {
    border: 1px solid rgba(255,255,255,0.08);
    transition: border-color 0.15s;
  }
  .stat-card.rolled { border-color: rgba(255,255,255,0.3); }
  .stat-card:hover  { border-color: rgba(255,255,255,0.2); }

  .gear-item {
    border: 1px solid rgba(255,255,255,0.08);
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
  }
  .gear-item:hover    { border-color: rgba(255,255,255,0.3); }
  .gear-item.selected { border-color: rgba(255,255,255,0.5); background: rgba(255,255,255,0.04); }

  .phase-tab {
    transition: opacity 0.15s, border-color 0.15s;
    cursor: default;
  }
  .phase-tab.active  { opacity: 1; border-bottom: 1px solid rgba(255,255,255,0.6); }
  .phase-tab.done    { opacity: 0.4; }
  .phase-tab.pending { opacity: 0.15; }
</style>

<div class="min-h-screen bg-black text-white scanline mono">

  <!-- Grid overlay -->
  <div class="fixed inset-0 pointer-events-none"
    style="background-image:linear-gradient(rgba(255,255,255,0.025) 1px,transparent 1px),
           linear-gradient(90deg,rgba(255,255,255,0.025) 1px,transparent 1px);
           background-size:60px 60px;">
  </div>

  <!-- ═══ CHROME ═══ -->
  <div class="fixed top-0 left-0 right-0 z-50">

    <div class="bg-[#0a0a0a] border-b border-white/10 px-4 h-9 flex items-center gap-4">
      <div class="flex gap-1.5">
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
      </div>
      <div class="flex-1 bg-black/60 border border-white/10 h-5 flex items-center px-3 max-w-lg">
        <span class="text-white/35 text-xs">HTTPS://TTRPG.GM.SYSTEM/CAMPAIGNS/{campaignId}/CHARACTER/CREATE</span>
      </div>
      <div class="ml-auto flex gap-3">
        <span class="text-white/20 text-xs">□</span>
        <span class="text-white/20 text-xs">—</span>
        <span class="text-white/20 text-xs">✕</span>
      </div>
    </div>

    <div class="bg-black/95 border-b border-white/10 h-10 flex items-center px-6">
      <div class="flex items-center gap-8 flex-1">
        <span class="display text-xl tracking-wider">/CHARACTER</span>
        <div class="rule-v h-5"></div>
        <a href="/dashboard" class="text-xs text-white/30 tracking-widest hover:text-white/55 transition-colors">CAMPAIGNS 戰役</a>
        <a href={`/campaigns/${campaignId}/sessions`} class="text-xs text-white/30 tracking-widest hover:text-white/55 transition-colors">SESSIONS 會話</a>
      </div>
      <div class="flex items-center gap-5">
        <span class="text-xs text-white/25">NODE [{nodeId}]</span>
        <button
          onclick={() => goto(`/campaigns/${campaignId}/sessions`)}
          class="text-xs text-white/30 tracking-widest hover:text-white transition-colors border border-white/10 hover:border-white/35 px-3 py-1">
          ← EXIT 退出
        </button>
      </div>
    </div>

    <!-- Ruler -->
    <div class="bg-black border-b border-white/10 h-4 flex items-end px-6 overflow-hidden">
      {#each Array(40) as _, i}
        <div class="flex-1 flex items-end justify-center">
          <div class="w-px bg-white" style="height:{i % 5 === 0 ? 8 : 4}px; opacity:{i % 5 === 0 ? 0.18 : 0.07};"></div>
        </div>
      {/each}
    </div>

    <!-- Phase tabs -->
    <div class="bg-black border-b border-white/10 h-9 flex items-center px-6 gap-8">
      {#each PHASES as p}
        {@const idx     = PHASES.indexOf(p)}
        {@const curIdx  = PHASES.indexOf(phase)}
        {@const status  = idx === curIdx ? "active" : idx < curIdx ? "done" : "pending"}
        <div class="phase-tab {status} pb-1 flex items-center gap-2">
          <span class="text-xs tracking-widest" style="color:rgba(255,255,255,{status==='active'?0.85:status==='done'?0.4:0.15});">
            {PHASE_LABELS[p]}
          </span>
          {#if status === "done"}
            <span class="text-white/30 text-xs">✓</span>
          {/if}
        </div>
      {/each}
    </div>
  </div>

  <!-- ═══ BODY ═══ -->
  <!-- top: chrome(88) + phase bar(37) = 125px -->
  <div class="fixed left-0 right-0 flex" style="top:125px; bottom:56px;">

    <!-- ── MAIN CONTENT ── -->
    <div class="flex-1 overflow-y-auto scroll">
      <div class="px-10 py-8 max-w-2xl">

        <!-- ══ PHASE: IDENTITY ══ -->
        {#if phase === "identity"}
          <div class="mb-7">
            <div class="text-white/20 text-xs tracking-widest mb-1">STEP 01 // FORGE YOUR IDENTITY</div>
            <div class="display text-5xl leading-none text-white">WHO ARE<br>YOU?</div>
            <div class="display text-5xl leading-none text-white/10">身份認同</div>
          </div>

          <div class="space-y-5">
            <div>
              <div class="text-white/30 text-xs tracking-widest mb-1.5">OPERATIVE NAME <span class="text-white/15">*</span></div>
              <div class="field {errors.name ? 'err' : ''}">
                <input type="text" bind:value={charName} placeholder="YOUR CALLSIGN" maxlength="40"
                  oninput={() => delete errors.name} />
              </div>
              {#if errors.name}<p class="text-red-400 text-xs mt-1">{errors.name}</p>{/if}
            </div>

            <div>
              <div class="text-white/30 text-xs tracking-widest mb-1.5">LEVEL</div>
              <div class="flex gap-2">
                {#each [1,2,3,4,5] as lvl}
                  <button onclick={() => charLevel = lvl}
                    class="w-10 h-10 border text-xs transition-all
                      {charLevel === lvl
                        ? 'border-white/50 text-white bg-white/8'
                        : 'border-white/10 text-white/30 hover:border-white/25'}">
                    {lvl}
                  </button>
                {/each}
              </div>
            </div>

            <div>
              <div class="text-white/30 text-xs tracking-widest mb-1.5">OPERATIVE NOTES <span class="text-white/15">OPTIONAL</span></div>
              <div class="field">
                <textarea bind:value={charNotes} rows="3"
                  placeholder="BACKSTORY, MOTIVATIONS, SCARS, ALLEGIANCES..."></textarea>
              </div>
              <p class="text-white/15 text-xs mt-1">INJECTED INTO GM CONTEXT AS CHARACTER BACKGROUND</p>
            </div>
          </div>

        <!-- ══ PHASE: ROLE ══ -->
        {:else if phase === "role"}
          <div class="mb-7">
            <div class="text-white/20 text-xs tracking-widest mb-1">STEP 02 // CHOOSE YOUR ROLE</div>
            <div class="display text-5xl leading-none text-white">YOUR<br>SPECIALIZATION</div>
            <div class="display text-5xl leading-none text-white/10">職業選擇</div>
          </div>

          {#if loadingRoles}
            <div class="text-white/20 text-xs blink">QUERYING RULEBOOK_</div>
          {:else}
            <div class="space-y-2">
              {#each roles as role}
                <button
                  onclick={() => { charRole = role; delete errors.role }}
                  class="w-full border px-5 py-3 text-left transition-all flex items-center justify-between
                    {charRole === role
                      ? 'border-white/50 bg-white/5 text-white'
                      : 'border-white/10 text-white/40 hover:border-white/30 hover:text-white/70'}">
                  <span class="mono text-sm tracking-widest">{role.toUpperCase()}</span>
                  {#if charRole === role}
                    <span class="text-white/40 text-xs">SELECTED ✓</span>
                  {/if}
                </button>
              {/each}
            </div>
            {#if errors.role}<p class="text-red-400 text-xs mt-3">{errors.role}</p>{/if}
          {/if}

        <!-- ══ PHASE: STATS ══ -->
        {:else if phase === "stats"}
          <div class="mb-7">
            <div class="text-white/20 text-xs tracking-widest mb-1">STEP 03 // ROLL YOUR STATS</div>
            <div class="display text-5xl leading-none text-white">ATTRIBUTE<br>ASSIGNMENT</div>
            <div class="display text-5xl leading-none text-white/10">屬性分配</div>
          </div>

          <div class="mb-5">
            <button onclick={rollAllStats}
              class="action-btn primary px-6 py-2.5 text-xs tracking-widest">
              ⚄ ROLL ALL STATS (3×1d6)
            </button>
          </div>

          <div class="space-y-3">
            {#each stats as stat}
              <div class="stat-card {stat.rolled ? 'rolled' : ''} p-5 flex items-center gap-6">

                <!-- Stat name -->
                <div class="w-24 shrink-0">
                  <div class="display text-2xl text-white tracking-wider">{stat.label}</div>
                  <div class="text-white/25 text-xs">{stat.cn}</div>
                  <div class="text-white/20 text-xs mt-1 leading-relaxed">{stat.description}</div>
                </div>

                <!-- Value display -->
                <div class="flex-1 flex items-center gap-4">
                  <div class="display text-5xl {stat.rolled ? 'text-white' : 'text-white/15'} w-12 text-center">
                    {stat.value ?? "—"}
                  </div>
                  {#if stat.rolled}
                    <div class="flex gap-px h-8">
                      {#each Array(stat.value ?? 0) as _}
                        <div class="w-3 bg-white/60"></div>
                      {/each}
                      {#each Array(6 - (stat.value ?? 0)) as _}
                        <div class="w-3 bg-white/10"></div>
                      {/each}
                    </div>
                  {/if}
                </div>

                <!-- Roll button -->
                <button
                  onclick={() => rollDie(6, stat.key)}
                  disabled={diceRolling}
                  class="action-btn px-4 py-2 text-xs tracking-widest shrink-0 disabled:opacity-30">
                  {stat.rolled ? "REROLL" : "ROLL 1d6"}
                </button>

              </div>
            {/each}
          </div>

          {#if stats.every(s => s.rolled)}
            <div class="mt-5 border border-white/15 px-4 py-3">
              <div class="text-white/20 text-xs tracking-widest mb-1">HP CALCULATION</div>
              <div class="flex items-center gap-4">
                <div class="display text-3xl text-white">{charHP ?? "—"}</div>
                <div class="text-white/30 text-xs">METAL ({stats.find(s=>s.key==="METAL")?.value}) + 4</div>
              </div>
            </div>
          {/if}

          {#if errors.stats}<p class="text-red-400 text-xs mt-3">{errors.stats}</p>{/if}

        <!-- ══ PHASE: EQUIPMENT ══ -->
        {:else if phase === "equipment"}
          <div class="mb-7">
            <div class="text-white/20 text-xs tracking-widest mb-1">STEP 04 // LOAD YOUR KIT</div>
            <div class="display text-5xl leading-none text-white">GEAR &amp;<br>INVENTORY</div>
            <div class="display text-5xl leading-none text-white/10">裝備清單</div>
          </div>

          <!-- Starting gear from rulebook -->
          <div class="mb-6">
            <div class="text-white/30 text-xs tracking-widest mb-3">STARTING GEAR — SELECT WHAT YOU CARRY</div>
            <div class="grid grid-cols-2 gap-1.5">
              {#each startingGear as item}
                <button
                  onclick={() => toggleGear(item)}
                  class="gear-item {inventory.find(i=>i.name===item) ? 'selected' : ''} px-4 py-2.5 text-left flex items-center gap-3">
                  <div class="w-3 h-3 border {inventory.find(i=>i.name===item) ? 'border-white/60 bg-white/20' : 'border-white/15'}"></div>
                  <span class="text-xs tracking-widest">{item}</span>
                </button>
              {/each}
            </div>
          </div>

          <!-- Custom item add -->
          <div class="mb-4">
            <div class="text-white/30 text-xs tracking-widest mb-2">ADD CUSTOM ITEM</div>
            <div class="flex gap-2">
              <div class="field flex-1">
                <input type="text" bind:value={newItemName} placeholder="ITEM NAME"
                  onkeydown={(e) => e.key === "Enter" && addItem()} />
              </div>
              <div class="field w-20">
                <input type="number" bind:value={newItemQty} min="1" max="99" />
              </div>
              <button onclick={addItem} class="action-btn px-4 text-xs tracking-widest">ADD</button>
            </div>
          </div>

          <!-- Inventory list -->
          {#if inventory.filter(i=>i.name).length > 0}
            <div class="border border-white/10">
              <div class="border-b border-white/10 px-4 py-2 flex items-center justify-between">
                <span class="text-white/20 text-xs tracking-widest">CURRENT INVENTORY</span>
                <span class="text-white/40 text-xs">{inventory.filter(i=>i.name).length} ITEMS</span>
              </div>
              {#each inventory.filter(i=>i.name) as item, idx}
                <div class="flex items-center gap-4 px-4 py-2.5 border-b border-white/8 last:border-0">
                  <span class="flex-1 text-xs text-white/60 tracking-widest">{item.name.toUpperCase()}</span>
                  <span class="text-white/30 text-xs w-8 text-center">x{item.qty}</span>
                  <button onclick={() => removeItem(idx)}
                    class="text-white/20 hover:text-white/60 transition-colors text-xs">✕</button>
                </div>
              {/each}
            </div>
          {/if}

        <!-- ══ PHASE: CONFIRM ══ -->
        {:else if phase === "confirm"}
          <div class="mb-7">
            <div class="text-white/20 text-xs tracking-widest mb-1">STEP 05 // CONFIRM &amp; DEPLOY</div>
            <div class="display text-5xl leading-none text-white">OPERATIVE<br>BRIEF</div>
            <div class="display text-5xl leading-none text-white/10">部署確認</div>
          </div>

          {#if errors.submit}
            <div class="mb-5 border border-red-500/30 bg-red-500/5 px-4 py-3">
              <span class="text-red-400 text-xs">{errors.submit}</span>
            </div>
          {/if}

          <!-- Character sheet preview -->
          <div class="border border-white/15 mb-6">
            <div class="border-b border-white/10 px-5 py-3 flex items-center justify-between">
              <span class="text-white/20 text-xs tracking-widest">CHARACTER SHEET PREVIEW</span>
              <span class="text-white/40 text-xs pulse">● READY TO DEPLOY</span>
            </div>

            <div class="p-5 grid grid-cols-2 gap-5">
              <div>
                <div class="text-white/20 text-xs mb-1">OPERATIVE</div>
                <div class="display text-3xl text-white tracking-wider">{charName.toUpperCase()}</div>
              </div>
              <div>
                <div class="text-white/20 text-xs mb-1">ROLE</div>
                <div class="display text-3xl text-white tracking-wider">{charRole.toUpperCase()}</div>
              </div>
              <div>
                <div class="text-white/20 text-xs mb-1">LEVEL</div>
                <div class="display text-2xl text-white">{charLevel}</div>
              </div>
              <div>
                <div class="text-white/20 text-xs mb-1">HP</div>
                <div class="display text-2xl text-white">{charHP}</div>
              </div>
            </div>

            <div class="rule-h px-5 py-4 grid grid-cols-3 gap-4">
              {#each stats as stat}
                <div class="text-center">
                  <div class="text-white/20 text-xs mb-1">{stat.label}</div>
                  <div class="display text-3xl text-white">{stat.value}</div>
                </div>
              {/each}
            </div>

            {#if inventory.filter(i=>i.name).length > 0}
              <div class="rule-h px-5 py-4">
                <div class="text-white/20 text-xs mb-2">INVENTORY ({inventory.filter(i=>i.name).length} ITEMS)</div>
                <div class="flex flex-wrap gap-2">
                  {#each inventory.filter(i=>i.name) as item}
                    <span class="border border-white/15 px-2 py-0.5 text-xs text-white/50">{item.name}</span>
                  {/each}
                </div>
              </div>
            {/if}
          </div>

          <button
            onclick={saveCharacter}
            disabled={saving}
            class="action-btn primary w-full py-4 text-sm tracking-widest flex items-center justify-center gap-3">
            {#if saving}
              <span class="blink">DEPLOYING OPERATIVE_</span>
            {:else}
              DEPLOY OPERATIVE →
            {/if}
          </button>
        {/if}

        <!-- Phase nav buttons -->
        <div class="flex items-center gap-4 mt-8 rule-h pt-6">
          {#if phase !== "identity"}
            <button onclick={prevPhase} class="action-btn px-5 py-2.5 text-xs tracking-widest">
              ← BACK
            </button>
          {/if}
          {#if phase !== "confirm"}
            <button onclick={nextPhase} class="action-btn primary px-5 py-2.5 text-xs tracking-widest ml-auto">
              NEXT →
            </button>
          {/if}
        </div>

      </div>
    </div>

    <!-- ── RIGHT SIDEBAR: DICE ── -->
    <div class="w-56 border-l border-white/10 flex flex-col shrink-0">

      <!-- Dice roller -->
      <div class="p-5 border-b border-white/10">
        <div class="text-white/20 text-xs tracking-widest mb-4">DICE ROLLER 骰子</div>

        <!-- Dice face display -->
        <div class="border border-white/15 mb-4 flex items-center justify-center py-4 relative overflow-hidden"
          style="min-height: 110px;">
          <div class="text-white/5 absolute inset-0 flex items-center justify-center"
            style="font-size:120px; font-family:'Bebas Neue',sans-serif; line-height:1;">
            {diceType}
          </div>
          <div class="dice-face {diceRolling ? 'dice-rolling' : ''} relative z-10
            {diceResult !== null && !diceRolling ? 'text-white' : 'text-white/40'}">
            {diceDisplay}
          </div>
        </div>

        <!-- Die type selector -->
        <div class="grid grid-cols-3 gap-1 mb-3">
          {#each [4,6,8,10,12,20] as d}
            <button onclick={() => diceType = d}
              class="border py-1.5 text-xs tracking-widest transition-all
                {diceType === d
                  ? 'border-white/50 text-white bg-white/8'
                  : 'border-white/10 text-white/30 hover:border-white/25'}">
              d{d}
            </button>
          {/each}
        </div>

        <button onclick={() => rollDie(diceType)} disabled={diceRolling}
          class="action-btn primary w-full py-2.5 text-xs tracking-widest disabled:opacity-30">
          {diceRolling ? "ROLLING..." : `ROLL 1d${diceType}`}
        </button>
      </div>

      <!-- Roll history -->
      <div class="p-5 flex-1 overflow-y-auto scroll">
        <div class="text-white/20 text-xs tracking-widest mb-3">ROLL LOG 記錄</div>
        {#if diceHistory.length === 0}
          <div class="text-white/15 text-xs">NO ROLLS YET</div>
        {:else}
          <div class="space-y-1.5">
            {#each diceHistory as roll, i}
              <div class="flex items-center justify-between border-b border-white/8 pb-1.5"
                style="opacity:{1 - i * 0.1}">
                <span class="text-white/30 text-xs">{roll.notation}</span>
                <span class="display text-lg text-white">{roll.result}</span>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Barcode -->
      <div class="p-4 border-t border-white/10">
        <div class="flex gap-px h-8">
          {#each Array(30) as _, i}
            <div class="flex-1 bg-white"
              style="opacity:{Math.random() > 0.4 ? Math.random() * 0.35 + 0.08 : 0};">
            </div>
          {/each}
        </div>
        <div class="text-white/12 text-xs mt-1 tracking-widest">CHAR-FORGE-SYS</div>
      </div>

    </div>
  </div>

  <!-- ═══ FOOTER ═══ -->
  <div class="fixed bottom-0 left-0 right-0 bg-black border-t border-white/10 z-50 h-14">
    <div class="border-b border-white/10 h-6 overflow-hidden flex items-center">
      <div class="ticker mono text-xs text-white/18">
        TTRPG-GM-SYSTEM &nbsp;///&nbsp; CHARACTER FORGE ONLINE &nbsp;///&nbsp;
        RULEBOOK LOADED &nbsp;///&nbsp; DICE ENGINE READY &nbsp;///&nbsp;
        FIST TTRPG // OPERATIVE CREATION &nbsp;///&nbsp;
      </div>
    </div>
    <div class="h-8 px-6 flex items-center gap-6">
      <div class="flex gap-px h-3.5">
        {#each Array(28) as _, i}
          <div class="w-px bg-white" style="opacity:{Math.random() > 0.5 ? 0.22 : 0.06};"></div>
        {/each}
      </div>
      <span class="mono text-xs text-white/20">NODE [{nodeId}]</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs text-white/20">PHASE: {PHASE_LABELS[phase]}</span>
      <div class="rule-v h-4"></div>
      {#if diceResult !== null}
        <span class="mono text-xs text-white/40">LAST ROLL: {diceResult}</span>
      {/if}
      <div class="ml-auto mono text-xs text-white/18">TTRPG INDUSTRIAL // COPYRIGHT © 2077</div>
    </div>
  </div>

</div>