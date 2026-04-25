<script lang="ts">
  import { onMount, tick } from "svelte"
  import { page } from "$app/stores"
  import { requireAuth, getToken } from "$lib/auth"

  // ── State ──────────────────────────────────────────────
  let messages   = $state<{ role: "user" | "gm" | "system"; content: string; ts: string }[]>([])
  let input      = $state("")
  let streaming  = $state(false)
  let loading    = $state(false)
  let now        = $state("")
  let nodeId     = $state("")
  let chatEl     = $state<HTMLElement | null>(null)
  let inputEl    = $state<HTMLTextAreaElement | null>(null)

  // session_id comes from the URL: /sessions/[session_id]
  const sessionId = $page.params.session_id

  // ── Lifecycle ──────────────────────────────────────────
  onMount(() => {
    requireAuth()
    now    = new Date().toLocaleString("en-GB", { hour12: false }).replace(",", "")
    nodeId = Math.random().toString(36).substring(2, 10).toUpperCase()
  })

  // ── Helpers ────────────────────────────────────────────
  async function scrollToBottom() {
    await tick()
    chatEl?.scrollTo({ top: chatEl.scrollHeight, behavior: "smooth" })
  }

  function ts() {
    return new Date().toISOString()
  }

  function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString("en-GB", {
      hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit"
    })
  }

  // ── Send message ───────────────────────────────────────
  async function sendMessage() {
    const text = input.trim()
    if (!text || streaming) return

    input = ""
    streaming = true

    // 1 — add player message to chat
    messages = [...messages, { role: "user", content: text, ts: ts() }]
    await scrollToBottom()

    // 2 — add empty GM message we will fill token by token
    messages = [...messages, { role: "gm", content: "", ts: ts() }]
    const gmIndex = messages.length - 1
    await scrollToBottom()

    try {
      // 3 — POST to backend, read SSE stream
      // body key must be "query" — matches body["query"] in the FastAPI endpoint
      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/${sessionId}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getToken()}`,
          },
          body: JSON.stringify({ query: text }),
        }
      )

      if (!res.ok || !res.body) {
        messages[gmIndex].content = "// TRANSMISSION ERROR — NO SIGNAL FROM GM"
        streaming = false
        return
      }

      // 4 — read the stream token by token
      const reader  = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const raw   = decoder.decode(value, { stream: true })
        const lines = raw.split("\n")

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          const token = line.slice(6)          // strip "data: " prefix
          if (token === "[DONE]") break
          if (!token) continue

          // append token to the last GM message
          messages[gmIndex] = {
            ...messages[gmIndex],
            content: messages[gmIndex].content + token,
          }
          await scrollToBottom()
        }
      }

    } catch {
      messages[gmIndex].content = "// CONNECTION LOST — RETRY"
    }

    streaming = false
    inputEl?.focus()
  }

  // ── Keyboard handler ───────────────────────────────────
  function onKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Bebas+Neue&display=swap" rel="stylesheet">
</svelte:head>

<style>
  :global(body) { background: #000; cursor: crosshair; overflow: hidden; }
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
  .rule-h { border-top: 1px solid rgba(255,255,255,0.12); }
  .rule-v { border-left: 1px solid rgba(255,255,255,0.12); }

  /* thin custom scrollbar */
  .scroll::-webkit-scrollbar       { width: 2px; }
  .scroll::-webkit-scrollbar-track { background: transparent; }
  .scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); }

  textarea          { resize: none; }
  textarea:focus    { outline: none; }

  /* message variants */
  .msg-gm     { border-left: 2px solid rgba(255,255,255,0.55); }
  .msg-user   { border-left: 2px solid rgba(255,255,255,0.18); }
  .msg-system { border-left: 2px solid rgba(255,255,255,0.06); }

  /* streaming cursor */
  .stream-cursor::after {
    content: "█";
    animation: blink 0.8s step-end infinite;
    color: rgba(255,255,255,0.4);
    margin-left: 2px;
  }
</style>

<div class="min-h-screen bg-black text-white scanline mono overflow-hidden">

  <!-- Grid overlay -->
  <div class="fixed inset-0 pointer-events-none"
    style="background-image:linear-gradient(rgba(255,255,255,0.025) 1px,transparent 1px),
           linear-gradient(90deg,rgba(255,255,255,0.025) 1px,transparent 1px);
           background-size:60px 60px;">
  </div>

  <!-- ═══ TOP CHROME ═══ -->
  <div class="fixed top-0 left-0 right-0 z-50">

    <!-- URL bar -->
    <div class="bg-[#0a0a0a] border-b border-white/10 px-4 h-9 flex items-center gap-4">
      <div class="flex gap-1.5">
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
      </div>
      <div class="flex-1 bg-black/60 border border-white/10 h-5 flex items-center px-3 max-w-md">
        <span class="text-white/35 text-xs">HTTPS://TTRPG.GM.SYSTEM/SESSIONS/{sessionId}</span>
      </div>
      <div class="ml-auto flex gap-3">
        <span class="text-white/20 text-xs">□</span>
        <span class="text-white/20 text-xs">—</span>
        <span class="text-white/20 text-xs">✕</span>
      </div>
    </div>

    <!-- Nav -->
    <div class="bg-black/95 border-b border-white/10 h-10 flex items-center px-6">
      <div class="flex items-center gap-8 flex-1">
        <span class="display text-xl tracking-wider">/SESSION</span>
        <div class="rule-v h-5"></div>
        <a href="/dashboard" class="text-xs text-white/30 tracking-widest hover:text-white/55 transition-colors">CAMPAIGNS 戰役</a>
        <a href="/rulebooks" class="text-xs text-white/30 tracking-widest hover:text-white/55 transition-colors">RULEBOOKS 規則</a>
      </div>
      <div class="flex items-center gap-5">
        <span class="text-xs text-white/30">NODE [{nodeId}]</span>
        <span class="text-xs text-white blink">● LIVE</span>
        <a href="/dashboard"
          class="text-xs text-white/30 tracking-widest hover:text-white transition-colors border border-white/10 hover:border-white/35 px-3 py-1">
          ← EXIT 退出
        </a>
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
  </div>

  <!-- ═══ BODY ═══ -->
  <!-- fixed between chrome (88px) and footer (56px) -->
  <div class="fixed left-0 right-0 flex" style="top:88px; bottom:56px;">

    <!-- ── LEFT SIDEBAR ── -->
    <div class="w-52 border-r border-white/10 flex flex-col shrink-0">

      <!-- Session ID block -->
      <div class="p-4 border-b border-white/10">
        <div class="text-white/20 text-xs tracking-widest mb-2">SESSION_NODE</div>
        <div class="display text-xl text-white leading-tight break-all">{sessionId}</div>
        <div class="text-white/20 text-xs mt-2">{now.split(" ")[0]}</div>
      </div>

      <!-- GM node -->
      <div class="p-4 border-b border-white/10">
        <div class="text-white/20 text-xs tracking-widest mb-3">PARTICIPANTS 參與者</div>
        <div class="flex items-center gap-3">
          <div class="w-6 h-6 border border-white/40 flex items-center justify-center flex-shrink-0">
            <span class="display text-xs text-white">GM</span>
          </div>
          <div>
            <div class="text-white text-xs">GAME MASTER</div>
            <div class="text-white/30 text-xs">AI // LOCAL LLM</div>
          </div>
          <div class="ml-auto w-1.5 h-1.5 rounded-full bg-white/60"
            style="animation: pulse 2s ease-in-out infinite;"
          ></div>
        </div>
      </div>

      <!-- Stats -->
      <div class="p-4 flex-1">
        <div class="text-white/20 text-xs tracking-widest mb-3">STATS 統計</div>
        <div class="space-y-2 text-xs">
          <div class="flex justify-between border-b border-white/8 pb-1.5">
            <span class="text-white/25">MESSAGES</span>
            <span class="text-white/55">{messages.length}</span>
          </div>
          <div class="flex justify-between border-b border-white/8 pb-1.5">
            <span class="text-white/25">GM TURNS</span>
            <span class="text-white/55">{messages.filter(m => m.role === "gm").length}</span>
          </div>
          <div class="flex justify-between border-b border-white/8 pb-1.5">
            <span class="text-white/25">STATUS</span>
            <span class="{streaming ? 'blink' : ''} text-white/55">
              {streaming ? "PROCESSING" : "READY"}
            </span>
          </div>
          <div class="flex justify-between border-b border-white/8 pb-1.5">
            <span class="text-white/25">RAG</span>
            <span class="text-white/55">ACTIVE</span>
          </div>
        </div>
      </div>

      <!-- Barcode -->
      <div class="p-4 border-t border-white/10">
        <div class="flex gap-px h-8">
          {#each Array(36) as _, i}
            <div class="flex-1 bg-white"
              style="opacity:{Math.random() > 0.4 ? Math.random() * 0.35 + 0.08 : 0};">
            </div>
          {/each}
        </div>
        <div class="text-white/15 text-xs mt-1 tracking-widest">SESSION-RAG-STREAM</div>
      </div>
    </div>

    <!-- ── CHAT PANEL ── -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Chat sub-header -->
      <div class="border-b border-white/10 px-6 h-9 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-4">
          <span class="text-white/20 text-xs tracking-widest">GM TRANSMISSION CHANNEL</span>
          <span class="text-white/10 text-xs">//</span>
          <span class="text-white/25 text-xs">RAG + VECTOR CONTEXT ACTIVE</span>
        </div>
        <span class="text-white/15 text-xs">{now.split(" ")[1] ?? ""}</span>
      </div>

      <!-- Messages -->
      <div
        bind:this={chatEl}
        class="flex-1 overflow-y-auto scroll px-6 py-4 space-y-0"
      >
        {#if messages.length === 0}
          <!-- Empty state -->
          <div class="h-full flex flex-col items-center justify-center text-center select-none">
            <div class="display text-[56px] leading-none text-white/5 mb-3">AWAITING<br>SIGNAL</div>
            <div class="text-white/20 text-xs tracking-widest mb-1">GAME MASTER IS STANDING BY</div>
            <div class="text-white/10 text-xs">&gt; TYPE A MESSAGE TO BEGIN YOUR SESSION</div>
          </div>

        {:else}
          {#each messages as msg, i}
            <div class="py-4 {i > 0 ? 'rule-h' : ''}">

              {#if msg.role === "gm"}
                <div class="msg-gm pl-4">
                  <div class="flex items-center gap-4 mb-2">
                    <span class="display text-sm tracking-widest text-white">GAME MASTER</span>
                    <span class="text-white/15 text-xs">//</span>
                    <span class="text-white/25 text-xs">{formatTime(msg.ts)}</span>
                    {#if streaming && i === messages.length - 1}
                      <span class="text-white/25 text-xs blink ml-1">TRANSMITTING_</span>
                    {/if}
                  </div>
                  <p class="text-white/75 text-sm leading-relaxed whitespace-pre-wrap
                    {streaming && i === messages.length - 1 ? 'stream-cursor' : ''}">
                    {msg.content}
                  </p>
                </div>

              {:else if msg.role === "user"}
                <div class="msg-user pl-4">
                  <div class="flex items-center gap-4 mb-2">
                    <span class="display text-sm tracking-widest text-white/45">PLAYER</span>
                    <span class="text-white/10 text-xs">//</span>
                    <span class="text-white/20 text-xs">{formatTime(msg.ts)}</span>
                  </div>
                  <p class="text-white/45 text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                </div>

              {:else}
                <div class="msg-system pl-4">
                  <p class="text-white/20 text-xs">{msg.content}</p>
                </div>
              {/if}

            </div>
          {/each}
        {/if}
      </div>

      <!-- Input area -->
      <div class="border-t border-white/15 shrink-0">
        <div class="px-6 py-4 flex items-end gap-3">

          <!-- Textarea wrapper -->
          <div class="flex-1 border border-white/10 hover:border-white/20 focus-within:border-white/28 transition-colors bg-white/[0.015]">
            <div class="flex items-center gap-2 px-4 py-1.5 border-b border-white/8">
              <span class="text-white/18 text-xs tracking-widest">INPUT 輸入</span>
              <span class="text-white/10 text-xs">//</span>
              <span class="text-white/12 text-xs">SHIFT+ENTER FOR NEWLINE</span>
            </div>
            <textarea
              bind:this={inputEl}
              bind:value={input}
              onkeydown={onKeydown}
              rows="3"
              placeholder="> TRANSMIT TO GAME MASTER..."
              disabled={streaming}
              class="w-full bg-transparent px-4 py-3 text-sm text-white/65
                     placeholder:text-white/12 disabled:opacity-30"
            ></textarea>
          </div>

          <!-- Send button -->
          <button
            onclick={sendMessage}
            disabled={!input.trim() || streaming}
            class="border border-white/25 hover:border-white hover:bg-white hover:text-black
                   disabled:opacity-20 disabled:cursor-not-allowed
                   transition-all px-5 py-3 text-xs tracking-widest text-white
                   self-stretch flex items-center justify-center min-w-[100px]"
          >
            {#if streaming}
              <span class="blink">TX_</span>
            {:else}
              TRANSMIT →
            {/if}
          </button>

        </div>

        <!-- Input footer -->
        <div class="px-6 pb-3 flex items-center gap-4">
          <div class="flex gap-px h-2.5">
            {#each Array(28) as _, i}
              <div class="w-px bg-white" style="opacity:{Math.random() > 0.5 ? 0.25 : 0.07};"></div>
            {/each}
          </div>
          <span class="text-white/12 text-xs">VECTOR MEMORY ACTIVE // RAG CONTEXT LOADED // SESSION {sessionId}</span>
        </div>
      </div>
    </div>

    <!-- ── RIGHT SIDEBAR ── -->
    <div class="w-48 border-l border-white/10 flex flex-col shrink-0">

      <div class="p-4 border-b border-white/10">
        <div class="text-white/20 text-xs tracking-widest mb-3">CONTEXT 上下文</div>
        <div class="space-y-2">
          {#each [
            { label: "RULEBOOK",  active: true },
            { label: "RAG INDEX", active: true },
            { label: "HISTORY",   active: messages.length > 0 },
            { label: "ENTITIES",  active: false },
            { label: "SUMMARY",   active: false },
          ] as item}
            <div class="flex items-center gap-2">
              <div class="w-1.5 h-1.5 rounded-full flex-shrink-0"
                style="background:rgba(255,255,255,{item.active ? 0.5 : 0.1});"></div>
              <span class="text-xs" style="color:rgba(255,255,255,{item.active ? 0.35 : 0.13});">
                {item.label}
              </span>
              <span class="ml-auto text-xs" style="color:rgba(255,255,255,{item.active ? 0.22 : 0.08});">
                {item.active ? "ON" : "—"}
              </span>
            </div>
          {/each}
        </div>
      </div>

      <div class="p-4 border-b border-white/10 flex-1">
        <div class="text-white/20 text-xs tracking-widest mb-3">SYSTEM LOG</div>
        <div class="space-y-1.5 text-xs text-white/20">
          <div>&gt; SESSION OPEN</div>
          <div>&gt; RAG LOADED</div>
          <div>&gt; GM READY</div>
          {#if messages.length > 0}
            <div>&gt; {messages.length} MSG LOGGED</div>
          {/if}
          {#if streaming}
            <div class="blink">&gt; STREAMING_</div>
          {/if}
        </div>
      </div>

      <!-- Mini barcode -->
      <div class="p-4">
        <div class="flex gap-px h-12">
          {#each Array(22) as _, i}
            <div class="flex-1 bg-white"
              style="opacity:{Math.random() > 0.45 ? Math.random() * 0.3 + 0.06 : 0};">
            </div>
          {/each}
        </div>
      </div>

    </div>
  </div>

  <!-- ═══ FOOTER ═══ -->
  <div class="fixed bottom-0 left-0 right-0 bg-black border-t border-white/10 z-50 h-14">
    <div class="border-b border-white/10 h-6 overflow-hidden flex items-center">
      <div class="ticker mono text-xs text-white/18">
        TTRPG-GM-SYSTEM &nbsp;///&nbsp; AI GAME MASTER ONLINE &nbsp;///&nbsp;
        RAG ENABLED &nbsp;///&nbsp; VECTOR DB SYNCED &nbsp;///&nbsp;
        SESSION MEMORY ACTIVE &nbsp;///&nbsp; SSE STREAM OPEN &nbsp;///&nbsp;
        TTRPG-GM-SYSTEM &nbsp;///&nbsp;
      </div>
    </div>
    <div class="h-8 px-6 flex items-center gap-6">
      <div class="flex gap-px h-3.5">
        {#each Array(28) as _, i}
          <div class="w-px bg-white" style="opacity:{Math.random() > 0.5 ? 0.25 : 0.07};"></div>
        {/each}
      </div>
      <span class="mono text-xs text-white/20">SESSION [{nodeId}]</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs text-white/20">MSG {messages.length}</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs {streaming ? 'blink' : ''} text-white/20">
        {streaming ? "● TRANSMITTING" : "● STANDBY"}
      </span>
      <div class="ml-auto mono text-xs text-white/18">TTRPG INDUSTRIAL // COPYRIGHT © 2077</div>
    </div>
  </div>

</div>