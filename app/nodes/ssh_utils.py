import json
import math
import os
import io
import re
import uuid
import shlex

import paramiko


def _node_template_vars(node, user_uuid: str = "") -> dict[str, str]:
    """Build flat dict of template variables from a Node instance."""
    vars_dict = {}
    for field in ("name", "protocol", "address", "config_path", "reload_cmd", "ssh_host", "ssh_user"):
        val = getattr(node, field, "") or ""
        vars_dict[field] = str(val)
    vars_dict["port"] = str(node.port or 0)
    vars_dict["ssh_port"] = str(node.ssh_port or 22)
    vars_dict["ip"] = node.address or "0.0.0.0"
    vars_dict["uuid"] = user_uuid or str(uuid.uuid4())
    vars_dict["uuid2"] = str(uuid.uuid4())
    vars_dict["uuid3"] = str(uuid.uuid4())
    for k, v in (node.config or {}).items():
        vars_dict[k] = str(v) if v is not None else ""
    return vars_dict


def _render_template(template: str, vars_dict: dict[str, str]) -> str:
    """Replace {{ var }} placeholders with values from vars_dict."""

    def _replacer(m):
        key = m.group(1).strip()
        return vars_dict.get(key, m.group(0))

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", _replacer, template)


_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v2ray_templates")


def _deploy_from_templates(node, vars_dict: dict[str, str]) -> str | None:
    """Use template files from v2ray_templates/ to generate configs.
    Returns error string on failure, None on success."""
    if not os.path.isdir(_TEMPLATE_DIR):
        return None  # no templates, skip

    _, _, code = ssh_exec(node, f"mkdir -p {_shell_quote(node.config_path)}")
    if code != 0:
        return "创建配置目录失败"

    for fname in os.listdir(_TEMPLATE_DIR):
        if not fname.endswith(".j2"):
            continue
        fpath = os.path.join(_TEMPLATE_DIR, fname)
        with open(fpath) as f:
            rendered = _render_template(f.read(), vars_dict)
        out_name = fname[:-3]  # strip .j2 → inbounds.json.j2 → inbounds.json
        remote = os.path.join(node.config_path, out_name).replace("\\", "/")
        _, _, code = ssh_write_file(node, remote, rendered)
        if code != 0:
            return f"写入 {out_name} 失败"
    return None


def _shell_quote(path: str) -> str:
    if not path or ';' in path or '|' in path or '`' in path or '$' in path:
        raise ValueError(f"路径包含非法字符: {path}")
    return shlex.quote(path)


def _connect(node) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host = node.ssh_host or node.address
    port = node.ssh_port or 22
    user = node.ssh_user or "root"

    if node.ssh_key:
        key_file = io.StringIO(node.ssh_key)
        try:
            pkey = paramiko.RSAKey.from_private_key(key_file)
        except paramiko.SSHException:
            key_file.seek(0)
            try:
                pkey = paramiko.Ed25519Key.from_private_key(key_file)
            except paramiko.SSHException:
                key_file.seek(0)
                pkey = paramiko.ECDSAKey.from_private_key(key_file)
        client.connect(host, port=port, username=user, pkey=pkey, timeout=10)
    elif node.ssh_password:
        client.connect(host, port=port, username=user, password=node.ssh_password, timeout=10)
    else:
        raise ValueError(f"节点 {node.name} 未配置 SSH 私钥或密码")
    return client


def ssh_exec(node, command: str, timeout: int = 30) -> tuple[str, str, int]:
    client = _connect(node)
    try:
        _, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return stdout.read().decode().strip(), stderr.read().decode().strip(), exit_code
    finally:
        client.close()


def ssh_write_file(node, remote_path: str, content: str) -> tuple[str, str, int]:
    safe_path = _shell_quote(remote_path)
    return ssh_exec(node, f"cat > {safe_path} << 'V2MANEOF'\n{content}\nV2MANEOF")


def ssh_upload_binary(node, remote_path: str, data: bytes) -> tuple[str, str, int]:
    """Upload binary data via SFTP."""
    client = _connect(node)
    try:
        sftp = client.open_sftp()
        with sftp.open(remote_path, "wb") as f:
            f.write(data)
        return "", "", 0
    except Exception as e:
        return "", str(e), -1
    finally:
        client.close()


def _inbounds_path(node) -> str:
    if node.config_path.endswith(".json"):
        return node.config_path
    return os.path.join(node.config_path, "inbounds.json").replace("\\", "/")


