#!/usr/bin/env python3
"""Send a Slack message via the Web API (chat.postMessage).

Dependency-free (stdlib only). Reads the bot token from the SLACK_BOT_TOKEN
environment variable — never pass it on the command line.

Examples:
    python notify.py --channel "#dev-notify" --text "deploy done :rocket:"
    python notify.py --text "uses SLACK_DEFAULT_CHANNEL"
    python notify.py --channel "#dev-notify" --blocks-file payload.json
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://slack.com/api/chat.postMessage"


def post_message(token, channel, text=None, blocks=None):
    payload = {"channel": channel}
    if text is not None:
        payload["text"] = text
    if blocks is not None:
        payload["blocks"] = blocks
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Send a Slack message.")
    parser.add_argument(
        "--channel",
        default=os.environ.get("SLACK_DEFAULT_CHANNEL"),
        help="Target channel (#name or ID). Defaults to $SLACK_DEFAULT_CHANNEL.",
    )
    parser.add_argument("--text", help="Message text (fallback text when using blocks).")
    parser.add_argument(
        "--blocks-file",
        help="Path to a JSON file containing a Block Kit blocks array.",
    )
    args = parser.parse_args(argv)

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        parser.error("SLACK_BOT_TOKEN environment variable is not set.")
    if not args.channel:
        parser.error("No channel given (--channel or $SLACK_DEFAULT_CHANNEL).")

    blocks = None
    if args.blocks_file:
        with open(args.blocks_file, encoding="utf-8") as fh:
            blocks = json.load(fh)
    if args.text is None and blocks is None:
        parser.error("Provide --text and/or --blocks-file.")

    try:
        result = post_message(token, args.channel, text=args.text, blocks=blocks)
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"network error: {exc.reason}", file=sys.stderr)
        return 1

    if not result.get("ok"):
        # Common errors: not_in_channel, channel_not_found, invalid_auth
        print(f"slack error: {result.get('error', 'unknown')}", file=sys.stderr)
        return 1

    print(f"sent to {result.get('channel')} ts={result.get('ts')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
