import React from 'react';

interface SidebarProps {
  logs?: string[];
}

const Sidebar: React.FC<SidebarProps> = ({ logs = ["System initialized...", "Establishing neural link...", "Ready for instructions."] }) => {
  return (
    <div className="w-64 border-r border-vecta-cyan/10 bg-black/40 backdrop-blur-md flex flex-col h-full overflow-hidden">
      <div className="p-3 border-b border-vecta-cyan/20">
        <h3 className="text-[10px] tracking-[0.2em] font-bold text-vecta-cyan/80 uppercase">Access Logs</h3>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-hide">
        {logs.map((log, i) => (
          <div key={i} className="text-[9px] font-mono text-vecta-cyan/40 break-words leading-relaxed">
            <span className="text-vecta-cyan/20 mr-2">[{new Date().toLocaleTimeString()}]</span>
            {log}
          </div>
        ))}
      </div>
      <div className="p-3 border-t border-vecta-cyan/10 bg-vecta-cyan/5">
        <div className="text-[8px] tracking-widest text-vecta-cyan/30 uppercase">Secure Terminal v2.0</div>
      </div>
    </div>
  );
};

export default Sidebar;
