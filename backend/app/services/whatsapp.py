"""
WhatsApp Service — Send messages via WhatsApp Business API.

Supports:
  ✓ Text messages
  ✓ Image + caption
  ✓ Video + caption  
  ✓ Document (PDF) + caption
  ✓ Bulk send to multiple recipients

Uses Ultra Message API format (easily adaptable to Twilio/360dialog/WATI).
"""

from __future__ import annotations

import httpx
from loguru import logger
from app.config import get_settings


settings = get_settings()


class WhatsAppService:
    """WhatsApp Business API client."""

    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.token = settings.WHATSAPP_API_TOKEN
        self.instance_id = settings.WHATSAPP_INSTANCE_ID
        self.enabled = settings.WHATSAPP_ENABLED

    def _format_phone(self, phone: str) -> str:
        """Format phone to international format (966XXXXXXXXX)."""
        phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
        if phone.startswith("05"):
            phone = "966" + phone[1:]
        elif phone.startswith("5") and len(phone) == 9:
            phone = "966" + phone
        return phone

    async def send_text(self, phone: str, message: str) -> dict:
        """Send a text message."""
        if not self.enabled:
            logger.info(f"[WhatsApp:Disabled] Would send to {phone}: {message[:80]}...")
            return {"success": True, "simulated": True}

        phone = self._format_phone(phone)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.api_url}/messages/chat",
                    data={
                        "token": self.token,
                        "to": phone,
                        "body": message,
                    },
                )
                result = resp.json()
                logger.info(f"[WhatsApp] Text sent to {phone}: {result}")
                # UltraMsg returns {"sent": "true", ...} on success
                success = str(result.get("sent", "")).lower() == "true"
                error_msg = result.get("error", "") or result.get("message", "")
                return {"success": success, "response": result, "error": error_msg}
        except Exception as e:
            logger.error(f"[WhatsApp] Error sending text to {phone}: {e}")
            return {"success": False, "error": str(e)}

    async def send_image(self, phone: str, image_url: str, caption: str = "") -> dict:
        """Send an image with optional caption."""
        if not self.enabled:
            logger.info(f"[WhatsApp:Disabled] Would send image to {phone}")
            return {"success": True, "simulated": True}

        phone = self._format_phone(phone)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.api_url}/messages/image",
                    data={
                        "token": self.token,
                        "to": phone,
                        "image": image_url,
                        "caption": caption,
                    },
                )
                result = resp.json()
                success = str(result.get("sent", "")).lower() == "true"
                error_msg = result.get("error", "") or result.get("message", "")
                return {"success": success, "response": result, "error": error_msg}
        except Exception as e:
            logger.error(f"[WhatsApp] Error sending image to {phone}: {e}")
            return {"success": False, "error": str(e)}

    async def send_video(self, phone: str, video_url: str, caption: str = "") -> dict:
        """Send a video with optional caption."""
        if not self.enabled:
            logger.info(f"[WhatsApp:Disabled] Would send video to {phone}")
            return {"success": True, "simulated": True}

        phone = self._format_phone(phone)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.api_url}/messages/video",
                    data={
                        "token": self.token,
                        "to": phone,
                        "video": video_url,
                        "caption": caption,
                    },
                )
                result = resp.json()
                success = str(result.get("sent", "")).lower() == "true"
                return {"success": success, "response": result, "error": result.get("error", "")}
        except Exception as e:
            logger.error(f"[WhatsApp] Error sending video to {phone}: {e}")
            return {"success": False, "error": str(e)}

    async def send_document(self, phone: str, document_url: str, filename: str = "", caption: str = "") -> dict:
        """Send a document (PDF/Excel) with optional caption."""
        if not self.enabled:
            logger.info(f"[WhatsApp:Disabled] Would send document to {phone}")
            return {"success": True, "simulated": True}

        phone = self._format_phone(phone)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.api_url}/messages/document",
                    data={
                        "token": self.token,
                        "to": phone,
                        "document": document_url,
                        "filename": filename,
                        "caption": caption,
                    },
                )
                result = resp.json()
                success = str(result.get("sent", "")).lower() == "true"
                return {"success": success, "response": result, "error": result.get("error", "")}
        except Exception as e:
            logger.error(f"[WhatsApp] Error sending document to {phone}: {e}")
            return {"success": False, "error": str(e)}

    async def send_bulk_text(self, phones: list[str], message: str) -> dict:
        """Send text to multiple recipients."""
        results = {"total": len(phones), "sent": 0, "failed": 0, "details": []}
        for phone in phones:
            result = await self.send_text(phone, message)
            if result.get("success"):
                results["sent"] += 1
            else:
                results["failed"] += 1
            results["details"].append({"phone": phone, **result})
        return results

    async def send_bulk_media(
        self,
        phones: list[str],
        media_type: str,  # "image", "video", "document"
        media_url: str,
        caption: str = "",
        filename: str = "",
    ) -> dict:
        """Send media to multiple recipients."""
        results = {"total": len(phones), "sent": 0, "failed": 0, "details": []}
        for phone in phones:
            if media_type == "image":
                result = await self.send_image(phone, media_url, caption)
            elif media_type == "video":
                result = await self.send_video(phone, media_url, caption)
            elif media_type == "document":
                result = await self.send_document(phone, media_url, filename, caption)
            else:
                result = await self.send_text(phone, f"{caption}\n{media_url}")

            if result.get("success"):
                results["sent"] += 1
            else:
                results["failed"] += 1
            results["details"].append({"phone": phone, **result})
        return results


# Singleton — recreated if settings change
_whatsapp: WhatsAppService | None = None


def get_whatsapp() -> WhatsAppService:
    global _whatsapp
    if _whatsapp is None or not _whatsapp.enabled:
        _whatsapp = WhatsAppService()
    return _whatsapp
