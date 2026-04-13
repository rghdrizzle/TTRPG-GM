<script lang="ts">
  import { onMount } from "svelte"
  import { requireAuth } from "$lib/auth"

  const sessionId = Math.random().toString(36).substring(2, 10).toUpperCase()
  const now = new Date().toLocaleString("en-GB", { hour12: false }).replace(",", "")

  const rulebook = {
    id: "fist-ttrpg-v1",
    title: "FIST",
    subtitle: "Freelance Infantry Salvage & Tactics",
    version: "v1.0 — ULTRA EDITION",
    system: "FIST TTRPG",
    author: "CLAYPIGEONPRESS",
    pages: 48,
    status: "LOADED",
    description: "FIST is a tabletop roleplaying game about mercenaries doing paramilitary operations in a weird, pulpy, retro-future world. Players are operatives of FIST — a ragtag band of freelance soldiers, weirdos, and war criminals who take jobs nobody else will.",
    tags: ["MERCENARY", "RETRO-FUTURE", "TACTICAL", "PULP", "PARAMILITARY"],
    mechanics: [
      { name: "2d6 RESOLUTION", desc: "Roll 2d6 + attribute. 10+ is a full success, 7–9 is a partial success, 6- is a failure with consequences." },
      { name: "ATTRIBUTES", desc: "Three core attributes: METAL (strength, toughness), WIRE (speed, stealth), HEART (charisma, morale)." },
      { name: "ROLES", desc: "Each operative has a Role — a specialization like Medic, Demo Expert, or Infiltrator — that grants unique moves." },
      { name: "HP & STRESS", desc: "Operatives have HP for physical damage and Stress for mental strain. Both matter in the field." },
      { name: "WAR CARDS", desc: "FIST uses a deck of War Cards to introduce chaos and escalation mid-mission." },
      { name: "MISSIONS", desc: "Sessions are structured as missions with objectives, complications, and an extraction phase." },
    ],
    stats: [
      { label: "CHUNKS", value: "847" },
      { label: "VECTORS", value: "1536" },
      { label: "INDEX", value: "IVFFLAT" },
      { label: "SIMILARITY", value: "COSINE" },
    ]
  }

  onMount(() => {
    requireAuth()
  })
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
  .ticker { animation: ticker 25s linear infinite; white-space: nowrap; }
  @keyframes ticker {
    from { transform: translateX(100%); }
    to { transform: translateX(-100%); }
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
      <span class="text-white/40 text-xs mono">HTTPS://TTRPG.GM.SYSTEM/RULEBOOKS</span>
    </div>
    <div class="ml-auto flex gap-3">
      <span class="text-white/20 text-xs">□</span>
      <span class="text-white/20 text-xs">—</span>
      <span class="text-white/20 text-xs">✕</span>
    </div>
  </div>

  <!-- ═══ NAV ═══ -->
  <div class="border-b border-white/10 h-10 flex items-center px-6 flex-shrink-0">
    <div class="flex items-center gap-8 flex-1">
      <span class="display text-xl tracking-wider text-white">/RULEBOOKS</span>
      <div class="border-l border-white/15 h-5"></div>
      <a href="/dashboard" class="text-xs text-white/30 mono tracking-widest hover:text-white/60 transition-colors">CAMPAIGNS</a>
      <a href="/rulebooks" class="text-xs text-white mono tracking-widest border-b border-white/60 pb-0.5">RULEBOOKS</a>
      <a href="/sessions" class="text-xs text-white/30 mono tracking-widest hover:text-white/60 transition-colors">SESSIONS</a>
    </div>
    <div class="text-xs text-white/20 mono">SESSION [{sessionId}]</div>
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
  <div class="flex-1 relative max-w-[1400px] mx-auto w-full px-6 py-10">

    <!-- Page header -->
    <div class="border-b border-white/10 pb-6 mb-8 grid grid-cols-12 gap-0">
      <div class="col-span-8 border-r border-white/10 pr-8">
        <div class="text-white/20 text-xs mono tracking-[0.4em] mb-2">LOADED RULEBOOKS // VECTOR INDEX</div>
        <div class="display text-[72px] leading-none text-white">/RULEBOOKS</div>
        <div class="display text-[72px] leading-none text-white/10">規則書庫</div>
      </div>
      <div class="col-span-4 pl-8 flex flex-col justify-between">
        <div class="space-y-2">
          {#each [
            { label: "TOTAL BOOKS", value: "01" },
            { label: "TOTAL CHUNKS", value: "847" },
            { label: "INDEX TYPE", value: "IVFFLAT" },
            { label: "STATUS", value: "● ONLINE" },
          ] as stat}
            <div class="flex justify-between border-b border-white/10 pb-1 text-xs mono">
              <span class="text-white/20">{stat.label}</span>
              <span class="text-white/60 {stat.label === 'STATUS' ? 'blink' : ''}">{stat.value}</span>
            </div>
          {/each}
        </div>
        <div class="mt-4">
          <div class="flex gap-px h-8">
            {#each Array(60) as _, i}
              <div class="flex-1 bg-white" style="opacity: {Math.random() > 0.4 ? Math.random() * 0.5 + 0.1 : 0};"></div>
            {/each}
          </div>
          <div class="text-white/20 text-xs mono mt-1">RULEBOOK-VECTOR-INDEX</div>
        </div>
      </div>
    </div>

    <!-- Rulebook card -->
    <div class="border border-white/15 relative">

      <!-- Left accent -->
      <div class="absolute top-0 left-0 w-1 h-full bg-white/60"></div>

      <!-- Card header -->
      <div class="border-b border-white/10 grid grid-cols-12 gap-0">

        <div class="col-span-1 border-r border-white/10 flex items-center justify-center py-6">
          <div class="display text-4xl text-white/20">01</div>
        </div>

        <div class="col-span-7 border-r border-white/10 px-8 py-6">
          <div class="text-white/20 text-xs mono tracking-widest mb-2">RULEBOOK_NODE // LOADED</div>
          <div class="display text-5xl text-white tracking-wider leading-none">{rulebook.title}</div>
          <div class="mono text-sm text-white/40 mt-1 tracking-wider">{rulebook.subtitle}</div>
          <div class="flex gap-3 mt-4 flex-wrap">
            {#each rulebook.tags as tag}
              <span class="mono text-xs text-white/40 border border-white/15 px-2 py-0.5">{tag}</span>
            {/each}
          </div>
        </div>

        <div class="col-span-4 px-6 py-6 flex flex-col justify-between">
          <div class="space-y-2">
            {#each [
              { label: "VERSION", value: rulebook.version },
              { label: "AUTHOR", value: rulebook.author },
              { label: "PAGES", value: String(rulebook.pages) },
              { label: "STATUS", value: rulebook.status },
            ] as item}
              <div class="flex justify-between border-b border-white/10 pb-1 text-xs mono">
                <span class="text-white/20">{item.label}</span>
                <span class="text-white/60">{item.value}</span>
              </div>
            {/each}
          </div>
          <div class="mt-4 grid grid-cols-2 gap-2">
            {#each rulebook.stats as stat}
              <div class="border border-white/10 p-2 text-center">
                <div class="display text-xl text-white">{stat.value}</div>
                <div class="mono text-xs text-white/20">{stat.label}</div>
              </div>
            {/each}
          </div>
        </div>

      </div>

      <!-- Description -->
      <div class="border-b border-white/10 grid grid-cols-12 gap-0">
        <div class="col-span-1 border-r border-white/10"></div>
        <div class="col-span-11 px-8 py-6">
          <div class="text-white/20 text-xs mono tracking-widest mb-3">DESCRIPTION // 說明</div>
          <p class="mono text-sm text-white/60 leading-relaxed max-w-2xl">{rulebook.description}</p>
        </div>
      </div>

      <!-- Mechanics -->
      <div class="grid grid-cols-12 gap-0">
        <div class="col-span-1 border-r border-white/10"></div>
        <div class="col-span-11">
          <div class="border-b border-white/10 px-8 py-3">
            <div class="text-white/20 text-xs mono tracking-widest">CORE MECHANICS // 核心機制</div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-0">
            {#each rulebook.mechanics as mechanic, i}
              <div class="border-r border-b border-white/10 p-6 hover:bg-white/5 transition-colors group">
                <div class="flex items-start gap-3 mb-3">
                  <div class="display text-2xl text-white/10 group-hover:text-white/30 transition-colors">
                    {String(i + 1).padStart(2, "0")}
                  </div>
                  <div class="mono text-xs text-white/80 tracking-widest pt-1">{mechanic.name}</div>
                </div>
                <div class="border-t border-white/10 pt-3">
                  <p class="mono text-xs text-white/40 leading-relaxed">{mechanic.desc}</p>
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>

      <!-- Action bar -->
      <div class="border-t border-white/10 grid grid-cols-12 gap-0">
        <div class="col-span-1 border-r border-white/10"></div>
        <div class="col-span-11 px-8 py-4 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-1.5 h-1.5 rounded-full bg-white blink"></div>
            <span class="mono text-xs text-white/40 tracking-widest">RAG INDEX ACTIVE — READY FOR QUERIES</span>
          </div>
          <a href="/campaigns/new?rulebook=fist-ttrpg-v1"
            class="mono text-xs tracking-widest px-6 py-2 border border-white/30 text-white hover:bg-white hover:text-black transition-all duration-150">
            + START CAMPAIGN WITH FIST
          </a>
        </div>
      </div>

    </div>

  </div>

  <!-- ═══ FOOTER ═══ -->
  <div class="border-t border-white/10 flex-shrink-0">
    <div class="h-6 overflow-hidden flex items-center border-b border-white/10">
      <div class="ticker mono text-xs text-white/20">
        TTRPG-GM-SYSTEM &nbsp;///&nbsp; FIST TTRPG LOADED &nbsp;///&nbsp;
        VECTOR INDEX ACTIVE &nbsp;///&nbsp; RAG PIPELINE ONLINE &nbsp;///&nbsp;
        847 CHUNKS INDEXED &nbsp;///&nbsp; COSINE SIMILARITY &nbsp;///&nbsp;
        TTRPG-GM-SYSTEM &nbsp;///&nbsp;
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
