import os
import json
import asyncio
import random
import time
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.errors import FloodWaitError, AuthKeyDuplicatedError, PeerFloodError, ChatWriteForbiddenError

# --- Configuration --- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_GROUPS_PATH = os.path.join(BASE_DIR, 'target_groups.json')

# --- Environment Variables Check --- #
def get_env_variable(var_name, is_required=True):
    value = os.getenv(var_name)
    if is_required and not value:
        print(f"❌ Error: Environment variable '{var_name}' is not set.")
    return value

# --- Load Target Groups ---
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
    pass

# --- Account Loading with Sorting --- #
def get_accounts_from_env():
    accounts_config = []
    env_vars = dict(os.environ)

    session_keys = [k for k in env_vars.keys() if k.startswith('TG_SESSION_')]
    session_keys.sort(key=lambda x: int(x.split('_')[-1]) if x.split('_')[-1].isdigit() else 0)

    for key in session_keys:
        suffix = key.split('_')[-1]
        api_id_var = f'TG_API_ID_{suffix}'
        api_hash_var = f'TG_API_HASH_{suffix}'

        api_id = get_env_variable(api_id_var, is_required=False)
        api_hash = get_env_variable(api_hash_var, is_required=False)
        session_str = get_env_variable(key, is_required=False)

        if api_id and api_hash and session_str:
            try:
                accounts_config.append({
                    'api_id': int(api_id),
                    'api_hash': api_hash,
                    'session_str': session_str,
                    'index': int(suffix) # Store the index for logging
                })
            except ValueError:
                print(f"❌ Warning: Invalid integer for API_ID for account {suffix}. Skipping.")
        else:
            print(f"⚠️ Warning: Incomplete environment variables for account {suffix}. Skipping this account.")
    return accounts_config

# --- Main Logic --- #
async def work_session(client_data, all_target_groups):
    client = client_data['client']
    api_id = client_data['api_id']
    client_index = client_data['index']
    
    print(f"➡️ บัญชีที่ {client_index} (API ID: {api_id}) กำลังจะส่งไปยัง {len(all_target_groups)} กลุ่ม")

    try:
        # ดึงข้อความล่าสุด 5 ข้อความจาก Saved Messages ('me')
        available_messages = await client.get_messages('me', limit=5)

        if not available_messages:
            print(f"❌ บัญชีที่ {client_index} (API ID: {api_id}): ไม่พบข้อความใน Saved Messages (ต้องมีอย่างน้อย 1 ข้อความ)")
            return

        # สุ่มลำดับกลุ่มเป้าหมายในแต่ละรอบ
        random.shuffle(all_target_groups)

        # ส่งข้อความไปยังแต่ละกลุ่ม
        sent_count = 0
        for i, group_id in enumerate(all_target_groups):
            try:
                # สุ่มเลือกข้อความจาก 5 ข้อความล่าสุด
                message_to_send = random.choice(available_messages)

                print(f"    [{client_index}] กำลังส่งไปยังกลุ่ม {group_id} (Progress: {i+1}/{len(all_target_groups)}) ...")
                # ส่ง Message Object โดยตรง เพื่อรักษา Formatting และ Media
                await client.send_message(group_id, message_to_send)
                print(f"    ✅ ส่งไปยังกลุ่ม {group_id} สำเร็จ")
                sent_count += 1
                
                # เพิ่ม Jitter เพื่อเลี่ยงการถูกแบน (10-20 วินาที)
                jitter_time = random.uniform(10, 20)
                await asyncio.sleep(jitter_time)
            except FloodWaitError as e:
                print(f"    ⚠️ [ID {client_index}] FloodWait: ต้องรอ {e.seconds} วินาที...")
                await asyncio.sleep(e.seconds)
                # พยายามส่งใหม่อีกครั้งหลังจากรอ
                try:
                    await client.send_message(group_id, message_to_send)
                    print(f"    ✅ ส่งไปยังกลุ่ม {group_id} สำเร็จ (หลัง FloodWait)")
                    sent_count += 1
                except Exception as e_retry:
                    print(f"    ❌ [ID {client_index}] ส่งซ้ำไม่สำเร็จหลัง FloodWait: {e_retry}")
            except PeerFloodError:
                print(f"    ⚠️ [ID {client_index}] PeerFlood: บัญชีเริ่มถูกจำกัดการส่งข้อความ (Spam detected) ข้ามกลุ่มนี้")
                # พักนานขึ้นเมื่อเจอ PeerFlood
                await asyncio.sleep(random.randint(60, 120))
            except ChatWriteForbiddenError:
                print(f"    ❌ [ID {client_index}] ChatWriteForbiddenError: ไม่สามารถส่งข้อความในกลุ่ม {group_id} ได้ (อาจเป็น Read-Only หรือถูกจำกัดสิทธิ์)")
                await asyncio.sleep(random.uniform(2, 5)) # หน่วงเวลาสั้นๆ ก่อนไปกลุ่มถัดไป
            except Exception as e:
                print(f"    ❌ เกิดข้อผิดพลาดในการส่งไปยังกลุ่ม {group_id}: {e}")
                await asyncio.sleep(random.uniform(2, 5)) # หน่วงเวลาสั้นๆ ก่อนไปกลุ่มถัดไป
        print(f"📊 บัญชีที่ {client_index} (API ID: {api_id}) ส่งสำเร็จ {sent_count}/{len(all_target_groups)} กลุ่ม")

    except Exception as e:
        print(f"❌ บัญชีที่ {client_index} (API ID: {api_id}): เกิดข้อผิดพลาดหลักในการดำเนินการ: {e}")
    finally:
        pass

