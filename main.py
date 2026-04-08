import asyncio
import random
import os
from telethon import TelegramClient
from telethon.errors import FloodWaitError

# ดึงค่าจาก Environment Variables (จะไปตั้งค่าใน Railway ทีหลัง)
# แต่ถ้าจะรันในคอมเพื่อเอาไฟล์ session ให้ใส่ค่าตรงๆ ไว้ก่อนได้ครับ
api_id = int(os.getenv('TG_API_ID', '31983626'))
api_hash = os.getenv('TG_API_HASH', '38276889e1410851bb888d0f568e5f52')
phone_number = os.getenv('TG_PHONE', '+66815900783')
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

client = TelegramClient('session_fast_batch', api_id, api_hash)

async def send_one(group_id, text, media):
    try:
        await client.send_message(group_id, text, file=media)
        print(f"✅ {group_id}")
    except FloodWaitError as e:
        print(f"⏳ Flood {e.seconds}s → {group_id}")
        raise e
    except Exception as e:
        print(f"❌ {group_id}: {e}")

async def send_batch(batch, text, media):
    tasks = [send_one(gid, text, media) for gid in batch]
    await asyncio.gather(*tasks)

async def main():
    await client.start(phone=phone_number)
    print("🚀 FAST BATCH MODE 24/7 STARTED\n")

    while True:
        try:
            msg = await client.get_messages('me', ids=MESSAGE_ID)
            if not msg:
                print(f"❌ ไม่เจอข้อความ ID {MESSAGE_ID}")
            else:
                text = msg.text or ""
                media = msg.media
                
                batch_size = 10
                for i in range(0, len(target_groups), batch_size):
                    batch = target_groups[i:i+batch_size]
                    try:
                        await send_batch(batch, text, media)
                    except FloodWaitError as e:
                        print(f"🛑 ติด Flood รอ {e.seconds} วิ")
                        await asyncio.sleep(e.seconds)
                        break
                    await asyncio.sleep(random.uniform(1, 3))
                
                print("🏁 จบรอบ ส่งครบแล้ว")

        except Exception as e:
            print(f"⚠️ Error: {e}")
            await asyncio.sleep(60)

        # 🔥 สุ่มพัก 15-30 นาที
        wait = random.randint(900, 1800)
        print(f"😴 พัก {wait//60} นาที...")
        await asyncio.sleep(wait)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("ปิดโปรแกรมเรียบร้อย")
    except RuntimeError as e:
        # กรณีรันบนบาง Environment ที่ asyncio.run มีปัญหา
        if "no running event loop" in str(e) or "current event loop" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main())
        else:
            raise e