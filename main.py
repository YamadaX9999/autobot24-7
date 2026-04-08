import asyncio
import random
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, AuthKeyDuplicatedError

# --- 1. CONFIGURATION & VARIABLES ---
# ตั้งค่าผ่าน Environment Variables ใน Railway
acc_count = int(os.getenv('ACC_COUNT', '1'))
MESSAGE_ID = int(os.getenv('TG_MSG_ID', '514'))

# 🔥 รายชื่อกลุ่มทั้งหมด 82 กลุ่มของคุณ
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

accounts = []
clients = []

# ดึงข้อมูลบัญชีจาก Env
for i in range(1, acc_count + 1):
    session_str = os.getenv(f'TG_SESSION_{i}')
    api_id = int(os.getenv(f'TG_API_ID_{i}', 0))
    api_hash = os.getenv(f'TG_API_HASH_{i}')
    
    if session_str and api_id > 0:
        accounts.append({'session': session_str, 'api_id': api_id, 'api_hash': api_hash})

# --- 2. CORE FUNCTIONS ---

async def init_all_clients():
    """เชื่อมต่อทุกบัญชีด้วยระบบ String Session"""
    for acc in accounts:
        try:
            client = TelegramClient(StringSession(acc['session']), acc['api_id'], acc['api_hash'])
            await client.start()
            clients.append(client)
            print(f"✅ เชื่อมต่อบัญชีสำเร็จ")
        except Exception as e:
            print(f"❌ บัญชีมีปัญหา: {e}")

async def attack_one_group(group_id, text, media):
    """รุมยิงข้อความจากทุกไอดีเข้ากลุ่มเดียว"""
    tasks = []
    for client in clients:
        tasks.append(client.send_message(group_id, text, file=media))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            print(f"   ❌ ไอดี {i+1} พลาด: {res}")
        else:
            print(f"   🚀 ไอดี {i+1} ยิงเข้า {group_id} สำเร็จ")

async def main():
    if not clients:
        await init_all_clients()
    
    if not clients:
        print("❌ ไม่มีบัญชีที่พร้อมทำงาน โปรดตรวจสอบ Environment Variables")
        return

    while True:
        try:
            # ดึงข้อความต้นฉบับจาก Saved Messages ของบัญชีแรก
            msg = await clients[0].get_messages('me', ids=MESSAGE_ID)
            
            if not msg:
                print(f"❌ ไม่พบข้อความ ID {MESSAGE_ID} ใน Saved Messages")
            else:
                text = msg.text or ""
                media = msg.media
                
                # เริ่มวนลูปยิง 82 กลุ่ม
                count = 0
                for gid in target_groups:
                    count += 1
                    print(f"🎯 [{count}/82] กำลังยิงกลุ่ม: {gid}")
                    await attack_one_group(gid, text, media)

                    # 🔥 Logic: ส่งครบ 10 กลุ่ม พัก 10-30 วินาที
                    if count % 10 == 0:
                        pause = random.randint(10, 30)
                        print(f"⏳ ส่งครบ {count} กลุ่มแล้ว พักสุ่ม {pause} วินาที...")
                        await asyncio.sleep(pause)
                    else:
                        # Delay ปกติระหว่างกลุ่ม 5-10 วินาที
                        await asyncio.sleep(random.uniform(5, 10))
                
                print("🏁 จบรอบระดมยิง 82 กลุ่ม")

        except Exception as e:
            print(f"⚠️ ข้อผิดพลาดลูปหลัก: {e}")
            await asyncio.sleep(60)

        # พักรอบใหญ่ก่อนเริ่มใหม่ (สุ่ม 15-30 นาที)
        wait_time = random.randint(900, 1800)
        print(f"😴 พักรบ {wait_time // 60} นาที... แล้วจะเริ่มใหม่เอง\n")
        await asyncio.sleep(wait_time)

# --- 3. EXECUTION ---
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
