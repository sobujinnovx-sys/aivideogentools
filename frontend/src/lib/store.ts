import { create } from "zustand";

interface User {
  id: string;
  email: string;
  full_name: string;
  credits: number;
}

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
  updateCredits: (credits: number) => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,

  setAuth: (token, user) => {
    localStorage.setItem("token", token);
    set({ token, user });
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ token: null, user: null });
  },

  updateCredits: (credits) =>
    set((state) => ({
      user: state.user ? { ...state.user, credits } : null,
    })),

  loadFromStorage: () => {
    const token = localStorage.getItem("token");
    if (token) {
      set({ token });
    }
  },
}));
