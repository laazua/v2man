"""Subscription views for generating client configurations."""

import base64
import json
import logging
from typing import Optional, Union

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Node
from .subscription import Subscription

logger = logging.getLogger("business")


def _build_v2ray_link(node: Node, user_uuid: str = "") -> str:
    """Generate standard V2Ray subscription link based on protocol."""
    uid: str = user_uuid or node.config.get("id", "")
    if node.protocol == "vless":
        params: dict = node.config or {}
        query: str = "&".join(f"{k}={v}" for k, v in params.items() if v != "")
        return (
            f"vless://{uid}@{node.address}:{node.port}" f"?{query}#{node.name}"
        )
    elif node.protocol == "vmess":
        v: dict[str, str] = {
            "v": "2",
            "ps": node.name,
            "add": node.address,
            "port": str(node.port),
            "id": uid,
            "aid": node.config.get("aid", "0"),
            "scy": node.config.get("scy", "auto"),
            "net": node.config.get("net", "tcp"),
            "type": node.config.get("type", "none"),
            "host": node.config.get("host", ""),
            "path": node.config.get("path", ""),
            "tls": node.config.get("tls", ""),
            "sni": node.config.get("sni", ""),
            "alpn": node.config.get("alpn", ""),
        }
        encoded: str = base64.b64encode(
            json.dumps(v, separators=(",", ":")).encode()
        ).decode()
        return f"vmess://{encoded}"
    elif node.protocol == "shadowsocks":
        method: str = node.config.get("method", "chacha20-ietf-poly1305")
        password: str = node.config.get("password", "")
        raw: str = f"{method}:{password}"
        encoded = base64.b64encode(raw.encode()).decode()
        return f"ss://{encoded}@{node.address}:{node.port}" f"#{node.name}"
    elif node.protocol == "trojan":
        password = node.config.get("password", "")
        sni: str = node.config.get("sni", node.address)
        peer: str = node.config.get("peer", node.address)
        query = f"?sni={sni}&peer={peer}"
        return (
            f"trojan://{password}@{node.address}:{node.port}"
            f"{query}#{node.name}"
        )
    elif node.protocol == "hysteria2":
        password = node.config.get("password", "")
        obfs: str = node.config.get("obfs", "")
        query_parts: list[str] = []
        if obfs:
            query_parts.append(f"obfs={obfs}")
            query_parts.append(
                f"obfs-password={node.config.get('obfs-password', '')}"
            )
        if node.config.get("sni"):
            query_parts.append(f"sni={node.config['sni']}")
        query = "&".join(query_parts)
        suffix: str = f"?{query}" if query else ""
        return (
            f"hysteria2://{password}@{node.address}:{node.port}"
            f"{suffix}#{node.name}"
        )
    return ""


def _generate_base64(nodes: list[Node], user_uuid: str = "") -> str:
    """Generate base64-encoded subscription content."""
    links: list[str] = []
    for node in nodes:
        link: str = _build_v2ray_link(node, user_uuid)
        if link:
            links.append(link)
    return base64.b64encode("\n".join(links).encode()).decode()


def _generate_clash(nodes: list[Node], user_uuid: str = "") -> str:
    """Generate Clash YAML format proxies section."""
    lines: list[str] = []
    for node in nodes:
        uid: str = user_uuid or node.config.get("id", "")
        if node.protocol == "vless":
            flow: str = node.config.get("flow", "")
            lines.append(f"  - name: {node.name}")
            lines.append("    type: vless")
            lines.append(f"    server: {node.address}")
            lines.append(f"    port: {node.port}")
            lines.append(f"    uuid: {uid}")
            lines.append(f"    flow: {flow}")
            tls: str = "true" if node.config.get("tls") else "false"
            lines.append(f"    tls: {tls}")
            lines.append("    skip-cert-verify: true")
            lines.append("    udp: true")
        elif node.protocol == "vmess":
            lines.append(f"  - name: {node.name}")
            lines.append("    type: vmess")
            lines.append(f"    server: {node.address}")
            lines.append(f"    port: {node.port}")
            lines.append(f"    uuid: {uid}")
            lines.append(f"    alterId: {node.config.get('aid', '0')}")
            lines.append(f"    cipher: {node.config.get('scy', 'auto')}")
            lines.append(f"    network: {node.config.get('net', 'tcp')}")
            tls = "true" if node.config.get("tls") else "false"
            lines.append(f"    tls: {tls}")
            lines.append("    skip-cert-verify: true")
            lines.append("    udp: true")
        elif node.protocol == "shadowsocks":
            lines.append(f"  - name: {node.name}")
            lines.append("    type: ss")
            lines.append(f"    server: {node.address}")
            lines.append(f"    port: {node.port}")
            lines.append(
                "    cipher:"
                f" {node.config.get('method', 'chacha20-ietf-poly1305')}"
            )
            lines.append(f"    password: {node.config.get('password', '')}")
        elif node.protocol == "trojan":
            lines.append(f"  - name: {node.name}")
            lines.append("    type: trojan")
            lines.append(f"    server: {node.address}")
            lines.append(f"    port: {node.port}")
            lines.append(f"    password: {node.config.get('password', '')}")
            lines.append(f"    sni: {node.config.get('sni', node.address)}")
            lines.append("    skip-cert-verify: true")
            lines.append("    udp: true")
        elif node.protocol == "hysteria2":
            lines.append(f"  - name: {node.name}")
            lines.append("    type: hysteria2")
            lines.append(f"    server: {node.address}")
            lines.append(f"    port: {node.port}")
            lines.append(f"    password: {node.config.get('password', '')}")
            lines.append(f"    sni: {node.config.get('sni', node.address)}")
            lines.append("    skip-cert-verify: true")
            lines.append("    udp: true")
    return "\n".join(lines)


