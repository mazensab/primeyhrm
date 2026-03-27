import "dotenv/config"

import cors from "cors"
import express from "express"
import fs from "node:fs"
import fsp from "node:fs/promises"
import path from "node:path"
import { fileURLToPath } from "node:url"

import pino from "pino"
import QRCode from "qrcode"
import makeWASocket, {
  Browsers,
  DisconnectReason,
  fetchLatestBaileysVersion,
  useMultiFileAuthState,
} from "@whiskeysockets/baileys"
import { Boom } from "@hapi/boom"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const PORT = Number(process.env.PORT || 3100)
const HOST = process.env.HOST || "127.0.0.1"
const GATEWAY_TOKEN = (process.env.GATEWAY_TOKEN || "").trim()
const LOG_LEVEL = process.env.LOG_LEVEL || "info"
const SESSIONS_DIR = path.resolve(__dirname, process.env.SESSIONS_DIR || "./sessions")
const CORS_ORIGIN = (process.env.CORS_ORIGIN || "").trim()

// ============================================================
// 🔗 Backend Webhook Bridge Config
// ============================================================
// ملاحظة:
// هذا هو الجسر الذي يربط Baileys Gateway مع Django backend.
// نرسل إليه كل:
// - الرسائل الواردة Inbound Messages
// - تحديثات الرسائل Message Status Updates
//
// مثال:
// WHATSAPP_BACKEND_WEBHOOK_URL=https://your-domain.com/api/system/whatsapp/webhook/receive/
// WHATSAPP_BACKEND_WEBHOOK_TOKEN=your_internal_shared_secret
// WHATSAPP_BACKEND_WEBHOOK_TIMEOUT_MS=10000
// ============================================================

const BACKEND_WEBHOOK_URL = (
  process.env.WHATSAPP_BACKEND_WEBHOOK_URL ||
  process.env.BACKEND_WEBHOOK_URL ||
  ""
).trim()

const BACKEND_WEBHOOK_TOKEN = (
  process.env.WHATSAPP_BACKEND_WEBHOOK_TOKEN ||
  process.env.BACKEND_WEBHOOK_TOKEN ||
  ""
).trim()

const BACKEND_WEBHOOK_TIMEOUT_MS = Number(
  process.env.WHATSAPP_BACKEND_WEBHOOK_TIMEOUT_MS ||
  process.env.BACKEND_WEBHOOK_TIMEOUT_MS ||
  10000
)

const logger = pino({
  level: LOG_LEVEL,
})

const app = express()
app.use(express.json({ limit: "10mb" }))
app.use(
  cors({
    origin: CORS_ORIGIN ? [CORS_ORIGIN] : true,
    credentials: true,
  })
)

const sessions = new Map()

function safeSessionName(value) {
  const raw = String(value || "primey-system-session").trim()
  return raw.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 100) || "primey-system-session"
}

function digitsOnly(value) {
  return String(value || "").replace(/\D/g, "")
}

function toWhatsAppJid(phone) {
  const normalized = digitsOnly(phone)
  return normalized ? `${normalized}@s.whatsapp.net` : ""
}

function nowIso() {
  return new Date().toISOString()
}

function ensureDirSync(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true })
  }
}

async function rmDirIfExists(dirPath) {
  try {
    await fsp.rm(dirPath, { recursive: true, force: true })
  } catch (error) {
    logger.warn({ err: error, dirPath }, "Failed to remove directory")
  }
}

function getSessionDir(sessionName) {
  return path.join(SESSIONS_DIR, safeSessionName(sessionName))
}

function hasStoredSessionFiles(sessionNameOrDir) {
  try {
    const dirPath = sessionNameOrDir.includes(path.sep)
      ? sessionNameOrDir
      : getSessionDir(sessionNameOrDir)

    if (!fs.existsSync(dirPath)) {
      return false
    }

    const entries = fs.readdirSync(dirPath, { withFileTypes: true })
    return entries.some((entry) => entry.isFile() || entry.isDirectory())
  } catch {
    return false
  }
}

function baseState(sessionName) {
  return {
    sessionName: safeSessionName(sessionName),
    sessionDir: getSessionDir(sessionName),
    sock: null,
    saveCreds: null,
    status: "disconnected",
    connected: false,
    connectedPhone: "",
    deviceLabel: "",
    qrCode: "",
    pairingCode: "",
    lastConnectedAt: "",
    lastError: "",
    isStarting: false,
    lastMode: "qr",
    lastPairingPhone: "",
    restartTimer: null,
  }
}

