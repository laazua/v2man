import json
import os
import io
import re

import paramiko


def _node_template_vars(node) -> dict[str, str]:
    """Build flat dict of template variables from a Node instance."""
    vars_dict = {}
    for field in ("name", "protocol", "address", "config_path", "reload_cmd", "ssh_host", "ssh_user"):
        val = getattr(node, field, "") or ""
        vars_dict[field] = str(val)
    vars_dict["port"] = str(node.port or 0)
    vars_dict["ssh_port"] = str(node.ssh_port or 22)
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
    return ssh_exec(node, f"cat > {remote_path} << 'V2MANEOF'\n{content}\nV2MANEOF")


def _inbounds_path(node) -> str:
    if node.config_path.endswith(".json"):
        return node.config_path
    return os.path.join(node.config_path, "inbounds.json").replace("\\", "/")


def _restart_cmd(node) -> str:
    return node.reload_cmd


def sync_user_uuid(node, old_uuid: str, new_uuid: str) -> dict:
    result = {"node_id": node.id, "node_name": node.name, "success": False, "error": ""}
    try:
        inb_path = _inbounds_path(node)
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
        inb_path = _inbounds_path(node)
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


def deploy_v2ray(node) -> dict:
    result = {"success": False, "error": ""}
    try:
        _, _, code = ssh_exec(
            node,
            "bash <(curl -fsSL https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh) 2>&1",
            timeout=120,
        )
        if code != 0:
            result["error"] = "V2Ray 安装失败"
            return result

        vars_dict = _node_template_vars(node)
        is_file_config = node.config_path.endswith(".json")
        templates_dir_exists = os.path.isdir(_TEMPLATE_DIR)

        if templates_dir_exists and not is_file_config:
            templates_used = _deploy_from_templates(node, vars_dict)
            if templates_used is not None:
                result["error"] = templates_used
                return result
            _, _, code = ssh_exec(node, f"{_restart_cmd(node)} 2>&1")
            if code != 0:
                result["error"] = "启动 V2Ray 失败"
                return result
            node.is_active = True
            node.save(update_fields=["is_active"])
            result["success"] = True
            return result

        if is_file_config:
            config = {
                "log": {"loglevel": "warning"},
                "inbounds": [{
                    "port": node.port,
                    "protocol": node.protocol,
                    "settings": {},
                    "tag": node.name,
                }],
                "outbounds": [{"protocol": "freedom", "tag": "direct"}],
            }
            _, _, code = ssh_write_file(node, node.config_path, json.dumps(config, indent=2))
            if code != 0:
                result["error"] = "写入配置文件失败"
                return result
        else:
            _, _, code = ssh_exec(node, f"mkdir -p {node.config_path}")
            if code != 0:
                result["error"] = "创建配置目录失败"
                return result
            files = {
                "log.json": json.dumps({"loglevel": "warning"}, indent=2),
                "inbounds.json": json.dumps({"inbounds": [{
                    "port": node.port,
                    "protocol": node.protocol,
                    "settings": {},
                    "tag": node.name,
                }]}, indent=2),
                "outbounds.json": json.dumps({"outbounds": [{"protocol": "freedom", "tag": "direct"}]}, indent=2),
                "dns.json": json.dumps({"dns": {}}, indent=2),
                "routing.json": json.dumps({"routing": {}}, indent=2),
                "api.json": json.dumps({"api": {}}, indent=2),
            }
            for name, content in files.items():
                remote = os.path.join(node.config_path, name).replace("\\", "/")
                _, _, code = ssh_write_file(node, remote, content)
                if code != 0:
                    result["error"] = f"写入 {name} 失败"
                    return result

        _, _, code = ssh_exec(node, f"{_restart_cmd(node)} 2>&1")
        if code != 0:
            result["error"] = "启动 V2Ray 失败"
            return result

        node.is_active = True
        node.save(update_fields=["is_active"])
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    return result