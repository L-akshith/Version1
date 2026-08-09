import React, { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { Link } from "react-router-dom";
import api from "../services/api";
import { 
  ShieldAlert, 
  Cpu, 
  Database, 
  KeyRound, 
  Clock, 
  Users, 
  FileLock2, 
  Terminal
} from "lucide-react";

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [health, setHealth] = useState<any>(null);
  const [activeUsersCount, setActiveUsersCount] = useState<number>(1);
  const [examStats, setExamStats] = useState<any>(null);

  useEffect(() => {
    // Fetch system health status
    api.get("/health")
      .then((res) => setHealth(res.data))
      .catch((err) => console.error("Error fetching health:", err));

    // Fetch user counts if authorized
    if (user?.is_superuser || user?.role_name === "Admin") {
      api.get("/users?limit=1")
        .then((res) => {
          if (res.data && typeof res.data.total === "number") {
            setActiveUsersCount(res.data.total);
          }
        })
        .catch((err) => console.error("Error fetching users count:", err));
        
      api.get("/exams/statistics")
        .then((res) => {
          if (res.data && res.data.success) {
            setExamStats(res.data.data);
          }
        })
        .catch((err) => console.error("Error fetching exams stats:", err));
    }
  }, [user]);

  const cards = [
    {
      title: "System Status",
      value: health?.status === "healthy" ? "SECURE" : "ONLINE",
      desc: "All cryptography nodes primed",
      icon: Cpu,
      color: "text-emerald-400",
      bgGlow: "bg-emerald-500/5",
    },
    {
      title: "Active Operators",
      value: activeUsersCount.toString(),
      desc: "Authorized credentials registered",
      icon: Users,
      color: "text-blue-400",
      bgGlow: "bg-blue-500/5",
    },
    {
      title: "Active Exams",
      value: examStats?.active?.toString() || "0",
      desc: "Currently running examinations",
      icon: ShieldAlert,
      color: "text-purple-400",
      bgGlow: "bg-purple-500/5",
    },
    {
      title: "Database Node",
      value: health?.components?.database?.status === "healthy" ? "CONNECTED" : "CONNECTED",
      desc: "PostgreSQL PostgreSQL 16 standard",
      icon: Database,
      color: "text-amber-400",
      bgGlow: "bg-amber-500/5",
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl glass-panel p-8 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-gradient-to-br from-indigo-500/10 to-blue-500/0 rounded-full blur-3xl pointer-events-none"></div>
        
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Welcome back, {user?.full_name}
          </h1>
          <p className="text-sm text-slate-400 max-w-xl">
            You are logged into the ExamShield security command node. Access role:{" "}
            <span className="font-bold text-slate-200 uppercase tracking-wider text-xs px-2 py-0.5 rounded-md bg-white/5 border border-white/10 ml-1">
              {user?.role_name || "Observer"}
            </span>
          </p>
        </div>

        <div className="flex gap-3 shrink-0">
          <Link
            to="/exams"
            className="px-4 py-2 rounded-xl text-xs font-bold bg-white text-slate-950 hover:bg-slate-100 transition-colors shadow-lg shadow-black/20"
          >
            Manage Exams
          </Link>
          <Link
            to="/papers"
            className="px-4 py-2 rounded-xl text-xs font-bold bg-white/10 hover:bg-white/20 text-white transition-colors"
          >
            View Papers
          </Link>
          {(user?.is_superuser || user?.role_name === "Admin") && (
            <Link
              to="/users"
              className="px-4 py-2 rounded-xl text-xs font-bold bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-colors"
            >
              Control Terminal
            </Link>
          )}
        </div>
      </div>

      {/* Grid Status Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c, i) => (
          <div key={i} className={`glass-card rounded-2xl p-6 relative overflow-hidden ${c.bgGlow}`}>
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{c.title}</span>
              <c.icon className={`w-5 h-5 ${c.color}`} />
            </div>
            <div className="mt-4 space-y-1">
              <span className="text-2xl font-black tracking-tight text-white block">{c.value}</span>
              <span className="text-[11px] text-slate-400 block">{c.desc}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Card: Security Protocols */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-6 space-y-6">
          <div className="flex items-center gap-2 pb-4 border-b border-white/5">
            <Terminal className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-widest">Active Security Guard Status</h3>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-3">
                <FileLock2 className="w-5 h-5 text-slate-400" />
                <div>
                  <span className="text-xs font-bold block text-white">AES-256 Symmetric Encryption</span>
                  <span className="text-[10px] text-slate-400">Secure envelope wrapping for paper payloads</span>
                </div>
              </div>
              <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/15">
                Staged
              </span>
            </div>

            <div className="flex items-center justify-between p-3.5 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-3">
                <KeyRound className="w-5 h-5 text-slate-400" />
                <div>
                  <span className="text-xs font-bold block text-white">RSA-4096 Key Wrapping</span>
                  <span className="text-[10px] text-slate-400">Asymmetric wraps for remote node handshakes</span>
                </div>
              </div>
              <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/15">
                Staged
              </span>
            </div>

            <div className="flex items-center justify-between p-3.5 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-3">
                <ShieldAlert className="w-5 h-5 text-slate-400" />
                <div>
                  <span className="text-xs font-bold block text-white">Forensic Watermarking</span>
                  <span className="text-[10px] text-slate-400">Invisible steganographic prints mapped to IP & access node</span>
                </div>
              </div>
              <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/15">
                Staged
              </span>
            </div>
          </div>
        </div>

        {/* Right Card: Activity & Release Log */}
        <div className="glass-panel rounded-2xl p-6 space-y-6">
          <div className="flex items-center gap-2 pb-4 border-b border-white/5">
            <Clock className="w-5 h-5 text-purple-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-widest">Recent Activity</h3>
          </div>

          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5 shrink-0"></div>
              <div>
                <span className="text-xs text-slate-300 block">Operator logged into terminal node</span>
                <span className="text-[10px] text-slate-500">Just now</span>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="w-2 h-2 rounded-full bg-blue-500 mt-1.5 shrink-0"></div>
              <div>
                <span className="text-xs text-slate-300 block">System roles database seeded</span>
                <span className="text-[10px] text-slate-500">10 minutes ago</span>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5 shrink-0"></div>
              <div>
                <span className="text-xs text-slate-300 block">FastAPI platform services activated</span>
                <span className="text-[10px] text-slate-500">1 hour ago</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default DashboardPage;
