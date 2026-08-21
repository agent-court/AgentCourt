'use client';

import { useState, useEffect } from 'react';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { Shield, Activity, Scale, CheckCircle2, Clock, Terminal, AlertTriangle } from 'lucide-react';
import { CreateJobModal } from '@/components/CreateJobModal';
import CaseDetailModal from '@/components/CaseDetailModal';

interface Job {
  job_id: number;
  client: string;
  provider: string;
  evaluator: string;
  status: number;
  escrow_amount_wei: string;
  deliverable_hash: string;
}

interface WsEvent {
  type: string;
  job_id?: number;
  verdict?: {
    consensus_bps: number;
    opinion: string;
    juror_breakdown: Array<{ juror: string; basis_points: number; reasoning: string }>;
    outliers_dropped: Array<any>;
  };
  tx_hash?: string;
  block_number?: number;
  error?: string;
}

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [events, setEvents] = useState<WsEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);

  const fetchJobs = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/jobs');
      if (res.ok) {
        const data = await res.json();
        setJobs(data.jobs || []);
      }
    } catch (err) {
      console.error('Error fetching jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 6000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/ws/stream');

    ws.onopen = () => setWsConnected(true);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setEvents((prev) => [data, ...prev].slice(0, 20));
        if (data.type === 'SETTLEMENT_CONFIRMED' || data.type === 'JOB_SUBMITTED') {
          fetchJobs();
        }
      } catch (err) {
        console.error('WS Parse Error:', err);
      }
    };
    ws.onclose = () => setWsConnected(false);
    return () => ws.close();
  }, []);

  const getStatusBadge = (status: number) => {
    switch (status) {
      case 0:
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20"><Clock className="w-3.5 h-3.5" /> Created</span>;
      case 1:
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20"><Activity className="w-3.5 h-3.5" /> Funded</span>;
      case 2:
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20"><Scale className="w-3.5 h-3.5" /> Deliberating</span>;
      default:
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><CheckCircle2 className="w-3.5 h-3.5" /> Settled ({status} bps)</span>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
              <Scale className="w-6 h-6" />
            </div>
            <div>
              <span className="font-bold text-lg text-white">AgentCourt</span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">Base Sepolia</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <CreateJobModal onJobCreated={fetchJobs} />
            <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800">
              <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
              <span className="text-slate-400">{wsConnected ? 'Oracle Live' : 'Reconnecting'}</span>
            </div>
            <ConnectButton />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-400" />
              Active Escrow Registry ({jobs.length})
            </h2>
            <button onClick={fetchJobs} className="text-xs text-slate-400 hover:text-white transition">Refresh</button>
          </div>

          {loading ? (
            <div className="p-12 text-center text-slate-500 border border-slate-900 rounded-xl bg-slate-900/20">Loading on-chain state...</div>
          ) : (
            <div className="grid gap-4">
              {jobs.map((job) => (
                <div key={job.job_id}
                onClick={() => setSelectedCaseId(job.job_id)}
                style={{ cursor: 'pointer' }} className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 hover:border-slate-700 transition">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-bold text-white">Escrow Case #{job.job_id}</span>
                    {getStatusBadge(job.status)}
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs text-slate-400 font-mono">
                    <div>Client: <span className="text-slate-200">{job.client.slice(0, 6)}...{job.client.slice(-4)}</span></div>
                    <div>Provider: <span className="text-slate-200">{job.provider.slice(0, 6)}...{job.provider.slice(-4)}</span></div>
                    <div className="col-span-2 truncate">Hash: <span className="text-blue-400">{job.deliverable_hash}</span></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Terminal className="w-5 h-5 text-emerald-400" />
            Live Deliberation Terminal
          </h2>
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/70 h-[600px] overflow-y-auto space-y-3 font-mono text-xs">
            {events.length === 0 ? (
              <p className="text-slate-500 text-center py-20">Waiting for on-chain events...</p>
            ) : (
              events.map((ev, idx) => (
                <div key={idx} className="p-3 rounded-lg border border-slate-800/80 bg-slate-950/60 space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-blue-400 font-semibold">
                    <span>⚡ {ev.type}</span>
                    {ev.job_id && <span>Job #{ev.job_id}</span>}
                  </div>
                  {ev.verdict && (
                    <div className="space-y-2 mt-1 pt-1 border-t border-slate-900">
                      <div className="text-emerald-400 font-bold">Consensus: {ev.verdict.consensus_bps} bps</div>
                      <div className="space-y-1">
                        {ev.verdict.juror_breakdown.map((j, i) => (
                          <div key={i} className="text-slate-300">
                            <span className="text-purple-400">{j.juror}</span>: {j.basis_points} bps - <span className="text-slate-400">{j.reasoning}</span>
                          </div>
                        ))}
                      </div>
                      {ev.verdict.outliers_dropped?.length > 0 && (
                        <div className="text-amber-400 flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" /> Dropped Outlier: {ev.verdict.outliers_dropped.map(o => o.juror).join(', ')}
                        </div>
                      )}
                    </div>
                  )}
                  {ev.tx_hash && <div className="text-slate-500 truncate">TX: {ev.tx_hash}</div>}
                </div>
              ))
            )}
          </div>
        </div>
        <CaseDetailModal jobId={selectedCaseId} onClose={() => setSelectedCaseId(null)} />
    </main>
    </div>
  );
}
