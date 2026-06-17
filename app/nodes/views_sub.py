import base64
import json

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .models import Node
from .subscription import Subscription


def _build_v2ray_link(node: Node) -> str:
    """Generate standard V2Ray subscription link based on protocol."""
    if node.protocol == "vless":
        params = node.config or {}
        query = "&".join(f"{k}={v}" for k, v in params.items() if v)
        return f"vless://{node.config.get('id', '')}@{node.address}:{node.port}?{query}#{node.name}"
    elif node.protocol == "vmess":
        v = {
            "v": "2",
            "ps": node.name,
            "add": node.address,
            "port": str(node.port),
            "id": node.config.get("id", ""),
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
        return f"vmess://{base64.b64encode(json.dumps(v, separators=(',', ':')).encode()).decode()}"
    elif node.protocol == "shadowsocks":
        method = node.config.get("method", "chacha20-ietf-poly1305")
        password = node.config.get("password", "")
        raw = f"{method}:{password}"
        encoded = base64.b64encode(raw.encode()).decode()
        return f"ss://{encoded}@{node.address}:{node.port}#{node.name}"
    elif node.protocol == "trojan":
        password = node.config.get("password", "")
        query = f"?sni={node.config.get('sni', node.address)}&peer={node.config.get('peer', node.address)}"
        return f"trojan://{password}@{node.address}:{node.port}{query}#{node.name}"
    elif node.protocol == "hysteria2":
        password = node.config.get("password", "")
        obfs = node.config.get("obfs", "")
        query_parts = []
        if obfs:
            query_parts.append(f"obfs={obfs}")
            query_parts.append(f"obfs-password={node.config.get('obfs-password', '')}")
        if node.config.get("sni"):
            query_parts.append(f"sni={node.config['sni']}")
        query = "&".join(query_parts)
        return f"hysteria2://{password}@{node.address}:{node.port}{'?' + query if query else ''}#{node.name}"
    return ""


def _generate_base64(nodes) -> str:
    links = []
    for node in nodes:
        link = _build_v2ray_link(node)
        if link:
            links.append(link)
    return base64.b64encode("\n".join(links).encode()).decode()


def _generate_clash(nodes) -> str:
    """Generate Clash YAML format proxies."""
    lines = []
    for node in nodes:
        if node.protocol == "vless":
            id_ = node.config.get("id", "")
            flow = node.config.get("flow", "")
            lines.append(f"  - name: {node.name}")
            lines.append(f"    type: vless")
            lines.append(f"    server: {node.address}")
            lines.append(f"    port: {node.port}")
            lines.append(f"    uuid: {id_}")
            lines.append(f"    flow: {flow}")
            lines.append(f"    tls: {bool(node.config.get('tls', False))}")
            lines.append(f"    skip-cert-verify: true")
            lines.append(f"    udp: true")
        elif node.protocol == "shadowsocks":
            lines.append(f"  - name: {node.name}")
            lines.append(f"    type: ss")
            lines.append(f"    server: {node.address}")
            lines.append(f"    port: {node.port}")
            lines.append(f"    cipher: {node.config.get('method', 'chacha20-ietf-poly1305')}")
            lines.append(f"    password: {node.config.get('password', '')}")
        elif node.protocol == "trojan":
            lines.append(f"  - name: {node.name}")
            lines.append(f"    type: trojan")
            lines.append(f"    server: {node.address}")
            lines.append(f"    port: {node.port}")
            lines.append(f"    password: {node.config.get('password', '')}")
            lines.append(f"    sni: {node.config.get('sni', node.address)}")
            lines.append(f"    skip-cert-verify: true")
            lines.append(f"    udp: true")
        elif node.protocol == "hysteria2":
            lines.append(f"  - name: {node.name}")
            lines.append(f"    type: hysteria2")
            lines.append(f"    server: {node.address}")
            lines.append(f"    port: {node.port}")
            lines.append(f"    password: {node.config.get('password', '')}")
            lines.append(f"    sni: {node.config.get('sni', node.address)}")
            lines.append(f"    skip-cert-verify: true")
            lines.append(f"    udp: true")
    return "\n".join(lines)


def _generate_singbox(nodes) -> str:
    """Generate Sing-box JSON format outbounds."""
    outbounds = []
    for node in nodes:
        tag = node.name
        if node.protocol == "vless":
            outbounds.append({
                "type": "vless",
                "tag": tag,
                "server": node.address,
                "server_port": node.port,
                "uuid": node.config.get("id", ""),
                "flow": node.config.get("flow", ""),
                "tls": {"enabled": bool(node.config.get("tls", False))},
            })
        elif node.protocol == "shadowsocks":
            outbounds.append({
                "type": "shadowsocks",
                "tag": tag,
                "server": node.address,
                "server_port": node.port,
                "method": node.config.get("method", "chacha20-ietf-poly1305"),
                "password": node.config.get("password", ""),
            })
        elif node.protocol == "trojan":
            outbounds.append({
                "type": "trojan",
                "tag": tag,
                "server": node.address,
                "server_port": node.port,
                "password": node.config.get("password", ""),
                "tls": {"enabled": True, "server_name": node.config.get("sni", node.address)},
            })
        elif node.protocol == "hysteria2":
            outbounds.append({
                "type": "hysteria2",
                "tag": tag,
                "server": node.address,
                "server_port": node.port,
                "password": node.config.get("password", ""),
                "tls": {"enabled": True, "server_name": node.config.get("sni", node.address)},
            })
    return json.dumps({"outbounds": outbounds}, indent=2, ensure_ascii=False)


class SubscriptionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token, output_fmt=None):
        fmt = output_fmt or request.query_params.get("format", "base64")
        try:
            sub = Subscription.objects.select_related("user").get(token=token)
        except Subscription.DoesNotExist:
            return Response({"error": "无效的订阅链接"}, status=status.HTTP_404_NOT_FOUND)

        user = sub.user
        if not user.is_active:
            return Response({"error": "用户已禁用"}, status=status.HTTP_403_FORBIDDEN)

        if not user.plan or (user.expire_date and user.expire_date < timezone.now()):
            return Response({"error": "未购买套餐或套餐已过期"}, status=status.HTTP_403_FORBIDDEN)

        nodes = Node.objects.filter(is_active=True)

        if fmt == "clash":
            proxies = _generate_clash(nodes)
            content = f"""proxies:
{proxies}"""
            return HttpResponse(content, content_type="application/yaml")
        elif fmt == "singbox":
            content = _generate_singbox(nodes)
            return HttpResponse(content, content_type="application/json")
        else:
            content = _generate_base64(nodes)
            return HttpResponse(content, content_type="text/plain")
