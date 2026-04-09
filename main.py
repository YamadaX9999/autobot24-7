import asyncio
import random
import os
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, AuthKeyDuplicatedError, PeerFloodError

# --- 1. CONFIGURATION ---
# ดึงจำนวนบัญชีจาก Environment Variable (ถ้าไม่มีให้เป็น 1)
acc_count = int(os.getenv('ACC_COUNT', '1'))

# โหลดรายชื่อกลุ่มเป้าหมายจากไฟล์ JSON
try:
    with open('target_groups.json', 'r') as f:
        target_groups = json.load(f)
except FileNotFoundError:
    print("❌ ไม่พบไฟล์ target_groups.json กรุณาสร้างไฟล์นี้และใส่ Group IDs")
    target_groups = []
except json.JSONDecodeError:
    print("❌ ไฟล์ target_groups.json มีรูปแบบไม่ถูกต้อง")
    target_groups = []

# --- 2. WORKER FUNCTION ---

async def work_session(acc_data, acc_index):
    """ฟังก์ชันจัดการงานของ 1 บัญชี"""
    client = TelegramClient(StringSession(acc_data['session']), acc_data['api_id'], acc_data['api_hash'])
    total_groups = len(target_groups)
    sent_count = 0
    
    try:
        await client.start()
        print(f"\n🚀 [ID {acc_index+1}] กำลังออนไลน์เพื่อเริ่มงาน...")

        # ดึงข้อความต้นฉบับจาก Saved Messages ของตัวเองตามเลข ID ที่กำหนด
        msg = await client.get_messages('me', ids=acc_data['msg_id'])
        if not msg:
            print(f"❌ [ID {acc_index+1}] ไม่พบข้อความ ID {acc_data['msg_id']} ในหน้า Saved Messages")
            return

        text = msg.text or ""
        media = msg.media

        # แบ่งกลุ่มเป็นก้อน ก้อนละ 10 กลุ่ม
        chunks = [target_groups[i:i + 10] for i in range(0, total_groups, 10)]

        for idx, chunk in enumerate(chunks):
            current_batch_size = len(chunk)
            print(f"📦 [ID {acc_index+1}] กำลังยิงชุดที่ {idx+1}/{len(chunks)} ({current_batch_size} กลุ่ม)...")
            
            # ส่งข้อความทีละกลุ่มใน Batch พร้อม Jitter เพื่อความเนียน (Anti-Spam)
            for gid in chunk:
                try:
                    # เพิ่ม Jitter ก่อนส่งแต่ละข้อความ (1-5 วินาที) เพื่อเลียนแบบพฤติกรรมมนุษย์
                    jitter = random.uniform(1, 5)
                    await asyncio.sleep(jitter)
                    
                    await client.send_message(gid, text, file=media)
                    sent_count += 1
                    print(f"✅ [ID {acc_index+1}] ส่งสำเร็จ: {gid}")
                
                except FloodWaitError as e:
                    print(f"⚠️ [ID {acc_index+1}] FloodWait: ต้องรอ {e.seconds} วินาที...")
                    await asyncio.sleep(e.seconds)
                    # พยายามส่งใหม่อีกครั้งหลังจากรอ
                    try:
                        await client.send_message(gid, text, file=media)
                        sent_count += 1
                    except Exception as e_retry:
                        print(f"❌ [ID {acc_index+1}] ส่งซ้ำไม่สำเร็จ: {e_retry}")
                
                except PeerFloodError:
                    print(f"⚠️ [ID {acc_index+1}] PeerFlood: บัญชีเริ่มถูกจำกัดการส่งข้อความ (Spam detected)")
                    # พักนานขึ้นเมื่อเจอ PeerFlood
                    await asyncio.sleep(random.randint(60, 120))
                
                except Exception as e:
                    print(f"❗ [ID {acc_index+1}] เกิดข้อผิดพลาดกับกลุ่ม {gid}: {e}")

            print(f"📊 Progress: [{sent_count}/{total_groups}] เรียบร้อย")

            # พักระหว่างก้อน (20-50 วินาที) - ปรับเป็น 30-60 วินาทีเพื่อความปลอดภัย
            if idx < len(chunks) - 1:
                pause = random.randint(30, 60)
                print(f"⏳ [ID {acc_index+1}] พักหายใจ {pause} วินาที...")
                await asyncio.sleep(pause)

        print(f"✅ [ID {acc_index+1}] จบภารกิจครบ {total_groups} กลุ่ม!")

    except AuthKeyDuplicatedError:
        print(f"❌ [ID {acc_index+1}] AuthKeyDuplicatedError: Session นี้อาจถูกใช้งานที่อื่น หรือหมดอายุแล้ว")
    except Exception as e:
        print(f"❗ [ID {acc_index+1}] พังกลางคัน: {e}")
    finally:
        # ตัดการเชื่อมต่อเพื่อให้ Account ขึ้น Offline ในระบบ Telegram
        if client.is_connected():
            await client.disconnect()

async def main():
    # โหลดบัญชีทั้งหมดจาก Environment Variables
    all_accounts = []
    for i in range(1, acc_count + 1):
        s = os.getenv(f'TG_SESSION_{i}')
        api_id = os.getenv(f'TG_API_ID_{i}')
        api_hash = os.getenv(f'TG_API_HASH_{i}')
        m = os.getenv(f'TG_MSG_ID_{i}')

        if s and api_id and api_hash and m:
            all_accounts.append({
                'session': s,
                'api_id': int(api_id),
                'api_hash': api_hash,
                'msg_id': int(m)
            })
        else:
            print(f"⚠️ ข้อมูลบัญชี TG_SESSION_{i}, TG_API_ID_{i}, TG_API_HASH_{i}, TG_MSG_ID_{i} ไม่ครบถ้วน จะข้ามบัญชีนี้")

    if not all_accounts:
        print("❌ ไม่พบข้อมูลบัญชีที่ถูกต้อง กรุณาตั้งค่า Variables ใน Railway ให้ถูกต้อง")
        return
    
    if not target_groups:
        print("❌ ไม่พบกลุ่มเป้าหมายใน target_groups.json ไม่สามารถดำเนินการต่อได้")
        return

    print(f"⚙️ ระบบพร้อมทำงาน: ตรวจพบ {len(all_accounts)} บัญชี และ {len(target_groups)} กลุ่มเป้าหมาย")

    while True:
        for idx, acc in enumerate(all_accounts):
            # 1. ให้บัญชีปัจจุบันทำงานจนจบลิสต์
            await work_session(acc, idx)
            
            # 2. Logic การพัก (Adaptive Rest)
            if len(all_accounts) == 1:
                # กรณี 1 บัญชี: สุ่มพักนาน 15-25 นาที (ถนอมไอดี)
                wait_next = random.randint(900, 1500)
                print(f"😴 [Single Mode] พักผ่อนสุ่ม {wait_next // 60} นาที เพื่อความเนียน...")
            else:
                # กรณีหลายบัญชี: พัก 10 นาทีตายตัว แล้วส่งต่อคนถัดไป
                wait_next = 600
                print(f"😴 [Multi Mode] พัก 10 นาที ก่อนส่งต่อให้ ID ถัดไป...")
            
            print("="*40)
            await asyncio.sleep(wait_next)

if __name__ == '__main__':
    asyncio.run(main())