function getOrCreateState(sessionName) {
  const key = safeSessionName(sessionName)

  if (!sessions.has(key)) {
    sessions.set(key, baseState(key))
  }

  return sessions.get(key)
}

function serializeState(state, extra = {}) {
  return {
    success: extra.success ?? true,
    status_code: extra.statusCode ?? 200,
    message: extra.message ?? "OK",
    session_name: state.sessionName,
    session_status: state.status || "disconnected",
    connected: Boolean(state.connected),
    connected_phone: state.connectedPhone || "",
    device_label: state.deviceLabel || "",
    qr_code: state.qrCode || "",
    pairing_code: state.pairingCode || "",
    last_connected_at: state.lastConnectedAt || "",
  }
}

function getDisconnectCode(lastDisconnect) {
  try {
    const error = lastDisconnect?.error
    if (error instanceof Boom) {
      return error.output?.statusCode
    }
    const wrapped = new Boom(error)
    return wrapped.output?.statusCode
  } catch {
    return undefined
  }
}

function clearRestartTimer(state) {
  if (state.restartTimer) {
    clearTimeout(state.restartTimer)
    state.restartTimer = null
  }
}

function resetEphemeralSessionState(state) {
  state.connected = false
  state.connectedPhone = ""
  state.deviceLabel = ""
  state.qrCode = ""
  state.pairingCode = ""
}

function authMiddleware(req, res, next) {
  if (!GATEWAY_TOKEN) {
    return next()
  }

  const authHeader = String(req.headers.authorization || "")
  const expected = `Bearer ${GATEWAY_TOKEN}`

  if (authHeader !== expected) {
    return res.status(401).json({
      success: false,
      status_code: 401,
      message: "Unauthorized gateway token",
    })
  }

  next()
}

