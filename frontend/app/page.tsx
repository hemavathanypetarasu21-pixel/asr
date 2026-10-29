import Link from "next/link";
import BrandMark from "@/components/BrandMark";
import { env } from "@/lib/env";
import { routes } from "@/lib/routes";

type Token = { word: string; lang: "en" | "ms" | "ta" };

const dialectSamples: { dialect: string; mix: string; tokens: Token[]; translation: string }[] = [
  {
    dialect: "Manglish",
    mix: "Malay + English",
    tokens: [
      { word: "Eh,", lang: "ms" },
      { word: "you", lang: "en" },
      { word: "dah makan ke?", lang: "ms" },
      { word: "Jom", lang: "ms" },
      { word: "we go", lang: "en" },
      { word: "mamak", lang: "ms" },
      { word: "after this meeting.", lang: "en" },
    ],
    translation: "Hey, have you eaten? Let's go to the mamak stall after this meeting.",
  },
  {
    dialect: "Tanglish",
    mix: "Tamil + English",
    tokens: [
      { word: "Machan,", lang: "ta" },
      { word: "naan", lang: "ta" },
      { word: "office", lang: "en" },
      { word: "la irukken,", lang: "ta" },
      { word: "I'll call you back in ten minutes.", lang: "en" },
    ],
    translation: "Bro, I'm at the office, I'll call you back in ten minutes.",
  },
];

const languageStyles: Record<Token["lang"], string> = {
  en: "bg-subtle text-ink",
  ms: "bg-brand-soft text-brand-ink",
  ta: "bg-accent-soft text-accent",
};

const features = [
  {
    title: "Speak or upload",
    body: "Tap the microphone and talk naturally, or upload an existing clip. Every recording is saved to your account.",
    icon: "M12 15a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3Zm6-3a6 6 0 0 1-12 0m6 6v3",
  },
  {
    title: "Manglish or Tanglish detection",
    body: "Speech recognition models identify whether a recording is Malay–English or Tamil–English, with a confidence score.",
    icon: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm-9 9h18M12 3c2.5 2.5 3.8 5.5 3.8 9s-1.3 6.5-3.8 9c-2.5-2.5-3.8-5.5-3.8-9S9.5 5.5 12 3Z",
  },
  {
    title: "Translation to English",
    body: "Code-switched speech is translated into clear English, keeping names and meaning intact.",
    icon: "M4 5h7M7.5 5v1.5c0 3-1.5 5.5-4 7M5 9.5c1 2 3 3.5 5.5 4.5M13 20l4-9 4 9m-6.8-3h5.6",
  },
  {
    title: "Native and non-native speakers",
    body: "Tag each recording with the speaker's nativeness so results can be compared across accents.",
    icon: "M16 19v-1a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v1M9 10a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm13 9v-1a4 4 0 0 0-3-3.9M16 3.1a3.5 3.5 0 0 1 0 6.8",
  },
  {
    title: "Choose your models",
    body: "Pick the dialect recognition model and the translation model that fit your accuracy and speed needs.",
    icon: "M4 6h16M4 12h10M4 18h6m8-6 2 2-2 2m-3 2 2 2-2 2",
  },
  {
    title: "Insights for every recording",
    body: "Replay audio, read the transcript, and see whether the detected dialect matches what was declared.",
    icon: "M4 19V9m5 10V5m5 14v-7m5 7V3",
  },
] as const;

const steps = [
  { title: "Speak", body: "Choose Manglish or Tanglish and your speaker mode, then talk or upload a clip." },
  { title: "Save", body: "The recording is stored securely in your account, ready when you are." },
  { title: "Analyse", body: "Detect the dialect and get an English translation in Insights." },
] as const;

function Icon({ path }: { path: string }) {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d={path} />
    </svg>
  );
}

function TokenLine({ tokens }: { tokens: Token[] }) {
  return (
    <span className="flex flex-wrap gap-1.5 leading-7">
      {tokens.map((token) => (
        <span key={token.word} className={`rounded-md px-1.5 ${languageStyles[token.lang]}`}>{token.word}</span>
      ))}
    </span>
  );
}

