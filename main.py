import asyncio
import random
import os
from telethon import TelegramClient
from telethon.errors import FloodWaitError

# --- CONFIGURATION ---
acc_count = int(os.getenv('ACC_COUNT', '1'))
MESSAGE_ID = int(os.getenv('TG_MSG_ID', '514'))

# 🔥 รายชื่อกลุ่ม (82 กลุ่ม)
target_groups = [
    -1002478474638,-1002517149993,-1001903626496,-1002250390373,-1001919304083,
    -1001664000137,-1001789640114,-1001897247628,-1001618732646,-1002628615859,
    -1002119039887,-1002192812008,-1002241747325,-1001887706833,-1001156381217,
    -1001809428120,-1002007797153,-1001880188179,-1002119105761,-1002145933860,
    -1002482612419,-1002455662763,-1001924681824,-1001814991683,-1002450557057,
    -1002227526162,-1001375263710,-1001233585278,-1001694925505,-1001791070496,
    -1001920096571,-1001798984360,-1002133005075,-1001897579363,-1001910260179,
    -1001390295134,-1001871072660,-1001346877982,-1001898420545,-1002011689664,
    -1002132939441,-1003264785551,-1001801341370,-1001988547616,-1002045863803,
    -1001820338887,-1002602092733,-1001740567353,-1001728358118,-1001873034924,
    -1001837418013,-1001835244921,-1001834234349,-1001545049810,-1001974269869,
    -1002074215371,-1001972645293,-1002107661734,-1001675689738,-1001971426670,
    -1002056229367,-1002026302865,-1002008617145,-1001881820903,-1002123285544,
    -1001618777702,-1002069776974,-1001824775512,-1001927095710,-1001499298416,
    -1001993065366,-1002209196647,-1001594062095,-1001660352109,-1001598156378,
    -1002094306502,-1002129554765,-1001967173585,-1002129105968,-1001641109030,
    -1002339895208
]

accounts = []
clients = []

for i in range(1, acc_count + 1):
    acc_data = {
        'session': os.getenv(f'TG_SESSION_{i}'),
        'api_id': int(os.getenv(f'TG_API_ID_{i}', 0)),
        'api_hash': os.getenv(f'TG_API_HASH_{i}'),
    }
    if acc_data['session'] and acc_data['api_id'] > 0:
        accounts.append(acc_data)

async def init_all_clients():
    for acc in accounts:
        client = TelegramClient(acc['session'], acc['api_id'], acc['api_hash'])
        await client.start()
        clients.append(client)
    print(f"✅ ระบบพร้อมทำงาน: {len(clients)} ไอดี")

async def send_per_account_batch(client_index, text, media):
    """ส่งทีละ 10 กลุ่มแล้วพักสั้นๆ จนครบกลุ่มตัวเอง"""
    current_client = clients[client_index]
    batch_size = 10
    
    print(f"📢 ID ที่ {client_index + 1} เริ่มส่งแบบ Batch...")
    
    # แบ่งกลุ่มเป็นชุดละ 10
    for i in range(0, len(target_groups), batch_size):
        batch = target_groups[i:i + batch_size]
        
        # ส่งใน Batch นั้นๆ (รัวได้ใน 10 กลุ่มนี้)
        for gid in batch:
            try:
                await current_client.send_message(gid, text, file=media)
                print(f"✅ ID {client_index + 1} -> {gid}")
            except FloodWaitError as e:
                print(f"⏳ ID {client_index + 1} ติด Flood รอ {e.seconds} วิ")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"❌ พลาดกลุ่ม {gid}: {e}")
            
            # ดีเลย์จิ๋วๆ 0.2 วิกันระบบค้าง
            await asyncio.sleep(0.2)
        
        # 🔥 พัก 15-30 วินาที หลังจากส่งครบ 10 กลุ่ม
        if i + batch_size < len(target_groups):
            wait_batch = random.randint(15, 30)
            print(f"☕ ส่งครบชุด 10 กลุ่มแล้ว พัก {wait_batch} วินาที...")
            await asyncio.sleep(wait_batch)

async def main():
    await init_all_clients()
    
    while True:
        for i in range(len(clients)):
            try:
                # ดึงต้นฉบับ
                msg = await clients[0].get_messages('me', ids=MESSAGE_ID)
                if not msg:
                    print("❌ ไม่พบข้อความต้นฉบับ")
                    break
                
                text = msg.text or ""
                media = msg.media

                # ส่งทีละ Batch จนครบ 82 กลุ่ม
                await send_per_account_batch(i, text, media)
                print(f"🏁 ID {i + 1} ทำหน้าที่เสร็จสิ้น")

                # 😴 รอ 10 นาที เพื่อให้ ID ถัดไปเริ่ม
                if i < len(clients) - 1:
                    print(f"🕒 พักเครื่อง 10 นาที ก่อน ID {i + 2} จะลุยต่อ...")
                    await asyncio.sleep(200)

            except Exception as e:
                print(f"⚠️ ระบบขัดข้อง: {e}")
                await asyncio.sleep(60)

        print("🔄 จบรอบใหญ่ (ทุก ID ส่งครบ) เริ่มต้นรอบใหม่ทันที...")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
