"""Tests for the nodes app."""

import base64
import json

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from nodes.models import Node
from nodes.serializers import NodePublicSerializer, NodeSerializer
from nodes.subscription import Subscription
from nodes.views_sub import (
    _build_v2ray_link,
    _generate_base64,
    _generate_clash,
    _generate_singbox,
)
from plans.models import Plan
from users.models import User


class BuildV2RayLinkTest(TestCase):
    """Tests for _build_v2ray_link protocol-specific link generation."""

    def setUp(self):
        self.node_kwargs = {
            "name": "TestNode",
            "address": "server.example.com",
            "port": 443,
        }

    def _make_node(self, protocol, config=None):
        return Node(
            name=self.node_kwargs["name"],
            protocol=protocol,
            address=self.node_kwargs["address"],
            port=self.node_kwargs["port"],
            config=config or {},
        )

    def test_vless_link(self):
        node = self._make_node("vless", {
            "id": "uuid-123", "flow": "xtls-rprx-vision", "tls": "tls",
        })
        link = _build_v2ray_link(node)
        self.assertTrue(link.startswith("vless://"))
        self.assertIn("uuid-123", link)
        self.assertIn("server.example.com", link)
        self.assertIn("443", link)
        self.assertIn("flow=xtls-rprx-vision", link)
        self.assertIn("TestNode", link)

    def test_vless_empty_config(self):
        node = self._make_node("vless", {})
        link = _build_v2ray_link(node)
        self.assertTrue(link.startswith("vless://"))

    def test_vmess_link(self):
        node = self._make_node("vmess", {
            "aid": "0", "scy": "auto", "net": "ws",
            "host": "example.com", "path": "/ws",
        })
        link = _build_v2ray_link(node)
        self.assertTrue(link.startswith("vmess://"))
        decoded = base64.b64decode(link[8:]).decode()
        data = json.loads(decoded)
        self.assertEqual(data["add"], "server.example.com")
        self.assertEqual(data["port"], "443")
        self.assertEqual(data["net"], "ws")
        self.assertEqual(data["v"], "2")

    def test_vmess_defaults(self):
        node = self._make_node("vmess", {})
        link = _build_v2ray_link(node)
        decoded = base64.b64decode(link[8:]).decode()
        data = json.loads(decoded)
        self.assertEqual(data.get("aid"), "0")
        self.assertEqual(data.get("scy"), "auto")
        self.assertEqual(data.get("net"), "tcp")

    def test_shadowsocks_link(self):
        node = self._make_node("shadowsocks", {
            "method": "aes-256-gcm", "password": "secret123",
        })
        link = _build_v2ray_link(node)
        self.assertTrue(link.startswith("ss://"))
        self.assertIn("server.example.com", link)
        self.assertIn("443", link)
        self.assertIn("TestNode", link)

    def test_shadowsocks_default_method(self):
        node = self._make_node("shadowsocks", {"password": "test"})
        link = _build_v2ray_link(node)
        self.assertTrue(link.startswith("ss://"))

    def test_trojan_link(self):
        node = self._make_node("trojan", {
            "password": "trojan-pass",
            "sni": "sni.example.com",
            "peer": "peer.example.com",
        })
        link = _build_v2ray_link(node)
        self.assertTrue(link.startswith("trojan://"))
        self.assertIn("trojan-pass", link)
        self.assertIn("server.example.com", link)
        self.assertIn("sni=sni.example.com", link)

    def test_trojan_default_sni(self):
        node = self._make_node("trojan", {"password": "pass"})
        link = _build_v2ray_link(node)
        self.assertIn("sni=server.example.com", link)

    def test_hysteria2_link(self):
        node = self._make_node("hysteria2", {
            "password": "hy-pass",
            "obfs": "salamander",
            "obfs-password": "obfs-pass",
            "sni": "hy.example.com",
        })
        link = _build_v2ray_link(node)
        self.assertTrue(link.startswith("hysteria2://"))
        self.assertIn("hy-pass@server.example.com", link)
        self.assertIn("obfs=salamander", link)
        self.assertIn("obfs-password=obfs-pass", link)
        self.assertIn("sni=hy.example.com", link)

    def test_hysteria2_no_obfs(self):
        node = self._make_node("hysteria2", {"password": "pass"})
        link = _build_v2ray_link(node)
        self.assertTrue(link.startswith("hysteria2://pass@"))

    def test_unknown_protocol(self):
        node = self._make_node("unknown", {})
        link = _build_v2ray_link(node)
        self.assertEqual(link, "")

    def test_with_user_uuid(self):
        node = self._make_node("vless", {"flow": "xtls"})
        link = _build_v2ray_link(node, user_uuid="custom-uuid")
        self.assertTrue(link.startswith("vless://custom-uuid@"))