def _generate_singbox(nodes: list[Node], user_uuid: str = "") -> str:
    """Generate Sing-box JSON format outbounds."""
    outbounds: list[dict] = []
    for node in nodes:
        uid: str = user_uuid or node.config.get("id", "")
        tag: str = node.name
        if node.protocol == "vless":
            outbounds.append(
                {
                    "type": "vless",
                    "tag": tag,
                    "server": node.address,
                    "server_port": node.port,
                    "uuid": uid,
                    "flow": node.config.get("flow", ""),
                    "tls": {
                        "enabled": bool(node.config.get("tls", False)),
                    },
                }
            )
        elif node.protocol == "vmess":
            outbounds.append(
                {
                    "type": "vmess",
                    "tag": tag,
                    "server": node.address,
                    "server_port": node.port,
                    "uuid": uid,
                    "alter_id": int(node.config.get("aid", "0")),
                    "security": node.config.get("scy", "auto"),
                }
            )
        elif node.protocol == "shadowsocks":
            outbounds.append(
                {
                    "type": "shadowsocks",
                    "tag": tag,
                    "server": node.address,
                    "server_port": node.port,
                    "method": node.config.get(
                        "method", "chacha20-ietf-poly1305"
                    ),
                    "password": node.config.get("password", ""),
                }
            )
        elif node.protocol == "trojan":
            outbounds.append(
                {
                    "type": "trojan",
                    "tag": tag,
                    "server": node.address,
                    "server_port": node.port,
                    "password": node.config.get("password", ""),
                    "tls": {
                        "enabled": True,
                        "server_name": node.config.get("sni", node.address),
                    },
                }
            )
        elif node.protocol == "hysteria2":
            outbounds.append(
                {
                    "type": "hysteria2",
                    "tag": tag,
                    "server": node.address,
                    "server_port": node.port,
                    "password": node.config.get("password", ""),
                    "tls": {
                        "enabled": True,
                        "server_name": node.config.get("sni", node.address),
                    },
                }
            )
    return json.dumps({"outbounds": outbounds}, indent=2, ensure_ascii=False)


class SubscriptionView(APIView):
    """API view for serving subscription content in various formats."""

    permission_classes = [AllowAny]

    def get(
        self,
        request: Request,
        token: str,
        output_fmt: Optional[str] = None,
    ) -> Union[HttpResponse, Response]:
        """Serve subscription content based on format parameter."""
        fmt: str = output_fmt or request.query_params.get("format", "base64")
        try:
            sub: Subscription = Subscription.objects.select_related(
                "user"
            ).get(token=token)
        except Subscription.DoesNotExist:
            return Response(
                {"error": "无效的订阅链接"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = sub.user
        if not user.is_active:
            return Response(
                {"error": "用户已禁用"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.plan or (
            user.expire_date and user.expire_date < timezone.now()
        ):
            return Response(
                {"error": "未购买套餐或套餐已过期"},
                status=status.HTTP_403_FORBIDDEN,
            )

        nodes: list[Node] = list(user.plan.nodes.filter(is_active=True))
        user_uuid: str = str(user.uuid)

        logger.info(
            "订阅请求: user_id=%s format=%s nodes=%d",
            user.id,
            fmt,
            len(nodes),
        )
        if fmt == "clash":
            proxies: str = _generate_clash(nodes, user_uuid)
            content: str = f"proxies:\n{proxies}"
            return HttpResponse(content, content_type="application/yaml")
        elif fmt == "singbox":
            content = _generate_singbox(nodes, user_uuid)
            return HttpResponse(content, content_type="application/json")
        else:
            content = _generate_base64(nodes, user_uuid)
            return HttpResponse(content, content_type="text/plain")
