import React from "react";
import { Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Shield } from "lucide-react";

export const AuthLayout: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="relative flex flex-col items-center">
          <div className="w-12 h-12 rounded-full border-4 border-slate-800 border-t-white animate-spin"></div>
          <p className="mt-4 text-sm text-slate-400 font-medium tracking-wide">Validating Credentials...</p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 flex items-center justify-center p-4 relative overflow-hidden select-none">
      {/* Decorative blurred background shapes */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] rounded-full bg-blue-500/10 blur-[80px]"></div>
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-[400px] h-[400px] rounded-full bg-indigo-500/10 blur-[90px]"></div>

      <div className="w-full max-w-[440px] z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-3 shadow-lg shadow-black/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">ExamShield</h1>
          <p className="text-sm text-slate-400 mt-1">Secure Exam Paper Management</p>
        </div>

        <div className="glass-card rounded-2xl p-8 shadow-2xl shadow-black/40 animate-fade-in">
          <Outlet />
        </div>
      </div>
    </div>
  );
};
export default AuthLayout;
