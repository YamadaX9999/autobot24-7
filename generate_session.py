import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

async def main():
    print("--- Telethon StringSession Generator (Updated for Python 3.10+) ---")
    
    try:
        api_id = int(input("Enter your API ID: ").strip())
        api_hash = input("Enter your API Hash: ").strip()
    except ValueError:
        print("❌ Error: API ID ต้องเป็นตัวเลขเท่านั้น")
        return

    # สร้าง Client ด้วย StringSession
    client = TelegramClient(StringSession(), api_id, api_hash)

    async with client:
        print("\nกำลังเชื่อมต่อ... หากเป็นครั้งแรก คุณอาจต้องกรอกเบอร์โทรศัพท์และรหัส OTP")
        # ระบบจะขอเบอร์โทรศัพท์และ OTP อัตโนมัติในขั้นตอนนี้
        await client.start()
        
        # เมื่อเข้าสู่ระบบสำเร็จ จะได้ StringSession
        session_string = client.session.save()
        print("\n" + "="*50)
        print("✅ StringSession ของคุณคือ (คัดลอกไปใช้ใน Railway):")
        print("="*50)
        print(f"\n{session_string}\n")
        print("="*50)
        print("⚠️ โปรดเก็บ StringSession นี้เป็นความลับสูงสุด!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nยกเลิกการทำงาน")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
