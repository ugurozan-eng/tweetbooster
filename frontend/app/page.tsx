import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)] px-4">
      <div className="text-center max-w-xl w-full">
        {/* Product name */}
        <h1 className="text-4xl sm:text-5xl font-bold text-white mb-3 tracking-tight">
          TwitBoost
        </h1>
        <p className="text-zinc-400 mb-10 text-base sm:text-lg">
          AI destekli Twitter yanıt aracı — Türkçe kullanıcılar için
        </p>

        {/* Mode buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/opposition"
            className="flex flex-col items-start gap-1 rounded-xl border border-zinc-700 bg-zinc-900 px-6 py-5 hover:border-blue-500 hover:bg-zinc-800 transition-all group"
          >
            <span className="text-xs font-semibold text-blue-400 uppercase tracking-widest">
              Mod 1
            </span>
            <span className="text-lg font-bold text-white group-hover:text-blue-300 transition-colors">
              Muhalif Mod
            </span>
            <span className="text-sm text-zinc-400 text-left">
              Tweet araştır, tutarsızlık bul, yanıt üret
            </span>
          </Link>

          <Link
            href="/niche"
            className="flex flex-col items-start gap-1 rounded-xl border border-zinc-700 bg-zinc-900 px-6 py-5 hover:border-emerald-500 hover:bg-zinc-800 transition-all group"
          >
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-widest">
              Mod 2
            </span>
            <span className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors">
              Niş Mod
            </span>
            <span className="text-sm text-zinc-400 text-left">
              Trend tweetleri getir, etkileşim yanıtları üret
            </span>
          </Link>
        </div>
      </div>
    </div>
  );
}
