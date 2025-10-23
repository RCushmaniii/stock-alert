"""
Test winotify notification with action button
"""
from winotify import Notification, audio
import os

print("Testing winotify notification with button...\n")

# Get icon path
icon_path = os.path.join(os.path.dirname(__file__), 'stock_alert.ico')

# Create test notification
toast = Notification(
    app_id="Stock Alert Test",
    title="📈 Test Alert",
    msg="AAPL reached $256.83 - Click 'View Chart' to open Yahoo Finance",
    duration="long",
    icon=icon_path if os.path.exists(icon_path) else None
)

# Add sound
toast.set_audio(audio.Default, loop=False)

# Add action button
toast.add_actions(
    label="View Chart",
    launch="https://finance.yahoo.com/quote/AAPL"
)

print("Showing notification...")
print("Look for the notification in the bottom-right corner.")
print("Click the 'View Chart' button to test if it opens the browser.\n")

toast.show()

print("✅ Notification sent!")
print("\nNote: If the button doesn't appear or work:")
print("  1. Windows may not show buttons on all notification types")
print("  2. Focus Assist settings might hide buttons")
print("  3. Some Windows versions have limited button support")
