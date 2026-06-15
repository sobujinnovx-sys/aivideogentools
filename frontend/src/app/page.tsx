import Link from "next/link";

export default function Home() {
  return (
    <div className="relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            AI Video Generator
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Type a prompt or upload images and get a 15-second AI-generated video
            in minutes.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/generate"
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Start Generating
            </Link>
            <Link
              href="/auth/register"
              className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition"
            >
              Create Account
            </Link>
          </div>
        </div>

        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            {
              title: "Text to Video",
              desc: "Describe your scene and let AI bring it to life",
            },
            {
              title: "Image to Video",
              desc: "Upload reference images for guided generation",
            },
            {
              title: "Multiple Formats",
              desc: "16:9, 9:16, and 1:1 aspect ratios supported",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="bg-white p-6 rounded-xl shadow-sm border"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600">{feature.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { step: "1", text: "Write a prompt or upload images" },
              { step: "2", text: "Choose duration and aspect ratio" },
              { step: "3", text: "AI generates your video" },
              { step: "4", text: "Download your MP4" },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 font-bold">
                  {item.step}
                </div>
                <p className="text-gray-600">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