class GenerateBase64Test(TestCase):
    """Tests for _generate_base64."""

    def setUp(self):
        self.node1 = Node(
            name="Node1", protocol="vless",
            address="a.com", port=443,
            config={"id": "uuid1"},
        )
        self.node2 = Node(
            name="Node2", protocol="shadowsocks",
            address="b.com", port=8443,
            config={"password": "pass"},
        )

    def test_generate_with_nodes(self):
        result = _generate_base64([self.node1, self.node2])
        decoded = base64.b64decode(result).decode()
        self.assertIn("vless://", decoded)
        self.assertIn("ss://", decoded)
        self.assertIn("Node1", decoded)
        self.assertIn("Node2", decoded)

    def test_generate_empty_list(self):
        result = _generate_base64([])
        self.assertEqual(result, "")

    def test_generate_with_user_uuid(self):
        result = _generate_base64([self.node1], user_uuid="user-uuid")
        decoded = base64.b64decode(result).decode()
        self.assertIn("user-uuid", decoded)


class GenerateClashTest(TestCase):
    """Tests for _generate_clash."""

    def setUp(self):
        self.nodes = [
            Node(
                name="VLESS Node", protocol="vless",
                address="vless.com", port=443,
                config={"id": "uuid", "flow": "xtls", "tls": "tls"},
            ),
            Node(
                name="VMess Node", protocol="vmess",
                address="vmess.com", port=80,
                config={"aid": "1", "scy": "auto", "net": "ws"},
            ),
            Node(
                name="SS Node", protocol="shadowsocks",
                address="ss.com", port=8388,
                config={"method": "aes-256-gcm", "password": "ss-pass"},
            ),
            Node(
                name="Trojan Node", protocol="trojan",
                address="trojan.com", port=443,
                config={
                    "password": "trojan-pass", "sni": "trojan-sni.com",
                },
            ),
            Node(
                name="Hy2 Node", protocol="hysteria2",
                address="hy2.com", port=443,
                config={"password": "hy-pass", "sni": "hy2-sni.com"},
            ),
        ]

    def test_clash_generates_all_protocols(self):
        result = _generate_clash(self.nodes)
        self.assertIn("VLESS Node", result)
        self.assertIn("VMess Node", result)
        self.assertIn("SS Node", result)
        self.assertIn("Trojan Node", result)
        self.assertIn("Hy2 Node", result)
        self.assertIn("type: vless", result)
        self.assertIn("type: vmess", result)
        self.assertIn("type: ss", result)
        self.assertIn("type: trojan", result)
        self.assertIn("type: hysteria2", result)

    def test_clash_empty(self):
        result = _generate_clash([])
        self.assertEqual(result, "")


class GenerateSingboxTest(TestCase):
    """Tests for _generate_singbox."""

    def setUp(self):
        self.nodes = [
            Node(
                name="VLESS", protocol="vless",
                address="a.com", port=443,
                config={"id": "uuid", "flow": "xtls", "tls": "tls"},
            ),
            Node(
                name="SS", protocol="shadowsocks",
                address="b.com", port=8388,
                config={"method": "aes-256-gcm", "password": "pass"},
            ),
        ]

    def test_singbox_generates_outbounds(self):
        result = json.loads(_generate_singbox(self.nodes))
        self.assertIn("outbounds", result)
        self.assertEqual(len(result["outbounds"]), 2)
        self.assertEqual(result["outbounds"][0]["type"], "vless")
        self.assertEqual(result["outbounds"][1]["type"], "shadowsocks")

    def test_singbox_empty(self):
        result = json.loads(_generate_singbox([]))
        self.assertEqual(result["outbounds"], [])


class NodeModelTest(TestCase):
    """Tests for Node model."""

    def test_str(self):
        node = Node(name="MyNode", protocol="vless")
        self.assertEqual(str(node), "MyNode (vless)")

    def test_default_values(self):
        node = Node.objects.create(
            name="Default", protocol="vmess",
            address="x.com", port=80,
        )
        self.assertTrue(node.is_active)
        self.assertEqual(node.sort_order, 0)
        self.assertEqual(node.config, {})
        self.assertEqual(node.ssh_port, 22)
        self.assertEqual(node.ssh_user, "root")


