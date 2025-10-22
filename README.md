# 🚗 Car Marketplace Bot
**Multilingual Telegram Bot for Buying & Selling Cars**

---

## ✨ **Features**
- **🌐 3 Languages**: English 🇺🇸, Arabic 🇸🇦, French 🇫🇷
- **💵 USD Currency**: Universal dollar pricing
- **📸 Photo Uploads**: Clear car photos
- **🔍 Smart Search**: Filter by price ($10K, $20K, $30K, All)
- **🗑️ Manage Listings**: View & delete your cars
- **📞 Direct Contact**: Message sellers instantly
- **📊 Live Stats**: Market analytics
- **🎨 Beautiful UI**: Professional design

---

## 🚀 **Quick Start**

### 1. **Install Dependencies**

pip install python-telegram-bot==20.7 python-dotenv==1.0.0

### 2. **Create `.env` file**
BOT_TOKEN=your_bot_token_here
IMAGES_DIR=car_images

**Get Bot Token**: Message [@BotFather](https://t.me/botfather) → `/newbot`

### 3. **Run the Bot**

python bot.py

✅ **Bot is live!**

---

## 📁 **Files Needed**

```
Carroom_bot/
├── bot.py           # Main bot
├── database.py      # Database functions
├── languages.py     # Translations
├── .env            # Bot token
└── car_images/     # Photos folder (auto-created)
```

---

## 🎮 **How to Use**

### **For Sellers** 🚗
1. Tap **"🚗 Add Car"**
2. Fill 8 steps: Model → Year → Price → Miles → Location → Condition → Phone → Photo
3. ✅ **Your ad is live!**

### **For Buyers** 🔍
1. Tap **"🔍 Browse Cars"**
2. Choose price: **$10K / $20K / $30K / All**
3. Tap **"✉️ Message Seller"** or **"📞 Copy Phone"**

### **Manage Your Ads** 🗂️
1. Tap **"🗂️ My Cars"**
2. Delete any listing with **"🗑️ Delete"**

---

## 🌍 **Languages**
Users can change language anytime:
- **🌐 Language** → Choose English / العربية / Français

---

## 💳 **Currency: USD**
```
💰 Prices in US Dollars only
• No conversion needed
• Works worldwide
```

---

## 🔧 **Commands**
```
/start    - Main Menu
/addcar   - Add New Car
/explore  - Browse Cars
/mycars   - My Cars
/stats    - Statistics
/help     - Help
/lang     - Change Language
/cancel   - Cancel
```

---

## 🗄️ **What Bot Stores**
```
✅ Car Details: Model, Year, Price, Miles, Location, Condition
✅ Phone Number (sanitized)
✅ Photo (saved locally)
✅ User Language preference
❌ No passwords or personal data
```

---

## 🛠️ **Troubleshooting**

| **Problem** | **Solution** |
|-------------|--------------|
| **Bot not starting** | Check `.env` BOT_TOKEN |
| **No photos** | Create `car_images/` folder |
| **Import errors** | `pip install -r requirements.txt` |
| **Database error** | Delete `cars.db` (bot recreates) |

---

## 📱 **Menu Buttons**
```
🚗 Add Car     🔍 Browse Cars
🗂️ My Cars    📊 Stats
ℹ️ Help       🌐 Language
```

---

## 🎉 **Ready to Go!**
1. Copy all 3 files: `bot.py`, `database.py`, `languages.py`
2. Add your `BOT_TOKEN` to `.env`
3. Run `python bot.py`
4. Share your bot link! 🚀

**Made for car enthusiasts worldwide!** ❤️

try to contact me :jalalweez@gmail.com 
Linkedin : https://www.linkedin.com/in/bekhti-djalal/