async function waitFor(predicate, timeoutMs = 15000, intervalMs = 300) {
  const started = Date.now()

  while (Date.now() - started < timeoutMs) {
    const result = await predicate()
    if (result) {
      return result
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }

  return null
}

async function waitForSessionOutcome(state, timeoutMs = 15000) {
  return waitFor(async () => {
    if (state.connected) return "connected"
    if (state.status === "qr_pending" && state.qrCode) return "qr"
    if (state.status === "pair_pending" && state.pairingCode) return "pairing"
    if (state.status === "failed") return "failed"

    if (!state.isStarting && !state.sock && !hasStoredSessionFiles(state.sessionDir)) {
      return "disconnected"
    }

    return null
  }, timeoutMs, 250)
}

async function requestPairingCodeSafe(sock, normalizedPhone) {
  if (typeof sock.requestPairingCode !== "function") {
    throw new Error("requestPairingCode is not available in current Baileys build")
  }

  const code = await sock.requestPairingCode(normalizedPhone)
  if (!code) {
    throw new Error("Failed to generate pairing code")
  }

  return code
}

// ============================================================
// 🔧 Inbound / Webhook Bridge Helpers
// ============================================================

function isGroupJid(jid) {
  return String(jid || "").endsWith("@g.us")
}

function isBroadcastJid(jid) {
  return String(jid || "").includes("@broadcast")
}

function isStatusJid(jid) {
  return String(jid || "").includes("status@broadcast")
}

function normalizePhoneFromJid(jid) {
  const raw = String(jid || "").split(":")[0].split("@")[0]
  const digits = digitsOnly(raw)
  return digits || ""
}

function firstNonEmpty(...values) {
  for (const value of values) {
    if (value === null || value === undefined) continue
    const text = String(value).trim()
    if (text) return text
  }
  return ""
}

function unixToIso(value) {
  try {
    const numeric = Number(value || 0)
    if (!numeric) return ""
    return new Date(numeric * 1000).toISOString()
  } catch {
    return ""
  }
}

function getMessageType(message) {
  if (!message || typeof message !== "object") {
    return "unknown"
  }

  const keys = Object.keys(message)
  if (!keys.length) {
    return "unknown"
  }

  if (message.conversation) return "conversation"
  if (message.extendedTextMessage) return "extendedTextMessage"
  if (message.imageMessage) return "imageMessage"
  if (message.videoMessage) return "videoMessage"
  if (message.audioMessage) return "audioMessage"
  if (message.documentMessage) return "documentMessage"
  if (message.stickerMessage) return "stickerMessage"
  if (message.locationMessage) return "locationMessage"
  if (message.contactMessage) return "contactMessage"
  if (message.contactsArrayMessage) return "contactsArrayMessage"
  if (message.buttonsResponseMessage) return "buttonsResponseMessage"
  if (message.listResponseMessage) return "listResponseMessage"
  if (message.templateButtonReplyMessage) return "templateButtonReplyMessage"
  if (message.ephemeralMessage) return "ephemeralMessage"
  if (message.viewOnceMessage) return "viewOnceMessage"
  if (message.viewOnceMessageV2) return "viewOnceMessageV2"
  if (message.protocolMessage) return "protocolMessage"
  return keys[0] || "unknown"
}

function unwrapMessage(message) {
  let current = message || null

  for (let i = 0; i < 5; i += 1) {
    if (!current || typeof current !== "object") break

    if (current.ephemeralMessage?.message) {
      current = current.ephemeralMessage.message
      continue
    }

    if (current.viewOnceMessage?.message) {
      current = current.viewOnceMessage.message
      continue
    }

    if (current.viewOnceMessageV2?.message) {
      current = current.viewOnceMessageV2.message
      continue
    }

    if (current.documentWithCaptionMessage?.message) {
      current = current.documentWithCaptionMessage.message
      continue
    }

    break
  }

  return current || {}
}

function extractTextFromMessage(message) {
  const msg = unwrapMessage(message)

  return firstNonEmpty(
    msg?.conversation,
    msg?.extendedTextMessage?.text,
    msg?.imageMessage?.caption,
    msg?.videoMessage?.caption,
    msg?.documentMessage?.caption,
    msg?.buttonsResponseMessage?.selectedDisplayText,
    msg?.listResponseMessage?.title,
    msg?.templateButtonReplyMessage?.selectedDisplayText,
    msg?.buttonsResponseMessage?.selectedButtonId,
    msg?.listResponseMessage?.singleSelectReply?.selectedRowId,
    ""
  )
}

function extractMediaMeta(message) {
  const msg = unwrapMessage(message)

  if (msg?.imageMessage) {
    return {
      media_type: "image",
      mimetype: firstNonEmpty(msg.imageMessage.mimetype),
      caption: firstNonEmpty(msg.imageMessage.caption),
      file_name: "",
    }
  }

  if (msg?.videoMessage) {
    return {
      media_type: "video",
      mimetype: firstNonEmpty(msg.videoMessage.mimetype),
      caption: firstNonEmpty(msg.videoMessage.caption),
      file_name: "",
    }
  }

  if (msg?.audioMessage) {
    return {
      media_type: "audio",
      mimetype: firstNonEmpty(msg.audioMessage.mimetype),
      caption: "",
      file_name: "",
    }
  }

  if (msg?.documentMessage) {
    return {
      media_type: "document",
      mimetype: firstNonEmpty(msg.documentMessage.mimetype),
      caption: firstNonEmpty(msg.documentMessage.caption),
      file_name: firstNonEmpty(msg.documentMessage.fileName),
    }
  }

  if (msg?.stickerMessage) {
    return {
      media_type: "sticker",
      mimetype: firstNonEmpty(msg.stickerMessage.mimetype),
      caption: "",
      file_name: "",
    }
  }

  return {
    media_type: "",
    mimetype: "",
    caption: "",
    file_name: "",
  }
}

function serializeInboundMessage(item, sessionName) {
  const key = item?.key || {}
  const message = item?.message || {}
  const normalizedMessage = unwrapMessage(message)
  const remoteJid = firstNonEmpty(key.remoteJid)
  const participantJid = firstNonEmpty(key.participant)
  const senderJid = firstNonEmpty(
    key.fromMe ? "" : participantJid,
    key.fromMe ? "" : remoteJid,
    remoteJid
  )
  const senderPhone = normalizePhoneFromJid(senderJid)
  const remotePhone = normalizePhoneFromJid(remoteJid)
  const text = extractTextFromMessage(message)
  const media = extractMediaMeta(message)

  return {
    session_name: sessionName,
    source: "baileys_gateway",
    provider: "whatsapp_web_session",
    event_type: "inbound_message",
    message_id: firstNonEmpty(key.id),
    remote_jid: remoteJid,
    participant_jid: participantJid,
    sender_jid: senderJid,
    sender_phone: senderPhone,
    remote_phone: remotePhone,
    push_name: firstNonEmpty(item?.pushName),
    from_me: Boolean(key.fromMe),
    is_group: isGroupJid(remoteJid),
    is_broadcast: isBroadcastJid(remoteJid),
    is_status: isStatusJid(remoteJid),
    message_type: getMessageType(normalizedMessage),
    text,
    timestamp: Number(item?.messageTimestamp || 0) || 0,
    timestamp_iso: unixToIso(item?.messageTimestamp),
    media_type: media.media_type,
    mime_type: media.mimetype,
    caption: media.caption,
    file_name: media.file_name,
    raw_message: message,
    raw_key: key,
    raw_payload: item,
  }
}

function serializeMessageUpdate(item, sessionName) {
  const key = item?.key || {}
  const update = item?.update || {}

  return {
    session_name: sessionName,
    source: "baileys_gateway",
    provider: "whatsapp_web_session",
    event_type: "message_update",
    message_id: firstNonEmpty(key.id),
    remote_jid: firstNonEmpty(key.remoteJid),
    participant_jid: firstNonEmpty(key.participant),
    from_me: Boolean(key.fromMe),
    update,
    raw_payload: item,
  }
}

async function postToBackendWebhook(payload) {
  if (!BACKEND_WEBHOOK_URL) {
    logger.warn(
      { payload_event_type: payload?.event_type || payload?.event || "unknown" },
      "WHATSAPP_BACKEND_WEBHOOK_URL is not configured; skipping backend webhook push"
    )
    return {
      success: false,
      skipped: true,
      status_code: 0,
      error_message: "Missing WHATSAPP_BACKEND_WEBHOOK_URL",
    }
  }

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), BACKEND_WEBHOOK_TIMEOUT_MS)

  try {
    const headers = {
      "Content-Type": "application/json",
      "Accept": "application/json",
    }

    if (BACKEND_WEBHOOK_TOKEN) {
      headers["Authorization"] = `Bearer ${BACKEND_WEBHOOK_TOKEN}`
      headers["X-Primey-Webhook-Token"] = BACKEND_WEBHOOK_TOKEN
    }

    const response = await fetch(BACKEND_WEBHOOK_URL, {
      method: "POST",
      headers,
      body: JSON.stringify(payload || {}),
      signal: controller.signal,
    })

    const rawText = await response.text()
    let parsed = null

    try {
      parsed = rawText ? JSON.parse(rawText) : null
    } catch {
      parsed = null
    }

    if (!response.ok) {
      logger.warn(
        {
          status: response.status,
          webhook_url: BACKEND_WEBHOOK_URL,
          response_body: rawText,
          payload_event_type: payload?.event_type || payload?.event || "unknown",
        },
        "Backend webhook returned non-OK response"
      )
    }

    return {
      success: response.ok,
      skipped: false,
      status_code: response.status,
      response_data: parsed,
      response_text: rawText,
    }
  } catch (error) {
    logger.error(
      {
        err: error,
        webhook_url: BACKEND_WEBHOOK_URL,
        payload_event_type: payload?.event_type || payload?.event || "unknown",
      },
      "Failed to push event to backend webhook"
    )

    return {
      success: false,
      skipped: false,
      status_code: 0,
      error_message: String(error?.message || error),
    }
  } finally {
    clearTimeout(timeout)
  }
}