class NodeSerializerTest(TestCase):
    """Tests for NodePublicSerializer and NodeSerializer."""

    def setUp(self):
        self.node = Node.objects.create(
            name="Serialized Node",
            protocol="trojan",
            address="s.com",
            port=443,
            ssh_key="my-private-key",
            ssh_password="",
        )

    def test_public_serializer_excludes_sensitive_fields(self):
        data = NodePublicSerializer(self.node).data
        self.assertIn("name", data)
        self.assertIn("protocol", data)
        self.assertIn("address", data)
        self.assertIn("port", data)
        self.assertNotIn("ssh_key", data)
        self.assertNotIn("ssh_password", data)
        self.assertNotIn("config_path", data)

    def test_full_serializer_includes_ssh_configured(self):
        data = NodeSerializer(self.node).data
        self.assertIn("ssh_configured", data)
        self.assertTrue(data["ssh_configured"])

    def test_ssh_configured_false(self):
        node = Node.objects.create(
            name="No SSH", protocol="vless",
            address="x.com", port=80,
        )
        data = NodeSerializer(node).data
        self.assertFalse(data["ssh_configured"])

    def test_ssh_configured_with_password(self):
        node = Node.objects.create(
            name="SSH Pass", protocol="vless",
            address="x.com", port=80,
            ssh_password="pass123",
        )
        data = NodeSerializer(node).data
        self.assertTrue(data["ssh_configured"])


class SubscriptionModelTest(TestCase):
    """Tests for Subscription model."""

    def test_token_auto_generated(self):
        user = User.objects.create_user(
            username="sub-test", password="test123",
        )
        sub = Subscription.objects.get(user=user)
        self.assertIsNotNone(sub.token)
        self.assertNotEqual(str(sub.token), "")

    def test_str(self):
        user = User.objects.create_user(
            username="sub-test2", password="test123",
        )
        sub = Subscription.objects.get(user=user)
        self.assertIn("sub-test2", str(sub))
        self.assertIn(str(sub.token), str(sub))


class NodeListViewTest(TestCase):
    """Tests for NodeListView."""

    def setUp(self):
        self.client = APIClient()
        self.active = Node.objects.create(
            name="Active", protocol="vless",
            address="a.com", port=443, is_active=True,
        )
        self.inactive = Node.objects.create(
            name="Inactive", protocol="vmess",
            address="b.com", port=80, is_active=False,
        )

    def test_list_only_active(self):
        resp = self.client.get("/api/nodes/")
        self.assertEqual(resp.status_code, 200)
        names = [n["name"] for n in resp.data]
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)

    def test_public_access(self):
        resp = self.client.get("/api/nodes/")
        self.assertEqual(resp.status_code, 200)


class SubscriptionViewTest(TestCase):
    """Tests for SubscriptionView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="sub-user", password="test123",
        )
        self.sub = Subscription.objects.get(user=self.user)
        self.node = Node.objects.create(
            name="Sub Node", protocol="vless",
            address="sub.example.com", port=443,
            config={"id": "test-uuid"}, is_active=True,
        )
        self.plan = Plan.objects.create(
            name="Test Plan", price=5.00,
            traffic_limit=1024, duration_days=30,
        )
        self.plan.nodes.add(self.node)

    def _assign_plan(self):
        self.user.plan = self.plan
        self.user.expire_date = (
            timezone.now() + timezone.timedelta(days=30)
        )
        self.user.save()

    def test_base64_format(self):
        self._assign_plan()
        resp = self.client.get(f"/api/subscription/{self.sub.token}/")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        decoded = base64.b64decode(content).decode()
        self.assertIn("vless://", decoded)
        self.assertIn("sub.example.com", decoded)

    def test_clash_format(self):
        self._assign_plan()
        resp = self.client.get(
            f"/api/subscription/{self.sub.token}/clashmeta/",
        )
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn("proxies:", content)
        self.assertIn("Sub Node", content)
        self.assertIn("type: vless", content)

    def test_singbox_format(self):
        self._assign_plan()
        resp = self.client.get(
            f"/api/subscription/{self.sub.token}/singbox/",
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn("outbounds", data)
        self.assertEqual(len(data["outbounds"]), 1)
        self.assertEqual(data["outbounds"][0]["type"], "vless")

    def test_invalid_token_404(self):
        resp = self.client.get(
            "/api/subscription/"
            "00000000-0000-0000-0000-000000000000/",
        )
        self.assertEqual(resp.status_code, 404)

    def test_expired_user_returns_error(self):
        self._assign_plan()
        self.user.expire_date = (
            timezone.now() - timezone.timedelta(days=1)
        )
        self.user.save()
        resp = self.client.get(f"/api/subscription/{self.sub.token}/")
        self.assertEqual(resp.status_code, 403)

    def test_no_plan_returns_error(self):
        resp = self.client.get(f"/api/subscription/{self.sub.token}/")
        self.assertEqual(resp.status_code, 403)

    def test_inactive_user_returns_error(self):
        self._assign_plan()
        self.user.is_active = False
        self.user.save()
        resp = self.client.get(f"/api/subscription/{self.sub.token}/")
        self.assertEqual(resp.status_code, 403)
