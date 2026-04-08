import asyncio
from telethon import TelegramClient

# --- ตั้งค่าบัญชีใหม่ตรงนี้ ---
api_id = 38577732  # ใส่ API ID ของคุณ
api_hash = '7d5569983109c5f0d8cac35b92a74a7a'  # ใส่ API Hash ของคุณ
session_name = 'acc2'  # ตั้งชื่อไฟล์ session ห้ามซ้ำกับที่มีอยู่

async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    
    print(f"--- เริ่มต้นการล็อกอินสำหรับ: {session_name} ---")
    
    # คำสั่ง start() จะจัดการถามเบอร์โทรและ OTP ให้เอง
    await client.start()
    
    print(f"✅ ล็อกอินสำเร็จ!")
    me = await client.get_me()
    print(f"ชื่อบัญชีที่ตรวจพบ: {me.first_name}")
    print(f"📂 ไฟล์ {session_name}.session ถูกสร้างขึ้นแล้วในโฟลเดอร์นี้")
    
    await client.disconnect()

if __name__ == '__main__':
    # สำหรับ Python 3.10+ แนะนำให้ใช้แบบนี้เพื่อหลีกเลี่ยง RuntimeError
    try:
        asyncio.run(main())
    except RuntimeError:
        # กรณีรันในสภาพแวดล้อมที่ asyncio.run มีปัญหา
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())