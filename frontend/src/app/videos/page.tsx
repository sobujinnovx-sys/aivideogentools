"use client";

import { useQuery } from "@tanstack/react-query";
import { getVideos, deleteVideo, downloadVideo } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2, Download, Play, Clock, Film } from "lucide-react";

export default function VideosPage() {
  const router = useRouter();
  const token = useAuthStore((s) => s.token);
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!token) router.push("/auth/login");
  }, [token, router]);

  const { data, isLoading } = useQuery({
    queryKey: ["videos", page],
    queryFn: async () => {
      const res = await getVideos(page);
      return res.data;
    },
    enabled: !!token,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteVideo,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["videos"] }),
  });

  if (!token) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Video Library</h1>
        <button
          onClick={() => router.push("/generate")}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          New Video
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto" />
        </div>
      ) : data?.videos?.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <Film className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No videos yet</p>
          <button
            onClick={() => router.push("/generate")}
            className="mt-4 text-blue-600 hover:underline"
          >
            Generate your first video
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data?.videos?.map((video: any) => (
              <div key={video.id} className="bg-white rounded-xl border shadow-sm overflow-hidden">
                <div className="aspect-video bg-gray-900 relative group">
                  {video.thumbnail_path ? (
                    <img
                      src={video.thumbnail_path}
                      alt={video.prompt}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Play className="w-12 h-12 text-white opacity-30" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                    <Play className="w-12 h-12 text-white" />
                  </div>
                </div>

                <div className="p-4">
                  <p className="text-sm text-gray-900 line-clamp-2 mb-3">{video.prompt}</p>
                  <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {video.duration}s
                    </span>
                    <span>{video.aspect_ratio}</span>
                    <span>{video.resolution}</span>
                    <span>{video.model_used}</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => downloadVideo(video.id)}
                      className="flex-1 flex items-center justify-center gap-1 bg-blue-600 text-white py-2 rounded-lg text-sm hover:bg-blue-700 transition"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </button>
                    <button
                      onClick={() => deleteMutation.mutate(video.id)}
                      className="p-2 text-gray-400 hover:text-red-500 border rounded-lg"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {data?.total > 20 && (
            <div className="flex justify-center gap-2 mt-8">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 border rounded-lg text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-sm text-gray-500">
                Page {page} of {Math.ceil(data.total / 20)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= Math.ceil(data.total / 20)}
                className="px-4 py-2 border rounded-lg text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
