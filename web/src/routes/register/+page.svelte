<script lang="ts">
  let username = $state("")
  let email = $state("")
  let password = $state("")
  let confirmPassword = $state("")
  let error = $state("")
  let loading = $state(false)

  const sessionId = Math.random().toString(36).substring(2, 10).toUpperCase()
  const now = new Date().toLocaleString("en-GB", { hour12: false }).replace(",", "")

  async function handleSubmit() {
    error = ""
    if (password !== confirmPassword) {
      error = "PASSWORD MISMATCH — fields do not match"
      return
    }
    loading = true

    const res = await fetch(`${import.meta.env.VITE_API_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),  // ← added username
    })

    const data = await res.json()
    loading = false

    if (data.status === 200) {
      window.location.href = "/login"
    } else {
      error = data.message || "REGISTRATION FAILED"
    }
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
  .blink { animation: blink 1.2s step-end infinite; }
  @keyframes blink { 50% { opacity: 0; } }
  .ticker { animation: ticker 20s linear infinite; white-space: nowrap; }
  @keyframes ticker {
    from { transform: translateX(100%); }
    to { transform: translateX(-100%); }
  }
  input:-webkit-autofill {
    -webkit-box-shadow: 0 0 0 100px black inset;
    -webkit-text-fill-color: white;
    caret-color: white;
  }
  input:focus { outline: none; }
</style>

<div class="min-h-screen bg-black text-white scanline mono overflow-hidden relative flex flex-col">

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
      <span class="text-white/40 text-xs mono">HTTPS://TTRPG.GM.SYSTEM/REGISTER</span>
    </div>
    <div class="ml-auto flex gap-3">
      <span class="text-white/20 text-xs">□</span>
      <span class="text-white/20 text-xs">—</span>
      <span class="text-white/20 text-xs">✕</span>
    </div>
  </div>

  <!-- ═══ NAV ═══ -->
  <div class="border-b border-white/10 h-10 flex items-center px-6 flex-shrink-0">
    <div class="display text-xl tracking-wider text-white">/AUTH</div>
    <div class="border-l border-white/15 h-5 mx-6"></div>
    <span class="text-xs text-white mono tracking-widest">REGISTER 註冊</span>
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

  <!-- ═══ MAIN SPLIT ═══ -->
  <div class="flex flex-1 overflow-hidden">

    <!-- LEFT — Visual panel -->
    <div class="hidden md:flex w-1/2 border-r border-white/10 flex-col overflow-hidden">
      <div class="flex-1 flex flex-col justify-between p-10">

        <div>
          <div class="text-white/20 text-xs mono tracking-[0.4em] mb-4">AUTH NODE // NEW IDENTITY CREATION</div>
          <div class="display text-[80px] leading-none text-white">/REGISTER</div>
          <div class="display text-[80px] leading-none text-white/10">新規登録</div>
        </div>

        <!-- Process steps -->
        <div class="mt-8 space-y-0 border border-white/10">
          {#each [
            { step: "01", label: "CHOOSE HANDLE", sub: "用戶名" },
            { step: "02", label: "PROVIDE EMAIL", sub: "電子郵件" },
            { step: "03", label: "SET PASSWORD", sub: "設定密碼" },
            { step: "04", label: "NODE INITIALIZED", sub: "節點初始化" },
          ] as item}
            <div class="flex items-center gap-4 border-b border-white/10 last:border-0 px-4 py-3 group hover:bg-white/5 transition-colors">
              <div class="display text-2xl text-white/20 group-hover:text-white/40 transition-colors w-8">{item.step}</div>
              <div class="border-l border-white/10 pl-4">
                <div class="mono text-xs text-white/60 tracking-widest">{item.label}</div>
                <div class="mono text-xs text-white/20">{item.sub}</div>
              </div>
            </div>
          {/each}
        </div>

        <!-- Metadata -->
        <div class="mt-8 border-t border-white/10 pt-4 grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <div class="flex justify-between text-xs mono">
              <span class="text-white/20">DATE 日期</span>
              <span class="text-white/50">{now.split(" ")[0]}</span>
            </div>
            <div class="flex justify-between text-xs mono">
              <span class="text-white/20">TIME 時間</span>
              <span class="text-white/50">{now.split(" ")[1] ?? ""}</span>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-xs mono">
              <span class="text-white/20">PROTOCOL</span>
              <span class="text-white/50">JWT / RS256</span>
            </div>
            <div class="flex justify-between text-xs mono">
              <span class="text-white/20">STATUS</span>
              <span class="text-white mono flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-white blink inline-block"></span>
                ONLINE
              </span>
            </div>
          </div>
        </div>

      </div>

      <!-- Barcode strip -->
      <div class="border-t border-white/10 p-4">
        <div class="flex gap-px h-8">
          {#each Array(80) as _, i}
            <div class="flex-1 bg-white" style="opacity: {Math.random() > 0.4 ? Math.random() * 0.5 + 0.1 : 0};"></div>
          {/each}
        </div>
        <div class="text-white/20 text-xs mono mt-1 tracking-widest">NEW-IDENTITY-TTRPG-GM-SYS</div>
      </div>

    </div>

    <!-- RIGHT — Form panel -->
    <div class="w-full md:w-1/2 flex flex-col">
      <div class="flex-1 flex items-center justify-center p-10">
        <div class="w-full max-w-sm">

          <!-- Form header -->
          <div class="border-b border-white/10 pb-4 mb-8">
            <div class="text-white/20 text-xs mono tracking-[0.4em] mb-1">INITIALIZE NEW NODE</div>
            <div class="display text-4xl text-white tracking-wider">CREATE IDENTITY</div>
          </div>

          <!-- Error -->
          {#if error}
            <div class="mb-6 border border-white/20 bg-white/5 px-4 py-3">
              <span class="text-white/40 mono text-xs">[ERR]</span>
              <span class="text-white mono text-xs ml-2">{error}</span>
            </div>
          {/if}

          <!-- Form -->
          <form onsubmit={(e) => { e.preventDefault(); handleSubmit() }} class="space-y-0">
            <div class="border border-white/15 p-4 hover:border-white/30 transition-colors">
  <div class="text-white/30 text-xs mono tracking-widest mb-2">
    <span class="text-white/20">&gt;</span> HANDLE 用戶名
  </div>
  <input
    bind:value={username}
    type="text"
    required
    placeholder="your_alias"
    class="w-full bg-transparent text-white mono text-sm placeholder-white/20"
    style="outline: none; border: none;"
  />
</div>

<!-- then email below it with border-t-0 -->
<div class="border border-white/15 border-t-0 p-4 hover:border-white/30 transition-colors">
            <div class="border border-white/15 p-4 hover:border-white/30 transition-colors">
              <div class="text-white/30 text-xs mono tracking-widest mb-2">
                <span class="text-white/20">&gt;</span> EMAIL 電子郵件
              </div>
              <input
                bind:value={email}
                type="email"
                required
                placeholder="user@domain.io"
                class="w-full bg-transparent text-white mono text-sm placeholder-white/20"
                style="outline: none; border: none;"
              />
            </div>

            <div class="border border-white/15 border-t-0 p-4 hover:border-white/30 transition-colors">
              <div class="text-white/30 text-xs mono tracking-widest mb-2">
                <span class="text-white/20">&gt;</span> PASSWORD 密碼
              </div>
              <input
                bind:value={password}
                type="password"
                required
                placeholder="••••••••••••"
                class="w-full bg-transparent text-white mono text-sm placeholder-white/20"
                style="outline: none; border: none;"
              />
            </div>

            <div class="border border-white/15 border-t-0 p-4 hover:border-white/30 transition-colors">
              <div class="text-white/30 text-xs mono tracking-widest mb-2">
                <span class="text-white/20">&gt;</span> CONFIRM 確認密碼
              </div>
              <input
                bind:value={confirmPassword}
                type="password"
                required
                placeholder="••••••••••••"
                class="w-full bg-transparent text-white mono text-sm placeholder-white/20"
                style="outline: none; border: none;"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              class="w-full border border-white/15 border-t-0 py-4 mono text-xs tracking-[0.3em] text-white hover:bg-white hover:text-black transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed display text-lg"
            >
              {#if loading}
                INITIALIZING NODE <span class="blink">_</span>
              {:else}
                &gt; FORGE IDENTITY
              {/if}
            </button>

          </form>

          <!-- Divider -->
          <div class="flex items-center gap-4 my-6">
            <div class="h-px flex-1 bg-white/10"></div>
            <span class="text-white/20 mono text-xs">//</span>
            <div class="h-px flex-1 bg-white/10"></div>
          </div>

          <!-- Login link -->
          <div class="text-center">
            <span class="text-white/20 mono text-xs tracking-widest">ALREADY ON THE GRID? </span>
            <a href="/login" class="text-white mono text-xs tracking-widest hover:text-white/60 transition-colors underline underline-offset-4">
              LOGIN_NODE
            </a>
          </div>

          <!-- Bottom metadata -->
          <div class="mt-10 pt-4 border-t border-white/10 grid grid-cols-2 gap-2">
            <div class="mono text-xs text-white/20">ENC: AES-256</div>
            <div class="mono text-xs text-white/20 text-right">VER: 2.7.7</div>
            <div class="mono text-xs text-white/20">PROTO: JWT</div>
            <div class="mono text-xs text-white/20 text-right">NET: SECURE</div>
          </div>

        </div>
      </div>
    </div>

  </div>

  <!-- ═══ FOOTER ═══ -->
  <div class="border-t border-white/10 flex-shrink-0">
    <div class="h-6 overflow-hidden flex items-center border-b border-white/10">
      <div class="ticker mono text-xs text-white/20">
        TTRPG-GM-SYSTEM &nbsp;///&nbsp; NEW NODE REGISTRATION &nbsp;///&nbsp;
        ENCRYPTED CONNECTION &nbsp;///&nbsp; JWT PROTOCOL ACTIVE &nbsp;///&nbsp;
        TTRPG-GM-SYSTEM &nbsp;///&nbsp; IDENTITY CREATION &nbsp;///&nbsp;
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
