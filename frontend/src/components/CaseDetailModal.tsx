"use client";

import React, { useEffect, useState } from "react";

interface CaseDetailModalProps {
  jobId: number | null;
  onClose: () => void;
}

export default function CaseDetailModal({ jobId, onClose }: CaseDetailModalProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (jobId === null) return;
    setLoading(true);
    fetch(`http://127.0.0.1:8000/cases/${jobId}`)
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [jobId]);

  if (jobId === null) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-[#0b132b] border border-blue-900/60 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto shadow-2xl p-6 text-gray-200">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-blue-900/40 pb-4">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">⚖️</span>
            <h2 className="text-xl font-bold tracking-wide text-white">
              Escrow Case #{jobId} <span className="text-sm font-normal text-blue-400">Judicial Record</span>
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white px-3 py-1 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition"
          >
            ✕
          </button>
        </div>

        {loading ? (
          <div className="py-16 text-center text-blue-400 animate-pulse">
            Retrieving on-chain records & neural jury deliberations...
          </div>
        ) : !data || data.error ? (
          <div className="py-12 text-center text-rose-400">
            Failed to retrieve judicial records for Case #{jobId}.
          </div>
        ) : (
          <div className="mt-6 space-y-6">
            
            {/* Status & Payout Badge */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-black/30 p-3 rounded-xl border border-blue-950">
                <span className="text-xs text-gray-400 uppercase font-semibold">State</span>
                <p className="text-sm font-bold text-emerald-400 mt-1">{data.state}</p>
              </div>
              <div className="bg-black/30 p-3 rounded-xl border border-blue-950">
                <span className="text-xs text-gray-400 uppercase font-semibold">Worker Award</span>
                <p className="text-sm font-bold text-cyan-400 mt-1">{data.worker_bps} bps ({data.worker_bps / 100}%)</p>
              </div>
              <div className="bg-black/30 p-3 rounded-xl border border-blue-950">
                <span className="text-xs text-gray-400 uppercase font-semibold">Client Refund</span>
                <p className="text-sm font-bold text-amber-400 mt-1">{data.client_bps} bps ({data.client_bps / 100}%)</p>
              </div>
              <div className="bg-black/30 p-3 rounded-xl border border-blue-950">
                <span className="text-xs text-gray-400 uppercase font-semibold">Precedent Status</span>
                <p className="text-sm font-bold text-purple-400 mt-1">{data.precedent ? "ChromaDB Indexed" : "Pending"}</p>
              </div>
            </div>

            {/* Task Specification */}
            <div>
              <label className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                Task Specification
              </label>
              <div className="mt-1 bg-black/40 border border-blue-950 rounded-xl p-3 text-sm text-gray-300 font-mono">
                {data.raw_spec}
              </div>
            </div>

            {/* Submitted Deliverable Code */}
            <div>
              <label className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                Submitted Deliverable Implementation
              </label>
              <pre className="mt-1 bg-black/60 border border-blue-950 rounded-xl p-4 text-xs text-emerald-400 font-mono overflow-x-auto whitespace-pre-wrap max-h-48">
                {data.raw_deliverable}
              </pre>
            </div>

            {/* Juror Deliberation & Precedent Analysis */}
            {data.precedent && (
              <div>
                <label className="text-xs font-semibold text-purple-400 uppercase tracking-wider">
                  Neural Deliberation & Stare Decisis Precedents
                </label>
                <div className="mt-1 bg-purple-950/20 border border-purple-900/40 rounded-xl p-4 text-xs text-purple-200 font-mono whitespace-pre-wrap">
                  {data.precedent.document}
                </div>
              </div>
            )}

            {/* Hashes */}
            <div className="text-[11px] font-mono text-gray-500 space-y-1 bg-black/20 p-3 rounded-lg border border-white/5">
              <p className="truncate"><span className="text-gray-400 font-bold">Client:</span> {data.client}</p>
              <p className="truncate"><span className="text-gray-400 font-bold">Provider:</span> {data.provider}</p>
              <p className="truncate"><span className="text-gray-400 font-bold">Spec Hash:</span> {data.spec_hash}</p>
              <p className="truncate"><span className="text-gray-400 font-bold">Deliverable Hash:</span> {data.deliverable_hash}</p>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
