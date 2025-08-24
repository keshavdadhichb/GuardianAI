import express, { Request, Response } from 'express';
import cors from 'cors';
import { PrismaClient } from '@prisma/client';
import axios from 'axios';
import { ethers } from 'ethers';
import 'dotenv/config';
import crypto from 'crypto';
import twilio from 'twilio';
import multer from 'multer';
import FormData from 'form-data';

import GuardianLogABI from '../../guardianai-blockchain/artifacts/contracts/GuardianLogs.sol/GuardianLog.json';

// --- Setup ---
const prisma = new PrismaClient();
const app = express();
const PORT = 8000;
const AI_SERVICE_URL = 'http://127.0.0.1:8001/api/analyze';
const twilioClient = twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);

const storage = multer.memoryStorage();
const upload = multer({ storage });

app.use(cors());
app.use(express.json({ limit: '5mb' }));

// --- Helper: Blockchain ---
async function logEvidenceOnBlockchain(evidenceHash: string) {
  try {
    const provider = new ethers.JsonRpcProvider(process.env.LOCAL_RPC_URL);
    const wallet = new ethers.Wallet(process.env.LOCAL_WALLET_PRIVATE_KEY!, provider);
    const guardianLogContract = new ethers.Contract(
      process.env.LOCAL_CONTRACT_ADDRESS!,
      GuardianLogABI.abi,
      wallet
    );
    console.log(`Submitting hash to blockchain: ${evidenceHash}`);
    const tx = await guardianLogContract.logEvidence(
      evidenceHash,
      Math.floor(Date.now() / 1000),
      "0,0"
    );
    const receipt = await tx.wait();
    console.log(`✅ Blockchain tx success! Hash: ${receipt.hash}`);
    return receipt.hash;
  } catch (error) {
    console.error("❌ Blockchain tx failed:", error);
    return null;
  }
}

// --- Helper: SMS ---
async function sendSmsAlert(verdict: string) {
  const messageBody = `GuardianAI Alert: A potential threat has been detected. AI Verdict: "${verdict}".`;
  try {
    console.log(`Sending SMS alert to ${process.env.EMERGENCY_CONTACT_PHONE_NUMBER}...`);
    await twilioClient.messages.create({
      body: messageBody,
      from: process.env.TWILIO_PHONE_NUMBER,
      to: process.env.EMERGENCY_CONTACT_PHONE_NUMBER!,
    });
    console.log('✅ SMS sent successfully.');
  } catch (error) {
    console.error('❌ SMS failed:', error);
  }
}

// --- MAIN ENDPOINT: Activate ---
app.post('/api/activate', upload.single('media_file'), async (req: Request, res: Response) => {
  try {
    let aiResponse;
    let evidenceBuffer: Buffer;

    if (req.file) {
      // Case 1: Video or Audio
      const isVideo = req.file.mimetype.startsWith('video/');
      const formData = new FormData();

      if (isVideo) {
        formData.append('video_file', req.file.buffer, {
          filename: req.file.originalname,
          contentType: req.file.mimetype,
        });
      } else {
        formData.append('audio_file', req.file.buffer, {
          filename: req.file.originalname,
          contentType: req.file.mimetype,
        });
      }

      aiResponse = await axios.post(AI_SERVICE_URL, formData, {
        headers: { ...formData.getHeaders() },
      });
      evidenceBuffer = req.file.buffer;
    } else {
      // Case 2: JSON/Image activation
      aiResponse = await axios.post(AI_SERVICE_URL, req.body);
      evidenceBuffer = Buffer.from(JSON.stringify(req.body));
    }

    const aiVerdict = aiResponse.data.verdict;
    console.log(`✅ AI Verdict: ${aiVerdict}`);

    if (aiVerdict.toLowerCase().includes('alert')) {
      await sendSmsAlert(aiVerdict);
    }

    // --- Log Evidence ---
    const evidenceHash = crypto.createHash('sha256').update(evidenceBuffer).digest('hex');
    console.log(`Generated SHA-256: ${evidenceHash}`);

    await prisma.alertEvent.create({
      data: { type: req.file ? 'MEDIA_SIGNAL' : 'IMAGE_SIGNAL', verdict: aiVerdict },
    });

    await logEvidenceOnBlockchain(evidenceHash);

    res.json({ message: `AI Verdict: ${aiVerdict}` });
  } catch (error) {
    console.error('❌ ERROR in /api/activate:', error);
    res.status(500).json({ message: 'Internal Server Error' });
  }
});

// --- Lightweight Endpoint: Live Audio ---
app.post('/api/analyze-live-audio', upload.single('audio_file'), async (req: Request, res: Response) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: "No audio file received." });
    }

    const formData = new FormData();
    formData.append('audio_file', req.file.buffer, {
      filename: 'recording.wav',
      contentType: req.file.mimetype,
    });

    const aiResponse = await axios.post(AI_SERVICE_URL, formData, {
      headers: { ...formData.getHeaders() },
    });

    res.json({ verdict: aiResponse.data.verdict });
  } catch (error) {
    console.error('❌ ERROR in /api/analyze-live-audio:', error);
    res.status(500).json({ message: 'Error analyzing audio.' });
  }
});

app.listen(PORT, () => {
  console.log(`✅ Backend running at http://localhost:${PORT}`);
});
