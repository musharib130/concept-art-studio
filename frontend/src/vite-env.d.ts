/// <reference types="vite/client" />

export {};

declare global {
  interface Window {
    pywebview?: {
      api: {
        check_weights(): Promise<{ downloaded: boolean }>;
        download_weights(): Promise<{ ok: true } | { ok: false; error: string }>;
        generate_image(
          prompt: string,
          imageBase64: string | null
        ): Promise<{ image: string } | { error: string }>;
      };
    };
  }
}
