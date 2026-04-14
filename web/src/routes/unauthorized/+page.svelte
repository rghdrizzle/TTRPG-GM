<script lang="ts">
  const sessionId = Math.random().toString(36).substring(2, 10).toUpperCase()
  const now = new Date().toLocaleString("en-GB", { hour12: false }).replace(",", "")
  const code = Math.floor(Math.random() * 9000 + 1000)
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
  .blink { animation: blink 1.2s step-end infinite; }
  @keyframes blink { 50% { opacity: 0; } }
  .ticker { animation: ticker 20s linear infinite; white-space: nowrap; }
  @keyframes ticker {
    from { transform: translateX(100%); }
    to { transform: translateX(-100%); }
  }
  .glitch {
    position: relative;
  }
  .glitch::before {
    content: attr(data-text);
    position: absolute;
    left: 2px;
    top: 0;
    color: white;
    opacity: 0.3;
    clip-path: polygon(0 30%, 100% 30%, 100% 50%, 0 50%);
    animation: glitch 3s infinite;
  }
  @keyframes glitch {
    0%, 90%, 100% { transform: translateX(0); opacity: 0; }
    92% { transform: translateX(-4px); opacity: 0.3; }
    94% { transform: translateX(4px); opacity: 0.3; }
    96% { transform: translateX(-2px); opacity: 0.3; }
    98% { transform: translateX(0); opacity: 0; }
  }
</style>

