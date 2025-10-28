# StockAlert Runtime Behavior - Quick Reference

## 🎯 Key Points

### Does NOT Auto-Start
- ❌ Does NOT run automatically when Windows starts
- ❌ Does NOT run in the background
- ❌ Does NOT minimize to system tray
- ✅ Must be manually launched each time
- ✅ Console window must stay open while monitoring

### When to Run
**Only during market hours!**

Stock prices don't change when markets are closed, so running 24/7 wastes resources.

**US Market Hours (Eastern Time):**
- **Regular:** 9:30 AM - 4:00 PM (Mon-Fri)
- **Pre-market:** 4:00 AM - 9:30 AM
- **After-hours:** 4:00 PM - 8:00 PM
- **Closed:** Nights, weekends, holidays

### Resource Usage
- **Memory:** ~50-100 MB
- **CPU:** Minimal (only active during price checks)
- **Network:** Brief API calls every 60 seconds (default)
- **Impact:** Very low, but no benefit when markets are closed

## 📋 Typical Usage

### Daily Workflow
1. Market opens (or when you start trading)
2. Launch **StockAlert** from Start Menu
3. Console window shows real-time prices
4. Get notifications when thresholds are crossed
5. Close window when done (or at market close)
6. Repeat next trading day

### Stopping Monitoring
- Close the console window, OR
- Press `Ctrl+C` in the console

Monitoring stops immediately when you do either.

## ⚙️ Optional: Auto-Start During Market Hours

If you want automatic startup (advanced users):

### Option 1: Windows Task Scheduler (Recommended)
- Starts at 9:25 AM on weekdays
- Stops after 8 hours
- Only runs Monday-Friday
- See USER_GUIDE.md for detailed instructions

### Option 2: Startup Folder (Not Recommended)
- Runs every time Windows starts
- Wastes resources nights/weekends
- Must manually close when not needed

## 🔮 Future Enhancements

Potential improvements for future versions:

1. **System Tray Support**
   - Minimize to tray instead of taskbar
   - Right-click menu for quick actions
   - Tray icon shows monitoring status

2. **Market Hours Detection**
   - Auto-pause when market closes
   - Auto-resume when market opens
   - Skip weekends/holidays automatically

3. **Windows Service Option**
   - Run invisibly in background
   - Auto-start/stop with market hours
   - No console window needed

4. **Sleep Mode**
   - Reduce check frequency when market is closed
   - Wake up when market opens
   - Configurable behavior

## ❓ Common Questions

**Q: Why doesn't it auto-start?**  
A: To save resources. Most users don't need 24/7 monitoring, and markets are only open ~6.5 hours/day.

**Q: Can I make it auto-start?**  
A: Yes, but use Task Scheduler to start only during market hours (see USER_GUIDE.md).

**Q: Why must the console stay open?**  
A: Current design. Future versions may add background/tray support.

**Q: What if I accidentally close the window?**  
A: Just restart StockAlert.exe. Your config is saved.

**Q: Does it use a lot of battery on laptops?**  
A: Minimal impact. But still recommended to run only when actively monitoring.

---

**Version:** 2.0.0  
**Design Philosophy:** User-controlled, resource-efficient, market-hours focused
