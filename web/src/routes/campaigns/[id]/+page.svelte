<script lang="ts">
  import { onMount } from "svelte"
  import { goto } from "$app/navigation"
  import { page } from "$app/stores"
  import { requireAuth, getToken } from "$lib/auth"

  // ── Types ─────────────────────────────────────────────────
  type SessionStatus = "ACTIVE" | "COMPLETED" | "SCHEDULED"

  interface Session {
    id: string
    name: string
    status: SessionStatus
    created_at: string
    summary?: string
    session_number: number
  }

  interface Campaign {
    id: string
    name: string
    rulebook: string
    description?: string
    max_players: number
    created_at: string
    player_count?: number
  }

  // ── State ─────────────────────────────────────────────────
  let campaign     = $state<Campaign | null>(null)
  let sessions     = $state<Session[]>([])
  let loading      = $state(true)
  let sessionId    = $state("")
  let now          = $state("")
  let hoveredRow   = $state<string | null>(null)
  let creating     = $state(false)
  let newSessionName = $state("")
  let showNewForm  = $state(false)
  let createError  = $state("")
  let scanline     = $state(0)

  // Status config
  const STATUS_META: Record<SessionStatus, { label: string; dot: string; text: string }> = {
    ACTIVE:    { label: "ACTIVE",    dot: "bg-white/80", text: "text-white/80" },
    COMPLETED: { label: "COMPLETED", dot: "bg-white/25", text: "text-white/30" },
    SCHEDULED: { label: "SCHEDULED", dot: "bg-white/10", text: "text-white/15" },
  }

  onMount(async () => {
    requireAuth?.()
    sessionId = Math.random().toString(36).substring(2, 10).toUpperCase()
    now = new Date().toLocaleString("en-GB", { hour12: false }).replace(",", "")

    // Scanline ticker
    setInterval(() => { scanline = (scanline + 1) % 100 }, 80)

    await loadData()
  })

  async function loadData() {
    loading = true
    const id = $page.params.id
    const headers = { Authorization: `Bearer ${getToken()}` }
    try {
      const [cRes, sRes] = await Promise.all([
        fetch(`${import.meta.env.VITE_API_URL}/campaigns/${id}`, { headers }),
        fetch(`${import.meta.env.VITE_API_URL}/campaigns/${id}/sessions`, { headers }),
      ])
      if (!cRes.ok) throw new Error(`Campaign fetch failed: ${cRes.status}`)
      if (!sRes.ok) throw new Error(`Sessions fetch failed: ${sRes.status}`)
      campaign = await cRes.json()
      sessions = await sRes.json()
    } catch (err) {
      console.error(err)
      // Optional: surface error to UI here
    } finally {
      loading = false
    }
  }

  async function createSession() {
    if (!newSessionName.trim()) { createError = "SESSION NAME REQUIRED"; return }
    creating = true
    createError = ""
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/campaigns/${$page.params.id}/sessions`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${getToken()}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ name: newSessionName.trim() }),
        }
      )
      if (!res.ok) throw new Error(`Create session failed: ${res.status}`)
      const newSes: Session = await res.json()
      sessions = [...sessions, newSes]
      newSessionName = ""
      showNewForm = false
    } catch (err) {
      console.error(err)
      createError = "TRANSMISSION FAILED — CHECK CONNECTION"
    } finally {
      creating = false
    }
  }

  function enterSession(ses: Session) {
    goto(`/campaigns/${campaign?.id}/sessions/${ses.id}`)
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", hour12: false })
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

  .ticker { animation: ticker 24s linear infinite; white-space: nowrap; }
  @keyframes ticker { from { transform: translateX(100%); } to { transform: translateX(-100%); } }

  .blink { animation: blink 1.2s step-end infinite; }
  @keyframes blink { 50% { opacity: 0; } }

  .rule-h { border-top: 1px solid rgba(255,255,255,0.1); }
  .rule-v { border-left: 1px solid rgba(255,255,255,0.15); }

  /* Pulse */
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.35; } }
  .pulse { animation: pulse 2s ease-in-out infinite; }

  /* Fade-in for rows */
  @keyframes fadeSlide {
    from { opacity:0; transform: translateX(-8px); }
    to   { opacity:1; transform: translateX(0); }
  }
  .row-in { animation: fadeSlide 0.25s ease forwards; }

  /* Session row */
  .session-row {
    border: 1px solid rgba(255,255,255,0.07);
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
  }
  .session-row:hover {
    border-color: rgba(255,255,255,0.3);
    background: rgba(255,255,255,0.03);
  }
  .session-row.active-session {
    border-color: rgba(255,255,255,0.25);
  }
  .session-row.scheduled {
    opacity: 0.5;
  }

  /* Field input */
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

  .field-wrap {
    border: 1px solid rgba(255,255,255,0.1);
    transition: border-color 0.15s;
  }
  .field-wrap:focus-within { border-color: rgba(255,255,255,0.35); }
  .field-wrap.has-error    { border-color: rgba(255,80,80,0.5); }

  /* Scan anim on hover row */
  .session-row::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.04) 50%, transparent 100%);
    transform: translateX(-100%);
    transition: transform 0.4s ease;
    pointer-events: none;
  }
  .session-row:hover::after { transform: translateX(100%); }

  /* Loading shimmer */
  @keyframes shimmer {
    0%   { background-position: -400px 0; }
    100% { background-position: 400px 0; }
  }
  .shimmer {
    background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.07) 50%, rgba(255,255,255,0.03) 75%);
    background-size: 800px 100%;
    animation: shimmer 1.4s linear infinite;
  }

  .action-btn {
    border: 1px solid rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.4);
    transition: border-color 0.15s, color 0.15s, background 0.15s;
    cursor: pointer;
  }
  .action-btn:hover {
    border-color: rgba(255,255,255,0.7);
    color: #fff;
  }
  .action-btn.primary {
    border-color: rgba(255,255,255,0.5);
    color: rgba(255,255,255,0.85);
  }
  .action-btn.primary:hover {
    background: #fff;
    color: #000;
  }
</style>

<div class="min-h-screen bg-black text-white scanline relative overflow-hidden mono">

  <!-- Grid overlay -->
  <div class="fixed inset-0 pointer-events-none"
    style="background-image: linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
           linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
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
        <span class="text-white/40 text-xs">HTTPS://TTRPG.GM.SYSTEM/CAMPAIGNS/{campaign?.id ?? '...'}</span>
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

    <!-- Breadcrumb bar -->
    <div class="border-b border-white/10 px-12 py-3 flex items-center gap-3">
      <a href="/dashboard" class="text-white/20 text-xs tracking-widest hover:text-white/50 transition-colors">CAMPAIGNS</a>
      <span class="text-white/10 text-xs">/</span>
      <span class="text-white/50 text-xs tracking-widest">
        {#if loading}···{:else}{campaign?.name?.toUpperCase()}{/if}
      </span>
      <span class="text-white/10 text-xs">/</span>
      <span class="text-white/25 text-xs tracking-widest">SESSIONS</span>

      <div class="ml-auto flex items-center gap-4">
        {#if !loading && campaign}
          <span class="text-white/15 text-xs">
            {sessions.filter(s => s.status === 'COMPLETED').length} COMPLETED
            &nbsp;·&nbsp;
            {sessions.filter(s => s.status === 'ACTIVE').length} ACTIVE
            &nbsp;·&nbsp;
            {sessions.filter(s => s.status === 'SCHEDULED').length} SCHEDULED
          </span>
        {/if}
      </div>
    </div>

    <div class="flex-1 flex">

      <!-- ── Main ── -->
      <div class="flex-1 px-12 py-8 space-y-8 min-w-0">

        <!-- ── Campaign Header ── -->
        {#if loading}
          <!-- skeleton -->
          <div class="space-y-3">
            <div class="shimmer h-3 w-32 rounded-none"></div>
            <div class="shimmer h-12 w-80 rounded-none"></div>
          </div>
        {:else if campaign}
          <div class="flex items-start justify-between gap-8">
            <div>
              <div class="text-white/20 text-xs tracking-widest mb-1">CAMPAIGN_NODE // {campaign.id}</div>
              <div class="display text-6xl text-white tracking-wider leading-none">{campaign.name.toUpperCase()}</div>
              <div class="flex items-center gap-5 mt-3">
                <span class="text-white/30 text-xs">SYS: {campaign.rulebook}</span>
                <div class="rule-v h-3"></div>
                <span class="text-white/30 text-xs">SLOTS: {campaign.player_count ?? 0}/{campaign.max_players}</span>
                <div class="rule-v h-3"></div>
                <span class="text-white/30 text-xs">CREATED: {formatDate(campaign.created_at)}</span>
              </div>
            </div>
            <!-- Enter active session shortcut -->
            {#if sessions.some(s => s.status === 'ACTIVE')}
              <button
                onclick={() => { const a = sessions.find(s => s.status === 'ACTIVE'); if(a) enterSession(a) }}
                class="action-btn primary shrink-0 px-5 py-3 flex items-center gap-3 text-sm tracking-widest"
              >
                <span class="pulse">●</span> RESUME ACTIVE SESSION →
              </button>
            {/if}
          </div>

          <!-- Description strip -->
          {#if campaign.description}
            <div class="border border-white/08 bg-white/[0.015] px-5 py-4 flex gap-4 items-start">
              <span class="text-white/15 text-xs shrink-0 mt-0.5">LORE</span>
              <div class="rule-v h-4 mt-0.5 shrink-0"></div>
              <p class="text-white/35 text-xs leading-relaxed">{campaign.description}</p>
            </div>
          {/if}
        {/if}

        <!-- ── Sessions Table ── -->
        <div>
          <!-- Table header -->
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-4">
              <span class="display text-2xl tracking-wider text-white">SESSIONS 會話</span>
              <span class="text-white/20 text-xs border border-white/10 px-2 py-0.5">{sessions.length} TOTAL</span>
            </div>
            <button
              onclick={() => { showNewForm = !showNewForm; createError = "" }}
              class="action-btn primary px-4 py-2 text-xs tracking-widest"
            >
              {showNewForm ? '✕ CANCEL' : '+ NEW SESSION'}
            </button>
          </div>

          <!-- New session form (inline) -->
          {#if showNewForm}
            <div class="border border-white/20 bg-white/[0.02] mb-4 p-5 space-y-4 row-in">
              <div class="text-white/20 text-xs tracking-widest">INITIALIZE SESSION NODE</div>
              <div>
                <div class="text-white/30 text-xs tracking-widest mb-1.5">SESSION NAME *</div>
                <div class="field-wrap {createError ? 'has-error' : ''}">
                  <div class="flex items-center border-b border-white/10 px-3 py-1.5">
                    <span class="text-white/20 text-xs">IDENT:</span>
                  </div>
                  <input
                    type="text"
                    bind:value={newSessionName}
                    placeholder="OPERATION NIGHTFALL"
                    maxlength="80"
                    class="field-input"
                    oninput={() => createError = ""}
                  />
                </div>
                {#if createError}
                  <p class="text-red-400 text-xs mt-1">{createError}</p>
                {/if}
              </div>
              <div class="flex items-center gap-4">
                <button
                  onclick={createSession}
                  disabled={creating}
                  class="border border-white/40 hover:border-white hover:bg-white hover:text-black transition-all px-6 py-2.5 text-xs tracking-widest text-white disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {creating ? 'DEPLOYING...' : 'DEPLOY SESSION →'}
                </button>
                <span class="text-white/15 text-xs">SESSION WILL BE ADDED TO THIS CAMPAIGN</span>
              </div>
            </div>
          {/if}

          <!-- Column headers -->
          <div class="grid grid-cols-[44px_1fr_120px_160px_32px] gap-0 border-b border-white/10 pb-2 mb-1 px-4">
            <span class="text-white/20 text-xs tracking-widest">#</span>
            <span class="text-white/20 text-xs tracking-widest">SESSION IDENT</span>
            <span class="text-white/20 text-xs tracking-widest">STATUS</span>
            <span class="text-white/20 text-xs tracking-widest">DATE</span>
            <span class="text-white/20 text-xs tracking-widest"></span>
          </div>

          <!-- Session rows -->
          {#if loading}
            {#each Array(3) as _, i}
              <div class="shimmer h-16 mb-1" style="animation-delay: {i * 0.1}s"></div>
            {/each}
          {:else if sessions.length === 0}
            <div class="border border-white/08 px-5 py-10 text-center">
              <div class="text-white/20 text-xs tracking-widest mb-2">NO SESSIONS FOUND</div>
              <div class="text-white/10 text-xs">INITIALIZE YOUR FIRST SESSION TO BEGIN</div>
            </div>
          {:else}
            <div class="space-y-1">
              {#each sessions as ses, i}
                {@const meta = STATUS_META[ses.status]}
                <div
                  class="session-row relative grid grid-cols-[44px_1fr_120px_160px_32px] gap-0 items-center px-4 py-4 row-in
                    {ses.status === 'ACTIVE' ? 'active-session' : ''}
                    {ses.status === 'SCHEDULED' ? 'scheduled' : ''}"
                  style="animation-delay: {i * 0.06}s"
                  onclick={() => enterSession(ses)}
                  onmouseenter={() => hoveredRow = ses.id}
                  onmouseleave={() => hoveredRow = null}
                  role="button"
                  tabindex="0"
                  onkeydown={(e) => e.key === 'Enter' && enterSession(ses)}
                >
                  <!-- Number -->
                  <span class="text-white/20 text-xs">{String(ses.session_number).padStart(2,'0')}</span>

                  <!-- Name + summary -->
                  <div class="min-w-0">
                    <div class="flex items-center gap-2">
                      {#if ses.status === 'ACTIVE'}
                        <span class="text-white/60 text-xs pulse">●</span>
                      {/if}
                      <span class="text-white/{ses.status === 'SCHEDULED' ? '30' : '75'} text-sm tracking-wider truncate">
                        {ses.name.toUpperCase()}
                      </span>
                    </div>
                    {#if ses.summary}
                      <p class="text-white/20 text-xs mt-0.5 truncate max-w-md">{ses.summary}</p>
                    {:else if ses.status === 'SCHEDULED'}
                      <p class="text-white/10 text-xs mt-0.5">PENDING INITIALIZATION</p>
                    {/if}
                  </div>

                  <!-- Status badge -->
                  <div class="flex items-center gap-2">
                    <div class="w-1.5 h-1.5 rounded-full {meta.dot}
                      {ses.status === 'ACTIVE' ? 'pulse' : ''}"></div>
                    <span class="text-xs {meta.text} tracking-widest">{meta.label}</span>
                  </div>

                  <!-- Date -->
                  <span class="text-white/20 text-xs">{formatDate(ses.created_at)}</span>

                  <!-- Arrow -->
                  <span class="text-white/20 text-xs transition-all
                    {hoveredRow === ses.id ? 'text-white/60' : ''}">→</span>
                </div>
              {/each}
            </div>
          {/if}
        </div>

      </div>

      <!-- ── Right sidebar ── -->
      <div class="w-64 border-l border-white/10 flex flex-col shrink-0 p-5 space-y-6">

        <!-- Campaign quick stats -->
        <div>
          <div class="text-white/20 text-xs tracking-widest mb-3">CAMPAIGN STATS</div>
          {#if loading}
            {#each Array(4) as _}
              <div class="shimmer h-8 mb-2"></div>
            {/each}
          {:else if campaign}
            <div class="space-y-1">
              {#each [
                { label: "TOTAL SESSIONS",   val: String(sessions.length) },
                { label: "COMPLETED",         val: String(sessions.filter(s=>s.status==='COMPLETED').length) },
                { label: "ACTIVE",            val: String(sessions.filter(s=>s.status==='ACTIVE').length) },
                { label: "SCHEDULED",         val: String(sessions.filter(s=>s.status==='SCHEDULED').length) },
                { label: "PLAYERS",           val: `${campaign.player_count ?? 0} / ${campaign.max_players}` },
              ] as row}
                <div class="flex items-center gap-2 py-1.5 border-b border-white/05">
                  <span class="text-white/20 text-xs flex-1">{row.label}</span>
                  <span class="text-white/50 text-xs">{row.val}</span>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        <!-- System status -->
        <div class="rule-h pt-4">
          <div class="text-white/20 text-xs tracking-widest mb-3">SYSTEM STATUS</div>
          <div class="space-y-2">
            {#each [
              { label: "GM ENGINE",    ok: true },
              { label: "RAG CONTEXT",  ok: true },
              { label: "SESSION MEM",  ok: true },
              { label: "DICE ENGINE",  ok: true },
              { label: "VECTOR DB",    ok: !loading },
            ] as item}
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full {item.ok ? 'bg-white/60' : 'bg-white/15 pulse'}"></div>
                <span class="text-xs {item.ok ? 'text-white/40' : 'text-white/15'}">{item.label}</span>
                <span class="ml-auto text-xs {item.ok ? 'text-white/30' : 'text-white/10'}">
                  {item.ok ? 'OK' : loading ? '···' : '—'}
                </span>
              </div>
            {/each}
          </div>
        </div>

        <!-- Actions -->
        <div class="rule-h pt-4">
          <div class="text-white/20 text-xs tracking-widest mb-3">ACTIONS 動作</div>
          <div class="space-y-2">
            <button
              onclick={() => goto('/campaigns')}
              class="action-btn w-full px-3 py-2.5 text-left text-xs tracking-widest flex items-center justify-between"
            >
              <span>ALL CAMPAIGNS</span>
              <span class="opacity-40">⌂</span>
            </button>
            <button
              onclick={() => goto(`/campaigns/${campaign?.id}/settings`)}
              class="action-btn w-full px-3 py-2.5 text-left text-xs tracking-widest flex items-center justify-between"
            >
              <span>CAMPAIGN SETTINGS</span>
              <span class="opacity-40">⚙</span>
            </button>
            <button
              onclick={() => goto(`/campaigns/${campaign?.id}/players`)}
              class="action-btn w-full px-3 py-2.5 text-left text-xs tracking-widest flex items-center justify-between"
            >
              <span>MANAGE PLAYERS</span>
              <span class="opacity-40">◈</span>
            </button>
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
        CAMPAIGN NODE ACTIVE &nbsp;///&nbsp; SESSION MANAGER READY &nbsp;///&nbsp;
        CLAUDE SONNET CONNECTED &nbsp;///&nbsp; VECTOR DB SYNCED &nbsp;///&nbsp;
      </div>
    </div>
    <div class="h-8 px-6 flex items-center gap-8">
      <span class="mono text-xs text-white/20">NODE [{sessionId}]</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs text-white/20">/CAMPAIGNS/{campaign?.id ?? '...'}/SESSIONS</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs text-white/20 blink">● SESSION MGR</span>
      <div class="ml-auto mono text-xs text-white/20">TTRPG INDUSTRIAL // COPYRIGHT © 2077</div>
    </div>
  </div>

</div>