<div class="min-h-screen bg-black text-white scanline mono flex flex-col">

  <!-- Grid overlay -->
  <div class="fixed inset-0 pointer-events-none"
    style="background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px); background-size: 60px 60px;">
  </div>

  <!-- ═══ BROWSER CHROME ═══ -->
  <div class="border-b border-white/10 bg-[#0a0a0a] h-9 flex items-center px-4 gap-4 flex-shrink-0">
    <div class="flex gap-1.5">
      <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
      <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
      <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
    </div>
    <div class="bg-black/60 border border-white/10 h-5 flex items-center px-3 max-w-sm flex-1">
      <span class="text-white/40 text-xs mono">HTTPS://TTRPG.GM.SYSTEM/UNAUTHORIZED</span>
    </div>
    <div class="ml-auto flex gap-3">
      <span class="text-white/20 text-xs">□</span>
      <span class="text-white/20 text-xs">—</span>
      <span class="text-white/20 text-xs">✕</span>
    </div>
  </div>

  <!-- ═══ NAV ═══ -->
  <div class="border-b border-white/10 h-10 flex items-center px-6 flex-shrink-0">
    <div class="display text-xl tracking-wider text-white">/ERROR</div>
    <div class="border-l border-white/15 h-5 mx-6"></div>
    <span class="text-xs text-white mono tracking-widest">UNAUTHORIZED 未授權</span>
    <div class="ml-auto text-xs text-white/20 mono">SESSION [{sessionId}]</div>
  </div>

  <!-- Ruler -->
  <div class="border-b border-white/10 h-4 flex items-end px-6 overflow-hidden flex-shrink-0">
    {#each Array(40) as _, i}
      <div class="flex-1 flex items-end justify-center">
        <div class="w-px bg-white/15" style="height: {i % 5 === 0 ? 8 : 4}px;"></div>
      </div>
    {/each}
  </div>

  <!-- ═══ MAIN ═══ -->
  <div class="flex-1 flex flex-col items-center justify-center px-6 relative">

    <!-- Corner decorations -->
    <div class="absolute top-8 left-8 w-12 h-12 border-t border-l border-white/20"></div>
    <div class="absolute top-8 right-8 w-12 h-12 border-t border-r border-white/20"></div>
    <div class="absolute bottom-8 left-8 w-12 h-12 border-b border-l border-white/20"></div>
    <div class="absolute bottom-8 right-8 w-12 h-12 border-b border-r border-white/20"></div>

    <div class="w-full max-w-2xl">

      <!-- Error code -->
      <div class="text-center mb-2">
        <div class="mono text-xs text-white/20 tracking-[0.5em] mb-4">ACCESS VIOLATION // ERROR_{code}</div>
        <div class="glitch display text-[160px] leading-none text-white" data-text="401">401</div>
        <div class="display text-[160px] leading-none text-white/5 -mt-8">未授權</div>
      </div>

      <!-- Divider -->
      <div class="flex items-center gap-4 my-6">
        <div class="h-px flex-1 bg-white/10"></div>
        <div class="mono text-xs text-white/20">//</div>
        <div class="h-px flex-1 bg-white/10"></div>
      </div>

      <!-- Message block -->
      <div class="border border-white/15 relative">
        <div class="absolute top-0 left-0 w-0.5 h-full bg-white/40"></div>

        <div class="border-b border-white/10 px-6 py-3">
          <div class="mono text-xs text-white/20 tracking-widest">SYSTEM MESSAGE // 系統訊息</div>
        </div>

        <div class="px-6 py-6 space-y-3">
          <div class="flex gap-3 items-start">
            <span class="text-white/20 mono text-xs mt-0.5">&gt;</span>
            <p class="mono text-sm text-white/60">
              ACCESS DENIED — no valid authentication token found on this node.
            </p>
          </div>
          <div class="flex gap-3 items-start">
            <span class="text-white/20 mono text-xs mt-0.5">&gt;</span>
            <p class="mono text-sm text-white/40">
              You must authenticate before accessing this resource.
            </p>
          </div>
          <div class="flex gap-3 items-start">
            <span class="text-white/20 mono text-xs mt-0.5">&gt;</span>
            <p class="mono text-sm text-white/30">
              INCIDENT REF: ERR-{code}-{sessionId}
            </p>
          </div>
        </div>

        <div class="border-t border-white/10 px-6 py-4 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-1.5 h-1.5 rounded-full bg-white blink"></div>
            <span class="mono text-xs text-white/30 tracking-widest">AWAITING AUTHENTICATION</span>
          </div>
          <div class="flex gap-3">
            <a href="/login"
              class="mono text-xs tracking-widest px-5 py-2 border border-white text-white hover:bg-white hover:text-black transition-all duration-150">
              &gt; LOGIN_NODE
            </a>
            <a href="/register"
              class="mono text-xs tracking-widest px-5 py-2 border border-white/20 text-white/40 hover:border-white hover:text-white transition-all duration-150">
              REGISTER
            </a>
          </div>
        </div>
      </div>

      <!-- Meta grid -->
      <div class="grid grid-cols-4 gap-0 border border-white/10 border-t-0 mt-0">
        {#each [
          { label: "ERROR", value: "401" },
          { label: "TYPE", value: "UNAUTHORIZED" },
          { label: "TIME", value: now.split(" ")[1] ?? "" },
          { label: "REF", value: sessionId },
        ] as item}
          <div class="border-r border-white/10 last:border-r-0 p-3 text-center">
            <div class="mono text-xs text-white/20 mb-1">{item.label}</div>
            <div class="mono text-xs text-white/50">{item.value}</div>
          </div>
        {/each}
      </div>

    </div>
  </div>

  <!-- ═══ FOOTER ═══ -->
  <div class="border-t border-white/10 flex-shrink-0">
    <div class="h-6 overflow-hidden flex items-center border-b border-white/10">
      <div class="ticker mono text-xs text-white/20">
        ACCESS DENIED &nbsp;///&nbsp; AUTHENTICATION REQUIRED &nbsp;///&nbsp;
        UNAUTHORIZED REQUEST LOGGED &nbsp;///&nbsp; REDIRECT TO LOGIN &nbsp;///&nbsp;
        TTRPG-GM-SYSTEM &nbsp;///&nbsp; ERROR 401 &nbsp;///&nbsp;
      </div>
    </div>
    <div class="h-8 px-6 flex items-center gap-6">
      <div class="flex gap-px h-4">
        {#each Array(32) as _, i}
          <div class="w-px bg-white" style="opacity: {Math.random() > 0.5 ? 0.3 : 0.08};"></div>
        {/each}
      </div>
      <span class="mono text-xs text-white/20">TTRPG INDUSTRIAL</span>
      <div class="border-l border-white/10 h-4"></div>
      <span class="mono text-xs text-white/20">COPYRIGHT © 2077</span>
      <div class="ml-auto mono text-xs text-white/20">{now.split(" ")[1] ?? ""}</div>
    </div>
  </div>

</div>