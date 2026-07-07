import base64
import json
import os
import re
import tempfile
from io import BytesIO

import aiohttp
from PIL import Image

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import Provider
from astrbot.api.star import Context, Star

# 插件会自动缩放图片，禁用 Pillow 解压炸弹防护以免拦截大图
Image.MAX_IMAGE_PIXELS = None


class AigcDetectorPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self._renderer_ready = self._check_renderer()

    @staticmethod
    def _check_renderer() -> bool:
        try:
            from PIL import Image  # noqa: F401

            return True
        except ImportError:
            return False

    def _get_first_image_url(self, event: AstrMessageEvent) -> str | None:
        chain = getattr(getattr(event, "message_obj", None), "message", None)
        if not isinstance(chain, list):
            return None

        for comp in chain:
            if isinstance(comp, Comp.Image):
                return comp.url or comp.file
            if isinstance(comp, Comp.Reply) and comp.chain:
                for reply_comp in comp.chain:
                    if isinstance(reply_comp, Comp.Image):
                        return reply_comp.url or reply_comp.file
        return None

    @filter.command("鉴定")
    async def aigc_detect(self, event: AstrMessageEvent):
        msg_text = event.get_message_str().removeprefix("鉴定").strip()
        image_url = self._get_first_image_url(event)

        if not image_url:
            yield event.plain_result(
                "请同时发送一张图片，或回复一张包含图片的消息。\n用法：鉴定 [附加说明]（需附带图片）"
            )
            return

        provider_id = self.config.get("image_model_provider", "")
        prompt_template = self.config.get("image_prompt_template", "")

        if not provider_id:
            provider = self.context.get_using_provider(event.unified_msg_origin)
        else:
            provider = self.context.get_provider_by_id(provider_id)

        if not isinstance(provider, Provider):
            yield event.plain_result("未找到可用的 LLM 提供商，请检查配置。")
            return

        modalities = provider.provider_config.get("modalities", None)
        if isinstance(modalities, list) and modalities and "image" not in modalities:
            yield event.plain_result(
                f"当前模型未启用图像能力，"
                "请在提供商配置中勾选「图像」能力，或更换支持多模态的提供商。"
            )
            return

        yield event.plain_result("正在分析图片，请稍候...")

        user_note = f"\n\n用户附加说明：{msg_text}" if msg_text else ""
        image_prompt = prompt_template + user_note

        try:
            local_path = await self._download_image(image_url)
            local_path = self._resize_image(local_path)

            image_data_uri = self._image_to_data_uri(local_path)
            resp = await provider.text_chat(
                prompt="请根据设定的角色和输出格式对这张图片进行 AIGC 检测分析，仅返回 JSON。",
                system_prompt=image_prompt,
                image_urls=[image_data_uri],
                session_id="",
            )
            raw = resp.completion_text if resp else ""
            if not raw:
                yield event.plain_result("分析失败，LLM 未返回有效结果。")
                return

            parsed = self._parse_json(raw)

            if parsed and self._renderer_ready:
                try:
                    report_path = self._generate_report(local_path, parsed)
                    yield event.image_result(report_path)
                    return
                except Exception as e:
                    logger.warning(f"报告图片生成失败，回退到文本: {e}")

            yield event.plain_result(self._format_fallback(parsed or raw))
        except Exception as e:
            logger.error(f"图片 AIGC 检测分析失败: {e}")
            yield event.plain_result(f"分析过程出现错误：{str(e)}")

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1)

        text = text.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    @staticmethod
    async def _download_image(url: str) -> str:
        if os.path.exists(url):
            return url
        output = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        output_path = output.name
        output.close()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                resp.raise_for_status()
                with open(output_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        f.write(chunk)
        return output_path

    @staticmethod
    def _resize_image(image_path: str, max_dim: int = 2048) -> str:
        img = Image.open(image_path)
        w, h = img.size
        if max(w, h) > max_dim:
            ratio = max_dim / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            img.save(image_path, quality=90, optimize=True)
            logger.info(f"图片已压缩: {w}×{h} → {new_w}×{new_h}")
        return image_path

    @staticmethod
    def _image_to_data_uri(image_path: str) -> str:
        img = Image.open(image_path)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=90)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"

    @staticmethod
    def _generate_report(image_path: str, data: dict) -> str:
        from .core import renderer

        return renderer.generate_report(image_path, data)

    @staticmethod
    def _format_fallback(data: dict | str) -> str:
        if isinstance(data, str):
            return data
        analysis = data.get("analysis", {})
        conclusion = data.get("conclusion", {})
        result = conclusion.get("result", "无法确定")
        aigc_score = conclusion.get("aigc_score", "N/A")
        summary = conclusion.get("summary", "")
        if isinstance(summary, list):
            summary = "\n".join(summary)
        lines = ["【AIGC 检测结果】\n"]
        for key, value in analysis.items():
            lines.append(f"▪ {key}：{value}\n")
        lines.append(f"\n结果判定：{result}")
        lines.append(f"AIGC评分：{aigc_score}%")
        if summary:
            lines.append(f"主要依据：{summary}")
        return "\n".join(lines)
