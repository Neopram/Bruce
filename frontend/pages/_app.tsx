// Ruta: C:\Users\feder\Downloads\BruceWayneV1\frontend\pages\_app.tsx

import type { AppProps } from "next/app"
import Head from "next/head"
import { AuthProvider } from "@/contexts/AuthContext"
import "@/styles/globals.css"

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Head>
        <title>Bruce AI</title> 
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta charSet="UTF-8" />
        <meta name="description" content="Intelligent trading assistant powered by Bruce & Aurora." />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Component {...pageProps} />
    </AuthProvider>
  )
}
