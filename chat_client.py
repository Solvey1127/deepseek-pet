# -*- coding: utf-8 -*-
"""Ollama 流式聊天客户端"""
import json
import requests

import re


class OllamaClient:
    def __init__(self, host="http://localhost:11434", model="deepseek-r1:8b"):
        self.host = host.rstrip("/")
        self.model = model

    def list_models(self):
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return []

    def is_online(self):
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def stream_chat(self, messages, temperature=0.7, top_p=0.9):
        """流式生成器：yield (delta_text)。messages 为 OpenAI 风格 [{role, content}]"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            },
        }
        with requests.post(f"{self.host}/api/chat", json=payload, stream=True, timeout=300) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("done"):
                    break
                delta = obj.get("message", {}).get("content", "")
                if delta:
                    yield delta

    @staticmethod
    def strip_think(text):
        """去掉 deepseek-r1 的思维链块 <think>...</think>"""
        return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
