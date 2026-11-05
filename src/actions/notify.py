import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

EXPLORER_BASE_URLS = {
    "sepolia": "https://sepolia.etherscan.io/address/",
    "mainnet": "https://etherscan.io/address/",
    "arbitrum-sepolia": "https://sepolia.arbiscan.io/address/",
    "optimism-sepolia": "https://sepolia-optimism.etherscan.io/address/",
    "base-sepolia": "https://sepolia.basescan.org/address/",
    "polygon-amoy": "https://amoy.polygonscan.com/address/",
}

def _detect_channel(webhook_url, user_channel):
    if user_channel:
        return user_channel.lower()
    if webhook_url:
        if "discord.com" in webhook_url or "discordapp.com" in webhook_url:
            return "discord"
        if "hooks.slack.com" in webhook_url:
            return "slack"
    return "generic"

def _format_discord_payload(title, message, status, contract, network, address, explorer_url):
    color = 0x22C55E if status == "success" else 0xEF4444  # Green or Red
    fields = []
    if contract:
        fields.append({"name": "Contract", "value": f"`{contract}`", "inline": True})
    if network:
        fields.append({"name": "Network", "value": f"`{network}`", "inline": True})
    if address:
        val = f"[{address}]({explorer_url})" if explorer_url else f"`{address}`"
        fields.append({"name": "Contract Address", "value": val, "inline": False})

    embed = {
        "title": title,
        "description": message or f"Web3 DevOps deployment finished with status: **{status.upper()}**",
        "color": color,
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "Web3 DevOps Toolkit"}
    }
    return {"username": "Web3 DevOps Bot", "embeds": [embed]}

def _format_slack_payload(title, message, status, contract, network, address, explorer_url):
    color = "#22c55e" if status == "success" else "#ef4444"
    fields = []
    if contract:
        fields.append({"title": "Contract", "value": contract, "short": True})
    if network:
        fields.append({"title": "Network", "value": network, "short": True})
    if address:
        val = f"<{explorer_url}|{address}>" if explorer_url else address
        fields.append({"title": "Contract Address", "value": val, "short": False})

    attachment = {
        "fallback": title,
        "color": color,
        "title": title,
        "text": message or f"Web3 DevOps deployment status: *{status.upper()}*",
        "fields": fields,
        "footer": "Web3 DevOps Toolkit",
        "ts": int(datetime.now(timezone.utc).timestamp())
    }
    return {"text": title, "attachments": [attachment]}

def _format_generic_payload(title, message, status, contract, network, address, explorer_url):
    return {
        "title": title,
        "message": message,
        "status": status,
        "contract": contract,
        "network": network,
        "address": address,
        "explorer_url": explorer_url,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def send_notification(params, pipeline_path=None, deployed_contracts=None, networks_config=None):
    webhook_url = (
        params.get('webhook_url')
        or os.environ.get('NOTIFICATION_WEBHOOK_URL')
        or os.environ.get('DISCORD_WEBHOOK_URL')
        or os.environ.get('SLACK_WEBHOOK_URL')
    )
    status = params.get('status', 'success')
    title = params.get('title', f"Web3 DevOps Alert: {status.title()}")
    message = params.get('message', '')
    contract = params.get('contract')
    network = params.get('network')
    address = params.get('address')

    # Resolve address from deployed contracts registry
    if not address and contract and deployed_contracts and contract in deployed_contracts:
        address = deployed_contracts[contract]
    elif not address and deployed_contracts and len(deployed_contracts) > 0:
        first_contract, first_address = next(iter(deployed_contracts.items()))
        if not contract:
            contract = first_contract
        address = first_address

    explorer_url = None
    if address and network and network in EXPLORER_BASE_URLS:
        explorer_url = f"{EXPLORER_BASE_URLS[network]}{address}"

    channel = _detect_channel(webhook_url, params.get('channel'))

    if channel == "discord":
        payload = _format_discord_payload(title, message, status, contract, network, address, explorer_url)
    elif channel == "slack":
        payload = _format_slack_payload(title, message, status, contract, network, address, explorer_url)
    else:
        payload = _format_generic_payload(title, message, status, contract, network, address, explorer_url)

    if not webhook_url:
        print(f"  [📢] Notification ({channel}): {title} (No webhook URL configured, skipping HTTP dispatch)")
        return {'status': 'success', 'notified': False, 'reason': 'No webhook configured'}

    print(f"  [📢] Sending {channel} notification to webhook...")
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Web3-DevOps-Toolkit/1.1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.getcode()
            if status_code in (200, 204):
                print(f"  [✅] Notification delivered successfully (HTTP {status_code}).")
                return {'status': 'success', 'notified': True, 'http_code': status_code}
            else:
                print(f"  [⚠️] Webhook returned status code: {status_code}")
                return {'status': 'failure', 'error': f'HTTP {status_code}'}
    except urllib.error.URLError as e:
        print(f"  [❌] Failed to deliver webhook notification: {e}")
        return {'status': 'failure', 'error': str(e)}
    except Exception as e:
        print(f"  [❌] Unexpected error sending notification: {e}")
        return {'status': 'failure', 'error': str(e)}