async function emitInboundMessagesToBackend({ sessionName, upsertType, messages }) {
  const safeMessages = Array.isArray(messages) ? messages : []
  if (!safeMessages.length) return

  const normalizedMessages = safeMessages
    .map((item) => serializeInboundMessage(item, sessionName))
    .filter((item) => item && item.message_id)

  if (!normalizedMessages.length) return

  const payload = {
    provider: "whatsapp_web_session",
    source: "baileys_gateway",
    event: "messages.upsert",
    event_type: "messages_upsert",
    scope_type: "SYSTEM",
    session_name: sessionName,
    upsert_type: firstNonEmpty(upsertType, "notify"),
    received_at: nowIso(),
    messages: normalizedMessages,
  }

  const result = await postToBackendWebhook(payload)

  logger.info(
    {
      session: sessionName,
      count: normalizedMessages.length,
      upsert_type: payload.upsert_type,
      webhook_success: result.success,
      webhook_status_code: result.status_code,
    },
    "Inbound WhatsApp messages forwarded to backend webhook"
  )
}

async function emitMessageUpdatesToBackend({ sessionName, updates }) {
  const safeUpdates = Array.isArray(updates) ? updates : []
  if (!safeUpdates.length) return

  const serializedUpdates = safeUpdates
    .map((item) => serializeMessageUpdate(item, sessionName))
    .filter((item) => item && item.message_id)

  if (!serializedUpdates.length) return

  const payload = {
    provider: "whatsapp_web_session",
    source: "baileys_gateway",
    event: "messages.update",
    event_type: "messages_update",
    scope_type: "SYSTEM",
    session_name: sessionName,
    received_at: nowIso(),
    message_updates: serializedUpdates,
  }

  const result = await postToBackendWebhook(payload)

  logger.info(
    {
      session: sessionName,
      count: serializedUpdates.length,
      webhook_success: result.success,
      webhook_status_code: result.status_code,
    },
    "WhatsApp message updates forwarded to backend webhook"
  )
}