async def main():
    print("✨ Autobot 24/7 กำลังออนไลน์เพื่อเริ่มงาน...")

    accounts_config = get_accounts_from_env()
    if not accounts_config:
        print("❌ ไม่พบการตั้งค่าบัญชี Telegram ใน Environment Variables. โปรดตรวจสอบ TG_API_ID_X, TG_API_HASH_X, TG_SESSION_X")
        return

    clients_data = []
    for acc_conf in accounts_config:
        api_id = acc_conf['api_id']
        api_hash = acc_conf['api_hash']
        session_str = acc_conf['session_str']
        client_index = acc_conf['index']

        try:
            client = TelegramClient(StringSession(session_str), api_id, api_hash)
            await client.connect()
            if not await client.is_user_authorized():
                print(f"⚠️ บัญชีที่ {client_index} (API ID: {api_id}) ไม่ได้เข้าสู่ระบบ หรือ Session หมดอายุ")
                await client.disconnect()
                continue
            clients_data.append({'client': client, 'api_id': api_id, 'index': client_index})
            print(f"✅ บัญชีที่ {client_index} (API ID: {api_id}) ออนไลน์แล้ว")
        except AuthKeyDuplicatedError as e:
            print(f"❌ บัญชีที่ {client_index} (API ID: {api_id}): เกิดข้อผิดพลาด AuthKeyDuplicatedError: {e}. Session นี้ถูกใช้งานซ้ำซ้อน.")
            if 'client' in locals() and client.is_connected():
                await client.disconnect()
            continue
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อบัญชีที่ {client_index} (API ID: {api_id}): {e}")
            if 'client' in locals() and client.is_connected():
                await client.disconnect()
            continue

    if not clients_data:
        print("❌ ไม่มีบัญชีใดออนไลน์ ไม่สามารถดำเนินการต่อได้")
        return

    if not target_groups:
        print("❌ ไม่พบกลุ่มเป้าหมายใน target_groups.json ไม่สามารถดำเนินการต่อได้")
        return

    print(f"🚀 เริ่มต้นการยิงข้อความไปยัง {len(target_groups)} กลุ่มเป้าหมายด้วย {len(clients_data)} บัญชี")
    
    # --- Infinite Loop for 24/7 Operation --- #
    while True:
        print("\n" + "="*60)
        print("🔄 เริ่มต้นรอบการทำงานใหม่...")
        print("="*60)

        for client_data in clients_data:
            # ตรวจสอบสถานะการเชื่อมต่อก่อนเริ่มงาน
            if not client_data['client'].is_connected():
                print(f"⚠️ บัญชีที่ {client_data['index']} (API ID: {client_data['api_id']}) หลุดการเชื่อมต่อ กำลังพยายามเชื่อมต่อใหม่...")
                try:
                    await client_data['client'].connect()
                    if not await client_data['client'].is_user_authorized():
                        print(f"❌ บัญชีที่ {client_data['index']} (API ID: {client_data['api_id']}) ไม่สามารถเชื่อมต่อใหม่ได้ (Session หมดอายุ?)")
                        continue # ข้ามบัญชีนี้ไป
                    print(f"✅ บัญชีที่ {client_data['index']} (API ID: {client_data['api_id']}) เชื่อมต่อใหม่สำเร็จ")
                except AuthKeyDuplicatedError as e:
                    print(f"❌ บัญชีที่ {client_data['index']} (API ID: {client_data['api_id']}): เกิดข้อผิดพลาด AuthKeyDuplicatedError ในการเชื่อมต่อใหม่: {e}. Session นี้ถูกใช้งานซ้ำซ้อน.")
                    continue
                except Exception as e:
                    print(f"❌ บัญชีที่ {client_data['index']} (API ID: {client_data['api_id']}) เกิดข้อผิดพลาดในการเชื่อมต่อใหม่: {e}")
                    continue

            # ให้แต่ละบัญชีส่งข้อความไปยังทุกกลุ่ม
            await work_session(client_data, list(target_groups)) # ใช้ list() เพื่อสร้างสำเนาให้ shuffle ได้
            
            # พักระหว่างบัญชี (1-2 นาที) เพื่อความปลอดภัย
            if len(clients_data) > 1 and client_data != clients_data[-1]: # ถ้ามีหลายบัญชีและไม่ใช่บัญชีสุดท้าย
                inter_account_rest = random.uniform(60, 120) # 1-2 นาที
                print(f"😴 พักระหว่างบัญชี... จะเริ่มบัญชีถัดไปในอีก {inter_account_rest // 60:.0f} นาที {inter_account_rest % 60:.0f} วินาที")
                await asyncio.sleep(inter_account_rest)

        print("\n" + "="*60)
        print("🎉 จบรอบการทำงานปัจจุบัน")
        
        # พักใหญ่หลังจบรอบทั้งหมด (5-10 นาที)
        min_wait_minutes = 5
        max_wait_minutes = 10
        wait_time_seconds = random.randint(min_wait_minutes * 60, max_wait_minutes * 60)
        
        print(f"😴 กำลังพักผ่อน... จะเริ่มรอบถัดไปในอีก {wait_time_seconds // 60} นาที {wait_time_seconds % 60} วินาที")
        print("="*60)
        await asyncio.sleep(wait_time_seconds)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 หยุดการทำงานโดยผู้ใช้")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
