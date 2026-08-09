import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { useAuth } from "../hooks/useAuth";
import { AlertCircle, Lock, Mail, Eye, EyeOff } from "lucide-react";

const loginSchema = zod.object({
  email: zod.string().email("Enter a valid official email address"),
  password: zod.string().min(8, "Password must be at least 8 characters"),
});

type LoginFormValues = zod.infer<typeof loginSchema>;

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isExpired = searchParams.get("expired") === "true";

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (values: LoginFormValues) => {
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      await login(values.email, values.password);
      navigate("/dashboard");
    } catch (err: any) {
      setErrorMessage(
        err.response?.data?.message || err.message || "Invalid credentials. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-white tracking-tight">Security Gateway</h2>
        <p className="text-xs text-slate-400">Authenticate to enter the command node.</p>
      </div>

      {isExpired && (
        <div className="flex items-center gap-2 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-semibold">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Your session has expired. Please sign in again.</span>
        </div>
      )}

      {errorMessage && (
        <div className="flex items-center gap-2 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Email Field */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Official Email</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Mail className="w-4 h-4" />
            </div>
            <input
              type="email"
              placeholder="name@examshield.gov.in"
              className={`w-full bg-black/40 border ${
                errors.email ? "border-rose-500/50 focus:border-rose-500" : "border-white/10 focus:border-white/30"
              } rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none transition-all`}
              {...register("email")}
            />
          </div>
          {errors.email && (
            <p className="text-[10px] text-rose-400 font-semibold">{errors.email.message}</p>
          )}
        </div>

        {/* Password Field */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center">
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Secure Keyphrase</label>
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type={showPassword ? "text" : "password"}
              placeholder="••••••••••••"
              className={`w-full bg-black/40 border ${
                errors.password ? "border-rose-500/50 focus:border-rose-500" : "border-white/10 focus:border-white/30"
              } rounded-xl py-2.5 pl-10 pr-10 text-sm text-white placeholder-slate-500 focus:outline-none transition-all`}
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {errors.password && (
            <p className="text-[10px] text-rose-400 font-semibold">{errors.password.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-white hover:bg-slate-100 disabled:bg-slate-400 text-slate-950 font-bold py-2.5 rounded-xl text-sm transition-all duration-200 shadow-lg shadow-black/20 flex items-center justify-center"
        >
          {isSubmitting ? (
            <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin"></div>
          ) : (
            "Authenticate Node"
          )}
        </button>
      </form>

      <div className="border-t border-white/5 pt-4 text-center">
        <p className="text-xs text-slate-400">
          New terminal officer?{" "}
          <Link to="/register" className="text-white hover:underline font-semibold">
            Request credentials
          </Link>
        </p>
      </div>
    </div>
  );
};
export default LoginPage;