// ============================================================
// 🏗 Socket Builder
// ============================================================

async function buildSocket(state, { mode = "qr", phoneNumber = "" } = {}) {
  if (state.isStarting) {
    await waitForSessionOutcome(state, 12000)
    return state
  }

  if (state.sock && (state.connected || state.status === "qr_pending" || state.status === "pair_pending")) {
    return state
  }

  state.isStarting = true
  state.lastMode = mode
  state.lastPairingPhone = phoneNumber || ""
  state.lastError = ""

  ensureDirSync(SESSIONS_DIR)
  ensureDirSync(state.sessionDir)
  clearRestartTimer(state)

  try {
    const { state: authState, saveCreds } = await useMultiFileAuthState(state.sessionDir)
    const { version } = await fetchLatestBaileysVersion()
    const hasStoredAuth = Boolean(authState?.creds?.registered) || hasStoredSessionFiles(state.sessionDir)

    if (!state.connected) {
      state.status = hasStoredAuth ? "restoring" : mode === "pairing_code" ? "pair_pending" : "starting"
    }

    const sock = makeWASocket({
      auth: authState,
      version,
      logger,
      printQRInTerminal: false,
      browser: Browsers.windows("Primey HR Cloud"),
      markOnlineOnConnect: false,
      syncFullHistory: false,
      defaultQueryTimeoutMs: 60000,
      generateHighQualityLinkPreview: false,
    })

    state.sock = sock
    state.saveCreds = saveCreds

    sock.ev.on("creds.update", saveCreds)

    // --------------------------------------------------------
    // 📥 Inbound Messages Listener
    // --------------------------------------------------------
    sock.ev.on("messages.upsert", async (event) => {
      try {
        const upsertType = firstNonEmpty(event?.type, "notify")
        const messages = Array.isArray(event?.messages) ? event.messages : []

        if (!messages.length) {
          return
        }

        const filtered = messages.filter((item) => {
          const key = item?.key || {}
          const remoteJid = firstNonEmpty(key.remoteJid)

          // نتجاهل رسائل النظام والحالات والبث
          if (key.fromMe) {
            return false
          }

          if (!remoteJid) {
            return false
          }

          if (isStatusJid(remoteJid)) {
            return false
          }

          return true
        })

        if (!filtered.length) {
          return
        }

        await emitInboundMessagesToBackend({
          sessionName: state.sessionName,
          upsertType,
          messages: filtered,
        })
      } catch (error) {
        logger.error(
          { err: error, session: state.sessionName },
          "messages.upsert handler failed"
        )
      }
    })

    // --------------------------------------------------------
    // 🔄 Message Updates Listener
    // --------------------------------------------------------
    sock.ev.on("messages.update", async (updates) => {
      try {
        if (!Array.isArray(updates) || !updates.length) {
          return
        }

        await emitMessageUpdatesToBackend({
          sessionName: state.sessionName,
          updates,
        })
      } catch (error) {
        logger.error(
          { err: error, session: state.sessionName },
          "messages.update handler failed"
        )
      }
    })

    sock.ev.on("connection.update", async (update) => {
      try {
        const { connection, lastDisconnect, qr } = update

        if (qr) {
          state.qrCode = await QRCode.toDataURL(qr)
          state.pairingCode = ""
          state.status = "qr_pending"
          state.connected = false
        }

        if (connection === "open") {
          state.connected = true
          state.status = "connected"
          state.qrCode = ""
          state.pairingCode = ""
          state.lastError = ""
          state.lastConnectedAt = nowIso()
          state.connectedPhone = String(sock.user?.id || "").split(":")[0] || ""
          state.deviceLabel = "Primey HR Cloud"
          logger.info({ session: state.sessionName }, "WhatsApp session connected")
        }

        if (connection === "close") {
          state.connected = false

          const code = getDisconnectCode(lastDisconnect)
          const shouldLogout = code === DisconnectReason.loggedOut
          const shouldRestart =
            code === DisconnectReason.restartRequired ||
            code === 515 ||
            (!shouldLogout && code !== DisconnectReason.badSession)

          logger.warn(
            { session: state.sessionName, code },
            "WhatsApp session closed"
          )

          state.sock = null

          if (shouldLogout) {
            state.status = "disconnected"
            state.qrCode = ""
            state.pairingCode = ""
            state.connectedPhone = ""
            state.deviceLabel = ""
            state.lastError = "Session logged out"
            return
          }

          if (shouldRestart) {
            state.status =
              state.lastMode === "pairing_code" ? "pair_pending" : "restoring"

            clearRestartTimer(state)
            state.restartTimer = setTimeout(() => {
              buildSocket(state, {
                mode: state.lastMode || "qr",
                phoneNumber: state.lastPairingPhone || "",
              }).catch((error) => {
                state.status = "failed"
                state.lastError = String(error?.message || error)
                logger.error(
                  { err: error, session: state.sessionName },
                  "Failed to restart WhatsApp session"
                )
              })
            }, 1500)
          }
        }
      } catch (error) {
        state.status = "failed"
        state.lastError = String(error?.message || error)
        logger.error(
          { err: error, session: state.sessionName },
          "connection.update handler failed"
        )
      }
    })

    if (mode === "pairing_code" && !authState.creds?.registered) {
      const normalizedPhone = digitsOnly(phoneNumber)
      if (!normalizedPhone) {
        throw new Error("phone_number is required for pairing code")
      }

      const pairingCode = await requestPairingCodeSafe(sock, normalizedPhone)

      state.pairingCode = pairingCode
      state.qrCode = ""
      state.status = "pair_pending"
    }

    return state
  } catch (error) {
    state.sock = null
    state.status = "failed"
    state.lastError = String(error?.message || error)
    logger.error(
      { err: error, session: state.sessionName },
      "Failed to build WhatsApp socket"
    )
    return state
  } finally {
    state.isStarting = false
  }
}