def _restart_cmd(node) -> str:
    return node.reload_cmd


def sync_user_uuid(node, old_uuid: str, new_uuid: str) -> dict:
    result = {"node_id": node.id, "node_name": node.name, "success": False, "error": ""}
    try:
        inb_path = _shell_quote(_inbounds_path(node))
        stdout, stderr, code = ssh_exec(
            node,
            f"sed -i 's/{old_uuid}/{new_uuid}/g' {inb_path} && "
            f"{_restart_cmd(node)} 2>&1; echo 'EXIT:$?'",
            timeout=30,
        )
        exit_code = int(stdout.split("EXIT:")[-1] if "EXIT:" in stdout else "1")
        if exit_code != 0:
            result["error"] = stderr or f"命令返回码 {exit_code}"
            return result
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    return result


def refresh_node_config(node, user_uuid: str) -> dict:
    result = {"node_id": node.id, "node_name": node.name, "success": False, "uuid_found": False, "error": ""}
    try:
        inb_path = _shell_quote(_inbounds_path(node))
        out, _, _ = ssh_exec(node, f"grep -q '{user_uuid}' {inb_path} 2>/dev/null && echo found || echo missing")
        result["uuid_found"] = "found" in out

        stdout, stderr, code = ssh_exec(node, f"{_restart_cmd(node)} 2>&1; echo 'EXIT:$?'")
        exit_code = int(stdout.split("EXIT:")[-1] if "EXIT:" in stdout else "1")
        if exit_code != 0:
            result["error"] = stderr or f"重启返回码 {exit_code}"
            return result
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    return result


def _build_inbound_entry(node, uuid_str: str) -> dict:
    cfg = node.config or {}
    entry = {
        "port": node.port,
        "protocol": node.protocol,
        "listen": node.address or "0.0.0.0",
        "tag": node.name,
    }
    if node.protocol == "shadowsocks":
        entry["settings"] = {
            "method": cfg.get("method", "chacha20-ietf-poly1305"),
            "password": cfg.get("password") or uuid_str[:16],
        }
    elif node.protocol == "trojan":
        entry["settings"] = {
            "clients": [{
                "password": cfg.get("password") or uuid_str[:16],
                "email": f"{uuid_str}@v2man.dev",
                "level": 0,
            }]
        }
    elif node.protocol == "hysteria2":
        entry["settings"] = {
            "clients": [{
                "password": cfg.get("password") or uuid_str[:16],
                "email": f"{uuid_str}@v2man.dev",
                "level": 0,
            }]
        }
    else:
        settings: dict = {
            "clients": [{
                "id": uuid_str,
                "email": f"{uuid_str}@v2man.dev",
                "level": 0,
            }]
        }
        if node.protocol == "vless":
            settings["decryption"] = "none"
        entry["settings"] = settings
    return entry


def _patch_v2ray_service(node) -> str | None:
    """Ensure systemd ExecStart (both main file and drop-in) matches node.config_path.
    Returns error string on failure, None on success."""
    config_flag = "-d" if not node.config_path.endswith(".json") else "-config"
    safe_cfg = _shell_quote(node.config_path)
    expected = f"ExecStart=/usr/local/bin/v2ray run {config_flag} {safe_cfg}"
    drop_in = "/etc/systemd/system/v2ray.service.d/10-donot_touch_single_conf.conf"
    patched = False

    # patch main service file
    out, _, _ = ssh_exec(
        node,
        f"grep -q '^{expected}' /etc/systemd/system/v2ray.service 2>/dev/null && echo OK || echo NEED_PATCH",
        timeout=10,
    )
    if "NEED_PATCH" in out:
        _, _, code = ssh_exec(
            node,
            f"sed -i 's|^ExecStart=/usr/local/bin/v2ray run .*|{expected}|' /etc/systemd/system/v2ray.service && "
            f"systemctl daemon-reload 2>&1",
            timeout=10,
        )
        if code != 0:
            return "更新 v2ray.service 失败"
        patched = True

    # patch drop-in if present (fhs-install-v2ray creates this, overrides main)
    out2, _, _ = ssh_exec(
        node, f"test -f {drop_in} && echo EXISTS || echo MISSING", timeout=10
    )
    if "EXISTS" in out2:
        _, _, code = ssh_exec(
            node,
            f"sed -i 's|^ExecStart=/usr/local/bin/v2ray run .*|{expected}|' {drop_in} && "
            f"systemctl daemon-reload 2>&1",
            timeout=10,
        )
        if code != 0:
            return "更新 v2ray.service.d drop-in 失败"
        patched = True

    if patched:
        _, _, _ = ssh_exec(node, "systemctl daemon-reload 2>&1", timeout=10)
    return None


