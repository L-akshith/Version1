import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { useAuth } from "../hooks/useAuth";
import { AlertCircle, Lock, Mail, User as UserIcon, CheckCircle2 } from "lucide-react";

const registerSchema = zod.object({
  fullName: zod.string().min(2, "Full name must be at least 2 characters"),
  email: zod.string().email("Enter a valid official email address"),
  password: zod
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[0-9]/, "Password must contain at least one number")
    .regex(/[^a-zA-Z0-9]/, "Password must contain at least one special character"),
});

type RegisterFormValues = zod.infer<typeof registerSchema>;

export const RegisterPage: React.FC = () => {
  const { register: registerAuth } = useAuth();
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (values: RegisterFormValues) => {
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      await registerAuth(values.email, values.password, values.fullName);
      setIsSuccess(true);
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    } catch (err: any) {
      setErrorMessage(
        err.response?.data?.message || err.message || "Registration failed. Try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="space-y-4 text-center animate-fade-in py-4">
        <div className="flex justify-center text-emerald-500 mb-2">
          <CheckCircle2 className="w-12 h-12" />
        </div>
        <h2 className="text-xl font-bold text-white tracking-tight">Access Requested</h2>
        <p className="text-sm text-slate-400 leading-relaxed">
          Your account request has been registered. Redirecting to login portal...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-white tracking-tight">Request Access</h2>
        <p className="text-xs text-slate-400">Submit details for official account authorization.</p>
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Full Name Field */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Full Name</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <UserIcon className="w-4 h-4" />
            </div>
            <input
              type="text"
              placeholder="Dr. Rajesh Kumar"
              className={`w-full bg-black/40 border ${
                errors.fullName ? "border-rose-500/50 focus:border-rose-500" : "border-white/10 focus:border-white/30"
              } rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none transition-all`}
              {...register("fullName")}
            />
          </div>
          {errors.fullName && (
            <p className="text-[10px] text-rose-400 font-semibold">{errors.fullName.message}</p>
          )}
        </div>

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
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Secure Keyphrase</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type="password"
              placeholder="Min. 8 chars, 1 uppercase, 1 special, 1 number"
              className={`w-full bg-black/40 border ${
                errors.password ? "border-rose-500/50 focus:border-rose-500" : "border-white/10 focus:border-white/30"
              } rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none transition-all`}
              {...register("password")}
            />
          </div>
          {errors.password && (
            <p className="text-[10px] text-rose-400 font-semibold leading-normal">{errors.password.message}</p>
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
            "Request Authorization"
          )}
        </button>
      </form>

      <div className="border-t border-white/5 pt-4 text-center">
        <p className="text-xs text-slate-400">
          Already have credentials?{" "}
          <Link to="/login" className="text-white hover:underline font-semibold">
            Authenticate
          </Link>
        </p>
      </div>
    </div>
  );
};
export default RegisterPage;
