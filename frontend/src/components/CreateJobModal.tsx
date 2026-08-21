'use client';

import { useState } from 'react';
import { useAccount, useWriteContract } from 'wagmi';
import { parseEther, keccak256, toHex, getAddress } from 'viem';
import { PlusCircle, Loader2, X } from 'lucide-react';
import contractData from '@/AgentEscrowV4.json';

const CONTRACT_ADDRESS = '0x00A0197635788C997AE443C0281E86FB495CD08b' as `0x${string}`;

export function CreateJobModal({ onJobCreated }: { onJobCreated: () => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [spec, setSpec] = useState('');
  const [criteria, setCriteria] = useState('');
  const [provider, setProvider] = useState('');
  const [amountEth, setAmountEth] = useState('0.0001');
  const [loading, setLoading] = useState(false);

  const { address } = useAccount();
  const { writeContractAsync } = useWriteContract();

  const handleCreateAndFund = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!address) return alert('Please connect wallet first.');

    try {
      setLoading(true);

      const payload = {
        task_title: title,
        task_specification: spec,
        criteria: criteria,
        deliverable_content: 'Pending provider submission.'
      };

      // 1. Pin metadata via FastAPI backend
      const res = await fetch('http://127.0.0.1:8000/pin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload }),
      });
      const data = await res.json();
      const metadataHash = (data.content_hash || keccak256(toHex(JSON.stringify(payload)))) as `0x${string}`;

      const targetProvider = provider ? getAddress(provider) : address;
      const escrowWei = parseEther(amountEth);

      // 2. Call non-payable createJob (value: 0)
      const createTx = await writeContractAsync({
        address: CONTRACT_ADDRESS,
        abi: contractData.abi || contractData,
        functionName: 'createJob',
        args: [targetProvider, address, escrowWei, metadataHash],
        gas: 350000n,
      });

      console.log('CreateJob Tx Hash:', createTx);
      alert('Job created on-chain! Oracle deliberation initiated.');
      setIsOpen(false);
      onJobCreated();
    } catch (err: any) {
      console.error(err);
      alert(`Transaction failed: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition shadow-lg shadow-blue-500/20"
      >
        <PlusCircle className="w-4 h-4" />
        New Dispute Escrow
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm p-4 flex items-center justify-center min-h-screen">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl relative my-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">Create Autonomous Escrow</h3>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateAndFund} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Task Title</label>
                <input
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Smart Contract Security Audit"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Specification</label>
                <textarea
                  required
                  rows={2}
                  value={spec}
                  onChange={(e) => setSpec(e.target.value)}
                  placeholder="Detailed requirements for the provider..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Evaluation Criteria</label>
                <input
                  required
                  value={criteria}
                  onChange={(e) => setCriteria(e.target.value)}
                  placeholder="e.g. Award 10000 bps if zero critical bugs found"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Provider Address</label>
                  <input
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    placeholder="Defaults to connected wallet"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white placeholder:text-slate-600 font-mono text-[11px] focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Escrow Amount (ETH)</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={amountEth}
                    onChange={(e) => setAmountEth(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-3 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold flex items-center justify-center gap-2 transition disabled:opacity-50 shadow-lg shadow-blue-600/30"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Escrow on Base Sepolia'}
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
