import React from 'react';
import type { SystemStats } from '../../hooks/useVectaState';

interface SystemStatusProps {
  stats: SystemStats;
}

const SystemStatus: React.FC<SystemStatusProps> = ({ stats }) => {
  const metrics = [
    { label: 'CPU LOAD', value: `${stats.cpu.toFixed(1)}%` },
    { label: 'GPU CORE', value: `${stats.gpu.toFixed(1)}%` },
    { label: 'RAM USAGE', value: `${stats.ram}GB / 32GB` },
    { label: 'UPLINK', value: stats.network },
  ];

  const subsystems = [
    { label: 'VISION SYSTEM', active: stats.vision },
    { label: 'VOICE MODULE', active: stats.voice },
  ];

  return (
    <div className="w-80 h-full bg-vecta-panel/75 backdrop-blur-sm border-r border-vecta-cyan/20 p-6 flex flex-col gap-10 overflow-y-auto z-20">
      <section>
        <h2 className="text-[10px] tracking-[0.4em] font-black text-vecta-cyan/60 uppercase mb-6 border-b border-vecta-cyan/10 pb-2">
          System Telemetry
        </h2>
        <div className="space-y-6">
          {metrics.map(m => (
            <div key={m.label}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-[9px] text-vecta-text-secondary tracking-widest font-bold opacity-70 uppercase">{m.label}</span>
                <span className="text-[8px] text-vecta-cyan/40 font-mono">OK</span>
              </div>
              <div className="text-lg font-black tracking-tighter text-vecta-cyan drop-shadow-[0_0_8px_rgba(0,209,255,0.2)]">
                {m.value}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-[10px] tracking-[0.4em] font-black text-vecta-cyan/60 uppercase mb-6 border-b border-vecta-cyan/10 pb-2">
          Neural Layers
        </h2>
        <div className="space-y-4">
          {subsystems.map(s => (
            <div key={s.label} className="flex items-center justify-between p-3 bg-black/20 border border-vecta-cyan/5 rounded-sm">
              <span className="text-[10px] text-vecta-text-primary tracking-[0.2em] font-bold">
                {s.label}
              </span>
              <div className={`w-1.5 h-1.5 rounded-full ${s.active ? 'bg-vecta-cyan shadow-[0_0_8px_#00D1FF]' : 'bg-red-900'}`} />
            </div>
          ))}
        </div>
      </section>

      <div className="mt-auto pt-4 border-t border-vecta-cyan/5">
        <div className="text-[8px] font-mono text-vecta-text-secondary/30 uppercase leading-relaxed">
          Wayne Enterprises // Terminal v7.4<br />
          Classified Information
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
