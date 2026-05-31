import { useState } from 'react'
import Shell from './components/layout/Shell'

function App() {
  const [status, setStatus] = useState<'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING'>('IDLE')

  return (
    <Shell status={status}>
      <div className="flex flex-col items-center">
        <div className="text-4xl font-bold tracking-[0.5em] text-vecta-cyan drop-shadow-[0_0_15px_rgba(0,212,255,0.8)] mb-4 uppercase">
          VECTA CORE
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => setStatus('LISTENING')}
            className="text-[10px] px-4 py-1 border border-vecta-cyan/40 hover:bg-vecta-cyan hover:text-black transition-all uppercase tracking-widest"
          >
            Test Listen
          </button>
          <button
            onClick={() => setStatus('THINKING')}
            className="text-[10px] px-4 py-1 border border-vecta-cyan/40 hover:bg-vecta-cyan hover:text-black transition-all uppercase tracking-widest"
          >
            Test Think
          </button>
          <button
            onClick={() => setStatus('IDLE')}
            className="text-[10px] px-4 py-1 border border-vecta-cyan/40 hover:bg-vecta-cyan hover:text-black transition-all uppercase tracking-widest"
          >
            Test Idle
          </button>
        </div>
      </div>
    </Shell>
  )
}

export default App