_INSTALL_URLS = [
    "https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh",
    "https://github.com/v2fly/fhs-install-v2ray/raw/master/install-release.sh",
]


_BINARY_URL = "https://github.com/v2fly/v2ray-core/releases/download/v5.49.0/v2ray-linux-64.zip"
_GH_MIRRORS = [
    "https://ghproxy.com/https://github.com",
    "https://hub.fastgit.xyz",
]


def _try_install_script(node) -> bool:
    """Try fhs-install-v2ray script (via mirrors). Returns True if installed."""
    script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    local_script = os.path.join(script_dir, "install-v2ray.sh")

    if not os.path.isfile(local_script):
        import urllib.request
        for url in _INSTALL_URLS:
            try:
                with urllib.request.urlopen(url, timeout=15) as resp:
                    with open(local_script, "wb") as f:
                        f.write(resp.read())
                break
            except Exception:
                continue

    if not os.path.isfile(local_script):
        return False

    with open(local_script) as f:
        script_content = f.read()

    for mirror in _GH_MIRRORS:
        patched = script_content.replace("https://github.com", mirror)
        _, _, code = ssh_write_file(node, "/tmp/install-v2ray.sh", patched)
        if code != 0:
            continue
        _, _, code = ssh_exec(node, "bash /tmp/install-v2ray.sh 2>&1", timeout=120)
        if code == 0:
            out, _, _ = ssh_exec(node, "which v2ray 2>/dev/null || echo MISSING", timeout=10)
            if "MISSING" not in out:
                return True
    return False


def _install_v2ray_binary(node) -> str | None:
    """Download v2ray zip from management server and install manually on node.
    Returns error string or None on success."""
    import urllib.request

    zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v2ray-bin.zip")
    if not os.path.isfile(zip_path):
        try:
            with urllib.request.urlopen(_BINARY_URL, timeout=60) as resp:
                with open(zip_path, "wb") as f:
                    f.write(resp.read())
        except Exception as e:
            return f"下载 v2ray 二进制失败: {e}"

    with open(zip_path, "rb") as f:
        zip_data = f.read()

    err = ssh_upload_binary(node, "/tmp/v2ray.zip", zip_data)
    if err[2] != 0:
        return f"上传 v2ray 二进制失败: {err[1]}"

    svc = (
        '[Unit]\nDescription=V2Ray Service\n'
        'Documentation=https://www.v2fly.org/\n'
        'After=network.target nss-lookup.target\n\n'
        '[Service]\nUser=root\n'
        'CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE\n'
        'AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE\n'
        'NoNewPrivileges=true\n'
        'ExecStart=/usr/local/bin/v2ray run -d /usr/local/etc/v2ray\n'
        'Restart=on-failure\nRestartPreventExitStatus=23\n\n'
        '[Install]\nWantedBy=multi-user.target\n'
    )

    cmds = (
        "mkdir -p /usr/local/bin /usr/local/share/v2ray /usr/local/etc/v2ray /var/log/v2ray && "
        "cd /tmp && unzip -o v2ray.zip 2>/dev/null && "
        "install -m 755 v2ray /usr/local/bin/v2ray && "
        "install -m 755 v2ctl /usr/local/bin/v2ctl 2>/dev/null; "
        "install -m 644 geoip.dat /usr/local/share/v2ray/geoip.dat 2>/dev/null; "
        "install -m 644 geosite.dat /usr/local/share/v2ray/geosite.dat 2>/dev/null; "
        "touch /var/log/v2ray/access.log /var/log/v2ray/error.log 2>/dev/null; "
        "mkdir -p /etc/systemd/system && "
        "which v2ray 2>/dev/null || echo MISSING"
    )
    out, _, code = ssh_exec(node, cmds, timeout=30)
    if "MISSING" in out or code != 0:
        return "手动安装 v2ray 失败"

    _, _, code = ssh_write_file(node, "/etc/systemd/system/v2ray.service", svc)
    if code != 0:
        return "创建 systemd 服务文件失败"
    return None


