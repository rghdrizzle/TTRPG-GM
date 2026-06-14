<script lang="ts">
  import { onMount } from "svelte"
  import { page } from "$app/stores"
  import { goto } from "$app/navigation"
  import { requireAuth, getToken } from "$lib/auth"

  // ── Params ───────────────────────────────────────────────
  // route: /campaigns/[id]/sessions/[session_id]/rooms/[room_id]
  const campaignId = $page.params.id
  const sessionId = $page.params.session_id

  // ── State ────────────────────────────────────────────────
  let loading       = $state(true)
  let checking      = $state(false)
  let creating      = $state(false)
  let error         = $state("")
  let existingRoom  = $state<any>(null)
  let sessionName   = $state("")
  let nodeId        = $state(Math.random().toString(36).substring(2, 10).toUpperCase())

  // Join-by-code state (lifted out of snippet — snippets can't hold $state)
  let joinCode      = $state("")
  let joinJoining   = $state(false)
  let joinErr       = $state("")

  // ── Lifecycle ────────────────────────────────────────────
  onMount(async () => {
    requireAuth()
    await checkExistingRoom()
    loading = false
  })

  // ── Check if a room already exists for this session ──────
  async function checkExistingRoom() {
    checking = true
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/sessions/${sessionId}/room`,
        { headers: { Authorization: `Bearer ${getToken()}` } }
      )
      if (res.ok) {
        const data = await res.json()
        existingRoom  = data?.payload?.room ?? null
        sessionName   = data?.payload?.session_name ?? sessionId
      }
    } catch {
      // no room found — that is fine
    } finally {
      checking = false
    }
  }

  // ── Go solo ──────────────────────────────────────────────
  function playSolo() {
    goto(`/campaigns/${campaignId}/sessions/${sessionId}/chat`)
  }

  // ── Go to existing room ──────────────────────────────────
  function joinExistingRoom() {
    goto(`/rooms/${existingRoom.id}`)
  }

  // ── Create new room ──────────────────────────────────────
  async function createRoom() {
    creating = true
    error    = ""
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/rooms`,
        {
          method:  "POST",
          headers: {
            Authorization:  `Bearer ${getToken()}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ session_id: sessionId }),
        }
      )
      if (!res.ok) {
        error = "ROOM CREATION FAILED — CHECK CONNECTION"
        return
      }
      const data = await res.json()
      const roomId = data?.payload?.room?.id
      if (roomId) goto(`/rooms/${roomId}`)
      else error = "INVALID RESPONSE FROM SERVER"
    } catch {
      error = "CONNECTION LOST — RETRY"
    } finally {
      creating = false
    }
  }

  // ── Join room by invite code ──────────────────────────────
  async function joinByCode() {
    if (!joinCode.trim()) return
    joinJoining = true
    joinErr     = ""
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/rooms/join/${joinCode.trim()}`,
        { method: "POST", headers: { Authorization: `Bearer ${getToken()}` } }
      )
      if (res.ok) {
        const d = await res.json()
        goto(`/rooms/${d?.payload?.room?.id}`)
      } else {
        joinErr = "INVALID CODE"
      }
    } catch {
      joinErr = "CONNECTION LOST — RETRY"
    } finally {
      joinJoining = false
    }
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
  @keyframes ticker { from { transform: translateX(100%); } to { transform: translateX(-100%); } }
  .blink { animation: blink 1.2s step-end infinite; }
  @keyframes blink { 50% { opacity: 0; } }
  .rule-h { border-top: 1px solid rgba(255,255,255,0.1); }
  .rule-v { border-left: 1px solid rgba(255,255,255,0.12); }
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
  .pulse { animation: pulse 2s ease-in-out infinite; }

  /* choice cards */
  .choice-card {
    border: 1px solid rgba(255,255,255,0.1);
    transition: border-color 0.2s, background 0.2s, transform 0.15s;
    cursor: pointer;
    position: relative;
    overflow: hidden;
  }
  .choice-card:hover {
    border-color: rgba(255,255,255,0.45);
    background: rgba(255,255,255,0.03);
    transform: translateY(-1px);
  }
  .choice-card:active { transform: translateY(0); }
  .choice-card.disabled {
    opacity: 0.4;
    cursor: not-allowed;
    pointer-events: none;
  }
  .choice-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 60%);
    pointer-events: none;
  }
  .card-accent {
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
  }
  .solo-accent    { background: linear-gradient(to bottom, rgba(255,255,255,0.6), rgba(255,255,255,0.1)); }
  .multi-accent   { background: linear-gradient(to bottom, rgba(255,255,255,0.4), rgba(255,255,255,0.05)); }
  .room-accent    { background: linear-gradient(to bottom, rgba(255,255,255,0.8), rgba(255,255,255,0.2)); }

  .shimmer {
    background: linear-gradient(90deg,
      rgba(255,255,255,0.03) 25%,
      rgba(255,255,255,0.07) 50%,
      rgba(255,255,255,0.03) 75%
    );
    background-size: 800px 100%;
    animation: shimmer 1.4s linear infinite;
  }
  @keyframes shimmer {
    0%   { background-position: -400px 0; }
    100% { background-position: 400px 0; }
  }
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
        <span class="text-white/35 text-xs truncate">
          HTTPS://TTRPG.GM.SYSTEM/CAMPAIGNS/{campaignId}/SESSIONS/{sessionId}/PLAY
        </span>
      </div>
      <div class="ml-auto flex gap-3">
        <span class="text-white/20 text-xs">□</span>
        <span class="text-white/20 text-xs">—</span>
        <span class="text-white/20 text-xs">✕</span>
      </div>
    </div>

    <div class="bg-black/95 border-b border-white/10 h-10 flex items-center px-6">
      <div class="flex items-center gap-8 flex-1">
        <span class="display text-xl tracking-wider">/DEPLOY</span>
        <div class="rule-v h-5"></div>
        <a href="/dashboard" class="text-xs text-white/30 tracking-widest hover:text-white/55 transition-colors">CAMPAIGNS 戰役</a>
        <a href={`/campaigns/${campaignId}/sessions`} class="text-xs text-white/30 tracking-widest hover:text-white/55 transition-colors">SESSIONS 會話</a>
      </div>
      <div class="flex items-center gap-5">
        <span class="text-xs text-white/25">NODE [{nodeId}]</span>
        <button
          onclick={() => goto(`/campaigns/${campaignId}/sessions`)}
          class="text-xs text-white/30 hover:text-white transition-colors border border-white/10 hover:border-white/35 px-3 py-1 tracking-widest">
          ← EXIT 退出
        </button>
      </div>
    </div>

    <div class="bg-black border-b border-white/10 h-4 flex items-end px-6 overflow-hidden">
      {#each Array(40) as _, i}
        <div class="flex-1 flex items-end justify-center">
          <div class="w-px bg-white" style="height:{i % 5 === 0 ? 8 : 4}px; opacity:{i % 5 === 0 ? 0.18 : 0.07};"></div>
        </div>
      {/each}
    </div>
  </div>

  <!-- ═══ MAIN ═══ -->
  <div class="pt-[88px] pb-20 min-h-screen flex flex-col">
    <div class="flex-1 flex flex-col items-center justify-center px-6 py-12">
      <div class="w-full max-w-2xl">

        <!-- Header -->
        <div class="text-center mb-12">
          <div class="text-white/20 text-xs tracking-[0.4em] mb-3">SESSION DEPLOYMENT // SELECT MODE</div>
          <div class="display text-[72px] leading-none text-white">HOW WILL</div>
          <div class="display text-[72px] leading-none text-white">YOU PLAY?</div>
          <div class="display text-[72px] leading-none text-white/8">遊玩模式</div>
          {#if sessionName}
            <div class="mt-4 inline-flex items-center gap-2 border border-white/15 px-4 py-1.5">
              <div class="w-1.5 h-1.5 rounded-full bg-white/50 pulse"></div>
              <span class="text-white/50 text-xs tracking-widest">{sessionId.toUpperCase()}</span>
            </div>
          {/if}
        </div>

        {#if loading}
          <!-- Loading state -->
          <div class="flex flex-col gap-3">
            <div class="shimmer h-48 rounded-sm"></div>
            <div class="shimmer h-48 rounded-sm"></div>
          </div>

        {:else}
          <!-- Error -->
          {#if error}
            <div class="mb-6 border border-red-500/30 bg-red-500/5 px-4 py-3 text-center">
              <span class="text-red-400 text-xs">[ERR] {error}</span>
            </div>
          {/if}

          <div class="flex flex-col gap-4">

            <!-- ── SOLO CARD ── -->
            <button
              onclick={playSolo}
              class="choice-card text-left p-0"
            >
              <div class="card-accent solo-accent"></div>
              <div class="pl-8 pr-6 py-7">
                <div class="flex items-start justify-between mb-4">
                  <div>
                    <div class="text-white/20 text-xs tracking-widest mb-2">MODE_01 // SINGLE PLAYER</div>
                    <div class="display text-4xl text-white tracking-wider leading-none">SOLO</div>
                    <div class="display text-4xl text-white/10 leading-none">獨自</div>
                  </div>
                  <div class="display text-6xl text-white/10 leading-none">01</div>
                </div>

                <div class="rule-h pt-4 grid grid-cols-3 gap-4">
                  <div>
                    <div class="text-white/20 text-xs mb-1">PLAYERS</div>
                    <div class="display text-2xl text-white">1</div>
                  </div>
                  <div>
                    <div class="text-white/20 text-xs mb-1">ROOM</div>
                    <div class="display text-2xl text-white/30">NONE</div>
                  </div>
                  <div>
                    <div class="text-white/20 text-xs mb-1">LATENCY</div>
                    <div class="display text-2xl text-white">ZERO</div>
                  </div>
                </div>

                <div class="mt-4 flex items-center justify-between">
                  <p class="text-white/25 text-xs leading-relaxed max-w-sm">
                    Direct SSE stream to the GM. Fastest response. No room overhead.
                    Full access to character sheet and session history.
                  </p>
                  <div class="display text-2xl text-white/30">→</div>
                </div>
              </div>
            </button>

            <!-- ── MULTIPLAYER CARD ── -->
            {#if existingRoom}

              <!-- Room already exists — join it -->
              <button
                onclick={joinExistingRoom}
                class="choice-card text-left p-0"
              >
                <div class="card-accent room-accent"></div>
                <div class="pl-8 pr-6 py-7">
                  <div class="flex items-start justify-between mb-4">
                    <div>
                      <div class="text-white/20 text-xs tracking-widest mb-2">MODE_02 // ACTIVE ROOM FOUND</div>
                      <div class="display text-4xl text-white tracking-wider leading-none">JOIN ROOM</div>
                      <div class="display text-4xl text-white/10 leading-none">加入房間</div>
                    </div>
                    <div class="flex items-center gap-2">
                      <div class="w-2 h-2 rounded-full bg-white pulse"></div>
                      <span class="text-white/50 text-xs">ACTIVE</span>
                    </div>
                  </div>

                  <div class="rule-h pt-4 grid grid-cols-3 gap-4">
                    <div>
                      <div class="text-white/20 text-xs mb-1">ROOM CODE</div>
                      <div class="display text-2xl text-white tracking-widest">{existingRoom.invite_code}</div>
                    </div>
                    <div>
                      <div class="text-white/20 text-xs mb-1">PLAYERS</div>
                      <div class="display text-2xl text-white">{existingRoom.player_count ?? "—"}</div>
                    </div>
                    <div>
                      <div class="text-white/20 text-xs mb-1">STATUS</div>
                      <div class="display text-2xl text-white">{existingRoom.status ?? "WAITING"}</div>
                    </div>
                  </div>

                  <div class="mt-4 flex items-center justify-between">
                    <p class="text-white/25 text-xs leading-relaxed max-w-sm">
                      A room for this session already exists.
                      Join to play with others using code <span class="text-white/50">{existingRoom.invite_code}</span>.
                    </p>
                    <div class="display text-2xl text-white/30">→</div>
                  </div>
                </div>
              </button>

            {:else}

              <!-- No room — create one -->
              <button
                onclick={createRoom}
                disabled={creating}
                class="choice-card text-left p-0 {creating ? 'disabled' : ''}"
              >
                <div class="card-accent multi-accent"></div>
                <div class="pl-8 pr-6 py-7">
                  <div class="flex items-start justify-between mb-4">
                    <div>
                      <div class="text-white/20 text-xs tracking-widest mb-2">MODE_02 // MULTI PLAYER</div>
                      <div class="display text-4xl text-white tracking-wider leading-none">
                        {#if creating}
                          <span class="blink">CREATING_</span>
                        {:else}
                          CREATE ROOM
                        {/if}
                      </div>
                      <div class="display text-4xl text-white/10 leading-none">多人遊玩</div>
                    </div>
                    <div class="display text-6xl text-white/10 leading-none">02</div>
                  </div>

                  <div class="rule-h pt-4 grid grid-cols-3 gap-4">
                    <div>
                      <div class="text-white/20 text-xs mb-1">MAX PLAYERS</div>
                      <div class="display text-2xl text-white">6</div>
                    </div>
                    <div>
                      <div class="text-white/20 text-xs mb-1">INVITE</div>
                      <div class="display text-2xl text-white">CODE</div>
                    </div>
                    <div>
                      <div class="text-white/20 text-xs mb-1">BROADCAST</div>
                      <div class="display text-2xl text-white">WS</div>
                    </div>
                  </div>

                  <div class="mt-4 flex items-center justify-between">
                    <p class="text-white/25 text-xs leading-relaxed max-w-sm">
                      Create a room and get an invite code to share.
                      All players see GM narration live via WebSocket.
                    </p>
                    <div class="display text-2xl text-white/30">→</div>
                  </div>
                </div>
              </button>

            {/if}

          </div>

          <!-- ── JOIN BY CODE ── -->
          <div class="mt-6 border-t border-white/8 pt-6">
            <div class="flex items-center gap-3">
              <span class="text-white/20 text-xs tracking-widest whitespace-nowrap">JOIN BY CODE 加入</span>
              <div class="flex gap-2 flex-1">
                <div class="flex-1 border border-white/10 focus-within:border-white/30 transition-colors">
                  <input
                    type="text"
                    bind:value={joinCode}
                    placeholder="ENTER INVITE CODE"
                    maxlength="8"
                    onkeydown={(e) => e.key === "Enter" && joinByCode()}
                    class="w-full bg-transparent px-4 py-2.5 text-xs text-white/70 mono placeholder-white/15"
                    style="outline:none; text-transform:uppercase;"
                  />
                </div>
                <button
                  disabled={!joinCode.trim() || joinJoining}
                  onclick={joinByCode}
                  class="border border-white/15 hover:border-white hover:bg-white hover:text-black
                         disabled:opacity-20 disabled:cursor-not-allowed
                         transition-all px-5 py-2.5 text-xs tracking-widest text-white mono">
                  {joinJoining ? "..." : "JOIN →"}
                </button>
              </div>
              {#if joinErr}
                <span class="text-red-400 text-xs">{joinErr}</span>
              {/if}
            </div>
          </div>

        {/if}

      </div>
    </div>
  </div>

  <!-- ═══ FOOTER ═══ -->
  <div class="fixed bottom-0 left-0 right-0 bg-black border-t border-white/10 z-50 h-14">
    <div class="border-b border-white/10 h-6 overflow-hidden flex items-center">
      <div class="ticker mono text-xs text-white/18">
        TTRPG-GM-SYSTEM &nbsp;///&nbsp; SESSION DEPLOYMENT &nbsp;///&nbsp;
        SOLO OR MULTIPLAYER &nbsp;///&nbsp; WEBSOCKET ROOMS &nbsp;///&nbsp;
        GM AI ONLINE &nbsp;///&nbsp; RAG ENABLED &nbsp;///&nbsp;
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
      <span class="mono text-xs text-white/20">SESSION // {sessionId.slice(0,8).toUpperCase()}</span>
      <div class="ml-auto mono text-xs text-white/18">TTRPG INDUSTRIAL // COPYRIGHT © 2077</div>
    </div>
  </div>

</div>