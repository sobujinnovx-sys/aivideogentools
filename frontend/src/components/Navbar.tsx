"use client";

import Link from "next/link";
import { useAuthStore } from "@/lib/store";
import { useQuery } from "@tanstack/react-query";
import { getMe } from "@/lib/api";
import { Video, CreditCard, LogOut, LayoutDashboard, Sparkles } from "lucide-react";

export function Navbar() {
  const { token, user, setAuth, logout } = useAuthStore();

  useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const res = await getMe();
      setAuth(token!, res.data);
      return res.data;
    },
    enabled: !!token && !user,
    retry: false,
  });

  return (
    <nav className="bg-white border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-gray-900">
            <Sparkles className="w-6 h-6 text-blue-600" />
            AIVideo
          </Link>

          <div className="flex items-center gap-6">
            {user ? (
              <>
                <Link href="/dashboard" className="flex items-center gap-1 text-gray-600 hover:text-gray-900">
                  <LayoutDashboard className="w-4 h-4" />
                  Dashboard
                </Link>
                <Link href="/generate" className="flex items-center gap-1 text-gray-600 hover:text-gray-900">
                  <Video className="w-4 h-4" />
                  Generate
                </Link>
                <Link href="/videos" className="flex items-center gap-1 text-gray-600 hover:text-gray-900">
                  <Video className="w-4 h-4" />
                  Library
                </Link>
                <Link href="/credits" className="flex items-center gap-1 text-gray-600 hover:text-gray-900">
                  <CreditCard className="w-4 h-4" />
                  <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-sm font-medium">
                    {user.credits} credits
                  </span>
                </Link>
                <span className="text-sm text-gray-500">{user.email}</span>
                <button onClick={logout} className="text-gray-400 hover:text-red-500">
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                <Link href="/auth/login" className="text-gray-600 hover:text-gray-900">
                  Login
                </Link>
                <Link
                  href="/auth/register"
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
