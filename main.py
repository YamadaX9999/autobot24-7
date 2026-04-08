import asyncio
import random
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, AuthKeyDuplicatedError, PeerFloodError

# --- 1. CONFIGURATION ---
acc_count = int(os.getenv('ACC_COUNT', '1'))
MESSAGE_ID = int(os.getenv('TG_MSG_ID', '14'))

target_groups = [
    -1002478474638, -1002517149993, -1001903626496, -1002250390373, -1001919304083,
    -1001664000137, -1001789640114, -1001897247628, -1001618732646, -1002628615859,
    -1002119039887, -1002192812008, -1002241747325, -1001887706833, -1001156381217,
    -1001809428120, -1002007797153, -1001880188179, -1002119105761, -1002145933860,
    -1002482612419, -1002455662763, -1001924681824, -1001814991683, -1002450557057,
    -1002227526162, -1001375263710, -1001233585278, -1001694925505, -1001791070496,
    -1001920096571, -1001798984360, -1002133005075, -1001897579363, -1001910260179,
    -1001390295134, -1001871072660, -1001346877982, -1001898420545, -1002011689664,
    -1002132939441, -1003264785551, -1001801341370, -1001988547616, -1002045863803,
    -1001820338887, -1002602092733, -1001740567353, -1001728358118, -1001873034924,
    -1001837418013, -1001835244921, -1001834234349, -1001545049810, -1001974269869,
    -1002074215371, -1001972645293, -1002107661734, -1001675689738, -1001971426670,
    -1002056229367, -1002026302865, -1002008617145, -1001881820903, -1002123285544,
    -1001618777702, -1002069776974, -1001824775512, -1001927095710, -1001499298416,
    -1001993065366, -1002209196647, -1001594062095, -1001660352109, -1001598156378,
    -1002094306502, -1002129554765, -1001967173585, -1002129105968, -1001641109030,
    -1002339895208
]

# --- 2. WORKER FUNCTION ---

async def work_session(acc_data, acc_index):
    """ฟังก์ชันการทำงานของ 1 บัญชีจนจบลิสต์"""
    client = TelegramClient(StringSession(acc_data['session']), acc_data['api_id'], acc_data['api_hash'])
    
    try:
        await client.start()
        print(f"\n🟢 [ID {acc_index+1}] เริ่มเข้าเวรทำงาน...")

        # ดึงข้อความต้นฉบับจาก Saved Messages ของตัวเอง
        msg = await client.get_messages('me', ids=MESSAGE_ID)
        if not msg:
            print(f"❌ [ID {acc_index+1}] ไม่พบข้อความต้นฉบับ ID {MESSAGE_ID}")
            return

        text = msg.text or ""
        media = msg.media

        # แบ่งกลุ่มเป็นชุดละ 10
        chunks = [target_groups[i:i + 10] for i in range(0, len(target_groups), 10)]

        for idx, chunk in enumerate(chunks):
            print(f"🔥 [ID {acc_index+1}] กำลังยิงชุดที่ {idx+1} ({len(chunk)} กลุ่ม)")
            
            # ยิง 10 กลุ่มนี้พร้อมกัน (Burst ในตัวมันเอง)
            tasks = [client.send_message(gid, text, file=media) for gid in chunk]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # เช็คผลลัพธ์คร่าวๆ
            for r in results:
                if isinstance(r, (FloodWaitError, PeerFloodError)):
                    print(f"⚠️ [ID {acc_index+1}] ตรวจพบข้อจำกัด: {r}")

            # พักระหว่างชุด 10 กลุ่ม (20-50 วินาที)
            if idx < len(chunks) - 1:
                pause = random.randint(20, 50)
                print(f"⏳ [ID {acc_index+1}] พักหายใจ {pause} วินาที...")
                await asyncio.sleep(pause)

        print(f"✅ [ID {acc_index+1}] ส่งครบ 82 กลุ่มแล้ว!")

    except Exception as e:
        print(f"❗ [ID {acc_index+1}] เกิดข้อผิดพลาด: {e}")
    finally:
        await client.disconnect()

async def main():
    # โหลดบัญชีทั้งหมดเก็บไว้
    all_accounts = []
    for i in range(1, acc_count + 1):
        s = os.getenv(f'TG_SESSION_{i}')
        if s:
            all_accounts.append({
                'session': s,
                'api_id': int(os.getenv(f'TG_API_ID_{i}')),
                'api_hash': os.getenv(f'TG_API_HASH_{i}')
            })

    if not all_accounts:
        print("❌ ไม่พบข้อมูลบัญชีใน Environment Variables")
        return

    while True:
        for idx, acc in enumerate(all_accounts):
            # 1. รันบัญชีปัจจุบันให้เสร็จทั้งลิสต์
            await work_session(acc, idx)
            
            # 2. เมื่อบัญชีนี้ทำเสร็จ พัก 10 นาที (600 วินาที) ก่อนส่งต่อให้บัญชีถัดไป
            wait_next = 600
            print(f"😴 [ID {idx+1}] พักเวร 10 นาที... เตรียมส่งต่อให้บัญชีถัดไป\n")
            await asyncio.sleep(wait_next)

if __name__ == '__main__':
    asyncio.run(main())
