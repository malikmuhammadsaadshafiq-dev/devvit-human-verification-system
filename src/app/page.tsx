export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl w-full text-center">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          Devvit - Human Verification System
        </h1>
        <p className="text-gray-400 text-xl mb-10">Advanced human verification for Reddit communities. Protect subreddits from bots and spam.</p>
        <ul className="text-left space-y-3 mb-10 inline-block text-lg text-gray-300">
          <li key="0" className="flex items-center gap-2"><span className="text-green-500">&#10003;</span>Proof-of-human challenges</li><li key="1" className="flex items-center gap-2"><span className="text-green-500">&#10003;</span>Reddit mod dashboard</li><li key="2" className="flex items-center gap-2"><span className="text-green-500">&#10003;</span>Custom verification flows</li><li key="3" className="flex items-center gap-2"><span className="text-green-500">&#10003;</span>Auto-ban bot accounts</li><li key="4" className="flex items-center gap-2"><span className="text-green-500">&#10003;</span>Real-time analytics</li>
        </ul>
        <div>
          <a href="#" className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-xl transition-colors">
            Get Early Access
          </a>
        </div>
      </div>
    </main>
  );
}
