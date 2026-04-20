<script lang="ts">
  import { onMount } from "svelte"
  import { requireAuth, logout, getToken } from "$lib/auth"

  let campaigns = $state<any[]>([])
  let loading = $state(true)
  let now = $state("")
  let sessionId = $state("")

  onMount(async () => {
    requireAuth()
    now = new Date().toLocaleString("en-GB", { hour12: false }).replace(",", "")
    sessionId = Math.random().toString(36).substring(2, 10).toUpperCase()
    await fetchCampaigns()
  })

  async function fetchCampaigns() {
    const token = getToken()
    const res = await fetch(`${import.meta.env.VITE_API_URL}/campaigns`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    if (res.ok) {
      const data = await res.json()
      campaigns = data.payload.campaigns
      loading = false
    }
  }
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Bebas+Neue&display=swap" rel="stylesheet">
</svelte:head>

<style>
  :global(body) {
    background: #000;
    cursor: crosshair;
  }
  .mono { font-family: 'Share Tech Mono', monospace; }
  .display { font-family: 'Bebas Neue', sans-serif; }
  .ticker {
    animation: ticker 20s linear infinite;
    white-space: nowrap;
  }
  @keyframes ticker {
    from { transform: translateX(100%); }
    to { transform: translateX(-100%); }
  }
  .blink { animation: blink 1.2s step-end infinite; }
  @keyframes blink { 50% { opacity: 0; } }
  .scanline {
    background: repeating-linear-gradient(
      0deg, transparent, transparent 3px,
      rgba(255,255,255,0.015) 3px, rgba(255,255,255,0.015) 4px
    );
  }
  .rule-h { border-top: 1px solid rgba(255,255,255,0.15); }
  .rule-v { border-left: 1px solid rgba(255,255,255,0.15); }
  .campaign-card:hover .card-index { opacity: 1; }
  .campaign-card:hover { background: rgba(255,255,255,0.04); }
</style>

<div class="min-h-screen bg-black text-white scanline relative overflow-hidden mono">

  <!-- Grid overlay -->
  <div class="fixed inset-0 pointer-events-none"
    style="background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px); background-size: 60px 60px;">
  </div>

  <!-- ═══ BROWSER CHROME ═══ -->
  <div class="fixed top-0 left-0 right-0 z-50">

    <!-- URL bar -->
    <div class="bg-[#0a0a0a] border-b border-white/10 px-4 h-9 flex items-center gap-4">
      <div class="flex gap-1.5">
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-white/20"></div>
      </div>
      <div class="flex-1 bg-black/60 border border-white/10 h-5 flex items-center px-3 max-w-sm">
        <span class="text-white/40 text-xs mono">HTTPS://TTRPG.GM.SYSTEM/DASHBOARD</span>
      </div>
      <div class="ml-auto flex gap-3">
        <span class="text-white/20 text-xs">□</span>
        <span class="text-white/20 text-xs">—</span>
        <span class="text-white/20 text-xs">✕</span>
      </div>
    </div>

    <!-- Nav -->
    <div class="bg-black/95 border-b border-white/10 h-10 flex items-center px-6 gap-0">
      <div class="flex items-center gap-8 flex-1">
        <span class="display text-xl tracking-wider text-white">/DASHBOARD</span>
        <div class="rule-v h-5"></div>
        <a href="/dashboard" class="text-xs text-white mono tracking-widest hover:text-white/60 transition-colors">CAMPAIGNS 戰役</a>
        <a href="/rulebook" class="text-xs text-white/30 mono tracking-widest hover:text-white/60 transition-colors">RULEBOOK 規則</a>
        <a href="/sessions" class="text-xs text-white/30 mono tracking-widest hover:text-white/60 transition-colors">SESSIONS 會話</a>
      </div>
      <div class="flex items-center gap-6">
        <span class="text-xs text-white/30 mono">SESSION [{sessionId}]</span>
        <button onclick={logout} class="text-xs text-white/30 mono tracking-widest hover:text-white transition-colors border border-white/10 hover:border-white/40 px-3 py-1">
          DISCONNECT 斷開
        </button>
      </div>
    </div>

    <!-- Ruler -->
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

  <!-- ═══ MAIN CONTENT ═══ -->
  <div class="pt-[88px] pb-24 px-6 max-w-[1400px] mx-auto">

    <!-- Hero header -->
    <div class="rule-h pt-8 pb-6 mt-4 grid grid-cols-12 gap-0">
      <div class="col-span-8 rule-v pl-4">
        <div class="text-white/30 text-xs mono tracking-[0.4em] mb-2">GM CONTROL NODE // ACTIVE CAMPAIGNS</div>
        <h1 class="display text-[80px] leading-none text-white tracking-wider mb-1">/CAMPAIGNS</h1>
        <p class="display text-[80px] leading-none text-white/10 tracking-wider">戰役列表</p>
      </div>
      <div class="col-span-4 pl-6 flex flex-col justify-between">
        <!-- Metadata block -->
        <div class="space-y-2 text-xs mono text-white/30">
          <div class="flex justify-between border-b border-white/10 pb-1">
            <span>DATE 日期</span>
            <span class="text-white/60">{now.split(" ")[0]}</span>
          </div>
          <div class="flex justify-between border-b border-white/10 pb-1">
            <span>TIME 時間</span>
            <span class="text-white/60">{now.split(" ")[1] ?? ""}</span>
          </div>
          <div class="flex justify-between border-b border-white/10 pb-1">
            <span>NODES 節點</span>
            <span class="text-white/60">{campaigns.length}</span>
          </div>
          <div class="flex justify-between border-b border-white/10 pb-1">
            <span>STATUS 狀態</span>
            <span class="text-white blink">● ONLINE</span>
          </div>
        </div>
        <!-- Barcode -->
        <div class="mt-4">
          <div class="flex gap-px h-10">
            {#each Array(48) as _, i}
              <div class="flex-1 bg-white" style="opacity: {Math.random() > 0.4 ? Math.random() * 0.6 + 0.2 : 0};"></div>
            {/each}
          </div>
          <div class="text-white/20 text-xs mono mt-1 tracking-widest">TTRPG-GM-SYS-2077</div>
        </div>
      </div>
    </div>

    <!-- Action bar -->
    <div class="rule-h flex items-center justify-between py-3">
      <div class="flex items-center gap-6">
        <span class="text-xs mono text-white/20 tracking-widest">FILTER: ALL</span>
        <span class="text-xs mono text-white/20 tracking-widest">SORT: RECENT</span>
      </div>
      <a href="/campaigns/new"
        class="mono text-xs tracking-[0.3em] px-5 py-2 border border-white text-white hover:bg-white hover:text-black transition-all duration-150"
      >
        + INITIALIZE NODE
      </a>
    </div>

    <!-- Loading -->
    {#if loading}
      <div class="rule-h py-20 text-center">
        <div class="text-xs mono text-white/30 tracking-widest">
          LOADING <span class="blink">_</span>
        </div>
      </div>

    <!-- Empty -->
    {:else if campaigns.length === 0}
      <div class="rule-h py-20 grid grid-cols-12">
        <div class="col-span-8 rule-v pl-4">
          <div class="display text-6xl text-white/10 mb-4">[ NULL ]</div>
          <p class="mono text-xs text-white/30 tracking-widest mb-1">NO CAMPAIGN NODES FOUND ON THE GRID</p>
          <p class="mono text-xs text-white/20">&gt; INITIALIZE A NEW NODE TO BEGIN YOUR SESSION</p>
          <a href="/campaigns/new"
            class="inline-block mt-8 mono text-xs tracking-widest px-6 py-2 border border-white/30 text-white/50 hover:border-white hover:text-white transition-all"
          >
            + INITIALIZE FIRST NODE
          </a>
        </div>
        <div class="col-span-4 pl-6 flex items-center justify-center">
          <div class="display text-[120px] text-white/5 leading-none">00</div>
        </div>
      </div>

    <!-- Campaign list -->
    {:else}
      <div class="rule-h">
        {#each campaigns as campaign, i}
          <a href={`/campaigns/${campaign.id}`}
            class="campaign-card rule-h grid grid-cols-12 gap-0 py-5 transition-all duration-150 relative group cursor-crosshair"
          >
            <!-- Index number -->
            <div class="col-span-1 rule-v pl-4 flex items-center">
              <span class="display text-4xl text-white/10 group-hover:text-white/30 transition-colors">
                {String(i + 1).padStart(2, "0")}
              </span>
            </div>

            <!-- Name -->
            <div class="col-span-5 rule-v pl-6 flex flex-col justify-center">
              <div class="text-white/20 mono text-xs tracking-widest mb-1">CAMPAIGN_NAME</div>
              <div class="display text-3xl text-white tracking-wider leading-tight">
                {campaign.name.toUpperCase()}
              </div>
            </div>

            <!-- Details -->
            <div class="col-span-3 rule-v pl-6 flex flex-col justify-center gap-1">
              <div class="flex items-center gap-3">
                <span class="mono text-xs text-white/20">SYSTEM</span>
                <span class="mono text-xs text-white/60">{campaign.rulebook ?? "UNKNOWN"}</span>
              </div>
              <div class="flex items-center gap-3">
                <span class="mono text-xs text-white/20">STATUS</span>
                <span class="mono text-xs text-white flex items-center gap-1">
                  <span class="w-1.5 h-1.5 rounded-full bg-white inline-block blink"></span>
                  ACTIVE
                </span>
              </div>
            </div>

            <!-- Action -->
            <div class="col-span-3 pl-6 flex items-center justify-between">
              <div class="mono text-xs text-white/20 tracking-widest">RESUME_SESSION →</div>
              <div class="display text-5xl text-white/5 group-hover:text-white/20 transition-colors pr-4">
                ↗
              </div>
            </div>

          </a>
        {/each}
      </div>
    {/if}

  </div>

  <!-- ═══ FOOTER METADATA BAR ═══ -->
  <div class="fixed bottom-0 left-0 right-0 bg-black border-t border-white/10 z-50">

    <!-- Ticker -->
    <div class="border-b border-white/10 h-6 overflow-hidden flex items-center">
      <div class="ticker mono text-xs text-white/20">
        TTRPG-GM-SYSTEM &nbsp;///&nbsp; RAG ENABLED &nbsp;///&nbsp; VECTOR DB ONLINE &nbsp;///&nbsp;
        SESSION MEMORY ACTIVE &nbsp;///&nbsp; CLAUDE SONNET CONNECTED &nbsp;///&nbsp;
        MULTI-PLAYER ROOMS STANDBY &nbsp;///&nbsp; TTRPG-GM-SYSTEM &nbsp;///&nbsp;
      </div>
    </div>

    <!-- Metadata -->
    <div class="h-8 px-6 flex items-center gap-8">
      <div class="flex gap-px h-4">
        {#each Array(32) as _, i}
          <div class="w-px bg-white" style="opacity: {Math.random() > 0.5 ? 0.4 : 0.1};"></div>
        {/each}
      </div>
      <span class="mono text-xs text-white/20">FOUNDERS 創人 ///////////////////</span>
      <span class="mono text-xs text-white/40">TTRPG INDUSTRIAL</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs text-white/20">SESSIONS 節點</span>
      <span class="mono text-xs text-white/40">{campaigns.length}</span>
      <div class="rule-v h-4"></div>
      <span class="mono text-xs text-white/20">TIME 時間</span>
      <span class="mono text-xs text-white/40">{now.split(" ")[1] ?? ""}</span>
      <div class="ml-auto mono text-xs text-white/20">COPYRIGHT © 2077</div>
    </div>

  </div>

</div>
