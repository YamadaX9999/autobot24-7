import os
import json
import asyncio
import random
import time
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetHistoryRequest # ยังคง import ไว้เผื่อใช้ในอนาคต แต่ไม่ได้ใช้ในส่วนนี้แล้ว
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.errors import FloodWaitError, AuthKeyDuplicatedError, PeerFloodError

# --- Configuration --- #
# ค้นหาตำแหน่งโฟลเดอร์ที่ไฟล์ main.py วางอยู่
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_GROUPS_PATH = os.path.join(BASE_DIR, 'target_groups.json')

# --- Environment Variables Check --- #
def get_env_variable(var_name, is_required=True):
    value = os.getenv(var_name)
    if is_required and not value:
        print(f"❌ Error: Environment variable '{var_name}' is not set.")
        exit(1)
    return value

ACC_COUNT = int(get_env_variable('ACC_COUNT', is_required=True))

# --- Load Target Groups --- #
def load_target_groups():
    try:
        if not os.path.exists(TARGET_GROUPS_PATH):
            print(f"❌ ไม่พบไฟล์: {TARGET_GROUPS_PATH} กรุณาสร้างไฟล์นี้และใส่ Group IDs")
            return []
            
        with open(TARGET_GROUPS_PATH, 'r', encoding='utf-8') as f:
            groups = json.load(f)
            if not groups:
                print("❌ ไม่พบกลุ่มเป้าหมายใน target_groups.json ไม่สามารถดำเนินการต่อได้")
                return []
            # ตรวจสอบว่าทุก group ID เป็น int
            return [int(g) for g in groups]
    except json.JSONDecodeError as e:
        print(f"❌ Error: รูปแบบไฟล์ target_groups.json ไม่ถูกต้อง: {e}")
        return []
    except ValueError as e:
        print(f"❌ Error: Group ID ใน target_groups.json ต้องเป็นตัวเลขเท่านั้น: {e}")
        return []
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการโหลดไฟล์ target_groups.json: {e}")
        return []

target_groups = load_target_groups()
if not target_groups:
    exit(1)

