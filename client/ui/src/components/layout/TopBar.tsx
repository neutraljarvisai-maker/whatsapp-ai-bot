import React from 'react';

interface TopBarProps {
  time: Date;
}

const TopBar: React.FC<TopBarProps> = ({ time }) => {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
  };

  const formatDay = (date: Date) => {
    return date.toLocaleDateString('en-GB', { weekday: 'long' }).toUpperCase();
  };

  return (
    <div className="w-full h-14 bg-vecta-panel/60 backdrop-blur-md border-b border-vecta-cyan/20 flex items-center justify-end px-10 gap-12 z-50">
      <div className="flex flex-col items-end">
        <span className="text-[8px] text-vecta-cyan/40 tracking-[0.3em] font-bold">SYSTEM DATE</span>
        <span className="text-xs text-vecta-text-primary tracking-widest font-black">{formatDate(time)}</span>
      </div>

      <div className="flex flex-col items-end">
        <span className="text-[8px] text-vecta-cyan/40 tracking-[0.3em] font-bold">OPERATIONAL DAY</span>
        <span className="text-xs text-vecta-text-primary tracking-widest font-black">{formatDay(time)}</span>
      </div>

      <div className="flex flex-col items-end min-w-[100px]">
        <span className="text-[8px] text-vecta-cyan/40 tracking-[0.3em] font-bold">CHRONO UNIT</span>
        <span className="text-sm text-vecta-cyan tracking-[0.2em] font-black font-mono drop-shadow-[0_0_8px_rgba(0,209,255,0.4)]">
          {formatTime(time)}
        </span>
      </div>
    </div>
  );
};

export default TopBar;
