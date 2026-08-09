import React, { useState, useEffect } from "react";
import api from "../services/api";
import { 
  FileText, 
  UploadCloud, 
  ShieldCheck, 
  Clock, 
  Eye, 
  Lock, 
  AlertCircle, 
  Loader2
} from "lucide-react";

export const PapersPage: React.FC = () => {
  const [, setPapersInfo] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get("/papers")
      .then((res) => {
        if (res.data && res.data.success) {
          setPapersInfo(res.data.data);
        }
      })
      .catch((err) => console.error("Error fetching papers contract:", err))
      .finally(() => setIsLoading(false));
  }, []);

  const mockedPapers = [
    {
      id: "9e7d956a-12cf-4b11-9bc9-a78b4a5fe12a",
      subject: "Mathematics - Paper I (NEET Level)",
      code: "NEET-2026-M1",
      status: "encrypted",
      creator: "Prof. S. R. Srinivasan",
      approvals: 2,
      requiredApprovals: 3,
      modified: "2 hours ago",
    },
    {
      id: "a39b283d-e382-4f1b-ba77-e89c09d3b118",
      subject: "Physics - Paper II (JEE Advanced)",
      code: "JEE-2026-P2",
      status: "draft",
      creator: "Dr. Ananya Mukherjee",
      approvals: 1,
      requiredApprovals: 3,
      modified: "Yesterday",
    },
    {
      id: "4c1e892d-932f-48d8-99ee-2b02a983b129",
      subject: "General Studies - Paper I (UPSC)",
      code: "UPSC-2026-GS1",
      status: "released",
      creator: "Dr. K. Raghavan",
      approvals: 3,
      requiredApprovals: 3,
      modified: "3 days ago",
    },
  ];

  if (isLoading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-white animate-spin" />
        <span className="text-xs text-slate-400">Loading secure registry...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-xl font-bold tracking-tight text-white font-sans">Examination Papers</h1>
          <p className="text-xs text-slate-400">Manage high-security examination question papers and releases.</p>
        </div>

        <button className="flex items-center gap-2 bg-white/5 hover:bg-white/10 text-white border border-white/10 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-not-allowed">
          <UploadCloud className="w-4 h-4" />
          Upload Secure Paper (Staged)
        </button>
      </div>

      {/* Security Architecture Reminder Alert */}
      <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs">
        <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold block text-white">Hybrid Cryptography Envelope Design Staged</span>
          <span className="block leading-relaxed">
            In the upcoming release, all paper uploads will utilize client-side hybrid encryption: 
            each file is encrypted with a unique symmetric AES-256 key, which is subsequently wrapped with 
            RSA/ECC public keys of the authorized examiners. Real-time watermarks matching the viewer's ID 
            and endpoint details will be embedded upon decryption request.
          </span>
        </div>
      </div>

      {/* Active Papers Table */}
      <div className="glass-panel rounded-2xl overflow-hidden shadow-xl border border-white/5">
        <div className="px-6 py-4 border-b border-white/5 bg-white/[0.01]">
          <h3 className="text-xs font-bold text-white uppercase tracking-widest">Active Safe Repository</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 bg-white/[0.01] text-xs font-bold text-slate-400 uppercase tracking-widest">
                <th className="p-4 pl-6">Paper Code / Subject</th>
                <th className="p-4">Cryptographic Status</th>
                <th className="p-4">Owner / Author</th>
                <th className="p-4">Workflow Approvals</th>
                <th className="p-4 pr-6 text-right">Control Node</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm text-slate-200">
              {mockedPapers.map((paper) => (
                <tr key={paper.id} className="hover:bg-white/[0.01] transition-colors">
                  <td className="p-4 pl-6">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-slate-400">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div>
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">{paper.code}</span>
                        <span className="text-xs font-semibold text-slate-200">{paper.subject}</span>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
                        paper.status === "released"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/15"
                          : paper.status === "encrypted"
                          ? "bg-blue-500/10 text-blue-400 border border-blue-500/15"
                          : "bg-slate-500/10 text-slate-400 border border-slate-500/15"
                      }`}
                    >
                      {paper.status === "released" && <ShieldCheck className="w-3 h-3" />}
                      {paper.status === "encrypted" && <Lock className="w-3 h-3" />}
                      {paper.status === "draft" && <Clock className="w-3 h-3" />}
                      {paper.status}
                    </span>
                  </td>
                  <td className="p-4 text-xs text-slate-400 font-medium">{paper.creator}</td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-slate-900 h-1.5 rounded-full overflow-hidden border border-white/5">
                        <div 
                          className="bg-indigo-500 h-full"
                          style={{ width: `${(paper.approvals / paper.requiredApprovals) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-[10px] text-slate-400 font-bold">
                        {paper.approvals}/{paper.requiredApprovals}
                      </span>
                    </div>
                  </td>
                  <td className="p-4 pr-6 text-right">
                    <button className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-bold bg-white/5 border border-white/10 hover:bg-white/10 text-white transition-colors cursor-not-allowed">
                      <Eye className="w-3.5 h-3.5" /> View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default PapersPage;
