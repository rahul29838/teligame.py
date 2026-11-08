#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra-Fast Multi-Task Earning & Micro-Job Telegram Bot (BDT Edition)
Converted 100% from PHP to Python (Single File Architecture)
Bot Username: @DailyErancashbot
Token: 9289209742:AAEhqPhTJYuq9eQGX11pea813-WIJIBHF_c
Admin ID: 8971711599
"""

import os
import re
import sys
import copy
import json
import uuid
import time
import base64
import hashlib
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import pyotp
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ----------------------------------------------------
# লগিং ও কনফিগারেশন
# ----------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "9289209742:AAEhqPhTJYuq9eQGX11pea813-WIJIBHF_c"
ADMIN_ID = 8971711599
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

# কনকারেন্সি রক্ষার জন্য ফাইল লক
db_lock = asyncio.Lock()

# ----------------------------------------------------
# বাংলা সংখ্যা ও টাকা ফরম্যাট হেল্পার
# ----------------------------------------------------
def to_bangla_num(num_str: Any) -> str:
    en_digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    bn_digits = ["০", "১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯"]
    s = str(num_str)
    for en, bn in zip(en_digits, bn_digits):
        s = s.replace(en, bn)
    return s

def from_bangla_num(num_str: str) -> str:
    en_digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    bn_digits = ["০", "১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯"]
    s = str(num_str)
    for en, bn in zip(en_digits, bn_digits):
        s = s.replace(bn, en)
    return s

def format_taka(amount: Any, use_bangla_digits: bool = True) -> str:
    try:
        val = round(float(amount), 2)
    except (ValueError, TypeError):
        val = 0.0
    
    if val.is_integer():
        formatted = f"{int(val)}"
    else:
        formatted = f"{val:.2f}"
    
    if use_bangla_digits:
        return f"{to_bangla_num(formatted)} ৳"
    return f"{formatted} ৳"

# ----------------------------------------------------
# ডাটাবেজ মডেল ও ফাইল অপারেশন
# ----------------------------------------------------
DEFAULT_DATA: Dict[str, Any] = {
    "settings": {
        "bdt_migrated": True,
        "bot_status": "ON",
        "bot_username": "EasyCashEarn_bot",
        "welcome_msg": "স্বাগতম *first_name* আমাদের আর্নিং প্ল্যাটফর্মে!\n\nআপনার কাজ সম্পন্ন করে এবং বন্ধুদের রেফার করে সরাসরি বাংলা টাকায় (৳) আয় করুন। নিচের অপশনগুলো থেকে আপনার পছন্দের মেনু সিলেক্ট করুন:",
        "welcome_msg_id": None,
        "welcome_chat_id": None,
        "welcome_entities": [],
        "proof_channel": "",
        "withdraw_status": "ON",
        "min_withdraw": 50.0,
        "withdraw_charge": 5.0,
        "usd_to_bdt": 120.0,
        "default_task_pass": "Pass@2026#Secure",
        "referral_mode": "commission",
        "ref_direct_bonus": 5.0,
        "ref_commission_pct": 20.0,
        "ig_mode": "2fa",
        "fb_mode": "cookies",
        "rates": {
            "instagram": 10.0,
            "facebook": 12.0,
            "gmail": 8.0,
            "admin_file": 1200.0,
        },
        "task_status": {
            "instagram": "ON",
            "facebook": "ON",
            "gmail": "ON",
            "admin_file": "ON",
        },
        "videos": {
            "instagram": "",
            "facebook": "",
            "gmail": "",
        },
        "premium_emojis": {
            "btn_balance": {"char": "💰", "id": ""},
            "btn_task": {"char": "💼", "id": ""},
            "btn_withdraw": {"char": "💳", "id": ""},
            "btn_refer": {"char": "👥", "id": ""},
            "btn_new": {"char": "🎬", "id": ""},
            "btn_lang": {"char": "🌐", "id": ""},
            "btn_leaderboard": {"char": "🏆", "id": ""},
            "btn_back": {"char": "🔙", "id": ""},

            "btn_channel": {"char": "📢", "id": ""},
            "btn_verify": {"char": "✅", "id": ""},

            "btn_ig": {"char": "📸", "id": ""},
            "btn_fb": {"char": "📘", "id": ""},
            "btn_gmail": {"char": "📧", "id": ""},
            "btn_admin_file": {"char": "📁", "id": ""},
            "btn_2fa_key": {"char": "🔐", "id": ""},
            "btn_task_submit": {"char": "✅", "id": ""},
            "btn_task_cancel": {"char": "❌", "id": ""},
            "btn_ig_file": {"char": "📸", "id": ""},
            "btn_fb_file": {"char": "📘", "id": ""},
            "btn_gmail_file": {"char": "📧", "id": ""},

            "btn_new_ig": {"char": "📸", "id": ""},
            "btn_new_fb": {"char": "📘", "id": ""},
            "btn_new_gmail": {"char": "📧", "id": ""},
            "btn_new_close": {"char": "❌", "id": ""},
            "btn_lang_bn": {"char": "🇧🇩", "id": ""},
            "btn_lang_en": {"char": "🇺🇸", "id": ""},
            "btn_binance": {"char": "🟡", "id": ""},

            "task_ic_user": {"char": "👤", "id": ""},
            "task_ic_pass": {"char": "🔑", "id": ""},
            "task_ic_cookie": {"char": "🍪", "id": ""},
            "task_ic_2fa": {"char": "🔐", "id": ""},
            "task_ic_money": {"char": "💰", "id": ""},

            "ntf_ig": {"char": "📸", "id": ""},
            "ntf_fb": {"char": "📘", "id": ""},
            "ntf_gmail": {"char": "📧", "id": ""},
            "ntf_wait": {"char": "⏳", "id": ""},
            "ntf_no_bal": {"char": "⚠️", "id": ""},
            "ntf_wd_info": {"char": "💳", "id": ""},
            "ntf_wd_charge": {"char": "⚡", "id": ""},
            "ntf_wd_off": {"char": "🚫", "id": ""},
            "ntf_wd_done": {"char": "✅", "id": ""},
            "ntf_task_off": {"char": "🛑", "id": ""},
            "ntf_no_task": {"char": "📭", "id": ""},
            "ntf_cancel": {"char": "❌", "id": ""},
            "ntf_force_join": {"char": "📢", "id": ""},
            "ntf_approved": {"char": "🎉", "id": ""},
            "ntf_rejected": {"char": "❌", "id": ""},

            "bal_ic_user": {"char": "👨‍💻", "id": ""},
            "bal_ic_id": {"char": "🆔", "id": ""},
            "bal_ic_main": {"char": "💰", "id": ""},
            "bal_ic_earned": {"char": "💲", "id": ""},
            "bal_ic_pend": {"char": "🔄", "id": ""},
            "bal_ic_done": {"char": "✅", "id": ""},
            "bal_ic_ref": {"char": "👥", "id": ""},

            "ref_ic_link": {"char": "🔗", "id": ""},
            "ref_ic_count": {"char": "👥", "id": ""},
            "ref_ic_income": {"char": "💰", "id": ""},
            "ref_ic_reward": {"char": "🎁", "id": ""},

            "lb_rank_1": {"char": "🥇", "id": ""},
            "lb_rank_2": {"char": "🥈", "id": ""},
            "lb_rank_3": {"char": "🥉", "id": ""},
            "lb_rank_other": {"char": "🎖️", "id": ""},
        },
        "btn_colors": {
            "balance": "primary",
            "task": "success",
            "withdraw": "danger",
            "refer": "primary",
            "new": "primary",
            "lang": "primary",
            "leaderboard": "primary",
            "back": "danger",
            "ig": "primary",
            "fb": "primary",
            "gmail": "primary",
            "admin_file": "success",
            "2fa_key": "primary",
            "task_submit": "success",
            "task_cancel": "danger",
            "ig_file": "primary",
            "fb_file": "primary",
            "gmail_file": "primary",
            "lang_bn": "success",
            "lang_en": "primary",
            "binance": "primary",
            "channel": "success",
            "verify": "primary",
        },
    },
    "channels": [],
    "users": {},
    "tasks": {},
    "admin_deals": {},
    "withdrawals": {},
    "user_states": {},
    "admin_state": {},
}

def deep_merge(source: dict, destination: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            if isinstance(node, dict):
                deep_merge(value, node)
            else:
                destination[key] = copy.deepcopy(value)
        else:
            if key not in destination:
                destination[key] = copy.deepcopy(value)
    return destination

def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        data = copy.deepcopy(DEFAULT_DATA)
        save_data(data)
        return data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return copy.deepcopy(DEFAULT_DATA)
        merged = deep_merge(DEFAULT_DATA, data)
        merged["settings"]["bot_username"] = "EasyCashEarn_bot"
        return merged
    except Exception as e:
        logger.error(f"Error loading JSON data: {e}")
        return copy.deepcopy(DEFAULT_DATA)

def save_data(data: dict):
    tmp_file = DATA_FILE + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, DATA_FILE)
    except Exception as e:
        logger.error(f"Error saving JSON data: {e}")

# ----------------------------------------------------
# TOTP (2FA) জেনারেটর
# ----------------------------------------------------
def generate_2fa_otp(secret: str) -> Optional[str]:
    try:
        clean_secret = re.sub(r"[^A-Za-z2-7]", "", secret.strip().upper())
        if len(clean_secret) < 8:
            return None
        totp = pyotp.TOTP(clean_secret)
        return totp.now()
    except Exception as e:
        logger.warning(f"TOTP generation failed for secret: {e}")
        return None

# ----------------------------------------------------
# ইমোজি ও স্টাইল বাটন হেল্পার
# ----------------------------------------------------
def format_emoji_badge(item: Any) -> str:
    if isinstance(item, dict):
        if item.get("id"):
            return f"💎 [ID: {item['id']}]"
        if item.get("char"):
            return item["char"]
    return "[খালি]"

def get_emoji_info(key: str, db: dict) -> dict:
    pe = db.get("settings", {}).get("premium_emojis", {})
    e = None
    if key in pe:
        e = pe[key]
    elif f"btn_{key}" in pe:
        e = pe[f"btn_{key}"]
    
    if isinstance(e, dict):
        return {"id": e.get("id", ""), "char": e.get("char", "")}
    elif isinstance(e, str):
        return {"id": "", "char": e}
    return {"id": "", "char": ""}

def render_emoji_text(key: str, db: dict, default_char: str = "") -> str:
    info = get_emoji_info(key, db)
    if info["id"]:
        c = info["char"] if info["char"] else (default_char if default_char else "⭐")
        return f'<tg-emoji emoji-id="{info["id"]}">{c}</tg-emoji>'
    return info["char"] if info["char"] else default_char

def create_styled_button_text(title: str, key: str, db: dict) -> str:
    clean_key = key[4:] if key.startswith("btn_") else key
    emoji_key = f"btn_{clean_key}" if f"btn_{clean_key}" in db.get("settings", {}).get("premium_emojis", {}) else key
    info = get_emoji_info(emoji_key, db)
    char = info.get("char", "")
    if char:
        return f"{char} {title}"
    return title

# ----------------------------------------------------
# ভাষা ও মেসেজ ডিকশনারি
# ----------------------------------------------------
def get_lang_text(key: str, lang: str = "bn", replaces: Optional[dict] = None, db: Optional[dict] = None) -> str:
    if replaces is None:
        replaces = {}
    
    e_wait = render_emoji_text("ntf_wait", db, "⏳") if db else "⏳"
    e_no_bal = render_emoji_text("ntf_no_bal", db, "⚠️") if db else "⚠️"
    e_wd_info = render_emoji_text("ntf_wd_info", db, "💳") if db else "💳"
    e_wd_chg = render_emoji_text("ntf_wd_charge", db, "⚡") if db else "⚡"
    e_wd_off = render_emoji_text("ntf_wd_off", db, "🚫") if db else "🚫"
    e_wd_done = render_emoji_text("ntf_wd_done", db, "✅") if db else "✅"
    e_cancel = render_emoji_text("ntf_cancel", db, "❌") if db else "❌"
    e_force = render_emoji_text("ntf_force_join", db, "📢") if db else "📢"
    e_new = render_emoji_text("btn_new", db, "🎬") if db else "🎬"
    e_task = render_emoji_text("btn_task", db, "💼") if db else "💼"

    lang_data = {
        "bn": {
            "menu_balance": "ব্যালেন্স",
            "menu_task": "কাজ",
            "menu_withdraw": "উইথড্রল",
            "menu_refer": "রেফার",
            "menu_new": "আমি নতুন",
            "menu_lang": "ভাষা (Language)",
            "menu_leaderboard": "লিডারবোর্ড",
            "menu_back": "মেনু ফিরে যান",
            "force_verify_btn": "ভেরিফাই মেম্বারশিপ",
            "cancel_action": f"{e_cancel} <b>অ্যাকশন বাতিল করা হয়েছে।</b>",
            "lang_changed": "✅ ভাষা সফলভাবে বাংলায় পরিবর্তন করা হয়েছে!",
            "select_task": f"{e_task} <b>আপনার পছন্দের কাজ সিলেক্ট করুন:</b>\n(যেকোনো কাজ শুরু করতে নিচের বাটনে ক্লিক করুন)",
            "withdraw_off": f"{e_wd_off} <b>বর্তমানে উইথড্রল সিস্টেম সাময়িকভাবে বন্ধ আছে! পরবর্তীতে চেষ্টা করুন।</b>",
            "withdraw_info": f"{e_wd_info} <b>উইথড্রল ও পেমেন্ট নোটিশ</b>\n\n🔹 ন্যূনতম উইথড্র: <b>{{min}}</b>\n🔹 আপনার বর্তমান ব্যালেন্স: <b>{{bal}}</b>\n{e_wd_chg} <b>উইথড্র চার্জ:</b> প্রতি উইথড্রতে বাংলা টাকায় <b>{{charge}}</b> চার্জ কাটা হবে।\n\nউইথড্র করতে নিচের বাটনে চাপ দিন:",
            "enter_bep20": f"{e_wd_info} <b>আপনার Binance (BEP20) অ্যাড্রেস অথবা পেমেন্ট একাউন্ট দিন:</b>\n(বাতিল করতে কাজ বাতিল বাটনে চাপুন)",
            "enter_wd_amt": f"💵 <b>আপনি কত টাকা (৳) উইথড্র করতে চান তা লিখুন:</b>\n🔹 ন্যূনতম উইথড্র: <b>{{min}}</b>\n{e_wd_chg} চার্জ কাটবে: <b>{{charge}}</b>\n(বাতিল করতে কাজ বাতিল বাটনে চাপুন)",
            "invalid_amt": f"{e_no_bal} <b>আপনার পর্যাপ্ত ব্যালেন্স নেই অথবা সঠিক পরিমাণ লেখেননি!</b>\n(ন্যূনতম উইথড্র <b>{{min}}</b> এবং আপনার একাউন্টে পর্যাপ্ত ব্যালেন্স থাকতে হবে)",
            "wd_success": f"{e_wd_done} <b>আপনার উইথড্রল রিকোয়েস্ট সফলভাবে জমা নেওয়া হয়েছে!</b>\n\n💵 উইথড্র পরিমাণ: <b>{{amt}}</b>\n{e_wd_chg} চার্জ কাটা হয়েছে: <b>{{charge}}</b>\n💰 আপনি পাবেন: <b>{{net}}</b>\n\n{e_wait} অনুগ্রহ করে অপেক্ষা করুন, এডমিন যাচাই করে পেমেন্ট সম্পন্ন করবে।",
            "new_help_select": f"{e_new} <b>কাজের ভিডিও টিউটোরিয়াল:</b>\nআপনি কোন কাজের ভিডিও দেখতে চান তা নিচের বাটন থেকে নির্বাচন করুন:",
            "no_video": f"{e_no_bal} <b>আপাতত কোনো ভিডিও যুক্ত করা হয়নি। অনুগ্রহ করে অপেক্ষা করুন।</b>",
            "task_sub_done": f"{e_wait} <b>আপনার কাজটি সফলভাবে জমা নেওয়া হয়েছে!</b>\n\nঅনুগ্রহ করে অপেক্ষা করুন। এডমিন আপনার কাজটি যাচাই করে একাউন্টে টাকা যোগ করে দেবে।"
        },
        "en": {
            "menu_balance": "Balance",
            "menu_task": "Tasks",
            "menu_withdraw": "Withdrawal",
            "menu_refer": "Referral",
            "menu_new": "I am New",
            "menu_lang": "Language",
            "menu_leaderboard": "Leaderboard",
            "menu_back": "Back to Menu",
            "force_verify_btn": "Verify Membership",
            "cancel_action": f"{e_cancel} <b>Action cancelled.</b>",
            "lang_changed": "✅ Language switched to English successfully!",
            "select_task": f"{e_task} <b>Select a Task to Start Working:</b>\n(Click on any button below)",
            "withdraw_off": f"{e_wd_off} <b>Withdrawals are currently offline! Please try again later.</b>",
            "withdraw_info": f"{e_wd_info} <b>Withdrawal Information</b>\n\n🔹 Minimum Withdraw: <b>{{min}}</b>\n🔹 Your Balance: <b>{{bal}}</b>\n{e_wd_chg} <b>Withdraw Charge:</b> <b>{{charge}}</b> will be deducted as fee.\n\nClick below to request withdrawal:",
            "enter_bep20": f"{e_wd_info} <b>Send your Binance (BEP20) Address / Account Info:</b>",
            "enter_wd_amt": f"💵 <b>Enter withdrawal amount in BDT (৳):</b>\n🔹 Minimum: <b>{{min}}</b>\n{e_wd_chg} Fee: <b>{{charge}}</b>",
            "invalid_amt": f"{e_no_bal} <b>Insufficient balance or invalid amount!</b>\n(Minimum withdrawal is <b>{{min}}</b> and you must have sufficient balance)",
            "wd_success": f"{e_wd_done} <b>Your withdrawal request has been submitted!</b>\n\n💵 Amount: <b>{{amt}}</b>\n{e_wd_chg} Charge: <b>{{charge}}</b>\n💰 Receivable: <b>{{net}}</b>\n\n{e_wait} Please wait for admin review.",
            "new_help_select": f"{e_new} <b>Work Video Tutorials:</b>\nSelect the task tutorial you wish to watch:",
            "no_video": f"{e_no_bal} <b>No tutorial video added yet. Please wait for an update.</b>",
            "task_sub_done": f"{e_wait} <b>Task submitted successfully!</b>\n\nPlease wait for admin review. Funds will be credited to your balance soon."
        }
    }

    text = lang_data.get(lang, {}).get(key, lang_data["bn"].get(key, key))
    for k, v in replaces.items():
        text = text.replace(f"{{{k}}}", str(v))
    return text

# ----------------------------------------------------
# চ্যানেল পার্সার ও ফোর্স-জয়েন চেকার
# ----------------------------------------------------
def parse_channel_input(channel_input: str) -> dict:
    inp = channel_input.strip()
    url = inp
    chat_id = ""

    if re.match(r"^(?:https?://)?t\.me/(\+|joinchat/)([a-zA-Z0-9_-]+)", inp, re.IGNORECASE):
        url = inp if inp.startswith("http") else f"https://{inp}"
        chat_id = ""
    elif re.match(r"^-100\d+$", inp):
        chat_id = inp
        url = "https://t.me/"
    else:
        m = re.match(r"^(?:https?://)?(?:t\.me/|@)?([a-zA-Z0-9_]{4,})", inp, re.IGNORECASE)
        if m:
            uname = m.group(1)
            url = f"https://t.me/{uname}"
            chat_id = f"@{uname}"
        else:
            clean = inp.lstrip("@")
            url = inp if inp.startswith("http") else f"https://t.me/{clean}"
            chat_id = inp if inp.startswith("@") else f"@{clean}"

    return {"url": url, "chat_id": chat_id}

async def check_user_in_channel(bot: Any, chat_identifier: str, user_id: int) -> bool:
    if not chat_identifier:
        return True
    
    m = re.match(r"^(?:https?://)?t\.me/([a-zA-Z0-9_]+)$", chat_identifier, re.IGNORECASE)
    if m:
        chat_identifier = f"@{m.group(1)}"

    try:
        member = await bot.get_chat_member(chat_id=chat_identifier, user_id=user_id)
        valid_statuses = [
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.RESTRICTED,
        ]
        return member.status in valid_statuses
    except Exception as e:
        logger.warning(f"Error checking channel membership for {user_id} in {chat_identifier}: {e}")
        return False

async def get_unjoined_channels(bot: Any, user_id: int, channels: list) -> list:
    if not channels or not isinstance(channels, list):
        return []
    unjoined = []
    for index, ch in enumerate(channels):
        raw_target = ch.get("url") or ch.get("chat_id") or ""
        parsed = parse_channel_input(raw_target)
        target_chat_id = ch.get("chat_id") if (ch.get("chat_id") and not ch.get("chat_id").startswith("http")) else parsed["chat_id"]
        valid_url = ch.get("url") or parsed["url"]

        if target_chat_id:
            is_joined = await check_user_in_channel(bot, target_chat_id, user_id)
            if not is_joined:
                unjoined.append({
                    "index": index,
                    "title": ch.get("title") or "Join Channel",
                    "url": valid_url,
                    "chat_id": target_chat_id
                })
    return unjoined

def get_force_join_message(channels: list, db: dict, lang: str = "bn") -> str:
    e_force = render_emoji_text("ntf_force_join", db, "📢")
    if lang == "en":
        txt = (
            f"{e_force} <b>You must join our official channels to use this bot:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for i, ch in enumerate(channels, start=1):
            title = ch.get("title") or f"Official Channel {i}"
            url = ch.get("url", "")
            txt += f'👉 <b>Channel {i}:</b> <a href="{url}">{title}</a>\n'
        txt += (
            "\n━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <i>Join all channels and click the <b>Verify</b> button below.</i>"
        )
    else:
        txt = (
            f"{e_force} <b>বটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for i, ch in enumerate(channels, start=1):
            title = ch.get("title") or f"অফিসিয়াল চ্যানেল {i}"
            url = ch.get("url", "")
            txt += f'👉 <b>চ্যানেল {to_bangla_num(i)}:</b> <a href="{url}">{title}</a>\n'
        txt += (
            "\n━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <i>সবগুলো চ্যানেলে জয়েন করে নিচের <b>ভেরিফাই</b> বাটনে চাপ দিন।</i>"
        )
    return txt

def generate_force_join_keyboard(channels: list, db: dict, lang: str = "bn") -> InlineKeyboardMarkup:
    rows = []
    for i, ch in enumerate(channels, start=1):
        title = ch.get("title") or f"Channel {i}"
        btn_text = create_styled_button_text(title, "btn_channel", db)
        rows.append([InlineKeyboardButton(btn_text, url=ch.get("url", ""))])
    
    v_text = get_lang_text("force_verify_btn", lang, {}, db)
    verify_label = create_styled_button_text(v_text, "btn_verify", db)
    rows.append([InlineKeyboardButton(verify_label, callback_data="verify_join")])
    return InlineKeyboardMarkup(rows)

# ----------------------------------------------------
# কীবোর্ড লেআউট জেনারেটর
# ----------------------------------------------------
def get_user_main_menu_keyboard(user_id: int, db: dict) -> ReplyKeyboardMarkup:
    u_key = str(user_id)
    lang = db.get("users", {}).get(u_key, {}).get("lang", "bn")
    
    keyboard = [
        [
            KeyboardButton(create_styled_button_text(get_lang_text("menu_balance", lang), "balance", db)),
            KeyboardButton(create_styled_button_text(get_lang_text("menu_task", lang), "task", db)),
        ],
        [
            KeyboardButton(create_styled_button_text(get_lang_text("menu_withdraw", lang), "withdraw", db)),
            KeyboardButton(create_styled_button_text(get_lang_text("menu_refer", lang), "refer", db)),
        ],
        [
            KeyboardButton(create_styled_button_text(get_lang_text("menu_new", lang), "new", db)),
            KeyboardButton(create_styled_button_text(get_lang_text("menu_lang", lang), "lang", db)),
        ],
        [
            KeyboardButton(create_styled_button_text(get_lang_text("menu_leaderboard", lang), "leaderboard", db))
        ],
    ]

    if str(user_id) == str(ADMIN_ID):
        keyboard.append([KeyboardButton("⚙️ অ্যাডমিন প্যানেল")])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_task_menu_keyboard(user_id: int, db: dict) -> ReplyKeyboardMarkup:
    u_key = str(user_id)
    lang = db.get("users", {}).get(u_key, {}).get("lang", "bn")
    rates = db.get("settings", {}).get("rates", {})
    status = db.get("settings", {}).get("task_status", {
        "instagram": "ON", "facebook": "ON", "gmail": "ON", "admin_file": "ON"
    })
    is_bn = (lang == "bn")
    keyboard = []

    if status.get("instagram", "ON") == "ON":
        title = f"Instagram ({format_taka(rates.get('instagram', 10.0), is_bn)})"
        keyboard.append([KeyboardButton(create_styled_button_text(title, "ig", db))])
    
    if status.get("facebook", "ON") == "ON":
        title = f"Facebook ({format_taka(rates.get('facebook', 12.0), is_bn)})"
        keyboard.append([KeyboardButton(create_styled_button_text(title, "fb", db))])
    
    if status.get("gmail", "ON") == "ON":
        title = f"Gmail ({format_taka(rates.get('gmail', 8.0), is_bn)})"
        keyboard.append([KeyboardButton(create_styled_button_text(title, "gmail", db))])
    
    if status.get("admin_file", "ON") == "ON":
        prefix = "এডমিন ফাইল" if is_bn else "Admin Deal"
        title = f"{prefix} ({format_taka(rates.get('admin_file', 1200.0), is_bn)})"
        keyboard.append([KeyboardButton(create_styled_button_text(title, "admin_file", db))])

    back_text = get_lang_text("menu_back", lang)
    keyboard.append([KeyboardButton(create_styled_button_text(back_text, "back", db))])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_reply_keyboard(db: dict, lang: str = "bn") -> ReplyKeyboardMarkup:
    txt = "Cancel Task" if lang == "en" else "কাজ বাতিল"
    btn = KeyboardButton(create_styled_button_text(txt, "task_cancel", db))
    return ReplyKeyboardMarkup([[btn]], resize_keyboard=True)

def get_submit_task_reply_keyboard(db: dict, lang: str = "bn") -> ReplyKeyboardMarkup:
    sub_txt = "Submit Task" if lang == "en" else "টাস্ক সাবমিট"
    can_txt = "Cancel Task" if lang == "en" else "কাজ বাতিল"
    return ReplyKeyboardMarkup([
        [KeyboardButton(create_styled_button_text(sub_txt, "task_submit", db))],
        [KeyboardButton(create_styled_button_text(can_txt, "task_cancel", db))],
    ], resize_keyboard=True)

def get_2fa_key_reply_keyboard(db: dict, lang: str = "bn") -> ReplyKeyboardMarkup:
    can_txt = "Cancel Task" if lang == "en" else "কাজ বাতিল"
    return ReplyKeyboardMarkup([
        [KeyboardButton(create_styled_button_text("2FA Key", "2fa_key", db))],
        [KeyboardButton(create_styled_button_text(can_txt, "task_cancel", db))],
    ], resize_keyboard=True)

def get_admin_keyboard(bot_status: str) -> ReplyKeyboardMarkup:
    status_text = "🔴 বটের কাজ বন্ধ করুন" if bot_status == "ON" else "🟢 বট চালু করুন"
    return ReplyKeyboardMarkup([
        [KeyboardButton("📋 অল টাস্ক (Review)"), KeyboardButton("🛑 টাস্ক অন/অফ")],
        [KeyboardButton("📁 এডমিন ডিল ফাইল"), KeyboardButton("💳 উইথড্রল রিকোয়েস্ট")],
        [KeyboardButton("💲 অল রেট (Set Rates)"), KeyboardButton("⚙️ উইথড্রল সেটিংস")],
        [KeyboardButton("🔐 অল টাস্ক পাসওয়ার্ড"), KeyboardButton("🎁 রেফারেল বোনাস মোড")],
        [KeyboardButton("🎬 নতুনদের জন্য ভিডিও"), KeyboardButton("📢 পেমেন্ট প্রুফ চ্যানেল")],
        [KeyboardButton("📝 ওয়েলকাম মেসেজ"), KeyboardButton("📢 অল ইউজার মেসেজ")],
        [KeyboardButton("⭐ প্রিমিয়াম ইমোজি"), KeyboardButton("🎨 কালারিং প্যানেল")],
        [KeyboardButton("➕ চ্যানেল যোগ করুন"), KeyboardButton("➖ চ্যানেল রিমুভ")],
        [KeyboardButton("👥 মোট ইউজার"), KeyboardButton(status_text)],
        [KeyboardButton("🔙 মেইন মেনুতে ফিরুন")]
    ], resize_keyboard=True)

def get_cancel_inline_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ বাতিল (Cancel)", callback_data="cancel_admin_action")]
    ])

def build_task_status_inline_keyboard(db: dict) -> InlineKeyboardMarkup:
    st = db.get("settings", {}).get("task_status", {
        "instagram": "ON", "facebook": "ON", "gmail": "ON", "admin_file": "ON"
    })
    ig_mode = db.get("settings", {}).get("ig_mode", "2fa")
    fb_mode = db.get("settings", {}).get("fb_mode", "cookies")

    labels = {
        "instagram": "📸 Instagram কাজ",
        "facebook": "📘 Facebook কাজ",
        "gmail": "📧 Gmail কাজ",
        "admin_file": "📁 এডমিন ফাইল কাজ",
    }
    rows = []
    for k, title in labels.items():
        is_on = st.get(k, "ON") == "ON"
        badge = "🟢 চালু (ON)" if is_on else "🔴 বন্ধ (OFF)"
        rows.append([
            InlineKeyboardButton(f"{title} : {badge}", callback_data=f"adm_tog_task_{k}")
        ])

    ig_badge = "🍪 Cookies Mode" if ig_mode == "cookies" else "🔐 2FA Mode"
    fb_badge = "🔐 2FA Mode" if fb_mode == "2fa" else "🍪 Cookies Mode"

    rows.append([InlineKeyboardButton(f"📸 IG মোড পরিবর্তন: [{ig_badge}]", callback_data="adm_tog_ig_mode")])
    rows.append([InlineKeyboardButton(f"📘 FB মোড পরিবর্তন: [{fb_badge}]", callback_data="adm_tog_fb_mode")])
    rows.append([InlineKeyboardButton("❌ Close", callback_data="cancel_admin_action")])

    return InlineKeyboardMarkup(rows)

# ----------------------------------------------------
# ওয়েলকাম মেসেজ ও ইউজার রেজিস্ট্রেশন
# ----------------------------------------------------
async def send_welcome_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, first_name: str, db: dict):
    keyboard = get_user_main_menu_keyboard(user_id, db)
    raw_msg = db.get("settings", {}).get("welcome_msg") or "স্বাগতম *first_name*!"
    formatted_name = f"<b>{first_name}</b>"

    if "*first_name*" in raw_msg:
        text_to_send = raw_msg.replace("*first_name*", formatted_name)
    elif "**first_name**" in raw_msg:
        text_to_send = raw_msg.replace("**first_name**", formatted_name)
    else:
        text_to_send = f"👤 {formatted_name},\n\n{raw_msg}"

    await context.bot.send_message(
        chat_id=chat_id,
        text=text_to_send,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )

async def register_user(context: ContextTypes.DEFAULT_TYPE, db: dict, user_id: int, name: str, username: str, ref_by: Optional[str] = None):
    u_key = str(user_id)
    if u_key not in db["users"]:
        db["users"][u_key] = {
            "id": user_id,
            "name": name,
            "username": username,
            "balance": 0.00,
            "total_earned": 0.00,
            "referrals": 0,
            "ref_income": 0.00,
            "ref_by": None,
            "tasks_completed": 0,
            "lang": "bn",
            "is_verified": False,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if ref_by and str(ref_by) in db["users"] and str(ref_by) != u_key:
            ref_key = str(ref_by)
            db["users"][u_key]["ref_by"] = ref_by
            db["users"][ref_key]["referrals"] = db["users"][ref_key].get("referrals", 0) + 1

            e_app = render_emoji_text("ntf_approved", db, "🎉")
            if db.get("settings", {}).get("referral_mode") == "direct":
                bonus = float(db.get("settings", {}).get("ref_direct_bonus", 5.0))
                db["users"][ref_key]["balance"] += bonus
                db["users"][ref_key]["ref_income"] += bonus
                db["users"][ref_key]["total_earned"] += bonus
                bonus_str = format_taka(bonus)
                try:
                    await context.bot.send_message(
                        chat_id=int(ref_by),
                        text=f"{e_app} <b>নতুন রেফারেল বোনাস!</b>\nআপনার রেফারেল লিংকে একজন নতুন ইউজার যুক্ত হয়েছেন। আপনি পেয়েছেন <b>{bonus_str}</b>!",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            else:
                try:
                    await context.bot.send_message(
                        chat_id=int(ref_by),
                        text=f"{e_app} <b>নতুন রেফারেল!</b>\nআপনার লিংকে একজন ইউজার যুক্ত হয়েছেন। তিনি কাজ সম্পন্ন করলেই আপনি কমিশন পাবেন!",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
        save_data(db)
    else:
        changed = False
        if db["users"][u_key].get("name") != name:
            db["users"][u_key]["name"] = name
            changed = True
        if db["users"][u_key].get("username") != username:
            db["users"][u_key]["username"] = username
            changed = True
        if changed:
            save_data(db)

# ----------------------------------------------------
# লিডারবোর্ড লজিক
# ----------------------------------------------------
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE, db: dict):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    u_key = str(user_id)
    lang = db.get("users", {}).get(u_key, {}).get("lang", "bn")

    users_list = list(db.get("users", {}).items())
    users_list.sort(key=lambda x: float(x[1].get("total_earned", 0.0)), reverse=True)

    e_r1 = render_emoji_text("lb_rank_1", db, "🥇")
    e_r2 = render_emoji_text("lb_rank_2", db, "🥈")
    e_r3 = render_emoji_text("lb_rank_3", db, "🥉")
    e_ro = render_emoji_text("lb_rank_other", db, "🎖️")

    text = "🏆 <b>Top 10 Earners Leaderboard:</b>\n" if lang == "en" else "🏆 <b>টপ ১০ লিডারবোর্ড (Top 10 Earners):</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n"

    my_rank = "10+"
    for rank, (uid, udata) in enumerate(users_list, start=1):
        if str(uid) == u_key:
            my_rank = str(rank)
        
        if rank <= 10:
            uname = udata.get("name", "User")
            earned = f"{float(udata.get('total_earned', 0)):.2f} BDT" if lang == "en" else format_taka(udata.get("total_earned", 0))
            refs = f"{int(udata.get('referrals', 0))} Refs" if lang == "en" else f"{to_bangla_num(udata.get('referrals', 0))} জন"

            if rank == 1:
                icon = e_r1
            elif rank == 2:
                icon = e_r2
            elif rank == 3:
                icon = e_r3
            else:
                icon = e_ro

            rank_str = str(rank) if lang == "en" else to_bangla_num(rank)
            text += f"<b>#{rank_str}</b> {icon} <b>{uname}</b>\n"
            text += f"   └ 💰 <b>{earned}</b> | 👥 <b>{refs}</b>\n"

    user_info = db.get("users", {}).get(u_key, {})
    my_earned = f"{float(user_info.get('total_earned', 0)):.2f} BDT" if lang == "en" else format_taka(user_info.get("total_earned", 0))
    my_refs = f"{int(user_info.get('referrals', 0))} Users" if lang == "en" else f"{to_bangla_num(user_info.get('referrals', 0))} জন"
    my_rank_str = my_rank if lang == "en" else to_bangla_num(my_rank)

    text += "━━━━━━━━━━━━━━━━━━━━\n"
    if lang == "en":
        text += f"👤 <b>Your Rank:</b> <b>#{my_rank_str}</b>\n"
        text += f"💰 Total Earned: <b>{my_earned}</b> | 👥 Referrals: <b>{my_refs}</b>"
    else:
        text += f"👤 <b>আপনার অবস্থান:</b> <b>#{my_rank_str}</b>\n"
        text += f"💰 মোট আয়: <b>{my_earned}</b> | 👥 রেফার: <b>{my_refs}</b>"

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_user_main_menu_keyboard(user_id, db)
    )

# ----------------------------------------------------
# প্রধান টেক্সট মেসেজ হ্যান্ডলার
# ----------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or msg.chat.type != "private":
        return

    user_id = msg.from_user.id
    chat_id = msg.chat.id
    u_key = str(user_id)
    name = msg.from_user.first_name or "User"
    username = f"@{msg.from_user.username}" if msg.from_user.username else "No Username"
    text = (msg.text or "").strip()
    message_id = msg.message_id
    is_admin = (user_id == ADMIN_ID)

    async with db_lock:
        db = load_data()

        # বটের স্ট্যাটাস চেক
        if db.get("settings", {}).get("bot_status") == "OFF" and not is_admin:
            msg_off = "🛠️ <b>বটের সার্ভারে কাজ চলছে!</b>\nঅনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
            await msg.reply_text(msg_off, parse_mode=ParseMode.HTML)
            return

        # রেফারেল চেক (/start 123456)
        ref_by = None
        start_match = re.match(r"^/start\s+(\d+)", text)
        if start_match:
            ref_by = start_match.group(1)

        await register_user(context, db, user_id, name, username, ref_by)
        user_lang = db.get("users", {}).get(u_key, {}).get("lang", "bn")

        # এডমিন মেনু বাটন হ্যান্ডলিং
        admin_buttons = [
            "⚙️ অ্যাডমিন প্যানেল", "/admin", "📋 অল টাস্ক (Review)", "🛑 টাস্ক অন/অফ",
            "📁 এডমিন ডিল ফাইল", "💳 উইথড্রল রিকোয়েস্ট", "💲 অল রেট (Set Rates)",
            "🔐 অল টাস্ক পাসওয়ার্ড", "🎁 রেফারেল বোনাস মোড", "🎬 নতুনদের জন্য ভিডিও",
            "📢 পেমেন্ট প্রুফ চ্যানেল", "📝 ওয়েলকাম মেসেজ", "📢 অল ইউজার মেসেজ",
            "⭐ প্রিমিয়াম ইমোজি", "🎨 কালারিং প্যানেল", "➕ চ্যানেল যোগ করুন",
            "➖ চ্যানেল রিমুভ", "⚙️ উইথড্রল সেটিংস", "👥 মোট ইউজার",
            "🔴 বটের কাজ বন্ধ করুন", "🟢 বট চালু করুন", "🔙 মেইন মেনুতে ফিরুন"
        ]

        if is_admin and text in admin_buttons:
            db["admin_state"] = {}
            if u_key in db.get("user_states", {}):
                del db["user_states"][u_key]
            save_data(db)

            if text in ["⚙️ অ্যাডমিন প্যানেল", "/admin"]:
                await msg.reply_text(
                    "👑 <b>এডমিন কন্ট্রোল সেন্টার</b>\nটাস্ক অন/অফ, মোড পরিবর্তন, পাসওয়ার্ড, রেট ও উইথড্রল পরিচালনা করুন:",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

            if text == "🛑 টাস্ক অন/অফ":
                await msg.reply_text(
                    "🛑 <b>টাস্ক অন/অফ ও মোড কন্ট্রোল প্যানেল:</b>\n\nকাজের স্ট্যাটাস অন/অফ করতে অথবা Instagram ও Facebook-এর মোড (2FA / Cookies) পরিবর্তন করতে নিচের বাটনে চাপ দিন:",
                    parse_mode=ParseMode.HTML,
                    reply_markup=build_task_status_inline_keyboard(db)
                )
                return

            if text == "📁 এডমিন ডিল ফাইল":
                pending_deals = [d for d in db.get("admin_deals", {}).values() if d.get("status") == "pending"]
                if not pending_deals:
                    e_no_task = render_emoji_text("ntf_no_task", db, "📭")
                    await msg.reply_text(f"{e_no_task} <b>আপাতত কোনো কাজ আসে নাই! (কোনো এডমিন ডিল ফাইল পেন্ডিং নেই)</b>", parse_mode=ParseMode.HTML)
                    return

                for pd in pending_deals:
                    deal_kb = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ Approve ডিল", callback_data=f"adm_app_deal_{pd['id']}"),
                            InlineKeyboardButton("❌ Reject ডিল", callback_data=f"adm_rej_deal_{pd['id']}")
                        ]
                    ])
                    rew_str = format_taka(pd.get("reward", 0))
                    await msg.reply_text(
                        f"📁 <b>এডমিন ডিল রিভিউ:</b>\n🆔 আইডি: <code>{pd['id']}</code>\n👤 ইউজার: <code>{pd['user_id']}</code>\n🌐 সার্ভিস: <b>{pd.get('service', '').capitalize()}</b>\n📄 ফাইল/ডাটা: <code>{pd.get('file_name')}</code>\n💰 রেট: <b>{rew_str}</b>",
                        parse_mode=ParseMode.HTML,
                        reply_markup=deal_kb
                    )
                    file_id = pd.get("file_id")
                    if file_id and file_id != "raw_text":
                        try:
                            await context.bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=f"📄 ডিল ফাইল (#{pd['id']})")
                        except Exception as e:
                            logger.error(f"Failed to send deal document: {e}")
                return

            if text == "💳 উইথড্রল রিকোয়েস্ট":
                pending_wds = [w for w in db.get("withdrawals", {}).values() if w.get("status") == "pending"]
                if not pending_wds:
                    e_no_task = render_emoji_text("ntf_no_task", db, "📭")
                    await msg.reply_text(f"{e_no_task} <b>বর্তমানে কোনো পেন্ডিং উইথড্রল রিকোয়েস্ট নেই!</b>", parse_mode=ParseMode.HTML)
                    return

                for w in pending_wds:
                    kb = InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"📋 কপি এড্রেস ({w.get('address')})", callback_data=f"copynum_{w.get('address')}")],
                        [
                            InlineKeyboardButton("✅ Approve (পরিশোধিত)", callback_data=f"adm_app_wd_{w['id']}"),
                            InlineKeyboardButton("❌ Reject (বাতিল)", callback_data=f"adm_rej_wd_{w['id']}")
                        ]
                    ])
                    amt_str = format_taka(w.get("amount", 0))
                    chg_str = format_taka(w.get("charge", 5.0))
                    net_str = format_taka(w.get("net_amount", max(0, w.get("amount", 0) - 5.0)))
                    await msg.reply_text(
                        f"💳 <b>উইথড্রল রিকোয়েস্ট:</b>\n\n🆔 ইউজার: <code>{w.get('user_id')}</code>\n💵 মোট উইথড্র: <b>{amt_str}</b>\n⚡ চার্জ: <b>{chg_str}</b>\n💰 প্রদেয় (ইউজার পাবে): <b>{net_str}</b>\n📍 এড্রেস:\n<code>{w.get('address')}</code>\n⏰ সময়: {w.get('time')}",
                        parse_mode=ParseMode.HTML,
                        reply_markup=kb
                    )
                return

            if text == "📋 অল টাস্ক (Review)":
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📸 Instagram টাস্কসমূহ", callback_data="adm_vtasks_instagram")],
                    [InlineKeyboardButton("📘 Facebook টাস্কসমূহ", callback_data="adm_vtasks_facebook")],
                    [InlineKeyboardButton("📧 Gmail টাস্কসমূহ", callback_data="adm_vtasks_gmail")],
                    [InlineKeyboardButton("❌ Close", callback_data="cancel_admin_action")]
                ])
                await msg.reply_text(
                    "📋 <b>অল টাস্ক ম্যানেজার:</b>\nকোন ক্যাটাগরির জমা হওয়া কাজ দেখতে বা ফাইল নিতে চান সিলেক্ট করুন:",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                return

            if text == "💲 অল রেট (Set Rates)":
                rates = db.get("settings", {}).get("rates", {})
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"Instagram: {format_taka(rates.get('instagram', 10))}", callback_data="noop"), InlineKeyboardButton("✏️ এডিট", callback_data="ed_rate_instagram")],
                    [InlineKeyboardButton(f"Facebook: {format_taka(rates.get('facebook', 12))}", callback_data="noop"), InlineKeyboardButton("✏️ এডিট", callback_data="ed_rate_facebook")],
                    [InlineKeyboardButton(f"Gmail: {format_taka(rates.get('gmail', 8))}", callback_data="noop"), InlineKeyboardButton("✏️ এডিট", callback_data="ed_rate_gmail")],
                    [InlineKeyboardButton(f"Admin File: {format_taka(rates.get('admin_file', 1200))}", callback_data="noop"), InlineKeyboardButton("✏️ এডিট", callback_data="ed_rate_admin_file")],
                    [InlineKeyboardButton("❌ Close", callback_data="cancel_admin_action")]
                ])
                await msg.reply_text(
                    "💲 <b>অল টাস্ক রেট কনফিগারেশন (বাংলা টাকায় ৳):</b>\nরেট পরিবর্তনের জন্য পাশের ✏️ এডিট বাটনে চাপ দিন:",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                return

            if text == "⚙️ উইথড্রল সেটিংস":
                st = db.get("settings", {}).get("withdraw_status", "ON")
                btn_st_text = "🔴 উইথড্রল সিস্টেম বন্ধ করুন (OFF)" if st == "ON" else "🟢 উইথড্রল সিস্টেম চালু করুন (ON)"
                min_w = format_taka(db.get("settings", {}).get("min_withdraw", 50))
                chg_w = format_taka(db.get("settings", {}).get("withdraw_charge", 5))

                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton(btn_st_text, callback_data="adm_tog_wd_status")],
                    [InlineKeyboardButton(f"✏️ মিনিমাম উইথড্র কমান/বাড়ান ({min_w})", callback_data="adm_ed_min_wd")],
                    [InlineKeyboardButton(f"✏️ উইথড্র চার্জ পরিবর্তন ({chg_w})", callback_data="adm_ed_wd_chg")],
                    [InlineKeyboardButton("❌ Close", callback_data="cancel_admin_action")]
                ])
                await msg.reply_text(
                    f"⚙️ <b>উইথড্রল সেটিংস ও লিমিট কন্ট্রোল:</b>\n\n🔹 বর্তমান স্ট্যাটাস: <b>{st}</b>\n🔹 ন্যূনতম উইথড্র: <b>{min_w}</b>\n🔹 উইথড্র চার্জ: <b>{chg_w}</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                return

            if text == "🔐 অল টাস্ক পাসওয়ার্ড":
                db["admin_state"]["action"] = "set_task_pass"
                save_data(db)
                cur_pass = db.get("settings", {}).get("default_task_pass", "")
                await msg.reply_text(
                    f"🔐 <b>টাস্ক পাসওয়ার্ড ম্যানেজার:</b>\nবর্তমান পাসওয়ার্ড: <code>{cur_pass}</code>\n\nনতুন পাসওয়ার্ডটি লিখে পাঠান:",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_cancel_inline_markup()
                )
                return

            if text == "📝 ওয়েলকাম মেসেজ":
                db["admin_state"]["action"] = "set_welcome_msg"
                save_data(db)
                cur_msg = db.get("settings", {}).get("welcome_msg", "")
                await msg.reply_text(
                    f"📝 <b>বর্তমান ওয়েলকাম মেসেজ:</b>\n\n<blockquote expandable>{cur_msg}</blockquote>\n\n💡 <b>নির্দেশনা:</b>\nমেসেজের যেখানে ইউজারের নাম দেখাতে চান সেখানে <code>*first_name*</code> লিখবেন। বট অটোমেটিক ওই জায়গায় ইউজারের আসল নাম বসিয়ে দেবে।\n\nনতুন ওয়েলকাম মেসেজটি লিখে পাঠান:",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_cancel_inline_markup()
                )
                return

            if text == "📢 অল ইউজার মেসেজ":
                db["admin_state"]["action"] = "broadcast_all_media"
                save_data(db)
                await msg.reply_text(
                    "📢 <b>অল ইউজার মেসেজ (Broadcast):</b>\nযেকোনো টেক্সট, ভয়েস, ছবি, অডিও বা লিংক সহ পোস্ট পাঠান:",
                    reply_markup=get_cancel_inline_markup()
                )
                return

            if text == "⭐ প্রিমিয়াম ইমোজি":
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 চ্যানেল ও ভেরিফাই বাটন ইমোজি (✏️)", callback_data="pem_sub_channel")],
                    [InlineKeyboardButton("🔑 টাস্কের ভেতরের ডাটা ইমোজি (✏️)", callback_data="pem_sub_taskdata")],
                    [InlineKeyboardButton("🔘 মেইন মেনু বাটন ইমোজি (✏️)", callback_data="pem_sub_menu")],
                    [InlineKeyboardButton("💼 টাস্ক মেনুর বাটনসমূহ (✏️)", callback_data="pem_sub_task")],
                    [InlineKeyboardButton("🎬 আমি নতুন ও ভাষা বাটন (✏️)", callback_data="pem_sub_newlang")],
                    [InlineKeyboardButton("🔔 সকল নোটিশ ও অ্যালার্ট ইমোজি (✏️)", callback_data="pem_sub_ntf")],
                    [InlineKeyboardButton("👤 ব্যালেন্স/প্রোফাইল টেক্সট ইমোজি (✏️)", callback_data="pem_sub_bal")],
                    [InlineKeyboardButton("👥 রেফার ও লিডারবোর্ড ইমোজি (✏️)", callback_data="pem_sub_reflb")],
                    [InlineKeyboardButton("❌ Close", callback_data="cancel_admin_action")]
                ])
                await msg.reply_text(
                    "⭐ <b>অল-ইন-ওয়ান প্রিমিয়াম ইমোজি কন্ট্রোল প্যানেল:</b>\n\nবাটন বা নোটিশের প্রিমিয়াম ইমোজি পেন্সিল (✏️) আইকনে ক্লিক করে কাস্টমাইজ করুন:",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                return

            if text == "🎨 কালারিং প্যানেল":
                cols = db.get("settings", {}).get("btn_colors", {})
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"চ্যানেল বাটন [{cols.get('channel', 'SUCCESS').upper()}]", callback_data="adm_col_channel"), InlineKeyboardButton(f"ভেরিফাই বাটন [{cols.get('verify', 'PRIMARY').upper()}]", callback_data="adm_col_verify")],
                    [InlineKeyboardButton(f"ব্যালেন্স [{cols.get('balance', 'PRIMARY').upper()}]", callback_data="adm_col_balance"), InlineKeyboardButton(f"কাজ [{cols.get('task', 'SUCCESS').upper()}]", callback_data="adm_col_task")],
                    [InlineKeyboardButton(f"উইথড্রল [{cols.get('withdraw', 'DANGER').upper()}]", callback_data="adm_col_withdraw"), InlineKeyboardButton(f"রেফার [{cols.get('refer', 'PRIMARY').upper()}]", callback_data="adm_col_refer")],
                    [InlineKeyboardButton(f"লিডারবোর্ড [{cols.get('leaderboard', 'PRIMARY').upper()}]", callback_data="adm_col_leaderboard"), InlineKeyboardButton(f"ভাষা বাটন [{cols.get('lang', 'PRIMARY').upper()}]", callback_data="adm_col_lang")],
                    [InlineKeyboardButton(f"আমি নতুন [{cols.get('new', 'PRIMARY').upper()}]", callback_data="adm_col_new"), InlineKeyboardButton(f"ব্যাক বাটন [{cols.get('back', 'DANGER').upper()}]", callback_data="adm_col_back")],
                    [InlineKeyboardButton(f"2FA Key [{cols.get('2fa_key', 'PRIMARY').upper()}]", callback_data="adm_col_2fa_key"), InlineKeyboardButton(f"টাস্ক সাবমিট [{cols.get('task_submit', 'SUCCESS').upper()}]", callback_data="adm_col_task_submit")],
                    [InlineKeyboardButton("❌ Close", callback_data="cancel_admin_action")]
                ])
                await msg.reply_text(
                    "🎨 <b>বাটন কালার স্টাইলিং:</b>\nযে বাটনের রঙ পরিবর্তন করতে চান সিলেক্ট করুন:",
                    reply_markup=kb
                )
                return

            if text == "🎁 রেফারেল বোনাস মোড":
                mode = db.get("settings", {}).get("referral_mode", "commission")
                pct = db.get("settings", {}).get("ref_commission_pct", 20.0)
                fix = format_taka(db.get("settings", {}).get("ref_direct_bonus", 5.0))

                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🟢 কমিশন মোড (Active)" if mode == "commission" else "⚪ কমিশন মোড চালু করুন", callback_data="set_ref_mode_comm")],
                    [InlineKeyboardButton("🟢 ফিক্সড ক্যাশ মোড (Active)" if mode == "direct" else "⚪ ফিক্সড ক্যাশ চালু করুন", callback_data="set_ref_mode_dir")],
                    [InlineKeyboardButton("❌ Close", callback_data="cancel_admin_action")]
                ])
                await msg.reply_text(
                    f"🎁 <b>রেফারেল বোনাস কন্ট্রোল:</b>\nবর্তমান মোড: <b>{mode.upper()}</b>\n\n🔹 কমিশন মোড: প্রতি কাজের <b>{pct}%</b> পাবে।\n🔹 ফিক্সড মোড: রেফারে জয়েন করলেই <b>{fix}</b> সরাসরি ব্যালেন্সে যোগ হবে।",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                return

            if text == "🎬 নতুনদের জন্য ভিডিও":
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Instagram ভিডিও যোগ", callback_data="adm_addvid_instagram"), InlineKeyboardButton("🗑️ মুছুন", callback_data="adm_delvid_instagram")],
                    [InlineKeyboardButton("➕ Facebook ভিডিও যোগ", callback_data="adm_addvid_facebook"), InlineKeyboardButton("🗑️ মুছুন", callback_data="adm_delvid_facebook")],
                    [InlineKeyboardButton("➕ Gmail ভিডিও যোগ", callback_data="adm_addvid_gmail"), InlineKeyboardButton("🗑️ মুছুন", callback_data="adm_delvid_gmail")],
                    [InlineKeyboardButton("❌ Close", callback_data="cancel_admin_action")]
                ])
                await msg.reply_text("🎬 <b>টিউটোরিয়াল ভিডিও ম্যানেজার:</b>", parse_mode=ParseMode.HTML, reply_markup=kb)
                return

            if text == "📢 পেমেন্ট প্রুফ চ্যানেল":
                cur_ch = db.get("settings", {}).get("proof_channel") or "সেট করা নেই"
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ নতুন চ্যানেল সেট করুন", callback_data="adm_set_proof_ch")],
                    [InlineKeyboardButton("🗑️ চ্যানেল বাতিল করুন", callback_data="adm_rem_proof_ch")]
                ])
                await msg.reply_text(f"📢 <b>পেমেন্ট প্রুফ চ্যানেল:</b>\nবর্তমান চ্যানেল: <code>{cur_ch}</code>", parse_mode=ParseMode.HTML, reply_markup=kb)
                return

            if text == "➕ চ্যানেল যোগ করুন":
                db["admin_state"]["action"] = "add_chan_link"
                save_data(db)
                await msg.reply_text(
                    "➕ <b>চ্যানেলের ইউজারনেম (যেমন <code>@YourChannel</code>) অথবা চ্যানেলের পূর্ণ লিংক পাঠান:</b>\n\n⚠️ <i>মনে রাখবেন: ইউজারদের ভেরিফাই করার জন্য বটকে অবশ্যই উক্ত চ্যানেলে <b>Administrator</b> করে রাখবেন।</i>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_cancel_inline_markup()
                )
                return

            if text == "➖ চ্যানেল রিমুভ":
                channels = db.get("channels", [])
                if not channels:
                    await msg.reply_text("📭 কোনো চ্যানেল যুক্ত করা নেই।")
                    return
                for idx, c in enumerate(channels):
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ রিমুভ করুন", callback_data=f"del_chan_{idx}")]])
                    await msg.reply_text(
                        f"📢 <b>{c.get('title', '')}</b>\n🔗 {c.get('url', '')}",
                        parse_mode=ParseMode.HTML,
                        reply_markup=kb
                    )
                return

            if text == "👥 মোট ইউজার":
                total_users = len(db.get("users", {}))
                await msg.reply_text(
                    f"👥 <b>বটের মোট সক্রিয় ইউজার:</b> <b>{to_bangla_num(total_users)} জন</b>",
                    parse_mode=ParseMode.HTML
                )
                return

            if text in ["🔴 বটের কাজ বন্ধ করুন", "🟢 বট চালু করুন"]:
                new_st = "OFF" if db.get("settings", {}).get("bot_status") == "ON" else "ON"
                db["settings"]["bot_status"] = new_st
                save_data(db)
                resp = "🟢 বট সফলভাবে চালু করা হয়েছে!" if new_st == "ON" else "🔴 বট সাময়িকভাবে বন্ধ করা হয়েছে!"
                await msg.reply_text(resp, reply_markup=get_admin_keyboard(new_st))
                return

            if text == "🔙 মেইন মেনুতে ফিরুন":
                await msg.reply_text("মেইন মেনু:", reply_markup=get_user_main_menu_keyboard(ADMIN_ID, db))
                return

        # গ্লোবাল বাতিল ও ব্যাক চেকার
        cancel_words = ["/cancel", "cancel", "❌ cancel", "❌ কাজ বাতিল", "কাজ বাতিল", "বাতিল", "cancel task"]
        if (text.lower() in cancel_words or
            "কাজ বাতিল" in text or
            "Cancel Task" in text or
            "মেনু ফিরে যান" in text or
            "Back to Menu" in text):

            if u_key in db.get("user_states", {}):
                del db["user_states"][u_key]
            if is_admin:
                db["admin_state"] = {}
            save_data(db)

            await msg.reply_text(
                get_lang_text("cancel_action", user_lang, {}, db),
                parse_mode=ParseMode.HTML,
                reply_markup=get_user_main_menu_keyboard(user_id, db)
            )
            return

        # এডমিন স্টেট অ্যাকশন এক্সিকিউশন
        if is_admin and db.get("admin_state", {}).get("action"):
            adm_act = db["admin_state"]["action"]

            if adm_act == "set_task_pass":
                db["settings"]["default_task_pass"] = text
                db["admin_state"] = {}
                save_data(db)
                await msg.reply_text(
                    f"✅ <b>টাস্ক পাসওয়ার্ড সফলভাবে আপডেট হয়েছে!</b>\nনতুন পাসওয়ার্ড: <code>{text}</code>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

            if adm_act.startswith("set_rate_"):
                t_type = adm_act.replace("set_rate_", "")
                try:
                    new_rate = float(from_bangla_num(text))
                    if new_rate <= 0:
                        raise ValueError
                except ValueError:
                    await msg.reply_text("⚠️ দয়া করে একটি সঠিক রেট (যেমন 10 বা 15) লিখে পাঠান:")
                    return

                db["settings"]["rates"][t_type] = new_rate
                db["admin_state"] = {}
                save_data(db)
                r_str = format_taka(new_rate)
                await msg.reply_text(
                    f"✅ <b>{t_type.capitalize()}</b> এর নতুন রেট <b>{r_str}</b> সফলভাবে সেট হয়েছে!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

            if adm_act == "set_welcome_msg":
                db["settings"]["welcome_msg"] = text
                db["settings"]["welcome_msg_id"] = message_id
                db["settings"]["welcome_chat_id"] = chat_id
                db["admin_state"] = {}
                save_data(db)
                await msg.reply_text(
                    "✅ <b>ওয়েলকাম মেসেজ সফলভাবে সংরক্ষিত হয়েছে!</b>\nপ্রিমিয়াম ইমোজি ও <code>*first_name*</code> প্লেসহোল্ডার এখন থেকে লাইভ কাজ করবে।",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

            if adm_act == "broadcast_all_media":
                db["admin_state"] = {}
                save_data(db)
                users = list(db.get("users", {}).keys())
                await msg.reply_text(f"⏳ {len(users)} জন ইউজারের কাছে দ্রুত পাঠানো হচ্ছে...")
                s = 0
                f_count = 0
                for target_uid in users:
                    try:
                        await context.bot.copy_message(chat_id=int(target_uid), from_chat_id=chat_id, message_id=message_id)
                        s += 1
                        await asyncio.sleep(0.04)  # টেলিগ্রাম ফ্লাড লিমিট এড়াতে
                    except Exception:
                        f_count += 1
                await msg.reply_text(
                    f"✅ ব্রডকাস্ট সম্পন্ন!\n✔ ডেলিভারি: {s}\n✖ ব্যর্থ: {f_count}",
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

            if adm_act.startswith("add_vid_"):
                v_type = adm_act.replace("add_vid_", "")
                if msg.video:
                    db["settings"]["videos"][v_type] = f"FILE:{msg.video.file_id}"
                else:
                    db["settings"]["videos"][v_type] = text
                db["admin_state"] = {}
                save_data(db)
                await msg.reply_text(
                    f"✅ <b>{v_type.capitalize()}</b> এর টিউটোরিয়াল ভিডিও সফলভাবে যুক্ত হয়েছে!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

            if adm_act == "set_proof_channel":
                db["settings"]["proof_channel"] = text.strip()
                db["admin_state"] = {}
                save_data(db)
                await msg.reply_text(
                    f"✅ পেমেন্ট প্রুফ চ্যানেল আপডেট হয়েছে: <code>{text}</code>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

            if adm_act == "set_min_wd":
                try:
                    val = float(from_bangla_num(text))
                    if val <= 0:
                        raise ValueError
                except ValueError:
                    await msg.reply_text("⚠️ অনুগ্রহ করে সঠিক সংখ্যা (যেমন: 50 বা 100) পাঠান:")
                    return
                db["settings"]["min_withdraw"] = val
                db["admin_state"] = {}
                save_data(db)
                min_str = format_taka(val)
                await msg.reply_text(
                    f"✅ ন্যূনতম উইথড্রল লিমিট <b>{min_str}</b> করা হয়েছে!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

            if adm_act == "set_wd_chg":
                try:
                    val = float(from_bangla_num(text))
                    if val < 0:
                        val = 0.0
                except ValueError:
                    await msg.reply_text("⚠️ অনুগ্রহ করে সঠিক চার্জ পাঠান:")
                    return
                db["settings"]["withdraw_charge"] = val
                db["admin_state"] = {}
                save_data(db)
                chg_str = format_taka(val)
                await msg.reply_text(
                    f"✅ উইথড্র চার্জ <b>{chg_str}</b> সেট করা হয়েছে!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

            if adm_act == "add_chan_link":
                parsed = parse_channel_input(text)
                db["admin_state"]["temp_url"] = parsed["url"]
                db["admin_state"]["temp_chat_id"] = parsed["chat_id"]
                db["admin_state"]["action"] = "add_chan_title"
                save_data(db)
                await msg.reply_text(
                    "📝 <b>চ্যানেলের বাটনের নাম (Title) পাঠান:</b>\n(যেমন: <code>📢 Join Main Channel</code>)",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_cancel_inline_markup()
                )
                return

            if adm_act == "add_chan_title":
                new_chan = {
                    "title": text,
                    "url": db["admin_state"].get("temp_url", ""),
                    "chat_id": db["admin_state"].get("temp_chat_id", "")
                }
                db.setdefault("channels", []).append(new_chan)
                db["admin_state"] = {}
                save_data(db)
                await msg.reply_text(
                    f"🎉 <b>চ্যানেল সফলভাবে যুক্ত হয়েছে!</b>\n\n📢 <b>নাম:</b> {new_chan['title']}\n🔗 <b>লিংক:</b> {new_chan['url']}\n🆔 <b>চ্যাট আইডি:</b> <code>{new_chan['chat_id']}</code>\n\n⚠️ <i>মনে রাখবেন: চ্যানেল ভেরিফিকেশন চালু রাখতে বটকে উক্ত চ্যানেলে <b>Administrator</b> করে রাখবেন।</i>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

            if adm_act == "set_custom_emoji":
                target_key = db["admin_state"].get("target_key")
                if text == "0" or text.lower() == "clear":
                    db["settings"]["premium_emojis"][target_key] = {"char": "", "id": ""}
                    msg_out = "✅ ইমোজি মুছে ফেলা হয়েছে!"
                else:
                    custom_emoji_id = ""
                    char = text
                    if msg.entities:
                        for ent in msg.entities:
                            if ent.type == "custom_emoji" and ent.custom_emoji_id:
                                custom_emoji_id = ent.custom_emoji_id
                                char = text[ent.offset: ent.offset + ent.length] or "⭐"
                                break
                    db["settings"]["premium_emojis"][target_key] = {"char": char, "id": custom_emoji_id}
                    msg_out = f"✅ <b>[{target_key}]</b>-এ প্রিমিয়াম কাস্টম ইমোজি সেট হয়েছে!\nID: <code>{custom_emoji_id}</code>" if custom_emoji_id else f"✅ <b>[{target_key}]</b>-এ ইমোজি সেট হয়েছে: {char}"
                
                db["admin_state"] = {}
                save_data(db)
                await msg.reply_text(
                    msg_out,
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
                )
                return

        # চ্যানেল জয়েন ভেরিফিকেশন চেক
        channels = db.get("channels", [])
        if channels:
            is_verified = db.get("users", {}).get(u_key, {}).get("is_verified", False)
            if not is_verified:
                unjoined = await get_unjoined_channels(context.bot, user_id, channels)
                if unjoined:
                    await msg.reply_text(
                        get_force_join_message(channels, db, user_lang),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                        reply_markup=generate_force_join_keyboard(channels, db, user_lang)
                    )
                    return
                else:
                    db["users"][u_key]["is_verified"] = True
                    save_data(db)

        # 2FA Key বাটন হ্যান্ডলিং
        if "2FA Key" in text or "টু এফ এ কি" in text:
            cur_st = db.get("user_states", {}).get(u_key, {})
            cur_act = cur_st.get("action")
            if cur_act == "ig_ready_2fa_btn":
                db["user_states"][u_key]["action"] = "ig_wait_2fa"
                save_data(db)
                e_ig = render_emoji_text("ntf_ig", db, "📸")
                wait_txt = f"{e_ig} <b>Send your Instagram 2FA Secret Key:</b>" if user_lang == "en" else f"{e_ig} <b>আপনার Instagram 2FA Key (Secret Key) টি পাঠান:</b>"
                await msg.reply_text(wait_txt, parse_mode=ParseMode.HTML, reply_markup=get_cancel_reply_keyboard(db, user_lang))
                return
            elif cur_act == "fb_ready_2fa_btn":
                db["user_states"][u_key]["action"] = "fb_wait_2fa"
                save_data(db)
                e_fb = render_emoji_text("ntf_fb", db, "📘")
                wait_txt = f"{e_fb} <b>Send your Facebook 2FA Secret Key:</b>" if user_lang == "en" else f"{e_fb} <b>আপনার Facebook 2FA Key (Secret Key) টি পাঠান:</b>"
                await msg.reply_text(wait_txt, parse_mode=ParseMode.HTML, reply_markup=get_cancel_reply_keyboard(db, user_lang))
                return

        # টাস্ক সাবমিশন বাটন হ্যান্ডলিং
        if "টাস্ক সাবমিট" in text or "Submit Task" in text:
            st = db.get("user_states", {}).get(u_key, {})
            if st.get("action") == "ig_ready_submit":
                task_id = "tsk_" + uuid.uuid4().hex[:8]
                db.setdefault("tasks", {})[task_id] = {
                    "id": task_id,
                    "user_id": user_id,
                    "type": "instagram",
                    "username": st.get("username", ""),
                    "password": st.get("password", ""),
                    "secret": st.get("secret", ""),
                    "otp": st.get("otp", ""),
                    "cookies": st.get("cookies", ""),
                    "reward": db.get("settings", {}).get("rates", {}).get("instagram", 10.0),
                    "status": "pending",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                del db["user_states"][u_key]
                save_data(db)

                await msg.reply_text(
                    get_lang_text("task_sub_done", user_lang, {}, db),
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_user_main_menu_keyboard(user_id, db)
                )

                e_ntf = render_emoji_text("ntf_ig", db, "📸")
                extra_data = f"🍪 Cookies:\n<code>{st.get('cookies')}</code>" if st.get("cookies") else f"🔐 2FA: <code>{st.get('secret')}</code>\n🔢 OTP: <code>{st.get('otp')}</code>"
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"{e_ntf} <b>নতুন Instagram কাজ জমা পড়েছে!</b>\n👤 ইউজার: <code>{user_id}</code>\n👤 ইউজারনেম: <code>{st.get('username')}</code>\n🔑 পাসওয়ার্ড: <code>{st.get('password')}</code>\n{extra_data}",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
                return

            if st.get("action") == "fb_ready_submit":
                task_id = "tsk_" + uuid.uuid4().hex[:8]
                db.setdefault("tasks", {})[task_id] = {
                    "id": task_id,
                    "user_id": user_id,
                    "type": "facebook",
                    "first_name": st.get("first_name", ""),
                    "last_name": st.get("last_name", ""),
                    "password": st.get("password", ""),
                    "uid": st.get("uid", ""),
                    "cookies": st.get("cookies", ""),
                    "secret": st.get("secret", ""),
                    "otp": st.get("otp", ""),
                    "reward": db.get("settings", {}).get("rates", {}).get("facebook", 12.0),
                    "status": "pending",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                del db["user_states"][u_key]
                save_data(db)

                await msg.reply_text(
                    get_lang_text("task_sub_done", user_lang, {}, db),
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_user_main_menu_keyboard(user_id, db)
                )

                e_ntf = render_emoji_text("ntf_fb", db, "📘")
                extra_fb = f"🍪 Cookies:\n<code>{st.get('cookies')}</code>" if st.get("cookies") else f"🔐 2FA: <code>{st.get('secret')}</code>\n🔢 OTP: <code>{st.get('otp')}</code>"
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"{e_ntf} <b>নতুন Facebook কাজ জমা পড়েছে!</b>\n👤 ইউজার: <code>{user_id}</code>\n👤 নাম: <code>{st.get('first_name')} {st.get('last_name')}</code>\n🆔 UID: <code>{st.get('uid')}</code>\n🔑 পাসওয়ার্ড: <code>{st.get('password')}</code>\n{extra_fb}",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
                return

        # ইউজার স্টেট অনুযায়ী ডাটা গ্রহণ
        if u_key in db.get("user_states", {}):
            state = db["user_states"][u_key]
            act = state.get("action")

            if act == "ig_wait_2fa":
                secret = text.strip()
                otp = generate_2fa_otp(secret)
                if not otp:
                    e_err = render_emoji_text("ntf_no_bal", db, "⚠️")
                    err_txt = f"{e_err} <b>Invalid 2FA Secret Key!</b>\nPlease send a valid 2FA Secret Key:" if user_lang == "en" else f"{e_err} <b>ভুল 2FA Key!</b>\nঅনুগ্রহ করে সঠিক 2FA Secret Key পাঠান:"
                    await msg.reply_text(err_txt, parse_mode=ParseMode.HTML)
                    return

                db["user_states"][u_key]["secret"] = secret
                db["user_states"][u_key]["otp"] = otp
                db["user_states"][u_key]["action"] = "ig_ready_submit"
                save_data(db)

                copy_btn = InlineKeyboardMarkup([[InlineKeyboardButton(f"📋 Copy Code ({otp})" if user_lang == "en" else f"📋 কোড কপি করুন ({otp})", callback_data=f"copynum_{otp}")]])
                e_ig = render_emoji_text("ntf_ig", db, "📸")
                otp_txt = f"{e_ig} <b>Your 2FA Verification Code (OTP):</b>\n\n<code>{otp}</code>\n\nVerify your account and click <b>'Submit Task'</b> below:" if user_lang == "en" else f"{e_ig} <b>আপনার 2FA ভেরিফিকেশন কোড (OTP):</b>\n\n<code>{otp}</code>\n\nকোডটি দিয়ে ইনস্টাগ্রাম ভেরিফাই করে নিচের <b>'টাস্ক সাবমিট'</b> বাটনে চাপ দিন:"
                await msg.reply_text(otp_txt, parse_mode=ParseMode.HTML, reply_markup=copy_btn)
                await msg.reply_text("✅ Once finished, submit your task below:" if user_lang == "en" else "✅ কাজ শেষ হলে নিচের বাটনে সাবমিট করুন:", reply_markup=get_submit_task_reply_keyboard(db, user_lang))
                return

            if act == "ig_wait_cookie":
                db["user_states"][u_key]["cookies"] = text
                db["user_states"][u_key]["action"] = "ig_ready_submit"
                save_data(db)

                e_ig = render_emoji_text("ntf_ig", db, "📸")
                done_cook = f"{e_ig} <b>Instagram Cookies saved successfully!</b>\n\nNow click <b>'Submit Task'</b> below:" if user_lang == "en" else f"{e_ig} <b>Instagram Cookies সফলভাবে সেভ হয়েছে!</b>\n\nএখন নিচের <b>'টাস্ক সাবমিট'</b> বাটনে চাপ দিন:"
                await msg.reply_text(done_cook, parse_mode=ParseMode.HTML, reply_markup=get_submit_task_reply_keyboard(db, user_lang))
                return

            if act == "fb_wait_uid":
                db["user_states"][u_key]["uid"] = text
                fb_mode = db.get("settings", {}).get("fb_mode", "cookies")

                if fb_mode == "2fa":
                    db["user_states"][u_key]["action"] = "fb_ready_2fa_btn"
                    save_data(db)
                    e_fb = render_emoji_text("ntf_fb", db, "📘")
                    ask2fa = f"{e_fb} <b>UID received! Now click the '2FA Key' button below to send your Facebook 2FA:</b>" if user_lang == "en" else f"{e_fb} <b>UID পাওয়া গেছে! এবার আপনার ফেসবুকের টু-এফ-এ কি দিতে নিচের '2FA Key' বাটনে চাপ দিন:</b>"
                    await msg.reply_text(ask2fa, parse_mode=ParseMode.HTML, reply_markup=get_2fa_key_reply_keyboard(db, user_lang))
                else:
                    db["user_states"][u_key]["action"] = "fb_wait_cookie"
                    save_data(db)
                    e_cookie = render_emoji_text("task_ic_cookie", db, "🍪")
                    ask_cookie = f"{e_cookie} <b>UID received! Now send the Facebook account Cookies:</b>\n\n(Paste your complete cookies text here)" if user_lang == "en" else f"{e_cookie} <b>ইউআইডি (UID) পাওয়া গেছে! এবার ফেসবুক আইডির Cookies (কুকিজ) পাঠান:</b>\n\n(কুকিজ টেক্সটটি কপি করে এখানে পেস্ট করুন)"
                    await msg.reply_text(ask_cookie, parse_mode=ParseMode.HTML, reply_markup=get_cancel_reply_keyboard(db, user_lang))
                return

            if act == "fb_wait_2fa":
                secret = text.strip()
                otp = generate_2fa_otp(secret)
                if not otp:
                    e_err = render_emoji_text("ntf_no_bal", db, "⚠️")
                    err_txt = f"{e_err} <b>Invalid 2FA Secret Key!</b>\nPlease send a valid 2FA Secret Key:" if user_lang == "en" else f"{e_err} <b>ভুল 2FA Key!</b>\nঅনুগ্রহ করে সঠিক 2FA Secret Key পাঠান:"
                    await msg.reply_text(err_txt, parse_mode=ParseMode.HTML)
                    return

                db["user_states"][u_key]["secret"] = secret
                db["user_states"][u_key]["otp"] = otp
                db["user_states"][u_key]["action"] = "fb_ready_submit"
                save_data(db)

                copy_btn = InlineKeyboardMarkup([[InlineKeyboardButton(f"📋 Copy Code ({otp})" if user_lang == "en" else f"📋 কোড কপি করুন ({otp})", callback_data=f"copynum_{otp}")]])
                e_fb = render_emoji_text("ntf_fb", db, "📘")
                otp_txt = f"{e_fb} <b>Your 2FA Verification Code (OTP):</b>\n\n<code>{otp}</code>\n\nVerify and click <b>'Submit Task'</b> below:" if user_lang == "en" else f"{e_fb} <b>আপনার Facebook 2FA কোড (OTP):</b>\n\n<code>{otp}</code>\n\nকোডটি দিয়ে ভেরিফাই করে নিচের <b>'টাস্ক সাবমিট'</b> বাটনে চাপ দিন:"
                await msg.reply_text(otp_txt, parse_mode=ParseMode.HTML, reply_markup=copy_btn)
                await msg.reply_text("✅ Once finished, submit your task below:" if user_lang == "en" else "✅ কাজ শেষ হলে নিচের বাটনে সাবমিট করুন:", reply_markup=get_submit_task_reply_keyboard(db, user_lang))
                return

            if act == "fb_wait_cookie":
                db["user_states"][u_key]["cookies"] = text
                db["user_states"][u_key]["action"] = "fb_ready_submit"
                save_data(db)

                e_fb = render_emoji_text("ntf_fb", db, "📘")
                done_cook = f"{e_fb} <b>UID & Cookies saved successfully!</b>\n\nNow click <b>'Submit Task'</b> to send your task to Admin:" if user_lang == "en" else f"{e_fb} <b>UID ও Cookies সফলভাবে সংরক্ষণ করা হয়েছে!</b>\n\nএখন কাজটি জমা দিতে নিচের <b>'টাস্ক সাবমিট'</b> বাটনে চাপ দিন:"
                await msg.reply_text(done_cook, parse_mode=ParseMode.HTML, reply_markup=get_submit_task_reply_keyboard(db, user_lang))
                return

            if act == "gm_wait_email":
                if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", text):
                    e_err = render_emoji_text("ntf_no_bal", db, "⚠️")
                    err_txt = f"{e_err} Please send a valid Gmail address:" if user_lang == "en" else f"{e_err} অনুগ্রহ করে সঠিক জিমেইল এড্রেস লিখুন:"
                    await msg.reply_text(err_txt, parse_mode=ParseMode.HTML)
                    return
                db["user_states"][u_key]["email"] = text
                db["user_states"][u_key]["action"] = "gm_wait_pass"
                save_data(db)

                ask_pass = "🔑 <b>Enter your Gmail Password:</b>" if user_lang == "en" else "🔑 <b>জিমেইলের পাসওয়ার্ড দিন:</b>"
                await msg.reply_text(ask_pass, parse_mode=ParseMode.HTML, reply_markup=get_cancel_reply_keyboard(db, user_lang))
                return

            if act == "gm_wait_pass":
                db["user_states"][u_key]["pass"] = text
                db["user_states"][u_key]["action"] = "gm_wait_conf"
                save_data(db)

                ask_conf = "🔁 <b>Re-enter Password to Confirm:</b>" if user_lang == "en" else "🔁 <b>পাসওয়ার্ডটি আবার লিখে কনফার্ম করুন:</b>"
                await msg.reply_text(ask_conf, parse_mode=ParseMode.HTML, reply_markup=get_cancel_reply_keyboard(db, user_lang))
                return

            if act == "gm_wait_conf":
                if text != db["user_states"][u_key].get("pass"):
                    e_err = render_emoji_text("ntf_no_bal", db, "⚠️")
                    mismatch = f"{e_err} Passwords do not match! Try again:" if user_lang == "en" else f"{e_err} পাসওয়ার্ড মিলেনি! পুনরায় কনফার্ম পাসওয়ার্ড লিখুন:"
                    await msg.reply_text(mismatch, parse_mode=ParseMode.HTML)
                    return

                task_id = "tsk_" + uuid.uuid4().hex[:8]
                db.setdefault("tasks", {})[task_id] = {
                    "id": task_id,
                    "user_id": user_id,
                    "type": "gmail",
                    "email": db["user_states"][u_key]["email"],
                    "password": db["user_states"][u_key]["pass"],
                    "reward": db.get("settings", {}).get("rates", {}).get("gmail", 8.0),
                    "status": "pending",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                del db["user_states"][u_key]
                save_data(db)

                e_err = render_emoji_text("ntf_no_bal", db, "⚠️")
                warn = (
                    f"{e_err} <b>Important Notice:</b>\nPlease logout this Gmail account from your device immediately.\n\n" + get_lang_text("task_sub_done", user_lang, {}, db)
                    if user_lang == "en"
                    else f"{e_err} <b>জরুরি সতর্কতা:</b>\nএই জিমেইলটি আপনার ফোন থেকে দ্রুত <b>লগআউট</b> করে দিন।\n\n" + get_lang_text("task_sub_done", user_lang, {}, db)
                )

                await msg.reply_text(warn, parse_mode=ParseMode.HTML, reply_markup=get_user_main_menu_keyboard(user_id, db))

                e_ntf = render_emoji_text("ntf_gmail", db, "📧")
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"{e_ntf} <b>নতুন Gmail টাস্ক সাবমিট হয়েছে!</b>\n👤 ইউজার: <code>{user_id}</code>\n📧 ইমেইল: <code>{db['tasks'][task_id]['email']}</code>\n🔑 পাসওয়ার্ড: <code>{db['tasks'][task_id]['password']}</code>",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
                return

            if act == "admin_deal_wait_file":
                target_service = state.get("service")
                file_id = ""
                file_name = "deal_accounts.txt"

                if msg.document:
                    file_id = msg.document.file_id
                    file_name = msg.document.file_name or "deal_file.txt"
                elif text:
                    file_id = "raw_text"
                    file_name = text
                else:
                    e_err = render_emoji_text("ntf_no_bal", db, "⚠️")
                    err_txt = f"{e_err} Please send your deal account file:" if user_lang == "en" else f"{e_err} অনুগ্রহ করে আপনার একাউন্টের ফাইলটি সেন্ড করুন:"
                    await msg.reply_text(err_txt, parse_mode=ParseMode.HTML)
                    return

                deal_id = "deal_" + uuid.uuid4().hex[:8]
                db.setdefault("admin_deals", {})[deal_id] = {
                    "id": deal_id,
                    "user_id": user_id,
                    "service": target_service,
                    "file_id": file_id,
                    "file_name": file_name,
                    "reward": db.get("settings", {}).get("rates", {}).get("admin_file", 1200.0),
                    "status": "pending",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                del db["user_states"][u_key]
                save_data(db)

                e_wait = render_emoji_text("ntf_wait", db, "⏳")
                rew_str = format_taka(db.get("settings", {}).get("rates", {}).get("admin_file", 1200.0), (user_lang == "bn"))
                deal_succ = (
                    f"{e_wait} <b>Your Admin Deal file has been submitted!</b>\nAdmin will review and credit <b>{rew_str}</b> to your balance."
                    if user_lang == "en"
                    else f"{e_wait} <b>আপনার এডমিন ডিল ফাইলটি সফলভাবে জমা নেওয়া হয়েছে!</b>\nএডমিন ফাইলটি যাচাই করে আপনার একাউন্টে <b>{rew_str}</b> যুক্ত করে দেবে।"
                )

                await msg.reply_text(deal_succ, parse_mode=ParseMode.HTML, reply_markup=get_user_main_menu_keyboard(user_id, db))

                deal_adm_kb = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Approve ডিল", callback_data=f"adm_app_deal_{deal_id}"),
                        InlineKeyboardButton("❌ Reject ডিল", callback_data=f"adm_rej_deal_{deal_id}")
                    ]
                ])
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"📁 <b>নতুন এডমিন ফাইল জমা পড়েছে!</b>\n\n🆔 ডিল আইডি: <code>{deal_id}</code>\n👤 ইউজার: <code>{user_id}</code>\n🌐 সার্ভিস: <b>{target_service.capitalize()}</b>\n📄 ফাইল/ডাটা: <code>{file_name}</code>",
                        parse_mode=ParseMode.HTML,
                        reply_markup=deal_adm_kb
                    )
                    if file_id != "raw_text":
                        await context.bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=f"📄 ইউজার {user_id}-এর জমা দেওয়া ফাইল")
                except Exception:
                    pass
                return

            if act == "wd_wait_addr":
                db["user_states"][u_key]["address"] = text
                db["user_states"][u_key]["action"] = "wd_wait_amount"
                save_data(db)

                is_bn = (user_lang == "bn")
                min_wd = format_taka(db.get("settings", {}).get("min_withdraw", 50.0), is_bn)
                chg = format_taka(db.get("settings", {}).get("withdraw_charge", 5.0), is_bn)
                await msg.reply_text(
                    get_lang_text("enter_wd_amt", user_lang, {"min": min_wd, "charge": chg}, db),
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_cancel_reply_keyboard(db, user_lang)
                )
                return

            if act == "wd_wait_amount":
                clean_amt = from_bangla_num(text)
                try:
                    amt = float(clean_amt)
                except ValueError:
                    amt = 0.0

                min_wd = float(db.get("settings", {}).get("min_withdraw", 50.0))
                charge = float(db.get("settings", {}).get("withdraw_charge", 5.0))
                user_bal = float(db.get("users", {}).get(u_key, {}).get("balance", 0.0))

                if amt < min_wd or amt > user_bal or amt <= charge:
                    await msg.reply_text(
                        get_lang_text("invalid_amt", user_lang, {"min": format_taka(min_wd, (user_lang == "bn"))}, db),
                        parse_mode=ParseMode.HTML
                    )
                    return

                net_payable = max(0.0, amt - charge)
                db["users"][u_key]["balance"] -= amt
                wd_id = "wd_" + uuid.uuid4().hex[:8]
                address = db["user_states"][u_key].get("address", "")

                db.setdefault("withdrawals", {})[wd_id] = {
                    "id": wd_id,
                    "user_id": user_id,
                    "amount": amt,
                    "charge": charge,
                    "net_amount": net_payable,
                    "address": address,
                    "status": "pending",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                del db["user_states"][u_key]
                save_data(db)

                is_bn = (user_lang == "bn")
                amt_str = format_taka(amt, is_bn)
                chg_str = format_taka(charge, is_bn)
                net_str = format_taka(net_payable, is_bn)

                await msg.reply_text(
                    get_lang_text("wd_success", user_lang, {"amt": amt_str, "charge": chg_str, "net": net_str}, db),
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_user_main_menu_keyboard(user_id, db)
                )

                adm_kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 কপি এড্রেস", callback_data=f"copynum_{address}")],
                    [
                        InlineKeyboardButton("✅ Approve (পরিশোধিত)", callback_data=f"adm_app_wd_{wd_id}"),
                        InlineKeyboardButton("❌ Reject (বাতিল)", callback_data=f"adm_rej_wd_{wd_id}")
                    ]
                ])
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"💳 <b>নতুন উইথড্রল রিকোয়েস্ট!</b>\n\n🆔 ইউজার: <code>{user_id}</code>\n💵 মোট উইথড্র: <b>{amt_str}</b>\n⚡ চার্জ কাটা হয়েছে: <b>{chg_str}</b>\n💰 ইউজার পাবে: <b>{net_str}</b>\n📍 এড্রেস: <code>{address}</code>",
                        parse_mode=ParseMode.HTML,
                        reply_markup=adm_kb
                    )
                except Exception:
                    pass
                return

        # /start কমান্ড
        if text.startswith("/start"):
            await send_welcome_message(context, chat_id, user_id, name, db)
            return

        # লিডারবোর্ড বাটন
        if "লিডারবোর্ড" in text or "Leaderboard" in text:
            await show_leaderboard(update, context, db)
            return

        # ব্যালেন্স বাটন
        if "ব্যালেন্স" in text or "Balance" in text:
            u = db.get("users", {}).get(u_key, {})
            usd_rate = float(db.get("settings", {}).get("usd_to_bdt", 120.0))
            if usd_rate <= 0:
                usd_rate = 120.0

            bal_bdt = float(u.get("balance", 0.0))
            bal_usd = bal_bdt / usd_rate

            pend_wd_bdt = sum(
                float(w.get("amount", 0)) for w in db.get("withdrawals", {}).values()
                if str(w.get("user_id")) == u_key and w.get("status") == "pending"
            )
            pend_wd_usd = pend_wd_bdt / usd_rate

            tot_earn_bdt = float(u.get("total_earned", 0.0))
            tot_earn_usd = tot_earn_bdt / usd_rate

            completed_tasks = int(u.get("tasks_completed", 0))
            in_review_tasks = sum(
                1 for t in db.get("tasks", {}).values()
                if str(t.get("user_id")) == u_key and t.get("status") == "pending"
            )

            e_user = render_emoji_text("bal_ic_user", db, "👨‍💻")
            e_bal = render_emoji_text("bal_ic_main", db, "💰")
            e_pend = render_emoji_text("bal_ic_pend", db, "🔄")
            e_earn = render_emoji_text("bal_ic_earned", db, "💲")
            e_done = render_emoji_text("bal_ic_done", db, "✅")
            e_wait = render_emoji_text("ntf_wait", db, "⏳")

            if user_lang == "en":
                bal_txt = (
                    f"{e_user} <b>Your Account Balance:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{e_bal} <b>Balance:</b> {bal_bdt:.2f} BDT (${bal_usd:.3f})\n"
                    f"{e_pend} <b>Pending Withdraw:</b> {pend_wd_bdt:.2f} BDT (${pend_wd_usd:.3f})\n"
                    f"{e_earn} <b>Total Income:</b> {tot_earn_bdt:.2f} BDT (${tot_earn_usd:.3f})\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"{e_done} <b>Completed Tasks:</b> {completed_tasks}\n"
                    f"{e_wait} <b>In Review:</b> {in_review_tasks}"
                )
            else:
                bal_txt = (
                    f"{e_user} <b>আপনার একাউন্ট ব্যালেন্স:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{e_bal} <b>ব্যালেন্স:</b> {to_bangla_num(f'{bal_bdt:.2f}')} ৳ (${to_bangla_num(f'{bal_usd:.3f}')})\n"
                    f"{e_pend} <b>পেন্ডিং উইথড্র:</b> {to_bangla_num(f'{pend_wd_bdt:.2f}')} ৳ (${to_bangla_num(f'{pend_wd_usd:.3f}')})\n"
                    f"{e_earn} <b>সর্বমোট আয়:</b> {to_bangla_num(f'{tot_earn_bdt:.2f}')} ৳ (${to_bangla_num(f'{tot_earn_usd:.3f}')})\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"{e_done} <b>সম্পন্ন কাজ:</b> {to_bangla_num(completed_tasks)} টি\n"
                    f"{e_wait} <b>রিভিউতে আছে:</b> {to_bangla_num(in_review_tasks)} টি"
                )

            await msg.reply_text(bal_txt, parse_mode=ParseMode.HTML, reply_markup=get_user_main_menu_keyboard(user_id, db))
            return

        # কাজ বাটন
        if "কাজ" in text or "Tasks" in text:
            st = db.get("settings", {}).get("task_status", {
                "instagram": "ON", "facebook": "ON", "gmail": "ON", "admin_file": "ON"
            })
            any_active = any(st.get(k, "ON") == "ON" for k in ["instagram", "facebook", "gmail", "admin_file"])

            if not any_active:
                e_off = render_emoji_text("ntf_task_off", db, "🛑")
                no_task_msg = (
                    f"{e_off} <b>All tasks are temporarily closed! New tasks will arrive soon.</b>"
                    if user_lang == "en"
                    else f"{e_off} <b>বর্তমানে সকল কাজ সাময়িকভাবে বন্ধ রয়েছে! নতুন কাজ আসলে আবার চালু করা হবে।</b>"
                )
                await msg.reply_text(no_task_msg, parse_mode=ParseMode.HTML, reply_markup=get_user_main_menu_keyboard(user_id, db))
                return

            await msg.reply_text(
                get_lang_text("select_task", user_lang, {}, db),
                parse_mode=ParseMode.HTML,
                reply_markup=get_task_menu_keyboard(user_id, db)
            )
            return

        # ১. Instagram টাস্ক
        if "Instagram" in text and "ফাইল" not in text and "Deal" not in text:
            if db.get("settings", {}).get("task_status", {}).get("instagram", "ON") == "OFF":
                e_off = render_emoji_text("ntf_task_off", db, "🛑")
                await msg.reply_text(f"{e_off} <b>Instagram-এর কাজ বর্তমানে বন্ধ আছে!</b>", parse_mode=ParseMode.HTML, reply_markup=get_task_menu_keyboard(user_id, db))
                return

            ig_mode = db.get("settings", {}).get("ig_mode", "2fa")
            ig_names = ["rakib", "sakib", "humayun", "tanvir", "sabbir", "fahim", "imran", "mahmud", "hasan", "arif", "rashed", "nayeem", "shuvo", "tarek", "sohel", "masud", "rohan", "jisan", "emon", "ripon", "shakil", "nadim", "parvez", "sujon"]
            import random
            picked_name = random.choice(ig_names)
            rand_user = f"{picked_name}_{random.randint(100, 9999)}"
            task_pass = db.get("settings", {}).get("default_task_pass", "Pass@2026#Secure")
            rate_str = format_taka(db.get("settings", {}).get("rates", {}).get("instagram", 10.0), (user_lang == "bn"))

            e_ntf = render_emoji_text("ntf_ig", db, "📸")
            e_money = render_emoji_text("task_ic_money", db, "💰")
            e_user = render_emoji_text("task_ic_user", db, "👤")
            e_pass = render_emoji_text("task_ic_pass", db, "🔑")

            if ig_mode == "cookies":
                db["user_states"][u_key] = {
                    "action": "ig_wait_cookie",
                    "username": rand_user,
                    "password": task_pass
                }
                save_data(db)

                if user_lang == "en":
                    t_msg = (
                        f"{e_ntf} <b>Instagram Account Task (Cookies Mode)</b>\n\n"
                        f"{e_money} <b>Reward:</b> <b>{rate_str}</b>\n\n"
                        f"{e_user} <b>Username:</b> <code>{rand_user}</code>\n"
                        f"{e_pass} <b>Password:</b> <code>{task_pass}</code>\n\n"
                        "📌 Create the account and paste your <b>Instagram Cookies</b> here:"
                    )
                else:
                    t_msg = (
                        f"{e_ntf} <b>Instagram Account Task (কুকিজ মোড)</b>\n\n"
                        f"{e_money} <b>পারিশ্রমিক:</b> <b>{rate_str}</b>\n\n"
                        f"{e_user} <b>ইউজারনেম:</b> <code>{rand_user}</code>\n"
                        f"{e_pass} <b>পাসওয়ার্ড:</b> <code>{task_pass}</code>\n\n"
                        "📌 ওপরের ডিটেইলস দিয়ে একাউন্ট খুলে আপনার <b>Instagram Cookies</b> পেস্ট করে পাঠান:"
                    )
                await msg.reply_text(t_msg, parse_mode=ParseMode.HTML, reply_markup=get_cancel_reply_keyboard(db, user_lang))
            else:
                db["user_states"][u_key] = {
                    "action": "ig_ready_2fa_btn",
                    "username": rand_user,
                    "password": task_pass
                }
                save_data(db)

                if user_lang == "en":
                    t_msg = (
                        f"{e_ntf} <b>Instagram Account Creation Task</b>\n\n"
                        f"{e_money} <b>Reward:</b> <b>{rate_str}</b>\n\n"
                        f"{e_user} <b>Username:</b> <code>{rand_user}</code>\n"
                        f"{e_pass} <b>Password:</b> <code>{task_pass}</code>\n\n"
                        "📌 Create the account with above username and password.\n"
                        "When done, click the <b>'2FA Key'</b> button below:"
                    )
                else:
                    t_msg = (
                        f"{e_ntf} <b>Instagram Account Creation Task</b>\n\n"
                        f"{e_money} <b>পারিশ্রমিক:</b> <b>{rate_str}</b>\n\n"
                        f"{e_user} <b>ইউজারনেম:</b> <code>{rand_user}</code>\n"
                        f"{e_pass} <b>পাসওয়ার্ড:</b> <code>{task_pass}</code>\n\n"
                        "📌 ওপরের ইউজারনেম ও পাসওয়ার্ড দিয়ে একাউন্ট তৈরি করুন।\n"
                        "একাউন্ট তৈরি শেষ হলে নিচের <b>'2FA Key'</b> বাটনে চাপ দিন:"
                    )
                await msg.reply_text(t_msg, parse_mode=ParseMode.HTML, reply_markup=get_2fa_key_reply_keyboard(db, user_lang))
            return

        # ২. Facebook টাস্ক
        if "Facebook" in text and "ফাইল" not in text and "Deal" not in text:
            if db.get("settings", {}).get("task_status", {}).get("facebook", "ON") == "OFF":
                e_off = render_emoji_text("ntf_task_off", db, "🛑")
                await msg.reply_text(f"{e_off} <b>Facebook-এর কাজ বর্তমানে বন্ধ আছে!</b>", parse_mode=ParseMode.HTML, reply_markup=get_task_menu_keyboard(user_id, db))
                return

            first_names = ["Rakib", "Sakib", "Humayun", "Shakil", "Tanvir", "Arif", "Sabbir", "Rashed", "Mahmud", "Nayeem", "Hasan", "Imran", "Fahim", "Shuvo", "Tarek"]
            last_names = ["Hossain", "Ahmed", "Khan", "Islam", "Chowdhury", "Rahman", "Mia", "Sikder", "Mondol", "Sheikh", "Talukder"]
            import random
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            task_pass = db.get("settings", {}).get("default_task_pass", "Pass@2026#Secure")
            rate_str = format_taka(db.get("settings", {}).get("rates", {}).get("facebook", 12.0), (user_lang == "bn"))

            db["user_states"][u_key] = {
                "action": "fb_wait_uid",
                "first_name": fn,
                "last_name": ln,
                "password": task_pass
            }
            save_data(db)

            e_ntf = render_emoji_text("ntf_fb", db, "📘")
            e_money = render_emoji_text("task_ic_money", db, "💰")
            e_user = render_emoji_text("task_ic_user", db, "👤")
            e_pass = render_emoji_text("task_ic_pass", db, "🔑")

            if user_lang == "en":
                t_msg = (
                    f"{e_ntf} <b>Facebook Account Task</b>\n\n"
                    f"{e_money} <b>Reward:</b> <b>{rate_str}</b>\n\n"
                    f"{e_user} <b>First Name:</b> <code>{fn}</code>\n"
                    f"{e_user} <b>Last Name:</b> <code>{ln}</code>\n"
                    f"{e_pass} <b>Password:</b> <code>{task_pass}</code>\n\n"
                    "📌 Create the Facebook account with above details, then send your <b>Facebook UID</b>:"
                )
            else:
                t_msg = (
                    f"{e_ntf} <b>Facebook Account Task</b>\n\n"
                    f"{e_money} <b>পারিশ্রমিক:</b> <b>{rate_str}</b>\n\n"
                    f"{e_user} <b>First Name:</b> <code>{fn}</code>\n"
                    f"{e_user} <b>Last Name:</b> <code>{ln}</code>\n"
                    f"{e_pass} <b>পাসওয়ার্ড:</b> <code>{task_pass}</code>\n\n"
                    "📌 ওপরের নাম ও পাসওয়ার্ড দিয়ে ফ্রেশ ফেসবুক আইডি খুলে শুধু আপনার <b>Facebook UID</b> লিখে পাঠান:"
                )
            await msg.reply_text(t_msg, parse_mode=ParseMode.HTML, reply_markup=get_cancel_reply_keyboard(db, user_lang))
            return

        # ৩. Gmail টাস্ক
        if "Gmail" in text and "ফাইল" not in text and "Deal" not in text:
            if db.get("settings", {}).get("task_status", {}).get("gmail", "ON") == "OFF":
                e_off = render_emoji_text("ntf_task_off", db, "🛑")
                await msg.reply_text(f"{e_off} <b>Gmail-এর কাজ বর্তমানে বন্ধ আছে!</b>", parse_mode=ParseMode.HTML, reply_markup=get_task_menu_keyboard(user_id, db))
                return

            rate_str = format_taka(db.get("settings", {}).get("rates", {}).get("gmail", 8.0), (user_lang == "bn"))
            db["user_states"][u_key] = {"action": "gm_wait_email"}
            save_data(db)

            e_ntf = render_emoji_text("ntf_gmail", db, "📧")
            e_money = render_emoji_text("task_ic_money", db, "💰")

            if user_lang == "en":
                t_msg = (
                    f"{e_ntf} <b>Gmail Submission Task</b>\n\n"
                    f"{e_money} <b>Reward:</b> <b>{rate_str}</b>\n\n"
                    "📌 Send your fresh Gmail address from your mobile device:"
                )
            else:
                t_msg = (
                    f"{e_ntf} <b>Gmail Submission Task</b>\n\n"
                    f"{e_money} <b>পারিশ্রমিক:</b> <b>{rate_str}</b>\n\n"
                    "📌 আপনার ফোনে থাকা ফ্রেশ Gmail এড্রেসটি লিখে পাঠান:"
                )
            await msg.reply_text(t_msg, parse_mode=ParseMode.HTML, reply_markup=get_cancel_reply_keyboard(db, user_lang))
            return

        # ৪. এডমিন ফাইল
        if "এডমিন ফাইল" in text or "Admin Deal" in text:
            if db.get("settings", {}).get("task_status", {}).get("admin_file", "ON") == "OFF":
                e_off = render_emoji_text("ntf_task_off", db, "🛑")
                await msg.reply_text(f"{e_off} <b>এডমিন ফাইলের কাজ বর্তমানে বন্ধ আছে!</b>", parse_mode=ParseMode.HTML, reply_markup=get_task_menu_keyboard(user_id, db))
                return

            bulk_rate = format_taka(db.get("settings", {}).get("rates", {}).get("admin_file", 1200.0), (user_lang == "bn"))
            t_msg = (
                "📁 <b>এডমিন ডিল ও ফাইল সাবমিশন</b>\n\n"
                "📢 <b>বর্তমান নোটিশ:</b>\n"
                f"এডমিন ফাইলে রেট দেওয়া আছে <b>{bulk_rate}</b> (প্রতি ১০০ টি ফ্রেশ একাউন্ট)।\n\n"
                "আপনি কি এই কাজটি করতে চান? নিচে থেকে সার্ভিস বেছে নিন:"
            )

            deal_kb = ReplyKeyboardMarkup([
                [KeyboardButton(create_styled_button_text("Instagram ফাইল", "ig_file", db)), KeyboardButton(create_styled_button_text("Facebook ফাইল", "fb_file", db))],
                [KeyboardButton(create_styled_button_text("Gmail ফাইল", "gmail_file", db))],
                [KeyboardButton(create_styled_button_text(get_lang_text("menu_back", user_lang), "back", db))]
            ], resize_keyboard=True)

            await msg.reply_text(t_msg, parse_mode=ParseMode.HTML, reply_markup=deal_kb)
            return

        if "Instagram ফাইল" in text or "Facebook ফাইল" in text or "Gmail ফাইল" in text:
            srv = "instagram" if "Instagram" in text else ("facebook" if "Facebook" in text else "gmail")
            db["user_states"][u_key] = {"action": "admin_deal_wait_file", "service": srv}
            save_data(db)

            deal_msg = (
                f"📁 <b>{srv.capitalize()} ফাইল সাবমিশন:</b>\n\n"
                "⚠️ <b>শর্ত:</b> মিনিমাম ১০০ টা একাউন্ট জমা দিতে হবে।\n"
                "দয়া করে আপনার একাউন্টগুলোর ফাইলটি (TXT/DOC/ZIP) এখানে সেন্ড করুন:"
            )
            await msg.reply_text(deal_msg, parse_mode=ParseMode.HTML, reply_markup=get_cancel_reply_keyboard(db, user_lang))
            return

        # উইথড্রল মেনু বাটন
        if "উইথড্রল" in text or "Withdrawal" in text:
            if db.get("settings", {}).get("withdraw_status", "ON") == "OFF":
                await msg.reply_text(get_lang_text("withdraw_off", user_lang, {}, db), parse_mode=ParseMode.HTML)
                return

            is_bn = (user_lang == "bn")
            min_wd = format_taka(db.get("settings", {}).get("min_withdraw", 50.0), is_bn)
            chg = format_taka(db.get("settings", {}).get("withdraw_charge", 5.0), is_bn)
            user_bal = format_taka(db.get("users", {}).get(u_key, {}).get("balance", 0.0), is_bn)

            wd_menu = ReplyKeyboardMarkup([
                [KeyboardButton(create_styled_button_text("Binance (BEP20)", "binance", db))],
                [KeyboardButton(create_styled_button_text(get_lang_text("menu_back", user_lang), "back", db))]
            ], resize_keyboard=True)

            await msg.reply_text(
                get_lang_text("withdraw_info", user_lang, {"min": min_wd, "bal": user_bal, "charge": chg}, db),
                parse_mode=ParseMode.HTML,
                reply_markup=wd_menu
            )
            return

        if "Binance (BEP20)" in text:
            user_bal = float(db.get("users", {}).get(u_key, {}).get("balance", 0.0))
            min_wd = float(db.get("settings", {}).get("min_withdraw", 50.0))
            if user_bal < min_wd:
                await msg.reply_text(
                    get_lang_text("invalid_amt", user_lang, {"min": format_taka(min_wd, (user_lang == "bn"))}, db),
                    parse_mode=ParseMode.HTML
                )
                return

            db["user_states"][u_key] = {"action": "wd_wait_addr"}
            save_data(db)

            await msg.reply_text(
                get_lang_text("enter_bep20", user_lang, {}, db),
                parse_mode=ParseMode.HTML,
                reply_markup=get_cancel_reply_keyboard(db, user_lang)
            )
            return

        # রেফারেল মেনু বাটন
        if "রেফার" in text or "Referral" in text:
            bot_user = "EasyCashEarn_bot"
            ref_link = f"https://t.me/{bot_user}?start={user_id}"
            u = db.get("users", {}).get(u_key, {})
            usd_rate = float(db.get("settings", {}).get("usd_to_bdt", 120.0))
            if usd_rate <= 0:
                usd_rate = 120.0

            ref_count = int(u.get("referrals", 0))
            ref_inc_bdt = float(u.get("ref_income", 0.0))
            ref_inc_usd = ref_inc_bdt / usd_rate

            import urllib.parse
            share_url = "https://t.me/share/url?url=" + urllib.parse.quote(ref_link) + "&text=" + urllib.parse.quote("সহজ কাজ করে প্রতিদিন আয় করতে আমাদের আর্নিং বটে জয়েন করুন!")

            e_user = render_emoji_text("bal_ic_user", db, "👨‍💻")
            e_lnk = render_emoji_text("ref_ic_link", db, "🔗")
            e_cnt = render_emoji_text("ref_ic_count", db, "👥")
            e_inc = render_emoji_text("ref_ic_income", db, "💰")
            e_rew = render_emoji_text("ref_ic_reward", db, "🎁")

            if user_lang == "en":
                type_desc = f"{db.get('settings', {}).get('ref_commission_pct', 20.0)}% Commission" if db.get("settings", {}).get("referral_mode") == "commission" else f"{float(db.get('settings', {}).get('ref_direct_bonus', 5.0)):.2f} BDT Bonus"
                ref_text = (
                    f"{e_user} <b>Your Referral Dashboard:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{e_lnk} <b>Referral Link:</b>\n<code>{ref_link}</code>\n\n"
                    f"{e_cnt} <b>Total Referrals:</b> {ref_count} Users\n"
                    f"{e_inc} <b>Referral Income:</b> {ref_inc_bdt:.2f} BDT (${ref_inc_usd:.3f})\n"
                    f"{e_rew} <b>Reward System:</b> {type_desc}\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "🚀 <i>Share your link with friends to earn commission on every completed task!</i>"
                )
            else:
                type_desc = f"{to_bangla_num(db.get('settings', {}).get('ref_commission_pct', 20.0))}% কমিশন" if db.get("settings", {}).get("referral_mode") == "commission" else f"{format_taka(db.get('settings', {}).get('ref_direct_bonus', 5.0))} ফিক্সড বোনাস"
                ref_text = (
                    f"{e_user} <b>আপনার রেফারেল ড্যাশবোর্ড:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{e_lnk} <b>রেফারেল লিংক:</b>\n<code>{ref_link}</code>\n\n"
                    f"{e_cnt} <b>মোট রেফারেল:</b> {to_bangla_num(ref_count)} জন\n"
                    f"{e_inc} <b>রেফার থেকে আয়:</b> {to_bangla_num(f'{ref_inc_bdt:.2f}')} ৳ (${to_bangla_num(f'{ref_inc_usd:.3f}')})\n"
                    f"{e_rew} <b>রেফারেল বোনাস:</b> {type_desc}\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "🚀 <i>বন্ধুদের সাথে লিংক শেয়ার করে প্রতিটি কাজ থেকে কমিশন আয় করুন!</i>"
                )

            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 Copy Link" if user_lang == "en" else "📋 কপি লিংক", callback_data=f"copynum_{ref_link}"),
                    InlineKeyboardButton("🚀 Share Link" if user_lang == "en" else "🚀 শেয়ার করুন", url=share_url)
                ]
            ])

            await msg.reply_text(ref_text, parse_mode=ParseMode.HTML, reply_markup=kb)
            return

        # আমি নতুন বাটন
        if "আমি নতুন" in text or "I am New" in text:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(create_styled_button_text("Instagram কাজের ভিডিও", "btn_new_ig", db), callback_data="view_vid_instagram")],
                [InlineKeyboardButton(create_styled_button_text("Facebook কাজের ভিডিও", "btn_new_fb", db), callback_data="view_vid_facebook")],
                [InlineKeyboardButton(create_styled_button_text("Gmail কাজের ভিডিও", "btn_new_gmail", db), callback_data="view_vid_gmail")],
                [InlineKeyboardButton(create_styled_button_text("Close", "btn_new_close", db), callback_data="c_cancel")]
            ])
            await msg.reply_text(get_lang_text("new_help_select", user_lang, {}, db), parse_mode=ParseMode.HTML, reply_markup=kb)
            return

        # ভাষা বাটন
        if "ভাষা" in text or "Language" in text:
            lang_menu = ReplyKeyboardMarkup([
                [KeyboardButton(create_styled_button_text("বাংলা", "lang_bn", db)), KeyboardButton(create_styled_button_text("English", "lang_en", db))],
                [KeyboardButton(create_styled_button_text(get_lang_text("menu_back", user_lang), "back", db))]
            ], resize_keyboard=True)

            e_lang = render_emoji_text("btn_lang", db, "🌐")
            await msg.reply_text(f"{e_lang} <b>Select Language / ভাষা নির্বাচন করুন:</b>", parse_mode=ParseMode.HTML, reply_markup=lang_menu)
            return

        if "বাংলা" in text:
            db["users"][u_key]["lang"] = "bn"
            save_data(db)
            await msg.reply_text(get_lang_text("lang_changed", "bn", {}, db), reply_markup=get_user_main_menu_keyboard(user_id, db))
            return

        if "English" in text:
            db["users"][u_key]["lang"] = "en"
            save_data(db)
            await msg.reply_text(get_lang_text("lang_changed", "en", {}, db), reply_markup=get_user_main_menu_keyboard(user_id, db))
            return

# ----------------------------------------------------
# কলব্যাক কুয়েরি হ্যান্ডলার
# ----------------------------------------------------
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cb = update.callback_query
    if not cb or not cb.data:
        return

    data = cb.data
    user_id = cb.from_user.id
    u_key = str(user_id)
    chat_id = cb.message.chat.id if cb.message else user_id
    message_id = cb.message.message_id if cb.message else 0
    is_admin = (user_id == ADMIN_ID)

    async with db_lock:
        db = load_data()
        user_lang = db.get("users", {}).get(u_key, {}).get("lang", "bn")

        if data == "noop":
            await cb.answer()
            return

        if data == "c_cancel":
            await cb.answer()
            if cb.message:
                await cb.message.delete()
            return

        if data == "cancel_admin_action":
            if not is_admin:
                return
            db["admin_state"] = {}
            save_data(db)
            await cb.answer("বাতিল করা হয়েছে")
            if cb.message:
                await cb.message.delete()
            return

        if data.startswith("copynum_"):
            val = data.replace("copynum_", "")
            await cb.answer(f"কপি হয়েছে: {val}", show_alert=True)
            return

        # মেম্বারশিপ ভেরিফিকেশন
        if data == "verify_join":
            channels = db.get("channels", [])
            unjoined = await get_unjoined_channels(context.bot, user_id, channels)

            if not unjoined:
                db.setdefault("users", {}).setdefault(u_key, {})["is_verified"] = True
                save_data(db)
                succ_msg = "✅ Verification successful! Welcome." if user_lang == "en" else "✅ ভেরিফিকেশন সফল হয়েছে! আপনাকে স্বাগতম।"
                await cb.answer(succ_msg, show_alert=True)
                if cb.message:
                    await cb.message.delete()
                u_name = db.get("users", {}).get(u_key, {}).get("name", "User")
                await send_welcome_message(context, chat_id, user_id, u_name, db)
            else:
                fail_msg = "❌ You have not joined all channels yet! Please join and retry." if user_lang == "en" else "❌ আপনি এখনো সব চ্যানেলে জয়েন করেননি! দয়া করে জয়েন করে আবার ভেরিফাই করুন।"
                await cb.answer(fail_msg, show_alert=True)
            return

        # ভিডিও টিউটোরিয়াল দেখা
        if data.startswith("view_vid_"):
            v_type = data.replace("view_vid_", "")
            vid_data = db.get("settings", {}).get("videos", {}).get(v_type, "")
            await cb.answer()

            if not vid_data:
                await context.bot.send_message(chat_id=chat_id, text=get_lang_text("no_video", user_lang, {}, db), parse_mode=ParseMode.HTML)
                return

            if vid_data.startswith("FILE:"):
                file_id = vid_data[5:]
                try:
                    await context.bot.send_video(chat_id=chat_id, video=file_id, caption=f"🎬 <b>{v_type.capitalize()} কাজের টিউটোরিয়াল ভিডিও</b>", parse_mode=ParseMode.HTML)
                except Exception as e:
                    logger.error(f"Error sending video file: {e}")
            else:
                await context.bot.send_message(chat_id=chat_id, text=f"🎬 <b>{v_type.capitalize()} কাজের ভিডিও লিংক:</b>\n\n{vid_data}", parse_mode=ParseMode.HTML)
            return

        # এডমিন-অনলি কলব্যাকসমূহ
        if not is_admin:
            return

        if data.startswith("adm_tog_task_"):
            t_key = data.replace("adm_tog_task_", "")
            cur = db.get("settings", {}).get("task_status", {}).get(t_key, "ON")
            new_st = "OFF" if cur == "ON" else "ON"
            db.setdefault("settings", {}).setdefault("task_status", {})[t_key] = new_st
            save_data(db)

            msg_alert = f"{t_key.capitalize()} কাজ এখন {'চালু (ON)' if new_st == 'ON' else 'বন্ধ (OFF)'} করা হয়েছে!"
            await cb.answer(msg_alert, show_alert=True)
            if cb.message:
                await cb.message.edit_reply_markup(reply_markup=build_task_status_inline_keyboard(db))
            return

        if data == "adm_tog_ig_mode":
            cur_mode = db.get("settings", {}).get("ig_mode", "2fa")
            new_mode = "cookies" if cur_mode == "2fa" else "2fa"
            db.setdefault("settings", {})["ig_mode"] = new_mode
            save_data(db)

            await cb.answer(f"Instagram মোড পরিবর্তন হয়েছে: {new_mode.upper()}", show_alert=True)
            if cb.message:
                await cb.message.edit_reply_markup(reply_markup=build_task_status_inline_keyboard(db))
            return

        if data == "adm_tog_fb_mode":
            cur_mode = db.get("settings", {}).get("fb_mode", "cookies")
            new_mode = "2fa" if cur_mode == "cookies" else "cookies"
            db.setdefault("settings", {})["fb_mode"] = new_mode
            save_data(db)

            await cb.answer(f"Facebook মোড পরিবর্তন হয়েছে: {new_mode.upper()}", show_alert=True)
            if cb.message:
                await cb.message.edit_reply_markup(reply_markup=build_task_status_inline_keyboard(db))
            return

        if data == "adm_tog_wd_status":
            cur = db.get("settings", {}).get("withdraw_status", "ON")
            new_st = "OFF" if cur == "ON" else "ON"
            db.setdefault("settings", {})["withdraw_status"] = new_st
            save_data(db)

            btn_st_text = "🔴 উইথড্রল সিস্টেম বন্ধ করুন (OFF)" if new_st == "ON" else "🟢 উইথড্রল সিস্টেম চালু করুন (ON)"
            min_w = format_taka(db.get("settings", {}).get("min_withdraw", 50))
            chg_w = format_taka(db.get("settings", {}).get("withdraw_charge", 5))

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(btn_st_text, callback_data="adm_tog_wd_status")],
                [InlineKeyboardButton(f"✏️ মিনিমাম উইথড্র কমান/বাড়ান ({min_w})", callback_data="adm_ed_min_wd")],
                [InlineKeyboardButton(f"✏️ উইথড্র চার্জ পরিবর্তন ({chg_w})", callback_data="adm_ed_wd_chg")],
                [InlineKeyboardButton("❌ Close", callback_data="cancel_admin_action")]
            ])
            await cb.answer(f"উইথড্রল সিস্টেম {new_st} করা হয়েছে!", show_alert=True)
            if cb.message:
                await cb.message.edit_text(
                    f"⚙️ <b>উইথড্রল সেটিংস ও লিমিট কন্ট্রোল:</b>\n\n🔹 বর্তমান স্ট্যাটাস: <b>{new_st}</b>\n🔹 ন্যূনতম উইথড্র: <b>{min_w}</b>\n🔹 উইথড্র চার্জ: <b>{chg_w}</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            return

        if data == "adm_ed_min_wd":
            db["admin_state"]["action"] = "set_min_wd"
            save_data(db)
            await cb.answer()
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text="✏️ <b>নতুন মিনিমাম উইথড্র পরিমাণ (বাংলা টাকায়) লিখে পাঠান:</b>\n(যেমন: <code>50</code> বা <code>100</code>)",
                parse_mode=ParseMode.HTML,
                reply_markup=get_cancel_inline_markup()
            )
            return

        if data == "adm_ed_wd_chg":
            db["admin_state"]["action"] = "set_wd_chg"
            save_data(db)
            await cb.answer()
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text="✏️ <b>উইথড্র চার্জ কত টাকা কাটবে তা লিখে পাঠান:</b>\n(যেমন: <code>5</code>)",
                parse_mode=ParseMode.HTML,
                reply_markup=get_cancel_inline_markup()
            )
            return

        if data.startswith("del_chan_"):
            idx = int(data.replace("del_chan_", ""))
            channels = db.get("channels", [])
            if 0 <= idx < len(channels):
                channels.pop(idx)
                db["channels"] = channels
                save_data(db)
                await cb.answer("চ্যানেলটি রিমুভ করা হয়েছে!", show_alert=True)
                if cb.message:
                    await cb.message.delete()
            return

        if data.startswith("adm_addvid_"):
            v_type = data.replace("adm_addvid_", "")
            db["admin_state"]["action"] = f"add_vid_{v_type}"
            save_data(db)
            await cb.answer()
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🎬 <b>{v_type.capitalize()}</b> এর কাজের ভিডিও ফাইল অথবা ভিডিও লিংকটি পাঠান:",
                parse_mode=ParseMode.HTML,
                reply_markup=get_cancel_inline_markup()
            )
            return

        if data.startswith("adm_delvid_"):
            v_type = data.replace("adm_delvid_", "")
            db.setdefault("settings", {}).setdefault("videos", {})[v_type] = ""
            save_data(db)
            await cb.answer(f"{v_type.capitalize()} ভিডিও মুছে ফেলা হয়েছে!", show_alert=True)
            return

        if data in ["set_ref_mode_comm", "set_ref_mode_dir"]:
            mode = "commission" if data == "set_ref_mode_comm" else "direct"
            db.setdefault("settings", {})["referral_mode"] = mode
            save_data(db)
            await cb.answer("রেফারেল মোড আপডেট হয়েছে!", show_alert=True)
            if cb.message:
                await cb.message.delete()
            return

        if data == "adm_set_proof_ch":
            db["admin_state"]["action"] = "set_proof_channel"
            save_data(db)
            await cb.answer()
            await context.bot.send_message(chat_id=ADMIN_ID, text="📢 পেমেন্ট প্রুফ চ্যানেলের ইউজারনেম দিন (যেমন <code>@PaymentChannel</code>):", parse_mode=ParseMode.HTML, reply_markup=get_cancel_inline_markup())
            return

        if data == "adm_rem_proof_ch":
            db.setdefault("settings", {})["proof_channel"] = ""
            save_data(db)
            await cb.answer("প্রুফ চ্যানেল মুছে ফেলা হয়েছে!", show_alert=True)
            if cb.message:
                await cb.message.delete()
            return

        if data.startswith("adm_app_deal_"):
            deal_id = data.replace("adm_app_deal_", "")
            d = db.get("admin_deals", {}).get(deal_id)
            if d and d.get("status") == "pending":
                t_user = str(d["user_id"])
                reward = float(d.get("reward", 0))

                db.setdefault("users", {}).setdefault(t_user, {})
                db["users"][t_user]["balance"] = db["users"][t_user].get("balance", 0.0) + reward
                db["users"][t_user]["total_earned"] = db["users"][t_user].get("total_earned", 0.0) + reward
                db["admin_deals"][deal_id]["status"] = "approved"
                save_data(db)

                await cb.answer("ডিল এপ্রুভ সম্পন্ন!")
                if cb.message:
                    await cb.message.edit_text(f"{cb.message.text}\n\n✅ <b>Approved by Admin!</b>", parse_mode=ParseMode.HTML)

                e_app = render_emoji_text("ntf_approved", db, "🎉")
                rew_str = format_taka(reward)
                try:
                    await context.bot.send_message(
                        chat_id=int(t_user),
                        text=f"{e_app} <b>আপনার এডমিন ডিল ফাইল এপ্রুভ হয়েছে!</b>\nপরিমাণ: <b>{rew_str}</b> আপনার ব্যালেন্সে যোগ করা হয়েছে।",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            return

        if data.startswith("adm_rej_deal_"):
            deal_id = data.replace("adm_rej_deal_", "")
            d = db.get("admin_deals", {}).get(deal_id)
            if d and d.get("status") == "pending":
                db["admin_deals"][deal_id]["status"] = "rejected"
                save_data(db)

                await cb.answer("ডিল রিজেক্ট করা হয়েছে!")
                if cb.message:
                    await cb.message.edit_text(f"{cb.message.text}\n\n❌ <b>Rejected by Admin!</b>", parse_mode=ParseMode.HTML)

                e_rej = render_emoji_text("ntf_rejected", db, "❌")
                try:
                    await context.bot.send_message(
                        chat_id=int(d["user_id"]),
                        text=f"{e_rej} <b>আপনার জমা দেওয়া এডমিন ডিল ফাইলটি বাতিল করা হয়েছে!</b>\nসঠিক ও ফ্রেশ ফাইল দিয়ে পুনরায় জমা দিন।",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            return

        if data.startswith("adm_vtasks_"):
            t_type = data.replace("adm_vtasks_", "")
            pending_tasks = [t for t in db.get("tasks", {}).values() if t.get("type") == t_type and t.get("status") == "pending"]

            if not pending_tasks:
                e_no_task = render_emoji_text("ntf_no_task", db, "📭")
                await cb.answer("আপাতত কোনো কাজ আসে নাই!", show_alert=True)
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"{e_no_task} <b>{t_type.capitalize()}-এ আপাতত কোনো কাজ আসে নাই!</b>", parse_mode=ParseMode.HTML)
                return

            await cb.answer()
            export_btn = InlineKeyboardMarkup([[InlineKeyboardButton("📁 সব কাজ ফাইলের মধ্যে নিন (.txt ডাউনলোড)", callback_data=f"adm_exp_tasks_{t_type}")]])
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📋 <b>{t_type.capitalize()} পেন্ডিং কাজের তালিকা ({len(pending_tasks)} টি):</b>\nসবগুলো কাজ একসাথে ফাইলের মধ্যে নিতে নিচের বাটনে ক্লিক করুন:",
                parse_mode=ParseMode.HTML,
                reply_markup=export_btn
            )

            for pt in pending_tasks:
                rew_str = format_taka(pt.get("reward", 0))
                info = f"🆔 টাস্ক: <code>{pt['id']}</code>\n👤 ইউজার: <code>{pt['user_id']}</code>\n💰 রেট: <b>{rew_str}</b>\n"
                if t_type == "instagram":
                    info += f"👤 ইউজারনেম: <code>{pt.get('username')}</code>\n🔑 পাসওয়ার্ড: <code>{pt.get('password')}</code>\n"
                    if pt.get("cookies"):
                        info += f"🍪 Cookies:\n<code>{pt.get('cookies')}</code>"
                    else:
                        info += f"🔐 2FA: <code>{pt.get('secret')}</code>\n🔢 OTP: <code>{pt.get('otp')}</code>"
                elif t_type == "facebook":
                    info += f"👤 নাম: <code>{pt.get('first_name')} {pt.get('last_name')}</code>\n🆔 UID: <code>{pt.get('uid')}</code>\n🔑 পাসওয়ার্ড: <code>{pt.get('password')}</code>\n"
                    if pt.get("cookies"):
                        info += f"🍪 Cookies:\n<code>{pt.get('cookies')}</code>"
                    else:
                        info += f"🔐 2FA: <code>{pt.get('secret')}</code>\n🔢 OTP: <code>{pt.get('otp')}</code>"
                elif t_type == "gmail":
                    info += f"📧 ইমেইল: <code>{pt.get('email')}</code>\n🔑 পাসওয়ার্ড: <code>{pt.get('password')}</code>"

                act_kb = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Approve", callback_data=f"adm_app_tsk_{pt['id']}"),
                        InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_tsk_{pt['id']}")
                    ]
                ])
                await context.bot.send_message(chat_id=ADMIN_ID, text=info, parse_mode=ParseMode.HTML, reply_markup=act_kb)
            return

        if data.startswith("adm_exp_tasks_"):
            t_type = data.replace("adm_exp_tasks_", "")
            file_content = f"=== ALL PENDING {t_type.upper()} TASKS ===\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n====================================\n\n"
            count = 0

            for t in db.get("tasks", {}).values():
                if t.get("type") == t_type and t.get("status") == "pending":
                    count += 1
                    if t_type == "gmail":
                        file_content += f"{count}. Email: {t.get('email')} | Pass: {t.get('password')} | UserID: {t.get('user_id')}\n"
                    elif t_type == "instagram":
                        extra = f"Cookies: {t.get('cookies')}" if t.get("cookies") else f"2FA: {t.get('secret')}"
                        file_content += f"{count}. Username: {t.get('username')} | Pass: {t.get('password')} | {extra} | UserID: {t.get('user_id')}\n"
                    elif t_type == "facebook":
                        extra = f"Cookies: {t.get('cookies')}" if t.get("cookies") else f"2FA: {t.get('secret')}"
                        file_content += f"{count}. Name: {t.get('first_name')} {t.get('last_name')} | UID: {t.get('uid')} | Pass: {t.get('password')} | {extra} | UserID: {t.get('user_id')}\n"

            if count == 0:
                await cb.answer("আপাতত কোনো কাজ আসে নাই!", show_alert=True)
                return

            await cb.answer("ফাইল তৈরি হচ্ছে...")
            tmp_filename = os.path.join(BASE_DIR, f"{t_type}_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(tmp_filename, "w", encoding="utf-8") as f:
                f.write(file_content)

            try:
                with open(tmp_filename, "rb") as f:
                    await context.bot.send_document(
                        chat_id=ADMIN_ID,
                        document=f,
                        caption=f"📁 <b>{t_type.capitalize()} এর মোট {count} টি পেন্ডিং কাজের ফাইল</b>",
                        parse_mode=ParseMode.HTML
                    )
            finally:
                if os.path.exists(tmp_filename):
                    os.remove(tmp_filename)

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📁 <b>সব কাজ একত্রিত টেক্সট ভিউ:</b>\n\n<blockquote expandable><code>{file_content}</code></blockquote>",
                parse_mode=ParseMode.HTML
            )
            return

        if data.startswith("adm_app_tsk_"):
            t_id = data.replace("adm_app_tsk_", "")
            t = db.get("tasks", {}).get(t_id)
            if t and t.get("status") == "pending":
                t_user = str(t["user_id"])
                reward = float(t.get("reward", 0))

                db.setdefault("users", {}).setdefault(t_user, {})
                db["users"][t_user]["balance"] = db["users"][t_user].get("balance", 0.0) + reward
                db["users"][t_user]["total_earned"] = db["users"][t_user].get("total_earned", 0.0) + reward
                db["users"][t_user]["tasks_completed"] = db["users"][t_user].get("tasks_completed", 0) + 1
                db["tasks"][t_id]["status"] = "approved"

                e_app = render_emoji_text("ntf_approved", db, "🎉")
                ref_by = db["users"][t_user].get("ref_by")
                if ref_by and str(ref_by) in db.get("users", {}) and db.get("settings", {}).get("referral_mode") == "commission":
                    pct = float(db.get("settings", {}).get("ref_commission_pct", 20.0))
                    commission = round((reward * pct) / 100, 2)
                    ref_key = str(ref_by)
                    db["users"][ref_key]["balance"] = db["users"][ref_key].get("balance", 0.0) + commission
                    db["users"][ref_key]["ref_income"] = db["users"][ref_key].get("ref_income", 0.0) + commission
                    db["users"][ref_key]["total_earned"] = db["users"][ref_key].get("total_earned", 0.0) + commission

                    comm_str = format_taka(commission)
                    try:
                        await context.bot.send_message(
                            chat_id=int(ref_by),
                            text=f"{e_app} <b>রেফারেল কমিশন প্রাপ্তি!</b>\nআপনার রেফারেল ইউজারের টাস্ক সফল হওয়ায় আপনি <b>{comm_str}</b> কমিশন পেয়েছেন!",
                            parse_mode=ParseMode.HTML
                        )
                    except Exception:
                        pass

                save_data(db)
                await cb.answer("কাজটি এপ্রুভ করা হয়েছে!")
                if cb.message:
                    await cb.message.edit_text(f"{cb.message.text}\n\n✅ <b>Approved by Admin!</b>", parse_mode=ParseMode.HTML)

                rew_str = format_taka(reward)
                try:
                    await context.bot.send_message(
                        chat_id=int(t["user_id"]),
                        text=f"{e_app} <b>অভিনন্দন! আপনার টাস্ক এপ্রুভ হয়েছে।</b>\n💰 পারিশ্রমিক: <b>{rew_str}</b> আপনার ব্যালেন্সে যুক্ত করা হয়েছে।",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            return

        if data.startswith("adm_rej_tsk_"):
            t_id = data.replace("adm_rej_tsk_", "")
            t = db.get("tasks", {}).get(t_id)
            if t and t.get("status") == "pending":
                db["tasks"][t_id]["status"] = "rejected"
                save_data(db)

                await cb.answer("কাজটি বাতিল করা হয়েছে!")
                if cb.message:
                    await cb.message.edit_text(f"{cb.message.text}\n\n❌ <b>Rejected by Admin!</b>", parse_mode=ParseMode.HTML)

                e_rej = render_emoji_text("ntf_rejected", db, "❌")
                name_ident = t.get("username") or t.get("uid") or t.get("email") or "Task"
                try:
                    await context.bot.send_message(
                        chat_id=int(t["user_id"]),
                        text=f"{e_rej} <b>টাস্ক বাতিল নোটিফিকেশন:</b>\nআপনার জমা দেওয়া কাজ (<code>{name_ident}</code>) সঠিক নিয়মে না করায় বাতিল করা হয়েছে।",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            return

        if data.startswith("adm_app_wd_"):
            w_id = data.replace("adm_app_wd_", "")
            w = db.get("withdrawals", {}).get(w_id)
            if w and w.get("status") == "pending":
                db["withdrawals"][w_id]["status"] = "approved"
                save_data(db)

                await cb.answer("উইথড্রল পরিশোধ সম্পন্ন!")
                if cb.message:
                    await cb.message.edit_text(f"{cb.message.text}\n\n✅ <b>Paid & Approved</b>", parse_mode=ParseMode.HTML)

                e_app = render_emoji_text("ntf_approved", db, "🎉")
                net_str = format_taka(w.get("net_amount", w.get("amount", 0) - w.get("charge", 5)))
                amt_str = format_taka(w.get("amount", 0))
                try:
                    await context.bot.send_message(
                        chat_id=int(w["user_id"]),
                        text=f"{e_app} <b>আপনার উইথড্রল সফলভাবে পরিশোধ করা হয়েছে!</b>\n💵 মোট উইথড্র: <b>{amt_str}</b>\n💰 প্রাপ্ত পেমেন্ট: <b>{net_str}</b>",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass

                proof_ch = db.get("settings", {}).get("proof_channel")
                if proof_ch:
                    proof_post = (
                        f"{e_app} <b>New Withdrawal Paid!</b>\n\n"
                        f"👤 User ID: <code>{str(w['user_id'])[:4]}***</code>\n"
                        f"💵 Amount: <b>{amt_str}</b> (Paid: {net_str})\n"
                        "🟡 Gateway: <b>Binance (BEP20)</b>\n"
                        f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"🤖 Bot: @{db.get('settings', {}).get('bot_username')}"
                    )
                    try:
                        await context.bot.send_message(chat_id=proof_ch, text=proof_post, parse_mode=ParseMode.HTML)
                    except Exception as e:
                        logger.error(f"Failed to post to proof channel: {e}")
            return

        if data.startswith("adm_rej_wd_"):
            w_id = data.replace("adm_rej_wd_", "")
            w = db.get("withdrawals", {}).get(w_id)
            if w and w.get("status") == "pending":
                db["withdrawals"][w_id]["status"] = "rejected"
                t_user = str(w["user_id"])
                db["users"][t_user]["balance"] = db["users"][t_user].get("balance", 0.0) + float(w.get("amount", 0))
                save_data(db)

                await cb.answer("উইথড্রল বাতিল এবং রিফান্ড করা হয়েছে!")
                if cb.message:
                    await cb.message.edit_text(f"{cb.message.text}\n\n❌ <b>Rejected & Refunded</b>", parse_mode=ParseMode.HTML)

                e_rej = render_emoji_text("ntf_rejected", db, "❌")
                amt_str = format_taka(w.get("amount", 0))
                try:
                    await context.bot.send_message(
                        chat_id=int(t_user),
                        text=f"{e_rej} <b>আপনার উইথড্রল রিকোয়েস্ট বাতিল করা হয়েছে!</b>\nআপনার <b>{amt_str}</b> ব্যালেন্সে ফিরিয়ে দেওয়া হয়েছে।",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            return

        if data.startswith("ed_rate_"):
            t_type = data.replace("ed_rate_", "")
            db["admin_state"]["action"] = f"set_rate_{t_type}"
            save_data(db)

            await cb.answer()
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✏️ <b>{t_type.capitalize()}</b> এর নতুন রেট বাংলা টাকায় লিখে পাঠান (যেমন: <code>10</code> বা <code>15</code>):",
                parse_mode=ParseMode.HTML,
                reply_markup=get_cancel_inline_markup()
            )
            return

        # প্রিমিয়াম ইমোজি কনফিগারেশন সাব-মেনু
        if data.startswith("pem_sub_"):
            sub = data.replace("pem_sub_", "")
            p = db.get("settings", {}).get("premium_emojis", {})
            btns = []

            if sub == "taskdata":
                btns = [
                    [InlineKeyboardButton(f"ইউজারনেম আইকন: {format_emoji_badge(p.get('task_ic_user'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_task_ic_user")],
                    [InlineKeyboardButton(f"পাসওয়ার্ড আইকন: {format_emoji_badge(p.get('task_ic_pass'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_task_ic_pass")],
                    [InlineKeyboardButton(f"কুকিজ আইকন: {format_emoji_badge(p.get('task_ic_cookie'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_task_ic_cookie")],
                    [InlineKeyboardButton(f"টাকা/রেট আইকন: {format_emoji_badge(p.get('task_ic_money'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_task_ic_money")],
                    [InlineKeyboardButton(f"2FA কি আইকন: {format_emoji_badge(p.get('task_ic_2fa'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_task_ic_2fa")],
                ]
            elif sub == "channel":
                btns = [
                    [InlineKeyboardButton(f"চ্যানেল বাটন: {format_emoji_badge(p.get('btn_channel'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_channel")],
                    [InlineKeyboardButton(f"ভেরিফাই বাটন: {format_emoji_badge(p.get('btn_verify'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_verify")],
                    [InlineKeyboardButton(f"চ্যানেল নোটিশ আইকন: {format_emoji_badge(p.get('ntf_force_join'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_force_join")],
                ]
            elif sub == "menu":
                btns = [
                    [InlineKeyboardButton(f"ব্যালেন্স বাটন: {format_emoji_badge(p.get('btn_balance'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_balance")],
                    [InlineKeyboardButton(f"কাজ বাটন: {format_emoji_badge(p.get('btn_task'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_task")],
                    [InlineKeyboardButton(f"উইথড্রল বাটন: {format_emoji_badge(p.get('btn_withdraw'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_withdraw")],
                    [InlineKeyboardButton(f"রেফার বাটন: {format_emoji_badge(p.get('btn_refer'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_refer")],
                    [InlineKeyboardButton(f"আমি নতুন বাটন: {format_emoji_badge(p.get('btn_new'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_new")],
                    [InlineKeyboardButton(f"লিডারবোর্ড বাটন: {format_emoji_badge(p.get('btn_leaderboard'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_leaderboard")],
                    [InlineKeyboardButton(f"ভাষা বাটন: {format_emoji_badge(p.get('btn_lang'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_lang")],
                    [InlineKeyboardButton(f"ব্যাক বাটন: {format_emoji_badge(p.get('btn_back'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_back")],
                ]
            elif sub == "task":
                btns = [
                    [InlineKeyboardButton(f"Instagram বাটন: {format_emoji_badge(p.get('btn_ig'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_ig")],
                    [InlineKeyboardButton(f"Facebook বাটন: {format_emoji_badge(p.get('btn_fb'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_fb")],
                    [InlineKeyboardButton(f"Gmail বাটন: {format_emoji_badge(p.get('btn_gmail'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_gmail")],
                    [InlineKeyboardButton(f"এডমিন ফাইল বাটন: {format_emoji_badge(p.get('btn_admin_file'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_admin_file")],
                    [InlineKeyboardButton(f"2FA Key বাটন: {format_emoji_badge(p.get('btn_2fa_key'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_2fa_key")],
                    [InlineKeyboardButton(f"টাস্ক সাবমিট বাটন: {format_emoji_badge(p.get('btn_task_submit'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_task_submit")],
                    [InlineKeyboardButton(f"কাজ বাতিল বাটন: {format_emoji_badge(p.get('btn_task_cancel'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_task_cancel")],
                    [InlineKeyboardButton(f"IG ফাইল বাটন: {format_emoji_badge(p.get('btn_ig_file'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_ig_file")],
                    [InlineKeyboardButton(f"FB ফাইল বাটন: {format_emoji_badge(p.get('btn_fb_file'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_fb_file")],
                    [InlineKeyboardButton(f"Gmail ফাইল বাটন: {format_emoji_badge(p.get('btn_gmail_file'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_gmail_file")],
                ]
            elif sub == "newlang":
                btns = [
                    [InlineKeyboardButton(f"আমি নতুন (Instagram): {format_emoji_badge(p.get('btn_new_ig'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_new_ig")],
                    [InlineKeyboardButton(f"আমি নতুন (Facebook): {format_emoji_badge(p.get('btn_new_fb'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_new_fb")],
                    [InlineKeyboardButton(f"আমি নতুন (Gmail): {format_emoji_badge(p.get('btn_new_gmail'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_new_gmail")],
                    [InlineKeyboardButton(f"আমি নতুন (Close): {format_emoji_badge(p.get('btn_new_close'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_new_close")],
                    [InlineKeyboardButton(f"বাংলা ভাষা বাটন: {format_emoji_badge(p.get('btn_lang_bn'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_lang_bn")],
                    [InlineKeyboardButton(f"English ভাষা বাটন: {format_emoji_badge(p.get('btn_lang_en'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_lang_en")],
                    [InlineKeyboardButton(f"বাইনান্স উইথড্র বাটন: {format_emoji_badge(p.get('btn_binance'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_btn_binance")],
                ]
            elif sub == "ntf":
                btns = [
                    [InlineKeyboardButton(f"অপেক্ষা করুন (Wait নোটিশ): {format_emoji_badge(p.get('ntf_wait'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_wait")],
                    [InlineKeyboardButton(f"ব্যালেন্স নাই / সতর্কতা: {format_emoji_badge(p.get('ntf_no_bal'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_no_bal")],
                    [InlineKeyboardButton(f"উইথড্র মেইন নোটিশ: {format_emoji_badge(p.get('ntf_wd_info'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_wd_info")],
                    [InlineKeyboardButton(f"চার্জ নোটিশ: {format_emoji_badge(p.get('ntf_wd_charge'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_wd_charge")],
                    [InlineKeyboardButton(f"উইথড্র অফ নোটিশ: {format_emoji_badge(p.get('ntf_wd_off'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_wd_off")],
                    [InlineKeyboardButton(f"উইথড্র সাবমিট নোটিশ: {format_emoji_badge(p.get('ntf_wd_done'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_wd_done")],
                    [InlineKeyboardButton(f"কাজ অফ থাকার নোটিশ: {format_emoji_badge(p.get('ntf_task_off'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_task_off")],
                    [InlineKeyboardButton(f"কোনো কাজ আসে নাই নোটিশ: {format_emoji_badge(p.get('ntf_no_task'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_no_task")],
                    [InlineKeyboardButton(f"কাজ বাতিল নোটিশ: {format_emoji_badge(p.get('ntf_cancel'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_cancel")],
                    [InlineKeyboardButton(f"Instagram হেডার নোটিশ: {format_emoji_badge(p.get('ntf_ig'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_ig")],
                    [InlineKeyboardButton(f"Facebook হেডার নোটিশ: {format_emoji_badge(p.get('ntf_fb'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_fb")],
                    [InlineKeyboardButton(f"Gmail হেডার নোটিশ: {format_emoji_badge(p.get('ntf_gmail'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_gmail")],
                    [InlineKeyboardButton(f"Approve সফল নোটিশ: {format_emoji_badge(p.get('ntf_approved'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_approved")],
                    [InlineKeyboardButton(f"Reject বাতিল নোটিশ: {format_emoji_badge(p.get('ntf_rejected'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ntf_rejected")],
                ]
            elif sub == "bal":
                btns = [
                    [InlineKeyboardButton(f"ইউজার আইকন: {format_emoji_badge(p.get('bal_ic_user'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_bal_ic_user")],
                    [InlineKeyboardButton(f"আইডি আইকন: {format_emoji_badge(p.get('bal_ic_id'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_bal_ic_id")],
                    [InlineKeyboardButton(f"ব্যালেন্স আইকন: {format_emoji_badge(p.get('bal_ic_main'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_bal_ic_main")],
                    [InlineKeyboardButton(f"মোট আয় আইকন: {format_emoji_badge(p.get('bal_ic_earned'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_bal_ic_earned")],
                    [InlineKeyboardButton(f"পেন্ডিং কাজ: {format_emoji_badge(p.get('bal_ic_pend'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_bal_ic_pend")],
                    [InlineKeyboardButton(f"সম্পন্ন কাজ: {format_emoji_badge(p.get('bal_ic_done'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_bal_ic_done")],
                ]
            elif sub == "reflb":
                btns = [
                    [InlineKeyboardButton(f"রেফার লিংক: {format_emoji_badge(p.get('ref_ic_link'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ref_ic_link")],
                    [InlineKeyboardButton(f"মোট রেফার: {format_emoji_badge(p.get('ref_ic_count'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ref_ic_count")],
                    [InlineKeyboardButton(f"রেফার ইনকাম: {format_emoji_badge(p.get('ref_ic_income'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ref_ic_income")],
                    [InlineKeyboardButton(f"বোনাস টাইপ: {format_emoji_badge(p.get('ref_ic_reward'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_ref_ic_reward")],
                    [InlineKeyboardButton(f"১ম স্থান (Top 1): {format_emoji_badge(p.get('lb_rank_1'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_lb_rank_1")],
                    [InlineKeyboardButton(f"২য় স্থান (Top 2): {format_emoji_badge(p.get('lb_rank_2'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_lb_rank_2")],
                    [InlineKeyboardButton(f"৩য় স্থান (Top 3): {format_emoji_badge(p.get('lb_rank_3'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_lb_rank_3")],
                    [InlineKeyboardButton(f"৪-১০ম স্থান: {format_emoji_badge(p.get('lb_rank_other'))}", callback_data="noop"), InlineKeyboardButton("✏️", callback_data="ed_pe_lb_rank_other")],
                ]

            btns.append([InlineKeyboardButton("🔙 Back", callback_data="pem_back_main")])
            await cb.answer()
            if cb.message:
                await cb.message.edit_text(
                    "⭐ <b>প্রিমিয়াম ইমোজি কনফিগারেশন:</b>\nযেকোনো বাটন বা নোটিশের ইমোজি পরিবর্তন করতে পাশের ✏️ পেন্সিল আইকনে চাপ দিন:",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(btns)
                )
            return

        if data == "pem_back_main":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 চ্যানেল ও ভেরিফাই বাটন ইমোজি (✏️)", callback_data="pem_sub_channel")],
                [InlineKeyboardButton("🔑 টাস্কের ভেতরের ডাটা ইমোজি (✏️)", callback_data="pem_sub_taskdata")],
                [InlineKeyboardButton("🔘 মেইন মেনু বাটন ইমোজি (✏️)", callback_data="pem_sub_menu")],
                [InlineKeyboardButton("💼 টাস্ক মেনুর বাটনসমূহ (✏️)", callback_data="pem_sub_task")],
                [InlineKeyboardButton("🎬 আমি নতুন ও ভাষা বাটন (✏️)", callback_data="pem_sub_newlang")],
                [InlineKeyboardButton("🔔 সকল নোটিশ ও অ্যালার্ট ইমোজি (✏️)", callback_data="pem_sub_ntf")],
                [InlineKeyboardButton("👤 ব্যালেন্স/প্রোফাইল টেক্সট ইমোজি (✏️)", callback_data="pem_sub_bal")],
                [InlineKeyboardButton("👥 রেফার ও লিডারবোর্ড ইমোজি (✏️)", callback_data="pem_sub_reflb")],
                [InlineKeyboardButton("❌ Close", callback_data="cancel_admin_action")]
            ])
            await cb.answer()
            if cb.message:
                await cb.message.edit_text(
                    "⭐ <b>অল-ইন-ওয়ান প্রিমিয়াম ইমোজি কন্ট্রোল প্যানেল:</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            return

        if data.startswith("ed_pe_"):
            key = data.replace("ed_pe_", "")
            db["admin_state"]["action"] = "set_custom_emoji"
            db["admin_state"]["target_key"] = key
            save_data(db)

            await cb.answer()
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✏️ <b>প্রিমিয়াম ইমোজি সেট করুন:</b> <code>{key}</code>\nযেকোনো টেলিগ্রাম প্রিমিয়াম কাস্টম ইমোজি সেন্ড করুন!\n<i>(মুছে ফেলতে <code>0</code> পাঠান)</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=get_cancel_inline_markup()
            )
            return

        # কালার পরিবর্তন হ্যান্ডলিং
        if data.startswith("adm_col_") and "__" not in data:
            target = data.replace("adm_col_", "")
            palette = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🟢 Success (Green)", callback_data=f"adm_setcol_{target}__success"),
                    InlineKeyboardButton("🔵 Primary (Blue)", callback_data=f"adm_setcol_{target}__primary")
                ],
                [
                    InlineKeyboardButton("🔴 Danger (Red)", callback_data=f"adm_setcol_{target}__danger")
                ]
            ])
            await cb.answer()
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🎨 <b>{target.upper()}</b> বাটনের কালার নির্বাচন করুন:",
                parse_mode=ParseMode.HTML,
                reply_markup=palette
            )
            return

        if data.startswith("adm_setcol_"):
            raw = data.replace("adm_setcol_", "")
            parts = raw.split("__")
            target = parts[0]
            color = parts[1] if len(parts) > 1 else "primary"

            db.setdefault("settings", {}).setdefault("btn_colors", {})[target] = color
            save_data(db)
            await cb.answer("কালার আপডেট হয়েছে!")
            if cb.message:
                await cb.message.delete()
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✅ <b>{target}</b> বাটনের কালার <b>{color.upper()}</b> সেট হয়েছে!",
                parse_mode=ParseMode.HTML,
                reply_markup=get_admin_keyboard(db.get("settings", {}).get("bot_status", "ON"))
            )
            return

# ----------------------------------------------------
# এরর হ্যান্ডলার
# ----------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

# ----------------------------------------------------
# প্রধান এক্সেকিউশন লুপ
# ----------------------------------------------------
def main():
    # ফাইল ইনিশিয়ালাইজেশন
    if not os.path.exists(DATA_FILE):
        save_data(copy.deepcopy(DEFAULT_DATA))

    application = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()

    # মেসেজ ও ডকুমেন্ট হ্যান্ডলার
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_message))
    application.add_handler(CommandHandler("start", handle_message))
    application.add_handler(CommandHandler("admin", handle_message))
    application.add_handler(CommandHandler("cancel", handle_message))

    # কলব্যাক কুয়েরি হ্যান্ডলার
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # এরর হ্যান্ডলার
    application.add_error_handler(error_handler)

    logger.info("Bot starting in Long Polling mode...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
