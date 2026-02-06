'use client';

import { useEffect, useState } from 'react';
import { Wifi, WifiOff } from 'lucide-react';

export function WebSocketStatus() {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Note: WebSocket connection would go here
    // For now, just showing the UI component
    setConnected(true);
  }, []);

  return (
    <div className={`flex items-center gap-2 px-2 py-1 rounded-md text-xs font-medium ${
      connected 
        ? 'bg-emerald-500/10 text-emerald-400' 
        : 'bg-rose-500/10 text-rose-400'
    }`}>
      {connected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
      {connected ? 'Live' : 'Disconnected'}
    </div>
  );
}
