"use client";

import { useQuery } from "@tanstack/react-query";
import { getMe } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Video, CreditCard, Clock, Zap } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const router = useRouter();
  const { token, user, setAuth } = useAuthStore();

  const { data: userData } = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const res = await getMe();
      setAuth(token!, res.data);
      return res.data;
    },
    enabled: !!token,
  });

  useEffect(() => {
    if (!token) router.push("/auth/login");
  }, [token, router]);

  if (!user) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Welcome back, {user.full_name || user.email}
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl border shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <CreditCard className="w-5 h-5 text-blue-600" />
            <span className="text-sm text-gray-500">Credits</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{user.credits}</p>
          <Link href="/credits" className="text-sm text-blue-600 hover:underline mt-2 inline-block">
            Buy more credits
          </Link>
        </div>

        <div className="bg-white p-6 rounded-xl border shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Video className="w-5 h-5 text-green-600" />
            <span className="text-sm text-gray-500">Videos Generated</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">-</p>
          <Link href="/videos" className="text-sm text-blue-600 hover:underline mt-2 inline-block">
            View library
          </Link>
        </div>

        <div className="bg-white p-6 rounded-xl border shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Zap className="w-5 h-5 text-yellow-600" />
            <span className="text-sm text-gray-500">Quick Generate</span>
          </div>
          <Link
            href="/generate"
            className="inline-block mt-2 bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
          >
            Create Video
          </Link>
        </div>
      </div>

      <div className="bg-white rounded-xl border shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Pricing</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { duration: "5 seconds", credits: 10, price: "$0.10" },
            { duration: "10 seconds", credits: 20, price: "$0.20" },
            { duration: "15 seconds", credits: 30, price: "$0.30" },
          ].map((plan) => (
            <div key={plan.duration} className="border rounded-lg p-4 text-center">
              <p className="font-semibold text-gray-900">{plan.duration}</p>
              <p className="text-2xl font-bold text-blue-600 my-2">{plan.credits} credits</p>
              <p className="text-sm text-gray-500">{plan.price}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