def _ensure_v2ray_installed(node) -> str | None:
    """Install v2ray if not present. Returns error string or None."""
    out, _, _ = ssh_exec(node, "which v2ray 2>/dev/null || echo MISSING", timeout=10)
    if "MISSING" not in out:
        return None

    zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v2ray-bin.zip")
    if os.path.isfile(zip_path):
        err = _install_v2ray_binary(node)
        if err:
            return err
        return None

    if _try_install_script(node):
        return None

    err = _install_v2ray_binary(node)
    if err:
        return err
    return None


def deploy_v2ray(node) -> dict:
    admin_uuid = str(uuid.uuid4())
    result = {"success": False, "error": "", "admin_uuid": admin_uuid}
    try:
        install_err = _ensure_v2ray_installed(node)
        if install_err:
            result["error"] = install_err
            return result

        _, _, code = ssh_exec(node, "systemctl enable v2ray 2>&1", timeout=10)
        if code != 0:
            result["error"] = "启用 systemd 服务失败"
            return result

        svc_err = _patch_v2ray_service(node)
        if svc_err:
            result["error"] = svc_err
            return result

        ssh_exec(node, "mkdir -p /var/log/v2ray && chown -R root:root /var/log/v2ray && chmod 755 /var/log/v2ray && chmod 644 /var/log/v2ray/*.log 2>/dev/null", timeout=10)

        vars_dict = _node_template_vars(node, user_uuid=admin_uuid)
        is_file_config = node.config_path.endswith(".json")
        templates_dir_exists = os.path.isdir(_TEMPLATE_DIR)

        if templates_dir_exists and not is_file_config:
            templates_used = _deploy_from_templates(node, vars_dict)
            if templates_used is not None:
                result["error"] = templates_used
                return result
            restart_out, restart_err, code = ssh_exec(node, f"{_restart_cmd(node)} 2>&1")
            if code != 0:
                detail = (restart_err or restart_out or "").strip()[-300:]
                result["error"] = f"启动 V2Ray 失败: {detail}" if detail else "启动 V2Ray 失败"
                return result
            node.is_active = True
            node.save(update_fields=["is_active"])
            result["success"] = True
            result["template_uuids"] = [
                vars_dict.get("uuid", admin_uuid),
                vars_dict.get("uuid2", ""),
                vars_dict.get("uuid3", ""),
            ]
            return result

        inbound = _build_inbound_entry(node, admin_uuid)

        if is_file_config:
            config = {
                "log": {"loglevel": "warning"},
                "inbounds": [inbound],
                "outbounds": [{"protocol": "freedom", "tag": "direct"}],
                "api": {"tag": "api", "services": ["HandlerService", "LoggerService", "StatsService"]},
                "stats": {},
                "policy": {
                    "levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
                    "system": {"statsInboundUplink": True, "statsInboundDownlink": True},
                },
                "routing": {
                    "rules": [
                        {"type": "field", "inboundTag": ["api"], "outboundTag": "api"},
                        {"type": "field", "outboundTag": "direct", "ip": ["geoip:cn"]},
                        {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
                    ]
                },
            }
            config.setdefault("inbounds", []).append({
                "listen": "127.0.0.1", "port": 10085, "protocol": "dokodemo-door",
                "settings": {"address": "127.0.0.1"}, "tag": "api",
            })
            _, _, code = ssh_write_file(node, node.config_path, json.dumps(config, indent=2))
            if code != 0:
                result["error"] = "写入配置文件失败"
                return result
        else:
            _, _, code = ssh_exec(node, f"mkdir -p {_shell_quote(node.config_path)}")
            if code != 0:
                result["error"] = "创建配置目录失败"
                return result
            files = {
                "log.json": json.dumps({"loglevel": "warning"}, indent=2),
                "inbounds.json": json.dumps({"inbounds": [inbound]}, indent=2),
                "outbounds.json": json.dumps({"outbounds": [{"protocol": "freedom", "tag": "direct"}]}, indent=2),
                "dns.json": json.dumps({"dns": {}}, indent=2),
                "routing.json": json.dumps({"routing": {
                    "rules": [
                        {"type": "field", "inboundTag": ["api"], "outboundTag": "api"},
                        {"type": "field", "outboundTag": "direct", "ip": ["geoip:cn"]},
                        {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
                    ]
                }}, indent=2),
                "api.json": json.dumps({
                    "api": {"tag": "api", "services": ["HandlerService", "LoggerService", "StatsService"]},
                    "stats": {},
                }, indent=2),
                "policy.json": json.dumps({
                    "policy": {
                        "levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
                        "system": {"statsInboundUplink": True, "statsInboundDownlink": True},
                    }
                }, indent=2),
                "api_inbound.json": json.dumps({
                    "inbounds": [{"listen": "127.0.0.1", "port": 10085, "protocol": "dokodemo-door", "settings": {"address": "127.0.0.1"}, "tag": "api"}]
                }, indent=2),
            }
            for name, content in files.items():
                remote = os.path.join(node.config_path, name).replace("\\", "/")
                _, _, code = ssh_write_file(node, remote, content)
                if code != 0:
                    result["error"] = f"写入 {name} 失败"
                    return result

        restart_out, restart_err, code = ssh_exec(node, f"{_restart_cmd(node)} 2>&1")
        if code != 0:
            detail = (restart_err or restart_out or "").strip()[-300:]
            result["error"] = f"启动 V2Ray 失败: {detail}" if detail else "启动 V2Ray 失败"
            return result

        node.is_active = True
        node.save(update_fields=["is_active"])
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    return result


def collect_node_traffic(node) -> dict:
    """
    SSH into node, query v2ray StatsService via API.
    Returns {"email_prefix": {"uplink": int, "downlink": int}, ...} or {"error": msg}.
    Uses -reset to atomically read and clear counters.
    """
    try:
        cmd = "v2ray api stats -server=127.0.0.1:10085 -json -reset 2>&1"
        out, err, code = ssh_exec(node, cmd, timeout=30)
        if code != 0:
            msg = (err or out or "").strip()[-200:]
            return {"error": f"v2ray api stats 失败: {msg}"}
        data = json.loads(out)
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失败: {e}"}
    except Exception as e:
        return {"error": str(e)}

    result = {}
    for stat in data.get("stat", []):
        name = stat.get("name", "")
        value = int(stat.get("value", 0))
        if value <= 0:
            continue
        m = re.match(r"^user>>>(.+?)@v2man\.dev>>>traffic>>>(uplink|downlink)$", name)
        if not m:
            continue
        email_prefix = m.group(1)
        direction = m.group(2)
        if email_prefix not in result:
            result[email_prefix] = {"uplink": 0, "downlink": 0}
        result[email_prefix][direction] += value
    return result


def sync_users_to_node(node) -> str | None:
    """
    Read all active (non-expired) users whose plan includes this node,
    and rewrite the inbounds.json with all their UUIDs.
    Returns error string or None on success.
    """
    from django.contrib.auth import get_user_model
    from django.utils import timezone

    User = get_user_model()
    now = timezone.now()

    users = User.objects.filter(
        plan__isnull=False,
        plan__nodes=node,
        is_active=True,
        expire_date__gt=now,
    ).exclude(plan__isnull=True).only("uuid", "username", "traffic_used", "traffic_total")
    user_list = list(users)

    if node.protocol in ("shadowsocks",):
        return None  # shadowsocks uses shared password, not per-user

    clients = []
    for u in user_list:
        # 流量用完的用户不加入节点配置
        if u.traffic_total > 0 and u.traffic_used >= u.traffic_total:
            continue
        c: dict = {"email": f"{u.username}@v2man.dev", "level": 0}
        if node.protocol in ("trojan", "hysteria2"):
            cfg = node.config or {}
            c["password"] = cfg.get("password") or str(u.uuid)[:16]
        else:
            c["id"] = str(u.uuid)
            c["alterId"] = 0
        clients.append(c)

    if not clients:
        return "没有活跃用户需要同步"

    inbound = _build_inbound_entry(node, str(user_list[0].uuid))
    inbound["settings"]["clients"] = clients
    content = json.dumps({"inbounds": [inbound]}, indent=2)

    inb_path = _inbounds_path(node)
    _, _, code = ssh_write_file(node, inb_path, content)
    if code != 0:
        return "写入 inbounds.json 失败"

    r, _, c = ssh_exec(node, f"{_restart_cmd(node)} 2>&1; echo EXIT:$?", timeout=15)
    exit_code = int(r.split("EXIT:")[-1].strip()) if "EXIT:" in r else 1
    if exit_code != 0:
        return f"重启 V2Ray 失败: {(r or '')[:200]}"
    return None