# --- Main Logic --- #
async def main():
    print("✨ Autobot 24/7 กำลังออนไลน์เพื่อเริ่มงาน...")

    clients = []
    for i in range(1, ACC_COUNT + 1):
        session_str = get_env_variable(f'TG_SESSION_{i}')
        api_id = int(get_env_variable(f'TG_API_ID_{i}'))
        api_hash = get_env_variable(f'TG_API_HASH_{i}')
        msg_id = int(get_env_variable(f'TG_MSG_ID_{i}'))

        try:
            client = TelegramClient(StringSession(session_str), api_id, api_hash)
            await client.connect()
            if not await client.is_user_authorized():
                print(f"⚠️ บัญชีที่ {i} (API ID: {api_id}) ไม่ได้เข้าสู่ระบบ หรือ Session หมดอายุ")
                await client.disconnect()
                continue
            clients.append({'client': client, 'msg_id': msg_id, 'api_id': api_id})
            print(f"✅ บัญชีที่ {i} (API ID: {api_id}) ออนไลน์แล้ว")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อบัญชีที่ {i} (API ID: {api_id}): {e}")
            if client and client.is_connected():
                await client.disconnect()
            continue

    if not clients:
        print("❌ ไม่มีบัญชีใดออนไลน์ ไม่สามารถดำเนินการต่อได้")
        return

    print(f"🚀 เริ่มต้นการยิงข้อความไปยัง {len(target_groups)} กลุ่มเป้าหมายด้วย {len(clients)} บัญชี")

    # แบ่งกลุ่มเป้าหมายให้แต่ละบัญชี
    groups_per_client = [[] for _ in range(len(clients))]
    for i, group_id in enumerate(target_groups):
        groups_per_client[i % len(clients)].append(group_id)

    # เริ่มต้นการยิงข้อความ
    for client_idx, client_data in enumerate(clients):
        client = client_data['client']
        msg_id = client_data['msg_id']
        api_id = client_data['api_id']
        my_groups = groups_per_client[client_idx]

        if not my_groups:
            print(f"ℹ️ บัญชีที่ {client_idx+1} (API ID: {api_id}) ไม่มีกลุ่มเป้าหมายที่จะส่ง")
            continue

        print(f"➡️ บัญชีที่ {client_idx+1} (API ID: {api_id}) กำลังจะส่งไปยัง {len(my_groups)} กลุ่ม")

        try:
            # ดึงข้อความจาก Saved Messages ('me') โดยระบุ ID โดยตรง
            # วิธีนี้เสถียรและไม่ต้องใช้ GetHistoryRequest ที่ซับซ้อน
            messages = await client.get_messages('me', ids=msg_id)
            message_to_send = messages # get_messages เมื่อระบุ ids จะคืนค่าเป็น message object โดยตรง

            if not message_to_send:
                print(f"❌ บัญชีที่ {client_idx+1} (API ID: {api_id}): ไม่พบข้อความ ID {msg_id} ใน Saved Messages")
                await client.disconnect()
                continue

            print(f"✅ พบข้อความต้นฉบับแล้ว: {message_to_send.message[:30]}...")

            # เตรียม Media (ถ้ามี)
            media_to_send = message_to_send.media

            # ส่งข้อความไปยังแต่ละกลุ่ม
            for i, group_id in enumerate(my_groups):
                try:
                    print(f"    [{client_idx+1}/{len(clients)}] กำลังส่งไปยังกลุ่ม {group_id} (Progress: {i+1}/{len(my_groups)}) ...")
                    await client.send_message(group_id, message_to_send.message, file=media_to_send)
                    print(f"    ✅ ส่งไปยังกลุ่ม {group_id} สำเร็จ")
                    # เพิ่ม Jitter เพื่อเลี่ยงการถูกแบน
                    jitter_time = random.uniform(5, 15) # สุ่มหน่วงเวลา 5-15 วินาที
                    await asyncio.sleep(jitter_time)
                except FloodWaitError as e:
                    print(f"    ⚠️ [ID {client_idx+1}] FloodWait: ต้องรอ {e.seconds} วินาที...")
                    await asyncio.sleep(e.seconds)
                    # พยายามส่งใหม่อีกครั้งหลังจากรอ
                    try:
                        await client.send_message(group_id, message_to_send.message, file=media_to_send)
                        print(f"    ✅ ส่งไปยังกลุ่ม {group_id} สำเร็จ (หลัง FloodWait)")
                    except Exception as e_retry:
                        print(f"    ❌ [ID {client_idx+1}] ส่งซ้ำไม่สำเร็จหลัง FloodWait: {e_retry}")
                except PeerFloodError:
                    print(f"    ⚠️ [ID {client_idx+1}] PeerFlood: บัญชีเริ่มถูกจำกัดการส่งข้อความ (Spam detected) ข้ามกลุ่มนี้")
                    # พักนานขึ้นเมื่อเจอ PeerFlood
                    await asyncio.sleep(random.randint(60, 120))
                except Exception as e:
                    print(f"    ❌ เกิดข้อผิดพลาดในการส่งไปยังกลุ่ม {group_id}: {e}")
                    # หากส่งไม่ได้ ให้ข้ามไปกลุ่มถัดไป
                    await asyncio.sleep(random.uniform(2, 5)) # หน่วงเวลาสั้นๆ ก่อนไปกลุ่มถัดไป

        except Exception as e:
            print(f"❌ บัญชีที่ {client_idx+1} (API ID: {api_id}): เกิดข้อผิดพลาดหลักในการดำเนินการ: {e}")
        finally:
            if client.is_connected():
                await client.disconnect()
                print(f"🔌 บัญชีที่ {client_idx+1} (API ID: {api_id}) ตัดการเชื่อมต่อแล้ว")

    print("🎉 การดำเนินการทั้งหมดเสร็จสิ้น")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 หยุดการทำงานโดยผู้ใช้")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
