"use client"

import React, { useState, useEffect, useRef } from "react"
import styles from "./App.module.css"
import axios from "axios"
import Webcam from "react-webcam"
import { useReactMediaRecorder } from "react-media-recorder"

const API_URL = "http://localhost:8000/api/activate"
const animatedTextLines = ["Your Silent Guardian.", "Instant Alerts.", "Immutable Proof."]

function App() {
  // --- Intro animation state ---
  const [displayLines, setDisplayLines] = useState<string[]>(["", "", ""])
  const [currentLine, setCurrentLine] = useState(0)
  const [charIndex, setCharIndex] = useState(0)
  const [showIntro, setShowIntro] = useState(true)

  // --- Button state (idle, loading, success, error) ---
  const [buttonState, setButtonState] = useState<"idle" | "loading" | "success" | "error">("idle")

  // --- Status & verdict ---
  const [statusText, setStatusText] = useState("Idle")
  const [verdict, setVerdict] = useState("System is Idle.")

  // --- Webcam reference ---
  const webcamRef = useRef<Webcam>(null)

  // --- File input ref (video upload) ---
  const fileInputRef = useRef<HTMLInputElement>(null)

  // --- Audio recording ---
  const { status: audioStatus, startRecording, stopRecording } = useReactMediaRecorder({
    audio: true,
    onStop: (blobUrl, blob) => handleAudioUpload(blob),
  })

  // Intro overlay
  useEffect(() => {
    const introTimer = setTimeout(() => setShowIntro(false), 1500)
    return () => clearTimeout(introTimer)
  }, [])

  // Animated typing effect
  useEffect(() => {
    if (!showIntro && currentLine < animatedTextLines.length) {
      const currentText = animatedTextLines[currentLine]
      if (charIndex < currentText.length) {
        const timeoutId = setTimeout(() => {
          setDisplayLines((prev) => {
            const newLines = [...prev]
            newLines[currentLine] = currentText.slice(0, charIndex + 1)
            return newLines
          })
          setCharIndex((prev) => prev + 1)
        }, 50)
        return () => clearTimeout(timeoutId)
      } else {
        const timeoutId = setTimeout(() => {
          setCurrentLine((prev) => prev + 1)
          setCharIndex(0)
        }, 200)
        return () => clearTimeout(timeoutId)
      }
    }
  }, [currentLine, charIndex, showIntro])

  // --- Backend Upload Helper ---
  const sendToBackend = async (formData: FormData | object, isMultipart = false) => {
    setButtonState("loading")
    setStatusText("Analyzing...")
    setVerdict("Analyzing media...")

    try {
      const response = await axios.post(API_URL, formData, {
        headers: isMultipart ? { "Content-Type": "multipart/form-data" } : undefined,
      })
      console.log("✅ Backend responded:", response.data)
      setVerdict(response.data.message)
      setButtonState("success")
    } catch (error) {
      console.error("❌ Error sending to backend:", error)
      setVerdict("Error: Could not connect to backend.")
      setButtonState("error")
    } finally {
      setStatusText("Idle")
      setTimeout(() => setButtonState("idle"), 3000)
    }
  }

  // --- Webcam activation ---
  const handleWebcamActivate = async () => {
    if (buttonState === "loading") return
    const imageSrc = webcamRef.current?.getScreenshot()
    if (!imageSrc) {
      console.error("❌ Could not capture image")
      setButtonState("error")
      return
    }
    await sendToBackend({ image: imageSrc })
  }

  // --- Audio activation (5s auto-stop) ---
  const handleAudioActivate = () => {
    if (audioStatus === "recording") return
    startRecording()
    setButtonState("loading")
    setStatusText("Analyzing...")
    setVerdict("Recording audio...")
    setTimeout(() => stopRecording(), 5000)
  }

  const handleAudioUpload = async (audioBlob: Blob) => {
    const formData = new FormData()
    formData.append("media_file", audioBlob, "recording.wav")
    await sendToBackend(formData, true)
  }

  // --- Video upload ---
  const onVideoFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const formData = new FormData()
      formData.append("media_file", file, file.name)
      sendToBackend(formData, true)
    }
  }

  // --- Button text states ---
  const getButtonText = (mode: "webcam" | "audio" | "video") => {
    if (buttonState === "loading") return mode === "webcam" ? "Activating..." : mode === "audio" ? "Listening 5s..." : "Uploading..."
    if (buttonState === "success") return "Guardian Activated!"
    if (buttonState === "error") return "Connection Failed"
    return mode === "webcam" ? "Activate via Webcam" : mode === "audio" ? "Activate via Audio" : "Upload Video"
  }

  return (
    <div className={styles.container}>
      {/* Webcam (hidden with CSS) */}
      <Webcam audio={false} ref={webcamRef} screenshotFormat="image/jpeg" className={styles.webcamHidden} />

      {/* Intro overlay */}
      {showIntro && (
        <div className={styles.introOverlay}>
          <h1 className={styles.introTitle}>GuardianAI</h1>
        </div>
      )}

      {/* Shooting stars background */}
      <div className={styles.shootingStars}>
        <div className={styles.shootingStar}></div>
        <div className={styles.shootingStar}></div>
        <div className={styles.shootingStar}></div>
        <div className={styles.shootingStar}></div>
        <div className={styles.shootingStar}></div>
      </div>

      {/* Main content */}
      <div className={`${styles.mainContent} ${!showIntro ? styles.revealed : ""}`}>
        <div className={styles.textSection}>
          <h1 className={styles.header}>GuardianAI</h1>

          {/* Animated subtitle */}
          <div className={styles.subtitleContainer}>
            {displayLines.map((line, index) => (
              <p key={index} className={styles.subtitleLine}>
                {line}
                {currentLine === index && <span className={styles.cursor}>_</span>}
              </p>
            ))}
          </div>

          {/* Status + Verdict */}
          <p className={styles.headline}>
            Status: <span className={styles.statusText}>{statusText}</span>
          </p>
          <div className={styles.verdictBox}>
            <p>{verdict}</p>
          </div>
        </div>

        {/* Buttons */}
        <div className={styles.buttonSection}>
          <button className={`${styles.ctaButton} ${styles[buttonState]}`} onClick={handleWebcamActivate} disabled={buttonState === "loading"}>
            <span className={styles.buttonText}>{getButtonText("webcam")}</span>
            <span className={styles.buttonRipple}></span>
          </button>

          <button className={`${styles.ctaButton} ${styles[buttonState]}`} onClick={handleAudioActivate} disabled={buttonState === "loading"}>
            <span className={styles.buttonText}>{getButtonText("audio")}</span>
            <span className={styles.buttonRipple}></span>
          </button>

          <input type="file" accept="video/*" ref={fileInputRef} style={{ display: "none" }} onChange={onVideoFileChange} />
          <button className={`${styles.ctaButton} ${styles[buttonState]}`} onClick={() => fileInputRef.current?.click()} disabled={buttonState === "loading"}>
            <span className={styles.buttonText}>{getButtonText("video")}</span>
            <span className={styles.buttonRipple}></span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default App
