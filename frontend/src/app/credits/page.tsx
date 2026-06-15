"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCreditBalance, getCreditHistory, claimBonus } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { CreditCard, Plus, ArrowUpRight, ArrowDownLeft, Gift } from "lucide-react";

export default function CreditsPage() {
  const router = useRouter();
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const updateCredits = useAuthStore((s) => s.updateCredits);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!token) router.push("/auth/login");
  }, [token, router]);

  const { data: balance } = useQuery({
    queryKey: ["credits"],
    queryFn: async () => {
      const res = await getCreditBalance();
      updateCredits(res.data.credits);
      return res.data;
    },
    enabled: !!token,
  });

  const { data: history } = useQuery({
    queryKey: ["credit-history"],
    queryFn: async () => {
      const res = await getCreditHistory();
      return res.data;
    },
    enabled: !!token,
  });

  const bonusMutation = useMutation({
    mutationFn: claimBonus,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["credits"] });
      queryClient.invalidateQueries({ queryKey: ["credit-history"] });
    },
  });

  if (!token) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Credits</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white p-8 rounded-xl border shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <CreditCard className="w-6 h-6 text-blue-600" />
            <span className="text-gray-500">Current Balance</span>
          </div>
          <p className="text-5xl font-bold text-gray-900">{user?.credits || 0}</p>
          <p className="text-sm text-gray-400 mt-2">credits available</p>
        </div>

        <div className="bg-white p-8 rounded-xl border shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-4">Credit Packages</h3>
          <div className="space-y-3">
            {[
              { credits: 100, price: "$1.00" },
              { credits: 500, price: "$4.50" },
              { credits: 1000, price: "$8.00" },
            ].map((pkg) => (
              <button
                key={pkg.credits}
                className="w-full flex justify-between items-center p-3 border rounded-lg hover:border-blue-400 hover:bg-blue-50 transition"
              >
                <span className="font-medium">{pkg.credits} credits</span>
                <span className="text-gray-500">{pkg.price}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Welcome Bonus</h2>
          <button
            onClick={() => bonusMutation.mutate()}
            disabled={bonusMutation.isPending}
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
          >
            <Gift className="w-4 h-4" />
            {bonusMutation.isPending ? "Claiming..." : "Claim 50 Free Credits"}
          </button>
        </div>
        {bonusMutation.isError && (
          <p className="text-sm text-red-500">
            {(bonusMutation.error as any)?.response?.data?.detail || "Already claimed"}
          </p>
        )}
        {bonusMutation.isSuccess && (
          <p className="text-sm text-green-600">50 credits added to your account!</p>
        )}
      </div>

      <div className="bg-white rounded-xl border shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Transaction History</h2>

        {!history?.transactions?.length ? (
          <p className="text-gray-500 text-sm">No transactions yet</p>
        ) : (
          <div className="space-y-3">
            {history.transactions.map((tx: any) => (
              <div key={tx.id} className="flex items-center justify-between py-3 border-b last:border-0">
                <div className="flex items-center gap-3">
                  {tx.amount > 0 ? (
                    <ArrowDownLeft className="w-5 h-5 text-green-500" />
                  ) : (
                    <ArrowUpRight className="w-5 h-5 text-red-500" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-900">{tx.description}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <span
                  className={`font-semibold ${tx.amount > 0 ? "text-green-600" : "text-red-600"}`}
                >
                  {tx.amount > 0 ? "+" : ""}
                  {tx.amount}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
