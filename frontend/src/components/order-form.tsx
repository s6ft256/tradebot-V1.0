'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpCircle, ArrowDownCircle, Loader2 } from 'lucide-react';

export function OrderForm() {
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [orderType, setOrderType] = useState('market');
  const [amount, setAmount] = useState('0.1');
  const [price, setPrice] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const res = await fetch('/api/paper/order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          side,
          order_type: orderType,
          amount: parseFloat(amount),
          price: price ? parseFloat(price) : undefined,
          current_price: 50000,
        }),
      });
      
      if (res.ok) {
        setResult(await res.json());
      }
    } catch (err) {
      console.error('Order failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white">Paper Trade Order</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">
                Symbol
              </label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option>BTC/USDT</option>
                <option>ETH/USDT</option>
                <option>SOL/USDT</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">
                Side
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setSide('buy')}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md font-medium transition-colors ${
                    side === 'buy'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                      : 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700'
                  }`}
                >
                  <ArrowUpCircle className="w-4 h-4" />
                  Buy
                </button>
                <button
                  type="button"
                  onClick={() => setSide('sell')}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md font-medium transition-colors ${
                    side === 'sell'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/50'
                      : 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700'
                  }`}
                >
                  <ArrowDownCircle className="w-4 h-4" />
                  Sell
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">
                Order Type
              </label>
              <select
                value={orderType}
                onChange={(e) => setOrderType(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="market">Market</option>
                <option value="limit">Limit</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">
                Amount
              </label>
              <input
                type="number"
                step="0.0001"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                required
              />
            </div>

            {orderType === 'limit' && (
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">
                  Limit Price
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2 rounded-md font-medium transition-colors flex items-center justify-center gap-2 ${
                side === 'buy'
                  ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
                  : 'bg-rose-500 hover:bg-rose-600 text-white'
              }`}
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {side === 'buy' ? 'Place Buy Order' : 'Place Sell Order'}
            </button>
          </form>
        </CardContent>
      </Card>

      {result && (
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Order Result</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Order ID:</span>
                <span className="text-white font-mono">{result.order_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Symbol:</span>
                <span className="text-white">{result.symbol}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Side:</span>
                <span className={`capitalize ${result.side === 'buy' ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {result.side}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Amount:</span>
                <span className="text-white">{result.amount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Avg Price:</span>
                <span className="text-white">${result.average_price?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Status:</span>
                <span className="text-emerald-400 capitalize">{result.status}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
