import React, { createContext, useState, useEffect, useCallback } from "react";
import { authService } from "../services/auth";
import type { User } from "../types";

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    setUser(null);
    setIsLoading(false);
  }, []);

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      logout();
      return;
    }

    try {
      const res = await authService.getMe();
      if (res.success && res.data) {
        setUser(res.data);
        localStorage.setItem("user", JSON.stringify(res.data));
      } else {
        logout();
      }
    } catch (err) {
      console.error("Auth verification failed:", err);
      logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    // Initial load check
    const token = localStorage.getItem("access_token");
    const storedUser = localStorage.getItem("user");
    
    if (token) {
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
          setIsLoading(false);
          // Async background verification refresh
          refreshUser();
        } catch {
          refreshUser();
        }
      } else {
        refreshUser();
      }
    } else {
      setIsLoading(false);
    }
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await authService.login({ email, password });
      if (res.success && res.data) {
        localStorage.setItem("access_token", res.data.access_token);
        localStorage.setItem("refresh_token", res.data.refresh_token);
        
        // Fetch full profile info
        const profileRes = await authService.getMe();
        if (profileRes.success && profileRes.data) {
          setUser(profileRes.data);
          localStorage.setItem("user", JSON.stringify(profileRes.data));
        } else {
          throw new Error("Could not fetch user profile after successful login");
        }
      } else {
        throw new Error(res.message || "Login failed");
      }
    } catch (err) {
      logout();
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string) => {
    setIsLoading(true);
    try {
      const res = await authService.register({ email, password, full_name: fullName });
      if (!res.success) {
        throw new Error(res.message || "Registration failed");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
export default AuthContext;
