"""SSH utilities for deploying and managing V2Ray nodes."""

import io
import json
import logging
import os
import re
import shlex
import urllib.error
import urllib.request
import uuid
from typing import Optional

import paramiko

from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger("business")

_TEMPLATE_DIR: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "v2ray_templates",
)

_INSTALL_URLS: list[str] = [
    "https://raw.githubusercontent.com/v2fly/"
    "fhs-install-v2ray/master/install-release.sh",
    "https://github.com/v2fly/fhs-install-v2ray/"
    "raw/master/install-release.sh",
]

_BINARY_URL: str = (
    "https://github.com/v2fly/v2ray-core/releases/download/"
    "v5.49.0/v2ray-linux-64.zip"
)

_GH_MIRRORS: list[str] = [
    "https://ghproxy.com/https://github.com",
    "https://hub.fastgit.xyz",
]


def _node_template_vars(
    node: "Node", user_uuid: str = ""
) -> dict[str, str]:
    """Build flat dict of template variables from a Node instance."""
    vars_dict: dict[str, str] = {}
    for field in (
        "name",
        "protocol",
        "address",
        "config_path",
        "reload_cmd",
        "ssh_host",
        "ssh_user",
    ):
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


def _render_template(
    template: str, vars_dict: dict[str, str]
) -> str:
    """Replace {{ var }} placeholders with values from vars_dict."""
    def _replacer(m: re.Match) -> str:
        key: str = m.group(1).strip()
        return vars_dict.get(key, m.group(0))

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", _replacer, template)


def _deploy_from_templates(
    node: "Node", vars_dict: dict[str, str]
) -> Optional[str]:
    """Deploy configuration from Jinja-like template files."""
    if not os.path.isdir(_TEMPLATE_DIR):
        logger.info(
            "模板目录不存在，跳过模板部署: node=%s", node.name
        )
        return None

    _, _, code = ssh_exec(
        node, f"mkdir -p {_shell_quote(node.config_path)}"
    )
    if code != 0:
        return "创建配置目录失败"

    for fname in os.listdir(_TEMPLATE_DIR):
        if not fname.endswith(".j2"):
            continue
        fpath: str = os.path.join(_TEMPLATE_DIR, fname)
        with open(fpath) as f:
            rendered: str = _render_template(f.read(), vars_dict)
        out_name: str = fname[:-3]
        remote: str = os.path.join(
            node.config_path, out_name
        ).replace("\\", "/")
        _, _, code = ssh_write_file(node, remote, rendered)
        if code != 0:
            return f"写入 {out_name} 失败"
    return None


def _shell_quote(path: str) -> str:
    """Quote a shell path safely, rejecting dangerous characters."""
    if not path or ";" in path or "|" in path or "`" in path or "$" in path:
        raise ValueError(f"路径包含非法字符: {path}")
    return shlex.quote(path)


