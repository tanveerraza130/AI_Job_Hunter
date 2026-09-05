"use client";

import { useEffect, useRef, useState } from "react";

const DESKTOP_HEIGHT = 760;
const MOBILE_FALLBACK_HEIGHT = 1620;

export default function Section1() {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const observerRef = useRef<ResizeObserver | null>(null);

  const [mobileHeight, setMobileHeight] = useState(
    MOBILE_FALLBACK_HEIGHT,
  );

  useEffect(() => {
    const iframe = iframeRef.current;

    if (!iframe) return;

    const measure = () => {
      if (window.innerWidth > 620) {
        return;
      }

      try {
        const document = iframe.contentDocument;

        if (!document) return;

        const html = document.documentElement;
        const body = document.body;

        const height = Math.max(
          html?.scrollHeight ?? 0,
          html?.offsetHeight ?? 0,
          body?.scrollHeight ?? 0,
          body?.offsetHeight ?? 0,
        );

        if (height > 0) {
          setMobileHeight(Math.max(Math.ceil(height), 1620));
        }
      } catch {
        setMobileHeight(MOBILE_FALLBACK_HEIGHT);
      }
    };

    const handleLoad = () => {
      observerRef.current?.disconnect();
      observerRef.current = null;

      measure();

      const document = iframe.contentDocument;

      if (!document) return;

      const observer = new ResizeObserver(() => {
        measure();
      });

      observer.observe(document.documentElement);

      if (document.body) {
        observer.observe(document.body);
      }

      observerRef.current = observer;

      requestAnimationFrame(measure);
      setTimeout(measure, 100);
      setTimeout(measure, 500);
    };

    iframe.addEventListener("load", handleLoad);
    window.addEventListener("resize", measure);

    return () => {
      iframe.removeEventListener("load", handleLoad);
      window.removeEventListener("resize", measure);

      observerRef.current?.disconnect();
      observerRef.current = null;
    };
  }, []);

  return (
    <>
      <section
        aria-label="AI Job Hunter"
        style={{
          width: "100%",
          height: DESKTOP_HEIGHT,
          border: "0",
          overflow: "hidden",
        }}
      >
        <iframe
          ref={iframeRef}
          src="/sections/section1/index.html"
          title="AI Job Hunter"
          scrolling="no"
          style={{
            width: "100%",
            height: DESKTOP_HEIGHT,
            border: "0",
            display: "block",
            overflow: "hidden",
          }}
        />
      </section>

      <style>{`
        @media (max-width: 620px) {
          section[aria-label="AI Job Hunter"] {
            height: ${mobileHeight}px !important;
            overflow: hidden !important;
          }

          section[aria-label="AI Job Hunter"] iframe {
            height: ${mobileHeight}px !important;
            overflow: hidden !important;
          }
        }
      `}</style>
    </>
  );
}
