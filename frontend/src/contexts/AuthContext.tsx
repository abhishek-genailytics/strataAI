import React, { createContext, useContext, useEffect, useState } from "react";
import {
  createClient,
  SupabaseClient,
  User as SupabaseUser,
} from "@supabase/supabase-js";
import { AuthState, Organization, UserOrganization, User } from "../types";
import { apiService } from "../services/api";

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || "";
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || "";

const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey);

interface AuthContextType extends AuthState {
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string) => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error?: string }>;
  updateProfile: (updates: {
    email?: string;
    displayName?: string;
  }) => Promise<{ error?: string }>;
  updatePassword: (newPassword: string) => Promise<{ error?: string }>;
  refreshUser: () => Promise<void>;
  // Organization management
  setCurrentOrganization: (organization: Organization | null) => void;
  refreshOrganizations: () => Promise<void>;
  supabase: SupabaseClient;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<UserOrganization[]>([]);
  const [currentOrganization, setCurrentOrganization] =
    useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Convert Supabase user to our User type
  const convertSupabaseUser = (
    supabaseUser: SupabaseUser | null
  ): User | null => {
    if (!supabaseUser) return null;
    return {
      id: supabaseUser.id,
      email: supabaseUser.email || "",
      created_at: supabaseUser.created_at,
      updated_at: supabaseUser.updated_at || supabaseUser.created_at,
    };
  };

  useEffect(() => {
    // Get initial session
    const getInitialSession = async () => {
      try {
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession();
        if (error) {
          console.error("Error getting session:", error);
          setError(error.message);
        } else {
          setUser(convertSupabaseUser(session?.user ?? null));
        }
      } catch (err) {
        console.error("Error in getInitialSession:", err);
        setError("Failed to initialize authentication");
      } finally {
        setLoading(false);
      }
    };

    getInitialSession();

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      setUser(convertSupabaseUser(session?.user ?? null));
      setLoading(false);
      setError(null);

      if (event === "SIGNED_OUT") {
        // Clear any cached data
        localStorage.removeItem("strataai-cache");
        localStorage.removeItem("strataai-current-org");
        setOrganizations([]);
        setCurrentOrganization(null);
      } else if (event === "SIGNED_IN" && session?.user) {
        // Load user organizations after sign in
        loadUserOrganizations();
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);

      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        setError(error.message);
        return { error: error.message };
      }

      return {};
    } catch (err) {
      const errorMessage = "An unexpected error occurred during sign in";
      setError(errorMessage);
      return { error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);

      const { error } = await supabase.auth.signUp({
        email,
        password,
      });

      if (error) {
        setError(error.message);
        return { error: error.message };
      }

      return {};
    } catch (err) {
      const errorMessage = "An unexpected error occurred during sign up";
      setError(errorMessage);
      return { error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    try {
      setLoading(true);
      setError(null);

      const { error } = await supabase.auth.signOut();

      if (error) {
        setError(error.message);
        console.error("Error signing out:", error);
      }
    } catch (err) {
      setError("An unexpected error occurred during sign out");
      console.error("Error in signOut:", err);
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (email: string) => {
    try {
      setError(null);

      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });

      if (error) {
        setError(error.message);
        return { error: error.message };
      }

      return {};
    } catch (err) {
      const errorMessage = "An unexpected error occurred during password reset";
      setError(errorMessage);
      return { error: errorMessage };
    }
  };

  const updateProfile = async (updates: {
    email?: string;
    displayName?: string;
  }) => {
    try {
      setError(null);

      const updateData: any = {};

      if (updates.email) {
        updateData.email = updates.email;
      }

      if (updates.displayName) {
        updateData.data = {
          display_name: updates.displayName,
          full_name: updates.displayName,
        };
      }

      const { error } = await supabase.auth.updateUser(updateData);

      if (error) {
        setError(error.message);
        return { error: error.message };
      }

      return {};
    } catch (err) {
      const errorMessage = "An unexpected error occurred during profile update";
      setError(errorMessage);
      return { error: errorMessage };
    }
  };

  const updatePassword = async (newPassword: string) => {
    try {
      setError(null);

      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });

      if (error) {
        setError(error.message);
        return { error: error.message };
      }

      return {};
    } catch (err) {
      const errorMessage =
        "An unexpected error occurred during password update";
      setError(errorMessage);
      return { error: errorMessage };
    }
  };

  const refreshUser = async () => {
    try {
      const {
        data: { user },
        error,
      } = await supabase.auth.getUser();
      if (error) {
        console.error("Error refreshing user:", error);
        setError(error.message);
      } else {
        setUser(convertSupabaseUser(user));
        if (user) {
          await loadUserOrganizations();
        }
      }
    } catch (err) {
      console.error("Error in refreshUser:", err);
      setError("Failed to refresh user data");
    }
  };

  // Load user organizations from backend
  const loadUserOrganizations = async () => {
    try {
      const response = await apiService.getUserOrganizations();
      if (response.data) {
        setOrganizations(response.data);

        // Restore current organization from localStorage or set first one
        const savedOrgId = localStorage.getItem("strataai-current-org");
        if (savedOrgId) {
          const savedOrg = response.data.find(
            (uo: UserOrganization) => uo.organization.id === savedOrgId
          );
          if (savedOrg) {
            setCurrentOrganization(savedOrg.organization);
          } else if (response.data.length > 0) {
            setCurrentOrganization(response.data[0].organization);
          }
        } else if (response.data.length > 0) {
          setCurrentOrganization(response.data[0].organization);
        }
      }
    } catch (err) {
      console.error("Error loading organizations:", err);
      // Don't set error for organizations as it's not critical for basic auth
    }
  };

  // Organization management
  const handleSetCurrentOrganization = (organization: Organization | null) => {
    setCurrentOrganization(organization);
    if (organization) {
      localStorage.setItem("strataai-current-org", organization.id);
    } else {
      localStorage.removeItem("strataai-current-org");
    }
  };

  const refreshOrganizations = async () => {
    await loadUserOrganizations();
  };

  const value: AuthContextType = {
    user,
    organizations,
    currentOrganization,
    loading,
    error,
    signIn,
    signUp,
    signOut,
    resetPassword,
    updateProfile,
    updatePassword,
    refreshUser,
    setCurrentOrganization: handleSetCurrentOrganization,
    refreshOrganizations,
    supabase,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
