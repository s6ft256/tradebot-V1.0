'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Activity, Wallet, Settings, BarChart3, Zap } from 'lucide-react';
import { PnLChart } from '@/components/pnl-chart';
import { OrderForm } from '@/components/order-form';
import { SettingsPanel } from '@/components/settings-panel';
import { WebSocketStatus } from '@/components/websocket-status';

interface DashboardData {
  status: string;
  open_positions: number;
  daily_pnl_percent: number;
}

interface HealthData {
  status: string;
}

export default function Dashboard() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dashRes, healthRes] = await Promise.all([
          fetch('/api/dashboard/summary'),
          fetch('/api/health'),
        ]);
        
        if (dashRes.ok) setDashboard(await dashRes.json());
        if (healthRes.ok) setHealth(await healthRes.json());
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 rounded-lg">
              <Zap className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">TradeBot</h1>
              <p className="text-sm text-slate-400">AI-Assisted Crypto Trading</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <WebSocketStatus />
            <Badge variant={health?.status === 'ok' ? 'default' : 'destructive'}>
              {health?.status === 'ok' ? 'System Online' : 'Offline'}
            </Badge>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Open Positions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {dashboard?.open_positions ?? 0}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                {(dashboard?.daily_pnl_percent ?? 0) >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-rose-400" />
                )}
                Daily P&L
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${
                (dashboard?.daily_pnl_percent ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}>
                {(dashboard?.daily_pnl_percent ?? 0) >= 0 ? '+' : ''}
                {(dashboard?.daily_pnl_percent ?? 0).toFixed(2)}%
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Wallet className="w-4 h-4" />
                Paper Balance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">$10,000.00</div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Total Trades
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">0</div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="chart" className="space-y-4">
          <TabsList className="bg-slate-900 border border-slate-800">
            <TabsTrigger value="chart">Performance</TabsTrigger>
            <TabsTrigger value="trade">Paper Trade</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="chart" className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">P&L History</CardTitle>
              </CardHeader>
              <CardContent>
                <PnLChart />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trade">
            <OrderForm />
          </TabsContent>

          <TabsContent value="settings">
            <SettingsPanel />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