async function ensureSession(sessionName, options = {}) {
  const state = getOrCreateState(sessionName)

  if (state.isStarting) {
    await waitForSessionOutcome(state, 12000)
    return state
  }

  if (state.sock && (state.connected || state.status === "qr_pending" || state.status === "pair_pending")) {
    return state
  }

  return buildSocket(state, options)
}

async function restoreSessionIfExists(sessionName, options = {}) {
  const state = getOrCreateState(sessionName)

  if (!hasStoredSessionFiles(state.sessionDir)) {
    return state
  }

  if (state.connected) {
    return state
  }

  await ensureSession(sessionName, options)
  await waitForSessionOutcome(state, 12000)

  return state
}

async function bootstrapStoredSessions() {
  ensureDirSync(SESSIONS_DIR)

  let entries = []
  try {
    entries = await fsp.readdir(SESSIONS_DIR, { withFileTypes: true })
  } catch (error) {
    logger.error({ err: error }, "Failed to read sessions directory during bootstrap")
    return
  }

  const sessionDirs = entries
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)

  if (!sessionDirs.length) {
    logger.info("No stored WhatsApp sessions found during bootstrap")
    return
  }

  logger.info({ sessions: sessionDirs }, "Bootstrapping stored WhatsApp sessions")

  for (const sessionName of sessionDirs) {
    const state = getOrCreateState(sessionName)
    state.status = "restoring"

    restoreSessionIfExists(sessionName, { mode: "qr" }).catch((error) => {
      state.status = "failed"
      state.lastError = String(error?.message || error)
      logger.error(
        { err: error, session: sessionName },
        "Failed to restore stored WhatsApp session"
      )
    })
  }
}

app.get("/health", (_req, res) => {
  res.json({
    success: true,
    status_code: 200,
    message: "Gateway is running",
    uptime_seconds: Math.floor(process.uptime()),
    sessions_count: sessions.size,
    backend_webhook_enabled: Boolean(BACKEND_WEBHOOK_URL),
  })
})

app.post("/session/create-qr/", authMiddleware, async (req, res) => {
  try {
    const sessionName = safeSessionName(req.body?.session_name)
    const state = getOrCreateState(sessionName)

    if (state.isStarting) {
      await waitForSessionOutcome(state, 12000)
    } else if (!state.connected && hasStoredSessionFiles(state.sessionDir)) {
      state.status = "restoring"
      await restoreSessionIfExists(sessionName, { mode: "qr" })
    } else {
      await ensureSession(sessionName, { mode: "qr" })
    }

    const outcome = await waitForSessionOutcome(state, 15000)

    if (!outcome) {
      return res.status(504).json({
        ...serializeState(state, {
          success: false,
          statusCode: 504,
          message: "Timed out while waiting for QR generation or session recovery",
        }),
      })
    }

    if (state.status === "failed") {
      return res.status(400).json({
        ...serializeState(state, {
          success: false,
          statusCode: 400,
          message: state.lastError || "Failed to create or recover QR session",
        }),
      })
    }

    return res.json(
      serializeState(state, {
        success: true,
        statusCode: 200,
        message:
          state.connected
            ? "Session already connected"
            : state.qrCode
              ? "QR session created successfully"
              : "Session recovered successfully",
      })
    )
  } catch (error) {
    return res.status(500).json({
      success: false,
      status_code: 500,
      message: String(error?.message || error || "Failed to create QR session"),
    })
  }
})

