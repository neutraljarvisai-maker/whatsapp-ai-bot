import React from 'react';
import { motion } from 'framer-motion';

const SystemStatus: React.FC = () => {
  const metrics = [
    { label: 'CPU', value: '12%', status: 'NOMINAL' },
    { label: 'MEMORY', value: '4.2GB / 32GB', status: 'NOMINAL' },
    { label: 'NETWORK', value: '128 MBPS', status: 'STABLE' },
  ];

  const states = [
    { label: 'VOICE', active: true },
    { label: 'VISION', active: true },
    { label: 'AUTOMATION', active: false },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="w-80 h-full bg-vecta-panel border-r border-vecta-cyan/20 p-6 flex flex-col gap-8"
    >
      <section>
        <h2 className="text-xs tracking-[0.3em] font-bold text-vecta-cyan uppercase mb-4">Core Telemetry</h2>
        <div className="space-y-4">
          {metrics.map(m => (
            <div key={m.label} className="bg-black/40 border border-vecta-cyan/10 p-3 rounded-sm">
              <div className="flex justify-between items-end mb-1">
                <span className="text-[10px] text-vecta-text-secondary tracking-widest">{m.label}</span>
                <span className="text-[10px] text-vecta-cyan font-bold">{m.status}</span>
              </div>
              <div className="text-sm font-bold text-vecta-text-primary">{m.value}</div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xs tracking-[0.3em] font-bold text-vecta-cyan uppercase mb-4">Neural Layers</h2>
        <div className="space-y-2">
          {states.map(s => (
            <div key={s.label} className="flex items-center justify-between p-2 border-b border-vecta-cyan/5">
              <span className="text-xs text-vecta-text-primary tracking-wider">{s.label}</span>
              <div className={`w-2 h-2 rounded-full ${s.active ? 'bg-vecta-cyan shadow-[0_0_8px_#00D1FF]' : 'bg-vecta-text-secondary/20'}`} />
            </div>
          ))}
        </div>
      </section>
    </motion.div>
  );
};

export default SystemStatus;