def _connect(node: "Node") -> paramiko.SSHClient:
    """Establish SSH connection to the given node."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host: str = node.ssh_host or node.address
    port: int = node.ssh_port or 22
    user: str = node.ssh_user or "root"

    if node.ssh_key:
        auth_method: str = "key"
    elif node.ssh_password:
        auth_method = "password"
    else:
        auth_method = "none"

    logger.info(
        "SSH连接: node=%s(%s) host=%s port=%s user=%s auth=%s",
        node.name, node.id, host, port, user, auth_method,
    )
    try:
        if node.ssh_key:
            key_file = io.StringIO(node.ssh_key)
            try:
                pkey = paramiko.RSAKey.from_private_key(key_file)
            except paramiko.SSHException:
                key_file.seek(0)
                try:
                    pkey = paramiko.Ed25519Key.from_private_key(
                        key_file
                    )
                except paramiko.SSHException:
                    key_file.seek(0)
                    pkey = paramiko.ECDSAKey.from_private_key(
                        key_file
                    )
            client.connect(
                host,
                port=port,
                username=user,
                pkey=pkey,
                timeout=10,
            )
        elif node.ssh_password:
            client.connect(
                host,
                port=port,
                username=user,
                password=node.ssh_password,
                timeout=10,
            )
        else:
            raise ValueError(
                f"节点 {node.name} 未配置 SSH 私钥或密码"
            )
        logger.info("SSH连接成功: node=%s", node.name)
    except Exception as e:
        logger.error(
            "SSH连接失败: node=%s error=%s", node.name, str(e)
        )
        raise
    return client


def ssh_exec(
    node: "Node", command: str, timeout: int = 30
) -> tuple[str, str, int]:
    """Execute a command on the remote node via SSH."""
    trunc_cmd: str = command[:120].replace("\n", "\\n")
    logger.info(
        "SSH执行: node=%s cmd=%s timeout=%s",
        node.name, trunc_cmd, timeout,
    )
    client = _connect(node)
    try:
        _, stdout, stderr = client.exec_command(
            command, timeout=timeout
        )
        exit_code: int = stdout.channel.recv_exit_status()
        out_text: str = stdout.read().decode().strip()
        err_text: str = stderr.read().decode().strip()
        if exit_code != 0:
            logger.warning(
                "SSH执行失败: node=%s exit=%s stderr=%s",
                node.name, exit_code, err_text[:200],
            )
        else:
            logger.info(
                "SSH执行成功: node=%s exit=%s",
                node.name, exit_code,
            )
        return out_text, err_text, exit_code
    except Exception as e:
        logger.error(
            "SSH执行异常: node=%s error=%s",
            node.name, str(e),
        )
        raise
    finally:
        client.close()


def ssh_write_file(
    node: "Node", remote_path: str, content: str
) -> tuple[str, str, int]:
    """Write content to a remote file via SSH heredoc."""
    safe_path: str = _shell_quote(remote_path)
    size: int = len(content)
    logger.info(
        "SSH写文件: node=%s path=%s size=%s",
        node.name, safe_path, size,
    )
    heredoc: str = (
        f"cat > {safe_path} << 'V2MANEOF'\n{content}\nV2MANEOF"
    )
    result: tuple[str, str, int] = ssh_exec(node, heredoc)
    if result[2] != 0:
        logger.error(
            "SSH写文件失败: node=%s path=%s",
            node.name, safe_path,
        )
    else:
        logger.info(
            "SSH写文件成功: node=%s path=%s",
            node.name, safe_path,
        )
    return result


def ssh_upload_binary(
    node: "Node", remote_path: str, data: bytes
) -> tuple[str, str, int]:
    """Upload binary data to a remote file via SFTP."""
    logger.info(
        "SSH上传二进制: node=%s path=%s size=%s",
        node.name, remote_path, len(data),
    )
    client = _connect(node)
    try:
        sftp = client.open_sftp()
        with sftp.open(remote_path, "wb") as f:
            f.write(data)
        logger.info(
            "SSH上传二进制成功: node=%s path=%s",
            node.name, remote_path,
        )
        return "", "", 0
    except Exception as e:
        logger.error(
            "SSH上传二进制失败: node=%s path=%s error=%s",
            node.name, remote_path, str(e),
        )
        return "", str(e), -1
    finally:
        client.close()


def _inbounds_path(node: "Node") -> str:
    """Determine the inbounds configuration file path."""
    if node.config_path.endswith(".json"):
        return node.config_path
    return os.path.join(
        node.config_path, "inbounds.json"
    ).replace("\\", "/")


def _restart_cmd(node: "Node") -> str:
    """Get the V2Ray restart command for the node."""
    return node.reload_cmd


def sync_user_uuid(
    node: "Node", old_uuid: str, new_uuid: str
) -> dict:
    """Sync a user UUID change to the remote node configuration."""
    result: dict = {
        "node_id": node.id,
        "node_name": node.name,
        "success": False,
        "error": "",
    }
    logger.info(
        "同步UUID: node=%s old=%s new=%s",
        node.name,
        old_uuid[:8] + "***",
        new_uuid[:8] + "***",
    )
    try:
        inb_path: str = _shell_quote(_inbounds_path(node))
        cmd: str = (
            f"sed -i 's/{old_uuid}/{new_uuid}/g' {inb_path} && "
            f"{_restart_cmd(node)} 2>&1; echo 'EXIT:$?'"
        )
        stdout, stderr, code = ssh_exec(node, cmd, timeout=30)
        exit_code: int = int(
            stdout.split("EXIT:")[-1] if "EXIT:" in stdout else "1"
        )
        if exit_code != 0:
            result["error"] = stderr or f"命令返回码 {exit_code}"
            return result
        result["success"] = True
        logger.info("同步UUID成功: node=%s", node.name)
    except Exception as e:
        result["error"] = str(e)
        logger.error(
            "同步UUID失败: node=%s error=%s", node.name, str(e)
        )
    return result


def refresh_node_config(
    node: "Node", user_uuid: str
) -> dict:
    """Refresh the remote node configuration (check + restart)."""
    result: dict = {
        "node_id": node.id,
        "node_name": node.name,
        "success": False,
        "uuid_found": False,
        "error": "",
    }
    logger.info("刷新节点配置: node=%s", node.name)
    try:
        inb_path: str = _shell_quote(_inbounds_path(node))
        check_cmd: str = (
            f"grep -q '{user_uuid}' {inb_path}"
            " 2>/dev/null && echo found || echo missing"
        )
        out, _, _ = ssh_exec(node, check_cmd)
        result["uuid_found"] = "found" in out

        restart_cmd: str = (
            f"{_restart_cmd(node)} 2>&1; echo 'EXIT:$?'"
        )
        stdout, stderr, code = ssh_exec(node, restart_cmd)
        exit_code: int = int(
            stdout.split("EXIT:")[-1]
            if "EXIT:" in stdout else "1"
        )
        if exit_code != 0:
            result["error"] = stderr or f"重启返回码 {exit_code}"
            return result
        result["success"] = True
        logger.info(
            "刷新节点配置成功: node=%s uuid_found=%s",
            node.name, result["uuid_found"],
        )
    except Exception as e:
        result["error"] = str(e)
        logger.error(
            "刷新节点配置失败: node=%s error=%s",
            node.name, str(e),
        )
    return result


def _build_inbound_entry(
    node: "Node", uuid_str: str
) -> dict:
    """Build a V2Ray inbound configuration entry for the node."""
    cfg: dict = node.config or {}
    entry: dict = {
        "port": node.port,
        "protocol": node.protocol,
        "listen": node.address or "0.0.0.0",
        "tag": node.name,
    }
    if node.protocol == "shadowsocks":
        entry["settings"] = {
            "method": cfg.get(
                "method", "chacha20-ietf-poly1305"
            ),
            "password": cfg.get("password") or uuid_str[:16],
        }
    elif node.protocol == "trojan":
        entry["settings"] = {
            "clients": [
                {
                    "password": cfg.get("password")
                    or uuid_str[:16],
                    "email": f"{uuid_str}@v2man.dev",
                    "level": 0,
                }
            ]
        }
    elif node.protocol == "hysteria2":
        entry["settings"] = {
            "clients": [
                {
                    "password": cfg.get("password")
                    or uuid_str[:16],
                    "email": f"{uuid_str}@v2man.dev",
                    "level": 0,
                }
            ]
        }
    else:
        settings: dict = {
            "clients": [
                {
                    "id": uuid_str,
                    "email": f"{uuid_str}@v2man.dev",
                    "level": 0,
                }
            ]
        }
        if node.protocol == "vless":
            settings["decryption"] = "none"
        entry["settings"] = settings
    return entry


def _patch_v2ray_service(node: "Node") -> Optional[str]:
    """Patch the V2Ray systemd service file for correct config."""
    logger.info(
        "修补V2Ray systemd服务: node=%s config_path=%s",
        node.name, node.config_path,
    )
    config_flag: str = (
        "-d" if not node.config_path.endswith(".json")
        else "-config"
    )
    safe_cfg: str = _shell_quote(node.config_path)
    expected: str = (
        f"ExecStart=/etc/v2ray/v2ray run"
        f" {config_flag} {safe_cfg}"
    )
    drop_in: str = (
        "/etc/systemd/system/v2ray.service.d/"
        "10-donot_touch_single_conf.conf"
    )
    patched: bool = False

    grep_cmd: str = (
        f"grep -q '^{expected}'"
        " /etc/systemd/system/v2ray.service"
        " 2>/dev/null && echo OK || echo NEED_PATCH"
    )
    out, _, _ = ssh_exec(node, grep_cmd, timeout=10)
    if "NEED_PATCH" in out:
        sed_cmd: str = (
            "sed -i 's|^ExecStart=/etc/v2ray/v2ray run .*|"
            f"{expected}|' /etc/systemd/system/v2ray.service"
            " && systemctl daemon-reload 2>&1"
        )
        _, _, code = ssh_exec(node, sed_cmd, timeout=10)
        if code != 0:
            return "更新 v2ray.service 失败"
        patched = True

    dropin_check: str = (
        f"test -f {drop_in} && echo EXISTS || echo MISSING"
    )
    out2, _, _ = ssh_exec(node, dropin_check, timeout=10)
    if "EXISTS" in out2:
        sed_dropin_cmd: str = (
            "sed -i 's|^ExecStart=/etc/v2ray/v2ray run .*|"
            f"{expected}|' {drop_in}"
            " && systemctl daemon-reload 2>&1"
        )
        _, _, code = ssh_exec(node, sed_dropin_cmd, timeout=10)
        if code != 0:
            return "更新 v2ray.service.d drop-in 失败"
        patched = True

    if patched:
        ssh_exec(
            node, "systemctl daemon-reload 2>&1", timeout=10
        )
        logger.info(
            "systemd服务已修补: node=%s", node.name
        )
    else:
        logger.info(
            "systemd服务无需修补: node=%s", node.name
        )
    return None


def _try_install_script(node: "Node") -> bool:
    """Try to install V2Ray via the official install script."""
    logger.info("尝试脚本安装V2Ray: node=%s", node.name)
    script_dir: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".."
    )
    local_script: str = os.path.join(
        script_dir, "install-v2ray.sh"
    )

    if not os.path.isfile(local_script):
        for url in _INSTALL_URLS:
            try:
                with urllib.request.urlopen(
                    url, timeout=15
                ) as resp:
                    with open(local_script, "wb") as f:
                        f.write(resp.read())
                break
            except (urllib.error.URLError, OSError):
                continue

    if not os.path.isfile(local_script):
        logger.warning(
            "安装脚本不存在: node=%s", node.name
        )
        return False

    with open(local_script) as f:
        script_content: str = f.read()

    for mirror in _GH_MIRRORS:
        patched: str = script_content.replace(
            "https://github.com", mirror
        )
        _, _, code = ssh_write_file(
            node, "/tmp/install-v2ray.sh", patched
        )
        if code != 0:
            continue
        _, _, code = ssh_exec(
            node, "bash /tmp/install-v2ray.sh 2>&1",
            timeout=120,
        )
        if code == 0:
            out, _, _ = ssh_exec(
                node,
                "which v2ray 2>/dev/null || echo MISSING",
                timeout=10,
            )
            if "MISSING" not in out:
                logger.info(
                    "脚本安装V2Ray成功: node=%s", node.name
                )
                return True
            logger.warning(
                "脚本安装后v2ray未找到: node=%s mirror=%s",
                node.name, mirror,
            )
    logger.error(
        "脚本安装V2Ray失败: node=%s", node.name
    )
    return False


def _install_v2ray_binary(node: "Node") -> Optional[str]:
    """Install V2Ray by uploading binary zip and extracting."""
    logger.info("二进制安装V2Ray: node=%s", node.name)

    zip_path: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "v2ray-bin.zip",
    )
    if not os.path.isfile(zip_path):
        try:
            with urllib.request.urlopen(
                _BINARY_URL, timeout=60
            ) as resp:
                with open(zip_path, "wb") as f:
                    f.write(resp.read())
        except urllib.error.URLError as e:
            return f"下载 v2ray 二进制失败: {e}"

    with open(zip_path, "rb") as f:
        zip_data: bytes = f.read()

    err: tuple[str, str, int] = ssh_upload_binary(
        node, "/tmp/v2ray.zip", zip_data
    )
    if err[2] != 0:
        return f"上传 v2ray 二进制失败: {err[1]}"

    svc: str = (
        "[Unit]\nDescription=V2Ray Service\n"
        "Documentation=https://www.v2fly.org/\n"
        "After=network.target nss-lookup.target\n\n"
        "[Service]\nUser=root\n"
        "CapabilityBoundingSet=CAP_NET_ADMIN"
        " CAP_NET_BIND_SERVICE\n"
        "AmbientCapabilities=CAP_NET_ADMIN"
        " CAP_NET_BIND_SERVICE\n"
        "NoNewPrivileges=true\n"
        "Environment=V2RAY_LOCATION_ASSET=/etc/v2ray\n"
        "ExecStart=/etc/v2ray/v2ray run"
        " -d /usr/local/etc/v2ray\n"
        "Restart=on-failure\n"
        "RestartPreventExitStatus=23\n\n"
        "[Install]\nWantedBy=multi-user.target\n"
    )

    # Diagnostic: check zip status before extraction
    diag: tuple[str, str, int] = ssh_exec(
        node,
        "ls -la /tmp/v2ray.zip 2>&1"
        " && echo 'ZIP_OK' || echo 'ZIP_MISSING'",
    )
    logger.info(
        "节点v2ray.zip状态: node=%s out=%s err=%s code=%s",
        node.name, diag[0][:100], diag[1][:100], diag[2],
    )

    cmds: str = (
        "mkdir -p /etc/v2ray /usr/local/share/v2ray"
        " /usr/local/etc/v2ray /var/log/v2ray && "
        "cd /tmp && "
        "rm -rf v2ray_x && mkdir v2ray_x && "
        # Try python3 zipfile (stdlib) - extract v2ray directly
        "(python3 -c 'import zipfile;"
        "z=zipfile.ZipFile(\"v2ray.zip\");"
        "z.extractall(\"v2ray_x\")' 2>&1 || "
        # Fallback: ensure unzip, then extract
        "(command -v unzip >/dev/null 2>&1 || "
        "apt install -y unzip -qq 2>&1 || "
        "yum install -y unzip -q 2>&1 || "
        "dnf install -y unzip -q 2>&1) && "
        "unzip -o v2ray.zip -d v2ray_x 2>&1) && "
        # Find and install v2ray binary
        "v2ray_bin=$(find v2ray_x -name v2ray"
        " -type f | head -1) && "
        "[ -n \"$v2ray_bin\" ] && "
        "install -m 755 \"$v2ray_bin\""
        " /etc/v2ray/v2ray && "
        # Copy resource files alongside the binary
        "for f in geoip.dat geosite.dat; do "
        "src=$(find v2ray_x -name \"$f\""
        " -type f | head -1); "
        "[ -n \"$src\" ] && cp \"$src\""
        " /etc/v2ray/; done && "
        "touch /var/log/v2ray/access.log"
        " /var/log/v2ray/error.log 2>&1 && "
        "mkdir -p /etc/systemd/system && "
        "test -x /etc/v2ray/v2ray"
        " && echo OK || echo MISSING"
    )
    out, err, code = ssh_exec(node, cmds, timeout=120)
    if "MISSING" in out or code != 0:
        logger.error(
            "二进制安装V2Ray失败: node=%s code=%s"
            " out=%s err=%s",
            node.name,
            code,
            (out or "")[:500],
            (err or "")[:500],
        )
        return "手动安装 v2ray 失败"

    _, _, code = ssh_write_file(
        node, "/etc/systemd/system/v2ray.service", svc
    )
    if code != 0:
        return "创建 systemd 服务文件失败"
    return None


def _ensure_v2ray_installed(node: "Node") -> Optional[str]:
    """Ensure V2Ray is installed on the remote node."""
    logger.info("检查V2Ray安装: node=%s", node.name)
    out, _, _ = ssh_exec(
        node,
        "which v2ray 2>/dev/null || echo MISSING",
        timeout=10,
    )
    if "MISSING" not in out:
        logger.info("V2Ray已安装: node=%s", node.name)
        return None

    logger.info("V2Ray未安装，开始安装: node=%s", node.name)

    zip_path: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "v2ray-bin.zip",
    )
    if os.path.isfile(zip_path):
        err: Optional[str] = _install_v2ray_binary(node)
        if err:
            return err
        return None

    if _try_install_script(node):
        return None

    err = _install_v2ray_binary(node)
    if err:
        return err
    return None


def deploy_v2ray(node: "Node") -> dict:
    """Full V2Ray deployment pipeline on the remote node."""
    admin_uuid: str = str(uuid.uuid4())
    result: dict = {
        "success": False,
        "error": "",
        "admin_uuid": admin_uuid,
    }
    logger.info(
        "部署V2Ray开始: node=%s(%s) admin_uuid=%s",
        node.name, node.id, admin_uuid[:8] + "***",
    )
    try:
        install_err: Optional[str] = _ensure_v2ray_installed(node)
        if install_err:
            result["error"] = install_err
            return result

        _, _, code = ssh_exec(
            node, "systemctl enable v2ray 2>&1", timeout=10
        )
        if code != 0:
            result["error"] = "启用 systemd 服务失败"
            return result

        svc_err: Optional[str] = _patch_v2ray_service(node)
        if svc_err:
            result["error"] = svc_err
            return result

        log_cmd: str = (
            "mkdir -p /var/log/v2ray"
            " && chown -R root:root /var/log/v2ray"
            " && chmod 755 /var/log/v2ray"
            " && chmod 644 /var/log/v2ray/*.log"
            " 2>/dev/null"
        )
        ssh_exec(node, log_cmd, timeout=10)

        vars_dict: dict[str, str] = _node_template_vars(
            node, user_uuid=admin_uuid
        )
        is_file_config: bool = node.config_path.endswith(".json")
        templates_dir_exists: bool = os.path.isdir(_TEMPLATE_DIR)

        if templates_dir_exists and not is_file_config:
            templates_used: Optional[str] = _deploy_from_templates(
                node, vars_dict
            )
            if templates_used is not None:
                result["error"] = templates_used
                return result
            restart_cmd: str = f"{_restart_cmd(node)} 2>&1"
            restart_out, restart_err, code = ssh_exec(
                node, restart_cmd
            )
            if code != 0:
                detail: str = (
                    restart_err or restart_out or ""
                ).strip()[-300:]
                result["error"] = (
                    f"启动 V2Ray 失败: {detail}" if detail
                    else "启动 V2Ray 失败"
                )
                return result
            node.is_active = True
            node.deployed_at = timezone.now()
            node.save(update_fields=["is_active", "deployed_at"])
            result["success"] = True
            result["template_uuids"] = [
                vars_dict.get("uuid", admin_uuid),
                vars_dict.get("uuid2", ""),
                vars_dict.get("uuid3", ""),
            ]
            return result

        inbound: dict = _build_inbound_entry(node, admin_uuid)

        if is_file_config:
            config: dict = {
                "log": {"loglevel": "warning"},
                "inbounds": [inbound],
                "outbounds": [
                    {"protocol": "freedom", "tag": "direct"}
                ],
                "api": {
                    "tag": "api",
                    "services": [
                        "HandlerService",
                        "LoggerService",
                        "StatsService",
                    ],
                },
                "stats": {},
                "policy": {
                    "levels": {
                        "0": {
                            "statsUserUplink": True,
                            "statsUserDownlink": True,
                        }
                    },
                    "system": {
                        "statsInboundUplink": True,
                        "statsInboundDownlink": True,
                    },
                },
                "routing": {
                    "rules": [
                        {
                            "type": "field",
                            "inboundTag": ["api"],
                            "outboundTag": "api",
                        },
                        {
                            "type": "field",
                            "outboundTag": "direct",
                            "ip": ["geoip:cn"],
                        },
                        {
                            "type": "field",
                            "ip": ["geoip:private"],
                            "outboundTag": "direct",
                        },
                    ]
                },
            }
            config.setdefault("inbounds", []).append({
                "listen": "127.0.0.1",
                "port": 10085,
                "protocol": "dokodemo-door",
                "settings": {"address": "127.0.0.1"},
                "tag": "api",
            })
            _, _, code = ssh_write_file(
                node,
                node.config_path,
                json.dumps(config, indent=2),
            )
            if code != 0:
                result["error"] = "写入配置文件失败"
                return result
        else:
            _, _, code = ssh_exec(
                node,
                f"mkdir -p {_shell_quote(node.config_path)}",
            )
            if code != 0:
                result["error"] = "创建配置目录失败"
                return result
            files: dict[str, str] = {
                "log.json": json.dumps(
                    {"loglevel": "warning"}, indent=2
                ),
                "inbounds.json": json.dumps(
                    {"inbounds": [inbound]}, indent=2
                ),
                "outbounds.json": json.dumps(
                    {
                        "outbounds": [
                            {
                                "protocol": "freedom",
                                "tag": "direct",
                            }
                        ]
                    },
                    indent=2,
                ),
                "dns.json": json.dumps(
                    {"dns": {}}, indent=2
                ),
                "routing.json": json.dumps(
                    {
                        "routing": {
                            "rules": [
                                {
                                    "type": "field",
                                    "inboundTag": ["api"],
                                    "outboundTag": "api",
                                },
                                {
                                    "type": "field",
                                    "outboundTag": "direct",
                                    "ip": ["geoip:cn"],
                                },
                                {
                                    "type": "field",
                                    "ip": ["geoip:private"],
                                    "outboundTag": "direct",
                                },
                            ]
                        }
                    },
                    indent=2,
                ),
                "api.json": json.dumps(
                    {
                        "api": {
                            "tag": "api",
                            "services": [
                                "HandlerService",
                                "LoggerService",
                                "StatsService",
                            ],
                        },
                        "stats": {},
                    },
                    indent=2,
                ),
                "policy.json": json.dumps(
                    {
                        "policy": {
                            "levels": {
                                "0": {
                                    "statsUserUplink": True,
                                    "statsUserDownlink": True,
                                }
                            },
                            "system": {
                                "statsInboundUplink": True,
                                "statsInboundDownlink": True,
                            },
                        }
                    },
                    indent=2,
                ),
                "api_inbound.json": json.dumps(
                    {
                        "inbounds": [
                            {
                                "listen": "127.0.0.1",
                                "port": 10085,
                                "protocol": "dokodemo-door",
                                "settings": {
                                    "address": "127.0.0.1"
                                },
                                "tag": "api",
                            }
                        ]
                    },
                    indent=2,
                ),
            }
            for name, content in files.items():
                remote: str = os.path.join(
                    node.config_path, name
                ).replace("\\", "/")
                _, _, code = ssh_write_file(
                    node, remote, content
                )
                if code != 0:
                    result["error"] = f"写入 {name} 失败"
                    return result

        restart_cmd = f"{_restart_cmd(node)} 2>&1"
        restart_out, restart_err, code = ssh_exec(
            node, restart_cmd
        )
        if code != 0:
            detail = (
                restart_err or restart_out or ""
            ).strip()[-300:]
            result["error"] = (
                f"启动 V2Ray 失败: {detail}" if detail
                else "启动 V2Ray 失败"
            )
            return result

        node.is_active = True
        node.deployed_at = timezone.now()
        node.save(update_fields=["is_active", "deployed_at"])
        result["success"] = True
        logger.info("部署V2Ray成功: node=%s", node.name)
    except Exception as e:
        result["error"] = str(e)
        logger.error(
            "部署V2Ray失败: node=%s error=%s",
            node.name, str(e),
        )
    return result


def collect_node_traffic(node: "Node") -> dict:
    """Collect traffic statistics from a remote V2Ray node."""
    logger.info("采集节点流量: node=%s", node.name)
    try:
        cmd: str = (
            "v2ray api stats -server=127.0.0.1:10085"
            " -json -reset 2>&1"
        )
        out, err, code = ssh_exec(node, cmd, timeout=30)
        if code != 0:
            msg: str = (err or out or "").strip()[-200:]
            logger.warning(
                "采集流量失败: node=%s error=%s",
                node.name, msg,
            )
            return {"error": f"v2ray api stats 失败: {msg}"}
        data: dict = json.loads(out)
    except json.JSONDecodeError as e:
        logger.error(
            "采集流量JSON解析失败: node=%s error=%s",
            node.name, str(e),
        )
        return {"error": f"JSON 解析失败: {e}"}
    except Exception as e:
        logger.error(
            "采集流量异常: node=%s error=%s",
            node.name, str(e),
        )
        return {"error": str(e)}

    result: dict = {}
    for stat in data.get("stat", []):
        name: str = stat.get("name", "")
        value: int = int(stat.get("value", 0))
        if value <= 0:
            continue
        m: Optional[re.Match] = re.match(
            r"^user>>>(.+?)@v2man\.dev>>>traffic>>>(uplink|downlink)$",
            name,
        )
        if not m:
            continue
        email_prefix: str = m.group(1)
        direction: str = m.group(2)
        if email_prefix not in result:
            result[email_prefix] = {"uplink": 0, "downlink": 0}
        result[email_prefix][direction] += value
    logger.info(
        "采集流量完成: node=%s 用户数=%s",
        node.name, len(result),
    )
    return result


def sync_users_to_node(node: "Node") -> Optional[str]:
    """Sync active users from database to remote node config."""
    User = get_user_model()
    now = timezone.now()

    users = User.objects.filter(
        plan__isnull=False,
        plan__nodes=node,
        is_active=True,
        expire_date__gt=now,
    ).exclude(plan__isnull=True).only(
        "uuid", "username", "traffic_used", "traffic_total"
    )
    user_list = list(users)
    logger.info(
        "同步用户到节点: node=%s 活跃用户数=%s",
        node.name, len(user_list),
    )

    if node.protocol in ("shadowsocks",):
        return None

    clients: list[dict] = []
    for u in user_list:
        if (
            u.traffic_total > 0
            and u.traffic_used >= u.traffic_total
        ):
            continue
        c: dict = {
            "email": f"{u.username}@v2man.dev",
            "level": 0,
        }
        if node.protocol in ("trojan", "hysteria2"):
            cfg: dict = node.config or {}
            c["password"] = (
                cfg.get("password") or str(u.uuid)[:16]
            )
        else:
            c["id"] = str(u.uuid)
            c["alterId"] = 0
        clients.append(c)

    if not clients:
        logger.warning(
            "同步用户到节点: node=%s 无活跃用户", node.name
        )
        return "没有活跃用户需要同步"

    inbound: dict = _build_inbound_entry(
        node, str(user_list[0].uuid)
    )
    inbound["settings"]["clients"] = clients
    content: str = json.dumps(
        {"inbounds": [inbound]}, indent=2
    )

    inb_path: str = _inbounds_path(node)
    _, _, code = ssh_write_file(node, inb_path, content)
    if code != 0:
        return "写入 inbounds.json 失败"

    r, _, c = ssh_exec(
        node,
        f"{_restart_cmd(node)} 2>&1; echo EXIT:$?",
        timeout=15,
    )
    exit_code: int = (
        int(r.split("EXIT:")[-1].strip())
        if "EXIT:" in r else 1
    )
    if exit_code != 0:
        logger.error(
            "同步后重启V2Ray失败: node=%s exit=%s output=%s",
            node.name, exit_code, (r or "")[:200],
        )
        return f"重启 V2Ray 失败: {(r or '')[:200]}"
    logger.info(
        "同步用户到节点成功: node=%s clients=%s",
        node.name, len(clients),
    )
    return None
