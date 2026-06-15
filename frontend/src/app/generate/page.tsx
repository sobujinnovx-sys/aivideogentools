"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { generateVideo, uploadImage, getJob } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { Upload, X, Loader2, Download, Play, CheckCircle, AlertCircle } from "lucide-react";

const DURATIONS = [
  { value: 5, label: "5s", credits: 10 },
  { value: 10, label: "10s", credits: 20 },
  { value: 15, label: "15s", credits: 30 },
];

const ASPECT_RATIOS = [
  { value: "16:9", label: "16:9", desc: "Landscape" },
  { value: "9:16", label: "9:16", desc: "Portrait" },
  { value: "1:1", label: "1:1", desc: "Square" },
];

const MODELS = [
  { value: "wan2.1", label: "Wan 2.1", desc: "Text-to-video" },
  { value: "ltx-video", label: "LTX Video", desc: "Image-to-video" },
  { value: "cogvideox", label: "CogVideoX", desc: "Fallback" },
];

export default function GeneratePage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState(15);
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [model, setModel] = useState("wan2.1");
  const [images, setImages] = useState<{ url: string; file: File }[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const selectedCredits = DURATIONS.find((d) => d.value === duration)?.credits || 30;

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadImage(file),
  });

  const generateMutation = useMutation({
    mutationFn: generateVideo,
    onSuccess: (res) => {
      setJobId(res.data.id);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Generation failed");
    },
  });

  const { data: jobData } = useQuery({
    queryKey: ["job", jobId],
    queryFn: async () => {
      const res = await getJob(jobId!);
      return res.data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 2000;
    },
  });

  const handleImageUpload = useCallback(
    async (files: FileList) => {
      const remaining = 5 - images.length;
      const toUpload = Array.from(files).slice(0, remaining);

      for (const file of toUpload) {
        try {
          const res = await uploadMutation.mutateAsync(file);
          setImages((prev) => [...prev, { url: res.data.url, file }]);
        } catch {
          setError("Failed to upload image");
        }
      }
    },
    [images.length, uploadMutation]
  );

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  const handleGenerate = () => {
    if (!prompt.trim()) {
      setError("Please enter a prompt");
      return;
    }
    if (user && user.credits < selectedCredits) {
      setError("Insufficient credits");
      return;
    }

    setError("");
    generateMutation.mutate({
      prompt,
      duration,
      aspect_ratio: aspectRatio,
      model,
      image_urls: images.map((img) => img.url),
    });
  };

  const isGenerating = jobData && !["completed", "failed"].includes(jobData.status);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Generate Video</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the video you want to generate..."
              className="w-full h-32 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
              maxLength={2000}
            />
            <p className="text-xs text-gray-400 mt-1">{prompt.length}/2000</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reference Images (optional, max 5)
            </label>
            <div
              className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 transition"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                handleImageUpload(e.dataTransfer.files);
              }}
            >
              <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">Click or drag images here</p>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={(e) => e.target.files && handleImageUpload(e.target.files)}
              />
            </div>

            {images.length > 0 && (
              <div className="flex gap-3 mt-3 flex-wrap">
                {images.map((img, i) => (
                  <div key={i} className="relative w-20 h-20">
                    <img
                      src={img.url}
                      alt={`Reference ${i + 1}`}
                      className="w-full h-full object-cover rounded-lg border"
                    />
                    <button
                      onClick={() => removeImage(i)}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-0.5"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Duration</label>
            <div className="flex gap-3">
              {DURATIONS.map((d) => (
                <button
                  key={d.value}
                  onClick={() => setDuration(d.value)}
                  className={`flex-1 py-2 px-4 rounded-lg border text-sm font-medium transition ${
                    duration === d.value
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-200 text-gray-600 hover:border-gray-300"
                  }`}
                >
                  {d.label}
                  <span className="block text-xs text-gray-400">{d.credits} credits</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Aspect Ratio</label>
            <div className="flex gap-3">
              {ASPECT_RATIOS.map((ar) => (
                <button
                  key={ar.value}
                  onClick={() => setAspectRatio(ar.value)}
                  className={`flex-1 py-2 px-4 rounded-lg border text-sm font-medium transition ${
                    aspectRatio === ar.value
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-200 text-gray-600 hover:border-gray-300"
                  }`}
                >
                  {ar.label}
                  <span className="block text-xs text-gray-400">{ar.desc}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">AI Model</label>
            <div className="flex gap-3">
              {MODELS.map((m) => (
                <button
                  key={m.value}
                  onClick={() => setModel(m.value)}
                  className={`flex-1 py-2 px-4 rounded-lg border text-sm font-medium transition ${
                    model === m.value
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-200 text-gray-600 hover:border-gray-300"
                  }`}
                >
                  {m.label}
                  <span className="block text-xs text-gray-400">{m.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}

          <button
            onClick={handleGenerate}
            disabled={generateMutation.isPending || !!isGenerating}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
          >
            {generateMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Submitting...
              </>
            ) : isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Generate Video ({selectedCredits} credits)
              </>
            )}
          </button>
        </div>

        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-4">Status</h3>

            {!jobId && <p className="text-sm text-gray-500">No active generation</p>}

            {jobData && (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  {jobData.status === "completed" && <CheckCircle className="w-5 h-5 text-green-500" />}
                  {jobData.status === "failed" && <AlertCircle className="w-5 h-5 text-red-500" />}
                  {isGenerating && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
                  <span className="text-sm font-medium capitalize">{jobData.status}</span>
                </div>

                {isGenerating && (
                  <div>
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Progress</span>
                      <span>{Math.round(jobData.progress * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${jobData.progress * 100}%` }}
                      />
                    </div>
                  </div>
                )}

                {jobData.status === "failed" && jobData.error_message && (
                  <p className="text-xs text-red-500">{jobData.error_message}</p>
                )}

                {jobData.status === "completed" && (
                  <div className="space-y-3">
                    <div className="bg-gray-900 rounded-lg aspect-video flex items-center justify-center">
                      <Play className="w-12 h-12 text-white opacity-50" />
                    </div>
                    <a
                      href={`/api/videos/?job_id=${jobData.id}`}
                      className="flex items-center justify-center gap-2 bg-green-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition"
                    >
                      <Download className="w-4 h-4" />
                      Download MP4
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="bg-white p-6 rounded-xl border shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-3">Your Credits</h3>
            <p className="text-3xl font-bold text-blue-600">{user?.credits || 0}</p>
            <p className="text-xs text-gray-500 mt-1">New accounts get 50 free credits</p>
          </div>
        </div>
      </div>
    </div>
  );
}
