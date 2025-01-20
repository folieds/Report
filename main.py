import asyncio
import random
import aiohttp
from aiohttp import web
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipant

# Bot Configuration
API_ID = '29748628'
API_HASH = '45f3828a3a3d2f6e41696e5c39531110'
BOT_TOKEN = '7415801305:AAECmOHSfsqCjYvPumppruI-YhCAfBXdyR8'
CHANNEL_USERNAME = 'CodxByte'  # Replace with your channel username
ADMIN_USERNAME = 'faony'  # Replace with your admin's username (without @)
ADMIN_ID = 6076683960  # Replace with your admin's Telegram ID

# Initialize bot
bot = TelegramClient('new_report_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Global Variables
user_reporting = {}
notified_users = set()
active_users = set()
broadcasting = False
waiting_for_broadcast_message = None
broadcast_message_content = None

# Helper Function: Check Channel Membership
async def is_user_in_channel(user_id):
    try:
        participant = await bot(GetParticipantRequest(CHANNEL_USERNAME, user_id))
        return isinstance(participant.participant, ChannelParticipant)
    except:
        return False

# Start Command: Force Join + Notify Admin
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    user = await bot.get_entity(user_id)
    username = user.username or "No Username"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    permanent_link = f"tg://user?id={user_id}"

    # Add user to active users list
    active_users.add(user_id)

    # Check if user is in the channel
    if not await is_user_in_channel(user_id):
        await event.reply(
            f"👋🏻** Hey {full_name}! You must join our channel to use this bot.**",
            buttons=[
                [Button.url("ᴄᴏᴅxʙʏᴛᴇ", f"https://t.me/{CHANNEL_USERNAME}"),
                 Button.url("ᴏᴜᴛʟᴀᴡ ʙᴏᴛs", "https://t.me/outlawbots")],
                [Button.url("ɪʟʟᴇɢᴀʟ ᴄᴏʟʟᴇɢᴇ", "https://t.me/illegalCollege")]
            ]
        )
        return

    # Notify Admin Once
    if user_id not in notified_users:
        notified_users.add(user_id)
        total_users = len(active_users)
        await bot.send_message(
            ADMIN_USERNAME,
            f"🔔 **New User Alert**\n\n"
            f"👤 **Name:** [{full_name}]({permanent_link})\n"
            f"📛 **Username:** @{username if username != 'No Username' else 'No Username'}\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"🔗 **Profile Link:** [Click Here]({permanent_link})\n"
            f"👥 **Total Users:** {total_users}",
            link_preview=False
        )

    # Inform User
    user_reporting[user_id] = {'status': 'idle'}
    await event.reply(
        f"<b>👋🏻 Welcome, <a href='{permanent_link}'>{full_name}</a>! 🎉</b>\n\n"
        "<i>We're excited to have you here! 🚀 With this bot, you can report any Instagram account effortlessly.</i>\n\n"
        "<blockquote>📌 <b>Steps to Get Started:</b>\n"
        "1️⃣ Join our channel to unlock all features.\n"
        "2️⃣ Use the /report command to start reporting your target.</blockquote>\n\n"
        "💡 <i>Need help? Reach out to our support team anytime!</i>",
        buttons=[
            [
                Button.url("📢 Update", f"https://t.me/outlawbots"),
                Button.url("🛠 Support", "https://t.me/offchats")
            ],
            [
                Button.url("👤 Admin", "https://t.me/RehanCodz"),
                Button.url("👨‍💻 Developer", "https://t.me/faony")
            ]
        ],
        parse_mode="html"
    )

# Report Command
@bot.on(events.NewMessage(pattern='/report'))
async def report_command(event):
    user_id = event.sender_id
    if not await is_user_in_channel(user_id):
        await event.reply(
            "👋🏻**Hey! You must join our channel to use this bot.**",
            buttons=[
                [Button.url("ᴄᴏᴅxʙʏᴛᴇ", f"https://t.me/{CHANNEL_USERNAME}"),
                 Button.url("ᴏᴜᴛʟᴀᴡ ʙᴏᴛs", "https://t.me/outlawbots")],
                [Button.url("ɪʟʟᴇɢᴀʟ ᴄᴏʟʟᴇɢᴇ", "https://t.me/illegalCollege")]
            ]
        )
        return

    if user_reporting[user_id]['status'] != 'idle':
        await event.reply("⚠️ You already have a report in process. Finish that first.")
        return

    user_reporting[user_id]['status'] = 'awaiting_username'
    await event.reply(
        "⚠️ Note: Reporting an Instagram account can take a long time. Please be patient. Do not report accounts that are patched.",
        link_preview=False
    )

# Handle Username Submission
@bot.on(events.NewMessage)
async def handle_username(event):
    user_id = event.sender_id
    if user_reporting.get(user_id, {}).get('status') == 'awaiting_username':
        username = event.text.strip()
        if not username.startswith('@'):
            await event.reply("👤 Please send the username of your target (with @).")
            return

        instagram_link = f"[{username}](http://instagram.com/{username[1:]})"
        user_reporting[user_id] = {'status': 'reporting', 'username': username, 'count': 0, 'link': instagram_link}

        await event.reply(
            f"✅ Username `{username}` accepted.\nInstagram Link: {instagram_link}. Shall we start reporting?",
            buttons=[
                [Button.inline("Start Reporting", b'start_reporting')],
                [Button.inline("Cancel", b'cancel_reporting')]
            ]
        )

# Handle Inline Buttons
@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    if event.data == b'start_reporting':
        if user_reporting[user_id]['status'] != 'reporting':
            await event.answer("❌ Invalid action.", alert=True)
            return
        await start_reporting(event)
    elif event.data == b'cancel_reporting':
        user_reporting[user_id]['status'] = 'idle'
        await event.edit("❌ Reporting process has been cancelled.")
    elif event.data == b'stop_reporting':
        user_reporting[user_id]['status'] = 'idle'
        username = user_reporting[user_id].get('username', 'Unknown')
        await event.edit(f"🛑 Reporting for {username} has been stopped.")

# Reporting Function
async def start_reporting(event):
    import random  # Ensure random module is imported

    user_id = event.sender_id
    username = user_reporting[user_id]['username']

    message = await event.edit(
        f"🚀 Reporting Started for {username}...",
        buttons=[[Button.inline("Stop Reporting", b'stop_reporting')]]
    )

    total_failed = 0  # Track total failed reports
    total_successful = 0  # Track total successful reports

    for i in range(1, 10001):
        if user_reporting[user_id]['status'] != 'reporting':
            await message.edit(f"‼️ Reporting {username} stopped.\n\n📊 Total Reports:\n"
                               f"✅ Successful: {total_successful}\n❌ Failed: {total_failed}")
            return

        # Randomly decide if a report fails (e.g., 5-10% chance)
        is_failed = random.randint(1, 10) <= 3  # Failure rate of 20% (2 out of 10)

        if is_failed:
            total_failed += 1
        else:
            total_successful += 1

        # Update message every 10 reports
        if i % 10 == 0:
            try:
                await message.edit(
                    f"📊 **Reporting Progress for {username}:**\n\n"
                    f"✅ Successful Reports: {total_successful}\n"
                    f"❌ Failed Reports: {total_failed}\n\n"
                    f"🔄 Current Attempt: {i}\n"
                    f"🚀 Reporting is in progress...",
                    buttons=[[Button.inline("🛑 Stop Reporting", b'stop_reporting')]]
                )
            except Exception as e:
                print(f"Error updating message: {e}")

        await asyncio.sleep(0.5)  # Adjust this as per bot’s speed for a better simulation

    # Final report summary
    await message.edit(
        f"🎉 Reporting for @{username} is completed!\n\n"
        f"📊 **Total Reports:**\n"
        f"✅ Successful: {total_successful}\n"
        f"❌ Failed: {total_failed}\n\n"
        "Thank you for using the reporting service!"
    )


# Broadcast Command
@bot.on(events.NewMessage(pattern='/broadcast'))
async def broadcast(event):
    global broadcasting, waiting_for_broadcast_message, broadcast_message_content

    user_id = event.sender_id

    # Fetch the sender's entity
    sender = await bot.get_entity(user_id)
    sender_username = sender.username

    # Check if the sender is admin by comparing with ADMIN_USERNAME or ADMIN_ID
    if sender_username != ADMIN_USERNAME and user_id != ADMIN_ID:
        await event.reply("❌ Only Bot Admins Can Use This Command Niggah.")
        return

    # Set flag for broadcasting
    broadcasting = True
    waiting_for_broadcast_message = user_id  # Track that admin is being asked to send a message

    # Notify admin that the bot is ready to receive the message
    await event.reply("📝 Now Send The Message You Want to Broadcast to All Bot Users.")

# Handle Admin Message for Broadcast
@bot.on(events.NewMessage)
async def capture_admin_message(admin_event):
    global broadcasting, waiting_for_broadcast_message, broadcast_message_content

    user_id = admin_event.sender_id

    # Fetch the sender's entity
    sender = await bot.get_entity(user_id)
    sender_username = sender.username

    # Check if the sender is the admin and broadcasting flag is set
    if broadcasting and waiting_for_broadcast_message == user_id and (
        sender_username == ADMIN_USERNAME or user_id == ADMIN_ID
    ):
        broadcast_message = admin_event.text.strip()

        # Validate the broadcast message
        if not broadcast_message or broadcast_message == '/broadcast':
            await admin_event.reply("❌ Broadcast Message Can't Be Empty, Try Again.")
            return

        # Ask the admin for confirmation
        broadcast_message_content = broadcast_message
        broadcasting = False  # Reset the broadcasting flag to avoid conflicts
        waiting_for_broadcast_message = None  # Reset waiting admin ID
        await admin_event.reply(
            f"💬 Do You Want To Broadcast This Message:\n\n{broadcast_message}\n\nConfirm karein:",
            buttons=[
                [Button.inline("Yeahh", b'confirm_yes')],
                [Button.inline("Nopes", b'confirm_no')]
            ]
        )

# Handle Broadcast Confirmation (Yes/No)
@bot.on(events.CallbackQuery)
async def handle_broadcast_confirmation(event):
    global broadcast_message_content

    user_id = event.sender_id

    # Fetch the sender's entity
    sender = await bot.get_entity(user_id)
    sender_username = sender.username

    # Ensure only admin can confirm the broadcast
    if sender_username != ADMIN_USERNAME and user_id != ADMIN_ID:
        await event.answer("❌ Only Bot Admin Can Give Confirmation Bruhh.", alert=True)
        return

    if event.data == b'confirm_yes':
        if not broadcast_message_content:
            await event.answer("❌ Invalid Broadcast Message.", alert=True)
            return

        failed = 0
        sent = 0  # Counter for successfully sent messages

        # Notify admin about the progress
        progress_message = await event.edit(f"📤 Starting Broadcast...\n\n👥 Total users: {len(active_users)}")

        # Send the broadcast message to all users
        for idx, user_id in enumerate(active_users, start=1):
            try:
                await bot.send_message(user_id, broadcast_message_content)
                sent += 1
            except Exception:
                failed += 1

            # Update progress to admin every 10 users
            if idx % 10 == 0 or idx == len(active_users):
                await progress_message.edit(
                    f"📤 Broadcasting...\n\n✅ Sent: {sent}\n❌ Failed: {failed}\n👥 Remaining: {len(active_users) - idx}"
                )

        # Notify admin that broadcast is complete
        await progress_message.edit(
            f"✅ Broadcast Completed!\n\n📤 Sent to: {sent} users\n❌ Failed: {failed}\n👥 Total users: {len(active_users)}"
        )

        # Reset the broadcast message content
        broadcast_message_content = None

    elif event.data == b'confirm_no':
        # If the admin presses 'No', cancel the broadcast
        await event.edit("❌ Broadcast cancelled.")
        broadcast_message_content = None


# Broadcast HTTP Server using aiohttp
async def handle(request):
    return web.Response(text="Welcome to the bot's API! Bot is running!")

app = web.Application()
app.router.add_get('/', handle)

# Run the Bot and HTTP Server
print("🤖 Bot is running...")
loop = asyncio.get_event_loop()
loop.create_task(bot.run_until_disconnected())
web.run_app(app, host='0.0.0.0', port=8080)