app.post("/session/create-pairing-code/", authMiddleware, async (req, res) => {
  try {
    const sessionName = safeSessionName(req.body?.session_name)
    const phoneNumber = digitsOnly(req.body?.phone_number)

    if (!phoneNumber) {
      return res.status(400).json({
        success: false,
        status_code: 400,
        session_name: sessionName,
        session_status: "failed",
        connected: false,
        connected_phone: "",
        device_label: "",
        qr_code: "",
        pairing_code: "",
        last_connected_at: "",
        message: "phone_number is required",
      })
    }

    const state = getOrCreateState(sessionName)

    if (state.isStarting) {
      await waitForSessionOutcome(state, 12000)
    }

    if (!state.connected && hasStoredSessionFiles(state.sessionDir)) {
      state.status = "restoring"
      await restoreSessionIfExists(sessionName, {
        mode: "pairing_code",
        phoneNumber,
      })
    } else {
      await ensureSession(sessionName, {
        mode: "pairing_code",
        phoneNumber,
      })
    }

    const outcome = await waitForSessionOutcome(state, 15000)

    if (!outcome) {
      return res.status(504).json({
        ...serializeState(state, {
          success: false,
          statusCode: 504,
          message: "Timed out while waiting for pairing code generation or session recovery",
        }),
      })
    }

    if (state.status === "failed") {
      return res.status(400).json({
        ...serializeState(state, {
          success: false,
          statusCode: 400,
          message: state.lastError || "Failed to create pairing code",
        }),
      })
    }

    return res.json(
      serializeState(state, {
        success: true,
        statusCode: 200,
        message: state.connected
          ? "Session already connected"
          : state.pairingCode
            ? "Pairing code created successfully"
            : "Session recovered successfully",
      })
    )
  } catch (error) {
    return res.status(500).json({
      success: false,
      status_code: 500,
      message: String(error?.message || error || "Failed to create pairing code"),
    })
  }
})

app.post("/session/status/", authMiddleware, async (req, res) => {
  const sessionName = safeSessionName(req.body?.session_name)
  const state = getOrCreateState(sessionName)
  const hasSessionDir = hasStoredSessionFiles(state.sessionDir)

  try {
    if (state.isStarting) {
      await waitForSessionOutcome(state, 12000)
    } else if (!state.sock && hasSessionDir) {
      state.status = "restoring"
      await restoreSessionIfExists(sessionName, { mode: "qr" })
    }

    const outcome = await waitForSessionOutcome(state, 8000)

    return res.json(
      serializeState(state, {
        success: true,
        statusCode: 200,
        message:
          state.lastError ||
          (outcome === "connected"
            ? "Session status loaded successfully"
            : hasSessionDir
              ? "Session status loaded after recovery attempt"
              : "Session status loaded successfully"),
      })
    )
  } catch (error) {
    state.status = "failed"
    state.lastError = String(error?.message || error)

    return res.json(
      serializeState(state, {
        success: true,
        statusCode: 200,
        message: state.lastError || "Session status loaded with recovery error",
      })
    )
  }
})

app.post("/session/disconnect/", authMiddleware, async (req, res) => {
  const sessionName = safeSessionName(req.body?.session_name)
  const clearAuth = Boolean(req.body?.clear_auth ?? true)
  const state = getOrCreateState(sessionName)

  clearRestartTimer(state)

  try {
    if (state.sock?.logout) {
      await state.sock.logout()
    }
  } catch (error) {
    logger.warn({ err: error, session: sessionName }, "logout failed")
  }

  try {
    state.sock?.end?.(undefined)
  } catch {
    // ignore
  }

  state.sock = null
  state.saveCreds = null
  state.status = "disconnected"
  state.lastError = ""
  resetEphemeralSessionState(state)

  if (clearAuth) {
    await rmDirIfExists(state.sessionDir)
  }

  return res.json(
    serializeState(state, {
      success: true,
      statusCode: 200,
      message: "Session disconnected successfully",
    })
  )
})

