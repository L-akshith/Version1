import React from "react";
import { NavLink, Outlet, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { 
  Shield, 
  LayoutDashboard, 
  Users, 
  KeyRound, 
  FileText, 
  History, 
  LogOut,
  Menu,
  ClipboardList,
  BookOpen
} from "lucide-react";

export const MainLayout: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="relative flex flex-col items-center">
          <div className="w-12 h-12 rounded-full border-4 border-slate-800 border-t-white animate-spin"></div>
          <p className="mt-4 text-sm text-slate-400 font-medium tracking-wide">Initializing Safe Environment...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Helper to check user permissions
  const hasPermission = (permission: string) => {
    if (user.is_superuser) return true;
    // Default roles mapping
    if (permission === "users:manage" || permission === "roles:manage") {
      return user.role_name === "Admin";
    }
    if (permission === "audit:list") {
      return ["Admin", "Controller", "Observer", "Investigator"].includes(user.role_name || "");
    }
    if (permission === "exams:read") {
      return ["Admin", "Controller", "Observer", "Investigator"].includes(user.role_name || "");
    }
    if (permission === "subjects:read") {
      return ["Admin", "Controller", "Observer", "Question Setter"].includes(user.role_name || "");
    }
    if (permission === "workflow:view") {
      return ["Admin", "Controller"].includes(user.role_name || "");
    }
    return true;
  };

  const navItems = [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/exams", label: "Exams", icon: ClipboardList, permission: "exams:read" },
    { to: "/subjects", label: "Subjects", icon: BookOpen, permission: "subjects:read" },
    { to: "/question-papers", label: "Question Papers", icon: FileText, permission: "questionpapers:read" },
    { to: "/approvals", label: "Approvals", icon: CheckBadge, permission: "workflow:view" },
    { to: "/users", label: "User Management", icon: Users, permission: "users:manage" },
    { to: "/roles", label: "Roles & Permissions", icon: KeyRound, permission: "roles:manage" },
    { to: "/audit", label: "Audit Logs", icon: History, permission: "audit:list" },
  ];

  return (
    <div className="min-h-screen bg-slate-950 flex text-slate-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 bg-slate-950/80 backdrop-blur-xl flex flex-col justify-between p-4 hidden md:flex">
        <div className="space-y-6">
          <div className="flex items-center gap-3 px-2 py-3">
            <div className="w-8 h-8 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
              <Shield className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <span className="font-bold text-sm text-white tracking-wide block">ExamShield</span>
              <span className="text-[10px] text-slate-400 block -mt-0.5">Control Center</span>
            </div>
          </div>

          <nav className="space-y-1">
            {navItems.map((item) => {
              if (item.permission && !hasPermission(item.permission)) return null;
              
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? "bg-white/10 text-white shadow-lg"
                        : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                    }`
                  }
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* User profile section in sidebar */}
        <div className="border-t border-white/5 pt-4 space-y-3">
          <div className="flex items-center gap-3 px-2 py-1">
            <div className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-200 font-semibold text-sm">
              {user.full_name.charAt(0)}
            </div>
            <div className="truncate max-w-[140px]">
              <span className="text-xs font-semibold block text-slate-200 truncate">{user.full_name}</span>
              <span className="inline-block px-1.5 py-0.5 mt-0.5 text-[8.5px] font-bold uppercase rounded-md bg-white/10 text-slate-300 border border-white/5">
                {user.role_name || "Observer"}
              </span>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Top Header */}
        <header className="h-16 border-b border-white/5 bg-slate-950/40 backdrop-blur-md flex items-center justify-between px-6">
          <div className="flex items-center gap-3 md:hidden">
            <button className="p-2 -ml-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white">
              <Menu className="w-5 h-5" />
            </button>
            <span className="font-bold text-sm tracking-wide text-white">ExamShield</span>
          </div>

          <div className="hidden md:block">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Platform Core</h2>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="text-xs font-semibold text-slate-300">Secure Node</span>
            </div>
          </div>
        </header>

        {/* Content Outlet */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
export default MainLayout;