export default function LandingPage() {
  const [manglish] = dialectSamples;

  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <header className="sticky top-0 z-20 border-b border-line bg-surface/90 backdrop-blur">
        <nav className="mx-auto flex h-14 max-w-6xl items-center justify-between px-5" aria-label="Main">
          <BrandMark href={routes.home} />
          <div className="hidden items-center gap-6 text-[13px] font-medium text-muted md:flex">
            <a href="#dialects" className="hover:text-heading">Dialects</a>
            <a href="#features" className="hover:text-heading">Features</a>
            <a href="#how-it-works" className="hover:text-heading">How it works</a>
          </div>
          <div className="flex items-center gap-2">
            <Link href={routes.login} className="btn text-ink hover:bg-subtle">Log in</Link>
            <Link href={routes.signup} className="btn-primary">Get started</Link>
          </div>
        </nav>
      </header>

      <main className="flex-1">
        <section className="mx-auto grid max-w-6xl items-center gap-10 px-5 py-12 sm:py-16 lg:grid-cols-[1.05fr_1fr]">
          <div>
            <p className="eyebrow">Speech recognition for Malaysian code-switching</p>
            <h1 className="mt-3 text-3xl font-bold leading-[1.15] tracking-tight text-heading sm:text-4xl">
              Speak Manglish or Tanglish. Understand it in English.
            </h1>
            <p className="mt-4 max-w-xl text-[15px] leading-7 text-muted">
              {env.appName} records your mixed-language speech, detects whether it is{" "}
              <strong className="text-heading">Manglish</strong> (Malay–English) or{" "}
              <strong className="text-heading">Tanglish</strong> (Tamil–English), and translates it to English.
            </p>
            <div className="mt-6 flex flex-wrap gap-2.5">
              <Link href={routes.signup} className="btn-primary min-h-10 px-5 text-sm">Start speaking</Link>
              <a href="#how-it-works" className="btn-secondary min-h-10 px-5 text-sm">See how it works</a>
            </div>
            <ul className="mt-6 flex flex-wrap gap-1.5 text-[11px] font-semibold" aria-label="Supported dialects">
              <li className="rounded-full bg-brand-soft px-3 py-1.5 text-brand-ink">Manglish</li>
              <li className="rounded-full bg-accent-soft px-3 py-1.5 text-accent">Tanglish</li>
              <li className="rounded-full bg-subtle px-3 py-1.5 text-ink">Native &amp; non-native speakers</li>
            </ul>
          </div>

          <figure className="card p-4 text-[13px] shadow-[0_24px_60px_-20px_rgb(40_30_120/0.25)] sm:p-5" aria-label="Example analysis">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-white" aria-hidden="true">
                <Icon path={features[0].icon} />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-heading">speech-recording.webm</p>
                <p className="text-xs text-muted">Declared: Manglish · Non-native speaker</p>
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Example</span>
            </div>
            <div className="mt-4 flex h-10 items-center gap-[3px]" aria-hidden="true">
              {Array.from({ length: 48 }, (_, index) => (
                <span key={index} className="w-full rounded-full bg-brand/60" style={{ height: `${20 + Math.abs(Math.sin(index * 0.7)) * 70}%` }} />
              ))}
            </div>
            <div className="mt-4 grid gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">Transcript</p>
                <p className="mt-1.5"><TokenLine tokens={manglish.tokens} /></p>
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="rounded-full bg-brand-soft px-2.5 py-1 text-xs font-semibold text-brand-ink">Detected: Manglish</span>
                <span className="rounded-full bg-accent-soft px-2.5 py-1 text-xs font-semibold text-accent">Matches declared</span>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">English</p>
                <p className="mt-1.5 rounded-lg bg-subtle p-3 leading-6 text-ink">{manglish.translation}</p>
              </div>
            </div>
          </figure>
        </section>

        <section id="dialects" className="border-y border-line bg-surface">
          <div className="mx-auto max-w-6xl px-5 py-12 sm:py-16">
            <p className="eyebrow">Built for two dialects</p>
            <h2 className="mt-2 max-w-2xl text-2xl font-bold tracking-tight text-heading">
              Real conversations switch languages mid-sentence. So do we.
            </h2>
            <div className="mt-8 grid gap-4 md:grid-cols-2">
              {dialectSamples.map((sample) => (
                <article key={sample.dialect} className="card flex flex-col bg-canvas p-5 text-[13px]">
                  <div className="flex items-baseline justify-between">
                    <h3 className="text-lg font-bold text-heading">{sample.dialect}</h3>
                    <span className="text-xs text-muted">{sample.mix}</span>
                  </div>
                  <p className="mt-4"><TokenLine tokens={sample.tokens} /></p>
                  <p className="mt-3 border-t border-line pt-3 leading-6 text-muted">
                    <span className="font-semibold text-heading">English: </span>{sample.translation}
                  </p>
                </article>
              ))}
            </div>
            <div className="mt-6 flex flex-wrap gap-4 text-xs text-muted">
              <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-brand-soft ring-1 ring-brand/40" />Malay</span>
              <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-accent-soft ring-1 ring-accent/40" />Tamil</span>
              <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-subtle ring-1 ring-line" />English</span>
            </div>
          </div>
        </section>

        <section id="features" className="mx-auto max-w-6xl px-5 py-12 sm:py-16">
          <p className="eyebrow">Features</p>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-heading">From your voice to clear English</h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <article key={feature.title} className="card p-5">
                <span className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-soft text-brand-ink">
                  <Icon path={feature.icon} />
                </span>
                <h3 className="mt-3 text-sm font-semibold text-heading">{feature.title}</h3>
                <p className="mt-1.5 text-[13px] leading-6 text-muted">{feature.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="how-it-works" className="border-t border-line bg-surface">
          <div className="mx-auto max-w-6xl px-5 py-12 sm:py-16">
            <p className="eyebrow">How it works</p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-heading">Speak, save, analyse</h2>
            <ol className="mt-8 grid gap-4 md:grid-cols-3">
              {steps.map((step, index) => (
                <li key={step.title} className="card bg-canvas p-5">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand text-xs font-bold text-white">{index + 1}</span>
                  <h3 className="mt-2.5 text-sm font-semibold text-heading">{step.title}</h3>
                  <p className="mt-1 text-[13px] leading-6 text-muted">{step.body}</p>
                </li>
              ))}
            </ol>
            <div className="mt-10 flex flex-col items-start justify-between gap-4 rounded-xl bg-brand p-6 text-white sm:flex-row sm:items-center">
              <div>
                <h3 className="text-lg font-bold">Try it with your own voice</h3>
                <p className="mt-0.5 text-[13px] text-white/80">Create an account and record your first Manglish or Tanglish clip.</p>
              </div>
              <Link href={routes.signup} className="btn min-h-10 bg-white px-5 text-sm text-brand hover:bg-white/90">
                Create account
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line bg-canvas">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-5 py-6 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
          <BrandMark href={routes.home} />
          <nav className="flex gap-5" aria-label="Footer">
            <a href="#features" className="hover:text-heading">Features</a>
            <Link href={routes.login} className="hover:text-heading">Log in</Link>
            <Link href={routes.signup} className="hover:text-heading">Sign up</Link>
          </nav>
          <p>© {new Date().getFullYear()} {env.appName}</p>
        </div>
      </footer>
    </div>
  );
}
