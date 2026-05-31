import React, { useState, useEffect } from 'react';

interface StatusBarProps {
  status?: 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';
}

const StatusBar: React.FC<StatusBarProps> = ({ status = 'IDLE' }) => {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const getStatusColor = () => {
    switch (status) {
      case 'LISTENING': return 'bg-vecta-green shadow-[0_0_8px_#39ff14]';
      case 'THINKING': return 'bg-vecta-amber shadow-[0_0_8px_#ffbf00]';
      case 'SPEAKING': return 'bg-vecta-cyan shadow-[0_0_8px_#00d4ff]';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div className="h-10 border-b border-vecta-cyan/20 bg-vecta-bg-matte flex items-center justify-between px-4 select-none">
      <div className="flex items-center gap-4">
        <div className="text-[10px] tracking-[0.3em] font-bold text-vecta-cyan/60 uppercase">VECTA OS // HOLOGRAPHIC INTERFACE</div>
      </div>

      <div className="flex items-center gap-3">
        <span className={`w-2 h-2 rounded-full ${getStatusColor()} animate-pulse`} />
        <span className="text-[10px] tracking-[0.2em] font-bold text-vecta-cyan uppercase">{status}</span>
      </div>

      <div className="text-[10px] tracking-[0.2em] font-bold text-vecta-cyan/40">
        {time}
      </div>
    </div>
  );
};

export default StatusBar;
