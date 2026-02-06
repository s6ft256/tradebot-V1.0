'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Settings, Shield, AlertTriangle } from 'lucide-react';

interface SettingsData {
  risk: {
    max_open_positions: number;
    max_trades_per_day: number;
    max_risk_per_trade_percent: number;
  };
}

export function SettingsPanel() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await fetch('/api/settings', {
          headers: {
            'X-API-Key': 'dev-key',
          },
        });
        if (res.ok) {
          setSettings(await res.json());
        }
      } catch (err) {
        console.error('Failed to fetch settings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  if (loading) {
    return (
      <Card className="bg-slate-900/50 border-slate-800">
        <CardContent className="py-8">
          <div className="text-center text-slate-400">Loading settings...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-400" />
            Risk Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Max Open Positions</span>
              <span className="text-white font-mono text-lg">
                {settings?.risk?.max_open_positions ?? 2}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Max Trades per Day</span>
              <span className="text-white font-mono text-lg">
                {settings?.risk?.max_trades_per_day ?? 6}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Max Risk per Trade</span>
              <span className="text-white font-mono text-lg">
                {settings?.risk?.max_risk_per_trade_percent ?? 1.0}%
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Trading Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="text-slate-300">Paper Trading Active</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-slate-600"></div>
              <span className="text-slate-500">Live Trading Disabled</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
              <span className="text-slate-300">Risk Checks Enabled</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
              <span className="text-slate-300">AI Advisory Layer Active</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