app.post("/messages/send-text/", authMiddleware, async (req, res) => {
  const sessionName = safeSessionName(req.body?.session_name)
  const toPhone = digitsOnly(req.body?.to_phone)
  const body = String(req.body?.body || "").trim()

  if (!toPhone || !body) {
    return res.status(400).json({
      success: false,
      status_code: 400,
      provider_status: "validation_failed",
      message: "Missing to_phone or body",
    })
  }

  const state = getOrCreateState(sessionName)

  if (!state.connected && hasStoredSessionFiles(state.sessionDir)) {
    try {
      await restoreSessionIfExists(sessionName, { mode: "qr" })
    } catch (error) {
      logger.warn(
        { err: error, session: sessionName },
        "Failed to restore session before sending text message"
      )
    }
  }

  if (!state.sock || !state.connected) {
    return res.status(409).json({
      success: false,
      status_code: 409,
      provider_status: "session_not_connected",
      message: "WhatsApp session is not connected",
      session_status: state.status || "disconnected",
    })
  }

  try {
    const jid = toWhatsAppJid(toPhone)
    const response = await state.sock.sendMessage(jid, { text: body })

    return res.json({
      success: true,
      status_code: 200,
      provider_status: "accepted",
      message: "Text message sent successfully",
      external_message_id: response?.key?.id || "",
      session_status: state.status,
      connected: state.connected,
      connected_phone: state.connectedPhone,
      device_label: state.deviceLabel,
      last_connected_at: state.lastConnectedAt,
    })
  } catch (error) {
    return res.status(500).json({
      success: false,
      status_code: 500,
      provider_status: "send_failed",
      message: String(error?.message || error),
      session_status: state.status || "disconnected",
    })
  }
})

app.post("/messages/send-document/", authMiddleware, async (req, res) => {
  const sessionName = safeSessionName(req.body?.session_name)
  const toPhone = digitsOnly(req.body?.to_phone)
  const documentUrl = String(req.body?.document_url || "").trim()
  const caption = String(req.body?.caption || "").trim()
  const filename = String(req.body?.filename || "document").trim()
  const mimeType = String(req.body?.mime_type || "application/octet-stream").trim()

  if (!toPhone || !documentUrl) {
    return res.status(400).json({
      success: false,
      status_code: 400,
      provider_status: "validation_failed",
      message: "Missing to_phone or document_url",
    })
  }

  const state = getOrCreateState(sessionName)

  if (!state.connected && hasStoredSessionFiles(state.sessionDir)) {
    try {
      await restoreSessionIfExists(sessionName, { mode: "qr" })
    } catch (error) {
      logger.warn(
        { err: error, session: sessionName },
        "Failed to restore session before sending document message"
      )
    }
  }

  if (!state.sock || !state.connected) {
    return res.status(409).json({
      success: false,
      status_code: 409,
      provider_status: "session_not_connected",
      message: "WhatsApp session is not connected",
      session_status: state.status || "disconnected",
    })
  }

  try {
    const jid = toWhatsAppJid(toPhone)
    const response = await state.sock.sendMessage(jid, {
      document: { url: documentUrl },
      mimetype: mimeType,
      fileName: filename,
      caption,
    })

    return res.json({
      success: true,
      status_code: 200,
      provider_status: "accepted",
      message: "Document message sent successfully",
      external_message_id: response?.key?.id || "",
      session_status: state.status,
      connected: state.connected,
      connected_phone: state.connectedPhone,
      device_label: state.deviceLabel,
      last_connected_at: state.lastConnectedAt,
    })
  } catch (error) {
    return res.status(500).json({
      success: false,
      status_code: 500,
      provider_status: "send_failed",
      message: String(error?.message || error),
      session_status: state.status || "disconnected",
    })
  }
})

app.use((error, _req, res, _next) => {
  logger.error({ err: error }, "Unhandled gateway error")

  return res.status(500).json({
    success: false,
    status_code: 500,
    message: String(error?.message || error || "Internal gateway error"),
  })
})

async function bootstrap() {
  ensureDirSync(SESSIONS_DIR)

  app.listen(PORT, HOST, () => {
    logger.info(
      {
        host: HOST,
        port: PORT,
        sessionsDir: SESSIONS_DIR,
        backendWebhookEnabled: Boolean(BACKEND_WEBHOOK_URL),
        backendWebhookUrl: BACKEND_WEBHOOK_URL || null,
      },
      "Primey WhatsApp Session Gateway started"
    )
  })

  await bootstrapStoredSessions()
}

bootstrap().catch((error) => {
  logger.error({ err: error }, "Failed to start gateway")
  process.exit(1)
})