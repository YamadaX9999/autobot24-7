
import asyncio
import os
import json
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

async def main():
    print("--- Telethon Group ID Extractor (สำหรับ Autobot 24/7) ---")
    print("💡 สคริปต์นี้จะช่วยดึง Group ID ทั้งหมดที่คุณเป็นสมาชิกและบันทึกเป็นไฟล์ target_groups.json")
    print("⚠️ โปรดเตรียม API ID, API Hash และเบอร์โทรศัพท์ของคุณให้พร้อม")

    # ดึงค่าจาก Environment Variables หรือให้ผู้ใช้ป้อน
    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")
    phone_number = os.getenv("TG_PHONE_NUMBER")
    session_string = os.getenv("TG_SESSION") # สามารถใช้ StringSession ที่มีอยู่แล้วได้

    if not api_id:
        api_id = input("Enter your API ID (จาก my.telegram.org): ")
    if not api_hash:
        api_hash = input("Enter your API Hash (จาก my.telegram.org): ")
    if not phone_number:
        phone_number = input("Enter your Phone Number (รูปแบบ +66xxxxxxxx): ")

    try:
        api_id = int(api_id)
    except ValueError:
        print("❌ API ID ต้องเป็นตัวเลขเท่านั้น")
        return

    client = None
    try:
        if session_string:
            print("ℹ️ กำลังใช้ StringSession ที่มีอยู่...")
            client = TelegramClient(StringSession(session_string), api_id, api_hash)
        else:
            print("ℹ️ กำลังสร้าง Session ใหม่...")
            client = TelegramClient("group_extractor_session", api_id, api_hash)
        
        await client.connect()

        if not await client.is_user_authorized():
            print("⚠️ Session หมดอายุ หรือยังไม่ได้เข้าสู่ระบบ")
            print("➡️ กำลังเข้าสู่ระบบ...")
            await client.start(phone=phone_number)
            print("✅ เข้าสู่ระบบสำเร็จ!")
            # หากสร้าง session ใหม่ ให้บันทึก StringSession ไว้
            if not session_string:
                new_session_string = client.session.save()
                print("\n" + "="*50)
                print("✨ StringSession ของคุณ (เก็บไว้ใช้ใน TG_SESSION บน Railway):\n")
                print(f"{new_session_string}\n")
                print("="*50)
                print("⚠️ โปรดเก็บ StringSession นี้เป็นความลับสูงสุด!")

        print("🔍 กำลังดึงรายชื่อกลุ่มที่คุณเป็นสมาชิก...")
        group_ids = []
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                group_ids.append(dialog.id)
                print(f"  📌 พบกลุ่ม: {dialog.name} | ID: {dialog.id}")

        if not group_ids:
            print("❌ ไม่พบกลุ่มที่คุณเป็นสมาชิกเลย")
            return

        # บันทึก Group IDs ลงในไฟล์ target_groups.json
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        TARGET_GROUPS_PATH = os.path.join(BASE_DIR, 'target_groups.json')

        with open(TARGET_GROUPS_PATH, 'w', encoding='utf-8') as f:
            json.dump(group_ids, f, indent=4)
        
        print(f"\n✅ บันทึก {len(group_ids)} กลุ่มลงใน '{TARGET_GROUPS_PATH}' เรียบร้อยแล้ว!")
        print("💡 ไฟล์นี้พร้อมนำไปใช้กับโปรเจกต์ Autobot 24/7 ของคุณ")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        if client and client.is_connected():
            await client.disconnect()
            print("🔌 ตัดการเชื่อมต่อจาก Telegram แล้ว")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 หยุดการทำงานโดยผู้ใช้")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
