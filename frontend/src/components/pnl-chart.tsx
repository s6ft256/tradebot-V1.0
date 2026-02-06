'use client';

import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const data = [
  { time: '00:00', pnl: 0 },
  { time: '04:00', pnl: 0.5 },
  { time: '08:00', pnl: -0.2 },
  { time: '12:00', pnl: 1.2 },
  { time: '16:00', pnl: 0.8 },
  { time: '20:00', pnl: 1.5 },
  { time: '23:59', pnl: 0 },
];

export function PnLChart() {
  const gradientOffset = useMemo(() => {
    const dataMax = Math.max(...data.map((i) => i.pnl));
    const dataMin = Math.min(...data.map((i) => i.pnl));

    if (dataMax <= 0) return 0;
    if (dataMin >= 0) return 1;

    return dataMax / (dataMax - dataMin);
  }, []);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="splitColor" x1="0" y1="0" x2="0" y2="1">
              <stop offset={gradientOffset} stopColor="#10b981" stopOpacity={0.3} />
              <stop offset={gradientOffset} stopColor="#f43f5e" stopOpacity={0.3} />
            </linearGradient>
            <linearGradient id="splitStroke" x1="0" y1="0" x2="0" y2="1">
              <stop offset={gradientOffset} stopColor="#10b981" stopOpacity={1} />
              <stop offset={gradientOffset} stopColor="#f43f5e" stopOpacity={1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
          <YAxis stroke="#64748b" fontSize={12} unit="%" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#f1f5f9',
            }}
          />
          <Area
            type="monotone"
            dataKey="pnl"
            stroke="url(#splitStroke)"
            fill="url(#splitColor)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
