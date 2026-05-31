import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-vecta-gradient flex flex-col items-center justify-center p-8 border border-vecta-cyan/20 shadow-[inset_0_0_100px_rgba(0,212,255,0.05)]">
      <h1 className="text-6xl font-bold tracking-[0.2em] text-vecta-cyan drop-shadow-[0_0_10px_rgba(0,212,255,0.5)] mb-8">
        VECTA OS
      </h1>

      <div className="flex flex-col items-center gap-6 p-8 bg-vecta-bg-metallic/50 border border-vecta-cyan/30 rounded-lg backdrop-blur-sm shadow-[0_0_30px_rgba(0,212,255,0.1)]">
        <button
          onClick={() => setCount((count) => count + 1)}
          className="px-6 py-2 bg-vecta-bg-matte border border-vecta-cyan hover:bg-vecta-cyan hover:text-vecta-bg-matte transition-all duration-300 rounded shadow-[0_0_15px_rgba(0,212,255,0.2)]"
        >
          SYSTEM PULSE: {count}
        </button>

        <p className="text-sm text-vecta-cyan/60 italic">
          Edit <code className="text-vecta-cyan">src/App.tsx</code> to modify interface
        </p>
      </div>

      <div className="mt-12 flex gap-8">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-vecta-green animate-pulse shadow-[0_0_8px_#39ff14]" />
          <span className="text-xs text-vecta-green font-bold tracking-widest uppercase">AI STATUS: ACTIVE</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-vecta-amber animate-pulse shadow-[0_0_8px_#ffbf00]" />
          <span className="text-xs text-vecta-amber font-bold tracking-widest uppercase">SHIELD STATUS: NOMINAL</span>
        </div>
      </div>

      <p className="mt-auto text-[10px] text-vecta-cyan/40 tracking-[0.5em] uppercase">
        Initialized Vite + React + TypeScript + Tailwind for VECTA
      </p>
    </div>
  )
}

export default App
