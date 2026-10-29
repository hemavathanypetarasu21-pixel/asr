"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const LEVEL_FFT_SIZE = 256;

/** Microphone recorder exposing elapsed time and a live input level (0–1). */
export function useRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [level, setLevel] = useState(0);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const resolveRef = useRef<((file: File) => void) | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => () => cleanupRef.current?.(), []);

  const start = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      throw new Error("Audio recording is not supported in this browser.");
    }
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      throw new Error("Microphone access was blocked. Allow access and try again.");
    }

    const context = new AudioContext();
    const analyser = context.createAnalyser();
    analyser.fftSize = LEVEL_FFT_SIZE;
    context.createMediaStreamSource(stream).connect(analyser);
    const samples = new Uint8Array(analyser.fftSize);
    const startedAt = performance.now();
    let frame = 0;
    const tick = () => {
      analyser.getByteTimeDomainData(samples);
      const peak = samples.reduce((max, value) => Math.max(max, Math.abs(value - 128)), 0) / 128;
      setLevel(peak);
      setElapsed((performance.now() - startedAt) / 1000);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);

    cleanupRef.current = () => {
      cancelAnimationFrame(frame);
      stream.getTracks().forEach((track) => track.stop());
      void context.close();
    };

    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunksRef.current.push(event.data);
    };
    recorder.onstop = () => {
      cleanupRef.current?.();
      cleanupRef.current = null;
      setIsRecording(false);
      setLevel(0);
      const type = recorder.mimeType || "audio/webm";
      resolveRef.current?.(new File(chunksRef.current, `speech-${Date.now()}.webm`, { type }));
      resolveRef.current = null;
    };
    recorderRef.current = recorder;
    recorder.start();
    setElapsed(0);
    setIsRecording(true);
  }, []);

  /** Stops recording and resolves with the recorded file. */
  const stop = useCallback(
    () =>
      new Promise<File>((resolve, reject) => {
        const recorder = recorderRef.current;
        if (!recorder || recorder.state !== "recording") {
          reject(new Error("Not recording."));
          return;
        }
        resolveRef.current = resolve;
        recorder.stop();
      }),
    [],
  );

  return { isRecording, elapsed, level, start, stop };
}
