<script lang="ts">
  import { onMount, tick } from "svelte"
  import { page } from "$app/stores"
  import { requireAuth, getToken } from "$lib/auth"

  let campaign = $state<any>(null)
  let messages = $state<any[]>([])
  let players = $state<any[]>([])
  let input = $state("")
  let loading = $state(true)
  let sending = $state(false)
  let now = $state("")
  let sessionId = $state("")
  let chatEl = $state<HTMLElement | null>(null)
  let inputEl = $state<HTMLTextAreaElement | null>(null)

  const campaignId = $page.params.id

  onMount(async () => {
    requireAuth()
    now = new Date().toLocaleString("en-GB", { hour12: false }).replace(",", "")
    sessionId = Math.random().toString(36).substring(2, 10).toUpperCase()
    await Promise.all([fetchCampaign(), fetchHistory()])
    loading = false
    scrollToBottom()
  })

  async function fetchCampaign() {
    const token = getToken()
    const res = await fetch(`${import.meta.env.VITE_API_URL}/campaigns/${campaignId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (res.ok) campaign = await res.json()
  }

  async function fetchHistory() {
    const token = getToken()
    const res = await fetch(`${import.meta.env.VITE_API_URL}/campaigns/${campaignId}/messages`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (res.ok) messages = await res.json()
  }

  async function sendMessage() {
    if (!input.trim() || sending) return
    const text = input.trim()
    input = ""
    sending = true

    messages = [...messages, { role: "user", content: text, timestamp: new Date().toISOString() }]
    await scrollToBottom()

    const token = getToken()
    const res = await fetch(`${import.meta.env.VITE_API_URL}/campaigns/${campaignId}/chat`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    })

    if (res.ok) {
      const data = await res.json()
      messages = [...messages, { role: "assistant", content: data.reply, timestamp: new Date().toISOString() }]
    } else {
      messages = [...messages, { role: "system", content: "// TRANSMISSION ERROR — RETRY", timestamp: new Date().toISOString() }]
    }

    sending = false
    await scrollToBottom()
    inputEl?.focus()
  }

  async function scrollToBottom() {
    await tick()
    chatEl?.scrollTo({ top: chatEl.scrollHeight, behavior: "smooth" })
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString("en-GB", { hour12: false, hour: "2-digit", minute: "2-digit" })
  }
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Bebas+Neue&display=swap" rel="stylesheet">
</svelte:head>

<style>
  :global(body) { background: #000; cursor: crosshair; }
  .mono { font-family: 'Share Tech Mono', monospace; }
  .display { font-family: 'Bebas Neue', sans-serif; }
  .scanline {
    background: repeating-linear-gradient(
      0deg, transparent, transparent 3px,
      rgba(255,255,255,0.015) 3px, rgba(255,255,255,0.015) 4px
    );
  }
  .ticker { animation: ticker 20s linear infinite; white-space: nowrap; }
  @keyframes ticker {
    from { transform: translateX(100%); }
    to { transform: translateX(-100%); }
  }
  .blink { animation: blink 1.2s step-end infinite; }
  @keyframes blink { 50% { opacity: 0; } }
  .rule-h { border-top: 1px solid rgba(255,255,255,0.15); }
  .rule-v { border-left: 1px solid rgba(255,255,255,0.15); }
  .chat-scroll::-webkit-scrollbar { width: 2px; }
  .chat-scroll::-webkit-scrollbar-track { background: transparent; }
  .chat-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); }
  textarea { resize: none; }
  textarea:focus { outline: none; }
  .msg-gm { border-left: 2px solid rgba(255,255,255,0.6); }
  .msg-user { border-left: 2px solid rgba(255,255,255,0.2); }
  .msg-system { border-left: 2px solid rgba(255,255,255,0.08); }
  .player-dot { animation: pulse 2s ease-in-out infinite; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
</style>

<div class="min-h-screen bg-black text-white scanline relative overflow-hidden mono">

  <!-- Grid overlay -->
  <div class="fixed inset-0 pointer-events-none"
    style="background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px); background-size: 60px 60px;">
  </div>

  <!-- ═══ BROWSER CHROME ═══ -->
  <div class="fixed top-0 left-0 right-0 z-50">
    <div class="bg-[#0a0a0a] border-b border-white/10 px-4 h-9 flex items-center gap-4">
      <div class="flex gap-1.5">
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
      </div>
      <div class="flex-1 bg-black/60 border border-white/10 h-5 flex items-center px-3 max-w-sm">
        <span class="text-white/40 text-xs mono">HTTPS://TTRPG.GM.SYSTEM/SESSION/{campaignId}</span>
      </div>
      <div class="ml-auto flex gap-3">
        <span class="text-white/20 text-xs">□</span>
        <span class="text-white/20 text-xs">—</span>
        <span class="text-white/20 text-xs">✕</span>
      </div>
    </div>

    <div class="bg-black/95 border-b border-white/10 h-10 flex items-center px-6 gap-0">
      <div class="flex items-center gap-8 flex-1">
        <span class="display text-xl tracking-wider text-white">/SESSION</span>
        <div class="rule-v h-5"></div>
        <a href="/dashboard" class="text-xs text-white/30 mono tracking-widest hover:text-white/60 transition-colors">CAMPAIGNS 戰役</a>
        <a href="/rulebook" class="text-xs text-white/30 mono tracking-widest hover:text-white/60 transition-colors">RULEBOOK 規則</a>
        <a href="/sessions" class="text-xs text-white/30 mono tracking-widest hover:text-white/60 transition-colors">SESSIONS 會話</a>
      </div>
      <div class="flex items-center gap-6">
        <span class="text-xs text-white/30 mono">NODE [{sessionId}]</span>
        <span class="text-xs text-white blink mono">● LIVE</span>
        <a href="/dashboard" class="text-xs text-white/30 mono tracking-widest hover:text-white transition-colors border border-white/10 hover:border-white/40 px-3 py-1">
          ← EXIT 退出
        </a>
      </div>
    </div>

    <div class="bg-black border-b border-white/10 h-4 flex items-end px-6 overflow-hidden">
      {#each Array(40) as _, i}
        <div class="flex-1 flex items-end justify-center">
          {#if i % 5 === 0}
            <div class="w-px bg-white/20" style="height: 8px;"></div>
          {:else}
            <div class="w-px bg-white/10" style="height: 4px;"></div>
          {/if}
        </div>
      {/each}
    </div>
  </div>

  <!-- ═══ MAIN LAYOUT ═══ -->
  <div class="fixed left-0 right-0 flex" style="top: 88px; bottom: 56px;">

    <!-- ── LEFT PANEL: Campaign Info ── -->
    <div class="w-64 border-r border-white/10 flex flex-col shrink-0">
      <div class="p-4 border-b border-white/10">
        <div class="text-white/20 text-xs tracking-widest mb-1">CAMPAIGN_NODE</div>
        {#if campaign}
          <div class="display text-2xl text-white tracking-wider leading-tight">
            {campaign.name.toUpperCase()}
          </div>
          <div class="text-white/30 text-xs mt-1">{campaign.rulebook ?? "UNKNOWN SYSTEM"}</div>
        {:else}
          <div class="display text-2xl text-white/20">LOADING...</div>
        {/if}
      </div>

      <!-- Players -->
      <div class="p-4 border-b border-white/10 flex-1 overflow-y-auto">
        <div class="text-white/20 text-xs tracking-widest mb-3">ACTIVE PLAYERS 玩家</div>
        <div class="space-y-3">
          <!-- GM Node (AI) -->
          <div class="flex items-center gap-3">
            <div class="w-6 h-6 border border-white/40 flex items-center justify-center">
              <span class="text-white text-xs display">GM</span>
            </div>
            <div>
              <div class="text-white text-xs mono">GAME MASTER</div>
              <div class="text-white/30 text-xs mono">AI // CLAUDE</div>
            </div>
            <div class="ml-auto w-1.5 h-1.5 rounded-full bg-white player-dot"></div>
          </div>
          <!-- Dynamic players would map here -->
          {#each players as player}
            <div class="flex items-center gap-3">
              <div class="w-6 h-6 border border-white/20 flex items-center justify-center">
                <span class="text-white/40 text-xs display">{player.name[0]}</span>
              </div>
              <div>
                <div class="text-white/60 text-xs mono">{player.name.toUpperCase()}</div>
                <div class="text-white/20 text-xs mono">{player.character ?? "—"}</div>
              </div>
              <div class="ml-auto w-1.5 h-1.5 rounded-full bg-white/40 player-dot"></div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Session stats -->
      <div class="p-4">
        <div class="space-y-2 text-xs mono text-white/30">
          <div class="flex justify-between border-b border-white/10 pb-1">
            <span>MESSAGES 訊息</span>
            <span class="text-white/60">{messages.length}</span>
          </div>
          <div class="flex justify-between border-b border-white/10 pb-1">
            <span>SESSION 節點</span>
            <span class="text-white/60">{sessionId}</span>
          </div>
          <div class="flex justify-between border-b border-white/10 pb-1">
            <span>TIME 時間</span>
            <span class="text-white/60">{now.split(" ")[1] ?? ""}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ── CENTER PANEL: Chat ── -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Chat header -->
      <div class="border-b border-white/10 px-6 py-3 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-4">
          <div class="text-white/20 text-xs tracking-[0.4em]">GM TRANSMISSION CHANNEL</div>
          <div class="text-white/10 text-xs">///</div>
          <div class="text-white/40 text-xs">CONTEXT: RAG + VECTOR_DB</div>
        </div>
        <div class="text-white/20 text-xs mono">END-TO-END ENCRYPTED 加密</div>
      </div>

      <!-- Messages -->
      <div bind:this={chatEl} class="flex-1 overflow-y-auto chat-scroll px-6 py-4 space-y-0">

        {#if loading}
          <div class="flex items-center justify-center h-full">
            <span class="text-white/20 text-xs tracking-widest">LOADING MEMORY <span class="blink">_</span></span>
          </div>

        {:else if messages.length === 0}
          <div class="flex flex-col items-center justify-center h-full text-center">
            <div class="display text-6xl text-white/5 mb-4">AWAITING SIGNAL</div>
            <div class="text-white/20 text-xs tracking-widest mb-1">GAME MASTER IS READY</div>
            <div class="text-white/10 text-xs">&gt; TYPE A MESSAGE TO BEGIN YOUR SESSION</div>
          </div>

        {:else}
          {#each messages as msg, i}
            <div class="py-4 {i > 0 ? 'rule-h' : ''}">
              {#if msg.role === "assistant"}
                <div class="msg-gm pl-4">
                  <div class="flex items-center gap-4 mb-2">
                    <span class="display text-sm text-white tracking-widest">GAME MASTER</span>
                    <span class="text-white/20 text-xs">///</span>
                    <span class="text-white/30 text-xs mono">{formatTime(msg.timestamp)}</span>
                  </div>
                  <p class="text-white/80 text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                </div>
              {:else if msg.role === "user"}
                <div class="msg-user pl-4">
                  <div class="flex items-center gap-4 mb-2">
                    <span class="display text-sm text-white/50 tracking-widest">PLAYER</span>
                    <span class="text-white/10 text-xs">///</span>
                    <span class="text-white/20 text-xs mono">{formatTime(msg.timestamp)}</span>
                  </div>
                  <p class="text-white/50 text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                </div>
              {:else}
                <div class="msg-system pl-4">
                  <p class="text-white/20 text-xs mono">{msg.content}</p>
                </div>
              {/if}
            </div>
          {/each}

          {#if sending}
            <div class="py-4 rule-h">
              <div class="msg-gm pl-4">
                <div class="flex items-center gap-4 mb-2">
                  <span class="display text-sm text-white tracking-widest">GAME MASTER</span>
                  <span class="text-white/20 text-xs">///</span>
                  <span class="text-white/30 text-xs mono blink">PROCESSING_</span>
                </div>
                <p class="text-white/30 text-sm mono">
                  <span class="blink">█</span>
                </p>
              </div>
            </div>
          {/if}
        {/if}
      </div>

      <!-- Input -->
      <div class="border-t border-white/15 shrink-0">
        <div class="px-6 py-4 flex items-end gap-4">
          <div class="flex-1 border border-white/10 hover:border-white/20 transition-colors focus-within:border-white/30 bg-white/[0.02]">
            <div class="flex items-center gap-2 px-4 py-2 border-b border-white/10">
              <span class="text-white/20 text-xs mono tracking-widest">INPUT 輸入</span>
              <span class="text-white/10 text-xs">///</span>
              <span class="text-white/15 text-xs mono">SHIFT+ENTER FOR NEWLINE</span>
            </div>
            <textarea
              bind:this={inputEl}
              bind:value={input}
              onkeydown={handleKeydown}
              rows="3"
              placeholder="> TRANSMIT TO GAME MASTER..."
              disabled={sending || loading}
              class="w-full bg-transparent px-4 py-3 text-sm text-white/70 placeholder:text-white/15 mono disabled:opacity-40"
            ></textarea>
          </div>
          <button
            onclick={sendMessage}
            disabled={!input.trim() || sending || loading}
            class="border border-white/30 hover:border-white hover:bg-white hover:text-black disabled:opacity-20 disabled:cursor-not-allowed transition-all px-5 py-3 mono text-xs tracking-widest text-white self-stretch flex items-center justify-center"
          >
            {#if sending}
              <span class="blink">TX_</span>
            {:else}
              TRANSMIT →
            {/if}
          </button>
        </div>
        <div class="px-6 pb-3 flex items-center gap-4">
          <div class="flex gap-px h-3">
            {#each Array(24) as _, i}
              <div class="w-px bg-white" style="opacity: {Math.random() > 0.5 ? 0.3 : 0.08};"></div>
            {/each}
          </div>
          <span class="text-white/15 text-xs mono">VECTOR MEMORY ACTIVE // RAG CONTEXT LOADED</span>
        </div>
      </div>
    </div>

    <!-- ── RIGHT PANEL: Scene / Context ── -->
    <div class="w-56 border-l border-white/10 flex flex-col shrink-0">
      <div class="p-4 border-b border-white/10">
        <div class="text-white/20 text-xs tracking-widest mb-1">SCENE_DATA 場景</div>
        <div class="display text-xl text-white/80 tracking-wide leading-tight">CURRENT<br>SCENE</div>
      </div>

      <div class="flex-1 p-4 overflow-y-auto space-y-4">
        <!-- Context indicators -->
        <div>
          <div class="text-white/20 text-xs tracking-widest mb-2">MEMORY 記憶</div>
          <div class="space-y-1">
            {#each ["RULEBOOK LOADED", "SESSION HISTORY", "WORLD STATE", "NPC REGISTRY"] as item, i}
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-white/40"></div>
                <span class="text-white/30 text-xs mono">{item}</span>
              </div>
            {/each}
          </div>
        </div>

        <div class="rule-h pt-4">
          <div class="text-white/20 text-xs tracking-widest mb-2">ACTIVE RULES 規則</div>
          <div class="text-white/30 text-xs mono leading-relaxed">
            {campaign?.rulebook ?? "—"}
          </div>
        </div>

        <!-- Atmospheric barcode -->
        <div class="rule-h pt-4">
          <div class="flex gap-px h-16">
            {#each Array(28) as _, i}
              <div class="flex-1 bg-white" style="opacity: {Math.random() > 0.4 ? Math.random() * 0.4 + 0.1 : 0};"></div>
            {/each}
          </div>
        </div>
      </div>

      <!-- Danger zone / clear -->
      <div class="p-4 border-t border-white/10">
        <button class="w-full border border-white/10 hover:border-white/30 text-white/20 hover:text-white/50 transition-all text-xs mono tracking-widest py-2">
          CLEAR SESSION
        </button>
      </div>
    </div>

  </div>

  <!-- ═══ FOOTER ═══ -->
  <div class="fixed bottom-0 left-0 right-0 bg-black border-t border-white/10 z-50 h-14">
    <div class="border-b border-white/10 h-6 overflow-hidden flex items-center">
      <div class="ticker mono text-xs text-white/20">
        TTRPG-GM-SYSTEM &nbsp;///&nbsp; AI GAME MASTER ONLINE &nbsp;///&nbsp; RAG ENABLED &nbsp;///&nbsp;
        VECTOR DB SYNCED &nbsp;///&nbsp; SESSION MEMORY ACTIVE &nbsp;///&nbsp;
        MULTI-PLAYER ROOMS STANDBY &nbsp;///&nbsp; CLAUDE SONNET CONNECTED &nbsp;///&nbsp;
      </div>
    </div>
    <div class="h-8 px-6 flex items-center gap-8">
      <span class="mono text-xs text-white/20">SESSION [{sessionId}]</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs text-white/20">MSG 訊息</span>
      <span class="mono text-xs text-white/40">{messages.length}</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs text-white/20 blink">● LIVE TRANSMISSION</span>
      <div class="ml-auto mono text-xs text-white/20">TTRPG INDUSTRIAL // COPYRIGHT © 2077</div>
    </div>
  </div>

</div>