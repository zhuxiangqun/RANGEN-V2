#!/usr/bin/env python3
"""
Voice Module - 语音功能 (TTS/STT)

提供文本转语音和语音转文本功能
"""

import asyncio
import logging
import base64
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class VoiceProvider(Enum):
    """语音提供商"""
    GOOGLE = "google"
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    EDGE_TTS = "edge_tts"  # 免费推荐


@dataclass
class TTSConfig:
    """TTS 配置"""
    provider: VoiceProvider = VoiceProvider.EDGE_TTS
    voice: str = "zh-CN-XiaoxiaoNeural"  # 中文语音
    rate: str = "+0%"  # 语速
    pitch: str = "+0Hz"  # 音调
    output_format: str = "audio-16khz-32kbitrate-mono-mp3"


@dataclass
class STTConfig:
    """STT 配置"""
    provider: VoiceProvider = VoiceProvider.GOOGLE
    language: str = "zh-CN"
    sample_rate: int = 16000


class TTS:
    """
    Text-to-Speech 文本转语音
    
    支持多种提供商:
    - Edge TTS (免费，推荐)
    - Google Cloud TTS
    - OpenAI TTS
    - ElevenLabs TTS
    """
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self.provider = self.config.provider
    
    async def synthesize(self, text: str) -> bytes:
        """将文本转为语音"""
        if self.provider == VoiceProvider.EDGE_TTS:
            return await self._synthesize_edge(text)
        elif self.provider == VoiceProvider.GOOGLE:
            return await self._synthesize_google(text)
        elif self.provider == VoiceProvider.OPENAI:
            return await self._synthesize_openai(text)
        elif self.provider == VoiceProvider.ELEVENLABS:
            return await self._synthesize_elevenlabs(text)
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")
    
    async def _synthesize_edge(self, text: str) -> bytes:
        """使用 Edge TTS 合成语音"""
        try:
            from edge_tts import Communicate
            
            communicate = Communicate(
                text,
                voice=self.config.voice,
                rate=self.config.rate,
                pitch=self.config.pitch
            )
            
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            return audio_data
            
        except ImportError:
            logger.error("edge-tts not installed. Install with: pip install edge-tts")
            return b""
        except Exception as e:
            logger.error(f"Edge TTS failed: {e}")
            return b""
    
    async def _synthesize_google(self, text: str) -> bytes:
        """使用 Google Cloud TTS 合成语音"""
        # TODO: 实现 Google Cloud TTS
        logger.warning("Google Cloud TTS not implemented yet")
        return b""
    
    async def _synthesize_openai(self, text: str) -> bytes:
        """使用 OpenAI TTS 合成语音"""
        # TODO: 实现 OpenAI TTS
        logger.warning("OpenAI TTS not implemented yet")
        return b""
    
    async def _synthesize_elevenlabs(self, text: str) -> bytes:
        """使用 ElevenLabs TTS 合成语音"""
        # TODO: 实现 ElevenLabs TTS
        logger.warning("ElevenLabs TTS not implemented yet")
        return b""


class STT:
    """
    Speech-to-Text 语音转文本
    
    支持多种提供商:
    - Google Cloud STT
    - OpenAI Whisper
    - DeepSpeech
    """
    
    def __init__(self, config: Optional[STTConfig] = None):
        self.config = config or STTConfig()
        self.provider = self.config.provider
    
    async def recognize(self, audio_data: bytes) -> str:
        """将语音转为文本"""
        if self.provider == VoiceProvider.GOOGLE:
            return await self._recognize_google(audio_data)
        elif self.provider == VoiceProvider.OPENAI:
            return await self._recognize_openai(audio_data)
        else:
            raise ValueError(f"Unsupported STT provider: {self.provider}")
    
    async def _recognize_google(self, audio_data: bytes) -> str:
        """使用 Google Cloud STT 识别语音"""
        # TODO: 实现 Google Cloud STT
        logger.warning("Google Cloud STT not implemented yet")
        return ""
    
    async def _recognize_openai(self, audio_data: bytes) -> str:
        """使用 OpenAI Whisper 识别语音"""
        # TODO: 实现 OpenAI Whisper
        logger.warning("OpenAI Whisper not implemented yet")
        return ""


class Voice:
    """
    统一语音接口
    
    整合 TTS 和 STT 功能
    """
    
    def __init__(
        self,
        tts_config: Optional[TTSConfig] = None,
        stt_config: Optional[STTConfig] = None,
        llm_client: Optional[Any] = None
    ):
        self.tts = TTS(tts_config)
        self.stt = STT(stt_config)
        
        # 🚀 Gateway 能力扩展：集成 LLM 客户端
        self.llm_client = llm_client
        
        # 如果没有提供 LLM 客户端，尝试使用默认的
        if self.llm_client is None:
            try:
                from src.core.llm_integration import LLMIntegration
                self.llm_client = LLMIntegration()
            except ImportError:
                logger.warning("LLM client not available")
    
    async def speak(self, text: str) -> bytes:
        """将文本转为语音"""
        return await self.tts.synthesize(text)
    
    async def listen(self, audio_data: bytes) -> str:
        """将语音转为文本"""
        return await self.stt.recognize(audio_data)
    
    async def voice_chat(self, audio_input: bytes) -> bytes:
        """
        语音对话 (输入语音 -> 输出语音)
        
        1. STT: 语音 -> 文本
        2. LLM: 处理文本
        3. TTS: 文本 -> 语音
        """
        # 1. 语音转文本
        text = await self.listen(audio_input)
        
        # 2. 🚀 Gateway 能力扩展：调用 LLM/Agent 处理
        if self.llm_client:
            try:
                if hasattr(self.llm_client, 'chat'):
                    response = await self.llm_client.chat(text)
                    response_text = response.get("content", f"你说了: {text}") if isinstance(response, dict) else str(response)
                elif hasattr(self.llm_client, 'generate'):
                    response = await self.llm_client.generate(text)
                    response_text = response.get("text", f"你说了: {text}") if isinstance(response, dict) else str(response)
                elif hasattr(self.llm_client, 'complete'):
                    response = await self.llm_client.complete(text)
                    response_text = response if isinstance(response, str) else f"你说了: {text}"
                else:
                    response_text = f"你说了: {text}"
            except Exception as e:
                logger.warning(f"LLM 调用失败: {e}")
                response_text = f"你说了: {text}"
        else:
            response_text = f"你说了: {text}"
        
        # 3. 文本转语音
        audio_output = await self.speak(response_text)
        
        return audio_output


# ==================== 便捷函数 ====================

def create_voice(
    provider: VoiceProvider = VoiceProvider.EDGE_TTS,
    voice: str = "zh-CN-XiaoxiaoNeural"
) -> Voice:
    """创建语音接口"""
    tts_config = TTSConfig(provider=provider, voice=voice)
    stt_config = STTConfig()
    return Voice(tts_config, stt_config)
